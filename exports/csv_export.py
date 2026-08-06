"""
CSV Export Helpers.

Exports each dataset to its own CSV file with predictable, stable
filenames. Safe to run repeatedly — each export overwrites its file
rather than appending, so re-running the pipeline never produces
duplicate or stale rows.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

from utils.config import settings
from utils.logging_setup import get_logger

logger = get_logger("csv_export")


def export_table_to_csv(rows: List[Dict], filename: str) -> Path:
    out_dir = Path(settings.export_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename

    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    logger.info(f"Exported {len(rows)} row(s) to {path}")
    return path


def export_many(tables: Dict[str, List[Dict]]) -> Dict[str, Path]:
    """tables: {logical_name: rows} -> {logical_name: written_path}"""
    written = {}
    for name, rows in tables.items():
        written[name] = export_table_to_csv(rows, f"{name}.csv")
    return written
