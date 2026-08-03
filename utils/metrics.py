"""
Observability metrics collection.

Tracks per-agent runtime, failure rate, source usage, confidence
distribution, insight counts, and human approval/rejection counts.
Metrics are recorded in-memory during a run and persisted to the
``agent_metrics`` table plus a Power-BI-ready CSV at the end.
"""
from __future__ import annotations

import statistics
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, Iterator, List

from utils.helpers import iso_now, new_id


@dataclass
class AgentRunRecord:
    id: str
    agent_name: str
    step: str
    started_at: str
    duration_seconds: float
    success: bool
    error_message: str = ""


@dataclass
class MetricsCollector:
    """A single collector instance per pipeline run."""

    run_records: List[AgentRunRecord] = field(default_factory=list)
    confidence_scores: List[float] = field(default_factory=list)
    sources_used: Dict[str, int] = field(default_factory=dict)
    insights_produced: int = 0
    human_approvals: int = 0
    human_rejections: int = 0

    @contextmanager
    def track(self, agent_name: str, step: str) -> Iterator[None]:
        start = time.perf_counter()
        started_at = iso_now()
        error_message = ""
        success = True
        try:
            yield
        except Exception as exc:  # re-raised after recording
            success = False
            error_message = str(exc)
            raise
        finally:
            duration = time.perf_counter() - start
            self.run_records.append(
                AgentRunRecord(
                    id=new_id("run"),
                    agent_name=agent_name,
                    step=step,
                    started_at=started_at,
                    duration_seconds=round(duration, 4),
                    success=success,
                    error_message=error_message,
                )
            )

    def record_confidence(self, score: float) -> None:
        self.confidence_scores.append(score)

    def record_source_used(self, source_name: str) -> None:
        self.sources_used[source_name] = self.sources_used.get(source_name, 0) + 1

    def record_insight(self, count: int = 1) -> None:
        self.insights_produced += count

    def record_human_decision(self, approved: bool) -> None:
        if approved:
            self.human_approvals += 1
        else:
            self.human_rejections += 1

    # ----------------------------------------------------------------
    def failure_rate(self) -> float:
        if not self.run_records:
            return 0.0
        failures = sum(1 for r in self.run_records if not r.success)
        return round(failures / len(self.run_records), 4)

    def average_runtime_by_agent(self) -> Dict[str, float]:
        buckets: Dict[str, List[float]] = {}
        for r in self.run_records:
            buckets.setdefault(r.agent_name, []).append(r.duration_seconds)
        return {agent: round(statistics.mean(vals), 4) for agent, vals in buckets.items()}

    def confidence_distribution(self) -> Dict[str, float]:
        if not self.confidence_scores:
            return {"min": 0.0, "max": 0.0, "mean": 0.0, "median": 0.0}
        return {
            "min": round(min(self.confidence_scores), 4),
            "max": round(max(self.confidence_scores), 4),
            "mean": round(statistics.mean(self.confidence_scores), 4),
            "median": round(statistics.median(self.confidence_scores), 4),
        }

    def summary(self) -> Dict[str, object]:
        return {
            "total_agent_runs": len(self.run_records),
            "failure_rate": self.failure_rate(),
            "average_runtime_by_agent": self.average_runtime_by_agent(),
            "confidence_distribution": self.confidence_distribution(),
            "sources_used": self.sources_used,
            "insights_produced": self.insights_produced,
            "human_approvals": self.human_approvals,
            "human_rejections": self.human_rejections,
        }

    def persist(self, session, run_id: str) -> int:
        """Write every recorded agent run to the agent_metrics table."""
        from database.models import AgentMetric  # local import avoids a cycle
        from database.session import Repository

        repo = Repository(AgentMetric)
        rows = [
            AgentMetric(
                id=new_id("metric"),
                run_id=run_id,
                agent_name=r.agent_name,
                step=r.step,
                duration_seconds=r.duration_seconds,
                success=int(r.success),
                error_message=r.error_message or None,
                created_at=r.started_at,
            )
            for r in self.run_records
        ]
        repo.bulk_insert(session, rows)
        session.flush()
        return len(rows)
