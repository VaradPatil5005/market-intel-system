<p align="center">
  <img src="assets/banner.png" alt="SIGNALORA Multi-Agent Market Intelligence System" width="100%">
</p>

# SIGNALORA ☤
### Institutional Multi-Agent Autonomous Market Intelligence & Trading Strategy OS
<p align="center">
  <a href="#system-architecture">Architecture</a> •
  <a href="#32-autonomous-agent-matrix">Agent Matrix</a> •
  <a href="#quickstart">Quickstart</a> •
  <a href="#power-bi-kimball-star-schema-export">Power BI Star Schema</a> •
  <a href="#dual-interface-ecosystem">Terminal & API</a> •
  <a href="#closed-loop-self-learning">Self-Learning Loop</a> •
  <a href="#voice-ai--biometrics">KIM Voice AI</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Orchestration-LangGraph%20%7C%20CrewAI-FF6B6B?style=for-the-badge" alt="LangGraph & CrewAI">
  <img src="https://img.shields.io/badge/Tests-114%2F114%20Passing-brightgreen?style=for-the-badge" alt="114/114 Tests Passing">
  <img src="https://img.shields.io/badge/UI-Streamlit%20Institutional%20Blackbox-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit UI">
  <img src="https://img.shields.io/badge/API-FastAPI%20Async-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License: MIT">
  <a href="https://github.com/VaradPatil5005/market-intel-system"><img src="https://img.shields.io/badge/Built%20by-Varad%20Patil-blueviolet?style=for-the-badge" alt="Built by Varad Patil"></a>
</p>

**SIGNALORA** is an institutional-grade, multi-agent market intelligence platform that continuously ingests global news feeds, alternative data, order-flow telemetry, SEC regulatory filings, and market prices to synthesize validated, actionable macro signals. 

Unlike naive LLM wrappers, SIGNALORA features a **stateful LangGraph Directed Acyclic Graph (DAG)** with **32 specialized autonomous agents**, a **closed-loop self-learning engine (inspired by Nous Research Hermes)** that creates procedural trading skills from experience, a **forensic SEC 10-Q discrepancy auditor**, **Wav2Vec 2.0 voice biometrics**, a **Kimball Star Schema Power BI export engine**, and **KIM (Knowledge & Intelligence Model)** — an executive voice AI delivering instant 16-bit acoustic intelligence briefings.

---

<table>
<tr>
  <td width="30%"><b>Autonomous Multi-Agent Matrix</b></td>
  <td><b>32 specialized domain agents</b> executing concurrently across ingestion, domain credibility filtering, entity resolution, geopolitical chokepoints, forensic accounting, RAG, and execution routing.</td>
</tr>
<tr>
  <td><b>Stateful LangGraph DAG</b></td>
  <td>Deterministic, fault-tolerant execution graph with full checkpointing, rollback, conditional routing, and <b>0-error strict typing</b> across all pipeline states.</td>
</tr>
<tr>
  <td><b>Kimball Star Schema BI Export</b></td>
  <td>Engineered for institutional enterprise BI: generates <code>fact_market_intelligence.csv</code>, 4 dimension tables, and <code>star_schema_manifest.json</code> with pre-configured DAX measures and relationships.</td>
</tr>
<tr>
  <td><b>Recursive Chunking RAG</b></td>
  <td>Boundary-aware recursive character chunking (512 chunk size, 64 overlap) indexing ChromaDB vector embeddings and TF-IDF against historical market crisis dossiers.</td>
</tr>
<tr>
  <td><b>KIM Voice AI & Biometrics</b></td>
  <td>Executive voice strategist built on native 16-bit Windows SAPI female synthesizer + Wav2Vec 2.0 KAN voiceprint biometric authentication with acoustic anti-spoofing.</td>
</tr>
<tr>
  <td><b>Closed-Loop Self-Learning</b></td>
  <td>Autonomous reflection and dynamic procedural skill synthesis. Automatically creates, refines, and executes modular skills (carry trade unwinds, chokepoint hedging, microstructure TCA).</td>
