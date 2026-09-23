"""
Agent-Reach Unified Research Service for SIGNALORA.

Bridges the institutional multi-agent market intelligence pipeline
with the Agent-Reach multi-platform internet capability router (16 channels):
- Web reading & Jina Reader (r.jina.ai)
- Exa AI neural search & DuckDuckGo fallback
- Xueqiu equity quotes, hot stocks, and market sentiment
- Reddit & Twitter/X channel routing
- YouTube video transcripts & financial media extraction
- System health diagnostic matrix (Doctor)
"""
from __future__ import annotations

import html
import json
import logging
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from utils.config import settings
from utils.helpers import normalize_text

logger = logging.getLogger(__name__)


class AgentReachService:
    """
    Institutional facade for all Agent-Reach capabilities.
    Thread-safe, exception-contained, with zero-failure fallbacks.
    """

    _instance: Optional[AgentReachService] = None

    def __new__(cls) -> AgentReachService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._config = None
        self._init_reach_config()

    def _init_reach_config(self):
        try:
            from agent_reach.config import Config
            self._config = Config()
            if settings.groq_api_key:
                self._config.set("groq_key", settings.groq_api_key)
        except Exception as exc:
            logger.debug(f"AgentReach config initialization warning: {exc}")
            self._config = None

    # -------------------------------------------------------------------------
    # 1. Environment Health Diagnostics (Doctor)
    # -------------------------------------------------------------------------
    def run_doctor(self) -> Dict[str, Any]:
        """
        Runs comprehensive platform availability diagnostics across all 16 channels.
        Returns machine-readable channel status matrix.
        """
        try:
            from agent_reach.doctor import check_all
            from agent_reach.config import Config

            cfg = self._config or Config()
            channel_results = check_all(cfg)
            summary = {
                "total_channels": len(channel_results),
                "ok_count": sum(1 for c in channel_results.values() if c.get("status") == "ok"),
                "warn_count": sum(1 for c in channel_results.values() if c.get("status") == "warn"),
                "off_count": sum(1 for c in channel_results.values() if c.get("status") == "off"),
                "error_count": sum(1 for c in channel_results.values() if c.get("status") == "error"),
                "channels": channel_results,
            }
            return summary
        except Exception as exc:
            logger.warning(f"AgentReach doctor execution error: {exc}")
            return {
                "total_channels": 0,
                "ok_count": 0,
                "warn_count": 0,
                "off_count": 0,
                "error_count": 1,
                "error": str(exc),
                "channels": {},
            }

    # -------------------------------------------------------------------------
    # 2. Universal URL Reader (Jina Reader with direct fallback)
    # -------------------------------------------------------------------------
    def read_url(self, url: str, timeout: int = 20) -> Dict[str, Any]:
        """
        Converts any web page or analyst report into clean Markdown text.
        Primary: Jina Reader (https://r.jina.ai/<url>)
        Fallback: Direct HTTP request with HTML-to-markdown text extraction.
        """
        clean_url = url.strip()
        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            clean_url = "https://" + clean_url

        # Method A: Agent-Reach WebChannel (Jina Reader)
        if settings.agent_reach_prefer_jina:
            try:
                from agent_reach.channels.web import WebChannel
                ch = WebChannel()
                raw_markdown = ch.read(clean_url)
                if raw_markdown and len(raw_markdown.strip()) > 30:
                    lines = [ln.strip() for ln in raw_markdown.splitlines() if ln.strip()]
                    title = lines[0].lstrip("#").strip() if lines else "Document"
                    return {
                        "status": "success",
                        "provider": "Jina Reader",
                        "url": clean_url,
                        "title": title[:200],
                        "content": raw_markdown,
                        "char_count": len(raw_markdown),
                        "word_count": len(raw_markdown.split()),
                    }
            except Exception as exc:
                logger.debug(f"Jina Reader fallback for {clean_url}: {exc}")

        # Method B: Direct HTTP fetch with robust text conversion
        try:
            req = urllib.request.Request(
                clean_url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 MarketIntel/2.0"
                    ),
                    "Accept": "text/html,application/xhtml+xml,text/plain",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                raw_html = resp.read(2 * 1024 * 1024).decode(charset, errors="replace")

            title_match = re.search(r"<title[^>]*>(.*?)</title>", raw_html, re.IGNORECASE | re.DOTALL)
            title = html.unescape(title_match.group(1)).strip() if title_match else clean_url

            # Remove scripts, styles, metadata
            no_scripts = re.sub(r"<(script|style|nav|footer|header|noscript)[^>]*>.*?</\1>", " ", raw_html, flags=re.IGNORECASE | re.DOTALL)
            text_only = re.sub(r"<[^>]+>", " ", no_scripts)
            cleaned = html.unescape(text_only)
            normalized = re.sub(r"\s+", " ", cleaned).strip()

            return {
                "status": "success",
                "provider": "Direct Fetch",
                "url": clean_url,
                "title": title[:200],
                "content": normalized[:15000],
                "char_count": len(normalized),
                "word_count": len(normalized.split()),
            }
        except Exception as exc:
            logger.warning(f"Failed to read URL {clean_url}: {exc}")
            return {
                "status": "error",
                "provider": "None",
                "url": clean_url,
                "title": "Unreachable Resource",
                "content": f"Unable to fetch URL {clean_url}: {exc}",
                "char_count": 0,
                "word_count": 0,
            }

    # -------------------------------------------------------------------------
    # 3. Multi-Provider Web Search
    # -------------------------------------------------------------------------
    def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Executes an internet search across configured providers.
        Returns a list of search result dictionaries with title, url, snippet, source.
        """
        results: List[Dict[str, Any]] = []
        cleaned_query = query.strip()
        if not cleaned_query:
            return results

        # Provider 1: DuckDuckGo Instant Answer / HTML search (Free, zero-config)
        try:
            ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote_plus(cleaned_query)}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(
                ddg_url,
                headers={"User-Agent": "MarketIntelSystem/2.0 (Research)"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))

            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "url": topic.get("FirstURL", ""),
                        "snippet": normalize_text(topic.get("Text", "")),
                        "source": "DuckDuckGo",
                    })

            if data.get("AbstractText"):
                results.append({
                    "title": f"Summary: {cleaned_query}",
                    "url": data.get("AbstractURL", ""),
                    "snippet": normalize_text(data["AbstractText"]),
                    "source": "DuckDuckGo Abstract",
                })
        except Exception as exc:
            logger.debug(f"DuckDuckGo search error for '{cleaned_query}': {exc}")

        # Provider 2: Google News RSS Search fallback for market topics
        if len(results) < max_results:
            try:
                import feedparser
                news_rss = f"https://news.google.com/rss/search?q={urllib.parse.quote_plus(cleaned_query)}&hl=en-US&gl=US&ceid=US:en"
                feed = feedparser.parse(news_rss)
                for entry in feed.entries[:max_results - len(results)]:
                    results.append({
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "snippet": normalize_text(entry.get("summary", entry.get("title", ""))),
                        "source": "Google News Live",
                    })
            except Exception as exc:
                logger.debug(f"Google News search error for '{cleaned_query}': {exc}")

        return results[:max_results]

    # -------------------------------------------------------------------------
    # 4. Xueqiu Equity Intel & Social Sentiment
    # -------------------------------------------------------------------------
    def get_stock_intel(self, symbol_or_query: str) -> Dict[str, Any]:
        """
        Fetches stock quote metrics and community sentiment posts from Xueqiu.
        Supports Chinese A-shares (SH600519), HK shares (00700), and US equities (NVDA, AAPL).
        """
        result = {
            "symbol": symbol_or_query.upper(),
            "quote": {},
            "trending_posts": [],
            "source": "Xueqiu",
        }
        if not settings.agent_reach_xueqiu_enabled:
            return result

        try:
            from agent_reach.channels.xueqiu import XueqiuChannel
            xq = XueqiuChannel()
            quote_data = xq.get_stock_quote(symbol_or_query.upper())
            if quote_data and quote_data.get("current"):
                result["quote"] = quote_data

            hot_posts = xq.get_hot_posts(limit=6)
            if hot_posts:
                result["trending_posts"] = hot_posts
        except Exception as exc:
            logger.debug(f"Xueqiu stock intel query notice for '{symbol_or_query}': {exc}")

        return result

    # -------------------------------------------------------------------------
    # 5. Social Discussions & Community Sentiment (Reddit, Twitter, Xueqiu)
    # -------------------------------------------------------------------------
    def search_social_discussions(self, entity_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Discovers social community discussions and market velocity across platforms.
        """
        discussions: List[Dict[str, Any]] = []

        # Channel A: Xueqiu hot posts mentioning entity
        try:
            from agent_reach.channels.xueqiu import XueqiuChannel
            xq = XueqiuChannel()
            posts = xq.get_hot_posts(limit=25)
            entity_lower = entity_name.lower()
            for p in posts:
                txt = (p.get("title", "") + " " + p.get("text", "")).lower()
                if entity_lower in txt:
                    discussions.append({
                        "platform": "Xueqiu (Equities)",
                        "title": p.get("title") or f"Discussion on {entity_name}",
                        "content": p.get("text", ""),
                        "author": p.get("author", "Analyst"),
                        "likes": p.get("likes", 0),
                        "url": p.get("url", "https://xueqiu.com"),
                    })
                    if len(discussions) >= limit:
                        break
        except Exception as exc:
            logger.debug(f"Social search Xueqiu notice: {exc}")

        # Channel B: Reddit financial search
        try:
            reddit_url = (
                f"https://www.reddit.com/search.json?q={urllib.parse.quote_plus(entity_name + ' stock')}"
                "&sort=new&limit=5&restrict_sr=false"
            )
            req = urllib.request.Request(
                reddit_url,
                headers={"User-Agent": "MarketIntelSystem/2.0 (Research)"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            posts = data.get("data", {}).get("children", [])
            for post in posts[:limit - len(discussions)]:
                pd = post.get("data", {})
                title = pd.get("title", "")
                selftext = pd.get("selftext", "")[:400]
                discussions.append({
                    "platform": f"Reddit/{pd.get('subreddit_name_prefixed', 'r/investing')}",
                    "title": title,
                    "content": selftext or title,
                    "author": pd.get("author", "user"),
                    "likes": pd.get("ups", 0),
                    "url": f"https://reddit.com{pd.get('permalink', '')}",
                })
        except Exception as exc:
            logger.debug(f"Social search Reddit notice: {exc}")

        return discussions

    # -------------------------------------------------------------------------
    # 6. YouTube Transcripts & Audio Transcription
    # -------------------------------------------------------------------------
    def get_video_transcript(self, url: str, provider: str = "auto") -> Dict[str, Any]:
        """
        Retrieves subtitles or audio transcript for an investor call or video presentation.
        """
        try:
            from agent_reach.channels.youtube import YouTubeChannel
            yt = YouTubeChannel()
            if yt.can_handle(url):
                transcript_text = yt.transcribe(
                    url,
                    provider=provider,
                    config=self._config,
                    allow_provider_fallback=True,
                )
                return {
                    "status": "success",
                    "url": url,
                    "provider": provider,
                    "transcript": transcript_text,
                    "length": len(transcript_text),
                }
            else:
                return {
                    "status": "unsupported",
                    "url": url,
                    "error": "URL is not recognized as a YouTube video resource.",
                    "transcript": "",
                }
        except Exception as exc:
            logger.warning(f"Video transcription notice for {url}: {exc}")
            return {
                "status": "error",
                "url": url,
                "error": str(exc),
                "transcript": "",
            }


# Module singleton instance
reach_service = AgentReachService()
