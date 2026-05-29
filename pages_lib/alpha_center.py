"""alpha_center.py — Alpha Center v40.7 HIGH ASYMMETRY ONLY

ALPHA DEFINITION: Ticker dengan potensi 100-1000x% upside dalam 12-18 bulan.
Bukan MSFT +5% sebulan. Bukan swing 5-30%.

Sections:
 1. 🔥 Keith Fractal Breadth Meter
 2. 🚀 High Asymmetry Picks (100-1000x% upside) — Dynamic upside dari RR data
"""
import streamlit as st
import pandas as pd

# ── HIGH ASYMMETRY UNIVERSE (Stage 1-2 = highest potential) ──
HIGH_ASYM_UNIVERSE = {
    # Stage 1: Rare Earth / Critical Minerals / Micro Cap (highest asymmetry)
    "MP": {"layer": "Rare Earth", "stage": 1, "thesis": "MP Materials — US rare earth, China export controls, dari $15 ke $150+"},
    "LYSDY": {"layer": "Rare Earth", "stage": 1, "thesis": "Lynas — only Western rare earth miner, dari $2 ke $20+"},
    "UROY": {"layer": "Uranium", "stage": 1, "thesis": "Uranium Royalty — leverage to uranium price, dari $1 ke $10+"},
    "CCJ": {"layer": "Uranium", "stage": 1, "thesis": "Cameco — uranium supply deficit + reactor restart, dari $30 ke $300+"},
    "BRMS.JK": {"layer": "Gold", "stage": 1, "thesis": "Bumi Resources Minerals — gold explorer micro cap, dari $50 ke $500+"},
    "NCKL.JK": {"layer": "Nickel", "stage": 1, "thesis": "Nickel Industries — EV battery + Indonesia dominance, dari $100 ke $1000+"},
    "SMR": {"layer": "Nuclear/SMR", "stage": 1, "thesis": "NuScale SMR — regulatory inflection, dari $10 ke $100+"},
    "OKLO": {"layer": "Nuclear/SMR", "stage": 1, "thesis": "Oklo — Sam Altman backed SMR pioneer, dari $5 ke $50+"},
    # Stage 2: Tankers / Shipping / Commodity (high asymmetry)
    "FRO": {"layer": "Tankers", "stage": 2, "thesis": "Frontline — VLCC rates + Red Sea disruption, dari $15 ke $60+"},
    "TK": {"layer": "Tankers", "stage": 2, "thesis": "Teekay — tanker fleet aging, dari $5 ke $25+"},
    "INSW": {"layer": "Tankers", "stage": 2, "thesis": "International Seaways — M&A + rate surge, dari $40 ke $120+"},
    "STNG": {"layer": "Tankers", "stage": 2, "thesis": "Scorpio Tankers — product tanker squeeze, dari $60 ke $180+"},
    "MSTR": {"layer": "BTC Proxy", "stage": 2, "thesis": "MicroStrategy — BTC leverage play, 2x+ BTC upside, dari $300 ke $1500+"},
    "ADRO.JK": {"layer": "Coal", "stage": 2, "thesis": "Adaro — seaborne thermal + Indonesia export, dari $2000 ke $8000+"},
    "ITMG.JK": {"layer": "Coal", "stage": 2, "thesis": "Indo Tambangraya — coal royalty model, dari $10000 ke $40000+"},
    # Stage 3: Power / Infrastructure (medium-high asymmetry)
    "VST": {"layer": "Power/Cooling", "stage": 3, "thesis": "Vistra — nuclear renaissance + AI power contracts, dari $100 ke $300+"},
    "CEG": {"layer": "Power/Cooling", "stage": 3, "thesis": "Constellation Energy — nuclear + AI, dari $200 ke $600+"},
    "BE": {"layer": "Power/Cooling", "stage": 3, "thesis": "Bloom Energy — fuel cells for datacenters, dari $20 ke $80+"},
    "NXT": {"layer": "CPO/Connectors", "stage": 3, "thesis": "Nextracker — AI datacenter CPO, dari $40 ke $120+"},
    "AMPH": {"layer": "CPO/Connectors", "stage": 3, "thesis": "Amphenol — co-packaged optics, dari $30 ke $90+"},
    "HLIT": {"layer": "CPO/Connectors", "stage": 3, "thesis": "Harmonic — optical networking AI backbone, dari $10 ke $40+"},
    # Stage 4: Optics / Semis (medium asymmetry)
    "COHR": {"layer": "Optics", "stage": 4, "thesis": "Coherent — 800G/1.6T transceiver, dari $50 ke $150+"},
    "LITE": {"layer": "Optics", "stage": 4, "thesis": "Lumentum — Apple + AI datacenter, dari $60 ke $180+"},
    "MRVL": {"layer": "Optics", "stage": 4, "thesis": "Marvell — custom silicon + optics, dari $70 ke $210+"},
    "COIN": {"layer": "Exchange", "stage": 4, "thesis": "Coinbase — crypto infra + derivatives, dari $200 ke $600+"},
    "HOOD": {"layer": "Retail/Trading", "stage": 4, "thesis": "Robinhood — crypto + international, dari $40 ke $120+"},
    # Stage 5: Fertilizer / Materials (lower asymmetry tapi still >100%)
    "NTR": {"layer": "Fertilizer", "stage": 5, "thesis": "Nutrien — natgas squeeze + food security, dari $50 ke $100+"},
    "MOS": {"layer": "Fertilizer", "stage": 5, "thesis": "Mosaic — phosphate oligopoly, dari $30 ke $60+"},
    "CF": {"layer": "Fertilizer", "stage": 5, "thesis": "CF Industries — ammonia + hydrogen, dari $70 ke $140+"},
    "ANTM.JK": {"layer": "Gold", "stage": 5, "thesis": "Aneka Tambang — gold + central bank buying, dari $2000 ke $4000+"},
    "BBRI.JK": {"layer": "Banking", "stage": 5, "thesis": "BRI — NIM expansion + credit growth, dari $3000 ke $6000+"},
    "BMRI.JK": {"layer": "Banking", "stage": 5, "thesis": "Mandiri — largest bank dividend, dari $4000 ke $8000+"},
}