</tr>
<tr>
  <td><b>Forensic SEC Discrepancy Auditor</b></td>
  <td>Scans 10-K/10-Q regulatory filings to detect divergences between non-GAAP narrative reporting and GAAP balance-sheet cash flows, revenue recognition anomalies, and insider churn.</td>
</tr>
<tr>
  <td><b>Vibe Quant Confluence</b></td>
  <td>Synthesizes social media sentiment delta with microstructure liquidity book skews, options open-interest shifts, and dark pool prints to identify high-probability squeeze vectors.</td>
</tr>
<tr>
  <td><b>Institutional Dual Interface</b></td>
  <td><b>Streamlit Bloomberg-style Blackbox Terminal</b> (real-time telemetry, ticker tape, interactive global supply chain map) + <b>FastAPI High-Concurrency Async API</b>.</td>
</tr>
<tr>
  <td><b>Audited Human-in-the-Loop</b></td>
  <td>LangGraph breakpoint interrupts + non-blocking review queue gating low-confidence or high-risk signals with real-time operator approval, persistent audit trails, and automatic supervisor feedback loops.</td>
</tr>
</table>

---

## System Architecture

```
                                  ┌──────────────────────────────────────────────┐
                                  │           SIGNALORA SUPERVISOR               │
                                  │      (LangGraph Stateful DAG Engine)         │
                                  └──────────────────────┬───────────────────────┘
                                                         │
         ┌───────────────────────────────────────────────┴───────────────────────────────────────────────┐
         ▼                                               ▼                                               ▼
┌──────────────────┐                           ┌──────────────────┐                            ┌───────────────────┐
│  LIVE INGESTION  │                           │   DEEP RESEARCH  │                            │ FORENSIC AUDITING │
│  • RSS News Wire │                           │  • SerpAPI & DDG │                            │  • SEC 10-Q / 10-K│
│  • CoinGecko     │                           │  • Vector RAG    │                            │  • GAAP Divergence│
│  • Yahoo Finance │                           │  • ChromaDB TFIDF│                            │  • Chokepoint Risk│
└────────┬─────────┘                           └────────┬─────────┘                            └─────────┬─────────┘
         │                                              │                                                │
         ▼                                              ▼                                                ▼
┌──────────────────┐                           ┌──────────────────┐                            ┌───────────────────┐
│ CREDIBILITY GATE │                           │ CONFIDENCE ENGINE│                            │ VIBE QUANT ENGINE │
│  • Domain Trust  │                           │  • Bayesian Gate │                            │  • Social Velocity│
│  • Spoof Filter  │                           │  • Source Confl. │                            │  • Order Book Skew│
└────────┬─────────┘                           └────────┬─────────┘                            └─────────┬─────────┘
         │                                              │                                                │
         └──────────────────────────────────────────────┼────────────────────────────────────────────────┘
                                                        │
                                                        ▼
                                       ┌───────────────────────────────────┐
                                       │      SUPERVISOR DECISION GATE     │
                                       └────────────────┬──────────────────┘
                                                        │
                                  ┌─────────────────────┴─────────────────────┐
                                  ▼                                           ▼
                   ┌───────────────────────────────┐           ┌───────────────────────────────┐
                   │   CONFIDENCE ≥ THRESHOLD      │           │   LOW CONFIDENCE / ANOMALOUS  │
                   │   (Automated Fast-Path)       │           │   (Human-in-the-Loop Gate)    │
                   └──────────────┬────────────────┘           └──────────────┬────────────────┘
                                  │                                           │
                                  │                                           ▼
                                  │                            ┌───────────────────────────────┐
                                  │                            │      HUMAN REVIEW QUEUE       │
                                  │                            │   Pending Operator Decision   │
                                  │                            └──────────────┬────────────────┘
                                  │                                           │ (Approved)
                                  ├───────────────────────────────────────────┘
                                  ▼
                   ┌───────────────────────────────┐
                   │    GROUNDING VERIFICATION     │ ◄── [Reflexion Agent & Anti-Hallucination]
                   └──────────────┬────────────────┘
                                  │
                                  ▼
                   ┌───────────────────────────────┐
                   │      INSTITUTIONAL MEMO       │
                   │  • CrewAI Synthesis Layer     │
                   │  • KIM Executive Voice Synth  │
                   │  • Power BI Star Schema Hub   │
                   │  • Autonomous Skill Engine    │
                   └───────────────────────────────┘
```

