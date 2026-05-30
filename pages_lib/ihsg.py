"""pages_lib/ihsg.py - IHSG v40.5 (Wired)
Patched: front-run + broker proxy (crossing/cornering/accumulation) + ihsg_specialist
"""
from __future__ import annotations
import pandas as pd
import streamlit as st

from utils.helpers import _pct_fmt, _fmt
from utils.viz_utils import _render_ticker_detail


def render(snap: dict):
    st.header("🇮🇩 IHSG (Indonesia)")

    tab_picks, tab_frontrun, tab_broker, tab_detail = st.tabs(["📈 Picks", "⚡ Front-Run", "🏛️ Broker Flow", "🔎 Ticker Detail"])

    # ── TAB 1: PICKS ──
    with tab_picks:
        ac = snap.get("alpha_center", {})
        ihsg_picks = [i for i in ac.get("passed", []) if i.get("ticker", "").endswith(".JK")]
        if ihsg_picks:
            st.subheader(f"Alpha Center IHSG Picks ({len(ihsg_picks)})")
            df = pd.DataFrame([{
                "Ticker": i.get("ticker"),
                "Grade": i.get("grade"),
                "Direction": i.get("direction"),
                "Score": i.get("priority_score"),
                "Price": i.get("price"),
            } for i in ihsg_picks])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No IHSG picks in Alpha Center")

    # ── TAB 2: FRONT-RUN ──
    with tab_frontrun:
        front_run = snap.get("front_run_candidates", [])
        ihsg_front = [c for c in front_run if c.get("market_type") == "ihsg"]
        if ihsg_front:
            st.subheader(f"IHSG Front-Run Candidates ({len(ihsg_front)})")
            df = pd.DataFrame([{
                "Ticker": c.get("ticker"),
                "Theme": c.get("theme"),
                "Priority": c.get("priority"),
                "Price": c.get("price"),
                "Why": c.get("why_front_run", "")[:80],
            } for c in ihsg_front[:15]])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No IHSG front-run candidates")

    # ── TAB 3: BROKER FLOW ──
    with tab_broker:
        broker = snap.get("ihsg_broker_proxy", {})
        if broker:
            st.subheader(f"🕵️ Broker Proxy Signals ({len(broker)} tickers)")
            rows = []
            for t, data in list(broker.items())[:30]:
                rows.append({
                    "Ticker": t,
                    "Signal": data.get("signal"),
                    "Confidence": data.get("confidence"),
                    "Accumulation": data.get("real_accumulation"),
                    "Distribution": data.get("real_distribution"),
                    "Crossing": data.get("crossing_detected"),
                    "Cornering": data.get("cornering_supply"),
                    "5D Ret": _pct_fmt(data.get("r5d", 0)),
                    "20D Ret": _pct_fmt(data.get("r20d", 0)),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Filter by signal type
            sig_filter = st.multiselect("Filter by signal", ["ACCUMULATION", "DISTRIBUTION", "CROSSING", "CORNERING"], default=[])
            if sig_filter:
                filtered = {k: v for k, v in broker.items() if v.get("signal") in sig_filter}
                st.write(f"Showing {len(filtered)} tickers with signal in {sig_filter}")
                for t, data in list(filtered.items())[:10]:
                    st.markdown(f"**{t}**: {data.get('signal')} (conf: {data.get('confidence')})")
        else:
            st.info("No broker proxy data — run orchestrator to populate")

        # IHSG Specialist
        spec = snap.get("ihsg_specialist", {})
        if spec:
            st.divider()
            st.subheader("🏭 IHSG Specialist v38")
            goreng = spec.get("goreng_phases", [])
            if goreng:
                st.markdown("**Goreng Phases:**")
                for g in goreng[:5]:
                    st.markdown(f"- {g.get('ticker')}: {g.get('phase')} (score: {g.get('score')})")
            cong = spec.get("conglomerate_flows", [])
            if cong:
                st.markdown("**Conglomerate Flows:**")
                for c in cong[:5]:
                    st.markdown(f"- {c.get('conglomerate')}: {c.get('flow_direction')} ({c.get('strength')})")

    # ── TAB 4: TICKER DETAIL ──
    with tab_detail:
        ac = snap.get("alpha_center", {})
        all_ihsg = sorted({i.get("ticker") for i in ac.get("all", []) if i.get("ticker", "").endswith(".JK")})
        if all_ihsg:
            selected = st.selectbox("Select IHSG ticker", all_ihsg)
            if selected:
                _render_ticker_detail(selected, snap)
                broker_data = snap.get("ihsg_broker_proxy", {}).get(selected, {})
                if broker_data:
                    st.divider()
                    st.subheader("📡 Broker Proxy Detail")
                    st.json(broker_data)
        else:
            st.info("No IHSG tickers available")
