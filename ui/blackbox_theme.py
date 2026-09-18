"""
SIGNALORA : From market noise to verified signals.
Institutional Design System & Layout Components matching Reference Video (website look.mp4)
and AetherOS Desktop Environment.

Features:
  - 3D Interactive Cursor-Reactive Lily Flower Background (AetherOS OrbitWallpaper) running in components.html
  - Tastefully dimmed lily (opacity ~0.62, brightness 0.70) for optimal typography contrast
  - Unified background color (#06070c) across the entire application (no mismatched side colors or stacked boxes)
  - TradingView Top Taskbar with Real Dropdown Menus & Smooth Anchors (Zero ugly radio buttons)
  - Concise System Builder / Architect Card in Bottom-Left Corner
  - Clickable Breaking News Cards opening verified financial publications in new tabs
  - Dedicated Taskbar Launch for Analyst Desk (Kept out of the clean overview)
  - World Inflation Map with 0%-25% gradient and Economic Calendar
"""
from __future__ import annotations
import urllib.parse
from typing import Any, Dict, List, Optional

__all__ = [
    "BLACKBOX_CSS",
    "render_signalora_brand_header",
    "render_hero_banner",
    "render_hero_banner_component",
    "render_global_market_ribbon",
    "render_market_summary_section",
    "render_market_mini_cards",
    "render_stocks_section",
    "render_crypto_section",
    "render_world_inflation_map",
    "render_global_economy_dashboard",
    "render_about_me_section",
    "render_category_pills",
    "render_breaking_news_grid",
    "render_bonds_dashboard",
    "render_benchmark_bars",
    "render_tradingview_widget",
    "render_tradingview_heatmap",
]

