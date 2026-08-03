"""
Sentiment Analysis Agent.

Scores sentiment for each (source, entity) pair using a compact,
self-contained polarity lexicon (no network/model downloads required —
keeps the pipeline runnable offline). The scoring function is isolated
in `_polarity_of` so it can be swapped for a transformer-based model
later without touching the rest of the agent.
"""
from __future__ import annotations

import re
from typing import Dict, List

from agents.base import BaseAgent
from database.models import Entity, RawSource, SentimentResult
from database.session import Repository, Session
from utils.helpers import iso_now, new_id

sentiment_repo = Repository(SentimentResult)

POSITIVE_WORDS = {
    "beat", "beats", "growth", "surge", "surged", "record", "strong", "profit", "profits",
    "gain", "gains", "upgrade", "upgraded", "outperform", "bullish", "success", "successful",
    "win", "wins", "innovative", "expansion", "rally", "rallied", "soar", "soared", "positive",
    "breakthrough", "partnership", "approval", "approved", "milestone",
}
NEGATIVE_WORDS = {
    "miss", "misses", "decline", "declined", "drop", "dropped", "loss", "losses", "downgrade",
    "downgraded", "underperform", "bearish", "fail", "failure", "failed", "lawsuit", "recall",
    "layoffs", "layoff", "cut", "cuts", "risk", "risks", "risky", "scandal", "investigation",
    "plunge", "plunged", "slump", "warning", "negative", "concern", "concerns", "delay", "delayed",
}
NEGATIONS = {"not", "no", "never", "without"}
WORD_RE = re.compile(r"[a-z']+")


class SentimentAgent(BaseAgent):
    name = "sentiment_agent"

    def run(self, session: Session, sources: List[RawSource], entities: List[Entity]) -> List[SentimentResult]:
        with self.run_tracked("analyze_sentiment"):
            results: List[SentimentResult] = []
            entity_by_name: Dict[str, Entity] = {e.canonical_name.lower(): e for e in entities}

            for source in sources:
                if source.is_rejected:
                    continue
                text = f"{source.title} {source.content}"
                polarity, hits = self._polarity_of(text)
                label = self._label_for(polarity)

                related_entity = self._match_entity(text, entity_by_name)

                result = SentimentResult(
                    id=new_id("sent"),
                    source_id=source.id,
                    entity_id=related_entity.id if related_entity else None,
                    sentiment_label=label,
                    polarity_score=polarity,
                    subject=related_entity.canonical_name if related_entity else source.source_name,
                    explanation=f"matched_terms={hits}" if hits else "no strong sentiment terms detected",
                    created_at=iso_now(),
                )
                sentiment_repo.insert(session, result)
                results.append(result)

            session.flush()
            avg_polarity = round(sum(r.polarity_score for r in results) / len(results), 4) if results else 0.0

            self.audit(
                session,
                step="analyze_sentiment",
                action="scored_sentiment",
                output_summary={"records_scored": len(results), "average_polarity": avg_polarity},
                score=avg_polarity,
            )
            return results

    # ------------------------------------------------------------------
    def _polarity_of(self, text: str) -> tuple[float, List[str]]:
        tokens = WORD_RE.findall(text.lower())
        score = 0
        hits: List[str] = []
        for i, token in enumerate(tokens):
            negate = i > 0 and tokens[i - 1] in NEGATIONS
            if token in POSITIVE_WORDS:
                score += -1 if negate else 1
                hits.append(f"-{token}" if negate else token)
            elif token in NEGATIVE_WORDS:
                score += 1 if negate else -1
                hits.append(f"+{token}" if negate else token)
        if not tokens:
            return 0.0, hits
        normalized = max(-1.0, min(1.0, score / max(5, len(tokens) ** 0.5)))
        return round(normalized, 4), hits

    def _label_for(self, polarity: float) -> str:
        if polarity > 0.15:
            return "positive"
        if polarity < -0.15:
            return "negative"
        return "neutral"

    def _match_entity(self, text: str, entity_by_name: Dict[str, Entity]):
        lowered = text.lower()
        for name, entity in entity_by_name.items():
            if name in lowered:
                return entity
        return None
