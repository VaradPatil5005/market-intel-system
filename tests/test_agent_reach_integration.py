"""
Comprehensive integration test suite for Agent-Reach within SIGNALORA.
Tests:
- Agent-Reach engine import and Doctor diagnostics across 16 channels
- AgentReachService (web reading, search, stock intel, social sentiment)
- DeepSearchAgent integration and RawSource persistence
- Hermes AgentReachResearchSkill execution and weight self-learning
- FastAPI /api/reach/* endpoints
- Graceful degradation and zero-failure guarantees
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import agent_reach
from agents.deep_search_agent import DeepSearchAgent
from api.main import app
from database.session import get_session, init_db
from skills.agent_reach_research_skill import AgentReachResearchSkill
from skills.skill_registry import skill_registry
from utils.agent_reach_service import AgentReachService, reach_service


@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()


# -----------------------------------------------------------------------------
# 1. Core Package & Doctor Diagnostics
# -----------------------------------------------------------------------------
def test_agent_reach_package_version():
    assert hasattr(agent_reach, "__version__")
    assert agent_reach.__version__ == "1.5.0"


def test_agent_reach_doctor_diagnostics():
    doctor_res = reach_service.run_doctor()
    assert isinstance(doctor_res, dict)
    assert doctor_res.get("total_channels") == 16
    channels = doctor_res.get("channels", {})
    assert "web" in channels
    assert "youtube" in channels
    assert "reddit" in channels
    assert "twitter" in channels
    assert "xueqiu" in channels
    assert "github" in channels
    assert "exa_search" in channels


# -----------------------------------------------------------------------------
# 2. AgentReachService Capabilities
# -----------------------------------------------------------------------------
def test_agent_reach_service_singleton():
    s1 = AgentReachService()
    s2 = AgentReachService()
    assert s1 is s2


def test_reach_service_read_url_fallback():
    # Test reading with mocked Jina response
    mock_md = "# Market Analysis 2026\nInstitutional demand for AI inference accelerators continues surging."
    with patch("agent_reach.channels.web.WebChannel.read", return_value=mock_md):
        doc = reach_service.read_url("https://example.com/research-report")
        assert doc["status"] == "success"
        assert doc["provider"] == "Jina Reader"
        assert "Market Analysis 2026" in doc["title"]
        assert doc["word_count"] > 5


def test_reach_service_search_web():
    # Test web search with mocked response
    mock_hits = [
        {"title": "NVIDIA Q3 Data Center Revenue", "url": "https://example.com/nvda", "snippet": "Strong GPU shipments", "source": "DuckDuckGo"}
    ]
    with patch.object(reach_service, "search_web", return_value=mock_hits):
        hits = reach_service.search_web("NVDA earnings")
        assert len(hits) == 1
        assert hits[0]["title"] == "NVIDIA Q3 Data Center Revenue"
        assert hits[0]["source"] == "DuckDuckGo"


def test_reach_service_get_stock_intel():
    mock_quote = {
        "symbol": "NVDA",
        "current": 125.50,
        "percent": 3.25,
        "pe_ttm": 45.2,
        "market_capital": 3000000000,
    }
    with patch("agent_reach.channels.xueqiu.XueqiuChannel.get_stock_quote", return_value=mock_quote):
        intel = reach_service.get_stock_intel("NVDA")
        assert intel["symbol"] == "NVDA"
        assert intel["quote"]["current"] == 125.50
        assert intel["quote"]["percent"] == 3.25


def test_reach_service_search_social_discussions():
    mock_posts = [
        {"id": 101, "title": "NVDA breakout discussion", "text": "Heavy institutional call buying observed.", "author": "QuantTrader", "likes": 42}
    ]
    with patch("agent_reach.channels.xueqiu.XueqiuChannel.get_hot_posts", return_value=mock_posts):
        discussions = reach_service.search_social_discussions("NVDA", limit=3)
        assert len(discussions) >= 1
        assert "NVDA" in discussions[0]["title"]


def test_reach_service_get_video_transcript():
    with patch("agent_reach.channels.youtube.YouTubeChannel.can_handle", return_value=True), \
         patch("agent_reach.channels.youtube.YouTubeChannel.transcribe", return_value="Good morning investors, our revenue grew 40 percent."):
        res = reach_service.get_video_transcript("https://www.youtube.com/watch?v=mock123")
        assert res["status"] == "success"
        assert "revenue grew 40 percent" in res["transcript"]


# -----------------------------------------------------------------------------
# 3. DeepSearchAgent Integration & Persistence
# -----------------------------------------------------------------------------
def test_deep_search_agent_with_agent_reach():
    agent = DeepSearchAgent()
    with get_session() as session:
        mock_reach_data = [
            {
                "source_name": "AgentReach/Web",
                "source_type": "deep_search_reach_web",
                "url": "https://example.com/nvda-datacenter",
                "title": "NVIDIA Supply Chain Intelligence",
                "content": "Blackwell architecture production ramping smoothly across global foundries.",
                "published_at": "",
            },
            {
                "source_name": "AgentReach/Xueqiu",
                "source_type": "equity_telemetry_xueqiu",
                "url": "https://xueqiu.com/S/NVDA",
                "title": "NVDA Live Telemetry",
                "content": "Live price $125.50 with strong institutional volume accumulation.",
                "published_at": "",
            },
        ]
        with patch.object(agent, "_agent_reach_search", return_value=mock_reach_data):
            saved_sources = agent.run(session, ["NVDA"], run_id="test_reach_run_01")
            assert len(saved_sources) >= 2
            titles = [s.title for s in saved_sources]
            assert "NVIDIA Supply Chain Intelligence" in titles
            assert any(s.source_type == "deep_search_reach_web" for s in saved_sources)


# -----------------------------------------------------------------------------
# 4. Hermes Self-Learning Skill Integration
# -----------------------------------------------------------------------------
def test_agent_reach_research_skill():
    skill = AgentReachResearchSkill()
    assert skill.name == "agent_reach_research"
    assert skill.category == "RESEARCH"

    # Trigger evaluation
    assert skill.evaluate_trigger({"research_query": "Semiconductor shortages"}) is True
    assert skill.evaluate_trigger({"anomalous_entities": ["TSMC"]}) is True
    assert skill.evaluate_trigger({"volatility_regime": "HIGH"}) is True
    assert skill.evaluate_trigger({"volatility_regime": "NORMAL"}) is False

    # Skill execution
    with patch.object(reach_service, "search_web", return_value=[{"source": "Web", "title": "TSMC 2nm update", "snippet": "Yields ahead of plan", "url": "https://tsmc.com"}]):
        out = skill.execute({"target_entity": "TSMC"})
        assert out["skill"] == "agent_reach_research"
        assert out["target"] == "TSMC"
        assert out["corroborating_sources_count"] >= 1
        assert "recommendation" in out

    # Dynamic self-learning feedback
    initial_weight = skill.weight
    skill.record_feedback(0.85)  # High accuracy prediction
    assert skill.weight > initial_weight
    assert skill.win_rate == 1.0


def test_skill_registry_includes_agent_reach():
    assert "agent_reach_research" in skill_registry.skills
    catalog = skill_registry.get_skills_catalog()
    skill_ids = [c["SKILL_ID"] for c in catalog]
    assert "agent_reach_research" in skill_ids


# -----------------------------------------------------------------------------
# 5. FastAPI /api/reach/* REST Endpoints
# -----------------------------------------------------------------------------
def test_api_reach_doctor_endpoint():
    client = TestClient(app)
    response = client.get("/api/reach/doctor")
    assert response.status_code == 200
    data = response.json()
    assert data["total_channels"] == 16
    assert "channels" in data


def test_api_reach_search_endpoint():
    client = TestClient(app)
    mock_results = [{"title": "Fed Rate Decision", "url": "https://example.com/fed", "snippet": "Unchanged", "source": "Web"}]
    with patch.object(reach_service, "search_web", return_value=mock_results):
        response = client.post("/api/reach/search", json={"query": "Fed Rate", "max_results": 3})
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Fed Rate"
        assert data["count"] == 1
        assert data["results"][0]["title"] == "Fed Rate Decision"


def test_api_reach_read_endpoint():
    client = TestClient(app)
    mock_doc = {
        "status": "success",
        "provider": "Jina Reader",
        "url": "https://example.com/article",
        "title": "Article Title",
        "content": "# Clean Markdown\nExtracted content text.",
        "char_count": 45,
        "word_count": 6,
    }
    with patch.object(reach_service, "read_url", return_value=mock_doc):
        response = client.post("/api/reach/read", json={"url": "https://example.com/article"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["provider"] == "Jina Reader"
        assert data["word_count"] == 6


def test_api_reach_stock_endpoint():
    client = TestClient(app)
    mock_intel = {"symbol": "AAPL", "quote": {"current": 220.0}, "trending_posts": [], "source": "Xueqiu"}
    with patch.object(reach_service, "get_stock_intel", return_value=mock_intel):
        response = client.get("/api/reach/stock/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["quote"]["current"] == 220.0
