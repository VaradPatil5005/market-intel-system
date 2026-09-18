"""
Multi-Channel Alerting Engine — v2.

v1: Slack/generic JSON webhook only.
v2 additions:
  - Telegram bot dispatch (telegram_bot_token + telegram_chat_id)
  - Email via SMTP (email_smtp_* settings)
  - Priority tiering: CRITICAL / HIGH / LOW
  - send_multi_channel_alert() for use by LiveDaemon

Channel dispatch logic by priority:
  CRITICAL → all configured channels (Slack + Telegram + Email)
  HIGH     → Slack + Telegram only
  LOW      → log only (no network calls)

All channels are opt-in via settings. If a channel's settings are empty,
it is silently skipped — the pipeline never crashes due to alerting.

Alert conditions (unchanged from v1):
  - Any insight flagged for human review (is_flagged=True)
  - Any HIGH-confidence risk insight above alert_confidence_threshold
"""
from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.mime.text import MIMEText
from typing import List, Optional

import requests

from utils.config import settings
from utils.logging_setup import get_logger

logger = get_logger("utils.alerting")

PRIORITY_CRITICAL = "CRITICAL"
PRIORITY_HIGH = "HIGH"
PRIORITY_LOW = "LOW"


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
    """Sends (or logs) a single alert for an insight.
    Returns True if any real network send was attempted and succeeded."""
    message = f"[Market Intel Alert] {reason}\nCategory: {item.category}\n{item.text}"
    priority = PRIORITY_CRITICAL if item.is_flagged else PRIORITY_HIGH
    return send_multi_channel_alert(message, priority=priority)


def send_multi_channel_alert(message: str, priority: str = PRIORITY_HIGH) -> bool:
    """Dispatch an alert message to all channels appropriate for the given priority.

    Args:
        message:  Human-readable alert text
        priority: CRITICAL | HIGH | LOW

    Returns:
        True if at least one channel dispatch succeeded.
    """
    if priority == PRIORITY_LOW:
        logger.info(f"ALERT [LOW priority — log only]: {message}")
        return False

    any_success = False

    # Slack (v1 + v2 dedicated URL)
    webhook_url = settings.slack_webhook_url or settings.alert_webhook_url
    if webhook_url:
        success = _send_slack(message, webhook_url)
        any_success = any_success or success

    # Telegram (v2)
    if settings.telegram_bot_token and settings.telegram_chat_id:
        success = _send_telegram(message)
        any_success = any_success or success

    # Email (v2 — CRITICAL only)
    if priority == PRIORITY_CRITICAL and settings.email_smtp_host and settings.email_recipients:
        success = _send_email(message)
        any_success = any_success or success

    if not any_success:
        logger.info(f"ALERT (no channels configured — log only) [{priority}]: {message}")

    return any_success


def _send_slack(message: str, webhook_url: str) -> bool:
    try:
        resp = requests.post(
            webhook_url,
            json={"text": message},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("Alert dispatched to Slack successfully.")
        return True
    except requests.RequestException as exc:
        logger.warning(f"Slack alert failed: {exc}")
        return False


def _send_telegram(message: str) -> bool:
    """Send message via Telegram Bot API."""
    try:
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        resp = requests.post(
            url,
            json={
                "chat_id": settings.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML",
            },
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("Alert dispatched to Telegram successfully.")
        return True
    except Exception as exc:
        logger.warning(f"Telegram alert failed: {exc}")
        return False


def _send_email(message: str) -> bool:
    """Send alert via SMTP email."""
    try:
        smtp_host = settings.email_smtp_host
        smtp_port = settings.email_smtp_port
        smtp_user = settings.email_smtp_user
        smtp_pass = settings.email_smtp_password
        recipients = settings.email_recipients

        if not recipients:
            return False

        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = "[Market Intel] CRITICAL Alert"
        msg["From"] = smtp_user or "market-intel@noreply.com"
        msg["To"] = ", ".join(recipients)

        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as smtp:
            smtp.ehlo()
            if smtp_port in (587, 465):
                smtp.starttls()
            if smtp_user and smtp_pass:
                smtp.login(smtp_user, smtp_pass)
            smtp.sendmail(msg["From"], recipients, msg.as_string())

        logger.info(f"Alert email sent to {recipients}.")
        return True
    except Exception as exc:
        logger.warning(f"Email alert failed: {exc}")
        return False


def dispatch_alerts(items: List[AlertableInsight]) -> int:
    """Evaluate every item and dispatch alerts for the ones that qualify.
    Returns the count of alerts that qualified."""
    fired = 0
    for item in items:
        reason = should_alert(item)
        if reason:
            send_alert(item, reason)
            fired += 1
    return fired
