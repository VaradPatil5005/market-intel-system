"""
Supervisor Agent — conditional routing logic for the LangGraph workflow.

Pure decision functions (no side effects) so they're easy to unit test:
each takes the current PipelineState and returns the name of the next
node to route to.
"""
from __future__ import annotations

from orchestration.state import PipelineState
from utils.config import settings
from utils.logging_setup import get_logger

logger = get_logger("supervisor")


def route_after_ingestion(state: PipelineState) -> str:
    if not state.get("raw_sources"):
        logger.warning("No sources ingested — routing to error handling.")
        return "handle_error"
    return "score_credibility"


def route_after_credibility(state: PipelineState) -> str:
    sources = state.get("raw_sources", [])
    accepted = [s for s in sources if not getattr(s, "is_rejected", 0)]
    if not accepted:
        logger.warning("All sources rejected on credibility grounds — routing to error handling.")
        return "handle_error"
    return "resolve_entities"


def route_after_confidence(state: PipelineState) -> str:
    """Route to human review when confidence is low or evidence conflicts."""
    scores = state.get("confidence_scores", [])
    if not scores:
        return "generate_report"

    flagged = [s for s in scores if getattr(s, "is_flagged", 0)]
    avg_score = sum(s.score for s in scores) / len(scores)

    if avg_score < settings.human_review_required_below or flagged:
        logger.info(
            f"Routing to human review: avg_confidence={avg_score:.2f}, flagged={len(flagged)}"
        )
        return "human_review"
    return "generate_report"


def route_after_human_review(state: PipelineState) -> str:
    if state.get("human_approved") is False:
        logger.info("Human reviewer rejected the batch — ending run without publishing.")
        return "end_rejected"
    return "generate_report"
