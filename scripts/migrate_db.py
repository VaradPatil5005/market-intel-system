#!/usr/bin/env python
"""
Database migration script — adds columns and tables introduced in v2.1.

Safe to run multiple times (idempotent): uses ALTER TABLE ... ADD COLUMN IF NOT EXISTS
logic and CREATE TABLE IF NOT EXISTS so it won't fail if columns/tables already exist.

Usage:
    python scripts/migrate_db.py
    python scripts/migrate_db.py --db-url sqlite:///path/to/custom.db
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make project root importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text  # noqa: E402


def _column_exists(conn, table: str, column: str) -> bool:
    """Check if a column exists in a SQLite table."""
    result = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(row[1] == column for row in result)


def _table_exists(conn, table: str) -> bool:
    result = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table}
    ).fetchone()
    return result is not None


def run_migrations(db_url: str) -> None:
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    engine = create_engine(db_url, connect_args=connect_args, future=True)

    with engine.connect() as conn:
        print(f"Connected to: {db_url}")

        # ── v2.1 migrations ────────────────────────────────────────────────

        # 1. insights: add run_id (was missing in original schema.sql)
        if _table_exists(conn, "insights") and not _column_exists(conn, "insights", "run_id"):
            conn.execute(text("ALTER TABLE insights ADD COLUMN run_id TEXT NOT NULL DEFAULT ''"))
            print("  ✓ insights.run_id added")

        # 2. insights: add insight_type taxonomy column
        if _table_exists(conn, "insights") and not _column_exists(conn, "insights", "insight_type"):
            conn.execute(text("ALTER TABLE insights ADD COLUMN insight_type TEXT NOT NULL DEFAULT 'analysis'"))
            print("  ✓ insights.insight_type added (default: 'analysis')")
        else:
            print("  · insights.insight_type already exists, skipping")

        # 3. trend_results: add v2 statistical columns
        trend_v2_cols = [
            ("ewma_mean", "REAL"),
            ("ewma_std", "REAL"),
            ("z_score", "REAL"),
            ("is_anomalous", "INTEGER DEFAULT 0"),
        ]
        for col_name, col_type in trend_v2_cols:
            if _table_exists(conn, "trend_results") and not _column_exists(conn, "trend_results", col_name):
                conn.execute(text(f"ALTER TABLE trend_results ADD COLUMN {col_name} {col_type}"))
                print(f"  ✓ trend_results.{col_name} added")

        # 4. Create new v2 tables (idempotent — CREATE TABLE IF NOT EXISTS)
        new_tables = [
            (
                "forecast_results",
                """CREATE TABLE IF NOT EXISTS forecast_results (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    entity_id TEXT,
                    entity_name TEXT NOT NULL,
                    predicted_direction TEXT NOT NULL,
                    predicted_magnitude REAL,
                    observations_used INTEGER DEFAULT 0,
                    model_used TEXT NOT NULL,
                    confidence REAL,
                    created_at TEXT NOT NULL
                )""",
            ),
            (
                "user_queries",
                """CREATE TABLE IF NOT EXISTS user_queries (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    query_text TEXT NOT NULL,
                    extracted_entities TEXT,
                    intent_category TEXT,
                    run_id TEXT,
                    created_at TEXT NOT NULL
                )""",
            ),
            (
                "user_interest_profiles",
                """CREATE TABLE IF NOT EXISTS user_interest_profiles (
                    user_id TEXT PRIMARY KEY,
                    watchlist_override TEXT,
                    risk_appetite TEXT DEFAULT 'moderate',
                    preferred_depth TEXT DEFAULT 'standard',
                    top_categories TEXT,
                    query_count INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL
                )""",
            ),
            (
                "agent_learnings",
                """CREATE TABLE IF NOT EXISTS agent_learnings (
                    id TEXT PRIMARY KEY,
                    source_insight_id TEXT,
                    entity_name TEXT,
                    category TEXT,
                    human_action TEXT NOT NULL,
                    reviewer_note TEXT,
                    lesson_text TEXT NOT NULL,
                    lesson_type TEXT,
                    lesson_embedding TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                )""",
            ),
            (
                "grounding_records",
                """CREATE TABLE IF NOT EXISTS grounding_records (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    claim_text TEXT NOT NULL,
                    claimed_value TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    nearest_observed_value TEXT,
                    evidence_source TEXT,
                    created_at TEXT NOT NULL
                )""",
            ),
            (
                "price_snapshots",
                """CREATE TABLE IF NOT EXISTS price_snapshots (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    entity_id TEXT,
                    entity_name TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    current_price REAL,
                    price_7d_return_pct REAL,
                    price_30d_return_pct REAL,
                    volatility_30d REAL,
                    rsi_14 REAL,
                    bb_squeeze INTEGER DEFAULT 0,
                    volume_anomaly INTEGER DEFAULT 0,
                    data_source TEXT DEFAULT 'yfinance',
                    fetched_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )""",
            ),
            (
                "review_queue",
                """CREATE TABLE IF NOT EXISTS review_queue (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    flagged_count INTEGER DEFAULT 0,
                    avg_confidence REAL,
                    summary_json TEXT,
                    reviewer_notes TEXT,
                    reviewed_by TEXT,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT
                )""",
            ),
        ]

        for table_name, ddl in new_tables:
            conn.execute(text(ddl))
            print(f"  ✓ {table_name} table ensured")

        conn.commit()
        print("\nMigration complete. All changes are idempotent — safe to re-run.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply v2.1 database migrations.")
    parser.add_argument(
        "--db-url",
        default=None,
        help="SQLAlchemy database URL (default: reads DATABASE_URL env or settings default)",
    )
    args = parser.parse_args()

    if args.db_url:
        db_url = args.db_url
    else:
        from utils.config import settings
        db_url = settings.database_url

    run_migrations(db_url)
