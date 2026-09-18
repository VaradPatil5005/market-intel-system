"""
Reflexion Agent — Self-Learning from Human Reviewer Feedback.

Implements the Reflexion pattern: when a human reviewer Modifies or Rejects
an insight in the Streamlit UI, this agent automatically generates a
structured "lesson" that future pipeline runs can retrieve and apply.

How it works:
  1. Human clicks Reject/Modify in the Streamlit UI → `apply_decision()` is called
  2. The UI calls `ReflexionAgent.generate_lesson()` with the insight + action
  3. The agent generates a lesson using:
     - If LLM available (OpenAI): sends a structured prompt
     - Otherwise: fills a deterministic lesson template (always works offline)
  4. The lesson is stored in `agent_learnings` with a text embedding
  5. On future runs, `load_relevant_lessons(entity, category)` is called by
     ConfidenceScoringAgent and RagInsightAgent to retrieve top-K lessons
     and apply them as soft scoring adjustments

This creates a continuous improvement loop:
  Pipeline run → Human review → Reflexion lesson → Better next run
"""
from __future__ import annotations

import json
from typing import List, Optional, Tuple

from agents.base import BaseAgent
from database.models import AgentLearning, Insight
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id
from utils.logging_setup import get_logger

logger = get_logger("reflexion_agent")

learning_repo = Repository(AgentLearning)
insight_repo = Repository(Insight)

# --- Lazy embedding backend (same pattern as other agents) -----------------
_embed_model = None
_embed_attempted = False


def _get_embed_model():
    global _embed_model, _embed_attempted
    if _embed_attempted:
        return _embed_model
    _embed_attempted = True
    try:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        _embed_model = SentenceTransformer(settings.embedding_model_name)
    except Exception:
        _embed_model = None
    return _embed_model


def _embed_text(text: str) -> Optional[List[float]]:
    model = _get_embed_model()
    if model is None:
        return None
    try:
        vec = model.encode([text])[0]
        return vec.tolist()
    except Exception:
        return None


def _cosine_sim(a: List[float], b: List[float]) -> float:
    import math
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a * mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ---------------------------------------------------------------------------

LESSON_TEMPLATES = {
    "reject": (
        "LESSON [{entity}][{category}]: A reviewer REJECTED an insight claiming: \"{insight_text}\". "
        "Reason: {reason}. "
        "Guidance: In future runs, do not generate similar claims for [{entity}] in the [{category}] "
        "category without strong cross-source evidence. Apply an additional confidence penalty of 0.15 "
        "when similar patterns emerge."
    ),
    "modify": (
        "LESSON [{entity}][{category}]: A reviewer MODIFIED an insight. "
        "Original: \"{insight_text}\". Reviewer note: {reason}. "
        "Guidance: The original framing was inaccurate or overstated. "
        "For [{entity}] insights in [{category}], prefer more conservative language "
        "and require at least {min_sources} supporting sources."
    ),
}

LESSON_TYPE_MAP = {
    "reject": "false_positive_risk",
    "modify": "overstatement_risk",
}


