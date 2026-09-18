"""
Geopolitical Risk & Maritime Chokepoint Sentinel Agent.
Provides institutional surveillance of critical global trade arteries,
chokepoints (Hormuz, Malacca, Bab el-Mandeb, Suez, Panama, Taiwan Strait),
strategic export control regimes (semiconductors, rare earths, LNG),
and calculates the Composite Geopolitical Stress Index (CGSI).
"""

from typing import Dict, Any, List, Optional
import logging
from agents.base import BaseAgent
from utils.resilience import resilient_market_fetch
from utils.metrics import MetricsCollector

logger = logging.getLogger("GeopoliticalRiskAgent")

class GeopoliticalRiskAgent(BaseAgent):
    """
    Monitors global geopolitical friction, maritime transit disruptions,
    and strategic resource dependencies for institutional macro risk parity.
    """

    name: str = "geopolitical_risk_agent"

    CHOKEPOINTS = {
        "STRAIT_OF_HORMUZ": {
            "name": "Strait of Hormuz",
            "throughput_pct": 21.0,
            "commodity": "Crude Oil / Condensates (21M bbl/day)",
            "normal_risk": 15.0,
            "key_actors": ["Iran", "Oman", "US Fifth Fleet", "Saudi Arabia"]
        },
        "BAB_EL_MANDEB": {
            "name": "Bab el-Mandeb / Red Sea",
            "throughput_pct": 12.0,
            "commodity": "Containerized Freight & European Crude",
            "normal_risk": 35.0,
            "key_actors": ["Houthi Militia", "Yemen", "US Operation Prosperity Guardian", "Egypt"]
        },
        "MALACCA_STRAIT": {
            "name": "Strait of Malacca",
            "throughput_pct": 25.0,
            "commodity": "Asia-Bound Energy & Manufactured Goods",
            "normal_risk": 10.0,
            "key_actors": ["Singapore", "Malaysia", "Indonesia", "China PLAN"]
        },
        "TAIWAN_STRAIT": {
            "name": "Taiwan Strait",
            "throughput_pct": 48.0,
            "commodity": "Advanced Semiconductors (<3nm Foundry) & Tech Hardware",
            "normal_risk": 40.0,
            "key_actors": ["Taiwan (TSMC)", "China", "United States", "Japan"]
        },
        "PANAMA_CANAL": {
            "name": "Panama Canal",
            "throughput_pct": 5.0,
            "commodity": "US Gulf Coast LNG / Agricultural Bulk to Asia",
            "normal_risk": 12.0,
            "key_actors": ["Panama Canal Authority (ACP)", "US Shipping"]
        }
    }

    def __init__(self, metrics: Optional[MetricsCollector] = None):
        super().__init__(metrics=metrics)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates current geopolitical tensions, chokepoint threat vectors,
        and assigns risk scores and contingency alerts.
        """
        logger.info("[GeopoliticalRiskAgent] Initiating global maritime & sovereign risk scan.")
        stress_override = input_data.get("stress_scenario")
        target_entities = input_data.get("entities", ["NVDA", "AAPL", "XOM", "TSM"])

        chokepoint_status = self._assess_chokepoints(stress_override)
        composite_index = self._calculate_composite_stress(chokepoint_status)
        crude_premium = self._estimate_brent_risk_premium(chokepoint_status)
        entity_vulnerability = self._evaluate_equity_exposure(target_entities, chokepoint_status)

        regime = "NORMAL"
        if composite_index >= 70.0:
            regime = "CRITICAL_DISRUPTION"
        elif composite_index >= 45.0:
            regime = "ELEVATED_TENSION"

        return {
            "agent": self.name,
            "composite_geopolitical_stress_index": round(composite_index, 2),
            "geopolitical_regime": regime,
            "brent_crude_risk_premium_usd": round(crude_premium, 2),
            "chokepoints": chokepoint_status,
            "entity_vulnerabilities": entity_vulnerability,
            "strategic_implications": self._generate_strategic_briefing(regime, composite_index, crude_premium)
        }

    def _assess_chokepoints(self, scenario: str = None) -> Dict[str, Dict[str, Any]]:
        status = {}
        for key, info in self.CHOKEPOINTS.items():
            base_risk = info["normal_risk"]
            threat_level = "MODERATE"

            if scenario == "MIDDLE_EAST_ESCALATION":
                if key in ["STRAIT_OF_HORMUZ", "BAB_EL_MANDEB"]:
                    base_risk = min(100.0, base_risk + 45.0)
            elif scenario == "CROSS_STRAIT_BLOCKADE":
                if key == "TAIWAN_STRAIT":
                    base_risk = 92.0
                elif key == "MALACCA_STRAIT":
                    base_risk = 55.0

            if base_risk >= 75.0:
                threat_level = "CRITICAL_HAZARD"
            elif base_risk >= 40.0:
                threat_level = "HIGH_ALERT"
            elif base_risk >= 20.0:
                threat_level = "GUARDED"
            else:
                threat_level = "SECURE"

            status[key] = {
                "name": info["name"],
                "risk_score": base_risk,
                "threat_level": threat_level,
                "primary_commodity": info["commodity"],
                "global_throughput_pct": info["throughput_pct"],
                "routing_diversion_cost_est_usd": round(base_risk * 18500.0, 2)
            }
        return status

    def _calculate_composite_stress(self, chokepoints: Dict[str, Dict[str, Any]]) -> float:
        total_weighted_risk = 0.0
        total_weight = 0.0
        for cp in chokepoints.values():
            weight = cp["global_throughput_pct"]
            total_weighted_risk += cp["risk_score"] * weight
            total_weight += weight
        return total_weighted_risk / max(total_weight, 1.0)

    def _estimate_brent_risk_premium(self, chokepoints: Dict[str, Dict[str, Any]]) -> float:
        hormuz_risk = chokepoints.get("STRAIT_OF_HORMUZ", {}).get("risk_score", 15.0)
        red_sea_risk = chokepoints.get("BAB_EL_MANDEB", {}).get("risk_score", 35.0)
        excess_hormuz = max(0.0, hormuz_risk - 15.0)
        excess_red_sea = max(0.0, red_sea_risk - 35.0)
        return (excess_hormuz * 0.32) + (excess_red_sea * 0.11)

    def _evaluate_equity_exposure(self, entities: List[str], chokepoints: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        taiwan_risk = chokepoints.get("TAIWAN_STRAIT", {}).get("risk_score", 40.0)
        hormuz_risk = chokepoints.get("STRAIT_OF_HORMUZ", {}).get("risk_score", 15.0)
        results = {}
        for ent in entities:
            ent_upper = ent.upper()
            if ent_upper in ["NVDA", "AAPL", "AMD", "TSM", "QCOM", "AVGO"]:
                score = round(min(100.0, (taiwan_risk * 0.85) + 10.0), 1)
                factor = "Taiwan Foundry & Advanced Substrate Dependency"
            elif ent_upper in ["XOM", "CVX", "SHEL", "BP"]:
                score = round(min(100.0, (hormuz_risk * 0.90) + 15.0), 1)
                factor = "Persian Gulf Upstream & Tanker War Risk Premium"
            else:
                score = round((taiwan_risk * 0.2) + (hormuz_risk * 0.2), 1)
                factor = "Secondary Macro Supply Chain Inflation"

            results[ent_upper] = {
                "vulnerability_score": score,
                "primary_threat_vector": factor,
                "diversification_hedging_mandate": score >= 60.0
            }
        return results

    def _generate_strategic_briefing(self, regime: str, cgsi: float, crude_premium: float) -> str:
        return (
            f"Composite Geopolitical Stress Index is at {cgsi:.1f} ({regime}). "
            f"Crude risk premium priced at ${crude_premium:.2f}/bbl. "
            f"Institutional desks should evaluate maritime shipping war-risk surcharges "
            f"and critical semiconductor inventory safety buffers."
        )
