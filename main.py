"""
Multi-Agent Market Intelligence System — main entry point.

Runs the full pipeline once, end to end:
  ingest -> credibility -> entity resolution -> sentiment -> trend
  -> RAG insights -> confidence scoring -> (human review if needed)
  -> report generation -> Power BI / CSV export

Usage:
    python main.py
"""
from __future__ import annotations

import sys

from database.session import get_session, init_db
from exports.powerbi_export import export_all_for_powerbi
from exports.report_format import save_report, to_readable_text
from orchestration.checkpointing import list_checkpoints
from orchestration.crew_tasks import run_synthesis_crew
from orchestration.graph import run_pipeline
from utils.logging_setup import get_logger
from utils.metrics import MetricsCollector

logger = get_logger("main")


def main() -> int:
    logger.info("Initializing database ...")
    init_db()

    metrics = MetricsCollector()

    logger.info("Starting Market Intelligence pipeline run ...")
    final_state = run_pipeline(metrics)

    run_id = final_state.get("run_id")
    report = final_state.get("report")

    if final_state.get("error"):
        logger.error(f"Pipeline halted with error: {final_state['error']}")
        return 1

    if final_state.get("human_approved") is False:
        logger.info("Run ended: batch was rejected during human review. No report published.")
        with get_session() as session:
            metrics.persist(session, run_id)
        return 0

    if report is None:
        logger.error("Pipeline completed without producing a report.")
        return 1

    # Persist metrics + run Power BI / CSV exports + write readable report.
    with get_session() as session:
        metrics.persist(session, run_id)
        exported_paths = export_all_for_powerbi(session)

    saved_paths = save_report(report)

    # Optional CrewAI narrative synthesis layer (degrades gracefully offline).
    insights_dicts = [
        {"category": i.category, "text": i.text}
        for i in final_state.get("rag_insights", [])
    ]
    narrative = run_synthesis_crew(insights_dicts)

    print("\n" + to_readable_text(report))
    print("\n--- CrewAI narrative synthesis (or deterministic fallback) ---")
    print(narrative)

    print("\n--- Run summary ---")
    for key, value in metrics.summary().items():
        print(f"{key}: {value}")

    print("\n--- Checkpoints saved for this run ---")
    with get_session() as session:
        for cp in list_checkpoints(session, run_id):
            print(f"  [{cp.created_at}] {cp.node_name}")

    print("\n--- Files written ---")
    for name, path in exported_paths.items():
        print(f"  csv: {path}")
    for kind, path in saved_paths.items():
        print(f"  report ({kind}): {path}")

    logger.info(f"Run {run_id} complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
