"""Shared state schema passed between LangGraph nodes."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class PipelineState(TypedDict, total=False):
    run_id: str
    raw_sources: List[Any]        # database.models.RawSource
    entities: List[Any]           # database.models.Entity
    sentiment_results: List[Any]  # database.models.SentimentResult
    trend_results: List[Any]      # database.models.TrendResult
    rag_insights: List[Any]       # database.models.Insight (category="rag")
    confidence_scores: List[Any]  # database.models.ConfidenceScore
    report: Optional[Any]         # database.models.ReportExport

    # Control-flow flags used by supervisor routing
    needs_human_review: bool
    human_approved: Optional[bool]
    human_review_notes: Optional[str]
    error: Optional[str]
    metrics_summary: Dict[str, Any]
