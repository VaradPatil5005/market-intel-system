"""
Web layer for the Multi-Agent Market Intelligence System.

This does not replace `main.py` — it wraps the exact same pipeline
(`orchestration.graph.run_pipeline`) behind a REST API and serves a
static dashboard, so the whole thing can be deployed as a single free
web service (Render/Railway/Fly) instead of only running from the CLI.

Run locally:
    uvicorn api.main:app --reload

Deploy: see Dockerfile + render.yaml at the project root.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database.models import (
    AgentMetric,
    ConfidenceScore,
    Entity,
    ForecastResult,
    Insight,
    ReportExport,
    ReviewQueueItem,
    SentimentResult,
    TrendResult,
)
from database.session import Repository, get_session, init_db
from orchestration.checkpointing import list_checkpoints
from orchestration.graph import resume_pipeline, run_pipeline
from utils.config import settings
from utils.metrics import MetricsCollector

APP_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = APP_ROOT / "static"

app = FastAPI(title="Market Intel API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

report_repo = Repository(ReportExport)
insight_repo = Repository(Insight)
confidence_repo = Repository(ConfidenceScore)
trend_repo = Repository(TrendResult)
forecast_repo = Repository(ForecastResult)
entity_repo = Repository(Entity)
sentiment_repo = Repository(SentimentResult)
metric_repo = Repository(AgentMetric)
review_queue_repo = Repository(ReviewQueueItem)

# In-memory run tracker (single-process deployment). Swap for Redis/DB
# if you move to multiple workers.
_RUNS: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
def _startup() -> None:
    init_db()


def _rows(session, repo: Repository, limit: int = 200) -> List[Dict[str, Any]]:
    items = repo.all(session)
    items = items[-limit:] if limit else items
    return [i.to_dict() for i in reversed(items)]


# ---------------------------------------------------------------------------
# Read endpoints — power the dashboard
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard")
def dashboard() -> Dict[str, Any]:
    with get_session() as session:
        reports = report_repo.all(session)
        confidences = confidence_repo.all(session)
        entities = entity_repo.all(session)
        trends = trend_repo.all(session)
        insights = insight_repo.all(session)

        latest_report = reports[-1].to_dict() if reports else None
        avg_confidence = (
            round(sum(c.score for c in confidences) / len(confidences), 3)
            if confidences
            else None
        )
        top_entities = sorted(entities, key=lambda e: e.mention_count, reverse=True)[:8]

    return {
        "runs_completed": len(reports),
        "avg_confidence": avg_confidence,
        "entities_tracked": len(entities),
        "trend_signals": len(trends),
        "insights_total": len(insights),
        "latest_report": latest_report,
        "top_entities": [
            {"name": e.canonical_name, "type": e.entity_type, "mentions": e.mention_count}
            for e in top_entities
        ],
    }


@app.get("/api/reports")
def reports(limit: int = 20) -> List[Dict[str, Any]]:
    with get_session() as session:
        return _rows(session, report_repo, limit)


@app.get("/api/reports/latest")
def latest_report() -> Dict[str, Any]:
    with get_session() as session:
        items = report_repo.all(session)
        if not items:
            raise HTTPException(status_code=404, detail="No reports generated yet. Trigger a run first.")
        return items[-1].to_dict()


@app.get("/api/insights")
def insights(category: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    with get_session() as session:
        rows = _rows(session, insight_repo, limit)
        if category:
            rows = [r for r in rows if r.get("category") == category]
        return rows


@app.get("/api/entities")
def entities(limit: int = 100) -> List[Dict[str, Any]]:
    with get_session() as session:
        return _rows(session, entity_repo, limit)


@app.get("/api/sentiment")
def sentiment(limit: int = 100) -> List[Dict[str, Any]]:
    with get_session() as session:
        return _rows(session, sentiment_repo, limit)


@app.get("/api/trends")
def trends(limit: int = 100) -> List[Dict[str, Any]]:
    with get_session() as session:
        return _rows(session, trend_repo, limit)


@app.get("/api/forecasts")
def forecasts(limit: int = 100) -> List[Dict[str, Any]]:
    with get_session() as session:
        return _rows(session, forecast_repo, limit)


@app.get("/api/confidence")
def confidence(limit: int = 100) -> List[Dict[str, Any]]:
    with get_session() as session:
        return _rows(session, confidence_repo, limit)


@app.get("/api/metrics")
def metrics(limit: int = 200) -> List[Dict[str, Any]]:
    with get_session() as session:
        return _rows(session, metric_repo, limit)


@app.get("/api/review-queue")
def get_review_queue(status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    with get_session() as session:
        if status:
            items = review_queue_repo.filter_by(session, status=status)
            return [i.to_dict() for i in reversed(items[-limit:])]
        return _rows(session, review_queue_repo, limit)


@app.post("/api/review-queue/{queue_id}/decision")
def review_decision(
    queue_id: str,
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    approved = payload.get("approved")
    if approved is None:
        raise HTTPException(status_code=400, detail="Field 'approved' (bool) is required.")
    notes = payload.get("notes", "")
    reviewer = payload.get("reviewed_by", "analyst")

    with get_session() as session:
        item = review_queue_repo.get(session, queue_id)
        if not item:
            raise HTTPException(status_code=404, detail="Review queue item not found.")
        if item.status != "PENDING":
            raise HTTPException(status_code=400, detail=f"Item already resolved as {item.status}.")

        from utils.helpers import iso_now
        item.status = "APPROVED" if approved else "REJECTED"
        item.reviewer_notes = notes
        item.reviewed_by = reviewer
        item.resolved_at = iso_now()
        session.flush()
        run_id = item.run_id

    def _resume(run_id_to_resume: str, was_approved: bool):
        try:
            m = MetricsCollector()
            resume_pipeline(run_id_to_resume, m, human_approved=was_approved)
            with get_session() as s:
                m.persist(s, run_id_to_resume)
        except Exception:
            pass

    background_tasks.add_task(_resume, run_id, approved)
    return {
        "status": "success",
        "queue_id": queue_id,
        "decision": "APPROVED" if approved else "REJECTED",
        "run_id": run_id,
    }


# ---------------------------------------------------------------------------
# Write / trigger endpoints
# ---------------------------------------------------------------------------
def _execute_run(run_key: str) -> None:
    _RUNS[run_key]["status"] = "running"
    try:
        metrics_collector = MetricsCollector()
        final_state = run_pipeline(metrics_collector)
        with get_session() as session:
            metrics_collector.persist(session, final_state.get("run_id"))
        _RUNS[run_key]["status"] = "error" if final_state.get("error") else "complete"
        _RUNS[run_key]["run_id"] = final_state.get("run_id")
        _RUNS[run_key]["error"] = final_state.get("error")
    except Exception as exc:  # pragma: no cover - surfaced via status endpoint
        _RUNS[run_key]["status"] = "error"
        _RUNS[run_key]["error"] = str(exc)


@app.post("/api/run")
def trigger_run(background_tasks: BackgroundTasks) -> Dict[str, str]:
    """Kick off a full pipeline run in the background and return a tracking id."""
    run_key = str(uuid.uuid4())
    _RUNS[run_key] = {"status": "queued", "run_id": None, "error": None}
    background_tasks.add_task(_execute_run, run_key)
    return {"run_key": run_key, "status": "queued"}


@app.get("/api/run/{run_key}")
def run_status(run_key: str) -> Dict[str, Any]:
    if run_key not in _RUNS:
        raise HTTPException(status_code=404, detail="Unknown run_key")
    result = dict(_RUNS[run_key])
    if result.get("run_id"):
        with get_session() as session:
            result["checkpoints"] = [
                {"node": cp.node_name, "at": cp.created_at}
                for cp in list_checkpoints(session, result["run_id"])
            ]
    return result


@app.get("/api/config")
def public_config() -> Dict[str, Any]:
    """Non-secret config the frontend needs to render correctly."""
    return {
        "watchlist": [w.strip() for w in settings.company_watchlist.split(",") if w.strip()],
        "low_confidence_threshold": settings.low_confidence_threshold,
        "human_review_required_below": settings.human_review_required_below,
    }


# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------
app.mount("/assets", StaticFiles(directory=str(STATIC_DIR)), name="assets")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))
