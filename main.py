"""
SIGNALORA: Multi-Agent Market Intelligence System — Institutional CLI Entry Point.

Executes the LangGraph autonomous pipeline end-to-end with customizable CLI flags:
  python main.py --min-confidence 0.85 --export-powerbi --seed 42 --mode auto

Usage Examples:
    python main.py
    python main.py --min-confidence 0.80 --export-powerbi
    python main.py --mode queue --simulate-failure-at score_confidence
    python main.py --daemon
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from database.session import get_session, init_db
from exports.powerbi_export import export_all_for_powerbi
from exports.report_format import save_report, to_readable_text
from orchestration.checkpointing import list_checkpoints
from orchestration.crew_tasks import run_synthesis_crew
from orchestration.graph import run_pipeline
from utils.config import settings
from utils.logging_setup import get_logger
from utils.metrics import MetricsCollector

logger = get_logger("main")


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="signalora",
        description="SIGNALORA: Institutional Multi-Agent Autonomous Market Intelligence OS",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=settings.human_review_required_below,
        help="Minimum confidence threshold below which insights are gated for human review.",
    )
    parser.add_argument(
        "--export-powerbi",
        action="store_true",
        default=True,
        help="Export Kimball Star Schema datasets and Power BI schema manifest.",
    )
    parser.add_argument(
        "--no-powerbi",
        dest="export_powerbi",
        action="store_false",
        help="Skip Power BI dimensional dataset export.",
    )
    parser.add_argument(
        "--export-csv",
        action="store_true",
        default=True,
        help="Export analysis-friendly CSV datasets.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for deterministic pipeline execution & audit repeatability.",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Explicit unique run identifier (auto-generated if omitted).",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "queue", "interrupt"],
        default=settings.human_review_mode,
        help="Human-in-the-loop review mode: 'auto' (deterministic reviewer), 'queue' (async review queue), or 'interrupt' (LangGraph breakpoint).",
    )
    parser.add_argument(
        "--simulate-failure-at",
        type=str,
        default=None,
        help="Inject simulated failure at a specific node (e.g. 'score_confidence') to test checkpoint resumption.",
    )
    parser.add_argument(
        "--enable-deep-search",
        action="store_true",
        default=settings.enable_deep_search,
        help="Enable anomaly-driven multi-hop web and alternative search.",
    )
    parser.add_argument(
        "--enable-sec-edgar",
        action="store_true",
        default=settings.enable_sec_edgar,
        help="Enable SEC EDGAR 8-K / 10-Q corporate regulatory disclosures retrieval.",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        default=False,
        help="Start the autonomous background live daemon scheduler.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    if args.daemon:
        logger.info("Launching autonomous LiveDaemon background scheduler ...")
        from agents.live_daemon import LiveDaemon
        daemon = LiveDaemon()
        daemon.start()
        return 0

    # Apply CLI runtime configuration overrides
    settings.human_review_required_below = args.min_confidence
    settings.human_review_mode = args.mode
    settings.enable_deep_search = args.enable_deep_search
    settings.enable_sec_edgar = args.enable_sec_edgar

    logger.info("Initializing database ...")
    init_db()

    metrics = MetricsCollector()

    logger.info(
        f"Starting SIGNALORA pipeline run [mode={args.mode}, min_conf={args.min_confidence}, seed={args.seed}] ..."
    )
    final_state = run_pipeline(
        metrics=metrics,
        simulate_failure_at=args.simulate_failure_at,
        run_id=args.run_id,
        seed=args.seed,
    )

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

    if final_state.get("pending_review"):
        logger.info(f"Run paused: human review pending in queue. Queue item ID: {final_state.get('review_queue_id')}")
        with get_session() as session:
            metrics.persist(session, run_id)
        return 0

    if report is None:
        logger.error("Pipeline completed without producing a report.")
        return 1

    # Persist metrics + run Power BI Star Schema exports + save report
    exported_paths = {}
    with get_session() as session:
        metrics.persist(session, run_id)
        if args.export_powerbi or args.export_csv:
            exported_paths = export_all_for_powerbi(session)

    saved_paths = save_report(report)

    # Optional CrewAI narrative synthesis layer (degrades gracefully offline)
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
        print(f"  {key}: {value}")

    print("\n--- Checkpoints saved for this run ---")
    with get_session() as session:
        for cp in list_checkpoints(session, run_id):
            print(f"  [{cp.created_at}] {cp.node_name}")

    if exported_paths:
        print("\n--- Power BI Star Schema & Datasets Written ---")
        for name, path in exported_paths.items():
            print(f"  {name}: {path}")

    print("\n--- Intelligence Dossiers Saved ---")
    for kind, path in saved_paths.items():
        print(f"  report ({kind}): {path}")

    # Hermes Autonomous Self-Learning & Trajectory Evaluation Loop
    try:
        from agents.hermes_self_learning_agent import hermes_self_learning_agent
        self_learn_summary = hermes_self_learning_agent.run()
        print("\n--- Hermes Autonomous Self-Learning Loop ---")
        print(f"  Forecasts audited: {self_learn_summary['forecast_evaluations']['forecasts_audited']}")
        print(f"  Autonomous corrections generated: {self_learn_summary['forecast_evaluations']['autonomous_corrections_generated']}")
        print(f"  Memory consolidation: {self_learn_summary['memory_consolidation']['new_fact'] or 'Nominal (no drift)'}")
    except Exception as exc:
        logger.warning(f"Hermes self-learning notice: {exc}")

    logger.info(f"SIGNALORA Run {run_id} complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
