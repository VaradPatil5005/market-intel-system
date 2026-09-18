"""
Human-in-the-Loop Approval Module.

Pauses the workflow when overall confidence is low or evidence
conflicts, presents a concise summary for review, and only continues
once a decision is made. The decision is always logged to audit_logs.

Dual-mode operation (controlled by settings.human_review_mode):

  "auto"  (default):
      Uses `default_auto_reviewer` — a deterministic formula that approves
      unless > 33% of insights are flagged AND avg confidence < 0.5. A
      ReviewQueueItem row is still written to the DB for audit purposes and
      immediately resolved (APPROVED/REJECTED). No blocking occurs, so
      automated tests, batch jobs, and CI pipelines never stall.

  "queue":
      The pipeline halts. A ReviewQueueItem row is written with
      status="PENDING". `approved` is returned as None so the graph node
      can save the checkpoint and yield. An external analyst retrieves the
      item via GET /api/review-queue and resolves it via
      POST /api/review-queue/{id}/decision. Once resolved,
      resume_pipeline(run_id) is called to continue execution.

`review_callback` is injected so this module stays UI-agnostic:
swap it for a real prompt, Slack approval, or web UI callback in
production without touching orchestration logic.
"""
from __future__ import annotations

import json
from typing import Callable, Dict, List, Optional

from database.models import AuditLog, ConfidenceScore, Insight, ReviewQueueItem
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id
from utils.logging_setup import get_logger

logger = get_logger("human_in_loop")
audit_repo = Repository(AuditLog)
review_queue_repo = Repository(ReviewQueueItem)

ReviewCallback = Callable[[Dict], bool]


def build_review_summary(insights: List[Insight], confidence_scores: List[ConfidenceScore]) -> Dict:
    flagged = [c for c in confidence_scores if c.is_flagged]
    by_id = {i.id: i for i in insights}
    return {
        "total_insights": len(insights),
        "flagged_count": len(flagged),
        "flagged_insights": [
            {"insight": by_id[c.insight_id].text, "score": c.score}
            for c in flagged
            if c.insight_id in by_id
        ],
        "overall_average_confidence": (
            round(sum(c.score for c in confidence_scores) / len(confidence_scores), 4)
            if confidence_scores
            else 0.0
        ),
    }


def default_auto_reviewer(summary: Dict) -> bool:
    """Deterministic stand-in reviewer for automated demo runs.

    Approves unless more than a third of insights are flagged AND
    overall average confidence is below 0.5 — a clearly weak batch.
    """
    if summary["total_insights"] == 0:
        return True
    flag_ratio = summary["flagged_count"] / summary["total_insights"]
    return not (flag_ratio > 0.33 and summary["overall_average_confidence"] < 0.5)


def _write_review_queue_item(
    session: Session,
    run_id: str,
    summary: Dict,
    status: str,
    approved: Optional[bool],
    reviewer_notes: Optional[str] = None,
) -> ReviewQueueItem:
    """Persist a ReviewQueueItem row and return it."""
    item = ReviewQueueItem(
        id=new_id("rq"),
        run_id=run_id,
        status=status,
        flagged_count=summary["flagged_count"],
        avg_confidence=summary["overall_average_confidence"],
        summary_json=json.dumps(summary["flagged_insights"])[:4000],
        reviewer_notes=reviewer_notes,
        reviewed_by=("auto_reviewer" if status != "PENDING" else None),
        created_at=iso_now(),
        resolved_at=(iso_now() if status != "PENDING" else None),
    )
    review_queue_repo.insert(session, item)
    session.flush()
    return item


def request_human_review(
    session: Session,
    insights: List[Insight],
    confidence_scores: List[ConfidenceScore],
    review_callback: Optional[ReviewCallback] = None,
    run_id: str = "",
) -> Dict:
    """Run the (possibly automated or queued) human review step.

    Returns a dict with keys:
      - "approved":  bool (auto mode) | None (queue mode — pending analyst)
      - "summary":   the review summary dict
      - "queue_id":  str | None — ReviewQueueItem.id if mode="queue"
    """
    summary = build_review_summary(insights, confidence_scores)
    logger.info(
        f"Human review requested: {summary['flagged_count']} flagged / "
        f"{summary['total_insights']} total  [mode={settings.human_review_mode}]"
    )

    mode = settings.human_review_mode
    queue_id: Optional[str] = None

    if mode == "queue":
        # --- Queue mode: halt pipeline, persist PENDING item, return None ---
        item = _write_review_queue_item(session, run_id, summary, status="PENDING", approved=None)
        queue_id = item.id
        logger.info(f"Review queued as {queue_id} — pipeline pausing for analyst decision.")

        # Log audit entry for traceability
        audit_repo.insert(
            session,
            AuditLog(
                id=new_id("audit"),
                agent_name="human_in_loop",
                step="human_review",
                action="review_queued",
                input_summary=str(summary)[:2000],
                output_summary=f"queue_id={queue_id}, status=PENDING",
                score=summary["overall_average_confidence"],
                decision="pending",
                created_at=iso_now(),
            ),
        )
        session.flush()
        return {"approved": None, "summary": summary, "queue_id": queue_id}

    # --- Auto mode (default): resolve immediately with formula reviewer ---
    reviewer = review_callback or default_auto_reviewer
    approved = reviewer(summary)
    status = "APPROVED" if approved else "REJECTED"

    item = _write_review_queue_item(session, run_id, summary, status=status, approved=approved)
    queue_id = item.id

    record = AuditLog(
        id=new_id("audit"),
        agent_name="human_in_loop",
        step="human_review",
        action="review_decision",
        input_summary=str(summary)[:2000],
        output_summary=f"approved={approved}, queue_id={queue_id}",
        score=summary["overall_average_confidence"],
        decision="approved" if approved else "rejected",
        created_at=iso_now(),
    )
    audit_repo.insert(session, record)
    session.flush()

    return {"approved": approved, "summary": summary, "queue_id": queue_id}
