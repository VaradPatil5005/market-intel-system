"""
Confidence Scoring Agent.

Synthesizes remaining insight categories (sentiment shifts, competitor
movements, risk signals) from the upstream analytical results, then
assigns every insight (including RAG insights generated upstream) a
confidence score based on:
  - source_quality:    average credibility of contributing sources
  - agreement:         consistency of signal across sources/entities
  - recency:           how fresh the underlying data is
  - completeness:      how much supporting data backs the insight

Insights below `settings.low_confidence_threshold` are flagged for
human review.
"""
from __future__ import annotations

import json
import statistics
from typing import List

from agents.base import BaseAgent
from database.models import ConfidenceScore, Entity, Insight, RawSource, SentimentResult, TrendResult
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id

insight_repo = Repository(Insight)
confidence_repo = Repository(ConfidenceScore)


class ConfidenceScoringAgent(BaseAgent):
    name = "confidence_agent"

    def run(
        self,
        session: Session,
        sources: List[RawSource],
        entities: List[Entity],
        sentiment_results: List[SentimentResult],
        trend_results: List[TrendResult],
        rag_insights: List[Insight],
    ) -> tuple[List[ConfidenceScore], List[Insight]]:
        with self.run_tracked("score_confidence"):
            synthesized = self._synthesize_insights(session, entities, sentiment_results, trend_results)
            all_insights = synthesized + rag_insights

            accepted_sources = [s for s in sources if not s.is_rejected]
            avg_source_quality = (
                round(statistics.mean(s.credibility_score or 0.5 for s in accepted_sources), 4)
                if accepted_sources
                else 0.5
            )

            scores: List[ConfidenceScore] = []
            for insight in all_insights:
                agreement = self._agreement_component(insight, sentiment_results, trend_results)
                recency = 0.9 if accepted_sources else 0.5
                completeness = self._completeness_component(insight)

                score = round(
                    0.35 * avg_source_quality + 0.3 * agreement + 0.2 * recency + 0.15 * completeness,
                    4,
                )
                is_flagged = score < settings.low_confidence_threshold
                flag_reason = "low confidence — conflicting or sparse evidence" if is_flagged else None

                record = ConfidenceScore(
                    id=new_id("conf"),
                    insight_id=insight.id,
                    score=score,
                    source_quality_component=avg_source_quality,
                    agreement_component=agreement,
                    recency_component=recency,
                    completeness_component=completeness,
                    is_flagged=int(is_flagged),
                    flag_reason=flag_reason,
                    created_at=iso_now(),
                )
                confidence_repo.insert(session, record)
                scores.append(record)
                if self.metrics:
                    self.metrics.record_confidence(score)

            session.flush()
            flagged = [s for s in scores if s.is_flagged]

            self.audit(
                session,
                step="score_confidence",
                action="scored_insight_confidence",
                output_summary={"insights_scored": len(scores), "flagged_low_confidence": len(flagged)},
                score=round(statistics.mean(s.score for s in scores), 4) if scores else None,
            )
            return scores

    # ------------------------------------------------------------------
    def _synthesize_insights(
        self,
        session: Session,
        entities: List[Entity],
        sentiment_results: List[SentimentResult],
        trend_results: List[TrendResult],
    ) -> List[Insight]:
        insights: List[Insight] = []

        # Sentiment-shift insights: entities with notably positive/negative average sentiment
        by_entity: dict[str, List[SentimentResult]] = {}
        for r in sentiment_results:
            if r.entity_id:
                by_entity.setdefault(r.entity_id, []).append(r)

        entity_by_id = {e.id: e for e in entities}
        for entity_id, results in by_entity.items():
            avg_polarity = round(statistics.mean(r.polarity_score for r in results), 4)
            if abs(avg_polarity) < 0.2:
                continue
            entity_name = entity_by_id.get(entity_id).canonical_name if entity_id in entity_by_id else "Unknown"
            direction = "improving" if avg_polarity > 0 else "deteriorating"
            insight = Insight(
                id=new_id("insight"),
                category="sentiment",
                text=f"Sentiment around {entity_name} is {direction} (avg polarity {avg_polarity}) across {len(results)} source(s).",
                related_entity_id=entity_id,
                supporting_source_ids=json.dumps([r.source_id for r in results if r.source_id]),
                created_at=iso_now(),
            )
            insight_repo.insert(session, insight)
            insights.append(insight)

        # Trend / risk insights
        for trend in trend_results:
            if trend.trend_label == "stable":
                continue
            category = "risk" if trend.trend_label in ("falling", "anomalous") else "trend"
            insight = Insight(
                id=new_id("insight"),
                category=category,
                text=(
                    f"Topic '{trend.topic}' is {trend.trend_label} "
                    f"({trend.change_pct:+.1f}% vs. historical average)."
                ),
                related_entity_id=None,
                supporting_source_ids=None,
                created_at=iso_now(),
            )
            insight_repo.insert(session, insight)
            insights.append(insight)

        # Competitor-movement insight: entities with high mention counts this run
        top_entities = sorted(entities, key=lambda e: e.mention_count, reverse=True)[:3]
        if len(top_entities) >= 2:
            names = ", ".join(e.canonical_name for e in top_entities)
            insight = Insight(
                id=new_id("insight"),
                category="competitor",
                text=f"Highest market-activity entities this cycle: {names}.",
                related_entity_id=top_entities[0].id,
                supporting_source_ids=None,
                created_at=iso_now(),
            )
            insight_repo.insert(session, insight)
            insights.append(insight)

        session.flush()
        return insights

    def _agreement_component(
        self, insight: Insight, sentiment_results: List[SentimentResult], trend_results: List[TrendResult]
    ) -> float:
        if insight.category == "sentiment" and insight.related_entity_id:
            related = [r.polarity_score for r in sentiment_results if r.entity_id == insight.related_entity_id]
            if len(related) <= 1:
                return 0.6
            spread = max(related) - min(related)
            return round(max(0.2, 1 - spread), 4)
        if insight.category in ("trend", "risk"):
            return 0.75
        return 0.65

    def _completeness_component(self, insight: Insight) -> float:
        has_support = bool(insight.supporting_source_ids and insight.supporting_source_ids != "[]")
        has_entity = bool(insight.related_entity_id)
        return 0.5 + 0.25 * has_support + 0.25 * has_entity