class ReflexionAgent(BaseAgent):
    name = "reflexion_agent"

    # ------------------------------------------------------------------
    def generate_lesson(
        self,
        session: Session,
        insight_id: str,
        human_action: str,            # "reject" | "modify"
        reviewer_note: str,
        new_text: Optional[str] = None,
    ) -> Optional[AgentLearning]:
        """Generate and store a Reflexion lesson for this human decision.

        Called by the Streamlit UI after `apply_decision()`.
        """
        if not settings.enable_reflexion_learning:
            return None

        insight = insight_repo.get(session, insight_id)
        if insight is None:
            logger.warning(f"ReflexionAgent: insight {insight_id} not found — no lesson generated.")
            return None

        entity_name = self._resolve_entity_name(session, insight)
        lesson_text = self._build_lesson_text(
            insight, human_action, reviewer_note, entity_name
        )

        # Try LLM-quality lesson first, fall back to template
        llm_lesson = self._llm_lesson(insight, human_action, reviewer_note, entity_name)
        if llm_lesson:
            lesson_text = llm_lesson

        embedding = _embed_text(lesson_text)

        record = AgentLearning(
            id=new_id("lrn"),
            source_insight_id=insight_id,
            entity_name=entity_name,
            category=insight.category,
            human_action=human_action,
            reviewer_note=reviewer_note or "",
            lesson_text=lesson_text,
            lesson_type=LESSON_TYPE_MAP.get(human_action, "general"),
            lesson_embedding=json.dumps(embedding) if embedding else None,
            is_active=1,
            created_at=iso_now(),
        )
        learning_repo.insert(session, record)

        self.audit(
            session,
            step="reflexion",
            action="lesson_generated",
            input_summary={"insight_id": insight_id, "action": human_action},
            output_summary={"lesson_type": record.lesson_type, "entity": entity_name},
        )
        logger.info(
            f"Reflexion lesson generated for insight {insight_id} "
            f"(action={human_action}, entity={entity_name})"
        )
        return record

    # ------------------------------------------------------------------
    def load_relevant_lessons(
        self,
        session: Session,
        entity_name: str,
        category: str,
        query_text: str = "",
    ) -> List[Tuple[AgentLearning, float]]:
        """Retrieve top-K active lessons relevant to this entity/category.

        Returns list of (lesson, similarity_score) tuples.
        Similarity is computed:
          - Via cosine embedding similarity if embeddings are available
          - Otherwise by exact entity_name + category match (keyword fallback)
        """
        if not settings.enable_reflexion_learning:
            return []

        active_lessons = [
            l for l in learning_repo.all(session) if l.is_active == 1
        ]
        if not active_lessons:
            return []

        # Build query text for similarity
        q_text = query_text or f"{entity_name} {category}"
        q_embedding = _embed_text(q_text)

        scored: List[Tuple[AgentLearning, float]] = []
        for lesson in active_lessons:
            if q_embedding and lesson.lesson_embedding:
                try:
                    l_vec = json.loads(lesson.lesson_embedding)
                    sim = _cosine_sim(q_embedding, l_vec)
                except Exception:
                    sim = self._keyword_sim(lesson, entity_name, category)
            else:
                sim = self._keyword_sim(lesson, entity_name, category)

            if sim >= settings.reflexion_lesson_similarity_threshold:
                scored.append((lesson, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[: settings.reflexion_top_k_lessons]

    def compute_penalty(
        self,
        session: Session,
        entity_name: str,
        category: str,
        insight_text: str = "",
    ) -> float:
        """Compute cumulative score penalty from relevant Reflexion lessons.

        Returns a penalty between 0.0 (no lessons apply) and 0.30 (max penalty).
        """
        lessons = self.load_relevant_lessons(session, entity_name, category, insight_text)
        if not lessons:
            return 0.0

        # Each lesson applies a penalty proportional to its similarity
        total_penalty = 0.0
        for lesson, sim in lessons:
            base_penalty = 0.15 if lesson.human_action == "reject" else 0.08
            total_penalty += base_penalty * sim

        return min(total_penalty, 0.30)

    # ------------------------------------------------------------------
    def _build_lesson_text(
        self,
        insight: Insight,
        action: str,
        reviewer_note: str,
        entity_name: str,
    ) -> str:
        template = LESSON_TEMPLATES.get(action, LESSON_TEMPLATES["modify"])
        return template.format(
            entity=entity_name,
            category=insight.category,
            insight_text=insight.text[:200],
            reason=reviewer_note or "(no note provided)",
            min_sources=settings.min_cross_source_verification,
        )

    def _llm_lesson(
        self,
        insight: Insight,
        action: str,
        reviewer_note: str,
        entity_name: str,
    ) -> Optional[str]:
        """Try to generate a richer lesson using an LLM (degrades to None)."""
        if not settings.openai_api_key and not settings.anthropic_api_key:
            return None
        try:
            prompt = (
                f"A market intelligence analyst just {action}ed the following insight about {entity_name}:\n\n"
                f'Insight: "{insight.text}"\n'
                f"Reviewer note: {reviewer_note or '(none)'}\n\n"
                f"Generate a concise, structured learning lesson (2-3 sentences) that future AI agents "
                f"can use to avoid similar errors when analyzing {entity_name} in the {insight.category} "
                f"category. Be specific about what signal or evidence pattern was flawed."
            )
            if settings.openai_api_key:
                from openai import OpenAI  # noqa: PLC0415
                client = OpenAI(api_key=settings.openai_api_key)
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.3,
                )
                return resp.choices[0].message.content.strip()
        except Exception as exc:
            logger.debug(f"LLM lesson generation failed (using template fallback): {exc}")
        return None

    def _resolve_entity_name(self, session: Session, insight: Insight) -> str:
        if insight.related_entity_id:
            from database.models import Entity  # noqa: PLC0415
            entity = Repository(Entity).get(session, insight.related_entity_id)
            if entity:
                return entity.canonical_name
        return "Unknown Entity"

    def _keyword_sim(self, lesson: AgentLearning, entity_name: str, category: str) -> float:
        score = 0.0
        if lesson.entity_name and lesson.entity_name.lower() == entity_name.lower():
            score += 0.6
        if lesson.category and lesson.category.lower() == category.lower():
            score += 0.4
        return score
