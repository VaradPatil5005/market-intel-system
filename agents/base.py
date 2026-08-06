"""Shared base class for all pipeline agents.

Each agent is independent, reusable, accepts structured input, and
returns structured output. Orchestration (LangGraph/CrewAI) lives
outside these modules entirely.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from database.models import AuditLog
from database.session import Repository, Session
from utils.helpers import iso_now, new_id
from utils.logging_setup import get_logger, log_event
from utils.metrics import MetricsCollector

audit_repo = Repository(AuditLog)


class BaseAgent:
    """Common plumbing: logging, audit trail, metrics timing."""

    name: str = "base_agent"

    def __init__(self, metrics: Optional[MetricsCollector] = None):
        self.logger = get_logger(self.name)
        self.metrics = metrics

    def audit(
        self,
        session: Session,
        *,
        step: str,
        action: str,
        input_summary: Any = None,
        output_summary: Any = None,
        score: float | None = None,
        decision: str | None = None,
    ) -> None:
        """Write a row to audit_logs capturing this decision for traceability."""
        record = AuditLog(
            id=new_id("audit"),
            agent_name=self.name,
            step=step,
            action=action,
            input_summary=json.dumps(input_summary, default=str)[:2000] if input_summary is not None else None,
            output_summary=json.dumps(output_summary, default=str)[:2000] if output_summary is not None else None,
            score=score,
            decision=decision,
            created_at=iso_now(),
        )
        audit_repo.insert(session, record)
        log_event(
            self.logger,
            f"{action}",
            agent=self.name,
            step=step,
            score=score,
            decision=decision,
        )

    def run_tracked(self, step: str):
        """Context manager combining metrics timing for a pipeline step."""
        if self.metrics is not None:
            return self.metrics.track(self.name, step)
        return _NullContext()


class _NullContext:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False
