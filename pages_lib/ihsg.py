"""ihsg.py — IHSG (Indonesia) Tab v40.8 (Keith Filtered + Fallback)

Renders tickers dari snap["ihsg"] — pakai Keith filtered kalau ada, kalau tidak fallback ke semua.
"""
import streamlit as st
import pandas as pd


def render(snap: dict):
    st.title("🇮🇩 IHSG (Indonesia)")

    # Get Keith filtered tickers
    keith_filtered = snap.get("ihsg_keith_filtered", [])
    keith_meta = snap.get("ihsg_keith_meta", {})

    # Get all tickers for this tab
    tab_data = snap.get("ihsg", {})
    if not isinstance(tab_data, dict):
        st.warning("No data for this market tab.")
        return

    all_tickers = list(tab_data.keys())

    # FIX v40.8: kalau keith_filtered kosong list [], tetap fallback ke all_tickers
    if keith_filtered and len(keith_filtered) > 0:
        display_tickers = [t for t in all_tickers if t in keith_filtered]
        st.caption(f"🔥 Keith Curated: {len(display_tickers)} tickers (dari {len(all_tickers)} total)")
        if keith_meta:
            st.caption(f"Theme: {keith_meta.get('theme', '—')} | Breadth: {keith_meta.get('breadth_signal', '—')}")
    else:
        display_tickers = all_tickers
        st.caption(f"⚠️ Keith filter empty — showing {len(display_tickers)} tickers (full universe)")

    if not display_tickers:
        st.info("No tickers to display.")
        return

    # Get RR data
    rr_data = snap.get("risk_range", {}).get("asset_ranges", {}) if isinstance(snap.get("risk_range"), dict) else {}
    prices = snap.get("prices", {})
    keith_signals = snap.get("keith_signals", {})

    # Count long/short/monitor
    longs = 0
    shorts = 0
    monitors = 0
    for t in display_tickers:
        ks = keith_signals.get(t, {})
        kt = ks.get("keith_trade", "NEUTRAL") if isinstance(ks, dict) else "NEUTRAL"
        if kt == "BULLISH":
            longs += 1
        elif kt == "BEARISH":
            shorts += 1
        else:
            monitors += 1

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TICKERS", len(display_tickers))
    c2.metric("BUY/ADD", 0)
    c3.metric("TRIM", 0)
    c4.metric("A-GRADE", 0)

    st.markdown(f"🟢 Long ({longs}) · 🔴 Short ({shorts}) · ⚪ Monitor ({monitors})")
    st.caption("Names di bullish TREND (Keith-style inventory). Per Keith: kalau cuma sedikit signal bearish, 'slim pickings on short side' → wajar banyak long.")
    st.divider()

    # Render cards
    for ticker in display_tickers[:50]:
        rr = rr_data.get(ticker, {})
        px = rr.get("px") if isinstance(rr, dict) else None
        if px is None and ticker in prices:
            try:
                s = pd.to_numeric(pd.Series(prices[ticker]), errors="coerce").dropna()
                if len(s) > 0:
                    px = float(s.iloc[-1])
            except Exception:
                pass

        ks = keith_signals.get(ticker, {})
        kt = ks.get("keith_trade", "NEUTRAL") if isinstance(ks, dict) else "NEUTRAL"

        with st.container(border=True):
            hc1, hc2 = st.columns([3, 1])
            with hc1:
                keith_37 = {"SPY", "QQQ", "IWM", "DIA", "VIX", "XLK", "XLF", "XLE", "XLI", "XLB", "XLU", "XLP", "XLY", "TLT", "IEF", "GLD", "SLV", "CL=F", "GC=F", "SI=F", "NG=F", "AAPL", "MSFT", "NVDA", "TSLA", "META", "GOOGL", "BTC-USD", "EEM", "DX-Y.NYB", "UUP", "EURUSD=X", "GBPUSD=X", "JPY=X"}
                badge = "🔥" if ticker in keith_37 else ""
                st.markdown(f"### {ticker} {badge}")
                if px:
                    st.caption(f"Price: ${px:.2f}")
                st.caption(f"Keith: {kt}")
            with hc2:
                if kt == "BULLISH":
                    st.success("LONG")
                elif kt == "BEARISH":
                    st.error("SHORT")
                else:
                    st.info("MONITOR")
