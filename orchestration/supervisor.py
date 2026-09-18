"""
Supervisor Agent — conditional routing logic for the LangGraph workflow.

Pure decision functions (no side effects) so they're easy to unit test:
each takes the current PipelineState and returns the name of the next
node to route to.

v2 routing corrections:
  - route_after_ingestion_v2: no longer gates deep_search (deep_search runs
    after analyze_trends where trend_results are available, not right after ingest).
  - route_after_trends_v2: new gate — routes to deep_search post-trends if
    enable_deep_search=True or enable_sec_edgar=True, else goes to rag_retrieval.
  - route_after_confidence_v2: fallback now correctly goes to 'forecast_trends'
    instead of bypassing it via route_after_confidence (which jumped straight
    to human_review or generate_report, skipping forecasting entirely).
"""
from __future__ import annotations

from orchestration.state import PipelineState
from utils.config import settings
from utils.logging_setup import get_logger

logger = get_logger("supervisor")


# ---- v1 routing (preserved, still used by some edges) ----------------------

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
    if state.get("human_approved") is None:
        logger.info("Human review pending analyst decision — pausing pipeline execution.")
        return "end_pending"
    return "generate_report"


# ---- v2 routing (new conditional gates) ------------------------------------

def route_after_ingestion_v2(state: PipelineState) -> str:
    """After ingestion: validate sources, then proceed to credibility scoring.

    NOTE: deep_search now runs AFTER analyze_trends (where trend_results are
    populated) so that anomaly-driven search is actually meaningful. Ingestion
    routing therefore mirrors the v1 logic: error-check, then credibility.

    Routes to:
      - "handle_error"      if ingestion produced no sources
      - "score_credibility" otherwise
    """
    if not state.get("raw_sources"):
        logger.warning("No sources ingested — routing to error handling.")
        return "handle_error"

    return "score_credibility"


def route_after_trends_v2(state: PipelineState) -> str:
    """After trend analysis: optionally run deep_search on anomalous entities.

    Running deep_search HERE (post-trends) ensures DeepSearchAgent has access
    to state['trend_results'] and can target statistically anomalous entities
    (Z-score >= threshold) rather than blindly searching the whole watchlist.

    Routes to:
      - "deep_search"    if enable_deep_search=True OR enable_sec_edgar=True
      - "rag_retrieval"  otherwise
    """
    if settings.enable_deep_search or settings.enable_sec_edgar:
        logger.info("Routing to deep_search post-trends (anomaly-driven search enabled).")
        return "deep_search"

    return "rag_retrieval"


def route_after_confidence_v2(state: PipelineState) -> str:
    """After confidence scoring: optionally run price_enrich, then market_correlation.

    BUG FIX: The previous fallback called route_after_confidence(state) which
    jumped straight to human_review or generate_report, completely skipping
    forecast_trends when price_data_enabled=False and enable_market_correlation=False.
    Now the fallback routes to 'forecast_trends' unconditionally.

    Routes to:
      - "price_enrich"       if price_data_enabled=True
      - "market_correlation" if enable_market_correlation=True (skips price_enrich)
      - "forecast_trends"    otherwise (default — ensures forecasts always run)
    """
    if settings.price_data_enabled:
        logger.info("Routing to price_enrich (price_data_enabled=True).")
        return "price_enrich"

    if settings.enable_market_correlation:
        logger.info("Routing to market_correlation (skipping price_enrich).")
        return "market_correlation"

    # Default: always run forecasting regardless of optional enrichment steps
    logger.info("Routing to forecast_trends (no price/correlation enrichment enabled).")
    return "forecast_trends"
