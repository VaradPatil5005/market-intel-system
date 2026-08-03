# Multi-Agent Market Intelligence System

A production-style market intelligence platform that ingests real-time
news/market data, validates source credibility, resolves entities across
sources, analyzes sentiment and trends, retrieves historical context with
RAG, scores confidence, logs every decision, checkpoints/recovers from
failure, supports human-in-the-loop approval, and publishes a structured
report plus Power BI-ready datasets.

Built with **Python, LangGraph, CrewAI, SQLAlchemy/SQL, and Power BI-ready
CSV exports**. Runs fully offline out of the box using bundled mock data —
no API keys required to see the whole pipeline work end to end.

---

## Key features

- **Ingestion** from RSS feeds/news APIs, with automatic fallback to
  bundled mock/seed data when no live source is configured or reachable.
- **Source credibility scoring** — domain trust, recency, completeness,
  and duplicate detection, with automatic rejection of low-quality sources.
- **Entity resolution** — extracts and merges companies/products/topics
  across sources into canonical entities using normalized + fuzzy matching.
- **Sentiment analysis** — lexicon-based polarity scoring per entity/source.
- **Trend analysis** — keyword-spike detection compared against stored
  historical averages (rising / falling / stable / anomalous).
- **RAG insight agent** — TF-IDF retrieval over historical report notes to
  surface "this looks like a pattern we've seen before" insights.
- **Confidence scoring** — combines source quality, cross-source agreement,
  recency, and completeness into a 0–1 score per insight; flags weak ones.
- **Supervisor (LangGraph)** — routes conditionally on missing data, low
  confidence, or conflicting evidence; supports human-in-the-loop approval.
- **CrewAI synthesis layer** — an optional "analyst crew" (Research Analyst
  → Risk Analyst → Editor) turns insights into a narrative memo when an LLM
  key is configured; otherwise falls back to a deterministic summary so the
  pipeline never depends on external APIs to run.
- **Audit logging** — every agent decision, score, and action is logged to
  both a JSON-lines file and the `audit_logs` SQL table.
- **Checkpointing & recovery** — graph state is snapshotted after every
  major step (SQL + disk); a failed run can resume from the last checkpoint.
- **Observability** — per-agent runtime, failure rate, source usage,
  confidence distribution, insights produced, and human approval counts.
- **Power BI export** — every table exported to clean, stable-named CSVs.

---

## Architecture

```
                         ┌────────────────────┐
                         │   Supervisor /      │
                         │  LangGraph workflow  │
                         └─────────┬────────────┘
                                   │
   ┌───────────┐   ┌────────────────┐   ┌─────────────────┐   ┌────────────┐
   │ Ingestion │──▶│  Credibility    │──▶│ Entity Resolution │──▶│ Sentiment  │
   └───────────┘   └────────────────┘   └─────────────────┘   └─────┬──────┘
                                                                      │
   ┌────────────┐   ┌───────────────┐   ┌───────────────────┐        │
   │  Report Gen │◀──│  Confidence   │◀──│  RAG Insight       │◀───────┘
   └──────┬─────┘    │  Scoring +    │   │  (TF-IDF retrieval) │
          │           │  synthesis    │   └───────────────────┘
          ▼           └───────┬───────┘             ▲
   Power BI / CSV             │                      │
   exports + audit    ┌───────▼────────┐    ┌────────┴────────┐
   logs + checkpoints │ Human-in-the-  │    │  Trend Analysis  │
                       │ loop approval  │    └─────────────────┘
                       └────────────────┘
```

Every node runs inside its own DB session, writes an audit-log row, records
timing/metrics, and saves a checkpoint before control passes to the next
node — so the workflow is fully traceable and resumable.

---

## Folder structure

```
market-intel-system/
├── main.py                      # entry point — runs the full pipeline
├── requirements.txt
├── .env.example
├── agents/                      # one independent, testable module per agent
│   ├── base.py                  # shared logging/audit/metrics plumbing
│   ├── ingestion_agent.py
│   ├── credibility_agent.py
│   ├── entity_resolution_agent.py
│   ├── sentiment_agent.py
│   ├── trend_agent.py
│   ├── rag_agent.py
│   ├── confidence_agent.py
│   └── report_agent.py
├── orchestration/
│   ├── state.py                 # shared LangGraph state schema
│   ├── graph.py                 # LangGraph workflow wiring
│   ├── supervisor.py            # conditional routing logic
│   ├── human_in_loop.py         # approval gate
│   ├── checkpointing.py         # save/load/resume checkpoints
│   └── crew_tasks.py            # CrewAI synthesis crew (+ offline fallback)
├── database/
│   ├── schema.sql                # SQLite-friendly, Postgres-portable schema
│   ├── models.py                  # SQLAlchemy ORM models
│   └── session.py                 # session + generic repository layer
├── utils/
│   ├── config.py                  # typed settings (pydantic-settings)
│   ├── logging_setup.py           # console + JSON-lines structured logging
│   ├── metrics.py                 # observability metrics collector
│   └── helpers.py                 # text/date/retry/JSON utilities
├── exports/
│   ├── csv_export.py
│   ├── powerbi_export.py
│   └── report_format.py
├── data/
│   ├── seed/news_batch_1.json      # bundled mock ingestion data
│   └── historical_reports/*.md      # sample docs the RAG agent retrieves from
├── storage/
│   ├── market_intel.db              # SQLite database (created on first run)
│   ├── checkpoints/<run_id>/*.json   # on-disk checkpoint mirror
│   └── logs/agent_events.jsonl       # structured audit/event log
└── tests/
    └── test_pipeline.py              # smoke test for the full pipeline
```