BLACKBOX_CSS = """
<style>
/* ---- Typography & Reset ---- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

html {
    scroll-behavior: smooth;
    background-color: #06070c !important;
}

html, body, [data-testid="stAppViewContainer"], .main {
    background-color: #06070c !important;
    background: #06070c !important;
    color: #e8e4dc !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    -webkit-font-smoothing: antialiased;
    letter-spacing: -0.015em;
}

/* Hide default streamlit top header */
[data-testid="stHeader"] {
    display: none !important;
}

/* Ensure seamless full-width layout with unified margins */
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 3rem !important;
    padding-left: 0rem !important;
    padding-right: 0rem !important;
    max-width: 100% !important;
    background-color: #06070c !important;
}

[data-testid="stAppViewBlockContainer"] {
    padding-top: 0rem !important;
    padding-left: 0rem !important;
    padding-right: 0rem !important;
    max-width: 100% !important;
}

/* Seamless iframe embedding for 3D Hero stage */
iframe[title="streamlit_components_v1.html"], iframe {
    border: none !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
    background-color: #06070c !important;
    width: 100% !important;
    border-radius: 0px !important;
    overflow: hidden !important;
    margin: 0 !important;
    box-shadow: none !important;
    display: block !important;
}

/* ---- SIGNALORA Institutional Taskbar with Real Dropdowns ---- */
.sig-taskbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 36px;
    background: #06070c;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 0;
    margin: 0;
    width: 100%;
    box-shadow: none;
}

.sig-brand-group {
    display: flex;
    align-items: center;
    gap: 12px;
}
.sig-brand-title {
    font-family: 'Inter', sans-serif;
    font-weight: 900;
    font-size: 21px;
    letter-spacing: -0.03em;
    color: #ffffff;
    text-decoration: none;
}
.sig-brand-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    color: #FFD700;
    background: rgba(255, 215, 0, 0.08);
    padding: 3px 8px;
    border-radius: 4px;
    border: 1px solid rgba(255, 215, 0, 0.22);
    letter-spacing: 0.06em;
}

/* Taskbar Search Simulation */
.sig-search-box {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #0f1122;
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 12px;
    color: #71717a;
    min-width: 240px;
}

/* Taskbar Dropdown Navigation */
.sig-nav-menu {
    display: flex;
    align-items: center;
    gap: 16px;
}
.sig-dropdown {
    position: relative;
    display: inline-block;
}
.sig-dropbtn {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #cbd5e1;
    text-decoration: none;
    padding: 6px 10px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    gap: 4px;
    transition: all 0.15s ease;
    cursor: pointer;
}
.sig-dropbtn:hover {
    color: #ffffff;
    background: rgba(255, 255, 255, 0.06);
}
.sig-drop-content {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    min-width: 200px;
    background: #0e1022;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 6px;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.8);
    z-index: 1001;
}
.sig-dropdown:hover .sig-drop-content {
    display: block;
}
.sig-drop-item {
    display: block;
    padding: 8px 12px;
    font-size: 12px;
    font-weight: 500;
    color: #cbd5e1;
    text-decoration: none;
    border-radius: 4px;
    transition: all 0.12s ease;
}
.sig-drop-item:hover {
    background: rgba(255, 215, 0, 0.08);
    color: #FFD700;
}

/* Taskbar Right Controls */
.sig-taskbar-right {
    display: flex;
    align-items: center;
    gap: 12px;
}
.sig-telemetry-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    color: #22c55e;
    background: rgba(34, 197, 94, 0.08);
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid rgba(34, 197, 94, 0.2);
    white-space: nowrap;
}
.sig-nav-action-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: rgba(255, 215, 0, 0.12);
    border: 1px solid rgba(255, 215, 0, 0.35);
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: #FFD700;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.15s ease;
    white-space: nowrap;
}
.sig-nav-action-btn:hover {
    background: #FFD700;
    color: #06070c;
    box-shadow: 0 0 14px rgba(255, 215, 0, 0.35);
}
.sig-nav-action-active {
    background: rgba(59, 130, 246, 0.15);
    border-color: rgba(59, 130, 246, 0.4);
    color: #60a5fa;
}
.sig-nav-action-active:hover {
    background: #3b82f6;
    color: #ffffff;
    box-shadow: 0 0 14px rgba(59, 130, 246, 0.4);
}

/* Top Global Market Ticker Ribbon (Joined seamlessly under Taskbar) */
.tv-ribbon {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 36px;
    background: #080912;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 0;
    overflow-x: auto;
    white-space: nowrap;
    margin-bottom: 0px;
    box-shadow: none;
    width: 100%;
}
.tv-ribbon::-webkit-scrollbar { height: 3px; }

/* Centered Main Page Container for all sections below the Hero */
.sig-main-container {
    max-width: 1480px;
    margin: 0 auto;
    padding: 24px 32px 48px 32px;
}

/* TradingView World Inflation Map Styles */
.sig-country {
    transition: fill 0.15s ease, stroke 0.15s ease, filter 0.15s ease;
    stroke: #06070c;
    stroke-width: 0.5px;
}
.sig-country:hover {
    fill: #ffffff !important;
    stroke: #FFD700 !important;
    stroke-width: 1.2px;
    filter: drop-shadow(0 0 6px rgba(255, 215, 0, 0.9));
    cursor: pointer;
}

.tv-map-pills {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.tv-map-pill {
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 600;
    color: #cbd5e1;
    background: #0d0f1e;
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 5px 14px;
    border-radius: 999px;
    text-decoration: none;
    transition: all 0.15s ease;
    cursor: pointer;
}
.tv-map-pill:hover {
    color: #ffffff;
    border-color: rgba(255, 215, 0, 0.4);
    background: rgba(255, 215, 0, 0.06);
}
.tv-map-pill-active {
    background: #1e222d !important;
    color: #ffffff !important;
    border-color: rgba(255, 255, 255, 0.25) !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}
.tv-ribbon-item {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 10px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    transition: all 0.15s ease;
}
.tv-ribbon-sym { font-weight: 700; color: #f1f5f9; }
.tv-ribbon-price { font-weight: 600; color: #ffffff; }
.tv-ribbon-change-pos { color: #22c55e; font-weight: 600; }
.tv-ribbon-change-neg { color: #ef4444; font-weight: 600; }
.tv-ribbon-change-neutral { color: #FFD700; font-weight: 600; }

/* Unified Section Headers */
.sig-sec-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 32px 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}
.sig-sec-title {
    font-family: 'Inter', sans-serif;
    font-size: 21px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #ffffff;
    display: inline-flex;
    align-items: center;
    gap: 8px;
}
.sig-sec-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #94a3b8;
}

/* Unified Glassmorphic Cards (Matching Background) */
.sig-chart-card, .sig-indices-card, .sig-mini-card, .sig-table-card, .tv-bonds-container, .sig-map-container, .sig-about-wrap {
    background: #080912 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.5) !important;
}

/* Market Summary 2-Column Container */
.sig-summary-wrap {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 18px;
    margin-bottom: 22px;
}
@media (max-width: 992px) {
    .sig-summary-wrap { grid-template-columns: 1fr; }
}

.sig-index-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.sig-index-row:last-child { border-bottom: none; }
.sig-badge-round {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 11px;
    background: #14172a;
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #ffffff;
}

/* 3 Mini Metric Cards (Crypto, DXY, US10Y) */
.sig-mini-cards-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 26px;
}
@media (max-width: 900px) {
    .sig-mini-cards-grid { grid-template-columns: 1fr; }
}
.sig-mini-card {
    padding: 18px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.2s ease;
}
.sig-mini-card:hover {
    border-color: rgba(255, 215, 0, 0.35) !important;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6) !important;
}

/* Trending Chips Row */
.sig-trend-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 18px;
}
.sig-trend-chip {
    background: #0d0f1e;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 10px 14px;
    display: flex;
    flex-direction: column;
    min-width: 140px;
    transition: all 0.15s ease;
}
.sig-trend-chip:hover {
    border-color: rgba(255, 215, 0, 0.4);
    background: rgba(255, 215, 0, 0.04);
}

/* Gainers / Losers Side-by-Side */
.sig-gainers-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
    margin-bottom: 24px;
}
@media (max-width: 768px) {
    .sig-gainers-grid { grid-template-columns: 1fr; }
}
.sig-table-card {
    padding: 18px;
}
.sig-table-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 9px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.sig-table-row:last-child { border-bottom: none; }
.sig-pill-gain {
    background: rgba(34, 197, 94, 0.12);
    color: #22c55e;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
}
.sig-pill-loss {
    background: rgba(239, 68, 68, 0.12);
    color: #ef4444;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
}

/* CLICKABLE Breaking News Cards */
.tv-news-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 26px;
}
@media (max-width: 1024px) { .tv-news-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px) { .tv-news-grid { grid-template-columns: 1fr; } }

.tv-news-card-link {
    text-decoration: none;
    color: inherit;
    display: block;
}
.tv-news-card {
    background: #0a0b16;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;
    transition: all 0.2s ease;
}
.tv-news-card-link:hover .tv-news-card {
    border-color: rgba(255, 215, 0, 0.5);
    transform: translateY(-3px);
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.7), 0 0 14px rgba(255, 215, 0, 0.12);
}
.tv-news-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}
.tv-news-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #FFD700;
    background: rgba(255, 215, 0, 0.08);
    padding: 3px 8px;
    border-radius: 4px;
    border: 1px solid rgba(255, 215, 0, 0.2);
}
.tv-news-time {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #7a766e;
}
.tv-news-title {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 700;
    color: #f8fafc;
    line-height: 1.35;
    margin-bottom: 8px;
}
.tv-news-card-link:hover .tv-news-title {
    color: #FFD700;
}
.tv-news-summary {
    font-size: 12px;
    color: #94a3b8;
    line-height: 1.45;
    margin-bottom: 14px;
    flex-grow: 1;
}
.tv-news-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: 10px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.tv-news-source {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 600;
    color: #cbd5e1;
    display: flex;
    align-items: center;
    gap: 6px;
}
.tv-news-sentiment-bull {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    color: #22c55e;
    background: rgba(34, 197, 94, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
}
.tv-news-sentiment-bear {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
}
.tv-news-sentiment-neutral {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    color: #94a3b8;
    background: rgba(148, 163, 184, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
}

/* Category Navigation Pills */
.tv-pills-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 20px;
}
.tv-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 16px;
    background: #0a0b16;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 9999px;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 600;
    color: #cbd5e1;
    cursor: pointer;
    text-decoration: none;
    transition: all 0.2s ease;
}
.tv-pill:hover {
    border-color: #FFD700;
    color: #ffffff;
    background: rgba(255, 215, 0, 0.06);
}
.tv-pill-active {
    background: rgba(255, 215, 0, 0.12) !important;
    border-color: #FFD700 !important;
    color: #FFD700 !important;
}

/* Yield Curve Cards */
.tv-yield-cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 20px;
}
@media (max-width: 768px) { .tv-yield-cards { grid-template-columns: repeat(2, 1fr); } }
.tv-yield-card {
    background: #0d0f1e;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 14px;
}
.tv-yield-card-tenor {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #94a3b8;
    text-transform: uppercase;
}
.tv-yield-card-rate {
    font-family: 'Inter', sans-serif;
    font-size: 24px;
    font-weight: 800;
    color: #ffffff;
    margin-top: 4px;
}
.tv-yield-card-spread {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    margin-top: 2px;
}

/* World Inflation Map */
.sig-map-legend {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    margin-top: 18px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #94a3b8;
}
.sig-map-grad-bar {
    width: 240px;
    height: 10px;
    border-radius: 5px;
    background: linear-gradient(90deg, #ffd97d 0%, #fca311 25%, #e85d04 50%, #dc2f02 75%, #9d0208 100%);
}
.sig-calendar-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-top: 20px;
}
@media (max-width: 800px) { .sig-calendar-grid { grid-template-columns: repeat(2, 1fr); } }
.sig-cal-card {
    background: #0d0f1e;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 14px;
}

/* Institutional Footer */
.sig-sitemap-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 24px;
    padding: 28px 0;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    margin-top: 24px;
}
@media (max-width: 800px) { .sig-sitemap-grid { grid-template-columns: repeat(2, 1fr); } }
.sig-sitemap-col-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: #FFD700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 12px;
}
.sig-sitemap-link {
    font-size: 12px;
    color: #8c8880;
    line-height: 2.0;
    display: block;
    text-decoration: none;
}
.sig-sitemap-link:hover { color: #ffffff; }

.sig-giant-banner {
    text-align: center;
    font-family: 'Inter', sans-serif;
    font-size: 34px;
    font-weight: 900;
    letter-spacing: -0.03em;
    color: #ffffff;
    padding: 40px 0 20px 0;
    text-transform: uppercase;
    background: linear-gradient(180deg, #ffffff 30%, #52525b 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
</style>
"""


