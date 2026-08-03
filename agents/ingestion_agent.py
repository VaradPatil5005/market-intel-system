"""
Ingestion Agent.

Fetches raw market/news content from RSS feeds, company sources, or
(when no live sources are configured / reachable) falls back to bundled
mock/seed data so the pipeline always has something to process.
Normalizes everything into a common record shape before persistence.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import feedparser
import requests
from tenacity import RetryError

from agents.base import BaseAgent
from database.models import RawSource
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id, normalize_text, parse_date, retry_wrapper

raw_source_repo = Repository(RawSource)


class IngestionAgent(BaseAgent):
    name = "ingestion_agent"

    def __init__(self, metrics=None):
        super().__init__(metrics)
        self._retry = retry_wrapper(
            max_attempts=settings.max_retries,
            backoff_seconds=settings.retry_backoff_seconds,
            exceptions=(requests.RequestException,),
        )

    # ------------------------------------------------------------------
    def run(self, session: Session) -> List[RawSource]:
        """Fetch from configured feeds; fall back to mock seed data."""
        with self.run_tracked("ingest"):
            records: List[Dict[str, Any]] = []

            feeds = settings.rss_feed_list
            if feeds:
                for feed_url in feeds:
                    records.extend(self._fetch_rss_safe(feed_url))

            if not records:
                self.logger.info("No live sources configured/reachable — using mock seed data.")
                records.extend(self._load_seed_data())

            saved = [self._to_raw_source(r) for r in records]
            raw_source_repo.bulk_insert(session, saved)

            for r in saved:
                if self.metrics:
                    self.metrics.record_source_used(r.source_name)

            self.audit(
                session,
                step="ingest",
                action="fetched_and_normalized_sources",
                input_summary={"feeds_configured": len(feeds)},
                output_summary={"records_ingested": len(saved)},
            )
            return saved

    # ------------------------------------------------------------------
    def _fetch_rss_safe(self, feed_url: str) -> List[Dict[str, Any]]:
        try:
            return self._retry(self._fetch_rss)(feed_url)
        except (RetryError, requests.RequestException) as exc:
            self.logger.warning(f"Feed fetch failed after retries: {feed_url} ({exc})")
            return []

    def _fetch_rss(self, feed_url: str) -> List[Dict[str, Any]]:
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        results = []
        for entry in parsed.entries:
            results.append(
                {
                    "source_name": parsed.feed.get("title", feed_url),
                    "source_type": "rss",
                    "url": entry.get("link"),
                    "title": entry.get("title"),
                    "content": normalize_text(entry.get("summary", "")),
                    "published_at": entry.get("published", ""),
                }
            )
        return results

    def _load_seed_data(self) -> List[Dict[str, Any]]:
        seed_dir = Path(settings.seed_data_dir)
        records: List[Dict[str, Any]] = []
        for path in sorted(seed_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            items = data if isinstance(data, list) else [data]
            records.extend(items)
        return records

    def _to_raw_source(self, record: Dict[str, Any]) -> RawSource:
        return RawSource(
            id=new_id("src"),
            source_name=record.get("source_name", "unknown"),
            source_type=record.get("source_type", "mock"),
            url=record.get("url"),
            title=normalize_text(record.get("title", "")),
            content=normalize_text(record.get("content", "")),
            published_at=parse_date(record.get("published_at")).isoformat(),
            fetched_at=iso_now(),
            raw_metadata=json.dumps(record.get("metadata", {})),
        )
