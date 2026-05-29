"""alpha_center.py — Alpha Center v40.8 HIGH ASYMMETRY ONLY

ALPHA = 100-1000x% upside. Bukan MSFT +5%.
"""
import streamlit as st
import pandas as pd

HIGH_ASYM_UNIVERSE = {
    "MP": {"layer": "Rare Earth", "stage": 1, "thesis": "MP Materials — US rare earth, China export controls"},
    "LYSDY": {"layer": "Rare Earth", "stage": 1, "thesis": "Lynas — only Western rare earth miner"},
    "UROY": {"layer": "Uranium", "stage": 1, "thesis": "Uranium Royalty — leverage to uranium price"},
    "CCJ": {"layer": "Uranium", "stage": 1, "thesis": "Cameco — uranium supply deficit + reactor restart"},
    "BRMS.JK": {"layer": "Gold", "stage": 1, "thesis": "Bumi Resources Minerals — gold explorer micro cap"},
    "NCKL.JK": {"layer": "Nickel", "stage": 1, "thesis": "Nickel Industries — EV battery + Indonesia dominance"},
    "SMR": {"layer": "Nuclear/SMR", "stage": 1, "thesis": "NuScale SMR — regulatory inflection"},
    "OKLO": {"layer": "Nuclear/SMR", "stage": 1, "thesis": "Oklo — Sam Altman backed SMR pioneer"},
    "FRO": {"layer": "Tankers", "stage": 2, "thesis": "Frontline — VLCC rates + Red Sea disruption"},
    "TK": {"layer": "Tankers", "stage": 2, "thesis": "Teekay — tanker fleet aging"},
    "INSW": {"layer": "Tankers", "stage": 2, "thesis": "International Seaways — M&A + rate surge"},
    "STNG": {"layer": "Tankers", "stage": 2, "thesis": "Scorpio Tankers — product tanker squeeze"},
    "MSTR": {"layer": "BTC Proxy", "stage": 2, "thesis": "MicroStrategy — BTC leverage play, 2x+ BTC"},
    "ADRO.JK": {"layer": "Coal", "stage": 2, "thesis": "Adaro — seaborne thermal + Indonesia export"},
    "ITMG.JK": {"layer": "Coal", "stage": 2, "thesis": "Indo Tambangraya — coal royalty model"},
    "VST": {"layer": "Power/Cooling", "stage": 3, "thesis": "Vistra — nuclear renaissance + AI power"},
    "CEG": {"layer": "Power/Cooling", "stage": 3, "thesis": "Constellation Energy — nuclear + AI contracts"},
    "BE": {"layer": "Power/Cooling", "stage": 3, "thesis": "Bloom Energy — fuel cells for datacenters"},
    "NXT": {"layer": "CPO/Connectors", "stage": 3, "thesis": "Nextracker — AI datacenter CPO"},
    "AMPH": {"layer": "CPO/Connectors", "stage": 3, "thesis": "Amphenol — co-packaged optics"},
    "HLIT": {"layer": "CPO/Connectors", "stage": 3, "thesis": "Harmonic — optical networking AI backbone"},
    "COHR": {"layer": "Optics", "stage": 4, "thesis": "Coherent — 800G/1.6T transceiver"},
    "LITE": {"layer": "Optics", "stage": 4, "thesis": "Lumentum — Apple + AI datacenter"},
    "MRVL": {"layer": "Optics", "stage": 4, "thesis": "Marvell — custom silicon + optics"},
    "COIN": {"layer": "Exchange", "stage": 4, "thesis": "Coinbase — crypto infra + derivatives"},
    "HOOD": {"layer": "Retail/Trading", "stage": 4, "thesis": "Robinhood — crypto + international"},
    "NTR": {"layer": "Fertilizer", "stage": 5, "thesis": "Nutrien — natgas squeeze + food security"},
    "MOS": {"layer": "Fertilizer", "stage": 5, "thesis": "Mosaic — phosphate oligopoly"},
    "CF": {"layer": "Fertilizer", "stage": 5, "thesis": "CF Industries — ammonia + hydrogen"},
    "ANTM.JK": {"layer": "Gold", "stage": 5, "thesis": "Aneka Tambang — gold + central bank buying"},
    "BBRI.JK": {"layer": "Banking", "stage": 5, "thesis": "BRI — NIM expansion + credit growth"},
    "BMRI.JK": {"layer": "Banking", "stage": 5, "thesis": "Mandiri — largest bank dividend"},
}


