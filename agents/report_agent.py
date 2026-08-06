"""
Report Generation Agent.

Assembles a structured market intelligence report from all upstream
insights and confidence scores, then persists it to `report_exports`
(SQL) so it can be picked up by the Power BI export utilities.
"""
from __future__ import annotations

import json
import statistics
from typing import Dict, List

from agents.base import BaseAgent
from database.models import ConfidenceScore, Entity, ForecastResult, Insight, ReportExport
from database.session import Repository, Session
from utils.helpers import iso_now, new_id

report_repo = Repository(ReportExport)


class ReportGenerationAgent(BaseAgent):
    name = "report_agent"

    def run(
        self,
        session: Session,
        run_id: str,
        entities: List[Entity],
        insights: List[Insight],
        confidence_scores: List[ConfidenceScore],
        forecasts: List[ForecastResult] | None = None,
    ) -> ReportExport:
        with self.run_tracked("generate_report"):
            forecasts = forecasts or []
            confidence_by_insight = {c.insight_id: c for c in confidence_scores}

            def section(category: str) -> List[Dict]:
                items = []
                for insight in insights:
                    if insight.category != category:
                        continue
                    conf = confidence_by_insight.get(insight.id)
                    items.append(
                        {
                            "text": insight.text,
                            "confidence": conf.score if conf else None,
                            "flagged": bool(conf.is_flagged) if conf else False,
                        }
                    )
                return items

            key_trends = section("trend")
            competitor_movements = section("competitor")
            sentiment_shifts = section("sentiment")
            risk_signals = section("risk")
            rag_notes = section("rag")

            all_scores = [c.score for c in confidence_scores]
            overall_confidence = round(statistics.mean(all_scores), 4) if all_scores else 0.0
            flagged = [c for c in confidence_scores if c.is_flagged]

            executive_summary = self._build_executive_summary(
                entities, key_trends, sentiment_shifts, risk_signals, overall_confidence
            )

            recommended_actions = self._recommend_actions(risk_signals, sentiment_shifts, overall_confidence)

            predictive_outlook = self._build_predictive_outlook(forecasts)

            report_body = {
                "title": "Market Intelligence Report",
                "generated_at": iso_now(),
                "executive_summary": executive_summary,
                "key_trends": key_trends,
                "competitor_movements": competitor_movements,
                "sentiment_shifts": sentiment_shifts,
                "risk_signals": risk_signals,
                "historical_context": rag_notes,
                "predictive_outlook": predictive_outlook,
                "recommended_actions": recommended_actions,
                "confidence_notes": {
                    "overall_confidence": overall_confidence,
                    "insights_flagged_for_review": len(flagged),
                    "flagged_items": [c.insight_id for c in flagged],
                },
            }

            report = ReportExport(
                id=new_id("report"),
                run_id=run_id,
                report_title=report_body["title"],
                executive_summary=executive_summary,
                full_report_json=json.dumps(report_body, indent=2, default=str),
                approved=0,
                approved_by=None,
                created_at=iso_now(),
            )
            report_repo.insert(session, report)
            session.flush()

            self.audit(
                session,
                step="generate_report",
                action="generated_report",
                output_summary={"overall_confidence": overall_confidence, "flagged": len(flagged)},
                score=overall_confidence,
            )
            return report

    # ------------------------------------------------------------------
    def _build_executive_summary(self, entities, key_trends, sentiment_shifts, risk_signals, overall_confidence) -> str:
        top_entities = ", ".join(e.canonical_name for e in sorted(entities, key=lambda e: e.mention_count, reverse=True)[:5])
        parts = [
            f"This cycle tracked {len(entities)} entities, most active: {top_entities or 'n/a'}.",
            f"{len(key_trends)} notable trend(s) and {len(risk_signals)} risk signal(s) were detected.",
            f"{len(sentiment_shifts)} entities showed a meaningful sentiment shift.",
            f"Overall insight confidence for this run: {overall_confidence:.2f}.",
        ]
        return " ".join(parts)

    def _recommend_actions(self, risk_signals, sentiment_shifts, overall_confidence) -> List[str]:
        actions = []
        if risk_signals:
            actions.append("Review flagged risk signals with the relevant desk before next trading window.")
        negative_shifts = [s for s in sentiment_shifts if "deteriorating" in s["text"]]
        if negative_shifts:
            actions.append("Monitor entities with deteriorating sentiment for follow-on coverage.")
        if overall_confidence < 0.6:
            actions.append("Confidence is below target — seek additional corroborating sources before publishing externally.")
        if not actions:
            actions.append("No immediate action required; continue standard monitoring cadence.")
        return actions

    def _build_predictive_outlook(self, forecasts) -> List[Dict]:
        """Tier 2: renders each entity's forecast as a report line. Entities
        with insufficient history are shown too (transparently, as "not
        enough history yet") rather than omitted, so the report never
        silently hides which entities can't be forecast."""
        items = []
        for f in forecasts:
            if f.model_used == "insufficient_data":
                text = (
                    f"{f.entity_name}: not enough history yet to forecast "
                    f"({f.observations_used} observation(s) recorded so far)."
                )
            else:
                arrow = {"up": "improve", "down": "deteriorate", "neutral": "stay flat"}[f.predicted_direction]
                text = (
                    f"{f.entity_name}: sentiment predicted to {arrow} next cycle "
                    f"(magnitude {f.predicted_magnitude:.2f}, model confidence {f.confidence:.2f}, "
                    f"based on {f.observations_used} observations)."
                )
            items.append(
                {
                    "entity": f.entity_name,
                    "text": text,
                    "direction": f.predicted_direction,
                    "confidence": f.confidence,
                    "model_used": f.model_used,
                }
            )
        return items
