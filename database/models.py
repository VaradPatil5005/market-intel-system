"""SQLAlchemy ORM models mapped 1:1 with database/schema.sql."""
from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SerializableMixin:
    def to_dict(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}  # type: ignore[attr-defined]


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
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class Insight(Base, SerializableMixin):
    __tablename__ = "insights"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    related_entity_id: Mapped[str] = mapped_column(String, nullable=True)
    supporting_source_ids: Mapped[str] = mapped_column(Text, nullable=True)
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
