"""
Entity Resolution Agent.

Detects candidate entities (companies, products, people, topics) via a
lightweight rule-based extractor (capitalized-phrase + watchlist
matching), then merges duplicate/ambiguous mentions into canonical
entity records.

Tier 1 upgrade: merging now prefers dense semantic embeddings
(`sentence-transformers`, model = `settings.embedding_model_name`,
default `all-MiniLM-L6-v2`) over plain string fuzzy-matching, because
embeddings correctly merge names that share no common substring at all
(e.g. "NVDA" <-> "Nvidia Corp", or a translated/abbreviated name) —
something `difflib`/fuzzy matching structurally cannot do since it only
compares character sequences.

Per the project's graceful-degradation design, if `sentence-transformers`
is not installed, the model can't be downloaded (no network), or loading
fails for any other reason, this agent automatically and silently falls
back to the original difflib-based fuzzy matcher — the pipeline never
hard-fails because of a missing ML dependency.
"""
from __future__ import annotations

import difflib
import json
import re
from typing import Dict, List, Optional

from agents.base import BaseAgent
from database.models import Entity, RawSource
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id, normalize_entity_name

entity_repo = Repository(Entity)

CAPITALIZED_PHRASE_RE = re.compile(r"\b([A-Z][a-zA-Z0-9&.]*(?:\s+[A-Z][a-zA-Z0-9&.]*){0,2})\b")
STOPWORDS = {"The", "This", "That", "It", "In", "On", "For", "A", "An", "Its", "Their"}
FUZZY_SIMILARITY_THRESHOLD = 0.86  # used only in the difflib fallback path

# --- Lazy, optional embedding backend -------------------------------------
# Loaded once per process (not per agent instance) so repeated pipeline runs
# in the same process don't reload model weights from disk every time.
_embedding_model = None
_embedding_load_attempted = False


def _get_embedding_model():
    """Best-effort loader for the sentence-transformers model.

    Returns None (never raises) if the package isn't installed, the model
    weights aren't cached locally and there's no network to fetch them, or
    anything else goes wrong — callers must treat None as "use the fallback".
    """
    global _embedding_model, _embedding_load_attempted
    if _embedding_load_attempted:
        return _embedding_model
    _embedding_load_attempted = True
    if not settings.use_embedding_entity_resolution:
        return None
    try:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        _embedding_model = SentenceTransformer(settings.embedding_model_name)
    except Exception:
        _embedding_model = None
    return _embedding_model


def _cosine_similarity(vec_a, vec_b) -> float:
    import numpy as np  # sentence-transformers already depends on numpy

    a, b = np.asarray(vec_a), np.asarray(vec_b)
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-9
    return float(np.dot(a, b) / denom)


class EntityResolutionAgent(BaseAgent):
    name = "entity_resolution_agent"

    def run(self, session: Session, sources: List[RawSource]) -> List[Entity]:
        with self.run_tracked("resolve_entities"):
            watchlist = settings.watchlist
            canonical_index: Dict[str, Entity] = {}
            embedding_index: Dict[str, list] = {}  # norm_name -> embedding vector, for the embedding path

            embedding_model = _get_embedding_model()
            using_embeddings = embedding_model is not None
            self.logger.info(
                "Entity resolution backend: %s"
                % ("sentence-transformers embeddings" if using_embeddings else "difflib fuzzy match (fallback)")
            )

            for existing in entity_repo.all(session):
                norm = normalize_entity_name(existing.canonical_name)
                canonical_index[norm] = existing
                if using_embeddings:
                    embedding_index[norm] = embedding_model.encode(existing.canonical_name)

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

                    if using_embeddings:
                        candidate_vec = embedding_model.encode(candidate)
                        match_key = self._find_embedding_match(norm, candidate_vec, canonical_index, embedding_index)
                    else:
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
                        if using_embeddings:
                            embedding_index[norm] = candidate_vec
                        resolved_count += 1

            session.flush()
            all_entities = list(canonical_index.values())

            self.audit(
                session,
                step="resolve_entities",
                action="resolved_and_merged_entities",
                output_summary={
                    "new_entities": resolved_count,
                    "merged_mentions": merged_count,
                    "resolution_backend": "embeddings" if using_embeddings else "fuzzy_match_fallback",
                },
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

    def _find_fuzzy_match(self, norm_name: str, index: Dict[str, Entity]) -> Optional[str]:
        if norm_name in index:
            return norm_name
        best_key, best_score = None, 0.0
        for key in index:
            score = difflib.SequenceMatcher(None, norm_name, key).ratio()
            if score > best_score:
                best_key, best_score = key, score
        if best_score >= FUZZY_SIMILARITY_THRESHOLD:
            return best_key
        return None

    def _find_embedding_match(
        self,
        norm_name: str,
        candidate_vec,
        index: Dict[str, Entity],
        embedding_index: Dict[str, list],
    ) -> Optional[str]:
        if norm_name in index:
            return norm_name
        best_key, best_score = None, 0.0
        for key, vec in embedding_index.items():
            score = _cosine_similarity(candidate_vec, vec)
            if score > best_score:
                best_key, best_score = key, score
        if best_score >= settings.entity_embedding_similarity_threshold:
            return best_key
        return None
