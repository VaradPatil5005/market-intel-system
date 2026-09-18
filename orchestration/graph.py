"""
LangGraph Orchestration — v2 Enhanced.

Wires all agents into a single stateful, checkpointed, resumable graph:

    ingest -> score_credibility -> resolve_entities -> analyze_sentiment
           -> analyze_trends -> [deep_search?] -> rag_retrieval
           -> score_confidence -> [price_enrich?] -> [market_correlation?]
           -> forecast_trends -> [human_review?] -> generate_report
           -> grounding_gate -> END

New v2 nodes:
  - deep_search:       autonomous web/SEC discovery on anomaly (post-trends, conditional)
  - price_enrich:      OHLCV + technical indicators from yfinance (conditional)
  - market_correlation: cross-entity correlation + counterfactual scenarios
  - grounding_gate:    numeric claim verification before publish

Conditional routing:
  - deep_search triggers AFTER analyze_trends (so trend_results are available for
    anomaly-driven entity targeting) when enable_deep_search=True or enable_sec_edgar=True
  - price_enrich only when price_data_enabled=True
  - forecast_trends always runs (fallback from route_after_confidence_v2)
  - human_review path unchanged from v1
  - grounding_gate always runs if enable_grounding_gate=True

A checkpoint is saved after every node so failed runs can resume.
"""
from __future__ import annotations

from typing import Any, Dict, List, cast

from langgraph.graph import END, StateGraph

from agents.confidence_agent import ConfidenceScoringAgent
from agents.credibility_agent import CredibilityAgent
from agents.deep_search_agent import DeepSearchAgent
from agents.entity_resolution_agent import EntityResolutionAgent
from agents.forecasting_agent import ForecastingAgent
from agents.grounding_gate_agent import GroundingGateAgent
from agents.ingestion_agent import IngestionAgent
from agents.market_correlation_agent import MarketCorrelationAgent
from agents.price_data_agent import PriceDataAgent
from agents.rag_agent import RagInsightAgent
from agents.report_agent import ReportGenerationAgent
from agents.sentiment_agent import SentimentAgent
from agents.trend_agent import TrendAgent
from database.session import get_session
from orchestration import supervisor
from orchestration.checkpointing import save_checkpoint
from orchestration.human_in_loop import request_human_review
from orchestration.state import PipelineState
from utils.config import settings
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
    "deep_search",        # post-trends: anomaly-driven web/SEC discovery
    "rag_retrieval",
    "score_confidence",
    "price_enrich",
    "market_correlation",
    "forecast_trends",
    "human_review",
    "generate_report",
    "grounding_gate",
]


def next_node_after(node_name: str) -> str | None:
    if node_name not in NODE_ORDER:
        return None
    idx = NODE_ORDER.index(node_name)
    return NODE_ORDER[idx + 1] if idx + 1 < len(NODE_ORDER) else None


def _all_insights(session: Any, run_id: str) -> List[Any]:
    from database.models import Insight  # noqa: PLC0415
    from database.session import Repository  # noqa: PLC0415
    return Repository(Insight).filter_by(session, run_id=run_id)


