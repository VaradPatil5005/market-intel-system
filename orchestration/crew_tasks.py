"""
CrewAI Task Definitions.

CrewAI is used here for the *synthesis* stage — where specialized
"analyst" agents collaborate/delegate to turn raw sentiment/trend/RAG
signals into a narrative research memo, complementing the deterministic
Report Generation Agent used for the structured report.

CrewAI agents require an LLM configured (e.g. OPENAI_API_KEY). This
module works either way:
  - If an LLM key is available, a real Crew (Research Analyst ->
    Risk Analyst -> Editor) runs and returns a narrative memo.
  - If not, `run_synthesis_crew` degrades to a deterministic, template-
    based synthesis so the pipeline still runs fully offline/mock.

This keeps CrewAI a genuine, swappable collaboration layer rather than
a hard dependency for the whole system to function.
"""
from __future__ import annotations

from typing import Any, Dict, List

from utils.config import settings
from utils.logging_setup import get_logger

logger = get_logger("crew_tasks")

try:
    from crewai import Agent, Crew, Process, Task

    _CREWAI_AVAILABLE = True
except ImportError:
    _CREWAI_AVAILABLE = False


def _deterministic_synthesis(insights: List[Dict[str, Any]]) -> str:
    if not insights:
        return "No insights available for narrative synthesis this cycle."
    by_category: Dict[str, List[str]] = {}
    for insight in insights:
        by_category.setdefault(insight["category"], []).append(insight["text"])

    lines = ["Narrative synthesis (deterministic fallback — no LLM configured):"]
    for category, texts in by_category.items():
        lines.append(f"\n{category.upper()}:")
        for text in texts:
            lines.append(f"  - {text}")
    return "\n".join(lines)


def _build_crew(insights: List[Dict[str, Any]]) -> "Crew":
    research_analyst = Agent(
        role="Research Analyst",
        goal="Summarize sentiment and trend signals into clear observations.",
        backstory="A market intelligence analyst skilled at synthesizing noisy signals.",
        allow_delegation=True,
        verbose=False,
    )
    risk_analyst = Agent(
        role="Risk Analyst",
        goal="Identify and elevate the most material risk signals for leadership.",
        backstory="Specializes in surfacing risk from ambiguous or conflicting evidence.",
        allow_delegation=False,
        verbose=False,
    )
    editor = Agent(
        role="Editor",
        goal="Combine analyst outputs into one concise executive-ready memo.",
        backstory="Ensures the final memo is clear, concise, and decision-oriented.",
        allow_delegation=False,
        verbose=False,
    )

    insight_text = "\n".join(f"- [{i['category']}] {i['text']}" for i in insights)

    summarize_task = Task(
        description=f"Summarize these market signals:\n{insight_text}",
        expected_output="A short bullet summary of key observations.",
        agent=research_analyst,
    )
    risk_task = Task(
        description="From the same signals, call out the top risks leadership should know about.",
        expected_output="A short list of prioritized risks.",
        agent=risk_analyst,
    )
    edit_task = Task(
        description="Combine the summary and risk list into one concise memo (<200 words).",
        expected_output="Final narrative memo.",
        agent=editor,
    )

    return Crew(
        agents=[research_analyst, risk_analyst, editor],
        tasks=[summarize_task, risk_task, edit_task],
        process=Process.sequential,
        verbose=False,
    )


def run_synthesis_crew(insights: List[Dict[str, Any]]) -> str:
    """Produce a narrative synthesis memo from structured insights."""
    if not _CREWAI_AVAILABLE or not settings.openai_api_key:
        if not _CREWAI_AVAILABLE:
            logger.info("crewai not installed — using deterministic synthesis fallback.")
        else:
            logger.info("No LLM API key configured — using deterministic synthesis fallback.")
        return _deterministic_synthesis(insights)

    try:
        crew = _build_crew(insights)
        result = crew.kickoff()
        return str(result)
    except Exception as exc:  # network/LLM errors -> graceful fallback, never crash the pipeline
        logger.warning(f"CrewAI synthesis failed, falling back to deterministic summary: {exc}")
        return _deterministic_synthesis(insights)
