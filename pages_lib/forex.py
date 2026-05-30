"""pages_lib/forex.py - Forex v40.5 (Wired)
Patched: front-run + COT data overlay
"""
from __future__ import annotations
import pandas as pd
import streamlit as st

from utils.helpers import _pct_fmt, _fmt
from utils.viz_utils import _render_ticker_detail


def render(snap: dict):
    st.header("💱 Forex")

    tab_picks, tab_frontrun, tab_cot, tab_detail = st.tabs(["📈 Picks", "⚡ Front-Run", "📊 COT Data", "🔎 Ticker Detail"])

    # ── TAB 1: PICKS ──
    with tab_picks:
        ac = snap.get("alpha_center", {})
        fx_picks = [i for i in ac.get("passed", []) if "=X" in i.get("ticker", "") or i.get("ticker") in ["DX-Y.NYB", "UUP"]]
        if fx_picks:
            st.subheader(f"Alpha Center Forex Picks ({len(fx_picks)})")
            df = pd.DataFrame([{
                "Ticker": i.get("ticker"),
                "Grade": i.get("grade"),
                "Direction": i.get("direction"),
                "Score": i.get("priority_score"),
                "Price": i.get("price"),
            } for i in fx_picks])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No forex picks in Alpha Center")

    # ── TAB 2: FRONT-RUN ──
    with tab_frontrun:
        front_run = snap.get("front_run_candidates", [])
        fx_front = [c for c in front_run if c.get("market_type") == "forex"]
        if fx_front:
            st.subheader(f"Forex Front-Run Candidates ({len(fx_front)})")
            df = pd.DataFrame([{
                "Ticker": c.get("ticker"),
                "Theme": c.get("theme"),
                "Priority": c.get("priority"),
                "Price": c.get("price"),
                "Why": c.get("why_front_run", "")[:80],
            } for c in fx_front[:15]])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No forex front-run candidates")

    # ── TAB 3: COT DATA ──
    with tab_cot:
        cot = snap.get("cot_data", {})
        if cot:
            st.subheader(f"📊 CFTC COT Data ({len(cot)} instruments)")
            rows = []
            for inst, data in list(cot.items())[:20]:
                rows.append({
                    "Instrument": inst,
                    "Net Non-Commercial": data.get("net_noncommercial"),
                    "Commercial": data.get("commercial"),
                    "Non-Reportable": data.get("nonreportable"),
                    "Signal": data.get("signal", "NEUTRAL"),
                    "Last Updated": data.get("as_of"),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No COT data available — run orchestrator to populate")

    # ── TAB 4: TICKER DETAIL ──
    with tab_detail:
        ac = snap.get("alpha_center", {})
        all_fx = sorted({i.get("ticker") for i in ac.get("all", []) if "=X" in i.get("ticker", "") or i.get("ticker") in ["DX-Y.NYB", "UUP"]})
        if all_fx:
            selected = st.selectbox("Select forex ticker", all_fx)
            if selected:
                _render_ticker_detail(selected, snap)
                cot_data = snap.get("cot_data", {}).get(selected, {})
                if cot_data:
                    st.divider()
                    st.subheader("📡 COT Detail")
                    st.json(cot_data)
        else:
            st.info("No forex tickers available")
