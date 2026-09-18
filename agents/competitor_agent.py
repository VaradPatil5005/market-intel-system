"""
Competitor Signal Monitoring Agent — optional standalone signal extractor.

Scans the raw sources already ingested this run for concrete
"buying signal" / competitive-movement language — pricing changes,
funding rounds, leadership moves, hiring surges, partnership or
product launches — per watchlist entity, and writes each hit as a
`category="competitor"` Insight with the signal type and the source
it came from attached.

Architectural position:
  This agent is NOT wired into the main LangGraph graph by default.
  It operates as an optional standalone signal extractor. There are
  two ways to use it:

  1. **Confidence scoring integration (recommended):**
     `ConfidenceScoringAgent` calls it internally when
     `ENABLE_COMPETITOR_MONITOR=true` in .env, adding competitor
     signals as additional insights before confidence scoring runs.

  2. **Direct invocation:**
     Call `.detect(session, raw_sources, run_id)` directly from any
     scheduled job or ad-hoc script. The method accepts any list of
     RawSource objects — not just the current run's — so it can be
     used independently of the main ingestion cadence.

Design rationale: operates on `raw_sources` already fetched by
`IngestionAgent` this cycle rather than making its own network calls.
This keeps it dependency-free, preserves the pipeline's "degrade
gracefully offline" guarantee, and avoids double-fetching the same
feeds.

This complements (does not replace) the existing high-mention-count
"competitor" insight produced in `confidence_agent.py`; that one
flags *who is active*, this one flags *what specifically happened*.

Off by default — enable with `ENABLE_COMPETITOR_MONITOR=true` in .env
(see `utils/config.py`), so existing pipeline behavior/tests are
unaffected unless a developer opts in.
"""
from __future__ import annotations

import json
import re
from typing import Dict, List

from agents.base import BaseAgent
from database.models import Entity, Insight, RawSource
from database.session import Repository, Session
from utils.helpers import iso_now, new_id

insight_repo = Repository(Insight)

# signal_type -> regex patterns (case-insensitive). Kept intentionally
# simple/transparent (no ML) so every hit is explainable in the audit
# log — swap in a classifier later without changing the call shape.
SIGNAL_PATTERNS: Dict[str, List[str]] = {
    "pricing": [r"\bprice[sd]?\b.{0,20}\b(cut|hike|increase|change|drop)\b", r"\brepricing\b", r"\bnew pricing\b"],
    "funding": [r"\braises?\b.{0,15}\b(million|billion|series [a-e])\b", r"\bfunding round\b", r"\bvaluation of\b"],
    "leadership": [r"\bnames? new (ceo|cfo|cto|coo)\b", r"\bsteps? down as\b", r"\bappoints? .{0,20} as\b"],
    "hiring": [r"\bhiring (spree|surge)\b", r"\bopens? \d+ new (roles|positions)\b", r"\bexpands? (its |the )?team\b"],
    "partnership": [r"\bpartners? with\b", r"\bannounces? partnership\b", r"\bstrategic alliance\b"],
    "product_launch": [r"\blaunches?\b.{0,15}\b(product|platform|feature)\b", r"\bunveils?\b", r"\breleases? (a |its )?new\b"],
}

_COMPILED = {
    signal: [re.compile(p, re.IGNORECASE) for p in patterns] for signal, patterns in SIGNAL_PATTERNS.items()
}


class CompetitorMonitorAgent(BaseAgent):
    name = "competitor_monitor_agent"

    def run(
        self,
        session: Session,
        run_id: str,
        raw_sources: List[RawSource],
        entities: List[Entity],
    ) -> List[Insight]:
        with self.run_tracked("monitor_competitors"):
            insights = self.detect(raw_sources, entities, run_id)
            for insight in insights:
                insight_repo.insert(session, insight)

            self.audit(
                session,
                step="monitor_competitors",
                action="competitor_signals_detected",
                input_summary={"sources_scanned": len(raw_sources)},
                output_summary={"signals_found": len(insights)},
            )
            session.flush()
            return insights

    # ------------------------------------------------------------------
    def detect(self, raw_sources: List[RawSource], entities: List[Entity], run_id: str) -> List[Insight]:
        entity_names = {e.canonical_name.lower(): e for e in entities}
        found: List[Insight] = []

        for source in raw_sources:
            text = f"{source.title or ''} {source.content or ''}"
            if not text.strip():
                continue

            mentioned = [name for name in entity_names if name in text.lower()]
            if not mentioned:
                continue

            for signal_type, patterns in _COMPILED.items():
                for pattern in patterns:
                    match = pattern.search(text)
                    if not match:
                        continue
                    for name in mentioned:
                        entity = entity_names[name]
                        found.append(
                            Insight(
                                id=new_id("insight"),
                                run_id=run_id,
                                category="competitor",
                                text=(
                                    f"{entity.canonical_name}: {signal_type.replace('_', ' ')} signal detected "
                                    f'— "{match.group(0).strip()}" ({source.source_name}).'
                                ),
                                related_entity_id=entity.id,
                                supporting_source_ids=json.dumps([source.id]),
                                created_at=iso_now(),
                            )
                        )
                    break  # one hit per signal_type per source is enough

        return found
