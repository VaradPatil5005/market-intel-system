"""
Typed configuration for the Multi-Agent Market Intelligence System.

All settings are loaded from environment variables (optionally via a .env
file) with safe local-development defaults, so the system runs out of the
box in mock mode with zero external services configured.
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

    # --- Retry / resilience ---
    max_retries: int = 3
    retry_backoff_seconds: float = 2.0

    # --- Ingestion ---
    news_rss_feeds: str = ""  # comma-separated; empty => mock/seed mode
    company_watchlist: str = "OpenAI,Anthropic,Nvidia,Microsoft,Google"

    # --- Confidence / human review ---
    low_confidence_threshold: float = 0.55
    human_review_required_below: float = 0.65

    # --- Optional external API keys ---
    newsapi_key: str = ""
    openai_api_key: str = ""

    @property
    def rss_feed_list(self) -> List[str]:
        return [f.strip() for f in self.news_rss_feeds.split(",") if f.strip()]

    @property
    def watchlist(self) -> List[str]:
        return [c.strip() for c in self.company_watchlist.split(",") if c.strip()]

    def ensure_dirs(self) -> None:
        for d in (self.checkpoint_dir, self.chroma_dir, self.export_dir, self.log_dir):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
