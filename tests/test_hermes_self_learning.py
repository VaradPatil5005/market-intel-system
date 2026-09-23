"""
Unit and Integration Test Suite for Hermes-Agent Self-Learning Architecture.
Tests bounded memory constraints, dynamic market skills adaptation, and
autonomous trajectory back-testing.
"""

import pytest
from utils.memory_store import BoundedMemoryStore, MAX_MEMORY_CHARS
from skills.skill_registry import SkillRegistry
from agents.hermes_self_learning_agent import HermesSelfLearningAgent
from database.session import get_session, Repository
from database.models import AgentLearning

def test_bounded_memory_store_capacity_and_overflow():
    store = BoundedMemoryStore()
    stats = store.get_stats("MEMORY")
    assert stats["max_chars"] == MAX_MEMORY_CHARS
    assert stats["char_count"] <= MAX_MEMORY_CHARS

    # Test overflow prevention
    huge_text = "A" * (MAX_MEMORY_CHARS + 50)
    with pytest.raises(ValueError):
        store.save_content("MEMORY", huge_text)

def test_hermes_memory_snapshot_system_prompt_serialization():
    store = BoundedMemoryStore()
    snapshot = store.render_system_prompt_block()
    assert "HERMES PERSISTENT MEMORY" in snapshot
    assert "USER PROFILE & CONSTRAINTS" in snapshot
    assert "Zero Emoji Mandate" in snapshot

def test_skill_registry_triggers_and_weight_adaptation():
    registry = SkillRegistry()
    assert "chokepoint_hedging" in registry.skills
    assert "sec_discrepancy" in registry.skills

    # Trigger with high stress
    context = {
        "composite_geopolitical_stress_index": 70.0,
        "brent_crude_risk_premium_usd": 6.0,
        "discrepancies_flagged": 3,
        "flagged_entities": ["NVDA"]
    }
    results = registry.evaluate_and_execute_skills(context)
    assert len(results) >= 2

    # Test self-learning weight adaptation
    initial_weight = registry.skills["chokepoint_hedging"].weight
    registry.record_skill_feedback("chokepoint_hedging", 0.95)  # Success
    assert registry.skills["chokepoint_hedging"].weight > initial_weight
    assert registry.skills["chokepoint_hedging"].win_rate == 1.0

    registry.record_skill_feedback("chokepoint_hedging", 0.20)  # Failure
    assert registry.skills["chokepoint_hedging"].win_rate == 0.5

def test_hermes_self_learning_agent_autonomous_truth_loop():
    agent = HermesSelfLearningAgent()
    result = agent.run({"cgsi": 60.0, "discrepancies": 2})

    assert result["status"] == "COMPLETED"
    assert "forecast_evaluations" in result
    assert "memory_consolidation" in result
    assert len(result["skill_adaptations"]) > 0

    # Verify AgentLearning created in DB
    with get_session() as s:
        learnings = Repository(AgentLearning).all(s)
        assert len(learnings) > 0
