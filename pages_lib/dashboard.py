"""pages_lib/dashboard.py - MacroRegime Dashboard v40.5 (Wired)
Patched: render dead data + external data coverage + merged chain reactions
"""
from __future__ import annotations
import json, math
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
import streamlit as st

from utils.helpers import _pct_fmt, _delta_fmt, _fmt, _signal_color, _grade_badge, _recommendation_badge
from utils.data_utils import _get_prices, _get_price
from utils.viz_utils import (
    _render_regime_gauge, _render_vix_gauge, _render_dxy_gauge,
    _render_alpha_table, _render_daily_signals_table, _render_front_run_table,
    _render_chain_reaction_table, _render_tier1alpha_panel,
)


def render(snap: dict):
    st.header("🏠 MacroRegime Dashboard")

    # ── Top Metrics ──
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        quad = snap.get("current_quad", "Q3")
        st.metric("Structural Quad", quad)
    with col2:
        vix = snap.get("vix", 20.0)
        st.metric("VIX", f"{vix:.1f}")
    with col3:
        dxy = snap.get("dxy_ret", 0.0)
        st.metric("DXY 1M", _pct_fmt(dxy))
    with col4:
        err = len(snap.get("errors", []))
        st.metric("Errors", err, delta=None)
    with col5:
        bt = snap.get("build_time_s", 0)
        st.metric("Build Time", f"{bt:.0f}s")

    # ── Regime Gauges ──
    c1, c2, c3 = st.columns(3)
    with c1:
        _render_regime_gauge(snap.get("gip", None))
    with c2:
        _render_vix_gauge(snap.get("vix", 20.0))
    with c3:
        _render_dxy_gauge(snap.get("dxy_ret", 0.0))

    # ── Tier1Alpha Panel (top priority) ──
    st.divider()
    st.subheader("🎯 Tier1Alpha — Top Picks")
    _render_tier1alpha_panel(snap)

    # ── Auto-Discovered Tickers (NEW v40.5) ──
    auto_disc = snap.get("auto_discoveries", {})
    discovered = auto_disc.get("discovered_tickers", [])
    if discovered:
        st.divider()
        st.subheader(f"🔍 Auto-Discovered Tickers ({len(discovered)} new)")
        cols = st.columns(min(len(discovered), 8))
        for i, t in enumerate(discovered[:16]):
            with cols[i % len(cols)]:
                st.markdown(f"<div style='background:#1a1a2e;padding:8px;border-radius:6px;text-align:center'><b>{t}</b></div>", unsafe_allow_html=True)
        if len(discovered) > 16:
            st.caption(f"...and {len(discovered)-16} more")

    # ── Chain Reactions (MERGED v40.5) ──
    chain_reactions = snap.get("chain_reactions", {})
    catalog = chain_reactions.get("catalog", {})
    active_tx = chain_reactions.get("active_transmissions", [])
    supply_chains = chain_reactions.get("supply_chain_chains", [])
    if catalog or active_tx or supply_chains:
        st.divider()
        st.subheader("🔗 Chain Reactions & Supply Chain Cascades")
        tabs = st.tabs(["Catalog", "Active Shocks", "Supply Chain Chains"])
        with tabs[0]:
            if catalog:
                for name, chain in list(catalog.items())[:5]:
                    with st.expander(f"📦 {name}"):
                        st.json(chain)
            else:
                st.info("No chain catalog available")
        with tabs[1]:
            if active_tx:
                df_tx = pd.DataFrame(active_tx[:10])
                st.dataframe(df_tx, use_container_width=True)
            else:
                st.info("No active transmission shocks")
        with tabs[2]:
            if supply_chains:
                for chain in supply_chains:
                    with st.expander(f"⛓️ {chain.get('name', 'Chain')} — {chain.get('trigger', '')}"):
                        stages = chain.get("stages", [])
                        for stg in stages:
                            tickers = ", ".join(stg.get("tickers", []))
                            st.markdown(f"**Stage {stg.get('stage')}**: {stg.get('layer')} — Bottleneck: `{stg.get('bottleneck')}` | Tickers: `{tickers}`")
                        st.caption(f"Confidence: {chain.get('confidence', 0):.0%} | Source: {chain.get('source', 'N/A')}")
            else:
                st.info("No supply chain chains available")

    # ── External Data Coverage (NEW v40.5) ──
    st.divider()
    st.subheader("📡 External Data Coverage")
    ext_cols = st.columns(5)
    ext_data = {
        "Options": len(snap.get("options_data", {})),
        "COT": len(snap.get("cot_data", {})),
        "FINRA Dark Pool": len(snap.get("finra_short", {})),
        "On-Chain": len(snap.get("onchain_data", {})),
        "CME OI": len(snap.get("cme_oi", {})),
    }
    for i, (name, count) in enumerate(ext_data.items()):
        with ext_cols[i]:
            color = "#00ff88" if count > 0 else "#ff4444"
            st.markdown(f"<div style='background:#1a1a2e;padding:12px;border-radius:8px;text-align:center'><div style='color:{color};font-size:24px;font-weight:bold'>{count}</div><div style='color:#aaa;font-size:12px'>{name}</div></div>", unsafe_allow_html=True)

    # ── Daily Signals ──
    st.divider()
    st.subheader("📊 Daily Signals")
    daily = snap.get("daily_signals", [])
    if daily:
        _render_daily_signals_table(daily)
    else:
        st.info("No daily signals generated")

    # ── Front-Run Candidates (Top 10) ──
    front_run = snap.get("front_run_candidates", [])
    if front_run:
        st.divider()
        st.subheader("⚡ Top Front-Run Candidates")
        _render_front_run_table(front_run[:10])

    # ── Market Health ──
    st.divider()
    st.subheader("🏥 Market Health")
    health = snap.get("market_health", {})
    if health:
        score = health.get("score", 50)
        label = health.get("label", "UNKNOWN")
        color = "#00ff88" if score > 70 else ("#ffaa00" if score > 40 else "#ff4444")
        st.markdown(f"<div style='font-size:48px;color:{color};font-weight:bold'>{score}</div><div style='color:#aaa'>{label}</div>", unsafe_allow_html=True)
        if health.get("breadth"):
            st.metric("Breadth", f"{health['breadth']:.1f}%")
    else:
        st.info("Market health data unavailable")

    # ── Behavioral Macro ──
    st.divider()
    st.subheader("🧠 Behavioral Macro")
    beh = snap.get("behavioral_macro", {})
    if beh:
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Bullish", f"{beh.get('bullish', 0)}%")
        with c2: st.metric("Bearish", f"{beh.get('bearish', 0)}%")
        with c3: st.metric("Neutral", f"{beh.get('neutral', 0)}%")
        yves = beh.get("yves", {})
        if yves and yves.get("alert"):
            st.warning(f"🚨 Yves Alert: {yves['alert']} (Level: {yves.get('alert_level', 'NONE')})")
    else:
        st.info("Behavioral macro data unavailable")

    # ── Portfolio Stress Quick View ──
    st.divider()
    st.subheader("💥 Portfolio Stress (Quick View)")
    stress = snap.get("stress_test", [])
    if stress:
        for s in stress[:3]:
            with st.expander(f"{s.get('scenario', 'Unknown')} — DD: {s.get('portfolio_dd', 0):.1%}"):
                st.markdown(f"**Worst Asset:** {s.get('worst_asset', 'N/A')} ({s.get('worst_dd', 0):.1%})")
                st.markdown(f"**Best Asset:** {s.get('best_asset', 'N/A')} ({s.get('best_dd', 0):.1%})")
                st.markdown(f"**Hedge:** {s.get('hedge', 'N/A')}")
    else:
        st.info("Run full stress test from Portfolio Stress page")

    # ── News Narratives ──
    st.divider()
    st.subheader("📰 News Narratives")
    news = snap.get("news_narratives", {})
    emergent = news.get("emergent_narratives", [])
    if emergent:
        for nar in emergent[:5]:
            sentiment = nar.get("avg_sentiment", 0)
            color = "#00ff88" if sentiment > 0.2 else ("#ff4444" if sentiment < -0.2 else "#ffaa00")
            st.markdown(f"<span style='color:{color}'>●</span> **{nar.get('name', 'Theme')}** — Mentions: {nar.get('mentions', 0)}, Sentiment: {sentiment:+.2f}", unsafe_allow_html=True)
            tickers = ", ".join(nar.get("tickers", [])[:5])
            st.caption(f"Tickers: {tickers}")
    else:
        st.info("No emergent narratives detected")

    # ── Build Info ──
    st.divider()
    st.caption(f"Generated: {snap.get('_generated_at', 'N/A')} | Source: {snap.get('_source', 'unknown')} | v40.5")
