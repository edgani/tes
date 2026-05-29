"""ihsg.py — IHSG (Indonesia) Tab v40.9

Renders ALL tickers dari snap["ihsg"]. Keith filter sebagai overlay, bukan blocker.
"""
import streamlit as st
import pandas as pd


def render(snap: dict):
    st.title("🇮🇩 IHSG (Indonesia)")

    # Get tab data
    tab_data = snap.get("ihsg", {})
    if not isinstance(tab_data, dict) or not tab_data:
        st.warning("No data for this market tab. Run Rebuild.")
        return

    all_tickers = list(tab_data.keys())

    # Get Keith filtered (overlay, not blocker)
    keith_filtered = snap.get("ihsg_keith_filtered", [])
    keith_meta = snap.get("ihsg_keith_meta", {})

    if keith_filtered and len(keith_filtered) > 0:
        st.caption(f"🔥 Keith Curated overlay: {len(keith_filtered)} tickers | Total universe: {len(all_tickers)}")
    else:
        st.caption(f"📊 Total universe: {len(all_tickers)} tickers")

    # Get RR data + prices + keith signals
    rr_data = snap.get("risk_range", {}).get("asset_ranges", {}) if isinstance(snap.get("risk_range"), dict) else {}
    prices = snap.get("prices", {})
    keith_signals = snap.get("keith_signals", {})

    # Count long/short/monitor
    longs = 0; shorts = 0; monitors = 0
    for t in all_tickers:
        ks = keith_signals.get(t, {})
        kt = ks.get("keith_trade", "NEUTRAL") if isinstance(ks, dict) else "NEUTRAL"
        if kt == "BULLISH": longs += 1
        elif kt == "BEARISH": shorts += 1
        else: monitors += 1

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TICKERS", len(all_tickers))
    c2.metric("🟢 Long", longs)
    c3.metric("🔴 Short", shorts)
    c4.metric("⚪ Monitor", monitors)

    st.caption("Keith-style inventory: BULLISH = Long, BEARISH = Short, NEUTRAL = Monitor")
    st.divider()

    # Render cards
    for ticker in all_tickers[:100]:  # Limit 100 for performance
        rr = rr_data.get(ticker, {})
        px = rr.get("px") if isinstance(rr, dict) else None
        if px is None and ticker in prices:
            try:
                s = pd.to_numeric(pd.Series(prices[ticker]), errors="coerce").dropna()
                if len(s) > 0: px = float(s.iloc[-1])
            except Exception: pass

        ks = keith_signals.get(ticker, {})
        kt = ks.get("keith_trade", "NEUTRAL") if isinstance(ks, dict) else "NEUTRAL"
        is_keith = ticker in keith_filtered if keith_filtered else False

        with st.container(border=True):
            hc1, hc2 = st.columns([3, 1])
            with hc1:
                badge = "🔥" if is_keith else ""
                st.markdown(f"### {ticker} {badge}")
                if px: st.caption(f"Price: ${px:.2f}")
                st.caption(f"Keith: {kt}")
            with hc2:
                if kt == "BULLISH": st.success("LONG")
                elif kt == "BEARISH": st.error("SHORT")
                else: st.info("MONITOR")
