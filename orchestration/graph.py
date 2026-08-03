"""
LangGraph Orchestration.

Wires all agents into a single stateful, checkpointed, resumable graph:

    ingest -> score_credibility -> resolve_entities -> analyze_sentiment
           -> analyze_trends -> rag_retrieval -> score_confidence
           -> [human_review?] -> generate_report -> END

Conditional routing (missing data / low confidence / conflicting
evidence / human rejection) is delegated to `orchestration.supervisor`.
A checkpoint is saved to SQL + disk after every node so a failed run
can be resumed from the last successful step.
"""
from __future__ import annotations

from typing import Any, Dict

from langgraph.graph import END, StateGraph

from agents.confidence_agent import ConfidenceScoringAgent
from agents.credibility_agent import CredibilityAgent
from agents.entity_resolution_agent import EntityResolutionAgent
from agents.ingestion_agent import IngestionAgent
from agents.rag_agent import RagInsightAgent
from agents.report_agent import ReportGenerationAgent
from agents.sentiment_agent import SentimentAgent
from agents.trend_agent import TrendAgent
from database.session import get_session
from orchestration import supervisor
from orchestration.checkpointing import save_checkpoint
from orchestration.human_in_loop import request_human_review
from orchestration.state import PipelineState
from utils.helpers import new_id
from utils.logging_setup import get_logger
from utils.metrics import MetricsCollector

logger = get_logger("orchestration.graph")

NODE_ORDER = [
    "ingest",
    "score_credibility",
    "resolve_entities",
    "analyze_sentiment",
    "analyze_trends",
    "rag_retrieval",
    "score_confidence",
    "generate_report",
]


def next_node_after(node_name: str) -> str | None:
    """Return the node that should run after `node_name` on the happy path."""
    if node_name not in NODE_ORDER:
        return None
    idx = NODE_ORDER.index(node_name)
    return NODE_ORDER[idx + 1] if idx + 1 < len(NODE_ORDER) else None


