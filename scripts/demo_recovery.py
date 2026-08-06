"""
Demonstration: checkpointing + recovery.

Runs the pipeline with a simulated failure injected mid-graph, shows
the run halting with only partial checkpoints saved, then resumes the
SAME run from its last successful checkpoint and completes it.

Usage:
    python scripts/demo_recovery.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.session import get_session, init_db  # noqa: E402
from exports.report_format import to_readable_text  # noqa: E402
from orchestration.checkpointing import list_checkpoints  # noqa: E402
from orchestration.graph import resume_pipeline, run_pipeline  # noqa: E402
from utils.logging_setup import get_logger  # noqa: E402
from utils.metrics import MetricsCollector  # noqa: E402

logger = get_logger("demo_recovery")

FAILURE_NODE = "analyze_trends"


def main() -> int:
    init_db()
    metrics = MetricsCollector()

    print(f"\n>>> Step 1: running pipeline with a simulated failure at '{FAILURE_NODE}' ...\n")
    run_id = None
    try:
        run_pipeline(metrics, simulate_failure_at=FAILURE_NODE)
        print("Unexpected: pipeline did not fail.")
        return 1
    except Exception as exc:
        # The run_id was generated inside run_pipeline; recover it from the
        # most recent checkpoint set instead (in a real system you would
        # capture/propagate it via the exception context or a run registry).
        with get_session() as session:
            from database.models import Checkpoint
            from database.session import Repository

            all_ckpts = Repository(Checkpoint).all(session)
            run_id = sorted(all_ckpts, key=lambda c: c.created_at)[-1].run_id if all_ckpts else None
        print(f"Pipeline failed as expected: {exc}")

    if not run_id:
        print("Could not determine run_id to resume — aborting demo.")
        return 1

    with get_session() as session:
        saved = list_checkpoints(session, run_id)
        print(f"\nCheckpoints saved before failure ({len(saved)}):")
        for cp in saved:
            print(f"  - {cp.node_name}")

    print(f"\n>>> Step 2: resuming run {run_id} from its last successful checkpoint ...\n")
    final_state = resume_pipeline(run_id, metrics)

    report = final_state.get("report")
    if report is None:
        print("Resume did not produce a report — check logs above.")
        return 1

    print("\n>>> Recovery succeeded. Final report:\n")
    print(to_readable_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
