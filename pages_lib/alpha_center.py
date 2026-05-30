"""pages_lib/alpha_center.py - Alpha Center v40.5 (Wired)
Patched: entry_decisions, methodology_scores, movement_regimes, walkforward gate
"""
from __future__ import annotations
import json
from typing import Dict, List, Optional

import pandas as pd
import numpy as np
import streamlit as st

from utils.helpers import _pct_fmt, _delta_fmt, _fmt, _signal_color, _grade_badge, _recommendation_badge
from utils.viz_utils import _render_alpha_table, _render_ticker_detail


def render(snap: dict):
    st.header("⚡ Alpha Center")

    # ── Alpha Center Curator Output ──
    ac = snap.get("alpha_center", {})
    passed = ac.get("passed", [])
    rejected = ac.get("rejected", [])

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Passed", len(passed))
    with c2:
        st.metric("Rejected", len(rejected))
    with c3:
        keith_overrides = snap.get("keith_summary", {}).get("overrides_applied", 0)
        st.metric("Keith Overrides", keith_overrides)

    # ── Level 1 (A-grade) ──
    st.subheader("🥇 Level 1 — A-Grade Picks")
    level1 = [i for i in passed if i.get("grade") in ("A", "A+")]
    if level1:
        _render_alpha_table(level1, show_keith=True)
    else:
        st.info("No A-grade picks currently")

    # ── Level 2 (B-grade) ──
    st.subheader("🥈 Level 2 — B-Grade Picks")
    level2 = [i for i in passed if i.get("grade") == "B"]
    if level2:
        _render_alpha_table(level2, show_keith=True)
    else:
        st.info("No B-grade picks currently")

    # ── Entry Decisions (NEW v40.5) ──
    entry_decisions = snap.get("entry_decisions", {})
    if entry_decisions:
        st.divider()
        st.subheader("🎯 Entry Decisions")
        # Filter only for tickers in passed list
        passed_tickers = {i.get("ticker") for i in passed}
        filtered_entries = {k: v for k, v in entry_decisions.items() if k in passed_tickers}
        if filtered_entries:
            rows = []
            for t, d in list(filtered_entries.items())[:30]:
                rows.append({
                    "Ticker": t,
                    "Action": d.get("action", "AVOID"),
                    "Direction": d.get("direction", "NEUTRAL"),
                    "Conviction": d.get("conviction", 0),
                    "Entry": d.get("entry_px"),
                    "Stop": d.get("stop_loss"),
                    "Target": d.get("target_px"),
                    "R:R": d.get("risk_reward"),
                    "Basis": d.get("basis", "")[:60],
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Entry decisions available but none for current Alpha Center picks")

    # ── Methodology Scores (NEW v40.5) ──
    meth_scores = snap.get("methodology_scores", {})
    if meth_scores:
        st.divider()
        st.subheader("🧠 Methodology Scores (6-Investor Overlay)")
        passed_tickers = {i.get("ticker") for i in passed}
        filtered_meth = {k: v for k, v in meth_scores.items() if k in passed_tickers}
        if filtered_meth:
            rows = []
            for t, scores in list(filtered_meth.items())[:30]:
                row = {"Ticker": t}
                for investor in ["citrini", "leopold", "coatue", "karsan", "spotgamma", "hedgeye"]:
                    inv_data = scores.get(investor, {})
                    row[investor.capitalize()] = inv_data.get("score", 0) if isinstance(inv_data, dict) else inv_data
                rows.append(row)
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Methodology scores available but none for current picks")

    # ── Movement Timing (NEW v40.5) ──
    movement_regimes = snap.get("movement_regimes", {})
    if movement_regimes:
        st.divider()
        st.subheader("⏱️ Movement Timing Regimes")
        passed_tickers = {i.get("ticker") for i in passed}
        filtered_mov = {k: v for k, v in movement_regimes.items() if k in passed_tickers}
        if filtered_mov:
            rows = []
            for t, reg in list(filtered_mov.items())[:30]:
                rows.append({
                    "Ticker": t,
                    "Regime": reg.get("regime", "UNKNOWN"),
                    "Confidence": reg.get("confidence", 0),
                    "Expected Move": reg.get("expected_move_pct"),
                    "Duration": reg.get("expected_duration_days"),
                    "Signal": reg.get("signal", "HOLD"),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Movement timing available but none for current picks")

    # ── Walkforward Gate (v40.5) ──
    st.divider()
    st.subheader("🔄 Walkforward Backtest Gate")
    wf = snap.get("walkforward_results_v40", {})
    if wf.get("skipped"):
        st.warning(f"⏸️ Walkforward skipped: {wf.get('reason', 'Run on-demand')}")
        st.info("Go to **Portfolio Stress** page to run walkforward backtest on-demand.")
    else:
        passed_wf = wf.get("passed", 0)
        total_wf = wf.get("total", 0)
        st.metric("Walkforward Gate", f"{passed_wf}/{total_wf} passed")
        if wf.get("results"):
            st.json(wf["results"])

    # ── Keith Signal Sync Summary ──
    st.divider()
    st.subheader("📡 Keith Signal Sync")
    keith_summary = snap.get("keith_summary", {})
    if keith_summary:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total Signals", keith_summary.get("total_signals", 0))
        with c2: st.metric("Bullish Trade", keith_summary.get("trade_bullish", 0))
        with c3: st.metric("Bearish Trade", keith_summary.get("trade_bearish", 0))
        with c4: st.metric("Overrides Applied", keith_summary.get("overrides_applied", 0))
        st.caption(f"Last updated: {keith_summary.get('last_updated', 'N/A')} | Sources: {', '.join(keith_summary.get('sources', []))}")
    else:
        st.info("Keith signal sync data unavailable")

    # ── Ticker Detail Explorer ──
    st.divider()
    st.subheader("🔎 Ticker Detail Explorer")
    all_tickers = sorted({i.get("ticker") for i in passed})
    if all_tickers:
        selected = st.selectbox("Select ticker", all_tickers)
        if selected:
            _render_ticker_detail(selected, snap)
    else:
        st.info("No tickers available for detail view")
