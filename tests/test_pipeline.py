"""
Smoke test: runs the full pipeline against a throwaway SQLite database
and asserts the major artifacts were produced. Not a substitute for
per-agent unit tests, but verifies the wiring end to end.

Run with: python -m pytest tests/test_pipeline.py -v
(or simply: python tests/test_pipeline.py)
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Ensure project root is importable when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_full_pipeline_runs_end_to_end():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/test_market_intel.db"
        os.environ["EXPORT_DIR"] = f"{tmp}/exports"
        os.environ["CHECKPOINT_DIR"] = f"{tmp}/checkpoints"
        os.environ["LOG_DIR"] = f"{tmp}/logs"
        os.environ["CHROMA_DIR"] = f"{tmp}/chroma"

        # Re-import settings-dependent modules fresh with the env above.
        import importlib

        import utils.config as config_module

        importlib.reload(config_module)

        from database.session import get_session, init_db
        from orchestration.graph import run_pipeline
        from utils.metrics import MetricsCollector

        init_db()
        metrics = MetricsCollector()
        final_state = run_pipeline(metrics)

        assert final_state.get("error") is None, f"Pipeline reported an error: {final_state.get('error')}"
        assert final_state.get("raw_sources"), "No sources were ingested"
        assert final_state.get("entities"), "No entities were resolved"
        assert final_state.get("confidence_scores"), "No confidence scores were produced"
        assert final_state.get("report") is not None, "No report was generated"

        with get_session() as session:
            metrics.persist(session, final_state["run_id"])

        print("Smoke test passed:", metrics.summary())


if __name__ == "__main__":
    test_full_pipeline_runs_end_to_end()
    print("OK")
