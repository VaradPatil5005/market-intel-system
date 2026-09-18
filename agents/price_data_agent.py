"""
Price Data Agent — OHLCV & Technical Indicator Enrichment.

Fetches real market price series for tracked entities using yfinance (free,
no API key required). Computes key technical indicators used downstream by
ConfidenceScoringAgent and ForecastingAgent.

Technical indicators computed:
  - 7d / 30d price return (%)
  - 30d annualised volatility (std of daily log returns × √252)
  - RSI-14 (Relative Strength Index — overbought/oversold signal)
  - Bollinger Band squeeze detection (bandwidth compression)
  - Volume anomaly flag (today's volume > 2× 20-day average)

Entity → Ticker mapping:
  Reads from data/ticker_map.json. Entities not in the map are skipped.
  Built-in defaults: Nvidia→NVDA, Microsoft→MSFT, Google→GOOGL, etc.

Graceful degradation:
  - If yfinance not installed → logs and returns []
  - If ticker not found / delisted → skips entity, logs warning
  - If price_data_enabled=False → agent is not called at all (graph.py)
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Optional

from agents.base import BaseAgent
from database.models import Entity, PriceSnapshot
from database.session import Repository, Session
from utils.config import settings
from utils.helpers import iso_now, new_id
from utils.logging_setup import get_logger

logger = get_logger("price_data_agent")

price_repo = Repository(PriceSnapshot)

# Built-in ticker map fallback
DEFAULT_TICKER_MAP: Dict[str, str] = {
    "nvidia": "NVDA",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "openai": None,          # private company — no ticker
    "anthropic": None,       # private company — no ticker
    "meta": "META",
    "amazon": "AMZN",
    "apple": "AAPL",
    "tesla": "TSLA",
    "intel": "INTC",
    "amd": "AMD",
    "qualcomm": "QCOM",
    "salesforce": "CRM",
    "palantir": "PLTR",
}


def _load_ticker_map() -> Dict[str, str]:
    """Load ticker map from data/ticker_map.json, merging with built-in defaults."""
    merged = dict(DEFAULT_TICKER_MAP)
    path: Path = settings.ticker_map_path
    if path.exists():
        try:
            custom = json.loads(path.read_text(encoding="utf-8"))
            merged.update({k.lower(): v for k, v in custom.items()})
        except Exception as exc:
            logger.warning(f"Could not load ticker_map.json: {exc}")
    return merged


def _compute_rsi(closes: List[float], period: int = 14) -> Optional[float]:
    """Classic Wilder RSI calculation."""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def _bollinger_squeeze(closes: List[float], window: int = 20, num_std: float = 2.0) -> bool:
    """Detect Bollinger Band squeeze: bandwidth < 5% of middle band."""
    if len(closes) < window:
        return False
    recent = closes[-window:]
    mean = sum(recent) / len(recent)
    variance = sum((x - mean) ** 2 for x in recent) / len(recent)
    std = math.sqrt(variance)
    upper = mean + num_std * std
    lower = mean - num_std * std
    bandwidth = (upper - lower) / mean if mean != 0 else 0
    return bandwidth < 0.05   # less than 5% bandwidth = squeeze


class PriceDataAgent(BaseAgent):
    name = "price_data_agent"

    def __init__(self, metrics=None):
        super().__init__(metrics)
        self._ticker_map = _load_ticker_map()

    def run(
        self,
        session: Session,
        run_id: str,
        entities: List[Entity],
    ) -> List[PriceSnapshot]:
        """Fetch OHLCV + technical indicators for all entities with known tickers."""
        if not settings.price_data_enabled:
            return []

        # Check if yfinance is available
        try:
            import yfinance as yf  # noqa: PLC0415
        except ImportError:
            logger.info("yfinance not installed — price data enrichment skipped.")
            return []

        with self.run_tracked("price_enrich"):
            snapshots: List[PriceSnapshot] = []
            lookback = settings.price_data_lookback_days

            for entity in entities:
                ticker_sym = self._resolve_ticker(entity.canonical_name)
                if not ticker_sym:
                    continue

                snap = self._fetch_snapshot(yf, session, run_id, entity, ticker_sym, lookback)
                if snap:
                    price_repo.insert(session, snap)
                    snapshots.append(snap)

            session.flush()
            self.audit(
                session,
                step="price_enrich",
                action="fetched_price_snapshots",
                output_summary={"snapshots_written": len(snapshots)},
            )
            logger.info(f"PriceDataAgent: {len(snapshots)} price snapshots fetched.")
            return snapshots

    def get_snapshot(self, session: Session, run_id: str, entity_name: str) -> Optional[PriceSnapshot]:
        """Retrieve price snapshot for a specific entity in this run."""
        snaps = price_repo.filter_by(session, run_id=run_id)
        for s in snaps:
            if s.entity_name.lower() == entity_name.lower():
                return s
        return None

    # ------------------------------------------------------------------
    def _resolve_ticker(self, canonical_name: str) -> Optional[str]:
        return self._ticker_map.get(canonical_name.lower())

    def _fetch_snapshot(
        self,
        yf,
        session: Session,
        run_id: str,
        entity: Entity,
        ticker: str,
        lookback: int,
    ) -> Optional[PriceSnapshot]:
        try:
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period=f"{lookback}d", auto_adjust=True)
            if hist.empty or len(hist) < 5:
                logger.warning(f"PriceDataAgent: no/insufficient data for {ticker}")
                return None

            closes = hist["Close"].tolist()
            volumes = hist["Volume"].tolist()
            current_price = closes[-1]

            # Returns
            ret_7d = ((closes[-1] / closes[max(-8, -len(closes))]) - 1) * 100 if len(closes) >= 7 else None
            ret_30d = ((closes[-1] / closes[0]) - 1) * 100

            # Volatility (annualised)
            log_returns = [
                math.log(closes[i] / closes[i - 1])
                for i in range(1, len(closes))
                if closes[i - 1] > 0
            ]
            vol_30d = None
            if log_returns:
                mean_r = sum(log_returns) / len(log_returns)
                variance = sum((r - mean_r) ** 2 for r in log_returns) / len(log_returns)
                vol_30d = round(math.sqrt(variance) * math.sqrt(252) * 100, 2)

            # RSI
            rsi = _compute_rsi(closes, settings.price_rsi_period)

            # Bollinger squeeze
            bb_squeeze = _bollinger_squeeze(
                closes,
                settings.bollinger_band_window,
                settings.bollinger_band_std,
            )

            # Volume anomaly
            vol_anomaly = False
            if len(volumes) >= 20:
                avg_vol = sum(volumes[-20:-1]) / 19
                vol_anomaly = volumes[-1] > 2 * avg_vol if avg_vol > 0 else False

            return PriceSnapshot(
                id=new_id("psnap"),
                run_id=run_id,
                entity_id=entity.id,
                entity_name=entity.canonical_name,
                ticker=ticker,
                current_price=round(current_price, 4),
                price_7d_return_pct=round(ret_7d, 2) if ret_7d is not None else None,
                price_30d_return_pct=round(ret_30d, 2),
                volatility_30d=vol_30d,
                rsi_14=rsi,
                bb_squeeze=int(bb_squeeze),
                volume_anomaly=int(vol_anomaly),
                data_source="yfinance",
                fetched_at=iso_now(),
                created_at=iso_now(),
            )

        except Exception as exc:
            logger.warning(f"PriceDataAgent: failed to fetch {ticker}: {exc}")
            return None
