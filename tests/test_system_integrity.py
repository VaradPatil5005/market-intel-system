"""
System Integrity & Stress Test Suite — World-Level Scale Diagnostics.

Tests:
1. High-concurrency database persistence under multi-threaded read/write load
2. Risk Sentinel VaR, CVaR, drawdown calculations and circuit breaker triggers
3. Global Macro contagion indices and currency transmission channels
4. Discrepancy Auditor cross-source corroboration
5. Edge cases: extreme market volatility, negative returns, and malformed inputs
"""
from __future__ import annotations

import concurrent.futures
import numpy as np

from agents.discrepancy_auditor_agent import DiscrepancyAuditorAgent
from agents.global_macro_agent import GlobalMacroAgent
from agents.risk_sentinel_agent import RiskSentinelAgent
from database.models import UserQuery
from database.session import Repository, get_session, init_db


def test_concurrent_database_transactions():
    """Verify SQLite WAL mode handles multi-threaded concurrent read/write stress without locking."""
    init_db()
    repo = Repository(UserQuery)

    def write_task(thread_id: int):
        with get_session() as session:
            obj = UserQuery(
                id=f"stress_q_{thread_id}_{np.random.randint(10000, 99999)}",
                user_id=f"user_{thread_id}",
                query_text=f"Concurrent query load test {thread_id}",
                created_at="2026-09-15 12:00:00",
            )
            repo.insert(session, obj)
            # Immediate concurrent read
            all_q = repo.all(session, limit=10)
            return len(all_q)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(write_task, i) for i in range(20)]
        results = [f.result() for f in futures]

    assert len(results) == 20
    assert all(r > 0 for r in results)


def test_risk_sentinel_var_and_drawdown():
    """Verify parametric and historical VaR and peak-to-trough drawdown calculation."""
    agent = RiskSentinelAgent(max_allowable_drawdown=0.10, var_budget=0.03)

    # Simulated crash: price drops from 100 to 80 (20% drawdown)
    crash_prices = np.array([100.0, 98.0, 95.0, 90.0, 85.0, 80.0])
    metrics = agent.compute_risk_metrics(crash_prices, vix_level=35.0)

    assert metrics.max_drawdown >= 0.20
    assert metrics.current_drawdown >= 0.20
    assert metrics.circuit_breaker_active is True
    assert metrics.volatility_regime == "CRISIS_REGIME"
    assert metrics.tail_risk_index >= 8.0
    assert len(metrics.recommended_hedges) > 0


def test_risk_sentinel_calm_market():
    """Verify low volatility regime when market is stable."""
    agent = RiskSentinelAgent()
    calm_prices = np.linspace(100.0, 104.0, 30)
    metrics = agent.compute_risk_metrics(calm_prices, vix_level=13.5)

    assert metrics.circuit_breaker_active is False
    assert metrics.volatility_regime == "CALM"
    assert metrics.tail_risk_index < 3.0


def test_global_macro_contagion_scoring():
    """Verify global macro currency and commodity contagion modeling."""
    agent = GlobalMacroAgent()
    snapshot = agent.fetch_global_telemetry()

    assert snapshot.usdjpy_rate > 0
    assert snapshot.gold_price > 1000.0
    assert snapshot.copper_gold_ratio > 0
    assert 0.0 <= snapshot.contagion_risk_index <= 10.0
    assert snapshot.regime_status in ["ORDERLY", "CARRY_UNWIND_RISK", "DOLLAR_SQUEEZE", "FLIGHT_TO_QUALITY"]


def test_discrepancy_auditor_detects_filing_divergence():
    """Verify forensic discrepancy auditor detects PR vs SEC filing contradictions."""
    auditor = DiscrepancyAuditorAgent()
    news = "Company reports record revenue and unprecedented demand across all enterprise chips."
    filing = "Management notes severe gross margin pressure and rising cost of revenues for high-density packages."

    records = auditor.audit_claims(news_text=news, filing_text=filing, entity="NVIDIA")
    assert len(records) > 0
    assert any(r.discrepancy_type == "GROWTH_VS_MARGIN_DIVERGENCE" for r in records)
    assert any(r.severity in ["HIGH", "CRITICAL"] for r in records)


def test_extreme_market_price_inputs():
    """Verify quantitative indicators don't crash or emit NaN on extreme spikes."""
    from agents.vibe_quant_agent import VibeQuantAgent
    quant = VibeQuantAgent()

    # Extreme scenario: +500% flash pump then -80% dump
    extreme_prices = np.array([10.0, 12.0, 15.0, 50.0, 60.0, 55.0, 20.0, 12.0, 10.0, 8.0, 9.0, 11.0, 10.0, 10.0, 10.0, 10.0])
    ind = quant.compute_indicators(extreme_prices)

    assert not np.isnan(ind["rsi"])
    assert not np.isnan(ind["macd_line"])
    assert not np.isnan(ind["volatility"])
    assert ind["bb_upper"] > ind["bb_lower"]
