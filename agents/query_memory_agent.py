"""
Query Memory Agent — Personalized Context Engine.

Stores every user query in the database, extracts entities and intent
categories from it, and maintains a per-user interest profile. The profile
is then used to bias the pipeline: the report surface personally relevant
insights first, the watchlist can be dynamically extended with entities
the user has recently asked about, and the report depth adapts to the
user's stated preferences.

Pipeline integration:
  1. User submits a query in the Streamlit UI
  2. QueryMemoryAgent.record_query() extracts entities + intent and stores them
  3. At pipeline start, QueryMemoryAgent.load_user_context() returns a context
     dict that graph.py injects into the initial PipelineState
  4. ReportGenerationAgent reads context['user_profile'] to customize output

This creates a continuous personalization loop that improves with every
question the user asks.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent
from database.models import UserInterestProfile, UserQuery
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id
from utils.logging_setup import get_logger

logger = get_logger("query_memory_agent")

query_repo = Repository(UserQuery)
profile_repo = Repository(UserInterestProfile)

# Intent classification keywords
INTENT_KEYWORDS = {
    "earnings_risk": ["earnings", "revenue", "profit", "loss", "guidance", "beat", "miss", "eps"],
    "competitor_analysis": ["competitor", "competition", "vs", "versus", "market share", "rival"],
    "regulatory_risk": ["regulation", "regulatory", "sec", "ftc", "antitrust", "investigation", "lawsuit", "fine"],
    "supply_chain": ["supply", "chain", "shortage", "inventory", "manufacturing", "chip", "semiconductor"],
    "ma_activity": ["merger", "acquisition", "deal", "buyout", "takeover", "ipo", "spinoff"],
    "leadership": ["ceo", "cfo", "executive", "leadership", "management", "board"],
    "product_launch": ["launch", "release", "product", "announce", "unveil", "debut"],
    "macro_risk": ["inflation", "interest rate", "fed", "recession", "gdp", "economy", "macro"],
    "ai_technology": ["ai", "artificial intelligence", "llm", "model", "gpt", "machine learning"],
    "general": [],  # default
}

# Named entity extraction (simple regex-based for offline use)
ENTITY_PATTERN = re.compile(r"\b([A-Z][a-zA-Z0-9&.]*(?:\s+[A-Z][a-zA-Z0-9&.]*){0,2})\b")
STOPWORDS = {"The", "This", "That", "It", "In", "On", "For", "A", "An", "What", "Why", "How", "Is", "Are"}


class QueryMemoryAgent(BaseAgent):
    name = "query_memory_agent"

    # ------------------------------------------------------------------
    def record_query(
        self,
        session: Session,
        query_text: str,
        run_id: Optional[str] = None,
    ) -> UserQuery:
        """Store a user query and update their interest profile."""
        entities = self._extract_entities(query_text)
        intent = self._classify_intent(query_text)

        record = UserQuery(
            id=new_id("uq"),
            user_id=settings.user_id,
            query_text=query_text,
            extracted_entities=json.dumps(entities),
            intent_category=intent,
            run_id=run_id,
            created_at=iso_now(),
        )
        query_repo.insert(session, record)
        session.flush()

        # Update user interest profile
        self._update_profile(session, entities, intent, query_text)

        self.audit(
            session,
            step="query_memory",
            action="query_recorded",
            input_summary={"query": query_text[:200]},
            output_summary={"entities": entities, "intent": intent},
        )
        logger.info(f"QueryMemoryAgent: recorded query (intent={intent}, entities={entities})")
        return record

    def load_user_context(self, session: Session) -> Dict[str, Any]:
        """Load user context for the current user to inject into the pipeline.

        Returns a dict with:
          - user_profile: UserInterestProfile dict
          - recent_entities: entities from last 10 queries
          - top_intent: most common recent intent
          - extended_watchlist: watchlist merged with user's queried entities
        """
        profile = profile_repo.get(session, settings.user_id)

        recent_queries = list(reversed(query_repo.filter_by(session, user_id=settings.user_id)))[:10]

        recent_entities: List[str] = []
        intent_counts: Dict[str, int] = {}
        for q in recent_queries:
            if q.extracted_entities:
                try:
                    recent_entities.extend(json.loads(q.extracted_entities))
                except Exception:
                    pass
            if q.intent_category:
                intent_counts[q.intent_category] = intent_counts.get(q.intent_category, 0) + 1

        top_intent = max(intent_counts, key=lambda k: intent_counts[k]) if intent_counts else "general"

        # Build extended watchlist
        base_watchlist = settings.watchlist
        if profile and profile.watchlist_override:
            try:
                override = json.loads(profile.watchlist_override)
                base_watchlist = list(dict.fromkeys(base_watchlist + override))  # deduplicate preserving order
            except Exception:
                pass

        # Add recently queried entities to watchlist
        for ent in recent_entities:
            if ent not in base_watchlist and len(base_watchlist) < 20:
                base_watchlist.append(ent)

        return {
            "user_id": settings.user_id,
            "user_profile": profile.to_dict() if profile else {},
            "recent_entities": list(dict.fromkeys(recent_entities)),
            "top_intent": top_intent,
            "extended_watchlist": base_watchlist,
            "preferred_depth": profile.preferred_depth if profile else settings.user_preferred_depth,
            "risk_appetite": profile.risk_appetite if profile else settings.user_risk_appetite,
        }

    def get_query_history(
        self,
        session: Session,
        limit: int = 20,
    ) -> List[UserQuery]:
        """Return recent queries for the current user."""
        all_q = query_repo.filter_by(session, user_id=settings.user_id)
        return list(reversed(all_q))[:limit]

    # ------------------------------------------------------------------
    def _extract_entities(self, text: str) -> List[str]:
        matches = ENTITY_PATTERN.findall(text)
        entities = []
        for m in matches:
            if m not in STOPWORDS and len(m) > 1:
                # Also check if it's in the watchlist
                for w in settings.watchlist:
                    if w.lower() in text.lower() and w not in entities:
                        entities.append(w)
                if m not in entities and m[0].isupper():
                    entities.append(m)
        return list(dict.fromkeys(entities))[:10]   # deduplicate, max 10

    def _classify_intent(self, text: str) -> str:
        text_lower = text.lower()
        scores = {}
        for intent, keywords in INTENT_KEYWORDS.items():
            if intent == "general":
                continue
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[intent] = score
        if not scores:
            return "general"
        return max(scores, key=lambda k: scores[k])

    def _update_profile(
        self,
        session: Session,
        entities: List[str],
        intent: str,
        query_text: str,
    ) -> None:
        profile = profile_repo.get(session, settings.user_id)

        if profile is None:
            profile = UserInterestProfile(
                user_id=settings.user_id,
                watchlist_override=json.dumps(entities),
                risk_appetite=settings.user_risk_appetite,
                preferred_depth=settings.user_preferred_depth,
                top_categories=json.dumps([intent]),
                query_count=1,
                updated_at=iso_now(),
            )
            session.add(profile)
        else:
            # Update watchlist
            try:
                current_watch = json.loads(profile.watchlist_override or "[]")
            except Exception:
                current_watch = []
            merged = list(dict.fromkeys(current_watch + entities))[:20]
            profile.watchlist_override = json.dumps(merged)

            # Update top categories
            try:
                current_cats = json.loads(profile.top_categories or "[]")
            except Exception:
                current_cats = []
            if intent not in current_cats:
                current_cats.insert(0, intent)
            profile.top_categories = json.dumps(current_cats[:5])

            profile.query_count = (profile.query_count or 0) + 1
            profile.updated_at = iso_now()

        session.flush()
