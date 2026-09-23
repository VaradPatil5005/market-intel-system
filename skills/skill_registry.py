"""
Hermes-Agent Inspired Market Skills Registry.
Discovers, executes, and dynamically tracks win-rate accuracy for all market skills.
"""
from typing import Dict, List, Any
import logging
from skills.base_skill import BaseMarketSkill
from skills.chokepoint_hedging_skill import ChokepointHedgingSkill
from skills.sec_discrepancy_skill import SecDiscrepancySkill
from skills.microstructure_tca_skill import MicrostructureTcaSkill
from skills.carry_trade_unwind_skill import CarryTradeUnwindSkill
from skills.vibe_quant_confluence_skill import VibeQuantConfluenceSkill
from skills.agent_reach_research_skill import AgentReachResearchSkill

logger = logging.getLogger("SkillRegistry")

class SkillRegistry:
    """Registry coordinating dynamic market skill execution and self-learning adaptation."""

    def __init__(self):
        self.skills: Dict[str, BaseMarketSkill] = {
            "chokepoint_hedging": ChokepointHedgingSkill(),
            "sec_discrepancy": SecDiscrepancySkill(),
            "microstructure_tca": MicrostructureTcaSkill(),
            "carry_trade_unwind": CarryTradeUnwindSkill(),
            "quant_confluence": VibeQuantConfluenceSkill(),
            "agent_reach_research": AgentReachResearchSkill(),
        }

    def evaluate_and_execute_skills(self, market_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        for name, skill in self.skills.items():
            try:
                if skill.evaluate_trigger(market_context):
                    out = skill.execute(market_context)
                    results.append(out)
                    logger.info(f"[SkillRegistry] Triggered skill: {name}")
            except Exception as e:
                logger.error(f"[SkillRegistry] Failed executing skill {name}: {e}")
        return results

    def record_skill_feedback(self, skill_key: str, accuracy_score: float):
        if skill_key in self.skills:
            self.skills[skill_key].record_feedback(accuracy_score)
            logger.info(f"[SkillRegistry] Updated weight for {skill_key}: weight={self.skills[skill_key].weight:.2f}, win_rate={self.skills[skill_key].win_rate:.1%}")

    def get_skills_catalog(self) -> List[Dict[str, Any]]:
        catalog = []
        for key, s in self.skills.items():
            catalog.append({
                "SKILL_ID": key,
                "NAME": s.name,
                "CATEGORY": s.category,
                "WEIGHT": round(s.weight, 2),
                "INVOCATIONS": s.invocations,
                "WIN_RATE": f"{s.win_rate * 100:.1f}%",
                "DESCRIPTION": s.description
            })
        return catalog

skill_registry = SkillRegistry()
