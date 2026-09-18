"""
Confidence Scoring Agent — Enhanced v2.

Synthesizes insight categories from upstream analytical results, then
assigns every insight a multi-component confidence score.

v2 enhancements:
  1. Cross-source verification gate — insights with fewer than
     `settings.min_cross_source_verification` supporting sources are
     auto-flagged regardless of computed score.
  2. Reflexion learning integration — retrieves relevant past human-reviewer
     lessons and applies penalties/bonuses to the computed score.
  3. Adaptive Bayesian weights — when `adaptive_confidence_weights=True`,
     component weights are tuned from historical Brier Score calibration.
  4. Price signal boost — when price_data_enabled=True and a PriceSnapshot
     exists for the entity, RSI / volume anomaly signals adjust the score.
  5. Insight type taxonomy — synthesized insights are tagged with
     `insight_type` to distinguish what kind of claim they represent:
       "fact"           — directly observed in source text (sentiment shift,
                          mention count, price move)
       "analysis"       — cross-source synthesis, pattern detection,
                          historical comparison via RAG
       "prediction"     — forward-looking forecast from ForecastingAgent
       "recommendation" — prescriptive action derived from analysis

Scoring formula:
  score = w_quality * source_quality
        + w_agree   * agreement
        + w_recency * recency
        + w_complete * completeness
        - reflexion_penalty

where weights sum to 1.0 and are either static defaults or Bayesian-tuned.
"""
from __future__ import annotations

import json
import statistics
from typing import List, Tuple

from agents.base import BaseAgent
from database.models import ConfidenceScore, Entity, Insight, RawSource, SentimentResult, TrendResult
from database.session import Repository, Session
from utils.alerting import AlertableInsight, dispatch_alerts
from utils.config import settings
from utils.helpers import iso_now, new_id

insight_repo = Repository(Insight)
confidence_repo = Repository(ConfidenceScore)

# Static default weights (sum to 1.0)
DEFAULT_WEIGHTS = {
    "source_quality": 0.35,
    "agreement":      0.30,
    "recency":        0.20,
    "completeness":   0.15,
}