def _get_price(ticker, prices, rr_data):
    """Get current price from RR data or prices dict."""
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
    """Get TAIL TRR from RR data (farthest target = highest upside)."""
    rr = rr_data.get(ticker, {})
    if not isinstance(rr, dict):
        return None
    tail = rr.get("tail", {})
    if isinstance(tail, dict):
        return tail.get("trr")
    return None


def _get_trend_trr(ticker, rr_data):
    """Get TREND TRR from RR data (mid target)."""
    rr = rr_data.get(ticker, {})
    if not isinstance(rr, dict):
        return None
    trend = rr.get("trend", {})
    if isinstance(trend, dict):
        return trend.get("trr")
    return None


def _calc_upside(px, target):
    """Calculate upside percentage."""
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
        st.info(f"⚖️ NEUTRAL BREADTH — Mixed signals. Curation required.")
    st.divider()


def _render_high_asymmetry(snap):
    st.markdown("### 🚀 HIGH ASYMMETRY PICKS (100-1000x% upside)")
    st.caption("ALPHA = ticker yang bisa naik 3x-10x-50x dalam 12-18 bulan. Bukan MSFT +5% sebulan.")

    keith_signals = snap.get("keith_signals", {}) or {}
    rr_data = snap.get("risk_range", {}).get("asset_ranges", {}) if isinstance(snap.get("risk_range"), dict) else {}
    prices = snap.get("prices", {})

    # Build picks with DYNAMIC upside calculation
    picks = []
    for ticker, meta in HIGH_ASYM_UNIVERSE.items():
        ks = keith_signals.get(ticker, {})
        keith_trade = ks.get("keith_trade", "NEUTRAL") if isinstance(ks, dict) else "NEUTRAL"

        px = _get_price(ticker, prices, rr_data)
        tail_trr = _get_tail_trr(ticker, rr_data)
        trend_trr = _get_trend_trr(ticker, rr_data)

        upside_tail = _calc_upside(px, tail_trr)
        upside_trend = _calc_upside(px, trend_trr)

        # Use highest available upside
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

    # FILTER: minimum 30% upside (user adjustable)
    min_upside = st.select_slider(
        "🎯 Minimum Upside Threshold (%)",
        options=[30, 50, 100, 200, 500, 1000],
        value=100,
        help="ALPHA = minimum 100% upside. 30% = swing trade. 5% = dagang tahu.",
    )

    filtered = [p for p in picks if p["upside"] is not None and p["upside"] >= min_upside]
    filtered.sort(key=lambda x: (x["upside"] or 0), reverse=True)

    st.caption(f"📊 {len(filtered)} tickers dengan upside ≥ {min_upside}% (dari {len(picks)} universe)")
    st.divider()

    if not filtered:
        st.warning(f"❌ No tickers match {min_upside}% upside. Lower threshold or check RR data.")
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
                    st.metric("Price", "—")
                st.caption(f"Keith: {pick['keith']}")
            with c3:
                if pick["upside"] is not None:
                    st.metric("Upside", f"+{pick['upside']:.0f}%")
                    st.caption("to TAIL TRR" if pick["upside_tail"] else "to TREND TRR")
                else:
                    st.metric("Upside", "N/A")
            with c4:
                if pick["tail_trr"]:
                    st.metric("TAIL TRR", f"${pick['tail_trr']:.2f}")
                elif pick["trend_trr"]:
                    st.metric("TREND TRR", f"${pick['trend_trr']:.2f}")

            # Progress bar: current price vs target
            if pick["px"] and pick["tail_trr"] and pick["tail_trr"] > pick["px"]:
                progress = pick["px"] / pick["tail_trr"]
                st.progress(min(progress, 1.0))
                st.caption(f"Current ${pick['px']:.2f} → Target ${pick['tail_trr']:.2f} ({pick['upside']:.0f}% upside)")
            elif pick["px"] and pick["trend_trr"] and pick["trend_trr"] > pick["px"]:
                progress = pick["px"] / pick["trend_trr"]
                st.progress(min(progress, 1.0))
                st.caption(f"Current ${pick['px']:.2f} → Target ${pick['trend_trr']:.2f} ({pick['upside']:.0f}% upside)")

            # Keith signal badge
            if pick["keith"] == "BULLISH":
                st.success("🟢 Keith BULLISH — Fractal signal aligned")
            elif pick["keith"] == "BEARISH":
                st.error("🔴 Keith BEARISH — Avoid")
            else:
                st.info("⚪ Keith NEUTRAL — Cek composite signal")

    st.divider()
    st.markdown("""
    <div style='background:#161B22;border:1px solid #30363D;border-radius:8px;padding:12px;'>
    <b>🎯 ALPHA DEFINITION:</b> Ticker dengan potensi <b>100-1000x% upside</b> dalam 12-18 bulan.
    <br>Contoh: SNDK $30 → $1500 (50x). Bukan MSFT +5% sebulan.
    <br><i>"Kalo 1 bulan naik 5% mending dagang tahu bos lebih untung"</i> — @edgani
    </div>
    """, unsafe_allow_html=True)


def render(snap: dict):
    """Render Alpha Center v40.7 — High Asymmetry ONLY."""
    st.title("⚡ Alpha Center v40.7")
    st.caption("HIGH ASYMMETRY ONLY — 100-1000x% upside. Bukan swing 5-30%.")

    _render_keith_breadth(snap)
    _render_high_asymmetry(snap)