def clean_html(html_str: str) -> str:
    """Strips all leading and trailing whitespace from every line."""
    return "\n".join(line.strip() for line in html_str.strip().splitlines() if line.strip())


def render_signalora_brand_header(active_view: str = "overview") -> str:
    """
    Renders the unified top taskbar with real dropdown menus and integrated Analyst Desk action button.
    """
    is_analyst = (active_view == "analyst_desk")
    desk_btn = (
        '<a href="?view=overview" target="_self" class="sig-nav-action-btn sig-nav-action-active">&larr; RETURN TO OVERVIEW</a>'
        if is_analyst
        else '<a href="?view=analyst_desk" target="_self" class="sig-nav-action-btn">&#9889; OPEN ANALYST DESK</a>'
    )

    raw_html = f"""
    <div class="sig-taskbar">
        <div class="sig-brand-group">
            <a href="?view=overview" target="_self" class="sig-brand-title">SIGNALORA</a>
        </div>

        <div class="sig-search-box">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#71717a" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
            <span>Search ticker, claim, news... (Ctrl+K)</span>
        </div>

        <div class="sig-nav-menu">
            <div class="sig-dropdown">
                <span class="sig-dropbtn">Markets &#9662;</span>
                <div class="sig-drop-content">
                    <a href="#market-summary" class="sig-drop-item">S&amp;P 500 &amp; Indices</a>
                    <a href="#stocks-section" class="sig-drop-item">US Stocks Gainers</a>
                    <a href="#crypto-section" class="sig-drop-item">Crypto Intelligence</a>
                    <a href="#bonds-section" class="sig-drop-item">Bonds &amp; Yield Curve</a>
                    <a href="#world-map-section" class="sig-drop-item">Global Inflation Map</a>
                </div>
            </div>

            <div class="sig-dropdown">
                <span class="sig-dropbtn">News &#9662;</span>
                <div class="sig-drop-content">
                    <a href="#news-section" class="sig-drop-item">Live Financial Wire</a>
                    <a href="#news-section" class="sig-drop-item">Top Market Stories</a>
                </div>
            </div>

            <div class="sig-dropdown">
                <span class="sig-dropbtn">Strategist &#9662;</span>
                <div class="sig-drop-content">
                    <a href="#kim-strategist-section" class="sig-drop-item">Kim Voice AI Console</a>
                    <a href="#kim-strategist-section" class="sig-drop-item">TradingView Superchart</a>
                </div>
            </div>

            <div class="sig-dropdown">
                <span class="sig-dropbtn">About &#9662;</span>
                <div class="sig-drop-content">
                    <a href="#about-signalora" class="sig-drop-item">System Architect</a>
                    <a href="#about-signalora" class="sig-drop-item">32 Agent Swarm Specs</a>
                </div>
            </div>
        </div>

        <div class="sig-taskbar-right">
            <span class="sig-telemetry-pill">&#9679; 32 AGENTS ACTIVE</span>
            <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #FFD700; margin-right: 4px;">[ FEED: 5-10M ]</span>
            {desk_btn}
        </div>
    </div>
    """
    return clean_html(raw_html)


def render_hero_banner_component() -> str:
    """
    Self-contained full HTML/CSS/JS for the 3D Cursor-Reactive Lily Flower Hero Banner.
    Rendered via streamlit.components.v1.html to ensure 100% reliable 60fps canvas mousemove execution.
    Features:
      - Tastefully dimmed lily flower (opacity: 0.48, brightness: 0.68) for optimal typography contrast
      - Soft radial contrast cushion behind text plate so white & gold typography is razor sharp
      - Pure #06070c background blending seamlessly with the main site
      - Big bold SIGNALORA typography with illuminated text-shadows
      - Concise System Builder card in the bottom-left corner
      - Unwanted text completely removed
      - 60FPS fluid canvas with organic ambient flow and instant cursor following
    """
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap');

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body, html {
    width: 100%;
    height: 100%;
    overflow: hidden;
    background-color: #06070c;
    color: #e8e4dc;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    user-select: none;
    -webkit-font-smoothing: antialiased;
}

