"""Shared state schema passed between LangGraph nodes.

v2: Extended with deep_search, price, correlation, and grounding gate fields.
v2.1: Added seed, config_snapshot, input_snapshot for reproducibility;
      review_queue_id for async human review queue integration.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class PipelineState(TypedDict, total=False):
    run_id: str
    raw_sources: List[Any]           # database.models.RawSource
    entities: List[Any]              # database.models.Entity
    sentiment_results: List[Any]     # database.models.SentimentResult
    trend_results: List[Any]         # database.models.TrendResult
    rag_insights: List[Any]          # database.models.Insight (category="rag")
    confidence_scores: List[Any]     # database.models.ConfidenceScore
    forecasts: List[Any]             # database.models.ForecastResult
    report: Optional[Any]            # database.models.ReportExport

    # Control-flow flags used by supervisor routing
    needs_human_review: bool
    human_approved: Optional[bool]
    human_review_notes: Optional[str]
    review_queue_id: Optional[str]   # ReviewQueueItem.id (set in queue mode)
    error: Optional[str]
    metrics_summary: Dict[str, Any]

    # v2: deep search
    deep_search_entities: List[str]    # entity names that triggered deep search

    # v2: price enrichment
    price_snapshots: List[Any]         # database.models.PriceSnapshot

    # v2: market correlation + counterfactual scenarios
    correlation_matrix: Dict[str, Dict[str, float]]
    high_correlation_pairs: List[Any]  # [(entity1, entity2, float)]
    supply_chain_pairs: List[Any]      # [(entity1, entity2)]
    counterfactual_scenarios: List[str]

    # v2: grounding gate results
    grounding_records: List[Any]       # database.models.GroundingRecord
    grounding_flagged_count: int

    # v2: user personalization context
    user_context: Dict[str, Any]       # from QueryMemoryAgent.load_user_context()

    # Specialized domain intelligence fields
    sec_discrepancies: List[Any]       # from DiscrepancyAuditorAgent
    geopolitical_risks: List[Any]      # from GeopoliticalRiskAgent
    macro_rates: Dict[str, Any]        # from MacroRatesAgent
    global_macro: Dict[str, Any]       # from GlobalMacroAgent
    vibe_quant_signals: Dict[str, Any] # from VibeQuantAgent
    liquidity_order_flow: Dict[str, Any] # from LiquidityOrderFlowAgent
    risk_hedges: Dict[str, Any]        # from RiskSentinelAgent
    competitor_benchmarks: List[Any]   # from CompetitorAgent
    reflexion_critique: Dict[str, Any] # from ReflexionAgent
    execution_orders: List[Any]        # from ExecutionRouterAgent

    # v2.1: reproducibility metadata (populated by run_pipeline)
    seed: Optional[int]                # random seed used for this run
    config_snapshot: Dict[str, str]    # settings at run time (keys with secrets redacted)
    input_snapshot: Dict[str, Any]     # input parameters passed to run_pipeline
