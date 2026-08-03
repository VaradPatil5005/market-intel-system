"""
Trend Analysis Agent.

Detects recurring themes / keyword spikes in the current ingestion
batch and compares them against the historical average stored in
`trend_results`, producing rising/falling/stable/anomalous labels.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List

from agents.base import BaseAgent
from database.models import RawSource, TrendResult
from database.session import Repository, Session
from utils.helpers import iso_now, new_id

trend_repo = Repository(TrendResult)

WORD_RE = re.compile(r"[a-zA-Z]{4,}")
STOPWORDS = {
    "this", "that", "with", "from", "have", "will", "their", "about", "which", "there",
    "would", "could", "should", "after", "into", "over", "also", "been", "were", "when",
}
ANOMALY_CHANGE_PCT = 80.0
RISING_CHANGE_PCT = 20.0
FALLING_CHANGE_PCT = -20.0


class TrendAgent(BaseAgent):
    name = "trend_agent"

    def run(self, session: Session, sources: List[RawSource], window_days: int = 7) -> List[TrendResult]:
        with self.run_tracked("analyze_trends"):
            current_counts = self._keyword_counts(sources)
            historical_avgs = self._historical_averages(session)

            results: List[TrendResult] = []
            for topic, current_score in current_counts.most_common(15):
                historical_avg = historical_avgs.get(topic)
                change_pct = self._change_pct(current_score, historical_avg)
                label = self._label_for(change_pct, historical_avg)

                result = TrendResult(
                    id=new_id("trend"),
                    topic=topic,
                    trend_label=label,
                    current_score=float(current_score),
                    historical_avg=historical_avg,
                    change_pct=change_pct,
                    window_days=window_days,
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
                output_summary={"topics_tracked": len(results), "rising_or_anomalous": len(rising)},
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

    def _historical_averages(self, session: Session) -> Dict[str, float]:
        history = trend_repo.all(session)
        buckets: Dict[str, List[float]] = {}
        for row in history:
            buckets.setdefault(row.topic, []).append(row.current_score)
        return {topic: sum(vals) / len(vals) for topic, vals in buckets.items() if vals}

    def _change_pct(self, current: float, historical_avg: float | None) -> float:
        if not historical_avg:
            return 100.0 if current > 0 else 0.0
        return round(((current - historical_avg) / historical_avg) * 100, 2)

    def _label_for(self, change_pct: float, historical_avg: float | None) -> str:
        if historical_avg is None:
            return "stable"
        if change_pct >= ANOMALY_CHANGE_PCT:
            return "anomalous"
        if change_pct >= RISING_CHANGE_PCT:
            return "rising"
        if change_pct <= FALLING_CHANGE_PCT:
            return "falling"
        return "stable"
