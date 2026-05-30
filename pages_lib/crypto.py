"""pages_lib/crypto.py - Crypto v40.5 (Wired)
Patched: front-run + crypto_tokens on-chain + whale signals + unlock calendar
"""
from __future__ import annotations
import pandas as pd
import streamlit as st

from utils.helpers import _pct_fmt, _fmt
from utils.viz_utils import _render_ticker_detail


def render(snap: dict):
    st.header("₿ Crypto")

    tab_picks, tab_frontrun, tab_onchain, tab_detail = st.tabs(["📈 Picks", "⚡ Front-Run", "⛓️ On-Chain", "🔎 Ticker Detail"])

    # ── TAB 1: PICKS ──
    with tab_picks:
        ac = snap.get("alpha_center", {})
        crypto_picks = [i for i in ac.get("passed", []) if "-USD" in i.get("ticker", "")]
        if crypto_picks:
            st.subheader(f"Alpha Center Crypto Picks ({len(crypto_picks)})")
            df = pd.DataFrame([{
                "Ticker": i.get("ticker"),
                "Grade": i.get("grade"),
                "Direction": i.get("direction"),
                "Score": i.get("priority_score"),
                "Price": i.get("price"),
            } for i in crypto_picks])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No crypto picks in Alpha Center")

    # ── TAB 2: FRONT-RUN ──
    with tab_frontrun:
        front_run = snap.get("front_run_candidates", [])
        crypto_front = [c for c in front_run if c.get("market_type") == "crypto"]
        if crypto_front:
            st.subheader(f"Crypto Front-Run Candidates ({len(crypto_front)})")
            df = pd.DataFrame([{
                "Ticker": c.get("ticker"),
                "Theme": c.get("theme"),
                "Priority": c.get("priority"),
                "Price": c.get("price"),
                "Target": c.get("projection", {}).get("target_px"),
                "Confidence": c.get("projection", {}).get("confidence"),
            } for c in crypto_front[:15]])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No crypto front-run candidates")

    # ── TAB 3: ON-CHAIN ──
    with tab_onchain:
        tokens = snap.get("crypto_tokens", {})
        onchain = snap.get("onchain_data", {})

        if tokens:
            st.subheader("🐋 Whale Signals (Proxy)")
            rows = []
            for t, data in list(tokens.items())[:10]:
                rows.append({
                    "Token": t,
                    "Price": data.get("price"),
                    "Whale Signal": data.get("whale_signal"),
                    "7D Change": _pct_fmt(data.get("tvl_7d_change", 0)),
                    "30D Change": _pct_fmt(data.get("tvl_30d_change", 0)),
                    "Funding": data.get("funding_proxy"),
                    "Funding Extreme": data.get("funding_extreme"),
                    "OI Proxy": data.get("oi_proxy"),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No whale signal data")

        if onchain:
            st.divider()
            st.subheader("⛓️ On-Chain Metrics (DeFiLlama)")
            for t, data in list(onchain.items())[:5]:
                with st.expander(t):
                    st.json(data)

        # Unlock Calendar
        cc = snap.get("crypto_center", {})
        unlocks = cc.get("tokenomics", {}).get("upcoming_unlocks", [])
        if unlocks:
            st.divider()
            st.subheader("🔓 Token Unlock Calendar")
            df = pd.DataFrame(unlocks)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ── TAB 4: TICKER DETAIL ──
    with tab_detail:
        ac = snap.get("alpha_center", {})
        all_crypto = sorted({i.get("ticker") for i in ac.get("all", []) if "-USD" in i.get("ticker", "")})
        if all_crypto:
            selected = st.selectbox("Select crypto ticker", all_crypto)
            if selected:
                _render_ticker_detail(selected, snap)
                token_data = snap.get("crypto_tokens", {}).get(selected, {})
                if token_data:
                    st.divider()
                    st.subheader("📡 Proxy Metrics")
                    c1, c2, c3 = st.columns(3)
                    with c1: st.metric("Whale Signal", token_data.get("whale_signal", "N/A"))
                    with c2: st.metric("Funding Proxy", f"{token_data.get('funding_proxy', 0):.6f}")
                    with c3: st.metric("OI Proxy", token_data.get("oi_proxy"))
        else:
            st.info("No crypto tickers available")
