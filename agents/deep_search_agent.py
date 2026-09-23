"""
Deep Search Agent — Autonomous Internet-Wide Discovery.

When the pipeline detects a significant anomaly (EWMA Z-score above threshold)
for a tracked entity, this agent autonomously searches the internet for
explanatory context: news, regulatory filings, analyst commentary.

Data sources (in priority order):
  1. Tavily API (if api key configured) — high-quality filtered news search
  2. DuckDuckGo Instant Answer API (free, no key, rate-limited)
  3. SEC EDGAR RSS 8-K filings (always on when enable_sec_edgar=True)
  4. Reddit financial subreddits via Pushshift-compatible endpoint

All discovered items are converted to RawSource records and injected into
the current session so downstream agents (CredibilityAgent, EntityAgent, etc.)
process them normally — they're indistinguishable from RSS-fetched content.

Graceful degradation:
  - If no search provider works → logs and returns []
  - If SEC EDGAR is unreachable → skips silently
  - Never raises — always returns a (possibly empty) list
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import requests

from agents.base import BaseAgent
from database.models import RawSource
from database.session import Repository, Session
from utils.agent_reach_service import reach_service
from utils.config import settings
from utils.helpers import iso_now, new_id, normalize_text
from utils.logging_setup import get_logger

logger = get_logger("deep_search_agent")

raw_source_repo = Repository(RawSource)

SEC_EDGAR_RSS = (
    "https://efts.sec.gov/LATEST/search-index?q=%22{company}%22&dateRange=custom"
    "&startdt={start_date}&forms=8-K&hits.hits._source=period_of_report,"
    "entity_name,file_date,form_type,period_of_report"
)
SEC_EDGAR_FULL = "https://efts.sec.gov/LATEST/search-index?q=%22{company}%22&forms=8-K&hits.hits.total.value=1"

DDGO_SEARCH = "https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
REDDIT_SEARCH = (
    "https://www.reddit.com/search.json?q={query}&sort=new&limit=10&restrict_sr=false"
    "&sr_detail=false&include_over_18=false"
)
FINANCIAL_SUBREDDITS = ["r/stocks", "r/investing", "r/wallstreetbets", "r/SecurityAnalysis"]


class DeepSearchAgent(BaseAgent):
    name = "deep_search_agent"

    def run(
        self,
        session: Session,
        anomalous_entities: List[str],
        run_id: Optional[str] = None,
    ) -> List[RawSource]:
        """Run deep search for all anomalous entities.

        Args:
            anomalous_entities: List of entity canonical names with Z-score spikes
            run_id: current pipeline run ID for audit

        Returns:
            List of newly-created RawSource records (already persisted to session)
        """
        if not settings.enable_deep_search and not settings.enable_sec_edgar and not settings.enable_agent_reach:
            logger.info("DeepSearchAgent: deep search, sec_edgar, and agent_reach disabled — skipping.")
            return []

        with self.run_tracked("deep_search"):
            all_sources: List[RawSource] = []

            for entity_name in anomalous_entities:
                logger.info(f"DeepSearchAgent: searching for anomalous entity '{entity_name}'")

                # 1. Agent Reach Multi-Platform Research Engine
                if settings.enable_agent_reach:
                    reach_sources = self._agent_reach_search(entity_name)
                    all_sources.extend(self._to_raw_sources(session, reach_sources, entity_name))

                # 2. Traditional Web Search (Tavily or DuckDuckGo)
                if settings.enable_deep_search and not settings.enable_agent_reach:
                    web_results = self._web_search(entity_name)
                    all_sources.extend(self._to_raw_sources(session, web_results, entity_name))

                # 3. SEC EDGAR Material Event Filings (Form 8-K)
                if settings.enable_sec_edgar:
                    sec_results = self._sec_edgar_search(entity_name)
                    all_sources.extend(self._to_raw_sources(session, sec_results, entity_name))

                # 4. Reddit direct fallback
                if not settings.enable_agent_reach:
                    reddit_results = self._reddit_search(entity_name)
                    if reddit_results:
                        all_sources.extend(self._to_raw_sources(session, reddit_results, entity_name))

            self.audit(
                session,
                step="deep_search",
                action="autonomous_web_discovery",
                input_summary={"anomalous_entities": anomalous_entities},
                output_summary={"new_sources_found": len(all_sources)},
            )
            logger.info(
                f"DeepSearchAgent: discovered {len(all_sources)} new sources "
                f"for {len(anomalous_entities)} anomalous entities."
            )
            return all_sources

    # ------------------------------------------------------------------
    def _agent_reach_search(self, entity_name: str) -> List[Dict[str, Any]]:
        """Multi-platform discovery via Agent-Reach engine."""
        results: List[Dict[str, Any]] = []
        try:
            # A. Web Search (Jina / Exa / DDG)
            web_hits = reach_service.search_web(f"{entity_name} stock market catalysts risk", max_results=3)
            for hit in web_hits:
                results.append({
                    "source_name": f"AgentReach/{hit.get('source', 'Web')}",
                    "source_type": "deep_search_reach_web",
                    "url": hit.get("url", ""),
                    "title": hit.get("title", f"{entity_name} Intelligence"),
                    "content": hit.get("snippet", ""),
                    "published_at": "",
                })

            # B. Xueqiu equity metrics & trending posts
            if settings.agent_reach_xueqiu_enabled:
                stock_intel = reach_service.get_stock_intel(entity_name)
                quote = stock_intel.get("quote", {})
                if quote and quote.get("current"):
                    curr = quote.get("current")
                    pct = quote.get("percent", 0.0)
                    pe = quote.get("pe_ttm", "N/A")
                    mc = quote.get("market_capital", "N/A")
                    results.append({
                        "source_name": "AgentReach/Xueqiu",
                        "source_type": "equity_telemetry_xueqiu",
                        "url": f"https://xueqiu.com/S/{entity_name}",
                        "title": f"{entity_name} — Xueqiu Equity Telemetry (Price: {curr}, Change: {pct}%)",
                        "content": normalize_text(
                            f"Live quote for {entity_name}: Price ${curr}, intraday change {pct}%, "
                            f"PE(TTM): {pe}, Market Cap: {mc}. Xueqiu institutional and retail sentiment tracking active."
                        ),
                        "published_at": "",
                    })
                for post in stock_intel.get("trending_posts", [])[:2]:
                    results.append({
                        "source_name": "AgentReach/Xueqiu",
                        "source_type": "social_sentiment_xueqiu",
                        "url": post.get("url", "https://xueqiu.com"),
                        "title": post.get("title") or f"{entity_name} Discussion",
                        "content": normalize_text(post.get("text", "")),
                        "published_at": "",
                    })

            # C. Social community discussions
            if settings.agent_reach_reddit_enabled or settings.agent_reach_twitter_enabled:
                socials = reach_service.search_social_discussions(entity_name, limit=2)
                for s in socials:
                    results.append({
                        "source_name": f"AgentReach/{s.get('platform', 'Social')}",
                        "source_type": "social_sentiment_reach",
                        "url": s.get("url", ""),
                        "title": s.get("title", f"{entity_name} Social Post"),
                        "content": normalize_text(s.get("content", "")),
                        "published_at": "",
                    })

        except Exception as exc:
            logger.warning(f"Agent-Reach discovery notice for '{entity_name}': {exc}")
        return results

    # ------------------------------------------------------------------
    def _web_search(self, entity_name: str) -> List[Dict[str, Any]]:
        """Search web for entity context using configured provider."""
        query = f"{entity_name} market news risk analysis"

        if settings.deep_search_provider == "tavily" and settings.deep_search_api_key:
            return self._tavily_search(query)
        else:
            return self._duckduckgo_search(query, entity_name)

    def _tavily_search(self, query: str) -> List[Dict[str, Any]]:
        try:
            resp = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.deep_search_api_key,
                    "query": query,
                    "max_results": settings.deep_search_max_results,
                    "search_depth": "basic",
                    "include_answer": False,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("results", []):
                results.append({
                    "source_name": item.get("source", "Tavily"),
                    "source_type": "deep_search_tavily",
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "content": normalize_text(item.get("content", "")[:3000]),
                    "published_at": item.get("published_date", ""),
                })
            return results
        except Exception as exc:
            logger.warning(f"Tavily search failed for '{query}': {exc}")
            return []

    def _duckduckgo_search(self, query: str, entity_name: str) -> List[Dict[str, Any]]:
        """Free DuckDuckGo Instant Answer search — no API key needed."""
        results = []
        try:
            url = DDGO_SEARCH.format(query=quote_plus(query))
            resp = requests.get(
                url,
                headers={"User-Agent": "MarketIntelSystem/2.0 (research)"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            # DuckDuckGo RelatedTopics
            for topic in data.get("RelatedTopics", [])[:settings.deep_search_max_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "source_name": "DuckDuckGo",
                        "source_type": "deep_search_ddg",
                        "url": topic.get("FirstURL", ""),
                        "title": f"{entity_name} — Related: {topic['Text'][:80]}",
                        "content": normalize_text(topic["Text"]),
                        "published_at": "",
                    })

            # Abstract if available
            if data.get("AbstractText"):
                results.append({
                    "source_name": "DuckDuckGo Abstract",
                    "source_type": "deep_search_ddg",
                    "url": data.get("AbstractURL", ""),
                    "title": f"{entity_name} — Summary",
                    "content": normalize_text(data["AbstractText"]),
                    "published_at": "",
                })

        except Exception as exc:
            logger.warning(f"DuckDuckGo search failed for '{query}': {exc}")
        return results

    def _sec_edgar_search(self, entity_name: str) -> List[Dict[str, Any]]:
        """Search SEC EDGAR for recent 8-K material event filings (always free)."""
        results = []
        try:
            from datetime import datetime, timedelta, timezone  # noqa: PLC0415
            start_date = (datetime.now(timezone.utc) - timedelta(days=settings.sec_edgar_lookback_days)).strftime("%Y-%m-%d")
            url = f"https://efts.sec.gov/LATEST/search-index?q=%22{quote_plus(entity_name)}%22&forms=8-K&dateRange=custom&startdt={start_date}"
            resp = requests.get(
                url,
                headers={"User-Agent": "MarketIntelSystem varad@example.com"},
                timeout=12,
            )
            resp.raise_for_status()
            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            for hit in hits[:5]:
                src = hit.get("_source", {})
                filing_date = src.get("file_date", "")
                form_type = src.get("form_type", "8-K")
                company = src.get("entity_name", entity_name)
                entity_id = src.get("entity_id", "")
                filing_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={entity_id}&type=8-K&dateb=&owner=include&count=10"
                results.append({
                    "source_name": "SEC EDGAR",
                    "source_type": "sec_edgar_8k",
                    "url": filing_url,
                    "title": f"{company} — {form_type} Material Event Filing ({filing_date})",
                    "content": normalize_text(
                        f"SEC {form_type} filing by {company} on {filing_date}. "
                        f"This is a material event disclosure. Review the full filing for details."
                    ),
                    "published_at": filing_date,
                })
        except Exception as exc:
            logger.warning(f"SEC EDGAR search failed for '{entity_name}': {exc}")
        return results

    def _reddit_search(self, entity_name: str) -> List[Dict[str, Any]]:
        """Search Reddit for recent mentions of the entity in financial subreddits."""
        results = []
        try:
            query = f"{entity_name} stock"
            url = REDDIT_SEARCH.format(query=quote_plus(query))
            resp = requests.get(
                url,
                headers={"User-Agent": "MarketIntelSystem/2.0 (research)"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            for post in posts[:3]:
                p = post.get("data", {})
                subreddit = p.get("subreddit_name_prefixed", "")
                # Only include finance-relevant subreddits
                if not any(fin_sub.lower() in subreddit.lower() for fin_sub in ["stock", "invest", "finance", "market", "wallstreet", "security"]):
                    continue
                title = p.get("title", "")
                selftext = normalize_text(p.get("selftext", "")[:1000])
                results.append({
                    "source_name": f"Reddit/{subreddit}",
                    "source_type": "reddit_social",
                    "url": f"https://reddit.com{p.get('permalink', '')}",
                    "title": title,
                    "content": normalize_text(f"{title}. {selftext}"),
                    "published_at": "",
                })
        except Exception as exc:
            logger.debug(f"Reddit search failed for '{entity_name}': {exc}")
        return results

    def _to_raw_sources(
        self,
        session: Session,
        items: List[Dict[str, Any]],
        entity_name: str,
    ) -> List[RawSource]:
        """Convert raw dicts to persisted RawSource records."""
        saved = []
        for item in items:
            if not item.get("content") or len(item["content"]) < 20:
                continue
            record = RawSource(
                id=new_id("dsrc"),
                source_name=item.get("source_name", "DeepSearch"),
                source_type=item.get("source_type", "deep_search"),
                url=item.get("url"),
                title=item.get("title"),
                content=item.get("content"),
                published_at=item.get("published_at", ""),
                fetched_at=iso_now(),
                credibility_score=None,   # CredibilityAgent will score these
                is_rejected=0,
                raw_metadata=json.dumps({"discovered_for_entity": entity_name}),
            )
            raw_source_repo.insert(session, record)
            saved.append(record)
        return saved
