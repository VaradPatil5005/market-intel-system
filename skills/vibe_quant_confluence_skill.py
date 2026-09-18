"""
Multi-Factor Technical Confluence Skill (RSI, MACD, Bollinger Bands).
"""
from typing import Dict, Any
from skills.base_skill import BaseMarketSkill

class VibeQuantConfluenceSkill(BaseMarketSkill):
    name: str = "quant_confluence_playbook"
    description: str = "Identifies high-probability technical setups when RSI, MACD, and Bollinger Bands align"
    category: str = "QUANT"
    initial_weight: float = 1.15

    def evaluate_trigger(self, market_context: Dict[str, Any]) -> bool:
        confluence = abs(market_context.get("confluence_score", 0.0))
        return confluence >= 1.5

    def execute(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        score = market_context.get("confluence_score", 0.0)
        bias = "ACCUMULATE_BULLISH" if score > 0 else "DISTRIBUTE_BEARISH"
        return {
            "skill": self.name,
            "action": bias,
            "confluence_score": score,
            "recommendation": f"High technical confluence ({score:+.2f}). Align directional allocation.",
            "confidence_weight": round(self.weight, 2)
        }
