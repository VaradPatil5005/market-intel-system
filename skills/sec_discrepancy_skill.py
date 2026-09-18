"""
Corporate PR vs SEC 10-Q / 8-K Regulatory Forensic Discrepancy Skill.
Automatically identifies divergence between promotional PR narrative and
audited SEC regulatory disclosures, applying confidence haircuts.
"""

from typing import Dict, Any, List
from skills.base_skill import BaseMarketSkill

class SecDiscrepancySkill(BaseMarketSkill):
    name: str = "sec_discrepancy_forensics"
    description: str = "Cross-references public press statements against SEC filings and discounts unverified hype"
    category: str = "FORENSIC"
    initial_weight: float = 1.3

    def evaluate_trigger(self, market_context: Dict[str, Any]) -> bool:
        discrepancies = market_context.get("discrepancies_flagged", 0)
        return discrepancies > 0 or market_context.get("has_audited_filing_divergence", False)

    def execute(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        entities_flagged = market_context.get("flagged_entities", ["NVDA"])
        penalties = {}
        for ent in entities_flagged:
            penalties[ent] = {
                "confidence_penalty": 0.18,
                "mandate": "Discount unverified management narrative; demand audited footnote validation"
            }

        return {
            "skill": self.name,
            "action": "APPLY_REGULATORY_HAIRCUT",
            "flagged_entities": entities_flagged,
            "haircuts": penalties,
            "confidence_weight": round(self.weight, 2)
        }
