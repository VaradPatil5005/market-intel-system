"""
Human-in-the-Loop Approval Module.

Pauses the workflow when overall confidence is low or evidence
conflicts, presents a concise summary for review, and only continues
once a decision is made. The decision is always logged to audit_logs.

`review_callback` is injected so this module stays UI-agnostic: in this
demo it's a simple auto-reviewer (approves unless confidence is very
low); swap it for a real prompt, Slack approval, or web UI callback in
production without touching orchestration logic.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

from database.models import AuditLog, ConfidenceScore, Insight
from database.session import Repository, Session
from utils.helpers import iso_now, new_id
from utils.logging_setup import get_logger

logger = get_logger("human_in_loop")
audit_repo = Repository(AuditLog)

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


def request_human_review(
    session: Session,
    insights: List[Insight],
    confidence_scores: List[ConfidenceScore],
    review_callback: Optional[ReviewCallback] = None,
) -> Dict:
    """Run the (possibly automated) human review step and log the decision."""
    summary = build_review_summary(insights, confidence_scores)
    reviewer = review_callback or default_auto_reviewer

    logger.info(f"Human review requested: {summary['flagged_count']} flagged / {summary['total_insights']} total")
    approved = reviewer(summary)

    record = AuditLog(
        id=new_id("audit"),
        agent_name="human_in_loop",
        step="human_review",
        action="review_decision",
        input_summary=str(summary)[:2000],
        output_summary=f"approved={approved}",
        score=summary["overall_average_confidence"],
        decision="approved" if approved else "rejected",
        created_at=iso_now(),
    )
    audit_repo.insert(session, record)
    session.flush()

    return {"approved": approved, "summary": summary}