---

## 32 Autonomous Agent Matrix

SIGNALORA distributes analysis across a specialized matrix of 32 autonomous agents registered in [`agents/__init__.py`](agents/__init__.py):

| Category | Agent | Primary Intelligence Function |
| :--- | :--- | :--- |
| **Ingestion & Data** | [`IngestionAgent`](agents/ingestion_agent.py) | High-throughput RSS, JSON, and financial stream parsing with fallback. |
| | [`LiveNewsAgent`](agents/live_news_agent.py) | Dynamic multi-source market news collection across crypto, equities, and FX. |
| | [`PriceDataAgent`](agents/price_data_agent.py) | Real-time quote enrichment, SMA-20/50, RSI-14, volatility, and VWAP. |
| **Trust & Verification** | [`CredibilityAgent`](agents/credibility_agent.py) | Domain authority grading, recency decay penalization, and anti-spoof checks. |
| | [`GroundingGateAgent`](agents/grounding_gate_agent.py) | Strict citation and numeric claim verification preventing hallucinations. |
| | [`ReflexionAgent`](agents/reflexion_agent.py) | Self-critique engine checking reasoning bounds and statistical plausibility. |
| **Semantic & Context** | [`EntityResolutionAgent`](agents/entity_resolution_agent.py) | Normalizes company names, tickers, and token addresses across dirty text. |
| | [`SentimentAgent`](agents/sentiment_agent.py) | Lexicon and contextual sentiment scoring per resolved entity. |
| | [`TrendAgent`](agents/trend_agent.py) | Statistical z-score keyword spike detection against historical baselines. |
| | [`RagInsightAgent`](agents/rag_agent.py) | 512-char recursive chunking, ChromaDB & TF-IDF historical precedent matching. |
| | [`DeepSearchAgent`](agents/deep_search_agent.py) | Multi-hop external web search and SEC EDGAR 8-K retrieval for breaking events. |
| | [`ConfidenceScoringAgent`](agents/confidence_agent.py) | Bayesian multi-factor confidence scoring and source conflict adjudication. |
| **Forensic & Macro** | [`DiscrepancyAuditorAgent`](agents/discrepancy_auditor_agent.py) | SEC 10-Q forensic parser detecting revenue vs cash flow divergence. |
| | [`GeopoliticalRiskAgent`](agents/geopolitical_risk_agent.py) | Maritime chokepoint monitor (Hormuz, Malacca, Taiwan Strait, Bab-el-Mandeb). |
| | [`MacroRatesAgent`](agents/macro_rates_agent.py) | Sovereign yields, Fed futures, 2Y/10Y inversion tracking, and terminal rates. |
| | [`GlobalMacroAgent`](agents/global_macro_agent.py) | Cross-asset macro regime monitor (DXY, WTI crude, Dr. Copper, gold). |
| **Alpha & Strategy** | [`VibeQuantAgent`](agents/vibe_quant_agent.py) | Social retail sentiment velocity vs market microstructure confluence. |
| | [`LiquidityOrderFlowAgent`](agents/liquidity_order_flow_agent.py) | Level-2 book skew, bid/ask imbalance, and institutional dark pool prints. |
| | [`MarketCorrelationAgent`](agents/market_correlation_agent.py) | Dynamic rolling covariance matrices and cross-sector beta shifts. |
| | [`ForecastingAgent`](agents/forecasting_agent.py) | Multi-horizon directional forecasts with asymmetric confidence intervals. |
| | [`CompetitorAgent`](agents/competitor_agent.py) | Peer group margin benchmarking and competitive moat threat detection. |
| | [`RiskSentinelAgent`](agents/risk_sentinel_agent.py) | Value-at-Risk (VaR), tail risk hedging bounds, and maximum drawdown limits. |
| | [`ExecutionRouterAgent`](agents/execution_router_agent.py) | Algorithmic routing (TWAP, VWAP, POV) and transaction cost analysis (TCA). |
| **Voice & Biometrics** | [`KimVoiceAgent`](agents/kim_voice_agent.py) | High-definition female executive voice briefing generator (Windows SAPI). |
| | [`FridayVoiceAgent`](agents/friday_voice_agent.py) | Conversational voice intelligence interface. |
| | [`VoiceSecurityAgent`](agents/voice_security_agent.py) | Wav2Vec 2.0 acoustic voiceprint registration and biometric auth. |
| **Learning & Synthesis** | [`HermesSelfLearningAgent`](agents/hermes_self_learning_agent.py) | Autonomous closed-loop skill creation, execution tuning, and persistent recall. |
| | [`ReportGenerationAgent`](agents/report_agent.py) | Generates structured Markdown and JSON intelligence dossiers. |
| | [`QueryMemoryAgent`](agents/query_memory_agent.py) | Manages persistent analyst queries, user personalization, and context retrieval. |
| | [`LiveDaemon`](agents/live_daemon.py) | Autonomous background daemon orchestrating periodic pipeline cycles. |
| **Supervisor & Team** | [`SupervisorAgent`](orchestration/supervisor.py) | Stateful graph supervisor routing conditional flow and gating anomalies. |
| | [`CrewAITeam`](orchestration/crew_tasks.py) | Multi-agent narrative consensus synthesis (Senior Macro + Forensic Quants). |

