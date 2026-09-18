"""SQLAlchemy ORM models mapped 1:1 with database/schema.sql.

Extended in v2 with:
- UserQuery           — tracks every user question for personalized context
- UserInterestProfile — per-user entity watchlist, risk appetite, output depth
- AgentLearning       — Reflexion lessons generated from human reviewer edits
- GroundingRecord     — audit log for every claim verified by GroundingGateAgent
- PriceSnapshot       — OHLCV / technical indicator snapshots from yfinance
- ReviewQueueItem     — async human review queue ("queue" mode in human_review_mode)
- Insight.insight_type — fact / analysis / prediction / recommendation taxonomy
"""
from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SerializableMixin:
    def to_dict(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Original models (unchanged)
# ---------------------------------------------------------------------------

class RawSource(Base, SerializableMixin):
    __tablename__ = "raw_sources"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    published_at: Mapped[str] = mapped_column(String, nullable=True)
    fetched_at: Mapped[str] = mapped_column(String, nullable=False)
    credibility_score: Mapped[float] = mapped_column(Float, nullable=True)
    credibility_explanation: Mapped[str] = mapped_column(Text, nullable=True)
    is_rejected: Mapped[int] = mapped_column(Integer, default=0)
    raw_metadata: Mapped[str] = mapped_column(Text, nullable=True)


class Entity(Base, SerializableMixin):
    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    aliases: Mapped[str] = mapped_column(Text, nullable=True)
    source_id: Mapped[str] = mapped_column(String, nullable=True)
    first_seen_at: Mapped[str] = mapped_column(String, nullable=False)
    last_seen_at: Mapped[str] = mapped_column(String, nullable=False)
    mention_count: Mapped[int] = mapped_column(Integer, default=1)


class SentimentResult(Base, SerializableMixin):
    __tablename__ = "sentiment_results"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source_id: Mapped[str] = mapped_column(String, nullable=True)
    entity_id: Mapped[str] = mapped_column(String, nullable=True)
    sentiment_label: Mapped[str] = mapped_column(String, nullable=False)
    polarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class TrendResult(Base, SerializableMixin):
    __tablename__ = "trend_results"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    topic: Mapped[str] = mapped_column(String, nullable=False)
    trend_label: Mapped[str] = mapped_column(String, nullable=False)
    current_score: Mapped[float] = mapped_column(Float, nullable=False)
    historical_avg: Mapped[float] = mapped_column(Float, nullable=True)
    change_pct: Mapped[float] = mapped_column(Float, nullable=True)
    window_days: Mapped[int] = mapped_column(Integer, default=7)
    ewma_mean: Mapped[float] = mapped_column(Float, nullable=True)
    ewma_std: Mapped[float] = mapped_column(Float, nullable=True)
    z_score: Mapped[float] = mapped_column(Float, nullable=True)
    is_anomalous: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class ForecastResult(Base, SerializableMixin):
    """Tier 2: next-cycle sentiment/trend forecast for an entity."""

    __tablename__ = "forecast_results"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String, nullable=True)
    entity_name: Mapped[str] = mapped_column(String, nullable=False)
    predicted_direction: Mapped[str] = mapped_column(String, nullable=False)
    predicted_magnitude: Mapped[float] = mapped_column(Float, nullable=True)
    observations_used: Mapped[int] = mapped_column(Integer, default=0)
    model_used: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class Insight(Base, SerializableMixin):
    __tablename__ = "insights"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    related_entity_id: Mapped[str] = mapped_column(String, nullable=True)
    supporting_source_ids: Mapped[str] = mapped_column(Text, nullable=True)
    # Taxonomy: "fact" | "analysis" | "prediction" | "recommendation"
    # - fact:           directly observed in source text (e.g. sentiment shift, mention count)
    # - analysis:       cross-source synthesis, RAG historical parallels
    # - prediction:     forward-looking forecast from ForecastingAgent
    # - recommendation: prescriptive action derived from analysis
    insight_type: Mapped[str] = mapped_column(String, default="analysis")
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class ConfidenceScore(Base, SerializableMixin):
    __tablename__ = "confidence_scores"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    insight_id: Mapped[str] = mapped_column(String, nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    source_quality_component: Mapped[float] = mapped_column(Float, nullable=True)
    agreement_component: Mapped[float] = mapped_column(Float, nullable=True)
    recency_component: Mapped[float] = mapped_column(Float, nullable=True)
    completeness_component: Mapped[float] = mapped_column(Float, nullable=True)
    is_flagged: Mapped[int] = mapped_column(Integer, default=0)
    flag_reason: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class AuditLog(Base, SerializableMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    step: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    input_summary: Mapped[str] = mapped_column(Text, nullable=True)
    output_summary: Mapped[str] = mapped_column(Text, nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=True)
    decision: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class Checkpoint(Base, SerializableMixin):
    __tablename__ = "checkpoints"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False)
    node_name: Mapped[str] = mapped_column(String, nullable=False)
    state_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class ReportExport(Base, SerializableMixin):
    __tablename__ = "report_exports"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False)
    report_title: Mapped[str] = mapped_column(String, nullable=False)
    executive_summary: Mapped[str] = mapped_column(Text, nullable=True)
    full_report_json: Mapped[str] = mapped_column(Text, nullable=False)
    approved: Mapped[int] = mapped_column(Integer, default=0)
    approved_by: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class AgentMetric(Base, SerializableMixin):
    __tablename__ = "agent_metrics"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    step: Mapped[str] = mapped_column(String, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    success: Mapped[int] = mapped_column(Integer, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


# ---------------------------------------------------------------------------
# v2 Advanced Feature Models
# ---------------------------------------------------------------------------

class UserQuery(Base, SerializableMixin):
    """Stores every user question/query for personalized context retrieval.

    The QueryMemoryAgent reads these to build a user interest profile and
    bias entity watchlists + report depth toward topics the user cares about.
    """
    __tablename__ = "user_queries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_entities: Mapped[str] = mapped_column(Text, nullable=True)   # JSON list
    intent_category: Mapped[str] = mapped_column(String, nullable=True)    # e.g. "earnings_risk", "competitor_analysis"
    run_id: Mapped[str] = mapped_column(String, nullable=True)             # associated pipeline run if any
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class UserInterestProfile(Base, SerializableMixin):
    """Per-user persistent interest profile updated on each query.

    Drives: custom watchlist, preferred report depth, risk appetite signaling.
    """
    __tablename__ = "user_interest_profiles"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    watchlist_override: Mapped[str] = mapped_column(Text, nullable=True)   # JSON list of entity names
    risk_appetite: Mapped[str] = mapped_column(String, default="moderate") # conservative / moderate / speculative
    preferred_depth: Mapped[str] = mapped_column(String, default="standard") # brief / standard / deep
    top_categories: Mapped[str] = mapped_column(Text, nullable=True)       # JSON list of preferred insight categories
    query_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)


class AgentLearning(Base, SerializableMixin):
    """Reflexion lessons generated when a human reviewer modifies/rejects an insight.

    Future runs load the top-K relevant lessons via cosine similarity and
    apply them as soft constraints on insight generation and confidence scoring.
    """
    __tablename__ = "agent_learnings"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source_insight_id: Mapped[str] = mapped_column(String, nullable=True)
    entity_name: Mapped[str] = mapped_column(String, nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=True)
    human_action: Mapped[str] = mapped_column(String, nullable=False)      # "reject" | "modify"
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=True)
    lesson_text: Mapped[str] = mapped_column(Text, nullable=False)          # structured lesson
    lesson_type: Mapped[str] = mapped_column(String, nullable=True)         # e.g. "false_positive_risk"
    lesson_embedding: Mapped[str] = mapped_column(Text, nullable=True)      # JSON float list
    is_active: Mapped[int] = mapped_column(Integer, default=1)              # 0 = retired by human
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class GroundingRecord(Base, SerializableMixin):
    """Audit log for every numeric claim verified by GroundingGateAgent.

    Inspired by Vibe-Trading's grounding gate: every number in generated
    narrative text is checked against observed tool results before publication.
    """
    __tablename__ = "grounding_records"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)           # the sentence containing the claim
    claimed_value: Mapped[str] = mapped_column(String, nullable=False)      # extracted numeric string
    verdict: Mapped[str] = mapped_column(String, nullable=False)            # "verified" | "flagged" | "redacted"
    nearest_observed_value: Mapped[str] = mapped_column(String, nullable=True)
    evidence_source: Mapped[str] = mapped_column(String, nullable=True)    # which DB table confirmed/denied
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class PriceSnapshot(Base, SerializableMixin):
    """OHLCV and technical indicator snapshot for a tracked entity.

    Populated by PriceDataAgent using yfinance (free, no key required).
    Degrades gracefully: if yfinance unavailable, no rows are written and
    the pipeline continues without price enrichment.
    """
    __tablename__ = "price_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String, nullable=True)
    entity_name: Mapped[str] = mapped_column(String, nullable=False)
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=True)
    price_7d_return_pct: Mapped[float] = mapped_column(Float, nullable=True)
    price_30d_return_pct: Mapped[float] = mapped_column(Float, nullable=True)
    volatility_30d: Mapped[float] = mapped_column(Float, nullable=True)    # annualised std of daily returns
    rsi_14: Mapped[float] = mapped_column(Float, nullable=True)
    bb_squeeze: Mapped[int] = mapped_column(Integer, default=0)            # 1 = Bollinger Band squeeze detected
    volume_anomaly: Mapped[int] = mapped_column(Integer, default=0)        # 1 = unusual volume spike
    data_source: Mapped[str] = mapped_column(String, default="yfinance")
    fetched_at: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class ReviewQueueItem(Base, SerializableMixin):
    """Async human review queue — used when human_review_mode='queue'.

    Lifecycle:
      1. Pipeline halts at node_human_review and writes a PENDING row.
      2. External analyst retrieves the item via GET /api/review-queue.
      3. Analyst approves/rejects via POST /api/review-queue/{id}/decision.
      4. resume_pipeline(run_id) is called and the pipeline continues to
         generate_report if approved, or end_rejected if rejected.

    In 'auto' mode the row is still written but resolved immediately
    (status='APPROVED'/'REJECTED') by default_auto_reviewer() before
    any external interaction is required.
    """
    __tablename__ = "review_queue"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # PENDING → awaiting analyst  |  APPROVED → pipeline may continue  |  REJECTED → end
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    flagged_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    summary_json: Mapped[str] = mapped_column(Text, nullable=True)         # JSON snapshot of flagged insights
    reviewer_notes: Mapped[str] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[str] = mapped_column(String, nullable=True)        # "auto_reviewer" or analyst email
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    resolved_at: Mapped[str] = mapped_column(String, nullable=True)
