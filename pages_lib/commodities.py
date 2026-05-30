"""pages_lib/commodities.py - Commodities v40.5 (Wired)
Patched: front-run + COT data + CME OI
"""
from __future__ import annotations
import pandas as pd
import streamlit as st

from utils.helpers import _pct_fmt, _fmt
from utils.viz_utils import _render_ticker_detail


def render(snap: dict):
    st.header("🛢️ Commodities")

    tab_picks, tab_frontrun, tab_cot, tab_cme, tab_detail = st.tabs(["📈 Picks", "⚡ Front-Run", "📊 COT Data", "🏭 CME OI", "🔎 Ticker Detail"])

    # ── TAB 1: PICKS ──
    with tab_picks:
        ac = snap.get("alpha_center", {})
        comm_picks = [i for i in ac.get("passed", []) if "=F" in i.get("ticker", "") or i.get("ticker") in ["USO", "GLD", "SLV", "UNG", "CPER"]]
        if comm_picks:
            st.subheader(f"Alpha Center Commodity Picks ({len(comm_picks)})")
            df = pd.DataFrame([{
                "Ticker": i.get("ticker"),
                "Grade": i.get("grade"),
                "Direction": i.get("direction"),
                "Score": i.get("priority_score"),
                "Price": i.get("price"),
            } for i in comm_picks])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No commodity picks in Alpha Center")

    # ── TAB 2: FRONT-RUN ──
    with tab_frontrun:
        front_run = snap.get("front_run_candidates", [])
        comm_front = [c for c in front_run if c.get("market_type") == "commodity"]
        if comm_front:
            st.subheader(f"Commodity Front-Run Candidates ({len(comm_front)})")
            df = pd.DataFrame([{
                "Ticker": c.get("ticker"),
                "Theme": c.get("theme"),
                "Priority": c.get("priority"),
                "Price": c.get("price"),
                "Why": c.get("why_front_run", "")[:80],
            } for c in comm_front[:15]])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No commodity front-run candidates")

    # ── TAB 3: COT DATA ──
    with tab_cot:
        cot = snap.get("cot_data", {})
        comm_cot = {k: v for k, v in cot.items() if "=F" in k or k in ["USO", "GLD", "SLV", "UNG", "CPER"]}
        if comm_cot:
            st.subheader(f"📊 CFTC COT — Commodities ({len(comm_cot)})")
            rows = []
            for inst, data in list(comm_cot.items())[:20]:
                rows.append({
                    "Instrument": inst,
                    "Net Non-Commercial": data.get("net_noncommercial"),
                    "Commercial": data.get("commercial"),
                    "Signal": data.get("signal", "NEUTRAL"),
                    "Last Updated": data.get("as_of"),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No commodity COT data")

    # ── TAB 4: CME OI ──
    with tab_cme:
        cme = snap.get("cme_oi", {})
        if cme:
            st.subheader(f"🏭 CME Open Interest ({len(cme)} products)")
            rows = []
            for prod, data in list(cme.items())[:10]:
                rows.append({
                    "Product": prod,
                    "OI": data.get("oi"),
                    "Volume": data.get("volume"),
                    "Change": data.get("change"),
                    "Last Updated": data.get("as_of"),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No CME OI data — run orchestrator to populate")

    # ── TAB 5: TICKER DETAIL ──
    with tab_detail:
        ac = snap.get("alpha_center", {})
        all_comm = sorted({i.get("ticker") for i in ac.get("all", []) if "=F" in i.get("ticker", "") or i.get("ticker") in ["USO", "GLD", "SLV", "UNG", "CPER"]})
        if all_comm:
            selected = st.selectbox("Select commodity ticker", all_comm)
            if selected:
                _render_ticker_detail(selected, snap)
                cot_data = snap.get("cot_data", {}).get(selected, {})
                if cot_data:
                    st.divider()
                    st.subheader("📡 COT Detail")
                    st.json(cot_data)
                cme_data = snap.get("cme_oi", {}).get(selected, {})
                if cme_data:
                    st.divider()
                    st.subheader("📡 CME OI Detail")
                    st.json(cme_data)
        else:
            st.info("No commodity tickers available")