---

## Power BI Kimball Star Schema Export

SIGNALORA features a full dimensional modeling engine ([`exports/powerbi_export.py`](exports/powerbi_export.py)) that produces an enterprise-grade Kimball Star Schema directly into `exports/output/`:

### Star Schema Architecture
```
                         ┌─────────────────────┐
                         │      dim_date       │
                         │ (date_key, quarter) │
                         └──────────┬──────────┘
                                    │ 1
                                    │
                                    │ *
┌────────────────────┐   *    ┌─────┴─────────────────────┐    *    ┌────────────────────┐
│     dim_entity     │────────│  fact_market_intelligence │────────│     dim_source     │
│ (sector, exchange) │ 1      │  (scores, prices, z-score)│      1 │ (credibility_tier) │
└────────────────────┘        └─────┬─────────────────────┘         └────────────────────┘
                                    │ *
                                    │
                                    │ 1
                         ┌──────────┴──────────┐
                         │ dim_agent_execution │
                         │ (latency_ms, status)│
                         └─────────────────────┘
```

- **`fact_market_intelligence.csv`**: Central fact table storing granularity per insight, joined to date, entity, source, and run execution with metric measures: `confidence_score`, `sentiment_score`, `trend_zscore`, `asset_price_usd`, `forecast_return_pct`, `is_flagged`, `is_anomalous`.
- **`dim_entity.csv`**: Entity dimension containing ticker symbols, canonical names, asset class, sector taxonomy, and primary exchange.
- **`dim_source.csv`**: Source provenance dimension with credibility tiers (Tier 1 Institutional, Tier 2 Financial Media, Tier 3 Alternative Social).
- **`dim_date.csv`**: Time dimension covering year, quarter, month, day, day of week, and weekend flags.
- **`dim_agent_execution.csv`**: Performance telemetry dimension recording agent execution latency (ms) and success status per run.
- **`star_schema_manifest.json`**: Machine-readable Power BI data model manifest declaring table relationships, cardinality (`ManyToOne`), cross-filtering directions, and pre-built DAX measures (`Average Confidence`, `Weighted Sentiment`, `Anomalous Signal Count`, `Average Pipeline Latency (ms)`).

---

## Closed-Loop Self-Learning

Inspired by the self-evolving architecture of Nous Research's Hermes Agent, SIGNALORA features an autonomous procedural skill synthesis loop located in [`skills/`](skills/):

