"""
Human-in-the-Loop Review Dashboard (Tier 3).

A Streamlit dashboard that reads directly from `storage/market_intel.db`
and lets a human reviewer see flagged insights, anomaly alerts, and the
latest report — then Approve / Reject / Modify insights, writing the
decision straight back to the database.

This REPLACES the deterministic auto-reviewer used in `main.py` for
day-to-day use: run this instead of (or alongside) `main.py` once you
want an actual person making the call on flagged insights rather than
the automatic threshold-based reviewer.

Run with:
    streamlit run ui/app.py

Note: this only reads/writes the SQLite DB — it does not run the
pipeline itself. Run `python main.py` first to generate data, or run it
periodically in the background (see the README's "Future Improvements"
section for wiring this to a scheduled cron job).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running via `streamlit run ui/app.py` from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from database.models import ConfidenceScore, Entity, ForecastResult, Insight, ReportExport, TrendResult
from database.session import Repository, get_session, init_db

st.set_page_config(page_title="Market Intel — Review Dashboard", layout="wide")

init_db()

insight_repo = Repository(Insight)
confidence_repo = Repository(ConfidenceScore)
trend_repo = Repository(TrendResult)
forecast_repo = Repository(ForecastResult)
report_repo = Repository(ReportExport)
entity_repo = Repository(Entity)


# ---------------------------------------------------------------------------
def load_data():
    with get_session() as session:
        insights = insight_repo.all(session)
        scores = confidence_repo.all(session)
        trends = trend_repo.all(session)
        forecasts = forecast_repo.all(session)
        reports = report_repo.all(session)
        entities = entity_repo.all(session)
    return insights, scores, trends, forecasts, reports, entities


def latest_report(reports: list[ReportExport]) -> ReportExport | None:
    if not reports:
        return None
    return max(reports, key=lambda r: r.created_at)


def apply_decision(insight_id: str, decision: str, reviewer_note: str, new_text: str | None = None):
    """Writes a human review decision back to the DB.

    - "approve" / "reject" flips `ConfidenceScore.is_flagged` off and
      records the reviewer's note in `flag_reason` as an audit trail
      (rather than deleting the original reason).
    - "modify" additionally overwrites the insight's text.
    """
    with get_session() as session:
        scores = confidence_repo.filter_by(session, insight_id=insight_id)
        insight = insight_repo.get(session, insight_id)

        if new_text and insight:
            insight.text = new_text

        for score in scores:
            score.is_flagged = 0 if decision in ("approve", "modify") else 1
            prefix = {"approve": "APPROVED", "reject": "REJECTED", "modify": "MODIFIED"}[decision]
            score.flag_reason = f"[{prefix} by human reviewer] {reviewer_note or '(no note)'}"
        session.commit()


# ---------------------------------------------------------------------------
st.title("📊 Market Intelligence — Review Dashboard")
st.caption("Human-in-the-loop review for flagged insights, anomaly alerts, and forecasts.")

if st.button("🔄 Refresh data"):
    st.rerun()

insights, scores, trends, forecasts, reports, entities = load_data()
score_by_insight = {s.insight_id: s for s in scores}
report = latest_report(reports)

tab_overview, tab_review, tab_anomalies, tab_forecasts = st.tabs(
    ["📋 Latest Report", "🚩 Flagged for Review", "📈 Anomalies", "🔮 Forecasts"]
)

# --- Tab 1: latest report ---------------------------------------------------
with tab_overview:
    if not report:
        st.info("No report found yet. Run `python main.py` first to generate one.")
    else:
        data = json.loads(report.full_report_json)
        col1, col2, col3 = st.columns(3)
        col1.metric("Run ID", report.run_id)
        col2.metric("Approved", "Yes" if report.approved else "Pending")
        col3.metric(
            "Overall confidence",
            f"{data.get('confidence_notes', {}).get('overall_confidence', 0):.2f}",
        )
        st.subheader("Executive Summary")
        st.write(data.get("executive_summary", ""))

        for title, key in [
            ("Key Trends", "key_trends"),
            ("Competitor Movements", "competitor_movements"),
            ("Sentiment Shifts", "sentiment_shifts"),
            ("Risk Signals", "risk_signals"),
            ("Predictive Outlook", "predictive_outlook"),
        ]:
            items = data.get(key) or []
            with st.expander(f"{title} ({len(items)})", expanded=(key == "risk_signals" and bool(items))):
                if not items:
                    st.write("_(none this cycle)_")
                for item in items:
                    st.markdown(f"- {item.get('text', item)}")

# --- Tab 2: flagged insights (the actual human-in-the-loop review UI) ------
with tab_review:
    flagged = [i for i in insights if score_by_insight.get(i.id) and score_by_insight[i.id].is_flagged]
    st.subheader(f"Insights flagged for review ({len(flagged)})")

    if not flagged:
        st.success("Nothing currently flagged — all insights meet the confidence threshold.")

    for insight in flagged:
        score = score_by_insight[insight.id]
        with st.container(border=True):
            st.markdown(f"**[{insight.category.upper()}]** {insight.text}")
            st.caption(
                f"Confidence: {score.score:.2f}  |  Reason: {score.flag_reason or 'n/a'}  |  "
                f"Insight ID: `{insight.id}`"
            )
            new_text = st.text_area(
                "Edit text (used only if you click Modify & Approve)",
                value=insight.text,
                key=f"text_{insight.id}",
            )
            note = st.text_input("Reviewer note (optional)", key=f"note_{insight.id}")
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ Approve", key=f"approve_{insight.id}"):
                apply_decision(insight.id, "approve", note)
                st.rerun()
            if c2.button("❌ Reject", key=f"reject_{insight.id}"):
                apply_decision(insight.id, "reject", note)
                st.rerun()
            if c3.button("✏️ Modify & Approve", key=f"modify_{insight.id}"):
                apply_decision(insight.id, "modify", note, new_text=new_text)
                st.rerun()

# --- Tab 3: anomalies (Tier 1 trend anomaly detection) ---------------------
with tab_anomalies:
    anomalous = [t for t in trends if t.is_anomalous]
    st.subheader(f"Anomalous topics this run ({len(anomalous)})")
    if not anomalous:
        st.info("No statistically anomalous topics detected (z-score below threshold).")
    else:
        df = pd.DataFrame(
            [
                {
                    "Topic": t.topic,
                    "Current score": t.current_score,
                    "EWMA mean": t.ewma_mean,
                    "EWMA std": t.ewma_std,
                    "Z-score": t.z_score,
                    "Change %": t.change_pct,
                }
                for t in anomalous
            ]
        )
        st.dataframe(df, use_container_width=True)

    st.subheader("All tracked topics")
    if trends:
        df_all = pd.DataFrame(
            [
                {
                    "Topic": t.topic,
                    "Label": t.trend_label,
                    "Current score": t.current_score,
                    "Z-score": t.z_score,
                    "Anomalous": bool(t.is_anomalous),
                }
                for t in trends
            ]
        )
        st.dataframe(df_all, use_container_width=True)

# --- Tab 4: forecasts (Tier 2 predictive layer) -----------------------------
with tab_forecasts:
    st.subheader("Entity sentiment forecasts")
    if not forecasts:
        st.info("No forecasts yet — run the pipeline a few times to build up history.")
    else:
        df = pd.DataFrame(
            [
                {
                    "Entity": f.entity_name,
                    "Predicted direction": f.predicted_direction,
                    "Magnitude": f.predicted_magnitude,
                    "Confidence": f.confidence,
                    "Model": f.model_used,
                    "Observations used": f.observations_used,
                }
                for f in forecasts
            ]
        )
        st.dataframe(df, use_container_width=True)
        trained = df[df["Model"] == "gradient_boosting"]
        if not trained.empty:
            st.bar_chart(trained.set_index("Entity")["Magnitude"])