def build_graph(metrics: MetricsCollector, entry_point: str = "ingest", simulate_failure_at: str | None = None):
    ingestion_agent = IngestionAgent(metrics)
    credibility_agent = CredibilityAgent(metrics)
    entity_agent = EntityResolutionAgent(metrics)
    sentiment_agent = SentimentAgent(metrics)
    trend_agent = TrendAgent(metrics)
    rag_agent = RagInsightAgent(metrics)
    confidence_agent = ConfidenceScoringAgent(metrics)
    report_agent = ReportGenerationAgent(metrics)
    forecasting_agent = ForecastingAgent(metrics)
    deep_search_agent = DeepSearchAgent(metrics)
    price_agent = PriceDataAgent(metrics)
    correlation_agent = MarketCorrelationAgent(metrics)
    grounding_agent = GroundingGateAgent(metrics)

    def checkpointed(node_name: str, state: Any) -> None:
        with get_session() as session:
            save_checkpoint(session, state.get("run_id", ""), node_name, dict(state))

    def _maybe_fail(node_name: str) -> None:
        if simulate_failure_at == node_name:
            raise RuntimeError(f"Simulated failure injected at node '{node_name}' (for recovery demo).")

    # ---- v1 Nodes (all preserved) ----------------------------------------
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
                sources = credibility_agent.run(session, state.get("raw_sources", []))
            update = {"raw_sources": sources}
            checkpointed("score_credibility", {**state, **update})
            return update
        except Exception as exc:
            logger.exception("Credibility scoring failed")
            return {"error": str(exc)}

    def node_entities(state: PipelineState) -> Dict[str, Any]:
        _maybe_fail("resolve_entities")
        with get_session() as session:
            entities = entity_agent.run(session, state.get("raw_sources", []))
        update = {"entities": entities}
        checkpointed("resolve_entities", {**state, **update})
        return update

    def node_sentiment(state: PipelineState) -> Dict[str, Any]:
        _maybe_fail("analyze_sentiment")
        with get_session() as session:
            results = sentiment_agent.run(session, state.get("raw_sources", []), state.get("entities", []))
        update = {"sentiment_results": results}
        checkpointed("analyze_sentiment", {**state, **update})
        return update

    def node_trends(state: PipelineState) -> Dict[str, Any]:
        _maybe_fail("analyze_trends")
        with get_session() as session:
            results = trend_agent.run(session, state.get("raw_sources", []))
        update = {"trend_results": results}
        checkpointed("analyze_trends", {**state, **update})
        return update

    def node_rag(state: PipelineState) -> Dict[str, Any]:
        _maybe_fail("rag_retrieval")
        with get_session() as session:
            insights = rag_agent.run(
                session,
                state.get("run_id", ""),
                state.get("entities", []),
                state.get("trend_results", []),
            )
        update = {"rag_insights": insights}
        checkpointed("rag_retrieval", {**state, **update})
        return update

    def node_confidence(state: PipelineState) -> Dict[str, Any]:
        _maybe_fail("score_confidence")
        with get_session() as session:
            scores, all_insights = confidence_agent.run(
                session,
                state.get("run_id", ""),
                state.get("raw_sources", []),
                state.get("entities", []),
                state.get("sentiment_results", []),
                state.get("trend_results", []),
                state.get("rag_insights", []),
            )
        update = {"confidence_scores": scores}
        checkpointed("score_confidence", {**state, **update})
        return update

    def node_forecast(state: PipelineState) -> Dict[str, Any]:
        try:
            _maybe_fail("forecast_trends")
            with get_session() as session:
                forecasts = forecasting_agent.run(
                    session,
                    state.get("run_id", ""),
                    state.get("entities", []),
                )
            update = {"forecasts": forecasts}
            checkpointed("forecast_trends", {**state, **update})
            return update
        except Exception:
            logger.exception("Forecasting failed — continuing without predictions for this run")
            return {"forecasts": []}

    def node_human_review(state: PipelineState) -> Dict[str, Any]:
        with get_session() as session:
            run_id = state.get("run_id", "")
            insights = _all_insights(session, run_id)
            decision = request_human_review(
                session, insights, state.get("confidence_scores", []), run_id=run_id
            )
        if metrics:
            metrics.record_human_decision(decision["approved"])
        update = {
            "human_approved": decision["approved"],
            "human_review_notes": str(decision["summary"]),
            "needs_human_review": True,
            "review_queue_id": decision.get("queue_id"),
        }
        checkpointed("human_review", {**state, **update})
        return update

    def node_report(state: PipelineState) -> Dict[str, Any]:
        _maybe_fail("generate_report")
        with get_session() as session:
            run_id = state.get("run_id", "")
            insights = _all_insights(session, run_id)
            report = report_agent.run(
                session,
                run_id,
                state.get("entities", []),
                insights,
                state.get("confidence_scores", []),
                state.get("forecasts", []),
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

    def node_end_pending(state: PipelineState) -> Dict[str, Any]:
        logger.info("Run paused: human review pending in queue.")
        return {"human_approved": None, "pending_review": True}

    # ---- v2 New Nodes --------------------------------------------------------

    def node_deep_search(state: PipelineState) -> Dict[str, Any]:
        """Autonomous web/SEC discovery triggered by trend anomalies."""
        try:
            # Identify anomalous entities from trend results
            trend_results = state.get("trend_results", [])
            anomalous_entities = [
                t.topic for t in trend_results
                if getattr(t, "is_anomalous", 0) or (
                    getattr(t, "z_score", 0) and t.z_score >= settings.z_score_alert_threshold
                )
            ]

            if not anomalous_entities and not settings.enable_sec_edgar:
                logger.info("DeepSearch node: no anomalies + SEC disabled — skipping.")
                return {}

            # If no anomalies but SEC enabled, search for all watchlist entities
            if not anomalous_entities:
                anomalous_entities = settings.watchlist[:3]   # limit to top 3

            with get_session() as session:
                new_sources = deep_search_agent.run(session, anomalous_entities, state.get("run_id"))

            # Merge new sources into existing sources
            existing_sources = list(state.get("raw_sources", []))
            update = {
                "raw_sources": existing_sources + new_sources,
                "deep_search_entities": anomalous_entities,
            }
            checkpointed("deep_search", {**state, **update})
            return update
        except Exception:
            logger.exception("DeepSearch node failed — continuing without deep search")
            return {}

    def node_price_enrich(state: PipelineState) -> Dict[str, Any]:
        """OHLCV + technical indicators from yfinance (conditional)."""
        try:
            with get_session() as session:
                snapshots = price_agent.run(session, state.get("run_id", ""), state.get("entities", []))
            update = {"price_snapshots": snapshots}
            checkpointed("price_enrich", {**state, **update})
            return update
        except Exception:
            logger.exception("PriceEnrich node failed — continuing without price data")
            return {"price_snapshots": []}

    def node_market_correlation(state: PipelineState) -> Dict[str, Any]:
        """Cross-entity correlation matrix + counterfactual scenarios."""
        try:
            with get_session() as session:
                result = correlation_agent.run(session, state.get("entities", []))
            update = {
                "correlation_matrix": result.get("correlation_matrix", {}),
                "counterfactual_scenarios": result.get("counterfactual_scenarios", []),
                "supply_chain_pairs": result.get("supply_chain_pairs", []),
                "high_correlation_pairs": result.get("high_correlation_pairs", []),
            }
            checkpointed("market_correlation", {**state, **update})
            return update
        except Exception:
            logger.exception("MarketCorrelation node failed — continuing")
            return {
                "correlation_matrix": {},
                "counterfactual_scenarios": [],
                "supply_chain_pairs": [],
                "high_correlation_pairs": [],
            }

    def node_grounding_gate(state: PipelineState) -> Dict[str, Any]:
        """Verify all numeric claims in generated report/narrative before publish."""
        try:
            report = state.get("report")
            if report is None:
                return {}

            # Build narrative text to verify
            narrative = getattr(report, "executive_summary", "") or ""
            # Also check the full report JSON text
            full_json = getattr(report, "full_report_json", "") or ""
            combined_text = f"{narrative} {full_json[:2000]}"

            if not combined_text.strip():
                return {}

            with get_session() as session:
                sanitized_text, grounding_records = grounding_agent.run(
                    session, state.get("run_id", ""), combined_text
                )

            flagged_count = sum(1 for r in grounding_records if r.verdict == "flagged")
            logger.info(
                f"GroundingGate: {len(grounding_records)} claims checked, {flagged_count} flagged."
            )
            return {
                "grounding_records": grounding_records,
                "grounding_flagged_count": flagged_count,
            }
        except Exception:
            logger.exception("GroundingGate node failed — publishing report without verification")
            return {}

    # ---- Graph assembly -------------------------------------------------------
    graph = StateGraph(PipelineState)

    # v1 nodes
    graph.add_node("ingest", node_ingest)
    graph.add_node("score_credibility", node_credibility)
    graph.add_node("resolve_entities", node_entities)
    graph.add_node("analyze_sentiment", node_sentiment)
    graph.add_node("analyze_trends", node_trends)
    graph.add_node("rag_retrieval", node_rag)
    graph.add_node("score_confidence", node_confidence)
    graph.add_node("forecast_trends", node_forecast)
    graph.add_node("human_review", node_human_review)
    graph.add_node("generate_report", node_report)
    graph.add_node("handle_error", node_handle_error)
    graph.add_node("end_rejected", node_end_rejected)
    graph.add_node("end_pending", node_end_pending)

    # v2 new nodes
    graph.add_node("deep_search", node_deep_search)
    graph.add_node("price_enrich", node_price_enrich)
    graph.add_node("market_correlation", node_market_correlation)
    graph.add_node("grounding_gate", node_grounding_gate)

    # ---- Edge wiring ----------------------------------------------------------
    graph.set_entry_point(entry_point)

    # After ingest: route to error OR directly to credibility
    graph.add_conditional_edges("ingest", supervisor.route_after_ingestion_v2)

    # Credibility → entities (conditional on rejection)
    graph.add_conditional_edges("score_credibility", supervisor.route_after_credibility)

    # Linear chain: entities → sentiment → trends
    graph.add_edge("resolve_entities", "analyze_sentiment")
    graph.add_edge("analyze_sentiment", "analyze_trends")

    # After trends: optionally run deep_search on anomalous entities, then rag
    graph.add_conditional_edges("analyze_trends", supervisor.route_after_trends_v2)

    # deep_search (when triggered) feeds new sources into rag_retrieval
    graph.add_edge("deep_search", "rag_retrieval")

    # rag_retrieval always feeds into confidence scoring
    graph.add_edge("rag_retrieval", "score_confidence")

    # After confidence: optionally price_enrich, then market_correlation
    graph.add_conditional_edges("score_confidence", supervisor.route_after_confidence_v2)

    # price_enrich → market_correlation
    graph.add_edge("price_enrich", "market_correlation")

    # market_correlation → forecast
    graph.add_edge("market_correlation", "forecast_trends")

    # After forecast: human review gate (unchanged logic)
    graph.add_conditional_edges("forecast_trends", supervisor.route_after_confidence)

    # Human review path
    graph.add_conditional_edges("human_review", supervisor.route_after_human_review)

    # Report → grounding gate → END
    graph.add_edge("generate_report", "grounding_gate")
    graph.add_edge("grounding_gate", END)

    # Error and exit paths
    graph.add_edge("handle_error", END)
    graph.add_edge("end_rejected", END)
    graph.add_edge("end_pending", END)

    return graph.compile()


def run_pipeline(
    metrics: MetricsCollector,
    simulate_failure_at: str | None = None,
    run_id: str | None = None,
    seed: int | None = None,
) -> PipelineState:
    """Execute the full LangGraph pipeline.

    Args:
        metrics:              Shared metrics collector passed to all agents.
        simulate_failure_at:  Node name to intentionally fail at (for recovery demos).
        run_id:               Explicit run identifier — pass a fixed value for
                              deterministic regression tests / replay. Auto-generated
                              if not provided.
        seed:                 Optional random seed for reproducibility. Stored in
                              state for audit purposes; agents that use randomness
                              should read state["seed"] if set.
    """
    import random as _random  # noqa: PLC0415

    resolved_run_id = run_id or new_id("run")
    if seed is not None:
        _random.seed(seed)

    # Snapshot active config so every run is self-describing
    config_snapshot = {
        k: str(v)
        for k, v in settings.model_dump().items()
        if not k.endswith("_password") and not k.endswith("_key")
    }

    initial_state: PipelineState = {
        "run_id": resolved_run_id,
        "seed": seed,
        "config_snapshot": config_snapshot,
        "input_snapshot": {
            "simulate_failure_at": simulate_failure_at,
            "seed": seed,
            "run_id": resolved_run_id,
        },
    }

    app = build_graph(metrics, simulate_failure_at=simulate_failure_at)
    logger.info(f"Starting pipeline run_id={resolved_run_id}" + (f" seed={seed}" if seed is not None else ""))
    final_state = cast(PipelineState, app.invoke(initial_state, config={"recursion_limit": 60}))
    return final_state


def resume_pipeline(
    run_id: str,
    metrics: MetricsCollector,
    human_approved: bool | None = None,
) -> PipelineState:
    """Resume a previously-interrupted run from its last successful checkpoint."""
    from orchestration.checkpointing import deserialize_checkpoint_state, last_successful_node  # noqa: PLC0415

    with get_session() as session:
        node_name = last_successful_node(session, run_id)
        if node_name is None:
            raise RuntimeError(f"No checkpoints found for run {run_id} — nothing to resume from.")
        from orchestration.checkpointing import checkpoint_repo  # noqa: PLC0415
        rows = checkpoint_repo.filter_by(session, run_id=run_id)
        latest = max(rows, key=lambda r: r.created_at)
        import json as _json  # noqa: PLC0415
        snapshot = _json.loads(latest.state_snapshot)

    resume_from = next_node_after(node_name)
    if resume_from is None:
        raise RuntimeError(f"Run {run_id} already completed its last node ('{node_name}') — nothing to resume.")

    recovered_state = deserialize_checkpoint_state(snapshot)
    recovered_state["run_id"] = run_id

    if node_name == "human_review" and human_approved is not None:
        recovered_state["human_approved"] = human_approved
        if not human_approved:
            resume_from = "end_rejected"
        else:
            resume_from = "generate_report"

    logger.info(f"Recovering run {run_id}: last successful node='{node_name}', resuming at '{resume_from}'")

    app = build_graph(metrics, entry_point=resume_from)
    final_state = cast(PipelineState, app.invoke(cast(PipelineState, recovered_state), config={"recursion_limit": 60}))
    return final_state
