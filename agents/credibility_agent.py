"""
Source Credibility Agent.

Scores each raw source on reliability, recency, domain authority, and
historical trust, then down-ranks or rejects low-quality sources.
Fully rule-based and explainable — no external services required.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List
from urllib.parse import urlparse

from agents.base import BaseAgent
from database.models import RawSource
from database.session import Session
from utils.config import settings
from utils.helpers import parse_date

# Simple, explainable domain-trust table. Unknown domains get a neutral score.
DOMAIN_TRUST: Dict[str, float] = {
    "reuters.com": 0.95,
    "bloomberg.com": 0.93,
    "wsj.com": 0.92,
    "ft.com": 0.92,
    "apnews.com": 0.9,
    "cnbc.com": 0.85,
    "techcrunch.com": 0.8,
    "theverge.com": 0.78,
    "mock-source.local": 0.7,  # bundled seed data
}
DEFAULT_DOMAIN_TRUST = 0.6

REJECT_BELOW = 0.35
DOWNRANK_BELOW = 0.5


class CredibilityAgent(BaseAgent):
    name = "credibility_agent"

    def run(self, session: Session, sources: List[RawSource]) -> List[RawSource]:
        with self.run_tracked("score_credibility"):
            seen_titles: Dict[str, int] = {}
            for source in sources:
                domain_score = self._domain_score(source.url, source.source_name)
                recency_score = self._recency_score(source.published_at)
                duplicate_penalty = self._duplicate_penalty(source.title, seen_titles)
                completeness_score = self._completeness_score(source)

                score = round(
                    0.4 * domain_score
                    + 0.25 * recency_score
                    + 0.2 * completeness_score
                    - duplicate_penalty,
                    4,
                )
                score = max(0.0, min(1.0, score))

                explanation = (
                    f"domain={domain_score:.2f}, recency={recency_score:.2f}, "
                    f"completeness={completeness_score:.2f}, duplicate_penalty={duplicate_penalty:.2f}"
                )

                source.credibility_score = score
                source.credibility_explanation = explanation
                source.is_rejected = int(score < REJECT_BELOW)

            session.flush()

            accepted = [s for s in sources if not s.is_rejected]
            rejected = [s for s in sources if s.is_rejected]
            downranked = [s for s in accepted if s.credibility_score < DOWNRANK_BELOW]

            self.audit(
                session,
                step="score_credibility",
                action="scored_sources",
                input_summary={"total_sources": len(sources)},
                output_summary={
                    "accepted": len(accepted),
                    "rejected": len(rejected),
                    "downranked": len(downranked),
                },
            )
            return sources

    # ------------------------------------------------------------------
    def _domain_score(self, url: str | None, source_name: str) -> float:
        if not url:
            return DOMAIN_TRUST.get(source_name.lower(), DEFAULT_DOMAIN_TRUST)
        domain = urlparse(url).netloc.replace("www.", "")
        return DOMAIN_TRUST.get(domain, DEFAULT_DOMAIN_TRUST)

    def _recency_score(self, published_at: str | None) -> float:
        if not published_at:
            return 0.5
        published = parse_date(published_at)
        age_days = (datetime.now(timezone.utc) - published).total_seconds() / 86400
        if age_days <= 1:
            return 1.0
        if age_days <= 7:
            return 0.85
        if age_days <= 30:
            return 0.65
        if age_days <= 90:
            return 0.45
        return 0.25

    def _completeness_score(self, source: RawSource) -> float:
        fields_present = sum(bool(v) for v in (source.title, source.content, source.url, source.published_at))
        return fields_present / 4

    def _duplicate_penalty(self, title: str | None, seen_titles: Dict[str, int]) -> float:
        if not title:
            return 0.0
        key = title.strip().lower()
        seen_titles[key] = seen_titles.get(key, 0) + 1
        occurrences = seen_titles[key]
        return 0.0 if occurrences <= 1 else min(0.3, 0.1 * (occurrences - 1))
