"""
Maritime Chokepoint Escalation & Commodity Supply Disruption Skill.
Triggers dynamic hedges when global maritime choke points (Hormuz, Red Sea, Taiwan)
exceed threat thresholds.
"""

from typing import Dict, Any
from skills.base_skill import BaseMarketSkill

class ChokepointHedgingSkill(BaseMarketSkill):
    name: str = "chokepoint_hedging_playbook"
    description: str = "Hedges Persian Gulf and Taiwan Strait shipping risk by overweighting energy and foundries"
    category: str = "GEOPOLITICAL"
    initial_weight: float = 1.2

    def evaluate_trigger(self, market_context: Dict[str, Any]) -> bool:
        stress_idx = market_context.get("composite_geopolitical_stress_index", 0.0)
        return stress_idx >= 45.0

    def execute(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        stress_idx = market_context.get("composite_geopolitical_stress_index", 50.0)
        crude_prem = market_context.get("brent_crude_risk_premium_usd", 4.0)

        tactical_hedges = [
            "Overweight Brent Crude Futures (CL1! / BZ1!) to capture shipping premium",
            "Long Defense / Aerospace primes (RTX, LMT) as geopolitical volatility hedge",
            "Underweight high-energy European industrials and containerized cargo liners"
        ]
        if market_context.get("taiwan_threat_score", 0.0) >= 70.0:
            tactical_hedges.append("Mandate 15% delta put hedge on Taiwan semiconductor exposures (TSM, NVDA)")

        return {
            "skill": self.name,
            "action": "ENGAGE_GEOPOLITICAL_HEDGES",
            "stress_index": stress_idx,
            "crude_premium_usd": crude_prem,
            "tactical_hedges": tactical_hedges,
            "confidence_weight": round(self.weight, 2)
        }
