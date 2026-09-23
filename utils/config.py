"""
Typed configuration for the Multi-Agent Market Intelligence System.

All settings are loaded from environment variables (optionally via a .env
file) with safe local-development defaults, so the system runs out of the
box in mock mode with zero external services configured.

v2 additions: deep search, live daemon, price data, reflexion learning,
grounding gate, Telegram/email alerting, user personalization.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database ---
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'storage' / 'market_intel.db'}"

    # --- Paths ---
    checkpoint_dir: Path = PROJECT_ROOT / "storage" / "checkpoints"
    chroma_dir: Path = PROJECT_ROOT / "storage" / "chroma"
    export_dir: Path = PROJECT_ROOT / "exports" / "output"
    log_dir: Path = PROJECT_ROOT / "storage" / "logs"
    seed_data_dir: Path = PROJECT_ROOT / "data" / "seed"
    historical_reports_dir: Path = PROJECT_ROOT / "data" / "historical_reports"
    ticker_map_path: Path = PROJECT_ROOT / "data" / "ticker_map.json"

    # --- Retry / resilience ---
    max_retries: int = 3
    retry_backoff_seconds: float = 2.0

    # --- Ingestion ---
    news_rss_feeds: str = ""  # comma-separated; empty => mock/seed mode
    company_watchlist: str = "OpenAI,Anthropic,Nvidia,Microsoft,Google"

    # --- Confidence / human review ---
    low_confidence_threshold: float = 0.55
    human_review_required_below: float = 0.65
    human_review_mode: str = "auto"
    # "auto"  — deterministic formula-based reviewer (safe for CI, batch jobs, demos)
    # "queue" — pipeline halts, writes ReviewQueueItem to DB, waits for async analyst
    #           approval via API before proceeding to report generation.

    # --- Cross-source verification gate (v2) ---
    min_cross_source_verification: int = 2   # insights with fewer sources auto-flagged

    # --- Optional external API keys ---
    newsapi_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # --- Tier 1/2/3 feature flags & tuning (all default to safe/offline behavior) ---
    use_embedding_entity_resolution: bool = True
    entity_embedding_similarity_threshold: float = 0.75
    embedding_model_name: str = "all-MiniLM-L6-v2"

    use_chroma_rag: bool = True
    trend_anomaly_z_threshold: float = 2.0
    trend_ewma_span: int = 5

    use_finbert_sentiment: bool = True
    finbert_model_name: str = "ProsusAI/finbert"

    forecasting_min_observations: int = 10

    # --- Alerting (v1 + v2 multi-channel) ---
    alert_webhook_url: str = ""                    # Slack / generic JSON webhook
    alert_confidence_threshold: float = 0.85
    slack_webhook_url: str = ""                    # dedicated Slack hook (v2)
    telegram_bot_token: str = ""                   # Telegram bot token (v2)
    telegram_chat_id: str = ""                     # Telegram chat/channel ID (v2)
    email_smtp_host: str = ""                      # SMTP server (v2)
    email_smtp_port: int = 587
    email_smtp_user: str = ""
    email_smtp_password: str = ""
    email_alert_to: str = ""                       # comma-separated recipients
    z_score_alert_threshold: float = 3.0           # Z-score that triggers immediate mini-run

    # --- Playwright ingestion ---
    use_playwright_ingestion: bool = False
    playwright_urls: str = ""

    # --- v2: Deep web search (free DuckDuckGo or Tavily) ---
    enable_deep_search: bool = False               # activates DeepSearchAgent
    deep_search_provider: str = "duckduckgo"       # "duckduckgo" | "tavily"
    deep_search_api_key: str = ""                  # required only for "tavily"
    deep_search_max_results: int = 5
    deep_search_on_anomaly_only: bool = True       # only trigger on Z-score spikes

    # --- Agent-Reach Multi-Platform Internet Engine ---
    enable_agent_reach: bool = True                # unified multi-platform research
    agent_reach_prefer_jina: bool = True           # clean markdown web scraping via Jina Reader
    agent_reach_exa_enabled: bool = True           # Exa search routing
    agent_reach_xueqiu_enabled: bool = True        # Xueqiu equity quotes & hot sentiment
    agent_reach_reddit_enabled: bool = True        # Reddit social sentiment
    agent_reach_twitter_enabled: bool = True       # Twitter/X channel routing
    agent_reach_youtube_enabled: bool = True       # YouTube transcript & audio routing
    groq_api_key: str = ""                         # Optional Groq Whisper key

    # --- v2: SEC EDGAR ingestion ---
    enable_sec_edgar: bool = True                  # free, no key; fetches 8-K filings
    sec_edgar_lookback_days: int = 7

    # --- v2: Price data enrichment ---
    price_data_enabled: bool = False               # activates PriceDataAgent (yfinance)
    price_data_lookback_days: int = 30
    price_rsi_period: int = 14

    # --- v2: Reflexion self-learning ---
    enable_reflexion_learning: bool = True         # auto-generate lessons from human edits
    reflexion_top_k_lessons: int = 3              # lessons retrieved per insight
    reflexion_lesson_similarity_threshold: float = 0.50

    # --- v2: Grounding gate ---
    enable_grounding_gate: bool = True             # verify numeric claims before publish
    grounding_tolerance_pct: float = 0.05          # 5% tolerance for numeric match

    # --- v2: Adaptive confidence weights ---
    adaptive_confidence_weights: bool = False       # Bayesian weight tuning from history

    # --- v2: Live daemon ---
    enable_live_daemon: bool = False               # real-time polling daemon
    live_poll_interval_seconds: int = 300          # 5-minute polling cycle
    live_daemon_run_mini_pipeline: bool = True     # trigger mini-run on spike

    # --- v2: User personalization ---
    user_id: str = "default"                       # user persona identifier
    user_risk_appetite: str = "moderate"           # conservative / moderate / speculative
    user_preferred_depth: str = "standard"         # brief / standard / deep

    # --- v2: Market correlation ---
    enable_market_correlation: bool = True          # compute cross-entity correlation matrix
    correlation_min_observations: int = 5

    # --- v2: Technical indicators (when price_data_enabled=True) ---
    enable_technical_indicators: bool = False       # RSI, Bollinger Bands, momentum
    bollinger_band_window: int = 20
    bollinger_band_std: float = 2.0

    # --- v2: Counterfactual scenarios ---
    enable_counterfactual_scenarios: bool = True   # supply chain impact scenarios

    # --- Optional advanced: Competitor monitoring ---
    enable_competitor_monitor: bool = False        # activates CompetitorMonitorAgent

    @property
    def playwright_url_list(self) -> List[str]:
        return [u.strip() for u in self.playwright_urls.split(",") if u.strip()]

    @property
    def rss_feed_list(self) -> List[str]:
        return [f.strip() for f in self.news_rss_feeds.split(",") if f.strip()]

    @property
    def watchlist(self) -> List[str]:
        return [c.strip() for c in self.company_watchlist.split(",") if c.strip()]

    @property
    def email_recipients(self) -> List[str]:
        return [e.strip() for e in self.email_alert_to.split(",") if e.strip()]

    def ensure_dirs(self) -> None:
        for d in (self.checkpoint_dir, self.chroma_dir, self.export_dir, self.log_dir):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