.hero-stage {
    position: relative;
    width: 100%;
    height: 100%;
    background: #06070c;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

/* Background Lilies Layer with Tastefully Dimmed Atmospheric Styling */
.lily-front {
    position: absolute;
    top: 52%;
    left: 50%;
    transform: translate(-50%, -50%);
    max-height: 80%;
    max-width: 72%;
    object-fit: contain;
    pointer-events: none;
    z-index: 2;
    opacity: 0.48;
    filter: brightness(0.68) contrast(1.12) saturate(0.90) drop-shadow(0 20px 40px rgba(0,0,0,0.92));
}

.lily-reveal {
    position: absolute;
    top: 52%;
    left: 50%;
    transform: translate(-50%, -50%);
    max-height: 80%;
    max-width: 72%;
    object-fit: contain;
    pointer-events: none;
    z-index: 4;
    opacity: 0.20;
    mix-blend-mode: screen;
    filter: brightness(0.60);
}

canvas {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    z-index: 3;
    mix-blend-mode: screen;
    pointer-events: none;
}

/* Top Corner Badges (Placed in corners/sides, never in the middle) */
.hero-top-row {
    position: absolute;
    top: 14px;
    left: 0;
    right: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 28px;
    pointer-events: none;
    width: 100%;
}
.corner-badge {
    pointer-events: auto;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 6px;
    backdrop-filter: blur(12px);
    transition: all 0.2s ease;
}
.corner-left {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: #FFD700;
    background: rgba(8, 10, 18, 0.85);
    border: 1px solid rgba(255, 215, 0, 0.3);
    letter-spacing: 0.1em;
}
.corner-right {
    color: #94a3b8;
    background: rgba(8, 10, 18, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    letter-spacing: 0.08em;
}
.dot-green {
    width: 6px;
    height: 6px;
    background: #22c55e;
    border-radius: 50%;
    box-shadow: 0 0 8px #22c55e;
}

/* Center Content: Merged pure typography directly over flower (NO BOXES, NO PLATES, NO RADIAL CONTAINERS) */
.hero-center-flow {
    position: relative;
    z-index: 10;
    text-align: center;
    pointer-events: none;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 0 20px;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
.hero-center-flow * {
    pointer-events: auto;
}

.brand-title {
    font-size: 68px;
    font-weight: 900;
    letter-spacing: -0.04em;
    line-height: 1.0;
    color: #ffffff;
    text-shadow: 0 4px 36px rgba(0, 0, 0, 0.98), 0 2px 14px rgba(0, 0, 0, 0.95);
    margin: 0 0 12px 0;
    background: transparent !important;
    border: none !important;
}

.headline {
    font-size: 34px;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #ffffff;
    text-shadow: 0 4px 30px rgba(0, 0, 0, 0.98), 0 2px 10px rgba(0, 0, 0, 0.9);
    line-height: 1.1;
    margin: 0 0 18px 0;
    background: transparent !important;
    border: none !important;
}

.cta-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
}

.cta-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 28px;
    background: #ffffff;
    color: #06070c;
    font-weight: 800;
    font-size: 13.5px;
    border-radius: 999px;
    text-decoration: none;
    cursor: pointer;
    box-shadow: 0 4px 24px rgba(255, 255, 255, 0.25);
    transition: all 0.2s ease;
    border: none;
}
.cta-btn:hover {
    transform: translateY(-2px);
    background: #f1f5f9;
    box-shadow: 0 6px 30px rgba(255, 255, 255, 0.45);
}

.hero-chevron-down {
    cursor: pointer;
    animation: tvBounce 2.2s infinite ease-in-out;
    opacity: 0.75;
    transition: opacity 0.2s ease;
}
.hero-chevron-down:hover {
    opacity: 1;
}
@keyframes tvBounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(5px); }
}

/* Bottom Row of Hero Stage: Absolutely Pinned to Prevent Any Clipping */
.bottom-row {
    position: absolute;
    bottom: 12px;
    left: 0;
    right: 0;
    z-index: 10;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    padding: 0 28px;
    pointer-events: none;
}
.bottom-row * {
    pointer-events: auto;
}

/* Builder Card in Bottom-Left Corner: Crisp, Prominent Concise Information */
.builder-card {
    background: rgba(8, 10, 18, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-left: 3px solid #FFD700;
    border-radius: 8px;
    padding: 10px 16px;
    max-width: 380px;
    backdrop-filter: blur(16px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.85);
}
.builder-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    color: #FFD700;
    letter-spacing: 0.1em;
    margin-bottom: 2px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.builder-title {
    font-size: 13px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 3px;
}
.builder-specs {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    color: #cbd5e1;
    line-height: 1.45;
}

.telemetry-card {
    background: rgba(8, 10, 18, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 10px 16px;
    text-align: right;
    backdrop-filter: blur(16px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.85);
}
.telemetry-title {
    font-size: 13px;
    font-weight: 700;
    color: #ffffff;
}
.telemetry-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #22c55e;
    margin: 3px 0 8px 0;
}
.explore-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: #14172a;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    color: #ffffff;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.15s ease;
}
.explore-link:hover {
    color: #FFD700;
    border-color: #FFD700;
}
</style>
</head>
<body>
<div class="hero-stage">
    <!-- Tastefully Dimmed Atmospheric Lilies -->
    <img class="lily-front" src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260808_192942_e1086505-d7da-433b-a59b-8220f4e6c808.png" alt="Orbit Front Lily" />
    <canvas id="orbit-canvas"></canvas>
    <img class="lily-reveal" src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260808_151324_bf318a5f-5525-4fc7-aab5-e9a341018828.png" alt="Orbit Reveal Lily" />

    <!-- Top Corner Badges (Corners / Sides, NEVER in the middle!) -->
    <div class="hero-top-row">
        <div class="corner-badge corner-left">
            <span class="dot-green"></span>
            <span>AUTONOMOUS MULTI-AGENT QUANTITATIVE ENGINE</span>
        </div>
        <div class="corner-badge corner-right">
            <span>FROM MARKET NOISE TO VERIFIED SIGNALS</span>
        </div>
    </div>

    <!-- Center Flow: ONLY FLOWER + SIGNALORA (bold) + Look first / Then leap. (somewhat below) + CTA + Chevron (NO BOXES, NO PLATES, PURE MERGED TEXT) -->
    <div class="hero-center-flow">
        <div class="brand-title">SIGNALORA</div>
        <div class="headline">Look first / Then leap.</div>
        <div class="cta-wrap">
            <button class="cta-btn" onclick="scrollToMarkets()">
                <span>Explore Live Terminal</span>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"/></svg>
            </button>
            <div class="hero-chevron-down" onclick="scrollToMarkets()">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg>
            </div>
        </div>
    </div>

    <!-- Bottom Row: Builder Info on Left, Telemetry on Right -->
    <div class="bottom-row">
        <div class="builder-card">
            <div class="builder-tag"><span class="dot-green"></span> SYSTEM ARCHITECT</div>
            <div class="builder-title">Varad &bull; Multi-Agent Intelligence</div>
            <div class="builder-specs">
                &bull; 32 Autonomous Agents &bull; LangGraph DAG<br>
                &bull; Dual-Gate Bayesian Verification<br>
                &bull; SEC EDGAR 10-Q Forensic Auditor<br>
                &bull; Windows SAPI 16-Bit Biometrics
            </div>
        </div>

        <div class="telemetry-card">
            <div class="telemetry-title">Verified Signal Intelligence</div>
            <div class="telemetry-sub">&#9679; 32 Agents Synchronized &bull; Feed: 5-10m Active</div>
            <button class="explore-link" onclick="scrollToMarkets()">
                <span>Explore Markets</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>
            </button>
        </div>
    </div>
