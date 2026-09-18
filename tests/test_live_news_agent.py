"""
Unit tests for Live Internet Financial News & RSS Agent (agents.live_news_agent).
Zero emojis.
"""
import pytest
from agents.live_news_agent import LiveNewsAgent, live_news_agent


def test_live_news_agent_fetch_breaking_news():
    news = live_news_agent.fetch_breaking_news(limit=6)
    assert isinstance(news, list)
    assert len(news) == 6
    for item in news:
        assert "title" in item
        assert "source" in item
        assert "category" in item
        assert "sentiment" in item
        assert item["sentiment"] in ["BULLISH", "BEARISH", "NEUTRAL"]


def test_live_news_agent_category_filtering():
    agent = LiveNewsAgent()
    commodities = agent.fetch_breaking_news(limit=10, category="Futures & Commodities")
    assert len(commodities) > 0
    for c in commodities:
        text = (c.get("category", "") + " " + " ".join(c.get("tags", []))).lower()
        assert any(k in text for k in ["commodit", "oil", "gold", "energy", "futures", "metals"])


def test_live_news_agent_search():
    agent = LiveNewsAgent()
    hits = agent.search_news("oil", limit=3)
    assert len(hits) > 0
    assert any("oil" in (h["title"] + " " + h["summary"]).lower() for h in hits)


def test_live_news_market_condition_briefing():
    agent = LiveNewsAgent()
    cond = agent.get_market_condition_briefing()
    assert "regime" in cond
    assert "benchmark_rates" in cond
    assert "commodities" in cond
    assert "US_10Y" in cond["benchmark_rates"]
    assert "crude_oil_wti" in cond["commodities"]
    assert len(cond["headlines"]) > 0
