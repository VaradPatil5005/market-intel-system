"""
Trend Analysis Agent.

Detects recurring themes / keyword spikes in the current ingestion
batch and compares them against history stored in `trend_results`,
producing rising/falling/stable/new/anomalous labels.

Tier 1 upgrade: anomaly detection now uses an Exponentially Weighted
Moving Average (EWMA) + rolling standard deviation per topic (via
pandas) instead of a flat percentage-change rule. EWMA is used because
it weights recent runs more heavily than old ones, which suits
fast-moving market news better than a plain historical mean. A topic
is flagged `is_anomalous=True` when its z-score
(`(current - ewma_mean) / ewma_std`) exceeds
`settings.trend_anomaly_z_threshold` (2.0 by default = ~2 standard
deviations, the conventional statistical anomaly threshold).

The original percentage-change labels (rising/falling/stable) are kept
for readability in the report, and are now derived from whichever
signal is available — z-score once there's enough history (>=3 prior
observations), percentage-change before that.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List

import pandas as pd

from agents.base import BaseAgent
from database.models import RawSource, TrendResult
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id

trend_repo = Repository(TrendResult)

WORD_RE = re.compile(r"[a-zA-Z]{4,}")
STOPWORDS = {
    "this", "that", "with", "from", "have", "will", "their", "about", "which", "there",
    "would", "could", "should", "after", "into", "over", "also", "been", "were", "when",
}
RISING_CHANGE_PCT = 20.0
FALLING_CHANGE_PCT = -20.0
MIN_OBSERVATIONS_FOR_ZSCORE = 3


class TrendAgent(BaseAgent):
    name = "trend_agent"

    def run(self, session: Session, sources: List[RawSource], window_days: int = 7) -> List[TrendResult]:
        with self.run_tracked("analyze_trends"):
            current_counts = self._keyword_counts(sources)
            history_by_topic = self._history_by_topic(session)

            results: List[TrendResult] = []
            for topic, current_score in current_counts.most_common(15):
                history = history_by_topic.get(topic, [])
                historical_avg = round(sum(history) / len(history), 4) if history else None
                change_pct = self._change_pct(current_score, historical_avg)

                ewma_mean, ewma_std, z_score = self._ewma_stats(history, current_score)
                is_anomalous = bool(
                    z_score is not None and abs(z_score) >= settings.trend_anomaly_z_threshold
                )
                label = self._label_for(change_pct, historical_avg, z_score, is_anomalous)

                result = TrendResult(
                    id=new_id("trend"),
                    topic=topic,
                    trend_label=label,
                    current_score=float(current_score),
                    historical_avg=historical_avg,
                    change_pct=change_pct,
                    window_days=window_days,
                    ewma_mean=ewma_mean,
                    ewma_std=ewma_std,
                    z_score=z_score,
                    is_anomalous=int(is_anomalous),
                    created_at=iso_now(),
                )
                trend_repo.insert(session, result)
                results.append(result)

            session.flush()
            rising = [r for r in results if r.trend_label in ("rising", "anomalous")]

            self.audit(
                session,
                step="analyze_trends",
                action="detected_trends",
                output_summary={
                    "topics_tracked": len(results),
                    "rising_or_anomalous": len(rising),
                    "anomalous_count": sum(1 for r in results if r.is_anomalous),
                },
            )
            return results

    # ------------------------------------------------------------------
    def _keyword_counts(self, sources: List[RawSource]) -> Counter:
        counts: Counter = Counter()
        for source in sources:
            if source.is_rejected:
                continue
            text = f"{source.title} {source.content}".lower()
            words = [w for w in WORD_RE.findall(text) if w not in STOPWORDS]
            counts.update(words)
        return counts

    def _history_by_topic(self, session: Session) -> Dict[str, List[float]]:
        """All prior runs' current_score for each topic, oldest -> newest.

        (SQLite doesn't guarantee insertion order without an explicit
        ORDER BY, so we sort by created_at to make the EWMA's recency
        weighting actually mean something.)
        """
        history = sorted(trend_repo.all(session), key=lambda r: r.created_at)
        buckets: Dict[str, List[float]] = {}
        for row in history:
            buckets.setdefault(row.topic, []).append(row.current_score)
        return buckets

    def _change_pct(self, current: float, historical_avg: float | None) -> float:
        if not historical_avg:
            return 100.0 if current > 0 else 0.0
        return round(((current - historical_avg) / historical_avg) * 100, 2)

    def _ewma_stats(self, history: List[float], current_score: float):
        """Returns (ewma_mean, ewma_std, z_score) for this topic, or (None, None, None)
        if there isn't enough history yet to compute a meaningful z-score."""
        if len(history) < MIN_OBSERVATIONS_FOR_ZSCORE:
            return None, None, None

        series = pd.Series(history)
        ewma = series.ewm(span=settings.trend_ewma_span, adjust=False).mean()
        ewma_mean = float(ewma.iloc[-1])
        # rolling std of the raw series as the volatility estimate paired with the EWMA mean
        ewma_std = float(series.std(ddof=0)) or 1e-6
        z_score = round((current_score - ewma_mean) / (ewma_std + 1e-6), 4)
        return round(ewma_mean, 4), round(ewma_std, 4), z_score

    def _label_for(
        self,
        change_pct: float,
        historical_avg: float | None,
        z_score: float | None,
        is_anomalous: bool,
    ) -> str:
        if historical_avg is None:
            return "new"
        if is_anomalous:
            return "anomalous"
        if z_score is not None:
            # enough history for statistical comparison — prefer z-score-driven labeling
            if z_score >= 1.0:
                return "rising"
            if z_score <= -1.0:
                return "falling"
            return "stable"
        # not enough history yet for z-score — fall back to simple percentage change
        if change_pct >= RISING_CHANGE_PCT:
            return "rising"
        if change_pct <= FALLING_CHANGE_PCT:
            return "falling"
        return "stable"