def _get_price(ticker, prices, rr_data):
    rr = rr_data.get(ticker, {})
    px = rr.get("px") if isinstance(rr, dict) else None
    if px is not None:
        return float(px)
    if ticker in prices:
        try:
            s = pd.to_numeric(pd.Series(prices[ticker]), errors="coerce").dropna()
            if len(s) > 0:
                return float(s.iloc[-1])
        except Exception:
            pass
    return None


def _get_tail_trr(ticker, rr_data):
    rr = rr_data.get(ticker, {})
    if not isinstance(rr, dict):
        return None
    tail = rr.get("tail", {})
    return tail.get("trr") if isinstance(tail, dict) else None


def _get_trend_trr(ticker, rr_data):
    rr = rr_data.get(ticker, {})
    if not isinstance(rr, dict):
        return None
    trend = rr.get("trend", {})
    return trend.get("trr") if isinstance(trend, dict) else None


def _calc_upside(px, target):
    if px is None or target is None or px <= 0:
        return None
    return round((target - px) / px * 100, 1)


def _render_keith_breadth(snap):
    keith_breadth = snap.get("keith_breadth", {})
    if not keith_breadth or keith_breadth.get("total_signals", 0) == 0:
        st.info("Keith breadth data unavailable. Run snapshot rebuild.")
        return
    total = keith_breadth["total_signals"]
    bullish = keith_breadth.get("bullish", 0)
    bearish = keith_breadth.get("bearish", 0)
    neutral = keith_breadth.get("neutral", 0)
    bullish_pct = keith_breadth.get("bullish_pct", 0)

    st.markdown("### 🔥 Keith Fractal Breadth Meter")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Signals", f"{total}")
    c2.metric("🟢 Bullish", f"{bullish}", f"{bullish_pct}%")
    c3.metric("🔴 Bearish", f"{bearish}")
    c4.metric("⚪ Neutral", f"{neutral}")
    st.progress(bullish_pct / 100)
    st.caption(f"Keith: 'Only {bearish} of the {total} Risk Range™ Signals signaling Bearish TREND'")
    if bullish_pct > 60:
        st.success(f"📈 BULLISH BREADTH — {bullish_pct}% bullish. Slim pickings on short side.")
    elif bearish > (total * 0.4):
        st.error(f"📉 BEARISH BREADTH — {bearish}/{total} bearish. Defensive posture.")
    else:
        st.info(f"⚖️ NEUTRAL BREADTH — Mixed signals.")
    st.divider()


