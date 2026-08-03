"""
Structured logging for agent decisions, orchestration steps, and errors.

Logs go to both console (human-readable) and a JSON-lines file
(machine-readable, used for the audit trail / observability dashboard).
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from utils.config import settings


class JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)-8s %(name)-24s | %(message)s", "%H:%M:%S")
    )

    log_file = Path(settings.log_dir) / "agent_events.jsonl"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(JsonLineFormatter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def log_event(
    logger: logging.Logger,
    message: str,
    *,
    agent: Optional[str] = None,
    step: Optional[str] = None,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    """Emit a structured log line carrying audit-relevant metadata."""
    extra_fields = {"agent": agent, "step": step, **fields}
    extra_fields = {k: v for k, v in extra_fields.items() if v is not None}
    logger.log(level, message, extra={"extra_fields": extra_fields})
