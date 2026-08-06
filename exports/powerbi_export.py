"""
Power BI Export Utilities.

Pulls every reporting-relevant table from SQL and writes clean,
analysis-friendly CSV datasets that can be loaded directly into Power
BI (Get Data -> Text/CSV, or a folder-based combine query).
"""
from __future__ import annotations

from typing import Dict, List

from database.models import (
    AgentMetric,
    ConfidenceScore,
    Entity,
    ForecastResult,
    Insight,
    RawSource,
    ReportExport,
    SentimentResult,
    TrendResult,
)
from database.session import Repository, Session
from exports.csv_export import export_many
from utils.logging_setup import get_logger

logger = get_logger("powerbi_export")

TABLE_MAP = {
    "raw_sources": RawSource,
    "entities": Entity,
    "sentiment_results": SentimentResult,
    "trend_results": TrendResult,
    "insights": Insight,
    "confidence_scores": ConfidenceScore,
    "forecast_results": ForecastResult,
    "report_exports": ReportExport,
    "agent_metrics": AgentMetric,
}


def export_all_for_powerbi(session: Session) -> Dict[str, str]:
    tables: Dict[str, List[Dict]] = {}
    for logical_name, model in TABLE_MAP.items():
        repo = Repository(model)
        rows = repo.to_dicts(repo.all(session))
        tables[logical_name] = rows

    written_paths = export_many(tables)
    logger.info(f"Power BI export complete: {len(written_paths)} dataset(s) written.")
    return {name: str(path) for name, path in written_paths.items()}
