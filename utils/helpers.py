"""Generic, reusable helpers shared across agents and modules."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, TypeVar

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

T = TypeVar("T")


# --------------------------------------------------------------------------
# IDs / time
# --------------------------------------------------------------------------
def new_id(prefix: str = "") -> str:
    suffix = uuid.uuid4().hex[:12]
    return f"{prefix}_{suffix}" if prefix else suffix


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


# --------------------------------------------------------------------------
# Text normalization
# --------------------------------------------------------------------------
def normalize_text(text: Optional[str]) -> str:
    """Collapse whitespace, strip control characters, lowercase-insensitive trim."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)  # strip stray HTML
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_entity_name(name: str) -> str:
    """Normalize a candidate entity string for fuzzy-duplicate matching."""
    name = normalize_text(name).lower()
    name = re.sub(r"[^\w\s]", "", name)
    suffixes = (" inc", " corp", " corporation", " ltd", " llc", " co", " plc")
    for suf in suffixes:
        if name.endswith(suf):
            name = name[: -len(suf)]
    return name.strip()


def slugify(text: str) -> str:
    text = normalize_text(text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "item"


# --------------------------------------------------------------------------
# Date parsing
# --------------------------------------------------------------------------
def parse_date(value: Any) -> datetime:
    """Best-effort parse of a date/time value from feeds, APIs, or mock data."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if value is None:
        return utc_now()
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return utc_now()
    if isinstance(value, str):
        candidates = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%a, %d %b %Y %H:%M:%S %z",
        ]
        for fmt in candidates:
            try:
                dt = datetime.strptime(value, fmt)
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return utc_now()


# --------------------------------------------------------------------------
# Retry wrapper
# --------------------------------------------------------------------------
def retry_wrapper(max_attempts: int = 3, backoff_seconds: float = 2.0, exceptions: tuple = (Exception,)):
    """Return a tenacity retry decorator configured from the given params."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=backoff_seconds, min=backoff_seconds, max=backoff_seconds * 8),
        retry=retry_if_exception_type(exceptions),
        reraise=True,
    )


def safe_call(func: Callable[..., T], *args: Any, default: Optional[T] = None, **kwargs: Any) -> Optional[T]:
    """Call func, swallow exceptions, and return a fallback value instead."""
    try:
        return func(*args, **kwargs)
    except Exception:
        return default


# --------------------------------------------------------------------------
# JSON / file utilities
# --------------------------------------------------------------------------
def to_json(obj: Any) -> str:
    return json.dumps(obj, default=str, ensure_ascii=False)


def write_json(path: Path | str, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str, ensure_ascii=False), encoding="utf-8")


def read_json(path: Path | str) -> Any:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_dir(path: Path | str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def chunked(items: list, size: int) -> Iterable[list]:
    for i in range(0, len(items), size):
        yield items[i : i + size]
