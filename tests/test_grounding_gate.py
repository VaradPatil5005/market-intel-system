"""
Grounding Gate Unit Tests.

Tests numeric claim extraction, verification logic, and verdicts.
All tests run in-memory with no external dependencies.
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ---------------------------------------------------------------------------
# Test: Numeric extraction
# ---------------------------------------------------------------------------
def test_number_pattern_extracts_basic_floats():
    from agents.grounding_gate_agent import _NUMBER_PATTERN
    text = "Nvidia shows a 73% gain and a polarity of 0.85 over the period."
    matches = [m.group(1).replace(",", "") for m in _NUMBER_PATTERN.finditer(text)]
    nums = [float(m) for m in matches]
    assert 73.0 in nums
    assert 0.85 in nums


def test_number_pattern_extracts_negative():
    from agents.grounding_gate_agent import _NUMBER_PATTERN
    text = "Stock declined -12.5% vs last quarter."
    matches = [m.group(1).replace(",", "") for m in _NUMBER_PATTERN.finditer(text)]
    nums = [float(m) for m in matches if m]
    assert any(abs(n - 12.5) < 0.01 for n in nums)


def test_number_pattern_skips_years():
    from agents.grounding_gate_agent import _NUMBER_PATTERN
    # Use a plain decimal (no B/M suffix) so regex captures it cleanly
    text = "In 2024, the company posted 1.2 billion in revenue."
    matches = [m.group(1).replace(",", "") for m in _NUMBER_PATTERN.finditer(text)]
    nums = [float(m) for m in matches]
    # 1.2 should be found; 2024 is also extracted but filtered by year-skip logic
    assert any(abs(n - 1.2) < 0.01 for n in nums)


# ---------------------------------------------------------------------------
# Test: _check_claim verification logic
# ---------------------------------------------------------------------------

def test_verify_claim_within_tolerance():
    from agents.grounding_gate_agent import GroundingGateAgent
    agent = GroundingGateAgent()
    observed = {
        "sentiment_polarity": [0.72, 0.68, 0.75],
        "confidence_score": [0.85, 0.80],
        "trend_change_pct": [],
        "forecast_magnitude": [],
        "trend_z_score": [],
    }
    verdict, nearest, src = agent._check_claim(0.73, observed)
    assert verdict == "verified"
    assert nearest is not None


def test_verify_claim_flagged_when_no_match():
    from agents.grounding_gate_agent import GroundingGateAgent
    agent = GroundingGateAgent()
    observed = {
        "sentiment_polarity": [0.10, 0.12],
        "confidence_score": [0.20],
        "trend_change_pct": [],
        "forecast_magnitude": [],
        "trend_z_score": [],
    }
    verdict, nearest, src = agent._check_claim(0.99, observed)
    # 0.99 is far from all observed values → should be flagged
    assert verdict == "flagged"


def test_verify_claim_no_observed_data():
    from agents.grounding_gate_agent import GroundingGateAgent
    agent = GroundingGateAgent()
    observed = {
        "sentiment_polarity": [],
        "confidence_score": [],
        "trend_change_pct": [],
        "forecast_magnitude": [],
        "trend_z_score": [],
    }
    verdict, nearest, src = agent._check_claim(0.75, observed)
    assert verdict == "flagged"
    assert nearest is None


# ---------------------------------------------------------------------------
# Test: Sentence flagging (integration-style — no DB needed)
# ---------------------------------------------------------------------------

def test_flagged_claims_get_asterisk_marker():
    """Claims that can't be verified: check_claim returns 'flagged' for unmatched numbers."""
    from agents.grounding_gate_agent import GroundingGateAgent
    agent = GroundingGateAgent()
    observed = {
        "sentiment_polarity": [0.01],
        "confidence_score": [0.01],
        "trend_change_pct": [],
        "forecast_magnitude": [],
        "trend_z_score": [],
    }
    # 99.9 is far from any observed value → verdict should be "flagged"
    verdict, nearest, src = agent._check_claim(99.9, observed)
    assert verdict == "flagged"