def _render_high_asymmetry(snap):
    st.markdown("### 🚀 HIGH ASYMMETRY PICKS (100-1000x% upside)")
    st.caption("ALPHA = ticker yang bisa naik 3x-10x-50x dalam 12-18 bulan. Bukan MSFT +5% sebulan.")

    keith_signals = snap.get("keith_signals", {}) or {}
    rr_data = snap.get("risk_range", {}).get("asset_ranges", {}) if isinstance(snap.get("risk_range"), dict) else {}
    prices = snap.get("prices", {})

    # Build ALL picks (even without RR data)
    picks = []
    for ticker, meta in HIGH_ASYM_UNIVERSE.items():
        ks = keith_signals.get(ticker, {})
        keith_trade = ks.get("keith_trade", "NEUTRAL") if isinstance(ks, dict) else "NEUTRAL"

        px = _get_price(ticker, prices, rr_data)
        tail_trr = _get_tail_trr(ticker, rr_data)
        trend_trr = _get_trend_trr(ticker, rr_data)

        upside_tail = _calc_upside(px, tail_trr)
        upside_trend = _calc_upside(px, trend_trr)
        upside = upside_tail if upside_tail is not None else upside_trend

        stage = meta["stage"]
        if stage == 1:
            potential = "🚀🚀🚀 MOONSHOT"
        elif stage == 2:
            potential = "🚀🚀 HIGH"
        elif stage == 3:
            potential = "🚀 MEDIUM-HIGH"
        else:
            potential = "📈 MEDIUM"

        picks.append({
            "ticker": ticker,
            "layer": meta["layer"],
            "stage": stage,
            "thesis": meta["thesis"],
            "keith": keith_trade,
            "px": px,
            "tail_trr": tail_trr,
            "trend_trr": trend_trr,
            "upside_tail": upside_tail,
            "upside_trend": upside_trend,
            "upside": upside,
            "potential": potential,
        })

    # FILTER: user adjustable, default 30% (not 100% — so more tickers show)
    min_upside = st.select_slider(
        "🎯 Minimum Upside Threshold (%)",
        options=[0, 30, 50, 100, 200, 500, 1000],
        value=0,  # DEFAULT 0 = show ALL tickers even without RR data
        help="0 = show all. 30 = swing. 100 = alpha. 1000 = moonshot.",
    )

    # Filter: if upside is None (no RR data), show if min_upside == 0
    if min_upside == 0:
        filtered = picks  # Show ALL
    else:
        filtered = [p for p in picks if p["upside"] is not None and p["upside"] >= min_upside]

    filtered.sort(key=lambda x: (x["upside"] or 0), reverse=True)

    st.caption(f"📊 {len(filtered)} tickers (dari {len(picks)} universe)")
    st.divider()

    if not filtered:
        st.warning(f"❌ No tickers match {min_upside}% upside. Lower threshold.")
        return

    for pick in filtered:
        ticker = pick["ticker"]
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            with c1:
                st.markdown(f"### {ticker} {pick['potential']}")
                st.caption(f"{pick['layer']} · Stage {pick['stage']}")
                st.caption(f"💡 {pick['thesis']}")
            with c2:
                if pick["px"]:
                    st.metric("Price", f"${pick['px']:.2f}")
                else:
                    st.metric("Price", "N/A")
                st.caption(f"Keith: {pick['keith']}")
            with c3:
                if pick["upside"] is not None:
                    st.metric("Upside", f"+{pick['upside']:.0f}%")
                else:
                    st.metric("Upside", "N/A")
                    st.caption("No RR data — rebuild snapshot")
            with c4:
                if pick["tail_trr"]:
                    st.metric("TAIL TRR", f"${pick['tail_trr']:.2f}")
                elif pick["trend_trr"]:
                    st.metric("TREND TRR", f"${pick['trend_trr']:.2f}")
                else:
                    st.metric("Target", "N/A")

            # Progress bar
            if pick["px"] and pick["tail_trr"] and pick["tail_trr"] > pick["px"]:
                progress = pick["px"] / pick["tail_trr"]
                st.progress(min(progress, 1.0))
                st.caption(f"${pick['px']:.2f} → ${pick['tail_trr']:.2f} ({pick['upside']:.0f}% upside)")
            elif pick["px"] and pick["trend_trr"] and pick["trend_trr"] > pick["px"]:
                progress = pick["px"] / pick["trend_trr"]
                st.progress(min(progress, 1.0))
                st.caption(f"${pick['px']:.2f} → ${pick['trend_trr']:.2f} ({pick['upside']:.0f}% upside)")
            else:
                st.caption("⚠️ No target price available — rebuild snapshot for TRR/LRR data")

            # Keith badge
            if pick["keith"] == "BULLISH":
                st.success("🟢 Keith BULLISH")
            elif pick["keith"] == "BEARISH":
                st.error("🔴 Keith BEARISH — AVOID")
            else:
                st.info("⚪ Keith NEUTRAL")

    st.divider()
    st.markdown("""
    <div style='background:#161B22;border:1px solid #30363D;border-radius:8px;padding:12px;'>
    <b>🎯 ALPHA DEFINITION:</b> Ticker dengan potensi <b>100-1000x% upside</b> dalam 12-18 bulan.
    <br>Contoh: SNDK $30 → $1500 (50x). Bukan MSFT +5% sebulan.
    <br><i>"Kalo 1 bulan naik 5% mending dagang tahu bos lebih untung"</i> — @edgani
    </div>
    """, unsafe_allow_html=True)


def render(snap: dict):
    st.title("⚡ Alpha Center v40.8")
    st.caption("HIGH ASYMMETRY ONLY — 100-1000x% upside. Bukan swing 5-30%.")
    _render_keith_breadth(snap)
    _render_high_asymmetry(snap)
