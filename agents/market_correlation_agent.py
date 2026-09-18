"""
Market Correlation Agent — Cross-Entity Relationship Analysis.

Computes a correlation matrix across tracked entities based on their
historical sentiment polarity scores. Entities whose sentiment consistently
moves together may share:
  - Supply chain dependencies (TSMC ↔ Nvidia)
  - Competitive dynamics (Google ↔ Microsoft in AI)
  - Macro factor exposure (all semiconductors ↔ interest rate news)

This drives the Counterfactual Scenario Generator: if entity A shows a risk
signal and entity B has a high correlation with A, the agent generates a
downstream impact scenario for entity B automatically.

Output:
  - Correlation matrix as a dict of dicts (stored in pipeline state)
  - Supply chain dependency pairs (correlation > threshold)
  - Counterfactual scenario text blocks for the report

Graceful degradation:
  - If fewer than `correlation_min_observations` data points exist → skips
  - If scipy not installed → uses pure-Python Pearson correlation fallback
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from agents.base import BaseAgent
from database.models import Entity, SentimentResult
from database.session import Repository, Session
from utils.config import settings
from utils.logging_setup import get_logger

logger = get_logger("market_correlation_agent")

# Known supply chain / competitive dependency pairs (seed knowledge)
SUPPLY_CHAIN_MAP: Dict[str, List[str]] = {
    "nvidia": ["tsmc", "samsung", "asml", "arm"],
    "apple": ["tsmc", "qualcomm", "samsung", "foxconn"],
    "microsoft": ["openai", "nvidia", "amd"],
    "google": ["nvidia", "amd", "anthropic"],
    "meta": ["nvidia", "amd"],
    "amazon": ["nvidia", "amd", "qualcomm"],
    "anthropic": ["google", "amazon", "nvidia"],
    "openai": ["microsoft", "nvidia"],
}


def _pearson(x: List[float], y: List[float]) -> Optional[float]:
    """Pure-Python Pearson correlation coefficient."""
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    den_x = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    den_y = math.sqrt(sum((yi - my) ** 2 for yi in y))
    if den_x * den_y == 0:
        return None
    return round(num / (den_x * den_y), 4)


class MarketCorrelationAgent(BaseAgent):
    name = "market_correlation_agent"

    def run(
        self,
        session: Session,
        entities: List[Entity],
    ) -> Dict[str, Any]:
        """Compute correlation matrix and generate counterfactual scenarios.

        Returns:
            {
                "correlation_matrix": {entity1: {entity2: float, ...}, ...},
                "high_correlation_pairs": [(e1, e2, corr), ...],
                "counterfactual_scenarios": [str, ...],
                "supply_chain_pairs": [(e1, e2), ...]
            }
        """
        if not settings.enable_market_correlation:
            return {"correlation_matrix": {}, "high_correlation_pairs": [], "counterfactual_scenarios": [], "supply_chain_pairs": []}

        with self.run_tracked("market_correlation"):
            # Build sentiment time-series per entity
            all_sentiment = Repository(SentimentResult).all(session)
            series_by_entity: Dict[str, List[float]] = defaultdict(list)
            entity_id_map = {e.id: e.canonical_name for e in entities}

            for s in sorted(all_sentiment, key=lambda x: x.created_at):
                if s.entity_id and s.entity_id in entity_id_map:
                    name = entity_id_map[s.entity_id]
                    series_by_entity[name].append(s.polarity_score)

            # Filter entities with enough observations
            sufficient = {
                name: series
                for name, series in series_by_entity.items()
                if len(series) >= settings.correlation_min_observations
            }

            if len(sufficient) < 2:
                logger.info("MarketCorrelationAgent: insufficient sentiment history — skipping correlation.")
                return {"correlation_matrix": {}, "high_correlation_pairs": [], "counterfactual_scenarios": [], "supply_chain_pairs": []}

            # Compute pairwise Pearson correlations
            names = list(sufficient.keys())
            corr_matrix: Dict[str, Dict[str, float]] = {n: {} for n in names}
            high_corr_pairs: List[Tuple[str, str, float]] = []

            for i, n1 in enumerate(names):
                for j, n2 in enumerate(names):
                    if i >= j:
                        continue
                    # Align series by min-length
                    s1 = sufficient[n1]
                    s2 = sufficient[n2]
                    min_len = min(len(s1), len(s2))
                    corr = _pearson(s1[-min_len:], s2[-min_len:])
                    if corr is not None:
                        corr_matrix[n1][n2] = corr
                        corr_matrix[n2][n1] = corr
                        if abs(corr) > 0.65:
                            high_corr_pairs.append((n1, n2, corr))

            # Supply chain pairs from seed knowledge
            supply_pairs = []
            for entity in entities:
                name_lower = entity.canonical_name.lower()
                deps = SUPPLY_CHAIN_MAP.get(name_lower, [])
                for dep in deps:
                    for other in entities:
                        if other.canonical_name.lower() == dep:
                            supply_pairs.append((entity.canonical_name, other.canonical_name))

            # Generate counterfactual scenarios
            scenarios = []
            if settings.enable_counterfactual_scenarios:
                scenarios = self._generate_scenarios(
                    session, entities, high_corr_pairs, supply_pairs, all_sentiment
                )

            self.audit(
                session,
                step="market_correlation",
                action="correlation_computed",
                output_summary={
                    "entities_analyzed": len(names),
                    "high_corr_pairs": len(high_corr_pairs),
                    "supply_pairs": len(supply_pairs),
                    "scenarios": len(scenarios),
                },
            )

            logger.info(
                f"MarketCorrelationAgent: {len(names)} entities, "
                f"{len(high_corr_pairs)} high-correlation pairs, "
                f"{len(scenarios)} counterfactual scenarios."
            )

            return {
                "correlation_matrix": corr_matrix,
                "high_correlation_pairs": high_corr_pairs,
                "counterfactual_scenarios": scenarios,
                "supply_chain_pairs": supply_pairs,
            }

    # ------------------------------------------------------------------
    def _generate_scenarios(
        self,
        session: Session,
        entities: List[Entity],
        high_corr_pairs: List[Tuple[str, str, float]],
        supply_pairs: List[Tuple[str, str]],
        all_sentiment: List[SentimentResult],
    ) -> List[str]:
        """Generate counterfactual downstream impact scenarios."""
        scenarios = []

        # For each supply chain pair where one entity has negative recent sentiment
        entity_recent_sentiment: Dict[str, float] = {}
        entity_id_map = {e.id: e.canonical_name for e in entities}

        # Get most recent sentiment per entity
        sentiment_by_entity: Dict[str, List[SentimentResult]] = defaultdict(list)
        for s in all_sentiment:
            if s.entity_id and s.entity_id in entity_id_map:
                sentiment_by_entity[entity_id_map[s.entity_id]].append(s)

        for name, sentiments in sentiment_by_entity.items():
            if sentiments:
                recent = sorted(sentiments, key=lambda s: s.created_at)[-3:]
                entity_recent_sentiment[name] = sum(s.polarity_score for s in recent) / len(recent)

        # Supply chain impact scenarios
        for upstream, downstream in supply_pairs:
            upstream_sent = entity_recent_sentiment.get(upstream, 0.0)
            if upstream_sent < -0.1:   # upstream entity has negative sentiment
                scenarios.append(
                    f"️ COUNTERFACTUAL SCENARIO — Supply Chain Impact: "
                    f"{upstream} is showing negative sentiment (polarity={upstream_sent:.2f}). "
                    f"As a known supply chain dependency of {downstream}, disruptions at {upstream} "
                    f"could cascade to {downstream}'s production and delivery timelines. "
                    f"Monitor {downstream} for lagged negative sentiment over the next 1-2 cycles."
                )

        # Correlation-based contagion scenarios
        for e1, e2, corr in high_corr_pairs:
            if corr > 0.75:
                sent1 = entity_recent_sentiment.get(e1)
                sent2 = entity_recent_sentiment.get(e2)
                if sent1 is not None and sent2 is not None:
                    if sent1 < -0.2 and sent2 > 0.1:
                        scenarios.append(
                            f" CONTAGION RISK — {e1} and {e2} have historically correlated sentiment "
                            f"(r={corr:.2f}). {e1} is currently negative ({sent1:.2f}) while "
                            f"{e2} remains positive ({sent2:.2f}). Based on historical co-movement, "
                            f"{e2} sentiment may follow {e1}'s decline in the next reporting cycle."
                        )

        return scenarios[:8]   # cap at 8 scenarios per run
