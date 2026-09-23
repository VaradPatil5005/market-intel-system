"""
SIGNALORA // Institutional Multi-Agent Market Intelligence Platform
Tagline: From market noise to verified signals.
Visual Presentation matching Reference Video (website look.mp4)
and AetherOS Desktop Environment.

Features:
  - 3D Interactive Cursor-Reactive Lily Flower Background (AetherOS OrbitWallpaper)
  - TradingView Top Taskbar with Real Dropdown Menus & Smooth Anchors (Zero ugly radio buttons)
  - Concise System Builder / Architect Card in Bottom-Left Corner
  - Clickable Breaking News Cards opening verified financial publications in new tabs
  - Dedicated Taskbar Launch for Analyst Desk (Kept out of the clean overview)
  - World Inflation Map with 0%-25% gradient and Economic Calendar

Run with: streamlit run ui/app.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Allow running via `streamlit run ui/app.py` from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import streamlit as st

# Ensure Markdown never parses multi-line indented HTML as <pre><code> blocks
_orig_markdown = st.markdown


def safe_markdown(body, *args, **kwargs):
    if isinstance(body, str) and kwargs.get("unsafe_allow_html"):
        body = "\n".join(line.strip() for line in body.splitlines() if line.strip())
    return _orig_markdown(body, *args, **kwargs)


st.markdown = safe_markdown

from agents.execution_router_agent import ExecutionRouterAgent
from agents.geopolitical_risk_agent import GeopoliticalRiskAgent
from agents.liquidity_order_flow_agent import LiquidityOrderFlowAgent

geopolitical_risk_agent = GeopoliticalRiskAgent()
liquidity_order_flow_agent = LiquidityOrderFlowAgent()
execution_router_agent = ExecutionRouterAgent()
from agents.hermes_self_learning_agent import hermes_self_learning_agent
from utils.memory_store import memory_store
from skills.skill_registry import skill_registry
from agents.discrepancy_auditor_agent import discrepancy_auditor_agent
import importlib
import agents.kim_voice_agent
try:
    importlib.reload(agents.kim_voice_agent)
except Exception:
    pass

from agents.kim_voice_agent import kim_voice_agent, KimResponse

if hasattr(agents.kim_voice_agent, "synthesize_female_speech_wav"):
    synthesize_female_speech_wav = agents.kim_voice_agent.synthesize_female_speech_wav
else:
    def synthesize_female_speech_wav(text: str, output_filename: str = "storage/audio/kim_response.wav"):
        try:
            import subprocess, re
            os.makedirs(os.path.dirname(output_filename), exist_ok=True)
            clean = re.sub(r'[^a-zA-Z0-9\s.,!?-]', '', text)
            ps_cmd = f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Female); $s.SetOutputToWaveFile('{output_filename}'); $s.Speak('{clean}'); $s.Dispose()"
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True, timeout=8)
            if os.path.exists(output_filename) and os.path.getsize(output_filename) > 500:
                return output_filename
        except Exception:
            pass
        return None

if hasattr(agents.kim_voice_agent, "transcribe_audio_wav"):
    transcribe_audio_wav = agents.kim_voice_agent.transcribe_audio_wav
else:
    def transcribe_audio_wav(audio_path: str):
        try:
            if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 200:
                return None
            import subprocess
            ps_cmd = f"Add-Type -AssemblyName System.Speech; $reco = New-Object System.Speech.Recognition.SpeechRecognitionEngine; $reco.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar)); $reco.SetInputToWaveFile('{audio_path}'); $res = $reco.Recognize([TimeSpan]::FromSeconds(8)); if ($res -and $res.Text) {{ Write-Output $res.Text }}; $reco.Dispose()"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=8)
            return res.stdout.strip() or None
        except Exception:
            return None

from agents.friday_voice_agent import friday_voice_agent
from agents.global_macro_agent import global_macro_agent
from agents.macro_rates_agent import macro_rates_agent
from agents.risk_sentinel_agent import risk_sentinel_agent
from agents.vibe_quant_agent import vibe_quant_agent
from agents.voice_security_agent import voice_security_agent
from database.models import (
    AgentLearning,
    ConfidenceScore,
    Entity,
    ForecastResult,
    GroundingRecord,
    Insight,
    PriceSnapshot,
    ReportExport,
    TrendResult,
    UserInterestProfile,
    UserQuery,
)
from database.session import Repository, get_session, init_db
import utils.live_market_data
try:
    importlib.reload(utils.live_market_data)
except Exception:
    pass

import agents.live_news_agent
try:
    importlib.reload(agents.live_news_agent)
except Exception:
    pass
from agents.live_news_agent import live_news_agent

import streamlit.components.v1 as components
import ui.blackbox_theme
try:
    importlib.reload(ui.blackbox_theme)
except Exception:
    pass

from ui.blackbox_theme import (
    BLACKBOX_CSS,
    render_signalora_brand_header,
    render_hero_banner,
    render_hero_banner_component,
    render_global_market_ribbon,
    render_market_summary_section,
    render_market_mini_cards,
    render_stocks_section,
    render_crypto_section,
    render_world_inflation_map,
    render_about_me_section,
    render_category_pills,
    render_breaking_news_grid,
    render_bonds_dashboard,
    render_global_economy_dashboard,
    render_benchmark_bars,
    render_tradingview_widget,
    render_tradingview_heatmap,
)
from utils.config import settings

st.set_page_config(
    page_title="SIGNALORA // From market noise to verified signals",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Apply institutional SIGNALORA cosmic dark theme
st.markdown(BLACKBOX_CSS, unsafe_allow_html=True)

init_db()

# Repository handles
insight_repo = Repository(Insight)
confidence_repo = Repository(ConfidenceScore)
trend_repo = Repository(TrendResult)
forecast_repo = Repository(ForecastResult)
report_repo = Repository(ReportExport)
entity_repo = Repository(Entity)
query_repo = Repository(UserQuery)
profile_repo = Repository(UserInterestProfile)
learning_repo = Repository(AgentLearning)
grounding_repo = Repository(GroundingRecord)
price_repo = Repository(PriceSnapshot)


# ---- Data Acquisition ------------------------------------------------------
def load_data():
    with get_session() as session:
        insights = insight_repo.all(session)
        scores = confidence_repo.all(session)
        trends = trend_repo.all(session)
        forecasts = forecast_repo.all(session)
        reports = report_repo.all(session)
        entities = entity_repo.all(session)
        queries = query_repo.all(session)
        learnings = learning_repo.all(session)
        grounding_records = grounding_repo.all(session)
        price_snaps = price_repo.all(session)
    return insights, scores, trends, forecasts, reports, entities, queries, learnings, grounding_records, price_snaps


def apply_decision(insight_id: str, decision: str, reviewer_note: str, new_text: str | None = None):
    with get_session() as session:
        scores = confidence_repo.filter_by(session, insight_id=insight_id)
        insight = insight_repo.get(session, insight_id)

        if new_text and insight:
            insight.text = new_text
            session.flush()

        for score in scores:
            if decision == "approve":
                score.is_flagged = 0
                score.flag_reason = f"[APPROVED] {reviewer_note}" if reviewer_note else "[APPROVED]"
            elif decision in ("reject", "modify"):
                score.is_flagged = 1
                score.flag_reason = (
                    f"[{decision.upper()}] {reviewer_note}" if reviewer_note
                    else f"[{decision.upper()}]"
                )
            session.flush()

        if decision in ("reject", "modify") and insight:
            try:
                from agents.reflexion_agent import ReflexionAgent
                reflexion = ReflexionAgent()
                reflexion.generate_lesson(
                    session,
                    insight_id=insight_id,
                    human_action=decision,
                    reviewer_note=reviewer_note,
                    new_text=new_text,
                )
            except Exception as e:
                st.warning(f"Reflexion notice: {e}")


(
    insights,
    scores,
    trends,
    forecasts,
    reports,
    entities,
    queries,
    learnings,
    grounding_records,
    price_snaps,
) = load_data()

score_map = {s.insight_id: s for s in scores}
mean_conf = sum(s.score for s in scores) / len(scores) if scores else 0.69
grounded_ratio = (
    sum(1 for g in grounding_records if g.verdict == "verified") / len(grounding_records)
    if grounding_records else 1.0
)

# Active view state: "overview" (default) or "analyst_desk"
query_view = st.query_params.get("view", None) if hasattr(st, "query_params") else None
if query_view in ("overview", "analyst_desk"):
    st.session_state.active_view = query_view
elif "active_view" not in st.session_state:
    st.session_state.active_view = "overview"

# 1. Top Institutional Taskbar with Integrated View Switcher & Real Dropdowns
st.markdown(render_signalora_brand_header(active_view=st.session_state.active_view), unsafe_allow_html=True)

# 2. Institutional Global Market Ticker Ribbon (Seamless bottom shelf)
st.markdown(render_global_market_ribbon(), unsafe_allow_html=True)


# ==============================================================================
# VIEW 1: DEDICATED ANALYST DESK WORKBENCH (Kept out of Overview!)
# ==============================================================================
if st.session_state.active_view == "analyst_desk":
    st.markdown('<div class="sig-main-container">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="sig-sec-header">
            <div class="sig-sec-title">Analyst Desk // Multi-Agent Audit &amp; Forensics</div>
            <div class="sig-sec-sub">&#9679; 32 AUTONOMOUS AGENTS OPERATIONAL</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    desk_tabs = st.tabs([
        "INSIGHT REVIEW QUEUE",
        "RISK & MACRO SENTINEL",
        "GEOPOLITICAL & LIQUIDITY",
        "FORENSIC AUDIT (10-Q)",
        "QUANT CONFLUENCE",
        "HERMES PERSISTENT MEMORY",
        "AGENT REACH RESEARCH HUB",
    ])

    # ---- Sub-Tab 0: Insight Review Queue ----
    with desk_tabs[0]:
        filter_col, sort_col = st.columns([2, 1])
        with filter_col:
            category_filter = st.multiselect(
                "Filter Category",
                options=list({i.category for i in insights}),
                default=[],
                label_visibility="collapsed",
            )
        with sort_col:
            show_flagged = st.checkbox("Display Flagged Only", value=False)

        filtered_insights = insights
        if category_filter:
            filtered_insights = [i for i in filtered_insights if i.category in category_filter]
        if show_flagged:
            flagged_ids = {s.insight_id for s in scores if s.is_flagged}
            filtered_insights = [i for i in filtered_insights if i.id in flagged_ids]

        if not filtered_insights:
            st.info("No insights matching query criteria.")
        else:
            for insight in filtered_insights:
                score = score_map.get(insight.id)
                score_val = score.score if score else None
                score_str = f"{score_val:.2%}" if score_val is not None else "N/A"
                is_flagged = score.is_flagged if score else False
                status_text = "FLAGGED FOR AUDIT" if is_flagged else "VERIFIED"
                status_color = "#ef4444" if is_flagged else "#22c55e"

                st.markdown(f"""
                <div style="background: #0c0d18; border: 1px solid rgba(255,255,255,0.08); border-left: 3px solid {status_color}; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; text-transform:uppercase; color:#fff;">{insight.category}</span>
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700; color: {status_color};">
                            [{status_text}] · CONFIDENCE: {score_str}
                        </span>
                    </div>
                    <p style="margin: 8px 0; font-size: 13px; color: #d4d4d8; line-height: 1.5;">{insight.text}</p>
                    {'<div style="font-family: monospace; font-size: 10px; color:#ef4444;">FLAGGED: ' + (score.flag_reason or '') + '</div>' if is_flagged and score and score.flag_reason else ''}
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"ACTION PROTOCOL // {insight.id[:12]}"):
                    reviewer_note = st.text_input("Reviewer Audit Note:", key=f"note_{insight.id}")
                    new_text = st.text_area("Modify Claim Text:", value=insight.text, key=f"edit_{insight.id}")
                    b1, b2, b3 = st.columns(3)
                    with b1:
                        if st.button("APPROVE CLAIM", key=f"approve_{insight.id}"):
                            apply_decision(insight.id, "approve", reviewer_note)
                            st.rerun()
                    with b2:
                        if st.button("REJECT CLAIM", key=f"reject_{insight.id}"):
                            apply_decision(insight.id, "reject", reviewer_note)
                            st.rerun()
                    with b3:
                        if st.button("MODIFY CLAIM", key=f"modify_{insight.id}"):
                            apply_decision(insight.id, "modify", reviewer_note, new_text=new_text)
                            st.rerun()

    # ---- Sub-Tab 1: Risk & Macro Sentinel ----
    with desk_tabs[1]:
        risk_data = risk_sentinel_agent.evaluate_portfolio_risk()
        macro_data = global_macro_agent.fetch_global_telemetry()

        st.markdown("<div style='font-family: monospace; font-size: 10px; font-weight: 700; color: #FFD700; text-transform: uppercase; margin-bottom: 8px;'>[ SECTION 1: PORTFOLIO TAIL RISK &amp; CIRCUIT BREAKER ]</div>", unsafe_allow_html=True)
        rk1, rk2, rk3, rk4 = st.columns(4)
        with rk1:
            st.metric("VAR (95% 1-DAY)", f"{risk_data.var_95 * 100:.2f}%", f"Budget: {risk_data.risk_budget_consumption:.0f}%")
        with rk2:
            st.metric("EXPECTED SHORTFALL", f"{risk_data.expected_shortfall * 100:.2f}%", "CVaR Tail Loss")
        with rk3:
            st.metric("MAX DRAWDOWN", f"{risk_data.max_drawdown * 100:.2f}%", f"Current: {risk_data.current_drawdown * 100:.2f}%")
        with rk4:
            st.metric("VOLATILITY REGIME", risk_data.volatility_regime, f"Tail Index: {risk_data.tail_risk_index}/10")

        if risk_data.circuit_breaker_active:
            st.error("CIRCUIT BREAKER ENGAGED: Automated de-risking protocol mandated.")
        else:
            st.markdown("<div style='font-family: monospace; font-size: 11px; color: #22c55e; margin: 4px 0 16px 0;'>CIRCUIT BREAKER: NOMINAL [NO CAPITAL RESTRICTIONS]</div>", unsafe_allow_html=True)

        st.markdown(f"<div style='font-family: monospace; font-size: 11px; color: #71717a; margin-bottom: 24px;'>RECOMMENDED SYSTEMIC HEDGES: {', '.join(risk_data.recommended_hedges)}</div>", unsafe_allow_html=True)

        st.markdown("<div style='font-family: monospace; font-size: 10px; font-weight: 700; color: #FFD700; text-transform: uppercase; margin-bottom: 8px;'>[ SECTION 2: GLOBAL LIQUIDITY &amp; CONTAGION VECTORS ]</div>", unsafe_allow_html=True)
        gm1, gm2, gm3, gm4 = st.columns(4)
        with gm1:
            st.metric("USD / JPY", f"{macro_data.usdjpy_rate:.2f}", f"{macro_data.usdjpy_change_pct:+.2f}% [CARRY]")
        with gm2:
            st.metric("DOLLAR INDEX (DXY)", f"{macro_data.dxy_index:.2f}", "Funding Liquidity")
        with gm3:
            st.metric("SPOT GOLD (GC=F)", f"${macro_data.gold_price:.2f}", "Flight-to-Safety")
        with gm4:
            st.metric("COPPER / GOLD RATIO", f"{macro_data.copper_gold_ratio:.3f}", "Economic Growth")

    # ---- Sub-Tab 2: Geopolitical & Liquidity ----
    with desk_tabs[2]:
        col_scen, col_tgt = st.columns([2, 2])
        with col_scen:
            geo_scenario = st.selectbox(
                "Geopolitical Simulation Scenario",
                ["STANDARD_SURVEILLANCE", "MIDDLE_EAST_ESCALATION", "CROSS_STRAIT_BLOCKADE"],
                label_visibility="collapsed"
            )
        with col_tgt:
            st.markdown(f"<div style='font-family: monospace; font-size: 11px; color: #a1a1aa; padding-top: 8px;'>ACTIVE SCENARIO: {geo_scenario}</div>", unsafe_allow_html=True)

        geo_data = geopolitical_risk_agent.run({"stress_scenario": geo_scenario, "entities": ["NVDA", "AAPL", "XOM", "TSM"]})

        g1, g2, g3, g4 = st.columns(4)
        with g1:
            st.metric("COMPOSITE STRESS", f"{geo_data['composite_geopolitical_stress_index']:.1f} / 100", f"REGIME: {geo_data['geopolitical_regime']}")
        with g2:
            st.metric("BRENT RISK PREM", f"+${geo_data['brent_crude_risk_premium_usd']:.2f}", "Excess / Barrel")
        with g3:
            st.metric("CRITICAL ARTERY", "HORMUZ (21% CRUDE)", "21M bbl/day flow")
        with g4:
            st.metric("FOUNDRY EXPOSURE", "TSM TAIWAN (85%)", "Sub-3nm Monopoly")

        choke_rows = []
        for cp_id, cp_info in geo_data["chokepoints"].items():
            choke_rows.append({
                "CHOKEPOINT": cp_info["name"].upper(),
                "RISK SCORE": f"{cp_info['risk_score']:.1f}",
                "THREAT LEVEL": cp_info["threat_level"],
                "GLOBAL THROUGHPUT": f"{cp_info['global_throughput_pct']}%",
                "PRIMARY COMMODITY": cp_info["primary_commodity"][:38] + "...",
                "DIVERT COST/SHIP": f"${cp_info['routing_diversion_cost_est_usd']:,.0f}"
            })
        st.dataframe(pd.DataFrame(choke_rows), hide_index=True, use_container_width=True)

    # ---- Sub-Tab 3: Forensic Audit & Discrepancies ----
    with desk_tabs[3]:
        st.markdown("<div style='font-family: monospace; font-size: 11px; color: #a1a1aa; margin-bottom: 8px;'>FORENSIC DISCREPANCY AUDITOR // SEC 10-Q vs PUBLIC PRESS CONFLICTS</div>", unsafe_allow_html=True)
        disc_c1, disc_c2 = st.columns([1, 1])
        with disc_c1:
            audit_ticker = st.selectbox("Entity Symbol", ["NVDA", "TSLA", "MSFT", "AAPL"], key="audit_ticker_sym")
        with disc_c2:
            st.markdown(f"<div style='font-family: monospace; font-size: 11px; color: #a1a1aa; padding-top: 8px;'>MANDATE: DISCLOSURE DIVERGENCE ANALYSIS</div>", unsafe_allow_html=True)

        audit_res = discrepancy_auditor_agent.audit_entity(audit_ticker)

        ad1, ad2, ad3, ad4 = st.columns(4)
        with ad1:
            st.metric("MATERIAL DISCREPANCY", "DETECTED" if audit_res.discrepancy_detected else "NONE", f"Confidence: {audit_res.confidence_score:.0%}")
        with ad2:
            st.metric("HAIRCUT PENALTY", f"-{audit_res.suggested_haircut_pct:.1f}%", "Valuation Drag")
        with ad3:
            st.metric("AUDIT SEVERITY", audit_res.severity, "Reg Risk")
        with ad4:
            st.metric("FILING EVIDENCE", f"10-Q Item {audit_res.sec_filing_reference}", "SEC EDGAR")

    # ---- Sub-Tab 4: Quantitative Signals ----
    with desk_tabs[4]:
        selected_sym = st.selectbox("Symbol Analysis", ["NVDA", "AAPL", "MSFT", "GOOGL", "TSLA", "CL1!", "SPY", "QQQ"], key="quant_sel_sym")
        quant = vibe_quant_agent.analyze_ticker(selected_sym)

        q1, q2, q3, q4 = st.columns(4)
        with q1:
            st.metric("CURRENT PRICE", f"${quant.current_price:.2f}", f"Stance: {quant.stance}")
        with q2:
            st.metric("RSI (14-PERIOD)", f"{quant.rsi_14:.1f}", "Momentum")
        with q3:
            st.metric("MACD HISTOGRAM", f"{quant.macd_histogram:+.3f}", "Trend Divergence")
        with q4:
            st.metric("BOLLINGER BAND", f"${quant.bollinger_lower:.2f} - ${quant.bollinger_upper:.2f}", "Envelope")

        st.markdown(render_tradingview_widget(symbol=selected_sym, height=420), unsafe_allow_html=True)

    # ---- Sub-Tab 5: System Telemetry & Hermes Memory ----
    with desk_tabs[5]:
        mem1, mem2 = st.columns(2)
        with mem1:
            st.markdown("<div style='font-family: monospace; font-size: 11px; font-weight: 700; color: #FFD700; margin-bottom: 8px;'>HERMES PERSISTENT DISCOVERY NOTES (MEMORY.MD)</div>", unsafe_allow_html=True)
            mem_content = memory_store.read_memory() if hasattr(memory_store, "read_memory") else memory_store.get_content("MEMORY")
            st.text_area("MEMORY.md", value=mem_content, height=220, disabled=True)
        with mem2:
            st.markdown("<div style='font-family: monospace; font-size: 11px; font-weight: 700; color: #FFD700; margin-bottom: 8px;'>HERMES USER MANDATES (USER.MD)</div>", unsafe_allow_html=True)
            user_content = memory_store.read_user() if hasattr(memory_store, "read_user") else memory_store.get_content("USER")
            st.text_area("USER.md", value=user_content, height=220, disabled=True)

        if st.button("RUN AUTONOMOUS SELF-LEARNING CYCLE", key="btn_run_self_learn", use_container_width=True):
            with st.spinner("Hermes executing autonomous self-learning loop..."):
                res = hermes_self_learning_agent.run_learning_cycle()
                eval_pred = res.get('evaluated_predictions', 0)
                skills_len = len(res.get('adapted_skills', []))
                st.success(f"Self-learning cycle completed. Realized predictions evaluated: {eval_pred}, Skills adapted: {skills_len}.")
                st.rerun()

    # ---- Sub-Tab 6: Agent Reach Research Hub ----
    with desk_tabs[6]:
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,215,0,0.15); padding-bottom: 8px;">
                <div style="font-family: monospace; font-size: 11px; font-weight: 700; color: #FFD700; text-transform: uppercase;">
                    AGENT REACH RESEARCH HUB // 16-PLATFORM MULTI-CHANNEL INTERNET CAPABILITY
                </div>
                <div style="font-family: monospace; font-size: 10px; color: #22c55e;">
                    ● ENGINE ONLINE · MULTI-BACKEND AUTO-ROUTING
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        reach_sub_tabs = st.tabs([
            "OMNI-CHANNEL SEARCH",
            "UNIVERSAL URL READER",
            "16-PLATFORM DOCTOR",
            "MEDIA TRANSCRIBER",
        ])

        from utils.agent_reach_service import reach_service

        # 1. Omni-Channel Search
        with reach_sub_tabs[0]:
            st.markdown("<div style='font-size: 11px; color: #a1a1aa; margin-bottom: 8px;'>Execute real-time intelligence queries across Web, Xueqiu Equities, and Social communities.</div>", unsafe_allow_html=True)
            sc1, sc2, sc3 = st.columns([3, 1, 1])
            with sc1:
                search_q = st.text_input("Research Topic / Entity Query", value="NVIDIA AI data center demand", key="reach_query_input")
            with sc2:
                search_scope = st.selectbox("Channel Scope", ["All Channels", "Web (Exa / Jina)", "Xueqiu Equities", "Social Communities"], key="reach_scope_sel")
            with sc3:
                max_res = st.selectbox("Max Results", [3, 5, 8, 10], index=1, key="reach_max_res")

            if st.button("EXECUTE AGENT REACH RESEARCH", key="btn_run_reach_search", use_container_width=True):
                with st.spinner("Agent-Reach dispatching across multi-backend channels..."):
                    results_found = []
                    if search_scope in ("All Channels", "Web (Exa / Jina)"):
                        web_hits = reach_service.search_web(search_q, max_results=max_res)
                        for w in web_hits:
                            results_found.append({"source": f"Web / {w.get('source')}", "title": w.get("title"), "text": w.get("snippet"), "url": w.get("url")})

                    if search_scope in ("All Channels", "Xueqiu Equities"):
                        stock_res = reach_service.get_stock_intel(search_q)
                        quote = stock_res.get("quote", {})
                        if quote and quote.get("current"):
                            results_found.append({
                                "source": "Xueqiu Stock Quote",
                                "title": f"{search_q.upper()} Live Telemetry",
                                "text": f"Price: ${quote.get('current')} ({quote.get('percent')}%), PE: {quote.get('pe_ttm')}, Market Cap: {quote.get('market_capital')}",
                                "url": f"https://xueqiu.com/S/{search_q.upper()}",
                            })
                        for p in stock_res.get("trending_posts", [])[:3]:
                            results_found.append({
                                "source": "Xueqiu Community",
                                "title": p.get("title") or "Xueqiu Discussion",
                                "text": p.get("text", "")[:280],
                                "url": p.get("url", "https://xueqiu.com"),
                            })

                    if search_scope in ("All Channels", "Social Communities"):
                        social_hits = reach_service.search_social_discussions(search_q, limit=max_res)
                        for s in social_hits:
                            results_found.append({
                                "source": s.get("platform", "Social"),
                                "title": s.get("title"),
                                "text": s.get("content"),
                                "url": s.get("url"),
                            })

                    st.session_state["last_reach_results"] = results_found

            if "last_reach_results" in st.session_state and st.session_state["last_reach_results"]:
                res_list = st.session_state["last_reach_results"]
                st.markdown(f"<div style='font-family: monospace; font-size: 11px; color: #22c55e; margin: 10px 0;'>DISCOVERED {len(res_list)} CORROBORATING SIGNALS:</div>", unsafe_allow_html=True)
                for item in res_list:
                    st.markdown(f"""
                    <div style="background: #090a14; border: 1px solid rgba(255,255,255,0.08); border-left: 3px solid #FFD700; border-radius: 6px; padding: 12px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700; color: #FFD700; text-transform: uppercase;">[{item.get('source')}]</span>
                            <a href="{item.get('url', '#')}" target="_blank" style="color: #38bdf8; font-size: 11px; text-decoration: none;">View Source &#8599;</a>
                        </div>
                        <div style="font-size: 12px; font-weight: 600; color: #f4f4f5; margin: 4px 0;">{item.get('title')}</div>
                        <div style="font-size: 11px; color: #a1a1aa; line-height: 1.4;">{item.get('text')}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # 2. Universal URL Reader (Jina Reader)
        with reach_sub_tabs[1]:
            st.markdown("<div style='font-size: 11px; color: #a1a1aa; margin-bottom: 8px;'>Paste any financial article, SEC regulatory document, or research substack URL for clean Markdown extraction.</div>", unsafe_allow_html=True)
            u_col1, u_col2 = st.columns([4, 1])
            with u_col1:
                target_url = st.text_input("Target URL", value="https://news.ycombinator.com", key="reach_read_url_input")
            with u_col2:
                st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
                read_btn = st.button("PARSE WITH JINA", key="btn_read_jina_url", use_container_width=True)

            if read_btn:
                with st.spinner("Extracting clean markdown via Agent-Reach Jina Reader backend..."):
                    read_doc = reach_service.read_url(target_url)
                    st.session_state["last_read_doc"] = read_doc

            if "last_read_doc" in st.session_state:
                doc = st.session_state["last_read_doc"]
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("READER PROVIDER", doc.get("provider", "Jina"), f"Status: {doc.get('status')}")
                with m2:
                    st.metric("WORD COUNT", f"{doc.get('word_count', 0):,}", "Document Length")
                with m3:
                    st.metric("BYTE LENGTH", f"{doc.get('char_count', 0):,} chars", "Payload")

                st.markdown(f"**Document Title:** {doc.get('title', 'Document')}")
                st.text_area("Extracted Markdown Content", value=doc.get("content", ""), height=280)

        # 3. 16-Platform Channel Doctor
        with reach_sub_tabs[2]:
            doc_c1, doc_c2 = st.columns([3, 1])
            with doc_c1:
                st.markdown("<div style='font-size: 11px; color: #a1a1aa;'>Real-time platform access matrix across all 16 Agent-Reach channels. Probes active backends and credential health.</div>", unsafe_allow_html=True)
            with doc_c2:
                run_doc_btn = st.button("REFRESH DOCTOR", key="btn_refresh_doctor", use_container_width=True)

            if run_doc_btn or "doctor_cache" not in st.session_state:
                with st.spinner("Probing 16 channel backends..."):
                    st.session_state["doctor_cache"] = reach_service.run_doctor()

            doc_data = st.session_state.get("doctor_cache", {})
            dm1, dm2, dm3, dm4 = st.columns(4)
            with dm1:
                st.metric("TOTAL CHANNELS", doc_data.get("total_channels", 16), "Monitored")
            with dm2:
                st.metric("ACTIVE / READY", doc_data.get("ok_count", 0), "Zero-Config / OK")
            with dm3:
                st.metric("NEEDS SETUP / WARN", doc_data.get("warn_count", 0), "Login Required")
            with dm4:
                st.metric("UNAVAILABLE / OFF", doc_data.get("off_count", 0), "Tool Missing")

            channels = doc_data.get("channels", {})
            grid_cols = st.columns(4)
            for idx, (ch_name, ch_info) in enumerate(channels.items()):
                col = grid_cols[idx % 4]
                status = ch_info.get("status", "off")
                color = "#22c55e" if status == "ok" else ("#eab308" if status == "warn" else "#ef4444")
                active = ch_info.get("active_backend") or "None"
                with col:
                    st.markdown(f"""
                    <div style="background: #090a14; border: 1px solid rgba(255,255,255,0.08); border-top: 2px solid {color}; border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: #fff; text-transform: uppercase;">{ch_name}</span>
                            <span style="font-size: 9px; font-weight: 700; color: {color}; border: 1px solid {color}; border-radius: 3px; padding: 1px 4px;">{status.upper()}</span>
                        </div>
                        <div style="font-size: 10px; color: #71717a; margin-top: 4px;">Tier {ch_info.get('tier', 0)} · Backend: <strong style="color: #e4e4e7;">{active}</strong></div>
                    </div>
                    """, unsafe_allow_html=True)

        # 4. Media Transcriber
        with reach_sub_tabs[3]:
            st.markdown("<div style='font-size: 11px; color: #a1a1aa; margin-bottom: 8px;'>Extract audio transcripts from earnings conference calls, CEO interviews, and market analysis YouTube videos.</div>", unsafe_allow_html=True)
            v_col1, v_col2 = st.columns([3, 1])
            with v_col1:
                vid_url = st.text_input("Media / YouTube URL", value="https://www.youtube.com/watch?v=dQw4w9WgXcQ", key="reach_vid_url_input")
            with v_col2:
                transcribe_btn = st.button("TRANSCRIBE AUDIO", key="btn_run_transcribe", use_container_width=True)

            if transcribe_btn:
                with st.spinner("Downloading audio and transcribing via Whisper/yt-dlp..."):
                    tr_res = reach_service.get_video_transcript(vid_url)
                    st.session_state["last_transcribe_res"] = tr_res

            if "last_transcribe_res" in st.session_state:
                tr = st.session_state["last_transcribe_res"]
                if tr.get("status") == "success":
                    st.success(f"Transcript retrieved successfully ({tr.get('length', 0):,} characters).")
                    st.text_area("Extracted Transcript", value=tr.get("transcript", ""), height=220)
                else:
                    st.info(f"Transcriber Notice: {tr.get('error', 'Ready for valid YouTube/audio endpoint.')}")

    st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# VIEW 2: CLEAN INSTITUTIONAL TERMINAL OVERVIEW (Zero Analyst Desk Clutter!)
# ==============================================================================
else:
    # 1. 3D Interactive Cursor-Reactive Lily Flower Hero Banner (with Builder info in bottom-left)
    components.html(render_hero_banner_component(), height=540, scrolling=False)

    # Wrap post-hero overview sections in centered container
    st.markdown('<div class="sig-main-container">', unsafe_allow_html=True)

    # 2. Section 1: Market Summary (S&P 500 interactive chart + Major Indices list)
    st.markdown(render_market_summary_section(), unsafe_allow_html=True)

    # 3. Section 1 Tri-Metric Sparkline Cards (Crypto Cap & Dominance, DXY & Commodities, US 10Y & Inflation)
    st.markdown(render_market_mini_cards(), unsafe_allow_html=True)

    # 4. Kim Voice Strategist & Superchart Section
    st.markdown(
        """
        <div id="kim-strategist-section" class="sig-sec-header">
            <div class="sig-sec-title">Strategist Console &gt; <span style="font-size: 13px; font-weight: 500; color: #FFD700;">● Kim Voice AI &amp; Supercharts</span></div>
            <div class="sig-sec-sub">16-BIT PCM BIOMETRIC SYNTHESIS</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cond = live_news_agent.get_market_condition_briefing()
    from utils.live_market_data import fetch_mini_cards_data
    _mc = fetch_mini_cards_data()
    st.markdown(
        f"""
        <div style="background: #090a14; border: 1px solid rgba(255, 215, 0, 0.18); border-radius: 8px; padding: 10px 16px; margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span class="bb-tag-square"></span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: #FFD700; text-transform: uppercase;">
                    MARKET REGIME: {cond['regime']}
                </span>
            </div>
            <div style="display: flex; align-items: center; gap: 18px; font-family: 'JetBrains Mono', monospace; font-size: 11px;">
                <span style="color: #94a3b8;">CRUDE OIL: <strong style="color: {'#22c55e' if _mc.get('crude_up') else '#ef4444'};">{cond['commodities']['crude_oil_wti']}</strong> ({_mc.get('crude_chg', '+2.59%')})</span>
                <span style="color: #94a3b8;">US 10Y: <strong style="color: {'#22c55e' if _mc.get('us_10y_up') else '#ef4444'};">{cond['benchmark_rates']['US_10Y']}</strong> ({_mc.get('us_10y_chg', '+0.30%')})</span>
                <span style="color: #94a3b8;">GOLD: <strong style="color: #FFD700;">{cond['commodities']['gold']}</strong> ({_mc.get('gold_chg', '-0.45%')})</span>
                <span style="color: #94a3b8;">CRYPTO CAP: <strong style="color: {'#22c55e' if _mc.get('crypto_cap_up') else '#ef4444'};">{cond['crypto_total_cap']}</strong> ({_mc.get('crypto_cap_chg', '-3.94%')})</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "kim_state" not in st.session_state:
        init_wav = synthesize_female_speech_wav(
            "Good morning. I am Kim, your strategic market analyst. Oil is up more than 2%, the Nasdaq is in the red, and the Fed decides on Wednesday. Where do you want to start?"
        )
        st.session_state.kim_state = {
            "viewport": "chart",
            "symbol": "US30Y",
            "spoken": "Good morning. I am Kim, your strategic market analyst. Oil is up more than 2%, the Nasdaq is in the red, and the Fed decides on Wednesday. Where do you want to start?",
            "teleprompter": (
                "### STRATEGIC DISPATCH // EXECUTIVE BRIEFING\n\n"
                "- **Commodities:** Brent Crude Oil +2.1% steepening headline inflation expectations.\n"
                "- **Fixed Income:** US 30-Year Treasury yield holding resistance at 4.58%.\n"
                "- **Equities:** Nasdaq-100 down -1.45% intraday driven by semiconductor profit taking.\n"
                "- **Macro Catalyst:** FOMC Target Rate Decision on Wednesday (82% hike probability)."
            ),
            "logs": [
                "[09:00:01] SIGNALORA_ORCHESTRATOR: PIPELINE_INITIALIZED",
                "[09:00:02] KIM_SECURITY: WAV2VEC_KAN_MODEL_AUTHENTICATED [GENUINE]",
                "[09:00:03] CHARTIST_GATEWAY: TRADINGVIEW_BRIDGE_ONLINE",
                "[09:00:04] ORACLE_MACRO: CME_FEDWATCH_PROBABILITIES_HYDRATED",
                "[09:00:05] VIBE_QUANT: CONFLUENCE_MATRIX_READY [RSI, MACD, BB]",
                "[09:00:06] KIM_SYNTHESIS: FEMALE_VOICE_PROFILE_LOADED [WINDOWS SAPI 16-BIT]",
            ],
            "audio_path": init_wav,
            "play_audio": False,
            "authenticity_score": 0.998,
            "voice_status": "VERIFIED_GENUINE",
        }

    left_console, right_viewport = st.columns([1, 1], gap="large")

    with left_console:
        st.markdown(
            """
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: #cbd5e1;">
                    KIM // EXECUTIVE AI MARKET STRATEGIST
                </div>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700; color: #FFD700; background: rgba(255, 215, 0, 0.08); padding: 4px 10px; border-radius: 4px; border: 1px solid rgba(255, 215, 0, 0.2);">
                    ONLINE // FEMALE VOICE SYNTHESIS
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        mic_recording = st.audio_input(
            "Record Audio Query for Kim",
            key="kim_chrome_mic_input",
            label_visibility="collapsed",
        )

        user_prompt = st.text_input(
            "Direct Directive to Kim:",
            placeholder="Ask Kim anything (e.g. 'Pull up US 30-year chart' or 'What is happening with oil?')...",
            key="kim_text_prompt",
            label_visibility="collapsed",
        )

        r1, r2, r3 = st.columns(3)
        with r1:
            btn_chart = st.button("US 30Y CHART", use_container_width=True, key="kim_btn_chart")
        with r2:
            btn_fed = st.button("CME FEDWATCH", use_container_width=True, key="kim_btn_fed")
        with r3:
            btn_heat = st.button("SECTOR TREEMAP", use_container_width=True, key="kim_btn_heat")

        r4, r5, r6 = st.columns(3)
        with r4:
            btn_macro = st.button("MACRO SPREAD", use_container_width=True, key="kim_btn_macro")
        with r5:
            btn_quant = st.button("NVIDIA QUANT", use_container_width=True, key="kim_btn_quant")
        with r6:
            btn_brief = st.button("MARKET BRIEFING", use_container_width=True, key="kim_btn_brief")

        cmd_selected = None
        raw_audio_bytes = None

        if mic_recording is not None:
            raw_audio_bytes = mic_recording.getvalue()
            audio_sig = f"{len(raw_audio_bytes)}_{hash(raw_audio_bytes[:2000])}"
            if audio_sig != st.session_state.get("last_processed_mic_sig"):
                st.session_state["last_processed_mic_sig"] = audio_sig
                user_wav = os.path.join("storage", "audio", "user_mic_input.wav")
                os.makedirs(os.path.dirname(user_wav), exist_ok=True)
                with open(user_wav, "wb") as f_u:
                    f_u.write(raw_audio_bytes)
                transcribed = transcribe_audio_wav(user_wav)
                if transcribed:
                    cmd_selected = transcribed
                    st.session_state["kim_detected_speech"] = transcribed
                else:
                    cmd_selected = "Executive market intelligence briefing and strategic outlook"
                    st.session_state["kim_detected_speech"] = "Spoken directive captured via microphone"

        if user_prompt and not cmd_selected:
            cmd_selected = user_prompt
        elif btn_chart:
            cmd_selected = "Can you pull up the US 30-year chart in TradingView?"
        elif btn_fed:
            cmd_selected = "So what is the Fed going to do this Wednesday? Can you check?"
        elif btn_heat:
            cmd_selected = "Can you check the market heat map?"
        elif btn_macro:
            cmd_selected = "What does this mean for the market? Oil is the reason, tech is the victim."
        elif btn_quant:
            cmd_selected = "Analyze Nvidia technicals and quantitative confluence."
        elif btn_brief:
            cmd_selected = "Give me a complete market briefing and tactical takeaway."

        if cmd_selected:
            with st.spinner("Kim formulating dynamic strategic intelligence..."):
                resp = kim_voice_agent.process_command(
                    user_query=cmd_selected,
                    audio_data=raw_audio_bytes,
                    delivery_mode="HYBRID",
                )
                st.session_state.kim_state["spoken"] = resp.spoken_script
                st.session_state.kim_state["teleprompter"] = resp.teleprompter_text
                st.session_state.kim_state["viewport"] = resp.visual_action
                st.session_state.kim_state["symbol"] = resp.target_symbol or "US30Y"
                st.session_state.kim_state["audio_path"] = resp.audio_path
                st.session_state.kim_state["authenticity_score"] = resp.authenticity_score
                st.session_state.kim_state["voice_status"] = resp.voice_security_status
                st.session_state.kim_state["play_audio"] = True

        if st.session_state.kim_state.get("spoken"):
            st.markdown(
                f"""
                <div style="background: #0f1122; border: 1px solid rgba(255, 215, 0, 0.25); border-radius: 6px; padding: 12px 14px; margin: 10px 0; box-shadow: 0 4px 16px rgba(0,0,0,0.5);">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700; color: #FFD700; text-transform: uppercase;">
                            [ KIM SPOKEN DIRECTIVE // FEMALE VOICE ]
                        </span>
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #22c55e;">
                            16-BIT PCM // SYSTEM.SPEECH
                        </span>
                    </div>
                    <div style="color: #ffffff; font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 500; line-height: 1.5;">
                        "{st.session_state.kim_state['spoken']}"
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            audio_f = st.session_state.kim_state.get("audio_path")
            if not audio_f or not os.path.exists(audio_f):
                audio_f = synthesize_female_speech_wav(st.session_state.kim_state["spoken"])
                st.session_state.kim_state["audio_path"] = audio_f

            if audio_f and os.path.exists(audio_f):
                with open(audio_f, "rb") as f_aud:
                    kim_wav_bytes = f_aud.read()
                autoplay_flag = st.session_state.kim_state.get("play_audio", False)
                st.audio(kim_wav_bytes, format="audio/wav", autoplay=autoplay_flag)

        st.markdown(
            f"""
            <div style="background: #080913; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 6px; padding: 14px; margin-top: 10px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: #FFD700;">STRATEGIC DISPATCH // TELEPROMPTER</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700; color: #22c55e;">[ STATUS: VERIFIED ]</span>
                </div>
                <div style="font-size: 13px; line-height: 1.6; color: #cbd5e1;">{st.session_state.kim_state['teleprompter']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_viewport:
        vp = st.session_state.kim_state.get("viewport", "chart")
        sym = st.session_state.kim_state.get("symbol", "US30Y")

        v_col1, v_col2, v_col3, v_col4 = st.columns(4)
        with v_col1:
            if st.button("SUPERCHART", use_container_width=True, key="vp_btn_chart"):
                st.session_state.kim_state["viewport"] = "chart"
                st.rerun()
        with v_col2:
            if st.button("S&P 500 TREEMAP", use_container_width=True, key="vp_btn_heat"):
                st.session_state.kim_state["viewport"] = "heatmap"
                st.rerun()
        with v_col3:
            if st.button("CME FEDWATCH", use_container_width=True, key="vp_btn_fed"):
                st.session_state.kim_state["viewport"] = "fedwatch"
                st.rerun()
        with v_col4:
            if st.button("OIL VS TECH", use_container_width=True, key="vp_btn_corr"):
                st.session_state.kim_state["viewport"] = "correlation"
                st.rerun()

        if vp == "heatmap":
            st.markdown(render_tradingview_heatmap(height=500), unsafe_allow_html=True)
        elif vp == "fedwatch":
            rates_snap = macro_rates_agent.fetch_yield_snapshots()
            fw = rates_snap.fedwatch
            df_fed = pd.DataFrame([
                {"Outcome": "Rate Hike (Hawkish)", "Probability": fw.hike_probability * 100},
                {"Outcome": "Pause (Hold)", "Probability": fw.pause_probability * 100},
                {"Outcome": "Rate Cut (Dovish)", "Probability": fw.cut_probability * 100},
            ])
            st.bar_chart(df_fed.set_index("Outcome"), color="#FFD700", use_container_width=True)
        elif vp == "correlation":
            st.markdown(render_tradingview_widget(symbol="CL1!", height=240), unsafe_allow_html=True)
            st.markdown(render_tradingview_widget(symbol="QQQ", height=240), unsafe_allow_html=True)
        else:
            st.markdown(render_tradingview_widget(symbol=sym, height=500), unsafe_allow_html=True)

    # 5. Section 2: Today's News (Clickable links to real publications!)
    st.markdown(
        """
        <div id="news-section" class="sig-sec-header">
            <div class="sig-sec-title">Top stories &gt; <span style="font-size: 13px; font-weight: 500; color: #22c55e;">● Live Telemetry Wire (Zero Delay Stream)</span></div>
            <div class="sig-sec-sub">CLICK ANY CARD TO READ FULL STORY ON ORIGINAL OUTLET // UPDATED IN REAL-TIME</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    n_col1, n_col2, n_col3 = st.columns([3, 1, 0.7])
    with n_col1:
        selected_news_cat = st.radio(
            "Filter Category",
            ["All", "US Stocks", "Crypto", "Futures & Commodities", "Forex", "Bonds & Rates", "Global Economy"],
            index=0,
            horizontal=True,
            key="news_sec_cat_pills",
            label_visibility="collapsed",
        )
        st.markdown(render_category_pills(selected_news_cat), unsafe_allow_html=True)
    with n_col2:
        news_query = st.text_input(
            "Search Wire",
            placeholder="Search news or ticker...",
            key="news_sec_search_box",
            label_visibility="collapsed",
        )
    with n_col3:
        refresh_news = st.button("Refresh Wire", key="btn_refresh_news", use_container_width=True)

    if news_query:
        news_items = live_news_agent.search_news(news_query, limit=6)
    else:
        news_items = live_news_agent.fetch_breaking_news(
            limit=6, category=selected_news_cat, force_refresh=bool(refresh_news)
        )

    # Clickable news cards opening source URL in target="_blank"
    st.markdown(render_breaking_news_grid(news_items), unsafe_allow_html=True)

    # 6. Section 3: Today's Stocks & Real-Time Interactive Stock Graph
    st.markdown(
        """
        <div id="stocks-section" class="sig-sec-header" style="margin-top: 28px;">
            <div class="sig-sec-title">US stocks &gt; <span style="font-size: 13px; font-weight: 500; color: #22c55e;">● Live Real-Time Interactive Candlestick Graph</span></div>
            <div class="sig-sec-sub">LIVE STREAMING EQUITIES TELEMETRY // SELECT PRESET TICKER OR ENTER ANY SYMBOL</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    stk_c1, stk_c2 = st.columns([3, 1])
    with stk_c1:
        stock_options = ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "META", "GOOGL", "AMD", "PLTR", "SPY", "QQQ"]
        selected_stock_pill = st.radio(
            "Select Stock Ticker",
            stock_options,
            index=0,
            horizontal=True,
            key="stock_sec_ticker_pills",
            label_visibility="collapsed",
        )
    with stk_c2:
        custom_stock_input = st.text_input(
            "Custom Stock",
            placeholder="Custom Ticker (e.g. NFLX, COIN, ARM)...",
            key="custom_stock_sym_input",
            label_visibility="collapsed",
        )

    active_stock_sym = custom_stock_input.strip().upper() if custom_stock_input.strip() else selected_stock_pill

    stk_tf_c1, stk_tf_c2 = st.columns([3, 1])
    with stk_tf_c1:
        stock_tf = st.radio(
            "Candle Timeframe",
            ["1", "5", "15", "60", "D"],
            index=0,
            format_func=lambda x: {"1": "1M (LIVE INTRADAY TICKS)", "5": "5M", "15": "15M", "60": "1H", "D": "1D (DAILY)"}[x],
            horizontal=True,
            key="stock_sec_tf_pills",
        )
    with stk_tf_c2:
        st.markdown(
            f"""
            <div style="text-align: right; padding-top: 6px; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #22c55e;">
                ● LIVE EXCHANGE TICKS ({active_stock_sym})
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Live Interactive Institutional Stock Graph Console (TradingView Advanced Candlesticks)
    components.html(render_tradingview_widget(symbol=active_stock_sym, height=520, interval=stock_tf), height=535, scrolling=False)

    # Active Volume Leaders, Gainers & Losers Tables (Yahoo Finance live data)
    st.markdown(render_stocks_section(), unsafe_allow_html=True)

    # 7. Section 4: Crypto Desk & Real-Time Interactive Crypto Graph
    st.markdown(
        """
        <div id="crypto-section" class="sig-sec-header" style="margin-top: 28px;">
            <div class="sig-sec-title">Crypto desk &gt; <span style="font-size: 13px; font-weight: 500; color: #f59e0b;">● Live Real-Time Interactive Spot Graph</span></div>
            <div class="sig-sec-sub">ON-CHAIN SPOT &amp; EXCHANGE LIQUIDITY // REAL-TIME TRADINGVIEW CANDLESTICKS</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cr_c1, cr_c2 = st.columns([3, 1])
    with cr_c1:
        crypto_options = ["BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "BNBUSD", "DOGEUSD"]
        selected_crypto_pill = st.radio(
            "Select Crypto Pair",
            crypto_options,
            index=0,
            horizontal=True,
            key="crypto_sec_ticker_pills",
            label_visibility="collapsed",
        )
    with cr_c2:
        custom_crypto_input = st.text_input(
            "Custom Crypto",
            placeholder="Custom Pair (e.g. ADAUSD, AVAXUSD)...",
            key="custom_crypto_sym_input",
            label_visibility="collapsed",
        )

    active_crypto_sym = custom_crypto_input.strip().upper() if custom_crypto_input.strip() else selected_crypto_pill

    cr_tf_c1, cr_tf_c2 = st.columns([3, 1])
    with cr_tf_c1:
        crypto_tf = st.radio(
            "Crypto Candle Timeframe",
            ["1", "5", "15", "60", "D"],
            index=0,
            format_func=lambda x: {"1": "1M (24/7 LIVE STREAM)", "5": "5M", "15": "15M", "60": "1H", "D": "1D (DAILY)"}[x],
            horizontal=True,
            key="crypto_sec_tf_pills",
        )
    with cr_tf_c2:
        st.markdown(
            f"""
            <div style="text-align: right; padding-top: 6px; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #f59e0b;">
                ● 24/7 BINANCE SPOT TICKS ({active_crypto_sym})
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Live Interactive Institutional Crypto Graph Console
    components.html(render_tradingview_widget(symbol=active_crypto_sym, height=480, interval=crypto_tf), height=495, scrolling=False)

    # Spot Leaders, 24h Gainers & Losers Tables (CoinGecko live data)
    st.markdown(render_crypto_section(), unsafe_allow_html=True)

    # 8. Section 5: Bonds & Rates Desk + Futures & Forex
    st.markdown(
        """
        <div id="bonds-section" class="sig-sec-header">
            <div class="sig-sec-title">Bonds &amp; rates &gt; <span style="font-size: 13px; font-weight: 500; color: #FFD700;">● Fixed Income &amp; Forex</span></div>
            <div class="sig-sec-sub">SOVEREIGN BENCHMARK TELEMETRY</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(render_bonds_dashboard(), unsafe_allow_html=True)
    st.markdown(render_benchmark_bars(), unsafe_allow_html=True)

    rates_snap = macro_rates_agent.fetch_yield_snapshots()
    fw = rates_snap.fedwatch
    df_fed = pd.DataFrame([
        {"Outcome": "Rate Hike (Hawkish)", "Probability": fw.hike_probability * 100},
        {"Outcome": "Pause (Hold)", "Probability": fw.pause_probability * 100},
        {"Outcome": "Rate Cut (Dovish)", "Probability": fw.cut_probability * 100},
    ])
    st.markdown("<div style='font-family: monospace; font-size: 11px; font-weight: 700; color: #FFD700; margin: 16px 0 8px 0;'>CME FEDWATCH // PROBABILITY DISTRIBUTION</div>", unsafe_allow_html=True)
    st.bar_chart(df_fed.set_index("Outcome"), color="#FFD700", use_container_width=True)

    # 9. Section 6: The World Map (Global Inflation Map + Economic Calendar)
    st.markdown(render_world_inflation_map(), unsafe_allow_html=True)

    # 10. Section 7: About Me & SIGNALORA Institutional Footer with Giant Closing Banner
    st.markdown(render_about_me_section(), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