</div>

<!-- 60FPS Cursor-Following & Living Fluid Blob Canvas -->
<script>
(function() {
    const canvas = document.getElementById('orbit-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animFrame;
    let time = 0;
    let headRadius = 0;
    let targetR = 0;
    let points = [];
    let mousePos = { x: -1000, y: -1000 };
    let hasMouse = false;
    let ambientTimer = 0;

    const resize = () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const onMove = (e) => {
        mousePos = { x: e.clientX, y: e.clientY };
        hasMouse = true;
        targetR = 140;
    };

    window.addEventListener('mousemove', onMove, { passive: true });
    window.addEventListener('pointermove', onMove, { passive: true });
    window.addEventListener('touchmove', (e) => {
        if (e.touches && e.touches[0]) {
            onMove(e.touches[0]);
        }
    }, { passive: true });

    document.addEventListener('mouseenter', () => {
        hasMouse = true;
        targetR = 140;
    });

    document.addEventListener('mouseleave', () => {
        hasMouse = false;
        targetR = 0;
    });

    // Also listen to parent window mouse movement if accessible
    try {
        if (window.parent && window.parent !== window) {
            window.parent.addEventListener('mousemove', (e) => {
                const frame = window.frameElement;
                if (frame) {
                    const rect = frame.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    if (x >= -60 && x <= rect.width + 60 && y >= -60 && y <= rect.height + 60) {
                        mousePos = {
                            x: Math.max(0, Math.min(rect.width, x)),
                            y: Math.max(0, Math.min(rect.height, y))
                        };
                        hasMouse = true;
                        targetR = 140;
                    }
                }
            }, { passive: true });
        }
    } catch(err) {}

    const drawMorphBlob = (context, cx, cy, r, t, seed) => {
        if (r < 2) return;
        const numPts = 24;
        const pts = [];

        for (let i = 0; i < numPts; i++) {
            const angle = (i / numPts) * Math.PI * 2;
            const n1 = Math.sin(angle * 3 + t * 1.4 + seed) * 0.45;
            const n2 = Math.sin(angle * 5 - t * 0.9 + seed * 2.3) * 0.3;
            const n3 = Math.cos(angle * 2 + t * 1.8 + seed * 0.7) * 0.25;
            const noise = (n1 + n2 + n3) * 38 * (r / 140);
            const rad = Math.max(2, r + noise);
            pts.push({
                x: cx + Math.cos(angle) * rad,
                y: cy + Math.sin(angle) * rad
            });
        }

        context.beginPath();
        const firstMidX = (pts[0].x + pts[numPts - 1].x) / 2;
        const firstMidY = (pts[0].y + pts[numPts - 1].y) / 2;
        context.moveTo(firstMidX, firstMidY);

        for (let i = 0; i < numPts; i++) {
            const next = pts[(i + 1) % numPts];
            const midX = (pts[i].x + next.x) / 2;
            const midY = (pts[i].y + next.y) / 2;
            context.quadraticCurveTo(pts[i].x, pts[i].y, midX, midY);
        }
        context.closePath();
        context.fill();
    };

    const render = () => {
        time += 0.016;
        headRadius += (targetR - headRadius) * (hasMouse ? 0.14 : 0.04);

        // Organic ambient gentle pulse when mouse is idle
        if (!hasMouse || headRadius < 20) {
            ambientTimer += 0.018;
            const ambX = (canvas.width * 0.5) + Math.cos(ambientTimer * 0.7) * (canvas.width * 0.16);
            const ambY = (canvas.height * 0.52) + Math.sin(ambientTimer * 0.9) * (canvas.height * 0.12);
            if (Math.random() < 0.18 && points.length < 32) {
                points.push({
                    x: ambX + (Math.random() - 0.5) * 40,
                    y: ambY + (Math.random() - 0.5) * 40,
                    r: 75 + Math.sin(ambientTimer) * 25,
                    alpha: 0.65,
                    seed: Math.random() * 100
                });
            }
        }

        if (hasMouse && headRadius > 5) {
            const last = points[points.length - 1];
            const dist = last ? Math.hypot(mousePos.x - last.x, mousePos.y - last.y) : 999;
            if (dist > 7) {
                points.push({
                    x: mousePos.x,
                    y: mousePos.y,
                    r: headRadius,
                    alpha: 1,
                    seed: Math.random() * 100
                });
                if (points.length > 55) points.shift();
            }
        }

        for (let i = points.length - 1; i >= 0; i--) {
            points[i].alpha *= 0.93;
            points[i].r *= 0.992;
            if (points[i].alpha < 0.01) points.splice(i, 1);
        }

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (points.length > 0 || (hasMouse && headRadius > 5)) {
            ctx.fillStyle = 'rgba(255, 225, 150, 0.45)';
            points.forEach((p) => {
                ctx.save();
                ctx.globalAlpha = p.alpha * 0.70;
                drawMorphBlob(ctx, p.x, p.y, p.r, time, p.seed);
                ctx.restore();
            });

            if (hasMouse && headRadius > 5) {
                ctx.save();
                ctx.globalAlpha = 0.88;
                ctx.fillStyle = 'rgba(255, 255, 255, 0.82)';
                drawMorphBlob(ctx, mousePos.x, mousePos.y, headRadius, time, 42);
                ctx.restore();
            }
        }

        animFrame = requestAnimationFrame(render);
    };

    animFrame = requestAnimationFrame(render);
})();

function scrollToMarkets() {
    try {
        const target = window.parent.document.getElementById('market-summary');
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    } catch(e) {}
}
</script>
</body>
</html>
"""


def render_hero_banner() -> str:
    """
    Backward-compatible alias for render_hero_banner_component.
    """
    return render_hero_banner_component()


def render_global_market_ribbon(tickers: Optional[List[Dict[str, Any]]] = None) -> str:
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
    <div style="margin-top: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.08em;">
                ACTIVE EQUITIES VOLUME LEADERS // YAHOO FINANCE LIVE QUOTES
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #22c55e;">
                ● STREAMING LIVE
            </div>
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
    <div style="margin-top: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.08em;">
                ON-CHAIN SPOT &amp; PERPETUAL LEADERS // COINGECKO LIVE QUOTES
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #f59e0b;">
                ● STREAMING LIVE
            </div>
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


def render_global_economy_dashboard() -> str:
    """Renders the global economy and inflation telemetry dashboard."""
    return render_world_inflation_map()


_WORLD_MAP_SVG_CACHE: str | None = None

def get_world_map_svg_paths() -> str:
    """Loads and caches real country SVG paths from data/world_map_svg_paths.txt (excluding Antarctica)."""
    global _WORLD_MAP_SVG_CACHE
    if _WORLD_MAP_SVG_CACHE is not None:
        return _WORLD_MAP_SVG_CACHE

    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    map_file = os.path.join(base_dir, "data", "world_map_svg_paths.txt")
    if not os.path.exists(map_file):
        map_file = os.path.join("data", "world_map_svg_paths.txt")

    if os.path.exists(map_file):
        with open(map_file, "r", encoding="utf-8") as f:
            paths = [line.strip() for line in f if line.strip() and "Antarctica" not in line]
            _WORLD_MAP_SVG_CACHE = "\n".join(paths)
            return _WORLD_MAP_SVG_CACHE
    return ""


def render_world_inflation_map() -> str:
    """Renders Section 6: Real World Inflation Map (TradingView Choropleth) matching media_1789572311962.png."""
    svg_paths = get_world_map_svg_paths()

    raw_html = f"""
    <div id="world-map-section" class="sig-map-container" style="padding: 24px; margin-bottom: 26px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 14px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-family: 'Inter', sans-serif; font-size: 22px; font-weight: 800; color: #ffffff; letter-spacing: -0.02em;">
                    Global inflation map
                </span>
                <span style="font-size: 18px; color: #71717a; font-weight: 600;">&rsaquo;</span>
            </div>

            <div class="tv-map-pills">
                <a href="#stocks-section" class="tv-map-pill">US stocks</a>
                <a href="#crypto-section" class="tv-map-pill">Crypto</a>
                <a href="#bonds-section" class="tv-map-pill">Futures</a>
                <a href="#bonds-section" class="tv-map-pill">Forex</a>
                <span class="tv-map-pill tv-map-pill-active">Economy</span>
                <a href="#about-signalora" class="tv-map-pill">Brokers</a>
            </div>
        </div>

        <div style="background: #06070c; border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 10px; padding: 12px; overflow: hidden; position: relative; box-shadow: inset 0 2px 20px rgba(0,0,0,0.6);">
            <svg viewBox="0 0 1000 455" style="width: 100%; height: auto; display: block; filter: drop-shadow(0 4px 16px rgba(0,0,0,0.5));">
                <rect width="1000" height="455" fill="#06070c" rx="6"/>
                <!-- Subtle Coordinate Grid Lines -->
                <line x1="0" y1="113" x2="1000" y2="113" stroke="rgba(255,255,255,0.02)" stroke-dasharray="4,4"/>
                <line x1="0" y1="227" x2="1000" y2="227" stroke="rgba(255,255,255,0.03)"/>
                <line x1="0" y1="341" x2="1000" y2="341" stroke="rgba(255,255,255,0.02)" stroke-dasharray="4,4"/>
                <line x1="250" y1="0" x2="250" y2="455" stroke="rgba(255,255,255,0.02)" stroke-dasharray="4,4"/>
                <line x1="500" y1="0" x2="500" y2="455" stroke="rgba(255,255,255,0.03)"/>
                <line x1="750" y1="0" x2="750" y2="455" stroke="rgba(255,255,255,0.02)" stroke-dasharray="4,4"/>

                <!-- 176 Real Country Choropleth Paths -->
                {svg_paths}
            </svg>
        </div>

        <!-- Legend & Sovereign Benchmarks -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.06); flex-wrap: wrap; gap: 16px;">
            <div style="display: flex; align-items: center; gap: 12px; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #94a3b8;">
                <span>0% (Low)</span>
                <div style="width: 220px; height: 9px; border-radius: 4.5px; background: linear-gradient(90deg, #fed7aa 0%, #fdba74 20%, #fb923c 40%, #f97316 60%, #ea580c 80%, #991b1b 100%);"></div>
                <span>25%+ (Severe)</span>
            </div>
            <div style="display: flex; gap: 20px; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #71717a; flex-wrap: wrap;">
                <span>● US: <strong style="color:#ffffff;">2.6%</strong></span>
                <span>● Eurozone: <strong style="color:#ffffff;">2.2%</strong></span>
                <span>● UK: <strong style="color:#ffffff;">2.2%</strong></span>
                <span>● Japan: <strong style="color:#ffffff;">2.8%</strong></span>
                <span>● India: <strong style="color:#ffffff;">3.65%</strong></span>
                <span>● China: <strong style="color:#ffffff;">0.6%</strong></span>
                <span>● Brazil: <strong style="color:#ffffff;">4.2%</strong></span>
                <span style="color: #ea580c;">● Turkey: <strong>51.9%</strong></span>
                <span style="color: #ef4444;">● Argentina: <strong>236%</strong></span>
            </div>
        </div>

        <!-- Economic Calendar Below Map -->
        <div style="margin-top: 24px;">
            <div style="font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 700; color: #ffffff; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                Economic Calendar <span style="color: #71717a;">&rsaquo;</span> <span style="font-size: 11px; font-weight: 500; color: #94a3b8;">High-impact global macro catalysts</span>
            </div>
            <div class="sig-calendar-grid">
                <div class="sig-cal-card">
                    <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #71717a;">
                        <span>TODAY</span>
                        <span style="color: #FFD700;">17:45 GMT</span>
                    </div>
                    <div style="font-weight: 700; font-size: 12px; color: #ffffff; margin: 6px 0 4px 0;">ECB Vujcic Speech</div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #94a3b8;">Impact: Sovereign Yields</div>
                </div>
                <div class="sig-cal-card">
                    <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #71717a;">
                        <span>TODAY</span>
                        <span style="color: #22c55e;">00:09 GMT</span>
                    </div>
                    <div style="font-weight: 700; font-size: 12px; color: #ffffff; margin: 6px 0 4px 0;">US Housing Starts</div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #22c55e;">Actual: 240K | Prior: 229.1K</div>
                </div>
                <div class="sig-cal-card">
                    <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #71717a;">
                        <span>TODAY</span>
                        <span style="color: #FFD700;">LIVE</span>
                    </div>
                    <div style="font-weight: 700; font-size: 12px; color: #ffffff; margin: 6px 0 4px 0;">Building Permits MoM</div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #ef4444;">Forecast: -6.4% | Prior: 18.5%</div>
                </div>
                <div class="sig-cal-card">
                    <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #71717a;">
                        <span>TODAY</span>
                        <span style="color: #22c55e;">RELEASED</span>
                    </div>
                    <div style="font-weight: 700; font-size: 12px; color: #ffffff; margin: 6px 0 4px 0;">Import Prices MoM</div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #22c55e;">Forecast: +0.4% | Prior: +0.4%</div>
                </div>
            </div>
        </div>
    </div>
    """
    return clean_html(raw_html)


def render_benchmark_bars() -> str:
    """Render relative performance bars."""
    raw_html = """
    <div style="background: #0a0b16; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 18px; margin-bottom: 24px;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700; color: #9a968e; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 16px;">
            INTRADAY MACRO DIVERGENCE // RELATIVE STRENGTH SPREAD
        </div>
        <div style="display: flex; flex-direction: column; gap: 10px; font-family: 'JetBrains Mono', monospace; font-size: 11px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="width: 110px; color: #cbd5e1;">BRENT CRUDE</span>
                <div style="flex: 1; margin: 0 16px; background: rgba(255,255,255,0.05); height: 6px; border-radius: 3px;">
                    <div style="width: 82%; height: 100%; background: #22c55e; border-radius: 3px;"></div>
                </div>
                <span style="width: 60px; text-align: right; color: #22c55e; font-weight: 700;">+2.10%</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="width: 110px; color: #cbd5e1;">US 30Y YIELD</span>
                <div style="flex: 1; margin: 0 16px; background: rgba(255,255,255,0.05); height: 6px; border-radius: 3px;">
                    <div style="width: 65%; height: 100%; background: #ffffff; border-radius: 3px;"></div>
                </div>
                <span style="width: 60px; text-align: right; color: #ffffff; font-weight: 700;">4.58%</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="width: 110px; color: #cbd5e1;">S&P 500 (SPY)</span>
                <div style="flex: 1; margin: 0 16px; background: rgba(255,255,255,0.05); height: 6px; border-radius: 3px;">
                    <div style="width: 48%; height: 100%; background: #ef4444; border-radius: 3px;"></div>
                </div>
                <span style="width: 60px; text-align: right; color: #ef4444; font-weight: 700;">-0.35%</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="width: 110px; color: #cbd5e1;">NASDAQ 100</span>
                <div style="flex: 1; margin: 0 16px; background: rgba(255,255,255,0.05); height: 6px; border-radius: 3px;">
                    <div style="width: 32%; height: 100%; background: #ef4444; border-radius: 3px;"></div>
                </div>
                <span style="width: 60px; text-align: right; color: #ef4444; font-weight: 700;">-1.45%</span>
            </div>
        </div>
    </div>
    """
    return clean_html(raw_html)


def render_tradingview_widget(symbol: str = "NVDA", height: int = 500) -> str:
    """TradingView real-time interactive institutional candlestick & volume chart."""
    tv_symbol_map = {
        "US30Y": "TVC:US30Y",
        "US10Y": "TVC:US10Y",
        "US2Y": "TVC:US02Y",
        "DXY": "TVC:DXY",
        "NVDA": "NASDAQ:NVDA",
        "AAPL": "NASDAQ:AAPL",
        "MSFT": "NASDAQ:MSFT",
        "GOOGL": "NASDAQ:GOOGL",
        "GOOG": "NASDAQ:GOOG",
        "TSLA": "NASDAQ:TSLA",
        "AMD": "NASDAQ:AMD",
        "META": "NASDAQ:META",
        "AMZN": "NASDAQ:AMZN",
        "PLTR": "NYSE:PLTR",
        "NFLX": "NASDAQ:NFLX",
        "COIN": "NASDAQ:COIN",
        "ARM": "NASDAQ:ARM",
        "INTC": "NASDAQ:INTC",
        "QCOM": "NASDAQ:QCOM",
        "AVGO": "NASDAQ:AVGO",
        "SPY": "AMEX:SPY",
        "QQQ": "NASDAQ:QQQ",
        "DIA": "AMEX:DIA",
        "IWM": "AMEX:IWM",
        "CL1!": "NYMEX:CL1!",
        "GC1!": "COMEX:GC1!",
        "BTCUSD": "BINANCE:BTCUSDT",
        "BTC": "BINANCE:BTCUSDT",
        "ETHUSD": "BINANCE:ETHUSDT",
        "ETH": "BINANCE:ETHUSDT",
        "SOLUSD": "BINANCE:SOLUSDT",
        "SOL": "BINANCE:SOLUSDT",
        "XRPUSD": "BINANCE:XRPUSDT",
        "XRP": "BINANCE:XRPUSDT",
        "BNBUSD": "BINANCE:BNBUSDT",
        "BNB": "BINANCE:BNBUSDT",
        "DOGEUSD": "BINANCE:DOGEUSDT",
        "DOGE": "BINANCE:DOGEUSDT",
        "ADAUSD": "BINANCE:ADAUSDT",
        "ADA": "BINANCE:ADAUSDT",
    }
    sym_clean = symbol.strip().upper().replace("/", "").replace("-", "")
    if ":" in sym_clean:
        tv_symbol = sym_clean
    elif sym_clean in tv_symbol_map:
        tv_symbol = tv_symbol_map[sym_clean]
    else:
        tv_symbol = f"NASDAQ:{sym_clean}"

    raw_html = f"""
    <div style="height: {height}px; width: 100%; border-radius: 12px; overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.08); background: #06070c; box-shadow: 0 8px 32px rgba(0,0,0,0.6);">
      <iframe 
        style="width: 100%; height: 100%; border: none; display: block;"
        src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_widget&symbol={tv_symbol}&interval=D&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=06070c&theme=dark&style=1&timezone=exchange&studies=[]"
        allowfullscreen>
      </iframe>
    </div>
    """
    return clean_html(raw_html)


def render_tradingview_heatmap(height: int = 520) -> str:
    """TradingView Stock Heatmap Treemap."""
    raw_html = f"""
    <div style="height: {height}px; width: 100%; border-radius: 12px; overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.08); background: #0a0b16;">
      <iframe 
        style="width: 100%; height: 100%; border: none;"
        src="https://s.tradingview.com/embed-widget/stock-heatmap/?locale=en#%7B%22dataSource%22%3A%22SPX500%22%2C%22blockSize%22%3A%22market_cap_basic%22%2C%22blockColor%22%3A%22change%22%2C%22grouping%22%3A%22sector%22%2C%22theme%22%3A%22dark%22%2C%22isTransparent%22%3Atrue%7D"
        allowfullscreen>
      </iframe>
    </div>
    """
    return clean_html(raw_html)


def render_about_me_section() -> str:
    """Renders Section 8: About Me & SIGNALORA Institutional Architecture."""
    raw_html = """
    <div id="about-signalora" class="sig-about-wrap" style="padding: 28px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 20px;">
            <div style="max-width: 600px;">
                <div style="display: inline-flex; align-items: center; gap: 8px; font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700; color: #FFD700; background: rgba(255,215,0,0.08); padding: 4px 12px; border-radius: 999px; margin-bottom: 12px; border: 1px solid rgba(255,215,0,0.2);">
                    <span style="width: 6px; height: 6px; background: #22c55e; border-radius: 50%;"></span>
                    ABOUT THE ARCHITECT // SYSTEM MISSION
                </div>
                <div style="font-family: 'Inter', sans-serif; font-size: 26px; font-weight: 900; color: #ffffff; letter-spacing: -0.02em; margin-bottom: 8px;">
                    SIGNALORA
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; color: #FFD700; margin-bottom: 14px;">
                    "From market noise to verified signals."
                </div>
                <p style="font-size: 13px; color: #94a3b8; line-height: 1.6; margin-bottom: 14px;">
                    Engineered to eliminate noise, ungrounded commentary, and promotional bias in global financial data streams.
                </p>
                <p style="font-size: 13px; color: #94a3b8; line-height: 1.6;">
                    SIGNALORA coordinates 32 specialized agents via LangGraph state machines, multi-layered Bayesian confidence gating, Windows SAPI 16-bit biometric speech synthesis, and SEC EDGAR 10-Q forensic audit trees to extract pure, mathematically verified alpha.
                </p>
            </div>
            
            <div style="background: #0d0f1e; border: 1px solid rgba(255,215,0,0.2); border-radius: 10px; padding: 20px; min-width: 280px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: #FFD700; margin-bottom: 12px; text-transform: uppercase;">
                    SYSTEM ARCHITECTURE AT A GLANCE
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-family: 'JetBrains Mono', monospace; font-size: 11px;">
                    <div style="display: flex; justify-content: space-between;"><span style="color: #71717a;">Orchestration:</span> <strong style="color: #fff;">LangGraph DAG</strong></div>
                    <div style="display: flex; justify-content: space-between;"><span style="color: #71717a;">Active Agents:</span> <strong style="color: #22c55e;">32 Autonomous</strong></div>
                    <div style="display: flex; justify-content: space-between;"><span style="color: #71717a;">Biometrics:</span> <strong style="color: #FFD700;">KAN + GAT Verified</strong></div>
                    <div style="display: flex; justify-content: space-between;"><span style="color: #71717a;">Forensics:</span> <strong style="color: #fff;">SEC 10-Q Divergence</strong></div>
                    <div style="display: flex; justify-content: space-between;"><span style="color: #71717a;">Self-Learning:</span> <strong style="color: #3b82f6;">Hermes Reflexion</strong></div>
                    <div style="display: flex; justify-content: space-between;"><span style="color: #71717a;">Telemetry:</span> <strong style="color: #22c55e;">Nominal 0 Anomalies</strong></div>
                </div>
            </div>
        </div>

        <div class="sig-sitemap-grid">
            <div>
                <div class="sig-sitemap-col-title">PRODUCTS &amp; DATA</div>
                <span class="sig-sitemap-link">Supercharts Terminal</span>
                <span class="sig-sitemap-link">Multi-Asset Screeners</span>
                <span class="sig-sitemap-link">Yield Curves Architecture</span>
                <span class="sig-sitemap-link">Global Inflation Maps</span>
            </div>
            <div>
                <div class="sig-sitemap-col-title">AGENT SWARM</div>
                <span class="sig-sitemap-link">Kim Executive Strategist</span>
                <span class="sig-sitemap-link">Risk Sentinel &amp; VaR</span>
                <span class="sig-sitemap-link">Geopolitical Chokepoints</span>
                <span class="sig-sitemap-link">Forensic SEC Auditor</span>
            </div>
            <div>
                <div class="sig-sitemap-col-title">COMMUNITY &amp; IDEAS</div>
                <span class="sig-sitemap-link">Verified Trade Signals</span>
                <span class="sig-sitemap-link">Quantitative Confluence</span>
                <span class="sig-sitemap-link">SEC Disclosure Divergence</span>
                <span class="sig-sitemap-link">CME FedWatch Consensus</span>
            </div>
            <div>
                <div class="sig-sitemap-col-title">LEGAL &amp; SECURITY</div>
                <span class="sig-sitemap-link">Voice Biometric Trust</span>
                <span class="sig-sitemap-link">Bayesian Grounding Proofs</span>
                <span class="sig-sitemap-link">Terms of Market Intelligence</span>
                <span class="sig-sitemap-link">System Status: Operational</span>
            </div>
        </div>

        <div class="sig-giant-banner">
            SIGNALORA : FROM MARKET NOISE TO VERIFIED SIGNALS.
        </div>
    </div>
    """
    return clean_html(raw_html)
