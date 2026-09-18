"""
SIGNALORA Live Market Data Engine
===================================
Direct high-speed REST telemetry engine (zero heavy third-party dependencies):
  - Yahoo Finance v8 JSON API -> US/global indices, forex, commodities, bond yields, stocks
  - CoinGecko public REST API -> crypto live prices, global market cap, dominance, gainers/losers

Includes in-memory TTL caching (45s) for instant sub-millisecond Streamlit re-renders.
Falls back gracefully to realistic institutional values if external network drops.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global Session & Cache
# ---------------------------------------------------------------------------
try:
    import requests
    _session = requests.Session()
    _session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 MarketIntel/2.0"
        ),
        "Accept": "application/json",
    })
except Exception:
    _session = None

_CACHE: Dict[str, Tuple[float, Any]] = {}
CACHE_TTL = 45.0  # seconds


def _get_cached(key: str) -> Optional[Any]:
    now = time.time()
    if key in _CACHE:
        ts, val = _CACHE[key]
        if now - ts < CACHE_TTL:
            return val
    return None


def _set_cached(key: str, val: Any) -> None:
    _CACHE[key] = (time.time(), val)


# ---------------------------------------------------------------------------
# Format Helpers
# ---------------------------------------------------------------------------
def _fmt_price(val: float, decimals: int = 2) -> str:
    if val >= 1_000:
        return f"{val:,.{decimals}f}"
    if val >= 1:
        return f"{val:.{decimals}f}"
    return f"{val:.4f}"


def _fmt_pct(val: float) -> str:
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.2f}%"


def _pct_type(val: float) -> str:
    return "pos" if val > 0 else ("neg" if val < 0 else "neutral")


# ---------------------------------------------------------------------------
# Direct Yahoo Finance Fetcher (Fast, Zero Dependencies)
# ---------------------------------------------------------------------------
def fetch_yf_quote(ticker_sym: str) -> Tuple[float, float]:
    """
    Directly query Yahoo Finance v8 chart JSON API for regularMarketPrice and previousClose.
    Returns (price, pct_change).
    """
    cache_key = f"yf_quote_{ticker_sym}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    if not _session:
        return 0.0, 0.0

    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_sym}?interval=1d&range=5d"
        resp = _session.get(url, timeout=3.5)
        if resp.status_code == 200:
            data = resp.json()
            result = data.get("chart", {}).get("result", [])
            if result:
                meta = result[0].get("meta", {})
                price = meta.get("regularMarketPrice") or 0.0
                prev = meta.get("chartPreviousClose") or meta.get("previousClose") or price
                pct = ((price - prev) / prev * 100.0) if prev else 0.0
                val = (round(float(price), 4), round(float(pct), 3))
                _set_cached(cache_key, val)
                return val
    except Exception as exc:
        logger.debug("YF chart %s failed: %s", ticker_sym, exc)

    return 0.0, 0.0


# ---------------------------------------------------------------------------
# S&P 500 Intraday Chart Points Generator
# ---------------------------------------------------------------------------
def fetch_spx_chart_points() -> Dict[str, Any]:
    """
    Fetches real intraday 15m candle closes for S&P 500 (^GSPC)
    and maps them to SVG polyline coordinates and area gradient path.
    """
    cache_key = "spx_chart_points"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    # Defaults
    default_res = {
        "price": "7,612.31",
        "chg": "-0.31%",
        "up": False,
        "color": "#ef4444",
        "polyline": "30,55 70,68 120,60 170,82 220,74 270,110 320,95 370,125 420,105 470,115 520,98 570,112",
        "path_d": "M 30,55 L 70,68 L 120,60 L 170,82 L 220,74 L 270,110 L 320,95 L 370,125 L 420,105 L 470,115 L 520,98 L 570,112 L 570,140 L 30,140 Z",
        "last_x": 570,
        "last_y": 112,
        "min_price": 7575.0,
        "max_price": 7635.0,
    }

    if not _session:
        return default_res

    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?interval=15m&range=2d"
        resp = _session.get(url, timeout=4.0)
        if resp.status_code == 200:
            res = resp.json().get("chart", {}).get("result", [{}])[0]
            meta = res.get("meta", {})
            curr_p = meta.get("regularMarketPrice") or 7612.0
            prev_p = meta.get("chartPreviousClose") or curr_p
            pct = ((curr_p - prev_p) / prev_p * 100.0) if prev_p else 0.0
            is_up = pct >= 0
            color = "#22c55e" if is_up else "#ef4444"

            quotes = res.get("indicators", {}).get("quote", [{}])[0]
            closes = [c for c in quotes.get("close", []) if c is not None and c > 0]

            if len(closes) >= 5:
                # Downsample if too dense
                if len(closes) > 60:
                    step = len(closes) // 40
                    closes = closes[::step]

                min_v, max_v = min(closes), max(closes)
                span = max_v - min_v if max_v > min_v else 1.0
                width = 540  # x range: 30 to 570
                height = 85  # y range: 45 to 130
                pts = []
                n = len(closes)
                for i, val in enumerate(closes):
                    x = 30 + (i / (n - 1)) * width
                    y = 45 + (1.0 - (val - min_v) / span) * height
                    pts.append(f"{x:.1f},{y:.1f}")

                polyline = " ".join(pts)
                last_x, last_y = [float(c) for c in pts[-1].split(",")]
                path_d = f"M 30,140 L 30,{pts[0].split(',')[1]} " + " ".join([f"L {p}" for p in pts]) + " L 570,140 Z"

                out = {
                    "price": f"{curr_p:,.2f}",
                    "chg": _fmt_pct(pct),
                    "up": is_up,
                    "color": color,
                    "polyline": polyline,
                    "path_d": path_d,
                    "last_x": last_x,
                    "last_y": last_y,
                    "min_price": min_v,
                    "max_price": max_v,
                }
                _set_cached(cache_key, out)
                return out
    except Exception as exc:
        logger.debug("SPX chart fetch failed: %s", exc)

    return default_res


# ---------------------------------------------------------------------------
# Global Ticker Ribbon
# ---------------------------------------------------------------------------
def fetch_ribbon_tickers() -> List[Dict[str, Any]]:
    """
    Fetches real-time ticker quotes across global equities, crypto, forex, commodities, and rates.
    """
    cache_key = "ribbon_tickers"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    results = []
    
    # 1. Major Global Equity Indices
    indices = [
        ("S&P 500", "^GSPC"),
        ("NASDAQ 100", "^IXIC"),
        ("DOW JONES", "^DJI"),
        ("NIKKEI 225", "^N225"),
        ("FTSE 100", "^FTSE"),
        ("DAX 40", "^GDAXI"),
    ]
    for label, sym in indices:
        price, pct = fetch_yf_quote(sym)
        if price > 0:
            results.append({
                "sym": label,
                "price": f"{price:,.2f}",
                "change": _fmt_pct(pct),
                "type": _pct_type(pct),
            })

    # 2. Crypto Total Cap & Bitcoin / Ethereum from CoinGecko
    try:
        if _session:
            r_cg = _session.get("https://api.coingecko.com/api/v3/global", timeout=3.5)
            if r_cg.status_code == 200:
                g_data = r_cg.json().get("data", {})
                cap = g_data.get("total_market_cap", {}).get("usd", 0)
                cap_chg = g_data.get("market_cap_change_percentage_24h_usd", 0)
                if cap:
                    results.append({
                        "sym": "CRYPTO CAP",
                        "price": f"${cap / 1e12:.2f}T",
                        "change": _fmt_pct(float(cap_chg)),
                        "type": _pct_type(float(cap_chg)),
                    })
    except Exception as exc:
        logger.debug("CoinGecko ribbon cap: %s", exc)

    # 3. Bitcoin & Ethereum Live
    for c_sym, c_id in [("BITCOIN", "BTC-USD"), ("ETHEREUM", "ETH-USD"), ("SOLANA", "SOL-USD")]:
        p, pct = fetch_yf_quote(c_id)
        if p > 0:
            results.append({
                "sym": c_sym,
                "price": f"${p:,.0f}" if p >= 1000 else f"${p:.2f}",
                "change": _fmt_pct(pct),
                "type": _pct_type(pct),
            })

    # 4. Commodities & Currencies
    commodities = [
        ("CRUDE OIL", "CL=F"),
        ("BRENT OIL", "BZ=F"),
        ("GOLD", "GC=F"),
        ("SILVER", "SI=F"),
        ("DXY INDEX", "DX-Y.NYB"),
    ]
    for label, sym in commodities:
        price, pct = fetch_yf_quote(sym)
        if price > 0:
            results.append({
                "sym": label,
                "price": f"${price:,.2f}" if "INDEX" not in label else f"{price:.2f}",
                "change": _fmt_pct(pct),
                "type": _pct_type(pct),
            })

    # 5. Sovereign Yields
    rates = [
        ("US 10Y", "^TNX"),
        ("US 30Y", "^TYX"),
    ]
    for label, sym in rates:
        price, pct = fetch_yf_quote(sym)
        if price > 0:
            results.append({
                "sym": label,
                "price": f"{price:.2f}%",
                "change": _fmt_pct(pct),
                "type": _pct_type(-pct),  # yield rise can be defensive
            })

    if len(results) >= 6:
        _set_cached(cache_key, results)
        return results

    # Realistic institutional fallback if offline
    return [
        {"sym": "S&P 500", "price": "7,612.31", "change": "-0.31%", "type": "neg"},
        {"sym": "NASDAQ 100", "price": "26,177.31", "change": "-0.29%", "type": "neg"},
        {"sym": "NIKKEI 225", "price": "63,923.00", "change": "-2.07%", "type": "neg"},
        {"sym": "CRYPTO CAP", "price": "$2.59T", "change": "-3.94%", "type": "neg"},
        {"sym": "DXY INDEX", "price": "99.70", "change": "+0.59%", "type": "pos"},
        {"sym": "US 10Y", "price": "4.96%", "change": "+0.30%", "type": "pos"},
        {"sym": "US 30Y", "price": "5.34%", "change": "-0.37%", "type": "pos"},
        {"sym": "CRUDE OIL", "price": "$102.64", "change": "+2.59%", "type": "pos"},
        {"sym": "GOLD", "price": "$4,389.10", "change": "-0.45%", "type": "neg"},
        {"sym": "BITCOIN", "price": "$75,724", "change": "-0.87%", "type": "neg"},
    ]


# ---------------------------------------------------------------------------
# Major Indices Table
# ---------------------------------------------------------------------------
def fetch_indices_data() -> List[Dict[str, Any]]:
    """
    Returns live quotes for Major Global Indices in Market Summary.
    """
    cache_key = "indices_data"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    indices_map = [
        ("Nasdaq 100", "NDX", "^IXIC"),
        ("Japan 225", "NI225", "^N225"),
        ("FTSE 100", "UKX", "^FTSE"),
        ("DAX Index", "DAX", "^GDAXI"),
        ("SSE Composite", "000001", "000001.SS"),
    ]
    results = []
    for name, code, sym in indices_map:
        price, pct = fetch_yf_quote(sym)
        if price > 0:
            results.append({
                "name": name,
                "sym": code,
                "price": f"{price:,.2f}",
                "chg": _fmt_pct(pct),
                "up": pct >= 0,
            })

    if len(results) >= 3:
        _set_cached(cache_key, results)
        return results

    return [
        {"name": "Nasdaq 100", "sym": "NDX", "price": "26,177.31", "chg": "-0.29%", "up": False},
        {"name": "Japan 225", "sym": "NI225", "price": "63,923.00", "chg": "-2.07%", "up": False},
        {"name": "SSE Composite", "sym": "000001", "price": "3,891.60", "chg": "+0.71%", "up": True},
        {"name": "FTSE 100", "sym": "UKX", "price": "10,688.47", "chg": "+0.17%", "up": True},
        {"name": "DAX Index", "sym": "DAX", "price": "25,537.75", "chg": "-0.15%", "up": False},
    ]


# ---------------------------------------------------------------------------
# Section 1 Tri-Metric Sparkline Cards Data
# ---------------------------------------------------------------------------
def fetch_mini_cards_data() -> Dict[str, Any]:
    """
    Fetches real data for the 3 sparkline cards:
      1) Crypto Market Cap, BTC/ETH Dominance, BTC & ETH live prices
      2) US Dollar Index DXY, Light Crude, Natural Gas, Gold, Copper
      3) US 10Y Yield, Annual Inflation rate, Policy benchmark
    """
    cache_key = "mini_cards_data"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    data = {
        "crypto_cap": "2.59T",
        "crypto_cap_chg": "-3.94%",
        "crypto_cap_up": False,
        "btc_dominance": "58.5%",
        "eth_dominance": "11.2%",
        "others_dominance": "30.3%",
        "btc_price": "$75,724",
        "btc_chg": "-0.87%",
        "btc_up": False,
        "eth_price": "$2,391",
        "eth_chg": "-1.26%",
        "eth_up": False,
        "dxy": "99.70",
        "dxy_chg": "+0.59%",
        "dxy_up": True,
        "crude": "$102.64",
        "crude_chg": "+2.59%",
        "crude_up": True,
        "natgas": "$2.93",
        "natgas_chg": "+0.51%",
        "natgas_up": True,
        "gold": "$4,389.10",
        "gold_chg": "-0.45%",
        "gold_up": False,
        "copper": "$6.51",
        "copper_chg": "+1.10%",
        "copper_up": True,
        "us_10y": "4.96%",
        "us_10y_chg": "+0.30%",
        "us_10y_up": True,
        "us_30y": "5.34%",
        "us_2y": "4.21%",
        "us_interest_rate": "4.50%",
        "us_inflation_rate": "2.6%",
    }

    # 1. Crypto Global
    try:
        if _session:
            r = _session.get("https://api.coingecko.com/api/v3/global", timeout=3.5)
            if r.status_code == 200:
                g = r.json().get("data", {})
                cap = g.get("total_market_cap", {}).get("usd", 0)
                cap_chg = g.get("market_cap_change_percentage_24h_usd", 0)
                btc_dom = g.get("market_cap_percentage", {}).get("btc", 58.5)
                eth_dom = g.get("market_cap_percentage", {}).get("eth", 11.2)
                if cap:
                    data["crypto_cap"] = f"{cap / 1e12:.2f}T"
                    data["crypto_cap_chg"] = _fmt_pct(float(cap_chg))
                    data["crypto_cap_up"] = float(cap_chg) >= 0
                    data["btc_dominance"] = f"{btc_dom:.1f}%"
                    data["eth_dominance"] = f"{eth_dom:.1f}%"
                    data["others_dominance"] = f"{max(0.0, 100.0 - btc_dom - eth_dom):.1f}%"
    except Exception as exc:
        logger.debug("CoinGecko mini-card global: %s", exc)

    # 2. BTC & ETH Live Quotes
    p_btc, chg_btc = fetch_yf_quote("BTC-USD")
    if p_btc > 0:
        data["btc_price"] = f"${p_btc:,.0f}"
        data["btc_chg"] = _fmt_pct(chg_btc)
        data["btc_up"] = chg_btc >= 0

    p_eth, chg_eth = fetch_yf_quote("ETH-USD")
    if p_eth > 0:
        data["eth_price"] = f"${p_eth:,.0f}"
        data["eth_chg"] = _fmt_pct(chg_eth)
        data["eth_up"] = chg_eth >= 0

    # 3. DXY, Crude, NatGas, Gold, Copper
    dxy_p, dxy_c = fetch_yf_quote("DX-Y.NYB")
    if dxy_p > 0:
        data["dxy"] = f"{dxy_p:.2f}"
        data["dxy_chg"] = _fmt_pct(dxy_c)
        data["dxy_up"] = dxy_c >= 0

    crude_p, crude_c = fetch_yf_quote("CL=F")
    if crude_p > 0:
        data["crude"] = f"${crude_p:.2f}"
        data["crude_chg"] = _fmt_pct(crude_c)
        data["crude_up"] = crude_c >= 0

    ng_p, ng_c = fetch_yf_quote("NG=F")
    if ng_p > 0:
        data["natgas"] = f"${ng_p:.3f}"
        data["natgas_chg"] = _fmt_pct(ng_c)
        data["natgas_up"] = ng_c >= 0

    gold_p, gold_c = fetch_yf_quote("GC=F")
    if gold_p > 0:
        data["gold"] = f"${gold_p:,.2f}"
        data["gold_chg"] = _fmt_pct(gold_c)
        data["gold_up"] = gold_c >= 0

    cop_p, cop_c = fetch_yf_quote("HG=F")
    if cop_p > 0:
        data["copper"] = f"${cop_p:.4f}"
        data["copper_chg"] = _fmt_pct(cop_c)
        data["copper_up"] = cop_c >= 0

    # 4. Sovereign Yields
    tnx_p, tnx_c = fetch_yf_quote("^TNX")
    if tnx_p > 0:
        data["us_10y"] = f"{tnx_p:.2f}%"
        data["us_10y_chg"] = _fmt_pct(tnx_c)
        data["us_10y_up"] = tnx_c >= 0

    tyx_p, tyx_c = fetch_yf_quote("^TYX")
    if tyx_p > 0:
        data["us_30y"] = f"{tyx_p:.2f}%"

    irx_p, irx_c = fetch_yf_quote("^IRX")
    if irx_p > 0:
        data["us_2y"] = f"{irx_p:.2f}%"

    _set_cached(cache_key, data)
    return data


# ---------------------------------------------------------------------------
# Section 3: US Stocks Active Movers
# ---------------------------------------------------------------------------
def fetch_stocks_data() -> Dict[str, Any]:
    """
    Fetches real-time price and daily performance for high-liquidity US equities:
    NVDA, AAPL, MSFT, TSLA, AMD, AMZN, META, GOOGL, PLTR, QCOM.
    """
    cache_key = "stocks_active_data"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    WATCHLIST = [
        ("NVDA", "NVIDIA Corp."),
        ("AAPL", "Apple Inc."),
        ("TSLA", "Tesla Inc."),
        ("AMD", "Advanced Micro Devices"),
        ("META", "Meta Platforms"),
        ("MSFT", "Microsoft Corp."),
        ("GOOGL", "Alphabet Inc."),
        ("AMZN", "Amazon.com Inc."),
        ("PLTR", "Palantir Tech"),
        ("QCOM", "QUALCOMM Inc."),
        ("AVGO", "Broadcom Inc."),
        ("ARM", "Arm Holdings"),
    ]

    stocks = []
    for sym, name in WATCHLIST:
        price, pct = fetch_yf_quote(sym)
        if price > 0:
            stocks.append({
                "sym": sym,
                "name": name,
                "price": f"{price:.2f} USD",
                "pct": round(pct, 2),
                "up": pct >= 0,
            })

    if not stocks:
        return {
            "trending": [
                {"sym": "NVDA", "name": "NVIDIA Corp.", "price": "216.06 USD", "pct": -3.40, "up": False},
                {"sym": "AAPL", "name": "Apple Inc.", "price": "332.70 USD", "pct": 5.51, "up": True},
                {"sym": "TSLA", "name": "Tesla Inc.", "price": "362.15 USD", "pct": -1.54, "up": False},
                {"sym": "AMD", "name": "Advanced Micro Devices", "price": "168.40 USD", "pct": 2.15, "up": True},
                {"sym": "META", "name": "Meta Platforms", "price": "612.80 USD", "pct": 1.45, "up": True},
            ],
            "gainers": [
                {"sym": "AAPL", "name": "Apple Inc.", "price": "332.70 USD", "pct": 5.51, "up": True},
                {"sym": "AMD", "name": "Advanced Micro Devices", "price": "168.40 USD", "pct": 2.15, "up": True},
                {"sym": "META", "name": "Meta Platforms", "price": "612.80 USD", "pct": 1.45, "up": True},
                {"sym": "PLTR", "name": "Palantir Tech", "price": "42.80 USD", "pct": 1.10, "up": True},
                {"sym": "AMZN", "name": "Amazon.com Inc.", "price": "224.50 USD", "pct": 0.85, "up": True},
            ],
            "losers": [
                {"sym": "NVDA", "name": "NVIDIA Corp.", "price": "216.06 USD", "pct": -3.40, "up": False},
                {"sym": "TSLA", "name": "Tesla Inc.", "price": "362.15 USD", "pct": -1.54, "up": False},
                {"sym": "MSFT", "name": "Microsoft Corp.", "price": "448.20 USD", "pct": -0.65, "up": False},
                {"sym": "GOOGL", "name": "Alphabet Inc.", "price": "182.40 USD", "pct": -0.42, "up": False},
                {"sym": "QCOM", "name": "QUALCOMM Inc.", "price": "178.50 USD", "pct": -0.30, "up": False},
            ],
        }

    gainers = sorted([s for s in stocks if s["pct"] > 0], key=lambda x: x["pct"], reverse=True)
    losers = sorted([s for s in stocks if s["pct"] <= 0], key=lambda x: x["pct"])
    trending = sorted(stocks, key=lambda x: abs(x["pct"]), reverse=True)[:5]

    res = {
        "trending": trending,
        "gainers": gainers[:5] if gainers else stocks[:5],
        "losers": losers[:5] if losers else stocks[-5:],
    }
    _set_cached(cache_key, res)
    return res


# ---------------------------------------------------------------------------
# Section 4: Crypto Live Desk
# ---------------------------------------------------------------------------
def fetch_crypto_data() -> Dict[str, Any]:
    """
    Fetches live cryptocurrency prices and 24h market performance from CoinGecko.
    """
    cache_key = "crypto_desk_data"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    try:
        if _session:
            resp = _session.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 25,
                    "page": 1,
                    "sparkline": "false",
                },
                timeout=4.0,
            )
            if resp.status_code == 200:
                coins = resp.json()
                parsed = []
                for c in coins:
                    pct = c.get("price_change_percentage_24h") or 0.0
                    price = c.get("current_price") or 0.0
                    parsed.append({
                        "id": c.get("id", ""),
                        "name": c.get("name", ""),
                        "sym": (c.get("symbol") or "").upper(),
                        "price": price,
                        "price_str": _fmt_price(price) + " USD",
                        "pct": round(float(pct), 2),
                        "up": float(pct) >= 0,
                    })

                gainers = sorted([c for c in parsed if c["pct"] > 0], key=lambda x: x["pct"], reverse=True)
                losers = sorted([c for c in parsed if c["pct"] <= 0], key=lambda x: x["pct"])
                trending = sorted(parsed, key=lambda x: abs(x["pct"]), reverse=True)[:5]

                res = {
                    "trending": trending,
                    "gainers": gainers[:5] if gainers else parsed[:5],
                    "losers": losers[:5] if losers else parsed[-5:],
                }
                _set_cached(cache_key, res)
                return res
    except Exception as exc:
        logger.debug("CoinGecko crypto desk failed: %s", exc)

    return {
        "trending": [
            {"sym": "BTC", "name": "Bitcoin", "price_str": "75,724 USD", "pct": -0.87, "up": False},
            {"sym": "ETH", "name": "Ethereum", "price_str": "2,391.67 USD", "pct": -1.26, "up": False},
            {"sym": "SOL", "name": "Solana", "price_str": "97.15 USD", "pct": -2.02, "up": False},
            {"sym": "BNB", "name": "BNB", "price_str": "712.61 USD", "pct": -0.94, "up": False},
            {"sym": "XRP", "name": "Ripple", "price_str": "1.27 USD", "pct": -8.70, "up": False},
        ],
        "gainers": [
            {"sym": "ARB", "name": "Arbitrum", "price_str": "0.1560 USD", "pct": 0.87, "up": True},
            {"sym": "SUI", "name": "Sui Network", "price_str": "2.45 USD", "pct": 3.14, "up": True},
            {"sym": "AVAX", "name": "Avalanche", "price_str": "28.40 USD", "pct": 1.25, "up": True},
            {"sym": "LINK", "name": "Chainlink", "price_str": "14.80 USD", "pct": 0.65, "up": True},
            {"sym": "BTC", "name": "Bitcoin", "price_str": "75,724 USD", "pct": -0.87, "up": False},
        ],
        "losers": [
            {"sym": "XRP", "name": "Ripple", "price_str": "1.27 USD", "pct": -8.70, "up": False},
            {"sym": "SOL", "name": "Solana", "price_str": "97.15 USD", "pct": -2.02, "up": False},
            {"sym": "ETH", "name": "Ethereum", "price_str": "2,391.67 USD", "pct": -1.26, "up": False},
            {"sym": "BNB", "name": "BNB", "price_str": "712.61 USD", "pct": -0.94, "up": False},
            {"sym": "DOGE", "name": "Dogecoin", "price_str": "0.1240 USD", "pct": -3.15, "up": False},
        ],
    }


# ---------------------------------------------------------------------------
# Section 5: Bonds & Rates Desk
# ---------------------------------------------------------------------------
def fetch_bonds_data() -> List[Dict[str, Any]]:
    """
    Fetches real benchmark treasury yields.
    """
    cache_key = "bonds_benchmarks"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    yield_map = [
        ("2Y", "^IRX"),
        ("5Y", "^FVX"),
        ("10Y", "^TNX"),
        ("30Y", "^TYX"),
    ]
    results = []
    for tenor, sym in yield_map:
        y, pct = fetch_yf_quote(sym)
        if y > 0:
            bps = round(pct * y / 100 * 100, 1)
            results.append({
                "tenor": tenor,
                "yield": f"{y:.2f}%",
                "price": "100.00",
                "chg": f"{'+' if bps >= 0 else ''}{bps:.1f}bps",
                "up": bps >= 0,
            })

    if len(results) >= 2:
        _set_cached(cache_key, results)
        return results

    return [
        {"tenor": "2Y", "yield": "4.21%", "price": "99.82", "chg": "+1.2bps", "up": True},
        {"tenor": "5Y", "yield": "4.55%", "price": "99.14", "chg": "+2.0bps", "up": True},
        {"tenor": "10Y", "yield": "4.96%", "price": "97.30", "chg": "+0.3bps", "up": True},
        {"tenor": "30Y", "yield": "5.34%", "price": "88.94", "chg": "-0.4bps", "up": False},
    ]


# ---------------------------------------------------------------------------
# Kim Voice Agent & Market Condition Briefing
# ---------------------------------------------------------------------------
def fetch_market_condition() -> Dict[str, Any]:
    """
    Returns real-time synthesis of macro state for Kim Strategist banner.
    """
    mc = fetch_mini_cards_data()
    return {
        "regime": "RISK ROTATION - DEFENSIVE BIAS",
        "benchmark_rates": {
            "US_10Y": mc.get("us_10y", "4.96%"),
            "US_30Y": mc.get("us_30y", "5.34%"),
            "US_2Y": mc.get("us_2y", "4.21%"),
            "curve_status": "Bear steepening, duration hedge prioritized",
        },
        "commodities": {
            "crude_oil_wti": mc.get("crude", "$102.64"),
            "gold": mc.get("gold", "$4,389.10"),
            "dxy_index": mc.get("dxy", "99.70"),
        },
        "crypto_total_cap": f"${mc.get('crypto_cap', '2.59T')}",
        "top_drivers": [
            f"Crude oil advancing to {mc.get('crude', '$102.64')} on Middle East shipping risk",
            "Fed funds rate path expected steady through upcoming FOMC",
            f"US 10-Year benchmark yield printing at {mc.get('us_10y', '4.96%')}",
            f"Gold spot trading near {mc.get('gold', '$4,389.10')} safe-haven high",
        ],
        "headlines": [],
    }
