"""
Multi-Channel Alerting Engine (Tier 3).

Fires a webhook POST for high-impact events so a human doesn't have to
go read the report to notice something worth their attention. Works
with any generic JSON webhook endpoint — Slack incoming webhooks, MS
Teams connectors, and most "custom webhook" email-bridge services all
accept a POST with a `text` field, which is what this sends.

Alert conditions (see `should_alert` for the exact logic):
  - Any insight flagged for human review (`is_flagged=True`) — these are
    insights the confidence-scoring agent itself says are low-confidence
    / conflicting, so a human should look sooner rather than later.
  - Any HIGH-confidence insight in the "risk" category above
    `settings.alert_confidence_threshold` — i.e. the system is quite
    sure something risk-relevant is happening, which is exactly the
    kind of high-certainty, high-impact event alerting exists for.

If `settings.alert_webhook_url` is empty (the default), this module
never makes a network call — it just logs what *would* have been sent,
so the pipeline is fully usable with alerting "configured but off".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import requests

from utils.config import settings
from utils.logging_setup import get_logger

logger = get_logger("utils.alerting")


@dataclass
class AlertableInsight:
    insight_id: str
    category: str
    text: str
    confidence_score: float
    is_flagged: bool


def should_alert(item: AlertableInsight) -> Optional[str]:
    """Returns a human-readable reason string if this insight should
    trigger an alert, or None if it shouldn't."""
    if item.is_flagged:
        return "flagged for human review (low/conflicting confidence)"
    if item.category == "risk" and item.confidence_score >= settings.alert_confidence_threshold:
        return f"high-confidence risk signal ({item.confidence_score:.2f} >= {settings.alert_confidence_threshold})"
    return None


def send_alert(item: AlertableInsight, reason: str) -> bool:
    """Sends (or logs, if no webhook configured) a single alert.
    Returns True if a real network send was attempted and succeeded,
    False otherwise (including the "not configured" case)."""
    message = f"[Market Intel Alert] {reason}\nCategory: {item.category}\n{item.text}"

    if not settings.alert_webhook_url:
        logger.info(f"ALERT (webhook not configured, logging only): {message}")
        return False

    try:
        response = requests.post(
            settings.alert_webhook_url,
            json={"text": message},
            timeout=10,
        )
        response.raise_for_status()
        logger.info(f"Alert sent successfully for insight {item.insight_id}")
        return True
    except requests.RequestException as exc:
        logger.warning(f"Alert webhook failed for insight {item.insight_id}: {exc}")
        return False


def dispatch_alerts(items: List[AlertableInsight]) -> int:
    """Evaluates every item and sends alerts for the ones that qualify.
    Returns the count of alerts that qualified (regardless of whether the
    webhook call itself succeeded) so the caller can log/report totals."""
    fired = 0
    for item in items:
        reason = should_alert(item)
        if reason:
            send_alert(item, reason)
            fired += 1
    return fired
