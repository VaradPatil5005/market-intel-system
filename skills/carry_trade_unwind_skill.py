"""
USD/JPY Carry Trade Unwind & Liquidity Contagion Skill.
"""
from typing import Dict, Any
from skills.base_skill import BaseMarketSkill

class CarryTradeUnwindSkill(BaseMarketSkill):
    name: str = "carry_trade_unwind_playbook"
    description: str = "Detects rapid Yen appreciation and warns of global leveraged carry unwind risks"
    category: str = "MACRO"
    initial_weight: float = 1.25

    def evaluate_trigger(self, market_context: Dict[str, Any]) -> bool:
        usdjpy_change = market_context.get("usdjpy_change_pct", 0.0)
        return usdjpy_change <= -1.2 or market_context.get("contagion_risk_index", 0) >= 6

    def execute(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "skill": self.name,
            "action": "ALERT_CARRY_UNWIND",
            "warning": "Yen surging rapidly against USD indicates leveraged carry trade liquidation across global equities",
            "defensive_rebalancing": "Trim high-beta tech, raise USD cash buffer, long gold as flight-to-safety",
            "confidence_weight": round(self.weight, 2)
        }
