"""
Agent-Reach Multi-Platform Autonomous Research Skill.

Encapsulates autonomous multi-platform internet research, equity telemetry (Xueqiu),
and social sentiment discovery into an executable Hermes-agent skill playbook.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from skills.base_skill import BaseMarketSkill
from utils.agent_reach_service import reach_service

logger = logging.getLogger(__name__)


class AgentReachResearchSkill(BaseMarketSkill):
    """
    Autonomous multi-platform internet and social intelligence playbook.
    Triggers on entity anomaly, breaking macro shifts, or direct analyst research mandates.
    """

    name: str = "agent_reach_research"
    description: str = "Multi-platform internet research, Xueqiu equity telemetry, and social sentiment gathering."
    category: str = "RESEARCH"
    initial_weight: float = 1.2

    def evaluate_trigger(self, market_context: Dict[str, Any]) -> bool:
        """
        Activates if:
        1. Context requests explicit research query or entity lookup
        2. Anomalous entity has Z-score spike > 1.8
        3. Market volatility regime is HIGH or STRESSED
        """
        if market_context.get("research_query") or market_context.get("target_entity"):
            return True

        anomalies = market_context.get("anomalous_entities", [])
        if anomalies:
            return True

        z_score = market_context.get("z_score", 0.0)
        if abs(z_score) >= 1.8:
            return True

        regime = market_context.get("volatility_regime", "NORMAL")
        if regime in ("HIGH", "STRESSED", "CRITICAL"):
            return True

        return False

    def execute(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes multi-platform research across Web, Xueqiu, and Social channels.
        Synthesizes corroborated market intelligence.
        """
        target = market_context.get("target_entity") or market_context.get("research_query") or "Macro Market"
        if isinstance(target, list) and target:
            target = target[0]

        logger.info(f"[AgentReachResearchSkill] Executing multi-platform research for '{target}'")

        # 1. Web research
        web_hits = reach_service.search_web(f"{target} financial market catalysts risk", max_results=3)

        # 2. Xueqiu equity intel
        stock_data = reach_service.get_stock_intel(str(target))

        # 3. Social discussions
        social_hits = reach_service.search_social_discussions(str(target), limit=3)

        findings: List[str] = []
        for w in web_hits:
            findings.append(f"Web ({w.get('source')}): {w.get('title')}")

        quote = stock_data.get("quote", {})
        if quote and quote.get("current"):
            findings.append(
                f"Xueqiu: Current Price ${quote.get('current')}, Intraday {quote.get('percent')}%, "
                f"PE(TTM): {quote.get('pe_ttm')}"
            )

        for s in social_hits:
            findings.append(f"Social ({s.get('platform')}): {s.get('title')}")

        total_corroborating_sources = len(web_hits) + (1 if quote else 0) + len(social_hits)
        confidence = min(0.95, 0.50 + 0.10 * total_corroborating_sources)

        recommendation = "MONITOR_FLOWS"
        if total_corroborating_sources >= 4:
            recommendation = "HIGH_CONVICTION_DISPATCH"
        elif total_corroborating_sources >= 2:
            recommendation = "CORROBORATED_SURVEILLANCE"

        return {
            "skill": self.name,
            "target": target,
            "category": self.category,
            "corroborating_sources_count": total_corroborating_sources,
            "confidence_score": round(confidence, 2),
            "recommendation": recommendation,
            "findings": findings[:6],
            "raw_intelligence": {
                "web": web_hits,
                "quote": quote,
                "social": social_hits,
            },
        }
