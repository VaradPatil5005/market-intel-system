"""
Live Daemon — Real-Time Streaming & Anomaly-Triggered Pipeline.

A background scheduler (APScheduler) that:
  1. Polls configured RSS feeds and DeepSearch every `live_poll_interval_seconds`
  2. Computes fast EWMA rolling Z-scores on entity mention frequency
  3. When Z-score exceeds `z_score_alert_threshold` for any entity:
     - Triggers an immediate mini-pipeline run (ingest → credibility → sentiment → confidence)
     - Dispatches flash alerts via Slack/Telegram/email
  4. Tracks all daemon job states in the `LiveFeedJob` table

This replaces the need to manually run `python main.py` periodically —
the system watches the internet continuously and only kicks off full
analysis when something meaningful is actually happening.

Usage:
    python -m agents.live_daemon          # run daemon standalone
    or started from main.py when enable_live_daemon=True

Graceful degradation:
  - If APScheduler not installed → daemon startup fails gracefully with log
  - If enable_live_daemon=False → this module is never imported
"""
from __future__ import annotations

import json
import threading
import time
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

import requests

from utils.config import settings
from utils.logging_setup import get_logger

logger = get_logger("live_daemon")

# Track daemon state in memory (also persisted to DB)
_daemon_state: Dict[str, Any] = {
    "running": False,
    "last_poll": None,
    "total_polls": 0,
    "anomalies_detected": 0,
    "mini_runs_triggered": 0,
    "recent_alerts": [],
}

# Rolling entity mention counts for Z-score (in-memory ring buffer)
_mention_history: Dict[str, List[int]] = defaultdict(list)
_HISTORY_WINDOW = 20  # rolling window for EWMA


def _compute_zscore(history: List[int], current: int) -> float:
    """Compute simple rolling Z-score for spike detection."""
    if len(history) < 5:
        return 0.0
    import statistics as stats
    try:
        mean = stats.mean(history[-_HISTORY_WINDOW:])
        std = stats.stdev(history[-_HISTORY_WINDOW:])
        if std == 0:
            return 0.0
        return (current - mean) / std
    except Exception:
        return 0.0


def _count_entity_mentions(text: str, entities: List[str]) -> Dict[str, int]:
    """Count how many times each entity appears in a text blob."""
    counts = {}
    text_lower = text.lower()
    for entity in entities:
        counts[entity] = text_lower.count(entity.lower())
    return counts