---

## Setup

```bash
cd market-intel-system
python3 -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env      # edit if you want live feeds / an LLM key
```

`crewai` and `chromadb` have overlapping dependency ranges; if your resolver
complains, install everything except `crewai==0.51.1` first, then install
`crewai` separately. The code works with either installed or missing — see
"Optional dependencies" below.

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | local SQLite file |
| `CHECKPOINT_DIR`, `CHROMA_DIR`, `EXPORT_DIR`, `LOG_DIR` | output paths | `storage/...`, `exports/output` |
| `MAX_RETRIES`, `RETRY_BACKOFF_SECONDS` | ingestion retry policy | `3`, `2` |
| `NEWS_RSS_FEEDS` | comma-separated RSS URLs | empty → uses mock seed data |
| `COMPANY_WATCHLIST` | comma-separated company names to track | `OpenAI,Anthropic,Nvidia,Microsoft,Google` |
| `LOW_CONFIDENCE_THRESHOLD` | below this, an insight is flagged | `0.55` |
| `HUMAN_REVIEW_REQUIRED_BELOW` | below this avg confidence, pause for review | `0.65` |
| `NEWSAPI_KEY`, `OPENAI_API_KEY` | optional; system runs fully mocked without them | empty |

## How to run the pipeline

```bash
python main.py
```

This will:
1. Initialize the SQLite database (`storage/market_intel.db`) if needed.
2. Run the full LangGraph workflow once (ingest → … → report).
3. Print the formatted report, the CrewAI/deterministic narrative synthesis,
   the run's observability summary, and the checkpoints saved.
4. Write Power BI-ready CSVs to `exports/output/` and save the report as
   both JSON and readable text.

Run it again to see entity merging accumulate and trend comparisons use
real historical averages (the first run has no history to compare against,
so trends start out labeled "stable").

### Sample workflow

```
$ python main.py
...
MARKET INTELLIGENCE REPORT
EXECUTIVE SUMMARY
This cycle tracked 12 entities, most active: Nvidia, Microsoft, OpenAI,
Google, Anthropic. 0 notable trend(s) and 0 risk signal(s) were detected.
5 entities showed a meaningful sentiment shift. Overall insight confidence
for this run: 0.73.
...
--- Files written ---
  csv: exports/output/raw_sources.csv
  csv: exports/output/entities.csv
  ...
  report (text): exports/output/report_run_xxxxxxxx.txt
```

### Forcing the human-in-the-loop path

```bash
HUMAN_REVIEW_REQUIRED_BELOW=0.99 python main.py
```

Any run's average confidence will fall below `0.99`, so the supervisor
routes to `human_review` before publishing — demonstrating the pause,
summary, and approval/rejection logging.

### Resuming from a checkpoint

```python
from database.session import get_session
from orchestration.checkpointing import load_latest_checkpoint

with get_session() as session:
    state = load_latest_checkpoint(session, run_id="run_xxxxxxxx")
```

`state` is the exact JSON snapshot saved after the last successful node —
use it to re-seed a `PipelineState` and re-invoke the graph from there
after fixing whatever caused a node to fail.

---

## Database tables

`raw_sources`, `entities`, `sentiment_results`, `trend_results`, `insights`,
`confidence_scores`, `audit_logs`, `checkpoints`, `report_exports`,
`agent_metrics` — see `database/schema.sql` for full column definitions,
indexes, and foreign keys. SQLite by default; swap `DATABASE_URL` to a
PostgreSQL DSN for production (schema uses portable types throughout).

## How the Power BI export works

`exports/powerbi_export.export_all_for_powerbi(session)` reads every table
above via the generic `Repository`, converts rows to dicts, and writes one
CSV per table to `EXPORT_DIR` with stable filenames (`entities.csv`,
`insights.csv`, …). Point Power BI's "Folder" or "Text/CSV" connector at
that folder and refresh — filenames never change, so scheduled refreshes
just work. `agent_metrics.csv` powers the observability dashboard (runtime,
failure rate, confidence distribution, human approvals/rejections).

## Optional dependencies / graceful degradation

The system is designed so that missing optional pieces never crash the
pipeline — they just degrade to a deterministic fallback:

- **No RSS feeds configured / unreachable** → ingestion uses `data/seed/*.json`.
- **`crewai` not installed, or no `OPENAI_API_KEY`** → the synthesis step
  uses a deterministic, template-based summary instead of a live Crew.
- **`chromadb` not installed** → RAG retrieval uses TF-IDF + cosine
  similarity (scikit-learn) instead of a persistent vector store.

## Future improvements

- Swap the lexicon-based sentiment scorer for a transformer model.
- Add a browser-automation ingestion connector for JS-heavy sites.
- Add anomaly detection (e.g. z-score/EWMA) on top of the trend agent.
- Add a Streamlit/web UI for human-in-the-loop review instead of the
  deterministic auto-reviewer used in this demo.
- Add alerting (email/Slack) for high-confidence, high-impact insights.
- Swap the entity resolver's fuzzy matcher for embedding-based similarity.
