"""
Final Report Formatting Helpers.

Formats the market intelligence report (stored as JSON in
`report_exports.full_report_json`) into a readable plain-text version
and exposes the structured dict as-is, both easy to save/export.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from database.models import ReportExport
from utils.config import settings


def to_structured(report: ReportExport) -> Dict[str, Any]:
    return json.loads(report.full_report_json)


def to_readable_text(report: ReportExport) -> str:
    data = to_structured(report)
    lines = [
        "=" * 78,
        f"{data['title'].upper()}",
        f"Generated: {data['generated_at']}",
        f"Approved: {'YES' if report.approved else 'PENDING/NO'}",
        "=" * 78,
        "",
        "EXECUTIVE SUMMARY",
        "-" * 78,
        data["executive_summary"],
        "",
    ]

    def _section(title: str, key: str) -> None:
        items = data.get(key) or []
        lines.append(title)
        lines.append("-" * 78)
        if not items:
            lines.append("  (none this cycle)")
        for item in items:
            flag = " [FLAGGED]" if item.get("flagged") else ""
            conf = f" (confidence {item['confidence']:.2f})" if item.get("confidence") is not None else ""
            lines.append(f"  - {item['text']}{conf}{flag}")
        lines.append("")

    _section("KEY TRENDS", "key_trends")
    _section("COMPETITOR MOVEMENTS", "competitor_movements")
    _section("SENTIMENT SHIFTS", "sentiment_shifts")
    _section("RISK SIGNALS", "risk_signals")
    _section("HISTORICAL CONTEXT (RAG)", "historical_context")

    lines.append("RECOMMENDED ACTIONS")
    lines.append("-" * 78)
    for action in data.get("recommended_actions", []):
        lines.append(f"  - {action}")
    lines.append("")

    notes = data.get("confidence_notes", {})
    lines.append("CONFIDENCE NOTES")
    lines.append("-" * 78)
    lines.append(f"  Overall confidence: {notes.get('overall_confidence')}")
    lines.append(f"  Insights flagged for review: {notes.get('insights_flagged_for_review')}")
    lines.append("")
    lines.append("=" * 78)

    return "\n".join(lines)


def save_report(report: ReportExport) -> Dict[str, Path]:
    out_dir = Path(settings.export_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"report_{report.run_id}.json"
    text_path = out_dir / f"report_{report.run_id}.txt"

    json_path.write_text(json.dumps(to_structured(report), indent=2, default=str), encoding="utf-8")
    text_path.write_text(to_readable_text(report), encoding="utf-8")

    return {"json": json_path, "text": text_path}