```
       ┌────────────────────────┐
       │   Market Pipeline Run  │
       └───────────┬────────────┘
                   │  Outcomes & Metrics
                   ▼
       ┌────────────────────────┐
       │     Reflexion Agent    │ ───► Evaluates prediction vs realized reality
       └───────────┬────────────┘
                   │  Identifies strategic gaps
                   ▼
       ┌────────────────────────┐
       │  Hermes Learning Agent │ ───► Synthesizes new executable Python Skill
       └───────────┬────────────┘
                   │  Registers into Skill Registry
                   ▼
       ┌────────────────────────┐
       │   Active Skill Suite   │
       │ • Carry Trade Unwind   │
       │ • Chokepoint Hedging   │
       │ • SEC Discrepancy      │
       │ • Vibe Quant Confluence│
       │ • Microstructure TCA   │
       └────────────────────────┘
```

Skills are stored as modular Python modules implementing `BaseSkill`, dynamically loaded at runtime by the `SkillRegistry`, with persistent execution memories saved in `storage/memory/MEMORY.md`.

---

## Voice AI & Biometrics

### KIM (Knowledge & Intelligence Model)
SIGNALORA includes **KIM**, a dedicated voice AI executive strategist:
- **Audio Architecture**: High-fidelity 16-bit, 16,000Hz speech engine leveraging native Windows SAPI voices (Microsoft Zira / Hazel / David) with graceful algorithmic wav synthesis fallback.
- **Executive Voice Briefings**: Generates spoken morning and intraday market intelligence memos downloadable directly through the Streamlit dashboard or FastAPI stream.

### Wav2Vec 2.0 Voice Biometrics
Security is guaranteed through acoustic speaker identification:
- Enrolls operator voiceprints via acoustic mel-frequency extraction.
- Prevents unauthorized command execution through cosine distance verification and ambient noise floor anti-spoofing.

---

## Dual-Interface Ecosystem

SIGNALORA delivers two concurrent local interfaces designed for research and execution:

### 1. Streamlit Institutional Terminal (`http://localhost:8501`)
- **Cyberpunk Blackbox Aesthetics**: Deep charcoal (`#0a0b0e`) and golden amber (`#f39c12`) color tokens.
- **Real-Time Ticker Tape**: Continuously streaming asset quotes, percentage shifts, and sentiment labels.
- **Interactive Global Supply Chain Map**: Renders real-time status across maritime trade chokepoints.
- **Human Review Center**: Instant one-click approval or rejection of quarantined market alerts.
- **Embedded Audio Player**: Stream and replay KIM's voice intelligence briefings directly in the browser.

### 2. FastAPI Research Desk (`http://127.0.0.1:8000`)
High-concurrency async REST API with interactive Swagger docs at `http://127.0.0.1:8000/docs`:
- `POST /api/run`: Trigger full or partial pipeline runs with custom parameters.
- `GET /api/dashboard`: Fetch live telemetry, confidence distributions, and recent insights.
- `GET /api/review-queue`: Inspect all alerts awaiting human operator decision.
- `POST /api/review-queue/{queue_id}/decision`: Submit approval or rejection with audit commentary.
- `POST /api/voice-briefing`: Generate on-demand KIM audio briefings for any ticker.

---

## Quickstart

### Prerequisites
- Python 3.11 or higher
- Git
- Windows (native SAPI voice support) / Linux / macOS

### 1. Clone & Setup Environment

```bash
git clone https://github.com/VaradPatil5005/market-intel-system.git
cd market-intel-system

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # On Windows
# source venv/bin/activate # On Linux/macOS

# Install pinned dependencies
pip install -r requirements.txt
```

### 2. Initialize Database & Seed

```bash
python scripts/migrate_db.py
```

### 3. Launch Local Servers

In PowerShell / Terminal 1 (Streamlit UI):
```powershell
.\venv\Scripts\streamlit run ui/app.py --server.port 8501
```

In PowerShell / Terminal 2 (FastAPI Backend):
```powershell
.\venv\Scripts\python -m uvicorn api.main:app --port 8000 --reload
```

