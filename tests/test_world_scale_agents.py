"""
Unit and stress test suite for World-Scale Institutional Agents:
GeopoliticalRiskAgent, LiquidityOrderFlowAgent, ExecutionRouterAgent,
and the Network Resilience & Circuit Breaker engine.
"""

import pytest
import time
import threading
from agents.geopolitical_risk_agent import GeopoliticalRiskAgent
from agents.liquidity_order_flow_agent import LiquidityOrderFlowAgent
from agents.execution_router_agent import ExecutionRouterAgent
from utils.resilience import CircuitBreaker, CircuitBreakerOpenException, TokenBucketRateLimiter, resilient_market_fetch

def test_geopolitical_risk_normal_and_stress():
    agent = GeopoliticalRiskAgent()
    normal_res = agent.run({"entities": ["NVDA", "XOM"]})
    assert "composite_geopolitical_stress_index" in normal_res
    assert normal_res["geopolitical_regime"] in ["NORMAL", "ELEVATED_TENSION"]
    assert normal_res["brent_crude_risk_premium_usd"] >= 0.0

    # Test escalated scenario
    stress_res = agent.run({"stress_scenario": "MIDDLE_EAST_ESCALATION", "entities": ["XOM", "NVDA"]})
    assert stress_res["composite_geopolitical_stress_index"] > normal_res["composite_geopolitical_stress_index"]
    assert stress_res["brent_crude_risk_premium_usd"] > normal_res["brent_crude_risk_premium_usd"]
    assert stress_res["entity_vulnerabilities"]["XOM"]["vulnerability_score"] >= 60.0

def test_liquidity_order_flow_metrics():
    agent = LiquidityOrderFlowAgent()
    res = agent.run({
        "ticker": "NVDA",
        "price": 120.00,
        "trade_size_shares": 100000,
        "adv_shares": 50000000.0,
        "depth_bids": [5000, 10000, 15000],
        "depth_asks": [2000, 4000, 6000]
    })
    assert res["effective_spread_bps"] > 0.0
    assert res["order_book_imbalance_ratio"] > 0.0  # Bids exceed asks
    assert res["transaction_cost_analysis"]["total_estimated_slippage_bps"] > 0.0
    assert res["transaction_cost_analysis"]["trade_size_shares"] == 100000
    assert "routing_guidance" in res

def test_execution_router_twap_and_vwap():
    agent = ExecutionRouterAgent()
    order_qty = 60000
    res = agent.run({
        "ticker": "NVDA",
        "side": "BUY",
        "quantity": order_qty,
        "limit_price": 125.50,
        "algorithm": "TWAP",
        "num_slices": 6
    })
    assert res["total_slices"] == 6
    assert len(res["slices"]) == 6
    total_sliced = sum(s["quantity"] for s in res["slices"])
    assert total_sliced == order_qty  # Zero share leakage

    # Check FIX 4.4 serialization
    assert len(res["fix_messages"]) == 6
    first_fix = res["fix_messages"][0]
    assert "8=FIX.4.4" in first_fix
    assert "35=D" in first_fix
    assert "54=1" in first_fix  # BUY
    assert "100=" in first_fix  # ExDestination

def test_resilience_circuit_breaker_trips_and_recovers():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.2)

    def failing_call():
        raise ConnectionResetError("Remote gateway reset")

    # Call 1: fails
    with pytest.raises(ConnectionResetError):
        cb.call(failing_call)
    assert cb.state == "CLOSED"

    # Call 2: fails -> trips circuit breaker to OPEN
    with pytest.raises(ConnectionResetError):
        cb.call(failing_call)
    assert cb.state == "OPEN"

    # Call 3: fast-fails with CircuitBreakerOpenException without invoking func
    with pytest.raises(CircuitBreakerOpenException):
        cb.call(failing_call)

    # Wait for recovery timeout
    time.sleep(0.25)

    def successful_call():
        return "SUCCESS"

    # Call 4: probes in HALF_OPEN and succeeds, resetting to CLOSED
    result = cb.call(successful_call)
    assert result == "SUCCESS"
    assert cb.state == "CLOSED"

def test_resilience_token_bucket_rate_limiter():
    limiter = TokenBucketRateLimiter(capacity=3, refill_rate=2.0)
    # Drain initial capacity
    assert limiter.acquire(1.0, blocking=False) is True
    assert limiter.acquire(1.0, blocking=False) is True
    assert limiter.acquire(1.0, blocking=False) is True
    # Bucket now empty
    assert limiter.acquire(1.0, blocking=False) is False

def test_high_volume_concurrency_stress():
    geo_agent = GeopoliticalRiskAgent()
    liq_agent = LiquidityOrderFlowAgent()
    router_agent = ExecutionRouterAgent()

    errors = []

    def worker(worker_id: int):
        try:
            for _ in range(5):
                geo_res = geo_agent.run({"entities": ["NVDA", "AAPL"]})
                assert "composite_geopolitical_stress_index" in geo_res

                liq_res = liq_agent.run({"ticker": "AAPL", "price": 220.0, "trade_size_shares": 10000})
                assert "effective_spread_bps" in liq_res

                exec_res = router_agent.run({"ticker": "AAPL", "quantity": 10000, "algorithm": "VWAP"})
                assert exec_res["total_slices"] > 0
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Encountered concurrency errors: {errors}"
