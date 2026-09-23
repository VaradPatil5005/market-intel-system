"""
SIGNALORA Autonomous Agent Matrix.

Exposes the full catalog of autonomous intelligence agents with unified
metadata registry, lazy factory loading, and categorization.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

# Core & Ingestion Agents
from agents.base import BaseAgent
from agents.ingestion_agent import IngestionAgent
from agents.live_news_agent import LiveNewsAgent
from agents.price_data_agent import PriceDataAgent
from agents.credibility_agent import CredibilityAgent
from agents.grounding_gate_agent import GroundingGateAgent
from agents.reflexion_agent import ReflexionAgent

# Semantic & Context Agents
from agents.entity_resolution_agent import EntityResolutionAgent
from agents.sentiment_agent import SentimentAgent
from agents.trend_agent import TrendAgent
from agents.rag_agent import RagInsightAgent
from agents.deep_search_agent import DeepSearchAgent
from agents.confidence_agent import ConfidenceScoringAgent

# Forensic & Macro Agents
from agents.discrepancy_auditor_agent import DiscrepancyAuditorAgent
from agents.geopolitical_risk_agent import GeopoliticalRiskAgent
from agents.macro_rates_agent import MacroRatesAgent
from agents.global_macro_agent import GlobalMacroAgent

# Alpha & Strategy Agents
from agents.vibe_quant_agent import VibeQuantAgent
from agents.liquidity_order_flow_agent import LiquidityOrderFlowAgent
from agents.market_correlation_agent import MarketCorrelationAgent
from agents.forecasting_agent import ForecastingAgent
from agents.competitor_agent import CompetitorAgent
from agents.risk_sentinel_agent import RiskSentinelAgent
from agents.execution_router_agent import ExecutionRouterAgent

# Voice & Biometrics Agents
from agents.kim_voice_agent import KimVoiceAgent
from agents.friday_voice_agent import FridayVoiceAgent
from agents.voice_security_agent import VoiceSecurityAgent

# Learning, Memory & Synthesis Agents
from agents.hermes_self_learning_agent import HermesSelfLearningAgent
from agents.report_agent import ReportGenerationAgent
from agents.query_memory_agent import QueryMemoryAgent
from agents.live_daemon import LiveDaemon

# Metadata registry for all agents
AGENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "ingestion_agent": {
        "class": IngestionAgent,
        "category": "Ingestion & Data",
        "description": "High-throughput RSS, JSON, and financial stream parsing with fallback.",
    },
    "live_news_agent": {
        "class": LiveNewsAgent,
        "category": "Ingestion & Data",
        "description": "Dynamic multi-source market news collection across crypto, equities, and FX.",
    },
    "price_data_agent": {
        "class": PriceDataAgent,
        "category": "Ingestion & Data",
        "description": "Real-time quote enrichment, SMA-20/50, RSI-14, volatility, and VWAP.",
    },
    "credibility_agent": {
        "class": CredibilityAgent,
        "category": "Trust & Verification",
        "description": "Domain authority grading, recency decay penalization, and anti-spoof checks.",
    },
    "grounding_gate_agent": {
        "class": GroundingGateAgent,
        "category": "Trust & Verification",
        "description": "Strict numeric and citation verification preventing hallucinations in generated output.",
    },
    "reflexion_agent": {
        "class": ReflexionAgent,
        "category": "Trust & Verification",
        "description": "Self-critique engine checking reasoning bounds and statistical plausibility.",
    },
    "entity_resolution_agent": {
        "class": EntityResolutionAgent,
        "category": "Semantic & Context",
        "description": "Normalizes company names, tickers, and token addresses across unstructured text.",
    },
    "sentiment_agent": {
        "class": SentimentAgent,
        "category": "Semantic & Context",
        "description": "Lexicon and contextual sentiment scoring per entity.",
    },
    "trend_agent": {
        "class": TrendAgent,
        "category": "Semantic & Context",
        "description": "Statistical z-score keyword spike detection against historical baselines.",
    },
    "rag_agent": {
        "class": RagInsightAgent,
        "category": "Semantic & Context",
        "description": "ChromaDB vector and TF-IDF similarity recall over historical market precedents.",
    },
    "deep_search_agent": {
        "class": DeepSearchAgent,
        "category": "Semantic & Context",
        "description": "Multi-hop external web search and SEC EDGAR 8-K retrieval for breaking events.",
    },
    "confidence_agent": {
        "class": ConfidenceScoringAgent,
        "category": "Semantic & Context",
        "description": "Bayesian multi-factor confidence scoring and source conflict adjudication.",
    },
    "discrepancy_auditor_agent": {
        "class": DiscrepancyAuditorAgent,
        "category": "Forensic & Macro",
        "description": "SEC 10-Q forensic parser detecting revenue vs cash flow divergence.",
    },
    "geopolitical_risk_agent": {
        "class": GeopoliticalRiskAgent,
        "category": "Forensic & Macro",
        "description": "Maritime chokepoint monitor (Hormuz, Malacca, Taiwan Strait, Bab-el-Mandeb).",
    },
    "macro_rates_agent": {
        "class": MacroRatesAgent,
        "category": "Forensic & Macro",
        "description": "Sovereign yields, Fed futures, 2Y/10Y inversion tracking, and terminal rates.",
    },
    "global_macro_agent": {
        "class": GlobalMacroAgent,
        "category": "Forensic & Macro",
        "description": "Cross-asset macro regime monitor (DXY, WTI crude, Dr. Copper, gold).",
    },
    "vibe_quant_agent": {
        "class": VibeQuantAgent,
        "category": "Alpha & Strategy",
        "description": "Social retail sentiment velocity vs market microstructure confluence.",
    },
    "liquidity_order_flow_agent": {
        "class": LiquidityOrderFlowAgent,
        "category": "Alpha & Strategy",
        "description": "Level-2 book skew, bid/ask imbalance, and institutional dark pool prints.",
    },
    "market_correlation_agent": {
        "class": MarketCorrelationAgent,
        "category": "Alpha & Strategy",
        "description": "Dynamic rolling covariance matrices and cross-sector beta shifts.",
    },
    "forecasting_agent": {
        "class": ForecastingAgent,
        "category": "Alpha & Strategy",
        "description": "Multi-horizon directional forecasts with asymmetric confidence intervals.",
    },
    "competitor_agent": {
        "class": CompetitorAgent,
        "category": "Alpha & Strategy",
        "description": "Peer group margin benchmarking and competitive moat threat detection.",
    },
    "risk_sentinel_agent": {
        "class": RiskSentinelAgent,
        "category": "Alpha & Strategy",
        "description": "Value-at-Risk (VaR), tail risk hedging bounds, and maximum drawdown limits.",
    },
    "execution_router_agent": {
        "class": ExecutionRouterAgent,
        "category": "Alpha & Strategy",
        "description": "Algorithmic routing (TWAP, VWAP, POV) and transaction cost analysis (TCA).",
    },
    "kim_voice_agent": {
        "class": KimVoiceAgent,
        "category": "Voice & Biometrics",
        "description": "High-definition female executive voice briefing generator (Windows SAPI).",
    },
    "friday_voice_agent": {
        "class": FridayVoiceAgent,
        "category": "Voice & Biometrics",
        "description": "Conversational voice intelligence interface.",
    },
    "voice_security_agent": {
        "class": VoiceSecurityAgent,
        "category": "Voice & Biometrics",
        "description": "Wav2Vec 2.0 acoustic voiceprint registration and biometric auth.",
    },
    "hermes_self_learning_agent": {
        "class": HermesSelfLearningAgent,
        "category": "Learning & Synthesis",
        "description": "Autonomous closed-loop skill creation, execution tuning, and persistent recall.",
    },
    "report_agent": {
        "class": ReportGenerationAgent,
        "category": "Learning & Synthesis",
        "description": "Generates structured Markdown and JSON intelligence dossiers.",
    },
    "query_memory_agent": {
        "class": QueryMemoryAgent,
        "category": "Learning & Synthesis",
        "description": "Manages persistent analyst queries, user personalization, and context retrieval.",
    },
    "live_daemon": {
        "class": LiveDaemon,
        "category": "Learning & Synthesis",
        "description": "Autonomous background daemon orchestrating periodic pipeline cycles.",
    },
}


def get_agent(name: str, metrics: Optional[Any] = None) -> BaseAgent:
    """Instantiate an agent by its registered name."""
    if name not in AGENT_REGISTRY:
        raise KeyError(f"Agent '{name}' not found in AGENT_REGISTRY. Available: {list(AGENT_REGISTRY.keys())}")
    agent_cls = AGENT_REGISTRY[name]["class"]
    return agent_cls(metrics=metrics)


def list_agents() -> List[Dict[str, Any]]:
    """Return catalog of all registered agents."""
    return [
        {
            "name": name,
            "category": meta["category"],
            "class_name": meta["class"].__name__,
            "description": meta["description"],
        }
        for name, meta in AGENT_REGISTRY.items()
    ]


__all__ = [
    "BaseAgent",
    "IngestionAgent",
    "LiveNewsAgent",
    "PriceDataAgent",
    "CredibilityAgent",
    "GroundingGateAgent",
    "ReflexionAgent",
    "EntityResolutionAgent",
    "SentimentAgent",
    "TrendAgent",
    "RagInsightAgent",
    "DeepSearchAgent",
    "ConfidenceScoringAgent",
    "DiscrepancyAuditorAgent",
    "GeopoliticalRiskAgent",
    "MacroRatesAgent",
    "GlobalMacroAgent",
    "VibeQuantAgent",
    "LiquidityOrderFlowAgent",
    "MarketCorrelationAgent",
    "ForecastingAgent",
    "CompetitorAgent",
    "RiskSentinelAgent",
    "ExecutionRouterAgent",
    "KimVoiceAgent",
    "FridayVoiceAgent",
    "VoiceSecurityAgent",
    "HermesSelfLearningAgent",
    "ReportGenerationAgent",
    "QueryMemoryAgent",
    "LiveDaemon",
    "AGENT_REGISTRY",
    "get_agent",
    "list_agents",
]