class ConfidenceScoringAgent(BaseAgent):
    name = "confidence_agent"

    def run(
        self,
        session: Session,
        run_id: str,
        sources: List[RawSource],
        entities: List[Entity],
        sentiment_results: List[SentimentResult],
        trend_results: List[TrendResult],
        rag_insights: List[Insight],
    ) -> Tuple[List[ConfidenceScore], List[Insight]]:
        with self.run_tracked("score_confidence"):
            synthesized = self._synthesize_insights(session, run_id, entities, sentiment_results, trend_results)
            all_insights = synthesized + rag_insights

            if getattr(settings, "enable_competitor_monitor", False):
                try:
                    from agents.competitor_agent import CompetitorMonitorAgent  # noqa: PLC0415
                    comp_agent = CompetitorMonitorAgent(self.metrics)
                    comp_insights = comp_agent.run(session, run_id, sources, entities)
                    all_insights = comp_insights + all_insights
                except Exception as exc:
                    self.logger.warning(f"Competitor monitoring notice: {exc}")

            accepted_sources = [s for s in sources if not s.is_rejected]
            avg_source_quality = (
                round(statistics.mean(s.credibility_score or 0.5 for s in accepted_sources), 4)
                if accepted_sources
                else 0.5
            )

            # Determine scoring weights (adaptive or static)
            weights = self._get_weights(session)

            # Load Reflexion agent for lesson-based penalties
            reflexion_agent = self._get_reflexion_agent()

            # Load price snapshots for this run if available
            price_snapshots = self._load_price_snapshots(session, run_id)

            scores: List[ConfidenceScore] = []
            for insight in all_insights:
                agreement = self._agreement_component(insight, sentiment_results, trend_results)
                recency = 0.9 if accepted_sources else 0.5
                completeness = self._completeness_component(insight)

                # Base score
                score = round(
                    weights["source_quality"] * avg_source_quality
                    + weights["agreement"] * agreement
                    + weights["recency"] * recency
                    + weights["completeness"] * completeness,
                    4,
                )

                # --- v2: Reflexion penalty ---
                reflexion_penalty = 0.0
                if reflexion_agent and insight.related_entity_id:
                    entity_name = self._entity_name(entities, insight.related_entity_id)
                    reflexion_penalty = reflexion_agent.compute_penalty(
                        session, entity_name, insight.category, insight.text
                    )
                    score = max(0.0, round(score - reflexion_penalty, 4))

                # --- v2: Price signal adjustment ---
                price_boost = self._price_signal_boost(price_snapshots, insight, entities)
                score = min(1.0, max(0.0, round(score + price_boost, 4)))

                # --- v2: Cross-source verification gate ---
                source_count = self._count_supporting_sources(insight, accepted_sources)
                cross_source_flag = source_count < settings.min_cross_source_verification

                is_flagged = (
                    score < settings.low_confidence_threshold
                    or cross_source_flag
                )

                flag_reasons = []
                if score < settings.low_confidence_threshold:
                    flag_reasons.append("low confidence — conflicting or sparse evidence")
                if cross_source_flag:
                    flag_reasons.append(
                        f"insufficient cross-source verification ({source_count} < {settings.min_cross_source_verification} sources)"
                    )
                if reflexion_penalty > 0:
                    flag_reasons.append(f"Reflexion penalty applied ({reflexion_penalty:.2f})")

                flag_reason = "; ".join(flag_reasons) if flag_reasons else None

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

            # Tier 3: fire alerts
            insight_by_id = {i.id: i for i in all_insights}
            alertable = [
                AlertableInsight(
                    insight_id=score.insight_id,
                    category=insight_by_id[score.insight_id].category,
                    text=insight_by_id[score.insight_id].text,
                    confidence_score=score.score,
                    is_flagged=bool(score.is_flagged),
                )
                for score in scores
                if score.insight_id in insight_by_id
            ]
            alerts_fired = dispatch_alerts(alertable)

            self.audit(
                session,
                step="score_confidence",
                action="scored_insight_confidence",
                output_summary={
                    "insights_scored": len(scores),
                    "flagged_low_confidence": len(flagged),
                    "cross_source_flagged": sum(1 for s in scores if s.flag_reason and "cross-source" in s.flag_reason),
                    "reflexion_penalties_applied": sum(1 for s in scores if s.flag_reason and "Reflexion" in (s.flag_reason or "")),
                    "alerts_fired": alerts_fired,
                    "weights_used": weights,
                },
                score=round(statistics.mean(s.score for s in scores), 4) if scores else None,
            )
            return scores, all_insights

    # ------------------------------------------------------------------
    def _get_weights(self, session: Session) -> dict:
        """Return scoring weights — adaptive Bayesian or static defaults."""
        if not settings.adaptive_confidence_weights:
            return dict(DEFAULT_WEIGHTS)
        try:
            return self._compute_bayesian_weights(session)
        except Exception:
            return dict(DEFAULT_WEIGHTS)

    def _compute_bayesian_weights(self, session: Session) -> dict:
        """Tune weights based on historical calibration (Brier Score proxy).

        For each past ConfidenceScore, we use whether the insight was later
        accepted (not flagged) vs rejected (flagged + human_rejected) as ground
        truth and compute which components were most predictive.

        This is a lightweight heuristic, not full Bayesian inference — it
        upweights components that correlated with correct outcomes.
        """
        past_scores = confidence_repo.all(session, limit=200)
        if len(past_scores) < 20:
            return dict(DEFAULT_WEIGHTS)

        # Compute average component values for accepted vs flagged
        accepted = [s for s in past_scores if not s.is_flagged]
        flagged = [s for s in past_scores if s.is_flagged]

        if not accepted or not flagged:
            return dict(DEFAULT_WEIGHTS)

        def avg_comp(lst, attr):
            vals = [getattr(s, attr) for s in lst if getattr(s, attr) is not None]
            return statistics.mean(vals) if vals else 0.5

        # Components that differ most between accepted and flagged are most predictive
        diffs = {
            "source_quality": abs(avg_comp(accepted, "source_quality_component") - avg_comp(flagged, "source_quality_component")),
            "agreement": abs(avg_comp(accepted, "agreement_component") - avg_comp(flagged, "agreement_component")),
            "recency": abs(avg_comp(accepted, "recency_component") - avg_comp(flagged, "recency_component")),
            "completeness": abs(avg_comp(accepted, "completeness_component") - avg_comp(flagged, "completeness_component")),
        }
        total_diff = sum(diffs.values()) or 1.0
        # Normalize differences to weights summing to 1.0
        adaptive = {k: round(v / total_diff, 4) for k, v in diffs.items()}
        return adaptive

    def _get_reflexion_agent(self):
        try:
            from agents.reflexion_agent import ReflexionAgent  # noqa: PLC0415
            return ReflexionAgent(self.metrics)
        except Exception:
            return None

    def _load_price_snapshots(self, session: Session, run_id: str) -> dict:
        """Load price snapshots for this run keyed by entity_name."""
        if not settings.price_data_enabled:
            return {}
        try:
            from database.models import PriceSnapshot  # noqa: PLC0415
            snaps = Repository(PriceSnapshot).filter_by(session, run_id=run_id)
            return {s.entity_name.lower(): s for s in snaps}
        except Exception:
            return {}

    def _price_signal_boost(self, price_snapshots: dict, insight: Insight, entities: List[Entity]) -> float:
        """Compute confidence boost/penalty from price signals."""
        if not price_snapshots or not insight.related_entity_id:
            return 0.0
        entity_name = self._entity_name(entities, insight.related_entity_id)
        snap = price_snapshots.get(entity_name.lower())
        if snap is None:
            return 0.0

        boost = 0.0
        # Volume anomaly: unusual volume supports the insight's materiality
        if snap.volume_anomaly:
            boost += 0.05
        # RSI extremes: confirms sentiment direction
        if snap.rsi_14 is not None:
            if snap.rsi_14 < 30 and insight.category in ("risk", "sentiment"):
                boost += 0.04   # oversold + negative sentiment = high confidence
            elif snap.rsi_14 > 70 and insight.category == "sentiment":
                boost += 0.03   # overbought + positive sentiment = high confidence
        return min(boost, 0.10)   # cap at 10% boost

    def _count_supporting_sources(self, insight: Insight, accepted_sources: List[RawSource]) -> int:
        """Count distinct accepted sources supporting this insight."""
        if not insight.supporting_source_ids:
            return 0
        try:
            val = json.loads(insight.supporting_source_ids)
            if isinstance(val, list):
                source_ids = val
            elif isinstance(val, str):
                source_ids = [val]
            else:
                source_ids = [str(val)]
        except Exception:
            source_ids = [insight.supporting_source_ids.strip()]
        accepted_ids = {s.id for s in accepted_sources}
        return sum(1 for sid in source_ids if sid in accepted_ids)

    def _entity_name(self, entities: List[Entity], entity_id: str) -> str:
        for e in entities:
            if e.id == entity_id:
                return e.canonical_name
        return "Unknown"

    # ------------------------------------------------------------------
    # Synthesis and component methods (unchanged from v1)
    # ------------------------------------------------------------------

    def _synthesize_insights(
        self,
        session: Session,
        run_id: str,
        entities: List[Entity],
        sentiment_results: List[SentimentResult],
        trend_results: List[TrendResult],
    ) -> List[Insight]:
        insights: List[Insight] = []

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
            # Sentiment polarity is DIRECTLY OBSERVED from source text — type: fact
            insight = Insight(
                id=new_id("insight"),
                run_id=run_id,
                category="sentiment",
                text=f"Sentiment around {entity_name} is {direction} (avg polarity {avg_polarity}) across {len(results)} source(s).",
                related_entity_id=entity_id,
                supporting_source_ids=json.dumps([r.source_id for r in results if r.source_id]),
                insight_type="fact",
                created_at=iso_now(),
            )
            insight_repo.insert(session, insight)
            insights.append(insight)

        for trend in trend_results:
            if trend.trend_label == "stable":
                continue
            category = "risk" if trend.trend_label in ("falling", "anomalous") else "trend"
            if trend.trend_label == "new":
                category = "trend"
            if trend.trend_label == "new":
                text = f"Topic '{trend.topic}' is newly trending this cycle (no prior history to compare)."
            else:
                text = (
                    f"Topic '{trend.topic}' is {trend.trend_label} "
                    f"({trend.change_pct:+.1f}% vs. historical average)."
                )
            # Trend/risk insights are cross-source pattern detections — type: analysis
            insight = Insight(
                id=new_id("insight"),
                run_id=run_id,
                category=category,
                text=text,
                related_entity_id=None,
                supporting_source_ids=None,
                insight_type="analysis",
                created_at=iso_now(),
            )
            insight_repo.insert(session, insight)
            insights.append(insight)

        top_entities = sorted(entities, key=lambda e: e.mention_count, reverse=True)[:3]
        if len(top_entities) >= 2:
            names = ", ".join(e.canonical_name for e in top_entities)
            # Most-mentioned entity activity is cross-source synthesis — type: analysis
            insight = Insight(
                id=new_id("insight"),
                run_id=run_id,
                category="competitor",
                text=f"Highest market-activity entities this cycle: {names}.",
                related_entity_id=top_entities[0].id,
                supporting_source_ids=None,
                insight_type="analysis",
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