Open:
- **Terminal UI**: [http://localhost:8501](http://localhost:8501)
- **API Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Running Verification & Tests

SIGNALORA comes with an exhaustive test suite covering unit behaviors, state transitions, voice biometrics, star schema exports, and pipeline resilience:

```bash
pytest -v
```

```
====================== 114 passed, 3 warnings in 54.79s =======================
```

All 114 tests pass out of the box with zero external network or paid API key requirements.

---

## CLI Reference & Flags

Run a headless end-to-end market intelligence pipeline directly from the command line:

```bash
# Execute standard deterministic pipeline run
python main.py --seed 42

# Enforce human review threshold (gates signals under 80% confidence)
python main.py --min-confidence 0.80

# Generate Kimball Star Schema CSVs + manifest for Power BI
python main.py --export-powerbi

# Run in background daemon mode (continuous cycles every 300s)
python main.py --daemon --interval 300

# Combined production run with seed, confidence gate, and Power BI export
python main.py --seed 42 --min-confidence 0.80 --export-powerbi
```

### Supported CLI Flags
| Flag | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--seed` | `int` | `None` | Random seed for deterministic simulation and reproducibility. |
| `--min-confidence` | `float` | `None` | Overrides pipeline confidence threshold for human review routing. |
| `--export-powerbi` | `flag` | `False` | Generates 5-table Kimball Star Schema CSVs and JSON schema manifest. |
| `--mode` | `str` | `standard` | Pipeline execution mode (`standard`, `fast`, `deep`, `audit`). |
| `--daemon` | `flag` | `False` | Runs the pipeline continuously at fixed intervals. |
| `--interval` | `int` | `300` | Interval in seconds between daemon cycles. |
| `--run-id` | `str` | `auto` | Custom run identifier for checkpoint tracking. |
| `--top-k` | `int` | `5` | Maximum number of RAG historical precedents to retrieve. |

---

## Repository Structure

```
market-intel-system/
├── assets/
│   └── banner.png                # SIGNALORA visual brand identity
├── agents/                       # 32 Autonomous Intelligence Agents
│   ├── base.py                   # Abstract agent base class
│   ├── kim_voice_agent.py        # KIM voice synthesizer & strategist
│   ├── voice_security_agent.py   # Voice biometric authentication
│   ├── hermes_self_learning_agent.py # Closed-loop skill creator
│   ├── discrepancy_auditor_agent.py  # SEC 10-Q forensic analyzer
│   ├── geopolitical_risk_agent.py    # Maritime chokepoint monitor
│   ├── vibe_quant_agent.py       # Retail vibe vs book skew confluence
│   └── ...                       # Remaining specialized agents
├── orchestration/                # LangGraph Stateful Pipeline
│   ├── graph.py                  # Compiled state graph (0 typing errors)
│   ├── state.py                  # Typed PipelineState definitions
│   ├── supervisor.py             # Conditional routing & decision rules
│   └── crew_tasks.py             # CrewAI analyst synthesis team
├── exports/                      # Institutional Star Schema Hub
│   ├── powerbi_export.py         # Kimball Star Schema generator
│   └── csv_export.py             # Raw database snapshot exporter
├── skills/                       # Self-Learned Dynamic Trading Skills
│   ├── skill_registry.py         # Autonomous skill execution manager
│   ├── carry_trade_unwind_skill.py
│   ├── chokepoint_hedging_skill.py
│   ├── sec_discrepancy_skill.py
│   └── vibe_quant_confluence_skill.py
├── data/
│   └── historical_reports/       # Macro crisis dossiers for RAG retrieval
├── ui/                           # Streamlit Institutional Blackbox UI
│   ├── app.py                    # Multi-page dashboard
│   └── blackbox_theme.py         # Institutional design system
├── api/                          # FastAPI Async REST Endpoints
│   └── main.py                   # High-throughput API & review queue
├── database/                     # SQLAlchemy Models & SQLite Engine
│   ├── models.py                 # Structured schema definitions
│   └── session.py                # Connection pool & context managers
├── tests/                        # 114 Comprehensive Pytest Tests (14 suites)
├── storage/                      # Persistent state, memory & logs
└── utils/                        # Logging, resilience & market data
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

Built by **[Varad Patil](https://github.com/VaradPatil5005)**.
