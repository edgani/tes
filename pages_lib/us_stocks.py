"""pages_lib/us_stocks.py - US Stocks v40.5 (Wired)
Patched: front-run candidates + FINRA dark pool + options_data per ticker
"""
from __future__ import annotations
import pandas as pd
import streamlit as st

from utils.helpers import _pct_fmt, _fmt
from utils.viz_utils import _render_ticker_detail


def render(snap: dict):
    st.header("🇺🇸 US Stocks")

    tab_picks, tab_frontrun, tab_detail = st.tabs(["📈 Picks", "⚡ Front-Run", "🔎 Ticker Detail"])

    # ── TAB 1: PICKS ──
    with tab_picks:
        ac = snap.get("alpha_center", {})
        us_picks = [i for i in ac.get("passed", []) if not any(s in i.get("ticker", "") for s in [".JK", "=X", "=F", "-USD"])]
        if us_picks:
            st.subheader(f"Alpha Center US Picks ({len(us_picks)})")
            df = pd.DataFrame([{
                "Ticker": i.get("ticker"),
                "Grade": i.get("grade"),
                "Direction": i.get("direction"),
                "Score": i.get("priority_score"),
                "Price": i.get("price"),
                "TRR": i.get("trr"),
                "LRR": i.get("lrr"),
                "Keith": i.get("keith_trade", "—"),
            } for i in us_picks])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No US equity picks in Alpha Center")

    # ── TAB 2: FRONT-RUN ──
    with tab_frontrun:
        front_run = snap.get("front_run_candidates", [])
        us_front = [c for c in front_run if c.get("market_type") == "us_equity"]
        if us_front:
            st.subheader(f"US Front-Run Candidates ({len(us_front)})")
            df = pd.DataFrame([{
                "Ticker": c.get("ticker"),
                "Theme": c.get("theme"),
                "Role": c.get("role"),
                "Priority": c.get("priority"),
                "Price": c.get("price"),
                "Why": c.get("why_front_run", "")[:80],
                "Source": c.get("source"),
                "Target": c.get("projection", {}).get("target_px"),
                "Confidence": c.get("projection", {}).get("confidence"),
            } for c in us_front[:20]])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No US front-run candidates")

    # ── TAB 3: TICKER DETAIL ──
    with tab_detail:
        ac = snap.get("alpha_center", {})
        all_us = sorted({i.get("ticker") for i in ac.get("all", []) if not any(s in i.get("ticker", "") for s in [".JK", "=X", "=F", "-USD"])})
        if all_us:
            selected = st.selectbox("Select US ticker", all_us)
            if selected:
                _render_ticker_detail(selected, snap)

                # FINRA Dark Pool
                finra = snap.get("finra_short", {}).get(selected, {})
                if finra:
                    st.divider()
                    st.subheader("🌑 FINRA Dark Pool / Off-Exchange Short Volume")
                    c1, c2, c3 = st.columns(3)
                    with c1: st.metric("Short Vol %", f"{finra.get('short_vol_pct', 0):.1f}%")
                    with c2: st.metric("Signal", finra.get("signal", "NEUTRAL"))
                    with c3: st.metric("Confidence", f"{finra.get('confidence', 0):.0f}%")
                    if finra.get("trend"):
                        st.caption(f"Trend: {finra['trend']} | Days: {finra.get('days_observed', 0)}")

                # Options Data
                opts = snap.get("options_data", {}).get(selected, {})
                if opts:
                    st.divider()
                    st.subheader("📊 Options Data")
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: st.metric("Max Pain", opts.get("max_pain"))
                    with c2: st.metric("Call Wall", opts.get("call_wall"))
                    with c3: st.metric("Put Wall", opts.get("put_wall"))
                    with c4: st.metric("Net GEX", opts.get("net_gex"))
                    if opts.get("greeks_proxy"):
                        st.json(opts["greeks_proxy"])
                    if opts.get("source"):
                        st.caption(f"Source: {opts['source']}")
        else:
            st.info("No US tickers available")
