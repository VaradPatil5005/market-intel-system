"""
Reflexion Agent Unit Tests.

Tests intent classification, entity extraction, cosine similarity,
lesson template generation, and penalty computation.
All tests run offline — no DB, no LLM required.
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ---------------------------------------------------------------------------
# Test: Intent classification
# ---------------------------------------------------------------------------
def test_classify_earnings_intent():
    from agents.query_memory_agent import QueryMemoryAgent
    agent = QueryMemoryAgent()
    intent = agent._classify_intent("What are Nvidia's latest earnings and guidance for Q3?")
    assert intent == "earnings_risk"


def test_classify_regulatory_intent():
    from agents.query_memory_agent import QueryMemoryAgent
    agent = QueryMemoryAgent()
    intent = agent._classify_intent("Is the FTC investigating Anthropic for antitrust violations?")
    assert intent == "regulatory_risk"


def test_classify_ai_tech_intent():
    from agents.query_memory_agent import QueryMemoryAgent
    agent = QueryMemoryAgent()
    intent = agent._classify_intent("What's the latest GPT model from OpenAI and how does LLM performance compare?")
    assert intent == "ai_technology"


def test_classify_general_fallback():
    from agents.query_memory_agent import QueryMemoryAgent
    agent = QueryMemoryAgent()
    intent = agent._classify_intent("Tell me something interesting.")
    assert intent == "general"


# ---------------------------------------------------------------------------
# Test: Entity extraction
# ---------------------------------------------------------------------------
def test_extract_watchlist_entities():
    from agents.query_memory_agent import QueryMemoryAgent
    agent = QueryMemoryAgent()
    entities = agent._extract_entities("What is happening with Nvidia and Google today?")
    assert "Nvidia" in entities or "nvidia" in [e.lower() for e in entities]
    assert "Google" in entities or "google" in [e.lower() for e in entities]


# ---------------------------------------------------------------------------
# Test: Cosine similarity
# ---------------------------------------------------------------------------
def test_cosine_sim_identical_vectors():
    from agents.reflexion_agent import _cosine_sim
    v = [1.0, 0.5, 0.3]
    assert abs(_cosine_sim(v, v) - 1.0) < 1e-6


def test_cosine_sim_orthogonal_vectors():
    from agents.reflexion_agent import _cosine_sim
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert abs(_cosine_sim(a, b)) < 1e-6


def test_cosine_sim_zero_magnitude():
    from agents.reflexion_agent import _cosine_sim
    a = [0.0, 0.0]
    b = [1.0, 0.5]
    assert _cosine_sim(a, b) == 0.0


# ---------------------------------------------------------------------------
# Test: Keyword similarity fallback
# ---------------------------------------------------------------------------
def test_keyword_sim_exact_entity_and_category():
    from agents.reflexion_agent import ReflexionAgent
    from database.models import AgentLearning
    agent = ReflexionAgent()
    lesson = AgentLearning(
        id="test", source_insight_id=None, entity_name="Nvidia",
        category="risk", human_action="reject", reviewer_note=None,
        lesson_text="Test lesson", lesson_type="false_positive_risk",
        lesson_embedding=None, is_active=1, created_at="2024-01-01"
    )
    sim = agent._keyword_sim(lesson, "Nvidia", "risk")
    assert abs(sim - 1.0) < 1e-6


def test_keyword_sim_partial_match():
    from agents.reflexion_agent import ReflexionAgent
    from database.models import AgentLearning
    agent = ReflexionAgent()
    lesson = AgentLearning(
        id="test", source_insight_id=None, entity_name="Nvidia",
        category="sentiment", human_action="modify", reviewer_note=None,
        lesson_text="Test", lesson_type="overstatement_risk",
        lesson_embedding=None, is_active=1, created_at="2024-01-01"
    )
    sim = agent._keyword_sim(lesson, "Nvidia", "risk")
    assert 0.5 < sim < 1.0  # entity matches (0.6) but category doesn't (0.0)


# ---------------------------------------------------------------------------
# Test: Lesson template generation
# ---------------------------------------------------------------------------
def test_lesson_template_reject():
    from agents.reflexion_agent import LESSON_TEMPLATES
    from database.models import Insight
    insight = Insight(
        id="ins1", run_id="run1", category="risk",
        text="Nvidia is at risk of a 30% revenue decline this quarter.",
        related_entity_id=None, supporting_source_ids=None, created_at="2024-01-01"
    )
    template = LESSON_TEMPLATES["reject"]
    lesson_text = template.format(
        entity="Nvidia",
        category="risk",
        insight_text=insight.text[:200],
        reason="This was based on a single unverified source.",
        min_sources=2,
    )
    assert "Nvidia" in lesson_text
    assert "REJECTED" in lesson_text
    assert "unverified" in lesson_text


def test_lesson_template_modify():
    from agents.reflexion_agent import LESSON_TEMPLATES
    template = LESSON_TEMPLATES["modify"]
    lesson_text = template.format(
        entity="Microsoft",
        category="competitor",
        insight_text="Microsoft is dominating AI.",
        reason="Too broad a claim.",
        min_sources=2,
    )
    assert "Microsoft" in lesson_text
    assert "MODIFIED" in lesson_text


# ---------------------------------------------------------------------------
# Test: Pearson correlation
# ---------------------------------------------------------------------------
def test_pearson_perfect_positive():
    from agents.market_correlation_agent import _pearson
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [2.0, 4.0, 6.0, 8.0, 10.0]
    corr = _pearson(x, y)
    assert corr is not None
    assert abs(corr - 1.0) < 1e-4


def test_pearson_perfect_negative():
    from agents.market_correlation_agent import _pearson
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [5.0, 4.0, 3.0, 2.0, 1.0]
    corr = _pearson(x, y)
    assert corr is not None
    assert abs(corr + 1.0) < 1e-4


def test_pearson_insufficient_data():
    from agents.market_correlation_agent import _pearson
    corr = _pearson([1.0, 2.0], [1.0, 2.0])
    assert corr is None


# ---------------------------------------------------------------------------
# Test: RSI computation
# ---------------------------------------------------------------------------
def test_rsi_overbought():
    from agents.price_data_agent import _compute_rsi
    # Steadily rising prices → RSI should be high (overbought > 70)
    closes = [100.0 + i * 2 for i in range(20)]
    rsi = _compute_rsi(closes, period=14)
    assert rsi is not None
    assert rsi > 70


def test_rsi_insufficient_data():
    from agents.price_data_agent import _compute_rsi
    closes = [100.0, 101.0, 102.0]
    rsi = _compute_rsi(closes, period=14)
    assert rsi is None
