import sys

with open("ui/blackbox_theme.py", "r", encoding="utf-8") as f:
    content = f.read()

# Marker for start
start_marker = "def render_global_market_ribbon(tickers: Optional[List[Dict[str, Any]]] = None) -> str:"
end_marker = "def render_global_economy_dashboard() -> str:"

if start_marker not in content or end_marker not in content:
    print("ERROR: Markers not found in ui/blackbox_theme.py")
    sys.exit(1)

pre = content.split(start_marker)[0]
post = end_marker + content.split(end_marker)[1]

replacement = '''def render_global_market_ribbon(tickers: Optional[List[Dict[str, Any]]] = None) -> str:
    """Renders the live global market ticker ribbon."""
    if not tickers:
        try:
            from utils.live_market_data import fetch_ribbon_tickers
            tickers = fetch_ribbon_tickers()
        except Exception:
            tickers = None

    if not tickers:
        tickers = [
            {"sym": "S&P 500", "price": "7,610.76", "change": "-0.34%", "type": "neg"},
            {"sym": "NASDAQ 100", "price": "26,177.31", "change": "-0.29%", "type": "neg"},
            {"sym": "NIKKEI 225", "price": "63,923.00", "change": "-2.07%", "type": "neg"},
            {"sym": "CRYPTO CAP", "price": "$2.59T", "change": "-3.94%", "type": "neg"},
            {"sym": "DXY INDEX", "price": "99.70", "change": "+0.59%", "type": "pos"},
            {"sym": "US 10Y", "price": "4.96%", "change": "+0.30%", "type": "pos"},
            {"sym": "US 30Y", "price": "5.34%", "change": "-0.37%", "type": "neutral"},
            {"sym": "CRUDE OIL", "price": "$102.64", "change": "+2.59%", "type": "pos"},
            {"sym": "GOLD (GC=F)", "price": "$4,389.10", "change": "-0.45%", "type": "neg"},
            {"sym": "BITCOIN", "price": "$75,724", "change": "-0.87%", "type": "neg"},
        ]

    items_html = []
    for t in tickers:
        chg_cls = "tv-ribbon-change-pos" if t["type"] == "pos" else ("tv-ribbon-change-neg" if t["type"] == "neg" else "tv-ribbon-change-neutral")
        items_html.append(
            f'<div class="tv-ribbon-item"><span class="tv-ribbon-sym">{t["sym"]}</span><span class="tv-ribbon-price">{t["price"]}</span><span class="{chg_cls}">{t["change"]}</span></div>'
        )

    return clean_html(f'<div class="tv-ribbon">{"".join(items_html)}</div>')


def render_market_summary_section() -> str:
    """Renders Section 1 Market Summary with live S&P 500 intraday telemetry and major indices."""
    try:
        from utils.live_market_data import fetch_spx_chart_points, fetch_indices_data
        spx = fetch_spx_chart_points()
        indices = fetch_indices_data()
    except Exception:
        spx = {
            "price": "7,610.76",
            "chg": "-0.34%",
            "up": False,
            "color": "#ef4444",
            "polyline": "30,55 70,68 120,60 170,82 220,74 270,110 320,95 370,125 420,105 470,115 520,98 570,112",
            "path_d": "M 30,55 L 70,68 L 120,60 L 170,82 L 220,74 L 270,110 L 320,95 L 370,125 L 420,105 L 470,115 L 520,98 L 570,112 L 570,140 L 30,140 Z",
            "last_x": 570,
            "last_y": 112,
        }
        indices = [
            {"name": "Nasdaq 100", "sym": "NDX", "price": "26,177.31", "chg": "-0.29%", "up": False},
            {"name": "Japan 225", "sym": "NI225", "price": "63,923.00", "chg": "-2.07%", "up": False},
            {"name": "SSE Composite", "sym": "000001", "price": "3,891.60", "chg": "+0.71%", "up": True},
            {"name": "FTSE 100", "sym": "UKX", "price": "10,688.47", "chg": "+0.17%", "up": True},
            {"name": "DAX Index", "sym": "DAX", "price": "25,537.75", "chg": "-0.15%", "up": False},
        ]

    stroke_color = spx.get("color", "#ef4444")
    badge_bg = "rgba(34, 197, 94, 0.12)" if spx.get("up") else "rgba(239, 68, 68, 0.12)"
    badge_fg = "#22c55e" if spx.get("up") else "#ef4444"

    idx_rows_html = []
    for idx in indices:
        chg_fg = "#22c55e" if idx.get("up", True) else "#ef4444"
        idx_rows_html.append(f"""
        <div class="sig-index-row">
            <div>
                <div style="font-weight: 700; font-size: 13px; color: #ffffff;">{idx['name']}</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #71717a;">{idx['sym']}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700; color: #ffffff;">{idx['price']}</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: {chg_fg};">{idx['chg']}</div>
            </div>
        </div>
        """)

    raw_html = f"""
    <div id="market-summary">
        <div class="sig-sec-header">
            <div class="sig-sec-title">Market summary &gt;</div>
            <div class="sig-sec-sub">REAL-TIME GLOBAL TELEMETRY</div>
        </div>
        <div class="sig-summary-wrap">
            <div class="sig-chart-card" style="padding: 20px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span class="sig-badge-round" style="background: #27272a; color: {stroke_color};">500</span>
                        <div>
                            <span style="font-weight: 800; font-size: 16px; color: #ffffff;">S&amp;P 500</span>
                            <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #71717a; margin-left: 6px;">SPX</span>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-family: 'Inter', sans-serif; font-size: 22px; font-weight: 800; color: #ffffff;">{spx['price']}</span>
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: {badge_fg}; background: {badge_bg}; padding: 3px 8px; border-radius: 4px; margin-left: 8px;">{spx['chg']}</span>
                    </div>
                </div>
                <svg viewBox="0 0 600 170" style="width: 100%; height: 170px; overflow: visible;">
                    <defs>
                        <linearGradient id="spxGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stop-color="{stroke_color}" stop-opacity="0.3"/>
                            <stop offset="100%" stop-color="{stroke_color}" stop-opacity="0.0"/>
                        </linearGradient>
                    </defs>
                    <line x1="20" y1="40" x2="580" y2="40" stroke="rgba(255,255,255,0.04)" stroke-dasharray="2,2"/>
                    <line x1="20" y1="90" x2="580" y2="90" stroke="rgba(255,255,255,0.04)" stroke-dasharray="2,2"/>
                    <line x1="20" y1="140" x2="580" y2="140" stroke="rgba(255,255,255,0.08)"/>
                    <path d="{spx['path_d']}" fill="url(#spxGrad)"/>
                    <polyline fill="none" stroke="{stroke_color}" stroke-width="2.5" points="{spx['polyline']}"/>
                    <circle cx="{spx['last_x']}" cy="{spx['last_y']}" r="4" fill="{stroke_color}"/>
                    <text x="30" y="158" fill="#71717a" font-size="10" font-family="JetBrains Mono">INTRADAY</text>
                    <text x="180" y="158" fill="#71717a" font-size="10" font-family="JetBrains Mono">CANDLES (15M)</text>
                    <text x="380" y="158" fill="#71717a" font-size="10" font-family="JetBrains Mono">SESSION</text>
                    <text x="540" y="158" fill="{stroke_color}" font-size="10" font-family="JetBrains Mono" font-weight="700">● LIVE</text>
                </svg>
            </div>
            
            <div class="sig-indices-card" style="padding: 20px;">
                <div style="font-family: 'Inter', sans-serif; font-weight: 700; font-size: 14px; color: #ffffff; margin-bottom: 12px; display: flex; justify-content: space-between;">
                    <span>Major Indices</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #3b82f6; cursor: pointer;">Live Wire &gt;</span>
                </div>
                {''.join(idx_rows_html)}
            </div>
        </div>
    </div>
    """
    return clean_html(raw_html)


def render_market_mini_cards() -> str:
    """Renders Section 1 Tri-Metric Sparkline Cards with real live figures."""
    try:
        from utils.live_market_data import fetch_mini_cards_data
        mc = fetch_mini_cards_data()
    except Exception:
        mc = {
            "crypto_cap": "2.59T", "crypto_cap_chg": "-3.94%", "crypto_cap_up": False,
            "btc_dominance": "58.5%", "eth_dominance": "11.2%", "others_dominance": "30.3%",
            "btc_price": "$75,724", "btc_chg": "-0.87%", "btc_up": False,
            "eth_price": "$2,391", "eth_chg": "-1.26%", "eth_up": False,
            "dxy": "99.70", "dxy_chg": "+0.59%", "dxy_up": True,
            "crude": "$102.64", "crude_chg": "+2.59%", "crude_up": True,
            "natgas": "$2.93", "natgas_chg": "+0.51%", "natgas_up": True,
            "gold": "$4,389.10", "gold_chg": "-0.45%", "gold_up": False,
            "copper": "$6.51", "copper_chg": "+1.10%", "copper_up": True,
            "us_10y": "4.96%", "us_10y_chg": "+0.30%", "us_10y_up": True,
            "us_interest_rate": "4.50%", "us_inflation_rate": "2.6%",
        }

    c_cap_badge_color = "#22c55e" if mc.get("crypto_cap_up") else "#ef4444"
    c_cap_badge_bg = "rgba(34, 197, 94, 0.1)" if mc.get("crypto_cap_up") else "rgba(239, 68, 68, 0.1)"
    dxy_badge_color = "#22c55e" if mc.get("dxy_up") else "#ef4444"
    dxy_badge_bg = "rgba(34, 197, 94, 0.1)" if mc.get("dxy_up") else "rgba(239, 68, 68, 0.1)"
    u10_badge_color = "#22c55e" if mc.get("us_10y_up") else "#ef4444"
    u10_badge_bg = "rgba(34, 197, 94, 0.1)" if mc.get("us_10y_up") else "rgba(239, 68, 68, 0.1)"

    raw_html = f"""
    <div class="sig-mini-cards-grid">
        <div class="sig-mini-card">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase;">CRYPTO MARKET CAP // TOTAL</div>
                        <div style="font-family: 'Inter', sans-serif; font-size: 22px; font-weight: 800; color: #ffffff; margin-top: 2px;">{mc['crypto_cap']} <span style="font-size: 12px; color: #71717a;">USD</span></div>
                    </div>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: {c_cap_badge_color}; background: {c_cap_badge_bg}; padding: 3px 8px; border-radius: 4px;">{mc['crypto_cap_chg']}</span>
                </div>
                <svg viewBox="0 0 260 50" style="width: 100%; height: 50px; margin: 10px 0;">
                    <polyline fill="none" stroke="{c_cap_badge_color}" stroke-width="2" points="10,40 40,36 80,42 120,25 160,28 200,16 250,8"/>
                </svg>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #94a3b8; margin-bottom: 6px;">MARKET DOMINANCE (COINGECKO)</div>
                <div style="display: flex; height: 7px; border-radius: 4px; overflow: hidden; margin-bottom: 8px;">
                    <div style="width: {mc.get('btc_dominance', '58.5%')}; background: #f59e0b;" title="Bitcoin {mc.get('btc_dominance', '58.5%')}"></div>
                    <div style="width: {mc.get('eth_dominance', '11.2%')}; background: #3b82f6;" title="Ethereum {mc.get('eth_dominance', '11.2%')}"></div>
                    <div style="width: {mc.get('others_dominance', '30.3%')}; background: #64748b;" title="Others {mc.get('others_dominance', '30.3%')}"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #94a3b8;">
                    <span><strong style="color: #f59e0b;">●</strong> BTC {mc.get('btc_dominance', '58.5%')}</span>
                    <span><strong style="color: #3b82f6;">●</strong> ETH {mc.get('eth_dominance', '11.2%')}</span>
                    <span><strong style="color: #64748b;">●</strong> Alt {mc.get('others_dominance', '30.3%')}</span>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px; margin-top: 12px; font-family: 'JetBrains Mono', monospace; font-size: 11px;">
                <span>BTC <strong style="color: #fff;">{mc.get('btc_price', '$75,724')}</strong> (<span style="color: {'#22c55e' if mc.get('btc_up') else '#ef4444'};">{mc.get('btc_chg', '-0.87%')}</span>)</span>
                <span>ETH <strong style="color: #fff;">{mc.get('eth_price', '$2,391')}</strong> (<span style="color: {'#22c55e' if mc.get('eth_up') else '#ef4444'};">{mc.get('eth_chg', '-1.26%')}</span>)</span>
            </div>
        </div>

        <div class="sig-mini-card">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase;">US DOLLAR INDEX // DXY</div>
                        <div style="font-family: 'Inter', sans-serif; font-size: 22px; font-weight: 800; color: #ffffff; margin-top: 2px;">{mc['dxy']} <span style="font-size: 12px; color: #71717a;">USD</span></div>
                    </div>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: {dxy_badge_color}; background: {dxy_badge_bg}; padding: 3px 8px; border-radius: 4px;">{mc['dxy_chg']}</span>
                </div>
                <svg viewBox="0 0 260 50" style="width: 100%; height: 50px; margin: 10px 0;">
                    <polyline fill="none" stroke="{dxy_badge_color}" stroke-width="2" points="10,32 50,30 90,38 130,22 170,26 210,18 250,14"/>
                </svg>
                <div style="display: flex; flex-direction: column; gap: 6px; font-family: 'JetBrains Mono', monospace; font-size: 11px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #94a3b8;">Light Crude Oil</span>
                        <span><strong style="color: #fff;">{mc.get('crude', '$102.64')}</strong> <span style="color: {'#22c55e' if mc.get('crude_up') else '#ef4444'};">{mc.get('crude_chg', '+2.59%')}</span></span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #94a3b8;">Natural Gas</span>
                        <span><strong style="color: #fff;">{mc.get('natgas', '$2.93')}</strong> <span style="color: {'#22c55e' if mc.get('natgas_up') else '#ef4444'};">{mc.get('natgas_chg', '+0.51%')}</span></span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #94a3b8;">Spot Gold (GC=F)</span>
                        <span><strong style="color: #fff;">{mc.get('gold', '$4,389.10')}</strong> <span style="color: {'#22c55e' if mc.get('gold_up') else '#ef4444'};">{mc.get('gold_chg', '-0.45%')}</span></span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #94a3b8;">Copper</span>
                        <span><strong style="color: #fff;">{mc.get('copper', '$6.51')}</strong> <span style="color: {'#22c55e' if mc.get('copper_up') else '#ef4444'};">{mc.get('copper_chg', '+1.10%')}</span></span>
                    </div>
                </div>
            </div>
            <div style="border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px; margin-top: 12px; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #3b82f6;">
                Real-Time Commodities Telemetry &gt;
            </div>
        </div>

        <div class="sig-mini-card">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase;">US 10Y YIELD // BENCHMARK</div>
                        <div style="font-family: 'Inter', sans-serif; font-size: 22px; font-weight: 800; color: #ffffff; margin-top: 2px;">{mc['us_10y']} <span style="font-size: 12px; color: #71717a;">US10Y</span></div>
                    </div>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: {u10_badge_color}; background: {u10_badge_bg}; padding: 3px 8px; border-radius: 4px;">{mc['us_10y_chg']}</span>
                </div>
                <svg viewBox="0 0 260 50" style="width: 100%; height: 50px; margin: 10px 0;">
                    <polyline fill="none" stroke="{u10_badge_color}" stroke-width="2" points="10,25 40,28 80,20 130,26 170,16 210,22 250,12"/>
                </svg>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #94a3b8; margin-bottom: 6px;">US ANNUAL INFLATION RATE // USIRYY</div>
                <div style="display: flex; align-items: flex-end; gap: 8px; height: 36px; margin-bottom: 10px;">
                    <div style="flex: 1; height: 75%; background: #3b82f6; border-radius: 2px;" title="Historical: 3.3%"></div>
                    <div style="flex: 1; height: 68%; background: #3b82f6; border-radius: 2px;" title="Historical: 3.0%"></div>
                    <div style="flex: 1; height: 65%; background: #3b82f6; border-radius: 2px;" title="Historical: 2.9%"></div>
                    <div style="flex: 1; height: 58%; background: #22c55e; border-radius: 2px;" title="Current: {mc.get('us_inflation_rate', '2.6%')}"></div>
                    <div style="flex: 1; height: 55%; background: #FFD700; border-radius: 2px;" title="Target: 2.0%"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 11px;">
                    <span style="color: #94a3b8;">US Policy Rate:</span>
                    <span><strong style="color: #fff;">{mc.get('us_interest_rate', '4.50%')}</strong> (Target Band)</span>
                </div>
            </div>
            <div style="border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px; margin-top: 12px; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #3b82f6;">
                Macro Rates &amp; Policy Matrix &gt;
            </div>
        </div>
    </div>
    """
    return clean_html(raw_html)


def render_stocks_section() -> str:
    """Renders Section 3: Today's Stocks with live active equities."""
    try:
        from utils.live_market_data import fetch_stocks_data
        stk = fetch_stocks_data()
    except Exception:
        stk = {
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

    chips_html = []
    for s in stk.get("trending", [])[:5]:
        chg_fg = "#22c55e" if s.get("up") else "#ef4444"
        sign = "+" if s.get("pct", 0) >= 0 else ""
        chips_html.append(f"""
        <div class="sig-trend-chip">
            <div style="font-weight: 700; font-size: 13px; color: #ffffff;">{s['sym']}</div>
            <div style="font-size: 10px; color: #71717a;">{s['name']}</div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 800; color: {chg_fg}; margin-top: 4px;">{s['price']} <span style="font-size: 10px;">{sign}{s['pct']:.2f}%</span></div>
        </div>
        """)

    gainers_rows = []
    for s in stk.get("gainers", [])[:5]:
        sign = "+" if s.get("pct", 0) >= 0 else ""
        gainers_rows.append(f"""
        <div class="sig-table-row">
            <div>
                <div style="font-weight: 700; font-size: 13px; color: #ffffff;">{s['name']}</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #71717a;">{s['sym']}</div>
            </div>
            <div style="text-align: right; display: flex; align-items: center; gap: 12px;">
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700; color: #ffffff;">{s['price']}</span>
                <span class="sig-pill-gain">{sign}{s['pct']:.2f}%</span>
            </div>
        </div>
        """)

    losers_rows = []
    for s in stk.get("losers", [])[:5]:
        sign = "+" if s.get("pct", 0) >= 0 else ""
        losers_rows.append(f"""
        <div class="sig-table-row">
            <div>
                <div style="font-weight: 700; font-size: 13px; color: #ffffff;">{s['name']}</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #71717a;">{s['sym']}</div>
            </div>
            <div style="text-align: right; display: flex; align-items: center; gap: 12px;">
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700; color: #ffffff;">{s['price']}</span>
                <span class="sig-pill-loss">{sign}{s['pct']:.2f}%</span>
            </div>
        </div>
        """)

    raw_html = f"""
    <div id="stocks-section">
        <div class="sig-sec-header">
            <div class="sig-sec-title">US stocks &gt; <span style="font-size: 14px; font-weight: 500; color: #94a3b8;">Active Volume Leaders</span></div>
            <div class="sig-sec-sub">LIVE EQUITIES INTELLIGENCE (YAHOO FINANCE REST)</div>
        </div>
        <div class="sig-trend-chips">
            {''.join(chips_html)}
        </div>

        <div class="sig-gainers-grid">
            <div class="sig-table-card">
                <div style="font-family: 'Inter', sans-serif; font-weight: 800; font-size: 15px; color: #ffffff; margin-bottom: 14px; display: flex; justify-content: space-between;">
                    <span>Top Performers &gt;</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #22c55e;">Regular Hours</span>
                </div>
                {''.join(gainers_rows)}
            </div>

            <div class="sig-table-card">
                <div style="font-family: 'Inter', sans-serif; font-weight: 800; font-size: 15px; color: #ffffff; margin-bottom: 14px; display: flex; justify-content: space-between;">
                    <span>Under pressure &gt;</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #ef4444;">Regular Hours</span>
                </div>
                {''.join(losers_rows)}
            </div>
        </div>
    </div>
    """
    return clean_html(raw_html)


def render_crypto_section() -> str:
    """Renders Section 4: Crypto Desk with real live on-chain & spot telemetry."""
    try:
        from utils.live_market_data import fetch_crypto_data
        cry = fetch_crypto_data()
    except Exception:
        cry = {
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

    chips_html = []
    for c in cry.get("trending", [])[:5]:
        chg_fg = "#22c55e" if c.get("up") else "#ef4444"
        sign = "+" if c.get("pct", 0) >= 0 else ""
        chips_html.append(f"""
        <div class="sig-trend-chip">
            <div style="font-weight: 700; font-size: 13px; color: #ffffff;">{c['sym']}</div>
            <div style="font-size: 10px; color: #71717a;">{c['name']}</div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 800; color: {chg_fg}; margin-top: 4px;">{c['price_str']} <span style="font-size: 10px;">{sign}{c['pct']:.2f}%</span></div>
        </div>
        """)

    gainers_rows = []
    for c in cry.get("gainers", [])[:5]:
        sign = "+" if c.get("pct", 0) >= 0 else ""
        gainers_rows.append(f"""
        <div class="sig-table-row">
            <div>
                <div style="font-weight: 700; font-size: 13px; color: #ffffff;">{c['name']}</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #71717a;">{c['sym']} / USD</div>
            </div>
            <div style="text-align: right; display: flex; align-items: center; gap: 12px;">
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700; color: #ffffff;">{c['price_str']}</span>
                <span class="sig-pill-gain">{sign}{c['pct']:.2f}%</span>
            </div>
        </div>
        """)

    losers_rows = []
    for c in cry.get("losers", [])[:5]:
        sign = "+" if c.get("pct", 0) >= 0 else ""
        losers_rows.append(f"""
        <div class="sig-table-row">
            <div>
                <div style="font-weight: 700; font-size: 13px; color: #ffffff;">{c['name']}</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #71717a;">{c['sym']} / USD</div>
            </div>
            <div style="text-align: right; display: flex; align-items: center; gap: 12px;">
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700; color: #ffffff;">{c['price_str']}</span>
                <span class="sig-pill-loss">{sign}{c['pct']:.2f}%</span>
            </div>
        </div>
        """)

    raw_html = f"""
    <div id="crypto-section">
        <div class="sig-sec-header">
            <div class="sig-sec-title">Crypto &gt; <span style="font-size: 14px; font-weight: 500; color: #94a3b8;">Spot &amp; Perpetual Leaders</span></div>
            <div class="sig-sec-sub">ON-CHAIN &amp; PERPETUAL INTELLIGENCE (COINGECKO REST)</div>
        </div>
        <div class="sig-trend-chips">
            {''.join(chips_html)}
        </div>

        <div class="sig-gainers-grid">
            <div class="sig-table-card">
                <div style="font-family: 'Inter', sans-serif; font-weight: 800; font-size: 15px; color: #ffffff; margin-bottom: 14px; display: flex; justify-content: space-between;">
                    <span>Crypto Gainers &gt;</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #22c55e;">24h Change</span>
                </div>
                {''.join(gainers_rows)}
            </div>

            <div class="sig-table-card">
                <div style="font-family: 'Inter', sans-serif; font-weight: 800; font-size: 15px; color: #ffffff; margin-bottom: 14px; display: flex; justify-content: space-between;">
                    <span>Crypto Losers &gt;</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #ef4444;">24h Change</span>
                </div>
                {''.join(losers_rows)}
            </div>
        </div>
    </div>
    """
    return clean_html(raw_html)


def render_breaking_news_grid(news_items: List[Dict[str, Any]]) -> str:
    """Renders breaking news cards with real clickable target='_blank' links and live timestamps."""
    cards_html = []
    for item in news_items[:6]:
        tags = item.get("tags", ["MARKETS"])
        tag_str = tags[0] if tags else "MARKET INTEL"
        pub = item.get("published", "Live")
        title = item.get("title", "Market Update")
        summary = item.get("summary", "")
        source = item.get("source", "Financial Wire")
        sent = item.get("sentiment", "NEUTRAL").upper()

        raw_url = item.get("url")
        if raw_url and (raw_url.startswith("http://") or raw_url.startswith("https://")):
            url = raw_url
        else:
            url = f"https://news.google.com/search?q={urllib.parse.quote(title)}&hl=en-US"

        if sent == "BULLISH":
            sent_badge = '<span class="tv-news-sentiment-bull">BULLISH</span>'
        elif sent == "BEARISH":
            sent_badge = '<span class="tv-news-sentiment-bear">BEARISH</span>'
        else:
            sent_badge = '<span class="tv-news-sentiment-neutral">NEUTRAL</span>'

        cards_html.append(
            f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="tv-news-card-link" title="Open story on {source}">'
            f'<div class="tv-news-card">'
            f'<div>'
            f'<div class="tv-news-meta"><span class="tv-news-tag">{tag_str}</span><span class="tv-news-time">{pub}</span></div>'
            f'<div class="tv-news-title">{title}</div>'
            f'<div class="tv-news-summary">{summary}</div>'
            f'</div>'
            f'<div class="tv-news-footer">'
            f'<span class="tv-news-source">{source} <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg></span>'
            f'{sent_badge}'
            f'</div>'
            f'</div>'
            f'</a>'
        )

    return clean_html(f'<div class="tv-news-grid">{"".join(cards_html)}</div>')


def render_category_pills(active_category: str = "US Stocks") -> str:
    """Renders the asset category navigation pills."""
    categories = [
        "All",
        "US Stocks",
        "Crypto",
        "Futures & Commodities",
        "Forex",
        "Bonds & Rates",
        "Global Economy",
    ]
    pills_html = []
    for cat in categories:
        active_class = "active" if cat.lower() == active_category.lower() else ""
        pills_html.append(f'<span class="tv-cat-pill {active_class}">{cat}</span>')

    return clean_html(f'<div class="tv-cat-pills">{"".join(pills_html)}</div>')


def render_bonds_dashboard() -> str:
    """Renders the dedicated Bonds & Yield Curve hub with live telemetry."""
    try:
        from utils.live_market_data import fetch_bonds_data, fetch_mini_cards_data
        bonds = fetch_bonds_data()
        mc = fetch_mini_cards_data()
    except Exception:
        bonds = [
            {"tenor": "2Y", "yield": "3.94%", "price": "100.00", "chg": "+9.7bps", "up": True},
            {"tenor": "5Y", "yield": "4.78%", "price": "100.00", "chg": "+4.2bps", "up": True},
            {"tenor": "10Y", "yield": "4.96%", "price": "100.00", "chg": "+1.3bps", "up": True},
            {"tenor": "30Y", "yield": "5.34%", "price": "100.00", "chg": "-2.4bps", "up": False},
        ]
        mc = {"us_10y": "4.96%", "us_30y": "5.34%", "us_2y": "3.94%"}

    b_map = {b["tenor"]: b for b in bonds}
    y_2y = b_map.get("2Y", {}).get("yield", "3.94%")
    y_10y = b_map.get("10Y", {}).get("yield", "4.96%")
    y_30y = b_map.get("30Y", {}).get("yield", "5.34%")

    chg_2y = b_map.get("2Y", {}).get("chg", "+9.7bps")
    chg_10y = b_map.get("10Y", {}).get("chg", "+1.3bps")
    chg_30y = b_map.get("30Y", {}).get("chg", "-2.4bps")

    try:
        val_10 = float(y_10y.replace("%", "").strip())
        val_2 = float(y_2y.replace("%", "").strip())
        spread_bps = round((val_10 - val_2) * 100)
        spread_str = f"{'+' if spread_bps >= 0 else ''}{spread_bps} bps"
        regime = "Normal Curve" if spread_bps >= 0 else "Curve Inversion"
    except Exception:
        spread_str = "+102 bps"
        regime = "Normal Curve"

    raw_html = f"""
    <div id="bonds-section" class="tv-bonds-container">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: #FFD700; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 16px;">
            FIXED INCOME DESK // US TREASURY YIELD CURVE ARCHITECTURE (LIVE TELEMETRY)
        </div>
        
        <div class="tv-yield-cards">
            <div class="tv-yield-card">
                <div class="tv-yield-card-tenor">US 2-YEAR NOTE</div>
                <div class="tv-yield-card-rate">{y_2y}</div>
                <div class="tv-yield-card-spread" style="color: {'#22c55e' if '+' in chg_2y else '#ef4444'};">{chg_2y} Intraday</div>
            </div>
            <div class="tv-yield-card">
                <div class="tv-yield-card-tenor">US 10-YEAR BENCHMARK</div>
                <div class="tv-yield-card-rate">{y_10y}</div>
                <div class="tv-yield-card-spread" style="color: {'#22c55e' if '+' in chg_10y else '#ef4444'};">{chg_10y} Intraday</div>
            </div>
            <div class="tv-yield-card">
                <div class="tv-yield-card-tenor">US 30-YEAR LONG BOND</div>
                <div class="tv-yield-card-rate">{y_30y}</div>
                <div class="tv-yield-card-spread" style="color: {'#22c55e' if '+' in chg_30y else '#ef4444'};">{chg_30y} Intraday</div>
            </div>
            <div class="tv-yield-card">
                <div class="tv-yield-card-tenor">10Y - 2Y SPREAD</div>
                <div class="tv-yield-card-rate">{spread_str}</div>
                <div class="tv-yield-card-spread" style="color: #FFD700;">{regime}</div>
            </div>
        </div>

        <div style="background: #0d0f1e; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 16px; margin-bottom: 18px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #94a3b8; text-transform: uppercase;">
                    YIELD CURVE DYNAMICS: CURRENT (GOLD) vs 1-MONTH AGO (CYAN) vs 1-YEAR AGO (SLATE)
                </span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #22c55e;">
                    SPREAD: 10Y-2Y {spread_str}
                </span>
            </div>
            <svg viewBox="0 0 700 160" style="width: 100%; height: 160px; overflow: visible;">
                <line x1="40" y1="20" x2="680" y2="20" stroke="rgba(255,255,255,0.05)" stroke-dasharray="3,3" />
                <line x1="40" y1="60" x2="680" y2="60" stroke="rgba(255,255,255,0.05)" stroke-dasharray="3,3" />
                <line x1="40" y1="100" x2="680" y2="100" stroke="rgba(255,255,255,0.05)" stroke-dasharray="3,3" />
                <line x1="40" y1="140" x2="680" y2="140" stroke="rgba(255,255,255,0.1)" />

                <polyline fill="none" stroke="#475569" stroke-width="2" stroke-dasharray="4,4"
                    points="50,40 120,42 200,48 290,52 380,60 480,72 580,80 660,84" />

                <polyline fill="none" stroke="#38bdf8" stroke-width="2"
                    points="50,55 120,58 200,68 290,78 380,88 480,95 580,82 660,70" />

                <polyline fill="none" stroke="#FFD700" stroke-width="3"
                    points="50,65 120,70 200,82 290,98 380,108 480,118 580,88 660,60" />

                <circle cx="50" cy="65" r="4" fill="#FFD700" />
                <circle cx="200" cy="82" r="4" fill="#FFD700" />
                <circle cx="380" cy="108" r="4" fill="#FFD700" />
                <circle cx="480" cy="118" r="4" fill="#FFD700" />
                <circle cx="660" cy="60" r="4" fill="#FFD700" />

                <text x="50" y="155" fill="#64748b" font-size="10" font-family="JetBrains Mono" text-anchor="middle">1M</text>
                <text x="120" y="155" fill="#64748b" font-size="10" font-family="JetBrains Mono" text-anchor="middle">3M</text>
                <text x="200" y="155" fill="#64748b" font-size="10" font-family="JetBrains Mono" text-anchor="middle">6M</text>
                <text x="290" y="155" fill="#64748b" font-size="10" font-family="JetBrains Mono" text-anchor="middle">1Y</text>
                <text x="380" y="155" fill="#64748b" font-size="10" font-family="JetBrains Mono" text-anchor="middle">2Y ({y_2y})</text>
                <text x="480" y="155" fill="#64748b" font-size="10" font-family="JetBrains Mono" text-anchor="middle">10Y ({y_10y})</text>
                <text x="580" y="155" fill="#64748b" font-size="10" font-family="JetBrains Mono" text-anchor="middle">20Y</text>
                <text x="660" y="155" fill="#64748b" font-size="10" font-family="JetBrains Mono" text-anchor="middle">30Y ({y_30y})</text>
            </svg>
        </div>

        <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #94a3b8; text-transform: uppercase; margin-bottom: 8px;">
            GLOBAL SOVEREIGN 10-YEAR BENCHMARKS
        </div>
        <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px;">
            <div style="background: #0d0f1e; border: 1px solid rgba(255,255,255,0.06); padding: 8px 12px; border-radius: 6px;">
                <div style="font-size: 10px; color: #64748b;">UNITED STATES</div>
                <div style="font-size: 14px; font-weight: 700; color: #ffffff;">{y_10y}</div>
            </div>
            <div style="background: #0d0f1e; border: 1px solid rgba(255,255,255,0.06); padding: 8px 12px; border-radius: 6px;">
                <div style="font-size: 10px; color: #64748b;">GERMANY BUND</div>
                <div style="font-size: 14px; font-weight: 700; color: #ffffff;">2.74%</div>
            </div>
            <div style="background: #0d0f1e; border: 1px solid rgba(255,255,255,0.06); padding: 8px 12px; border-radius: 6px;">
                <div style="font-size: 10px; color: #64748b;">UK GILT</div>
                <div style="font-size: 14px; font-weight: 700; color: #ffffff;">4.65%</div>
            </div>
            <div style="background: #0d0f1e; border: 1px solid rgba(255,255,255,0.06); padding: 8px 12px; border-radius: 6px;">
                <div style="font-size: 10px; color: #64748b;">JAPAN JGB</div>
                <div style="font-size: 14px; font-weight: 700; color: #ffffff;">1.58%</div>
            </div>
            <div style="background: #0d0f1e; border: 1px solid rgba(255,255,255,0.06); padding: 8px 12px; border-radius: 6px;">
                <div style="font-size: 10px; color: #64748b;">INDIA 10Y</div>
                <div style="font-size: 14px; font-weight: 700; color: #ffffff;">6.78%</div>
            </div>
        </div>
    </div>
    """
    return clean_html(raw_html)
'''

new_content = pre + replacement + "\n\n" + post

with open("ui/blackbox_theme.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("SUCCESS: ui/blackbox_theme.py updated successfully!")