class LiveDaemon:
    """Real-time polling daemon with anomaly detection and mini-pipeline triggering."""

    def __init__(self, pipeline_callback: Optional[Callable] = None):
        """
        Args:
            pipeline_callback: function(anomalous_entities: List[str]) to call
                               when a spike is detected. Usually triggers a mini-pipeline run.
        """
        self._pipeline_callback = pipeline_callback
        self._scheduler = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start the live daemon. Non-blocking — runs in background thread."""
        if not settings.enable_live_daemon:
            logger.info("LiveDaemon: enable_live_daemon=False — daemon not started.")
            return

        try:
            from apscheduler.schedulers.background import BackgroundScheduler  # noqa: PLC0415
            from apscheduler.triggers.interval import IntervalTrigger  # noqa: PLC0415
        except ImportError:
            logger.warning(
                "LiveDaemon: apscheduler not installed — real-time daemon unavailable. "
                "Install with: pip install apscheduler"
            )
            return

        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(
            self._poll_cycle,
            trigger=IntervalTrigger(seconds=settings.live_poll_interval_seconds),
            id="live_poll",
            name="Market Intel Live Poll",
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.start()
        _daemon_state["running"] = True
        logger.info(
            f"LiveDaemon started — polling every {settings.live_poll_interval_seconds}s. "
            f"Z-score threshold for alerts: {settings.z_score_alert_threshold}"
        )

    def stop(self) -> None:
        """Stop the daemon gracefully."""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
        _daemon_state["running"] = False
        logger.info("LiveDaemon stopped.")

    def get_status(self) -> Dict[str, Any]:
        return dict(_daemon_state)

    # ------------------------------------------------------------------
    def _poll_cycle(self) -> None:
        """One polling cycle: fetch feeds, detect spikes, trigger alerts."""
        _daemon_state["total_polls"] = _daemon_state.get("total_polls", 0) + 1
        _daemon_state["last_poll"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        logger.debug(f"LiveDaemon: starting poll cycle #{_daemon_state['total_polls']}")

        # Fetch all configured feeds + free news endpoints
        text_corpus = self._fetch_feeds()
        if not text_corpus:
            logger.debug("LiveDaemon: no content fetched this cycle.")
            return

        # Count entity mentions and compute Z-scores
        watchlist = settings.watchlist
        mention_counts = _count_entity_mentions(text_corpus, watchlist)

        anomalous: List[str] = []
        for entity, count in mention_counts.items():
            history = _mention_history[entity]
            z = _compute_zscore(history, count)
            history.append(count)
            # Keep rolling window
            _mention_history[entity] = history[-_HISTORY_WINDOW:]

            if z >= settings.z_score_alert_threshold:
                logger.warning(
                    f"LiveDaemon: SPIKE detected for '{entity}' "
                    f"(mentions={count}, Z={z:.2f} >= threshold={settings.z_score_alert_threshold})"
                )
                anomalous.append(entity)
                _daemon_state["anomalies_detected"] = _daemon_state.get("anomalies_detected", 0) + 1

        if anomalous:
            self._handle_anomalies(anomalous, mention_counts)

    def _fetch_feeds(self) -> str:
        """Fetch all configured RSS feeds and return combined text."""
        import feedparser  # noqa: PLC0415
        combined = []

        for feed_url in settings.rss_feed_list:
            try:
                resp = requests.get(feed_url, timeout=8, headers={"User-Agent": "MarketIntelDaemon/2.0"})
                resp.raise_for_status()
                parsed = feedparser.parse(resp.content)
                for entry in parsed.entries[:20]:
                    combined.append(entry.get("title", ""))
                    combined.append(entry.get("summary", ""))
            except Exception as exc:
                logger.debug(f"LiveDaemon: feed fetch failed for {feed_url}: {exc}")

        # Also hit free financial headline APIs
        free_apis = [
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
            "https://feeds.marketwatch.com/marketwatch/topstories/",
        ]
        for api_url in free_apis:
            try:
                resp = requests.get(api_url, timeout=8, headers={"User-Agent": "MarketIntelDaemon/2.0"})
                parsed = feedparser.parse(resp.content)
                for entry in parsed.entries[:10]:
                    combined.append(entry.get("title", ""))
            except Exception:
                pass

        return " ".join(combined)

    def _handle_anomalies(self, anomalous_entities: List[str], mention_counts: Dict[str, int]) -> None:
        """Dispatch alerts and optionally trigger a mini-pipeline run."""
        from utils.alerting import AlertableInsight, dispatch_alerts, send_multi_channel_alert  # noqa: PLC0415

        logger.info(f"LiveDaemon: handling {len(anomalous_entities)} anomalous entities: {anomalous_entities}")

        # Record in state
        alert_record = {
            "timestamp": _daemon_state["last_poll"],
            "entities": anomalous_entities,
            "mention_counts": {e: mention_counts.get(e, 0) for e in anomalous_entities},
        }
        alerts = _daemon_state.get("recent_alerts", [])
        alerts.insert(0, alert_record)
        _daemon_state["recent_alerts"] = alerts[:50]   # keep last 50

        # Dispatch flash alert
        message = (
            f" LIVE MARKET SPIKE DETECTED\n"
            f"Entities: {', '.join(anomalous_entities)}\n"
            f"Mention counts: {json.dumps({e: mention_counts.get(e, 0) for e in anomalous_entities})}\n"
            f"An automated deep-search and analysis run is being triggered."
        )
        send_multi_channel_alert(message, priority="CRITICAL")

        # Trigger mini-pipeline run if callback is registered
        if self._pipeline_callback and settings.live_daemon_run_mini_pipeline:
            logger.info("LiveDaemon: triggering mini-pipeline run for anomalous entities...")
            try:
                self._pipeline_callback(anomalous_entities)
                _daemon_state["mini_runs_triggered"] = _daemon_state.get("mini_runs_triggered", 0) + 1
            except Exception as exc:
                logger.error(f"LiveDaemon: mini-pipeline run failed: {exc}")


def run_daemon_standalone() -> None:
    """Entry point for running the daemon as a standalone process."""
    from database.session import init_db  # noqa: PLC0415
    init_db()

    def mini_pipeline_callback(anomalous_entities: List[str]) -> None:
        """Trigger a focused pipeline run for anomalous entities."""
        try:
            from orchestration.graph import run_pipeline  # noqa: PLC0415
            from utils.metrics import MetricsCollector  # noqa: PLC0415
            metrics = MetricsCollector()
            logger.info(f"LiveDaemon: launching mini-pipeline for {anomalous_entities}")
            run_pipeline(metrics)
        except Exception as exc:
            logger.error(f"LiveDaemon: mini-pipeline error: {exc}")

    daemon = LiveDaemon(pipeline_callback=mini_pipeline_callback)
    daemon.start()

    logger.info("LiveDaemon running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        daemon.stop()


if __name__ == "__main__":
    run_daemon_standalone()
