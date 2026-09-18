"""Unit tests for Vibe Quant Intelligence Agent."""
from __future__ import annotations

import numpy as np
import pytest

from agents.vibe_quant_agent import VibeQuantAgent, vibe_quant_agent


def test_resolve_ticker():
    assert vibe_quant_agent.resolve_ticker("nvidia") == "NVDA"
    assert vibe_quant_agent.resolve_ticker("us30y") == "^TYX"
    assert vibe_quant_agent.resolve_ticker("oil") == "CL=F"
    assert vibe_quant_agent.resolve_ticker("AAPL") == "AAPL"


def test_rsi_calculation():
    agent = VibeQuantAgent()
    # Steady upward trend -> High RSI
    prices_up = np.linspace(100, 150, 30)
    ind_up = agent.compute_indicators(prices_up)
    assert ind_up["rsi"] > 70.0

    # Steady downward trend -> Low RSI
    prices_down = np.linspace(150, 100, 30)
    ind_down = agent.compute_indicators(prices_down)
    assert ind_down["rsi"] < 30.0


def test_bollinger_bands_ordering():
    agent = VibeQuantAgent()
    prices = np.sin(np.linspace(0, 10, 30)) * 10 + 100
    ind = agent.compute_indicators(prices)
    assert ind["bb_upper"] >= ind["bb_middle"]
    assert ind["bb_middle"] >= ind["bb_lower"]


def test_quant_analysis_snapshot():
    snapshot = vibe_quant_agent.analyze_ticker("NVDA")
    assert snapshot.ticker == "NVDA"
    assert snapshot.current_price > 0
    assert 0 <= snapshot.rsi_14 <= 100
    assert snapshot.stance in ["STRONG_BUY", "BULLISH", "NEUTRAL", "BEARISH", "STRONG_SELL"]
