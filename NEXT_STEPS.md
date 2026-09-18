# What changed, and what to do next

## What was added

Your project was a solid, working CLI pipeline (`python main.py`) with no
web layer — that's the main gap between what you had and "a free-deployable
website." Everything below is additive; nothing in your original agents,
orchestration, or database layer was rewritten, and the existing smoke test
(`pytest tests/test_pipeline.py`) still passes unchanged.

1. **`api/main.py`** — a FastAPI app that wraps `orchestration.graph.run_pipeline`
   behind a REST API (`/api/run`, `/api/dashboard`, `/api/reports`,
   `/api/entities`, `/api/trends`, `/api/sentiment`, `/api/confidence`,
   `/api/metrics`) and serves the dashboard. This is what makes the project
   a *website* instead of a script — one process, one free web-service slot.
2. **`static/`** — the dashboard itself (`index.html` / `styles.css` /
   `app.js`), plain HTML/CSS/JS with no build step. It reads live data from
   the API, and has a "Run new analysis" button that triggers a real
   pipeline run and shows each pipeline stage completing in order.
3. **`agents/competitor_agent.py`** — one real new advanced module:
   `CompetitorMonitorAgent` scans this run's ingested sources for concrete
   signal language (pricing, funding, leadership, hiring, partnership,
   product launch) per watchlist company and writes each hit as a
   `category="competitor"` insight, so it's automatically scored for
   confidence and shows up in the report and dashboard. It's wired into
   `orchestration/graph.py` behind `ENABLE_COMPETITOR_MONITOR` (off by
   default) — see the docstring in that file for why it's a flag rather
   than always-on.
4. **`Dockerfile` + `render.yaml`** — deploys the whole thing (API +
   dashboard + pipeline) as a single free web service. Heavy optional ML
   deps (torch/transformers/chromadb/crewai/playwright) are left out of the
   container on purpose — every agent that uses them already degrades to a
   classical fallback per your own docstrings, and free tiers don't have
   room for a multi-GB torch install.

## How to run it

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
# open http://127.0.0.1:8000
```

Click "Run new analysis" — in mock mode (no API keys configured) this uses
your bundled seed data, so it's safe to run immediately and will populate
the dashboard.

## Deploying free

1. Push this repo to GitHub.
2. Render: New → Blueprint → point at the repo (uses `render.yaml`).
   Or Railway: New Project → Deploy from GitHub (it will detect the
   `Dockerfile` automatically).
3. Both have a free tier that's enough for a portfolio/demo deployment —
   the app sleeps after inactivity and cold-starts on the next request,
   which is normal and worth mentioning as "cost-optimized" if anyone asks.

## Design note on the dashboard look

I didn't copy the generic dark-navy-plus-purple-gradient SaaS template
look (that's what most AI-page-builders default to, including most
Antigravity/Blackbox-style demos) — it reads as templated rather than
purpose-built. Instead the dashboard uses a "research desk" aesthetic:
ink background, brass/amber accent, a serif+mono type pairing (Newsreader
+ IBM Plex Mono), and ledger-style tables — closer to a financial research
terminal than a generic AI startup landing page, which fits a market
intelligence tool specifically.

## Roadmap for the rest of the blueprint's advanced modules

The blueprint you got from Perplexity listed 8 "advanced modules." Building
all 8 well in one pass isn't realistic — each is genuinely a multi-day
feature, not a stub worth adding just to check a box. Competitor monitoring
(#1) is done for real above. Here's the honest state of the rest, ordered by
how much of the foundation already exists in your codebase:

| Module | Status | Why |
|---|---|---|
| Trend scoring / momentum | **Already exists** | `agents/trend_agent.py` already does EWMA + z-score anomaly detection — the blueprint didn't know that because it never saw your real code. |
| Alerting | **Partially exists** | `utils/alerting.py` + `ALERT_WEBHOOK_URL` already sends webhook alerts on low-confidence runs. Extending it to per-rule custom alerts ("notify me if X") needs a rules table + a small UI form — next logical piece to build. |
| Natural-language query interface | Not started | Needs an endpoint that takes free text, uses the existing RAG retriever to answer it, and a chat-style panel in the dashboard. Medium effort — the retrieval half already exists in `agents/rag_agent.py`. |
| Automated battlecards | Not started | Straightforward once competitor monitoring has run for a few cycles — it's a report template over data you'll already have. |
| Intent signal detection | Overlaps with competitor monitoring | The "hiring" and "funding" signal types in the new agent are a starting point; a dedicated scoring/ranking layer on top is the remaining work. |
| TAM/SAM/SOM market sizing | Not started | Needs a real external data source (this can't be meaningfully faked with mock data) — worth scoping once you decide which market data API you're comfortable paying for or using free-tier. |
| API for external integrations | **Partially done** | `api/main.py` *is* that API layer now — add an API-key auth dependency before exposing it publicly. |

If you want, tell me which one to build next and I'll build it the same way
I built this one: real code wired into your existing pipeline, tested end
to end, not a mockup.
