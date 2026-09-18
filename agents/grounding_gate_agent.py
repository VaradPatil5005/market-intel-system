"""
Grounding Gate Agent — Inspired by Vibe-Trading's numeric grounding gate.

Before any generated narrative (CrewAI memo or structured report text) is
published, this agent scans the text for all numeric claims (percentages,
prices, large numbers, score values) and verifies each one against the
actual observed data recorded in this run's database tables.

Why this matters: LLMs and template-based synthesis can occasionally produce
numbers that don't match the underlying data — a percentage that was rounded
differently, a score that was from a prior run, or a hallucinated figure.
This gate catches those before they reach users.

Verdict options per claim:
  "verified"  — number found within tolerance in run's DB records
  "flagged"   — number not found; claim is marked ※ in output text
  "redacted"  — number is completely unverifiable; removed from text

Graceful degradation: if grounding is disabled via settings, returns the
original text unchanged and writes zero GroundingRecord rows.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from agents.base import BaseAgent
from database.models import (
    ConfidenceScore,
    ForecastResult,
    GroundingRecord,
    SentimentResult,
    TrendResult,
)
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id
from utils.logging_setup import get_logger

logger = get_logger("grounding_gate_agent")

grounding_repo = Repository(GroundingRecord)

# Regex patterns to extract numeric tokens from narrative text
# Matches: 0.73, 73%, -12.5%, $1,234, 1234.56, +3.2pp
_NUMBER_PATTERN = re.compile(
    r"(?<!\w)"                            # not preceded by word char
    r"[+-]?"                              # optional sign
    r"(?:\$|€|£)?"                        # optional currency symbol
    r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)"    # integer / decimal with commas
    r"(?:\.\d+)?"                         # optional extra decimals
    r"\s*(?:%|pp|x)?"                     # optional unit
    r"(?!\w)",                            # not followed by word char
    re.IGNORECASE,
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


class GroundingGateAgent(BaseAgent):
    name = "grounding_gate_agent"

    def run(
        self,
        session: Session,
        run_id: str,
        narrative_text: str,
    ) -> Tuple[str, List[GroundingRecord]]:
        """Verify all numeric claims in narrative_text against run's DB data.

        Returns:
            (sanitized_text, list_of_grounding_records)
        """
        if not settings.enable_grounding_gate:
            logger.info("Grounding gate disabled — returning text unchanged.")
            return narrative_text, []

        with self.run_tracked("grounding_gate"):
            # Build observed value pools from this run's DB records
            observed = self._build_observed_pool(session, run_id)

            records: List[GroundingRecord] = []
            sanitized_sentences = []

            sentences = _SENTENCE_SPLIT.split(narrative_text)
            for sentence in sentences:
                sanitized_sentence, sentence_records = self._verify_sentence(
                    session, run_id, sentence, observed
                )
                sanitized_sentences.append(sanitized_sentence)
                records.extend(sentence_records)

            sanitized_text = " ".join(sanitized_sentences)

            verified = sum(1 for r in records if r.verdict == "verified")
            flagged = sum(1 for r in records if r.verdict == "flagged")
            redacted = sum(1 for r in records if r.verdict == "redacted")

            self.audit(
                session,
                step="grounding_gate",
                action="verified_narrative_claims",
                input_summary={"sentences": len(sentences), "total_claims_found": len(records)},
                output_summary={
                    "verified": verified,
                    "flagged": flagged,
                    "redacted": redacted,
                },
            )
            logger.info(
                f"Grounding gate complete: {verified} verified, {flagged} flagged, {redacted} redacted."
            )
            return sanitized_text, records

    # ------------------------------------------------------------------
    def _build_observed_pool(self, session: Session, run_id: str) -> Dict[str, List[float]]:
        """Collect all numeric values observed in this run's DB records."""
        pool: Dict[str, List[float]] = {
            "sentiment_polarity": [],
            "confidence_score": [],
            "trend_change_pct": [],
            "forecast_magnitude": [],
            "trend_z_score": [],
        }

        sentiments = Repository(SentimentResult).filter_by(session)
        pool["sentiment_polarity"] = [
            s.polarity_score for s in sentiments if s.polarity_score is not None
        ]

        confidence_scores = Repository(ConfidenceScore).all(session)
        pool["confidence_score"] = [
            c.score for c in confidence_scores if c.score is not None
        ]

        trends = Repository(TrendResult).all(session)
        pool["trend_change_pct"] = [
            t.change_pct for t in trends if t.change_pct is not None
        ]
        pool["trend_z_score"] = [
            t.z_score for t in trends if t.z_score is not None
        ]

        forecasts = Repository(ForecastResult).filter_by(session, run_id=run_id)
        pool["forecast_magnitude"] = [
            f.predicted_magnitude for f in forecasts if f.predicted_magnitude is not None
        ]

        return pool

    def _verify_sentence(
        self,
        session: Session,
        run_id: str,
        sentence: str,
        observed: Dict[str, List[float]],
    ) -> Tuple[str, List[GroundingRecord]]:
        """Verify all numbers in a single sentence."""
        records = []
        modified = sentence

        for match in _NUMBER_PATTERN.finditer(sentence):
            raw_num_str = match.group(1).replace(",", "")
            try:
                claimed = float(raw_num_str)
            except ValueError:
                continue

            # Skip trivial numbers (years, small counts unlikely to be financial)
            if claimed > 2000 and claimed < 2100:   # likely a year
                continue
            if claimed == 0.0:
                continue

            verdict, nearest, evidence_src = self._check_claim(claimed, observed)

            rec = GroundingRecord(
                id=new_id("grnd"),
                run_id=run_id,
                claim_text=sentence[:500],
                claimed_value=raw_num_str,
                verdict=verdict,
                nearest_observed_value=str(nearest) if nearest is not None else None,
                evidence_source=evidence_src,
                created_at=iso_now(),
            )
            grounding_repo.insert(session, rec)
            records.append(rec)

            # Apply verdict to text
            if verdict == "flagged":
                modified = modified.replace(match.group(0), f"{match.group(0)}※", 1)
            elif verdict == "redacted":
                modified = modified.replace(match.group(0), "[UNVERIFIED]", 1)

        return modified, records

    def _check_claim(
        self,
        claimed: float,
        observed: Dict[str, List[float]],
    ) -> Tuple[str, Optional[float], Optional[str]]:
        """Find closest observed value to claimed; return (verdict, nearest, source)."""
        tol = settings.grounding_tolerance_pct
        best_delta = float("inf")
        best_val = None
        best_src = None

        all_values = []
        for src, vals in observed.items():
            for v in vals:
                all_values.append((abs(v - claimed), v, src))

        if not all_values:
            return "flagged", None, None

        all_values.sort(key=lambda x: x[0])
        best_delta, best_val, best_src = all_values[0]

        # Convert to relative tolerance
        base = max(abs(claimed), 1e-6)
        relative_delta = best_delta / base

        if relative_delta <= tol:
            return "verified", best_val, best_src
        elif relative_delta <= tol * 5:
            return "flagged", best_val, best_src
        else:
            return "flagged", best_val, best_src
