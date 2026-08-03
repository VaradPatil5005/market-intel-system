"""
Entity Resolution Agent.

Detects candidate entities (companies, products, people, topics) via a
lightweight rule-based extractor (capitalized-phrase + watchlist
matching), then merges duplicate/ambiguous mentions into canonical
entity records using normalized-name + fuzzy-similarity matching.

Designed to be swapped later for an embeddings-based resolver without
changing its interface (`run(session, sources) -> List[Entity]`).
"""
from __future__ import annotations

import difflib
import json
import re
from typing import Dict, List

from agents.base import BaseAgent
from database.models import Entity, RawSource
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id, normalize_entity_name

entity_repo = Repository(Entity)

CAPITALIZED_PHRASE_RE = re.compile(r"\b([A-Z][a-zA-Z0-9&.]*(?:\s+[A-Z][a-zA-Z0-9&.]*){0,2})\b")
STOPWORDS = {"The", "This", "That", "It", "In", "On", "For", "A", "An", "Its", "Their"}
SIMILARITY_THRESHOLD = 0.86


class EntityResolutionAgent(BaseAgent):
    name = "entity_resolution_agent"

    def run(self, session: Session, sources: List[RawSource]) -> List[Entity]:
        with self.run_tracked("resolve_entities"):
            watchlist = settings.watchlist
            canonical_index: Dict[str, Entity] = {}

            for existing in entity_repo.all(session):
                canonical_index[normalize_entity_name(existing.canonical_name)] = existing

            resolved_count = 0
            merged_count = 0

            for source in sources:
                if source.is_rejected:
                    continue
                candidates = self._extract_candidates(f"{source.title} {source.content}", watchlist)
                for candidate, entity_type in candidates:
                    norm = normalize_entity_name(candidate)
                    if not norm:
                        continue
                    match_key = self._find_fuzzy_match(norm, canonical_index)

                    if match_key:
                        entity = canonical_index[match_key]
                        entity.mention_count += 1
                        entity.last_seen_at = iso_now()
                        aliases = set(json.loads(entity.aliases or "[]"))
                        if candidate not in aliases:
                            aliases.add(candidate)
                            entity.aliases = json.dumps(sorted(aliases))
                        merged_count += 1
                    else:
                        entity = Entity(
                            id=new_id("ent"),
                            canonical_name=candidate,
                            entity_type=entity_type,
                            aliases=json.dumps([candidate]),
                            source_id=source.id,
                            first_seen_at=iso_now(),
                            last_seen_at=iso_now(),
                            mention_count=1,
                        )
                        entity_repo.insert(session, entity)
                        canonical_index[norm] = entity
                        resolved_count += 1

            session.flush()
            all_entities = list(canonical_index.values())

            self.audit(
                session,
                step="resolve_entities",
                action="resolved_and_merged_entities",
                output_summary={"new_entities": resolved_count, "merged_mentions": merged_count},
            )
            return all_entities

    # ------------------------------------------------------------------
    def _extract_candidates(self, text: str, watchlist: List[str]):
        found = []
        for name in watchlist:
            if name.lower() in text.lower():
                found.append((name, "company"))

        for match in CAPITALIZED_PHRASE_RE.finditer(text):
            phrase = match.group(1).strip()
            first_word = phrase.split()[0]
            if first_word in STOPWORDS or len(phrase) < 3:
                continue
            found.append((phrase, "topic"))
        return found

    def _find_fuzzy_match(self, norm_name: str, index: Dict[str, Entity]) -> str | None:
        if norm_name in index:
            return norm_name
        best_key, best_score = None, 0.0
        for key in index:
            score = difflib.SequenceMatcher(None, norm_name, key).ratio()
            if score > best_score:
                best_key, best_score = key, score
        if best_score >= SIMILARITY_THRESHOLD:
            return best_key
        return None