def build_graph(metrics: MetricsCollector, entry_point: str = "ingest", simulate_failure_at: str | None = None):
    ingestion_agent = IngestionAgent(metrics)
    credibility_agent = CredibilityAgent(metrics)
    entity_agent = EntityResolutionAgent(metrics)
    sentiment_agent = SentimentAgent(metrics)
    trend_agent = TrendAgent(metrics)
    rag_agent = RagInsightAgent(metrics)
    confidence_agent = ConfidenceScoringAgent(metrics)
    report_agent = ReportGenerationAgent(metrics)

    def checkpointed(node_name: str, state: PipelineState) -> None:
        with get_session() as session:
            save_checkpoint(session, state["run_id"], node_name, dict(state))

    def _maybe_fail(node_name: str) -> None:
        if simulate_failure_at == node_name:
            raise RuntimeError(f"Simulated failure injected at node '{node_name}' (for recovery demo).")

    # ---- Nodes ----------------------------------------------------------
    def node_ingest(state: PipelineState) -> Dict[str, Any]:
        try:
            _maybe_fail("ingest")
            with get_session() as session:
                sources = ingestion_agent.run(session)
            update = {"raw_sources": sources}
            checkpointed("ingest", {**state, **update})
            return update
        except Exception as exc:
            logger.exception("Ingestion failed")
            return {"error": str(exc), "raw_sources": []}

    def node_credibility(state: PipelineState) -> Dict[str, Any]:
        try:
            _maybe_fail("score_credibility")
            with get_session() as session:
                sources = credibility_agent.run(session, state["raw_sources"])
            update = {"raw_sources": sources}
            checkpointed("score_credibility", {**state, **update})
            return update
        except Exception as exc:
            logger.exception("Credibility scoring failed")
            return {"error": str(exc)}

    def node_entities(state: PipelineState) -> Dict[str, Any]:
        _maybe_fail("resolve_entities")
        with get_session() as session:
            entities = entity_agent.run(session, state["raw_sources"])
        update = {"entities": entities}
        checkpointed("resolve_entities", {**state, **update})
        return update

    def node_sentiment(state: PipelineState) -> Dict[str, Any]:
        _maybe_fail("analyze_sentiment")
        with get_session() as session:
            results = sentiment_agent.run(session, state["raw_sources"], state["entities"])
        update = {"sentiment_results": results}
        checkpointed("analyze_sentiment", {**state, **update})
        return update

    def node_trends(state: PipelineState) -> Dict[str, Any]:
        _maybe_fail("analyze_trends")
        with get_session() as session:
            results = trend_agent.run(session, state["raw_sources"])
        update = {"trend_results": results}
        checkpointed("analyze_trends", {**state, **update})
        return update

    def node_rag(state: PipelineState) -> Dict[str, Any]:
        _maybe_fail("rag_retrieval")
        with get_session() as session:
            insights = rag_agent.run(session, state["entities"], state["trend_results"])
        update = {"rag_insights": insights}
        checkpointed("rag_retrieval", {**state, **update})
        return update

    def node_confidence(state: PipelineState) -> Dict[str, Any]:
        _maybe_fail("score_confidence")
        with get_session() as session:
            scores = confidence_agent.run(
                session,
                state["raw_sources"],
                state["entities"],
                state["sentiment_results"],
                state["trend_results"],
                state["rag_insights"],
            )
        update = {"confidence_scores": scores}
        checkpointed("score_confidence", {**state, **update})
        return update

    def node_human_review(state: PipelineState) -> Dict[str, Any]:
        with get_session() as session:
            insights = _all_insights(session)
            decision = request_human_review(session, insights, state["confidence_scores"])
        if metrics:
            metrics.record_human_decision(decision["approved"])
        update = {
            "human_approved": decision["approved"],
            "human_review_notes": str(decision["summary"]),
            "needs_human_review": True,
        }
        checkpointed("human_review", {**state, **update})
        return update

    def node_report(state: PipelineState) -> Dict[str, Any]:
        _maybe_fail("generate_report")
        with get_session() as session:
            insights = _all_insights(session)
            report = report_agent.run(
                session,
                state["run_id"],
                state["entities"],
                insights,
                state["confidence_scores"],
            )
            if state.get("human_approved"):
                report.approved = 1
                report.approved_by = "auto_reviewer"
                session.flush()
        update = {"report": report}
        checkpointed("generate_report", {**state, **update})
        return update

    def node_handle_error(state: PipelineState) -> Dict[str, Any]:
        logger.error(f"Pipeline halted: {state.get('error')}")
        return {"error": state.get("error") or "unknown error"}

    def node_end_rejected(state: PipelineState) -> Dict[str, Any]:
        logger.info("Run ended: human reviewer rejected the batch.")
        return {"human_approved": False}

    # ---- Graph assembly --------------------------------------------------
    graph = StateGraph(PipelineState)
    graph.add_node("ingest", node_ingest)
    graph.add_node("score_credibility", node_credibility)
    graph.add_node("resolve_entities", node_entities)
    graph.add_node("analyze_sentiment", node_sentiment)
    graph.add_node("analyze_trends", node_trends)
    graph.add_node("rag_retrieval", node_rag)
    graph.add_node("score_confidence", node_confidence)
    graph.add_node("human_review", node_human_review)
    graph.add_node("generate_report", node_report)
    graph.add_node("handle_error", node_handle_error)
    graph.add_node("end_rejected", node_end_rejected)

    graph.set_entry_point(entry_point)
    graph.add_conditional_edges("ingest", supervisor.route_after_ingestion)
    graph.add_conditional_edges("score_credibility", supervisor.route_after_credibility)
    graph.add_edge("resolve_entities", "analyze_sentiment")
    graph.add_edge("analyze_sentiment", "analyze_trends")
    graph.add_edge("analyze_trends", "rag_retrieval")
    graph.add_edge("rag_retrieval", "score_confidence")
    graph.add_conditional_edges("score_confidence", supervisor.route_after_confidence)
    graph.add_conditional_edges("human_review", supervisor.route_after_human_review)
    graph.add_edge("generate_report", END)
    graph.add_edge("handle_error", END)
    graph.add_edge("end_rejected", END)

    return graph.compile()


def _all_insights(session):
    from database.models import Insight
    from database.session import Repository

    return Repository(Insight).all(session)


def run_pipeline(metrics: MetricsCollector, simulate_failure_at: str | None = None) -> PipelineState:
    app = build_graph(metrics, simulate_failure_at=simulate_failure_at)
    initial_state: PipelineState = {"run_id": new_id("run")}
    final_state = app.invoke(initial_state, config={"recursion_limit": 50})
    return final_state


def resume_pipeline(run_id: str, metrics: MetricsCollector) -> PipelineState:
    """Resume a previously-interrupted run from its last successful checkpoint."""
    from orchestration.checkpointing import deserialize_checkpoint_state, last_successful_node

    with get_session() as session:
        node_name = last_successful_node(session, run_id)
        if node_name is None:
            raise RuntimeError(f"No checkpoints found for run {run_id} — nothing to resume from.")
        snapshot = None
        from orchestration.checkpointing import checkpoint_repo

        rows = checkpoint_repo.filter_by(session, run_id=run_id)
        latest = max(rows, key=lambda r: r.created_at)
        import json as _json

        snapshot = _json.loads(latest.state_snapshot)

    resume_from = next_node_after(node_name)
    if resume_from is None:
        raise RuntimeError(f"Run {run_id} already completed its last node ('{node_name}') — nothing to resume.")

    logger.info(f"Recovering run {run_id}: last successful node='{node_name}', resuming at '{resume_from}'")
    recovered_state = deserialize_checkpoint_state(snapshot)
    recovered_state["run_id"] = run_id

    app = build_graph(metrics, entry_point=resume_from)
    final_state = app.invoke(recovered_state, config={"recursion_limit": 50})
    return final_state
