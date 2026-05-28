"""rich_ticker_card.py — Comprehensive ticker rendering with narrative analysis

Per Edward's spec: setiap ticker card harus nampilin:
  • Ticker + harga saat ini
  • TRR/LRR (TRADE/TREND/TAIL)
  • **PHASE NARRATIVE** (trending bullish/bearish/sideways + reasoning)
  • **ENTRY ZONE** (di mana buy/short, take profit, R/R)
  • **OPTIONS + GREEKS narrative** (call/put walls, OI heatmap, MM positioning,
    expected move, volatility outlook, ACTIONABLE recommendation)
  • Market-specific layer (COT/on-chain/bandar) with NARRATIVE interpretation
"""
import streamlit as st


# ═══════════════════════════════════════════════════════════════════════════
# NARRATIVE GENERATORS
# ═══════════════════════════════════════════════════════════════════════════

def _phase_narrative(rr: dict) -> str:
    """Generate phase explanation in plain language."""
    if not rr:
        return "Phase data unavailable."

    phase = rr.get("phase", "NEUTRAL")
    formation = rr.get("signals", {}).get("formation", "NEUTRAL")
    trade_pos = rr.get("signals", {}).get("trade_position_pct", 50)
    hurst = rr.get("hurst", {}).get("interpretation", "RANDOM_WALK")

    parts = []

    # Trend direction
    if phase == "BULL":
        parts.append("**Trending BULLISH** (21d MA > 63d MA by +0.5%)")
    elif phase == "BEAR":
        parts.append("**Trending BEARISH** (21d MA < 63d MA by -0.5%)")
    else:
        parts.append("**Sideways** (21d MA ≈ 63d MA, no clear direction)")

    # Hurst behavior
    if hurst == "TRENDING":
        parts.append("Hurst > 0.6 → persistent trend regime, ride momentum")
    elif hurst == "MEAN_REVERTING":
        parts.append("Hurst < 0.4 → mean-reverting, fade extremes")
    else:
        parts.append("Hurst ≈ 0.5 → random walk, low signal")

    # Position in TRADE range
    if trade_pos < 25:
        parts.append(f"At **lower 25%** of TRADE range ({trade_pos:.0f}%) — kalo bullish → ADD zone")
    elif trade_pos > 75:
        parts.append(f"At **upper 25%** of TRADE range ({trade_pos:.0f}%) — kalo bullish → TRIM zone")
    else:
        parts.append(f"Mid TRADE range ({trade_pos:.0f}%) — no edge")

    # Formation
    if formation == "BULLISH":
        parts.append("Formation bullish (price > TREND TRR + TAIL TRR)")
    elif formation == "BEARISH":
        parts.append("Formation bearish (price < TREND LRR + TAIL LRR)")

    return " · ".join(parts)


def _entry_narrative(rr: dict) -> str:
    """Generate entry/exit zone explanation."""
    if not rr:
        return ""
    sig = rr.get("signals", {})
    action = sig.get("action", "HOLD")
    px = rr.get("px", 0)
    trade = rr.get("trade", {})
    trend = rr.get("trend", {})
    tail = rr.get("tail", {})

    trade_lrr = trade.get("lrr", 0) or 0
    trade_trr = trade.get("trr", 0) or 0
    trend_lrr = trend.get("lrr", 0) or 0
    trend_trr = trend.get("trr", 0) or 0
    rr_ratio = sig.get("rr_ratio", 0) or 0

    if action == "BUY_DIP":
        return (f"🎯 **BUY ZONE NOW** — price at LRR ${trade_lrr:.2f}. "
                f"Take profit di TRR ${trade_trr:.2f} (+{((trade_trr/px-1)*100):.1f}%). "
                f"Stop loss if breaks TAIL LRR ${tail.get('lrr', 0) or 0:.2f}. R/R: {rr_ratio:.2f}")
    elif action == "ADD":
        return (f"🟢 **ADD ZONE** — lower 25% of TRADE range. "
                f"Entry up to ${trade_lrr + (trade_trr-trade_lrr)*0.25:.2f}. "
                f"Trim di ${trade_trr:.2f}. R/R: {rr_ratio:.2f}")
    elif action == "HOLD":
        return (f"⚪ **HOLD** — mid range. Wait. "
                f"Add jika turun ke ${trade_lrr:.2f}, trim jika naik ke ${trade_trr:.2f}.")
    elif action == "TRIM":
        return (f"🟡 **TRIM ZONE** — upper 25% of TRADE range. "
                f"Reduce exposure now. Re-add di ${trade_lrr:.2f}.")
    elif action == "TRIM_RIP":
        return (f"🟠 **TAKE PROFIT** — price at/above TRR ${trade_trr:.2f}. "
                f"Lock in gains. Wait pullback to ${trade_lrr:.2f}.")
    elif action == "SHORT_RIP":
        return (f"🔴 **SHORT ZONE** — bearish trend, price at TRR ${trade_trr:.2f}. "
                f"Cover di LRR ${trade_lrr:.2f}. R/R: {rr_ratio:.2f}")
    elif action == "COVER":
        return (f"🟣 **COVER ZONE** — bearish, price at LRR ${trade_lrr:.2f}. "
                f"Lock short gains.")
    elif action == "WATCH":
        return f"👀 **WATCH** — wait di sini. Setup unclear. LRR ${trade_lrr:.2f} / TRR ${trade_trr:.2f}"
    return ""


def _options_narrative(opts: dict, px: float, ticker: str) -> str:
    """Generate options + Greeks narrative."""
    if not opts:
        return ""

    parts = []

    # Walls
    call_wall = opts.get("call_wall") or opts.get("call_wall_strike")
    put_wall = opts.get("put_wall") or opts.get("put_wall_strike")
    max_pain = opts.get("max_pain")
    vol_trigger = opts.get("vol_trigger")
    gex = opts.get("gex") or opts.get("net_gex")

    if call_wall:
        dist_call = (float(call_wall) - px) / px * 100 if px else 0
        parts.append(f"**Call Wall ${float(call_wall):.2f}** ({dist_call:+.1f}% away) — major resistance, MM short-gamma above")
    if put_wall:
        dist_put = (float(put_wall) - px) / px * 100 if px else 0
        parts.append(f"**Put Wall ${float(put_wall):.2f}** ({dist_put:+.1f}% away) — major support, MM long-gamma below")
    if max_pain:
        parts.append(f"**Max Pain ${float(max_pain):.2f}** — pinning target for OPEX week")
    if vol_trigger:
        dist_vt = (float(vol_trigger) - px) / px * 100 if px else 0
        parts.append(f"**Vol Trigger ${float(vol_trigger):.2f}** ({dist_vt:+.1f}%) — gamma flip level")

    # GEX regime
    if gex is not None:
        try:
            gex_val = float(gex)
            if gex_val > 0:
                parts.append(f"GEX: **+${gex_val/1e9:.2f}B** (positive) → MM long gamma → **suppressed volatility**, mean-reverting")
            else:
                parts.append(f"GEX: **${gex_val/1e9:.2f}B** (negative) → MM short gamma → **amplified moves**, volatile breakouts")
        except (TypeError, ValueError):
            pass

    # IV
    iv_rank = opts.get("iv_rank")
    pc_ratio = opts.get("put_call_ratio") or opts.get("pc_ratio")
    if iv_rank is not None:
        try:
            ivr = float(iv_rank)
            if ivr > 70:
                parts.append(f"IV Rank **{ivr:.0f}** → vol expensive, sell premium")
            elif ivr < 30:
                parts.append(f"IV Rank **{ivr:.0f}** → vol cheap, buy options")
        except (TypeError, ValueError):
            pass
    if pc_ratio is not None:
        try:
            pc = float(pc_ratio)
            if pc > 1.0:
                parts.append(f"P/C ratio **{pc:.2f}** → put-heavy = hedging/bearish positioning")
            elif pc < 0.6:
                parts.append(f"P/C ratio **{pc:.2f}** → call-heavy = greed/squeeze risk")
        except (TypeError, ValueError):
            pass

    return "\n".join(f"• {p}" for p in parts) if parts else ""


def _mm_positioning(opts: dict, px: float) -> str:
    """Market maker positioning summary."""
    if not opts: return ""
    gex = opts.get("gex") or opts.get("net_gex")
    call_wall = opts.get("call_wall") or opts.get("call_wall_strike")
    put_wall = opts.get("put_wall") or opts.get("put_wall_strike")
    expected_move = opts.get("expected_move_pct") or opts.get("expected_move")

    summary_parts = []
    try:
        if gex is not None and float(gex) > 0 and call_wall and put_wall:
            summary_parts.append(
                f"**🟢 MM LONG GAMMA → BUY DIPS WORK.** Price kemungkinan pinball "
                f"antara Put Wall ${float(put_wall):.2f} dan Call Wall ${float(call_wall):.2f}. "
                f"Volatility supressed. Sell strangle/iron condor di range ini."
            )
        elif gex is not None and float(gex) < 0:
            summary_parts.append(
                f"**🔴 MM SHORT GAMMA → AMPLIFIED MOVES.** Break above Call Wall = "
                f"chase higher (MM buyback). Break below Put Wall = waterfall down. "
                f"Buy options, jangan sell premium."
            )
    except (TypeError, ValueError): pass

    if expected_move:
        try:
            em = float(expected_move)
            summary_parts.append(f"Expected move next week: **±{em:.2f}%** (implied by ATM straddle)")
        except (TypeError, ValueError): pass

    return "\n".join(summary_parts)


def _cot_narrative(cot: dict, ticker: str) -> str:
    """COT data interpretation for Forex/Commodities."""
    if not cot: return ""
    parts = []
    nc_net = cot.get("noncomm_net") or cot.get("non_commercial_net")
    nc_chg = cot.get("noncomm_change_wow") or cot.get("noncomm_change")
    extreme = cot.get("extreme_position") or cot.get("at_extreme")

    if nc_net is not None:
        try:
            nn = float(nc_net)
            if nn > 0:
                parts.append(f"**Non-commercial NET LONG: {nn:+,.0f}** contracts (large specs bullish)")
            else:
                parts.append(f"**Non-commercial NET SHORT: {nn:+,.0f}** contracts (large specs bearish)")
        except (TypeError, ValueError): pass

    if nc_chg is not None:
        try:
            ncc = float(nc_chg)
            if abs(ncc) > 5000:
                direction = "added longs" if ncc > 0 else "added shorts" if ncc < 0 else "flat"
                parts.append(f"WoW change: {ncc:+,.0f} ({direction}) — momentum {'building' if abs(ncc) > 10000 else 'modest'}")
        except (TypeError, ValueError): pass

    if extreme:
        parts.append("⚠️ **EXTREME POSITIONING** (>2σ from 1yr avg) — contrarian setup, watch for reversal")

    return "\n".join(f"• {p}" for p in parts) if parts else ""


def _onchain_narrative(oc: dict, ticker: str) -> str:
    """On-chain accumulation/distribution narrative for Crypto."""
    if not oc: return ""
    parts = []
    whale_7d = oc.get("whale_accum_7d") or oc.get("whale_accum")
    funding = oc.get("funding_rate") or oc.get("funding_8h")
    oi_chg = oc.get("oi_change_7d") or oc.get("oi_chg")
    exch_outflow = oc.get("exchange_outflow_pct") or oc.get("exch_outflow")
    sig = oc.get("signal") or ""

    if whale_7d is not None:
        try:
            wa = float(whale_7d) * 100 if abs(float(whale_7d)) < 1 else float(whale_7d)
            if wa > 5:
                parts.append(f"**Whale ACCUMULATION** +{wa:.1f}% (7d) — top 100 wallets adding")
            elif wa < -5:
                parts.append(f"**Whale DISTRIBUTION** {wa:.1f}% (7d) — top wallets dumping")
        except (TypeError, ValueError): pass

    if funding is not None:
        try:
            f = float(funding) * 100 if abs(float(funding)) < 1 else float(funding)
            if f > 0.05:
                parts.append(f"Funding +{f:.3f}% → longs paying shorts = overheated, squeeze risk")
            elif f < -0.05:
                parts.append(f"Funding {f:.3f}% → shorts paying longs = bottom signal, short squeeze setup")
        except (TypeError, ValueError): pass

    if oi_chg is not None:
        try:
            oc_val = float(oi_chg) * 100 if abs(float(oi_chg)) < 1 else float(oi_chg)
            if abs(oc_val) > 10:
                parts.append(f"OI {oc_val:+.1f}% (7d) — {'leverage building' if oc_val > 0 else 'deleveraging'}")
        except (TypeError, ValueError): pass

    if exch_outflow is not None:
        try:
            eo = float(exch_outflow) * 100 if abs(float(exch_outflow)) < 1 else float(exch_outflow)
            if eo > 2:
                parts.append(f"Exchange outflow +{eo:.1f}% → coins moving to self-custody = bullish HODL")
            elif eo < -2:
                parts.append(f"Exchange inflow {eo:.1f}% → coins moving to exchanges = sell pressure")
        except (TypeError, ValueError): pass

    if sig:
        parts.append(f"**On-chain signal: {sig}**")

    return "\n".join(f"• {p}" for p in parts) if parts else ""


def _bandar_narrative(b: dict, ticker: str) -> str:
    """IHSG bandar (Indonesian market maker) detailed narrative.

    Based on Hengky Adinata methodology + bandarmologi research:
    - Cornering supply detection
    - 4-phase goreng cycle (akumulasi → corp action → liquiditas → euforia)
    - Foreign vs domestic broker classification
    - Cross-trade detection (same broker buying + selling = wash trade)
    - Konglomerat group flow (Bakrie, Salim, Barito, Astra, Lippo)
    """
    if not b: return ""
    parts = []

    flow_signal = b.get("flow_signal", "UNCLEAR")
    confidence = b.get("confidence", 0)

    signal_explanations = {
        "ACCUMULASI_ASLI": (
            "🟢 **AKUMULASI ASLI** — bandar lokal aktif kumpulin posisi. "
            "Pattern: bid-offer frequency tinggi di bid, broker dominan (BRPT, MNCS, dll) jadi top buyer "
            "berhari-hari, harga konsolidasi (volatility menurun). Setup goreng phase 1."
        ),
        "DISTRIBUSI_ASLI": (
            "🔴 **DISTRIBUSI ASLI** — bandar sedang exit posisi. "
            "Pattern: top sellers = broker yang sebelumnya top buyer, harga di range tinggi tapi volume menurun, "
            "bid-offer asymmetric (lebih banyak offer). EXIT NOW."
        ),
        "FAKE_AKUM": (
            "🟡 **FAKE AKUMULASI** — kelihatan akumulasi tapi cross-trade detected. "
            "Same broker code muncul di top buyer DAN top seller = wash trade. "
            "Mereka coba narik retail, jangan kena."
        ),
        "FAKE_DISTR": (
            "🟡 **FAKE DISTRIBUSI** — kelihatan distribusi tapi cross-trade detected. "
            "Bandar coba scare retail biar jual murah, mereka beli balik. Hold."
        ),
        "FORCED_SELL": (
            "🔴 **FORCED SELL / MARGIN CALL** — broker likuidasi posisi nasabah. "
            "Volume spike + price drop tajam + concentrated seller. "
            "Bisa jadi bottom signal kalo udah selesai."
        ),
        "WINDOW_DRESSING": (
            "🟣 **WINDOW DRESSING** — biasanya akhir bulan/kuartal/tahun. "
            "Bandar/MI naikin harga buat appearance NAV. Setelah period close = balik turun."
        ),
        "UNCLEAR": "⚪ Flow signal belum jelas — observasi lebih lanjut.",
    }
    parts.append(signal_explanations.get(flow_signal, signal_explanations["UNCLEAR"]))
    if confidence:
        try:
            parts.append(f"Confidence: **{float(confidence)*100:.0f}%** (broker concentration + cross-trade analysis)")
        except (TypeError, ValueError): pass

    # Top brokers
    top_buy = b.get("top_brokers_buy") or b.get("top_buyers") or []
    top_sell = b.get("top_brokers_sell") or b.get("top_sellers") or []
    if top_buy:
        broker_explanations = _broker_codes_explained(top_buy[:5], side="buy")
        parts.append(f"\n**🟢 Top Buyers:** {broker_explanations}")
    if top_sell:
        broker_explanations = _broker_codes_explained(top_sell[:5], side="sell")
        parts.append(f"**🔴 Top Sellers:** {broker_explanations}")

    # Cornering signal
    cornering = b.get("cornering_signal") or b.get("cornering") or {}
    if isinstance(cornering, dict) and cornering.get("detected"):
        thesis = cornering.get("thesis", "Floating shares mengecil drastis")
        parts.append(
            f"\n⚠️ **CORNERING SUPPLY DETECTED**\n"
            f"• Floating shares yang available di market mengecil drastis (kemungkinan <15% free float)\n"
            f"• {thesis}\n"
            f"• Implikasi: harga bisa lompat tajam ke atas karena tidak ada supply. "
            f"Tapi juga risiko: ketika bandar exit, harga collapse karena retail panic."
        )

    # Goreng phase
    goreng = b.get("goreng_phase")
    if goreng:
        phase_explanations = {
            "PHASE_1_AKUMULASI": (
                "📦 **PHASE 1 — AKUMULASI** (3-12 bulan): "
                "Bandar diam-diam beli di harga murah. Volume rendah, range sempit. "
                "Retail belum aware. Best entry point."
            ),
            "PHASE_2_CORP_ACTION": (
                "📰 **PHASE 2 — CORPORATE ACTION** (1-3 bulan): "
                "Berita keluar (right issue / akuisisi / spin-off / pembagian dividen besar). "
                "Volume mulai naik, harga break range akumulasi. Retail mulai notice."
            ),
            "PHASE_3_LIQUIDITAS": (
                "💧 **PHASE 3 — LIQUIDITAS** (1-2 bulan): "
                "Bandar marik retail dengan candle bullish yang nyolok. Volume tinggi. "
                "Influencer/media coverage mulai banyak. Bandar mulai distribute pelan-pelan."
            ),
            "PHASE_4_EUFORIA": (
                "🔥 **PHASE 4 — EUFORIA** (2-4 minggu): "
                "Harga parabolik. Retail FOMO. Volume sangat tinggi. "
                "Bandar sudah hampir habis distribusi. CRASH IMMINENT — EXIT NOW."
            ),
        }
        parts.append(f"\n{phase_explanations.get(goreng, goreng)}")

    # Konglomerat group flow
    konglo = b.get("konglomerat_group") or b.get("conglomerate")
    if konglo:
        parts.append(f"\n🏢 **Group: {konglo}** — coordinated flow detected. "
                    f"Watch cross-correlation dengan ticker satu grup.")

    return "\n".join(parts)


def _broker_codes_explained(brokers: list, side="buy") -> str:
    """Indonesian broker code classifications."""
    # Common IHSG broker codes — classify foreign vs domestic + behavior
    FOREIGN_BROKERS = {"CS", "KZ", "MS", "AK", "BK", "DB", "GS", "ML", "DX", "RG", "UU"}  # CIMB Securities, Kim Eng (Maybank), Macquarie, etc.
    LOCAL_BANDAR_BROKERS = {"BR", "BNI", "DR", "FZ", "LG", "MQ", "MU", "NI", "RX", "PD", "PG", "YP", "YU", "YJ", "ZP", "BK"}  # local market makers
    RETAIL_BROKERS = {"AT", "AZ", "MG", "OD", "PC", "BQ", "EP", "II"}  # primarily retail flow

    results = []
    for code in brokers:
        c = str(code).upper().strip()
        if c in FOREIGN_BROKERS:
            results.append(f"`{c}` (foreign)")
        elif c in LOCAL_BANDAR_BROKERS:
            results.append(f"`{c}` (local bandar)")
        elif c in RETAIL_BROKERS:
            results.append(f"`{c}` (retail flow)")
        else:
            results.append(f"`{c}`")
    return " · ".join(results)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN RENDER
# ═══════════════════════════════════════════════════════════════════════════

ACTION_COLORS = {
    "BUY_DIP": "#3FB950", "ADD": "#3FB950", "HOLD": "#D29922",
    "TRIM": "#D29922", "TRIM_RIP": "#FF8C00",
    "SHORT_RIP": "#F85149", "COVER": "#A371F7",
    "WATCH": "#8B949E", "NO_DATA": "#484F58",
}


def render_rich_ticker(
    ticker: str, rr: dict, snap: dict, market_key: str = "us_equity",
    show_options: bool = False, show_cot: bool = False,
    show_onchain: bool = False, show_bandar: bool = False,
    is_frontrun: bool = False, frontrun_info: dict = None,
):
    """Render comprehensive ticker card with all narratives.

    Args:
        ticker: symbol
        rr: TRR/LRR dict from risk_range engine
        snap: full snapshot for data lookup
        market_key: us_equity/forex/commodity/crypto/ihsg
        show_*: which overlays to enable
        is_frontrun: True for front-run tab tickers
        frontrun_info: optional chain reaction context for front-run
    """
    if not rr or not isinstance(rr, dict):
        with st.container(border=True):
            st.markdown(f"### {ticker}  &nbsp; <span style='color:#8B949E;font-size:0.7rem;'>NO DATA</span>",
                       unsafe_allow_html=True)
            st.caption("Price/RR data unavailable for this ticker.")
        return

    px = rr.get("px") or 0
    phase = rr.get("phase", "NEUTRAL")
    sig = rr.get("signals", {})
    action = sig.get("action", "HOLD")
    quality = sig.get("quality", "C")

    # IHSG no-short rule
    if market_key == "ihsg" and action in ("SHORT_RIP", "COVER"):
        action = "WATCH"

    color = ACTION_COLORS.get(action, "#8B949E")

    with st.container(border=True):
        # ── HEADER: ticker, price, action ────────────────────────────────
        hc1, hc2, hc3 = st.columns([2.2, 1.2, 1.5])
        with hc1:
            head = f"### {ticker}"
            if is_frontrun:
                head += "  🔮"
            st.markdown(head)
            st.caption(f"**Quality {quality}** · Phase **{phase}** · Formation {sig.get('formation','NEUTRAL')}")
        with hc2:
            st.metric("Price", f"${px:,.2f}" if market_key != "forex" else f"{px:.4f}")
        with hc3:
            st.markdown(
                f"<div style='background:{color};color:#0D1117;padding:8px 12px;"
                f"border-radius:6px;text-align:center;font-weight:800;font-size:0.85rem;'>"
                f"{action}</div>",
                unsafe_allow_html=True,
            )

        # ── FRONT-RUN context (kalau di front-run tab) ────────────────────
        if is_frontrun and frontrun_info:
            driver = frontrun_info.get("driver", "?")
            shock = frontrun_info.get("shock_pct", 0)
            expected = frontrun_info.get("expected_pct", 0)
            lag = frontrun_info.get("lag_days", 0)
            thesis = frontrun_info.get("thesis", "")
            chain = frontrun_info.get("chain", "")
            st.info(
                f"🔮 **Front-Run Setup:** Driver **{driver}** moved **{shock:+.2f}%** → "
                f"expected impact pada {ticker}: **{expected:+.2f}% within {lag} days**. "
                f"Chain: {chain}. {thesis}"
            )

        # ── TRR/LRR ───────────────────────────────────────────────────────
        st.markdown("**📊 TRR/LRR v20.3b (Hedgeye-style)**")
        trade = rr.get("trade", {})
        trend = rr.get("trend", {})
        tail = rr.get("tail", {})
        rrc1, rrc2, rrc3 = st.columns(3)
        with rrc1:
            st.caption("**TRADE (15d)**")
            st.caption(f"LRR: ${(trade.get('lrr') or 0):.2f}")
            st.caption(f"TRR: ${(trade.get('trr') or 0):.2f}")
        with rrc2:
            st.caption("**TREND (63d)**")
            st.caption(f"LRR: ${(trend.get('lrr') or 0):.2f}")
            st.caption(f"TRR: ${(trend.get('trr') or 0):.2f}")
        with rrc3:
            st.caption("**TAIL (3yr)**")
            st.caption(f"LRR: ${(tail.get('lrr') or 0):.2f}")
            st.caption(f"TRR: ${(tail.get('trr') or 0):.2f}")

        # ── PHASE NARRATIVE ───────────────────────────────────────────────
        st.markdown(f"**🧭 Fase saat ini:** {_phase_narrative(rr)}")

        # ── ENTRY NARRATIVE ───────────────────────────────────────────────
        entry_text = _entry_narrative(rr)
        if entry_text:
            st.markdown(entry_text)

        # ── MARKET-SPECIFIC OVERLAYS ─────────────────────────────────────
        with st.expander("🔍 Detail per market (options/COT/on-chain/bandar)", expanded=False):

            if show_options:
                opts_map = snap.get("yfinance_options", {}) or snap.get("options_data", {}) or {}
                opts = opts_map.get(ticker, {}) if isinstance(opts_map, dict) else {}
                fund_map = snap.get("fundamentals", {}) or {}
                fund = fund_map.get(ticker, {}) if isinstance(fund_map, dict) else {}

                st.markdown("**📈 Options + Greeks + Vanna/Charm (NVTS-style)**")

                # Vanna/Charm calendar — ALWAYS available (calendar-based)
                try:
                    from engines.options_greeks_engine import build_options_intelligence
                    intel = build_options_intelligence(ticker, opts, px, fund)
                    vc = intel["opex_calendar"]["vanna_charm_window"]
                    cal = intel["opex_calendar"]

                    # Vanna/Charm window status
                    st.markdown(f"**🗓️ Vanna/Charm Window** (OPEX {cal['current_opex']}, {cal['days_to_opex']}d away)")
                    st.caption(f"{vc['note']}")
                    st.caption(f"Window: {vc['start']} (open) → {vc['peak']} (peak) → {vc['end']} (charm max)")

                    # Gamma positioning
                    g = intel["gamma"]
                    if g.get("available") and g.get("regime"):
                        st.markdown(f"**🎯 Gamma Regime:** {g.get('regime_note', '')}")
                        wall_parts = []
                        if g.get("call_wall"):
                            wall_parts.append(f"Call Wall ${g['call_wall']:.2f} ({g.get('call_wall_dist_pct', 0):+.1f}%)")
                        if g.get("put_wall"):
                            wall_parts.append(f"Put Wall ${g['put_wall']:.2f} ({g.get('put_wall_dist_pct', 0):+.1f}%)")
                        if g.get("gamma_flip"):
                            flip_state = "ABOVE (positive gamma)" if g.get("above_flip") else "BELOW (negative gamma)"
                            wall_parts.append(f"Gamma Flip ${g['gamma_flip']:.2f} — price {flip_state}")
                        if g.get("max_pain"):
                            wall_parts.append(f"Max Pain ${g['max_pain']:.2f}")
                        if wall_parts:
                            for wp in wall_parts:
                                st.caption(f"• {wp}")

                    # Short squeeze
                    sq = intel["squeeze"]
                    if sq.get("available"):
                        st.markdown(f"**🩳 Short Squeeze:** {sq.get('note', '')}")
                        if sq.get("days_to_cover"):
                            st.caption(f"Days to cover: {sq['days_to_cover']}")

                    # Expected move
                    if intel.get("expected_move_pct"):
                        st.caption(f"📏 Expected move (1wk): ±{intel['expected_move_pct']:.2f}%")
                except Exception as e:
                    st.caption(f"Vanna/charm calendar: {e}")

                # Raw options narrative (walls/IV/PC)
                opt_text = _options_narrative(opts, px, ticker)
                if opt_text:
                    st.markdown("**Detail:**")
                    st.markdown(opt_text)
                elif not opts:
                    st.caption("⚠️ Live options chain belum ke-fetch. Vanna/charm calendar di atas tetap valid (date-based). "
                              "Gamma walls + squeeze butuh options data dari yfinance/Deribit.")
                mm_text = _mm_positioning(opts, px)
                if mm_text:
                    st.markdown("**🏪 MM Positioning + Volatility Outlook**")
                    st.markdown(mm_text)

            if show_cot:
                cot_map = (snap.get("cot_oi", {}) or {}).get("cot", {}) or snap.get("cot_data", {}) or {}
                cot = cot_map.get(ticker, {}) if isinstance(cot_map, dict) else {}
                st.markdown("**📋 COT (Commitments of Traders)**")
                cot_text = _cot_narrative(cot, ticker)
                if cot_text:
                    st.markdown(cot_text)
                else:
                    st.caption("COT data unavailable for this ticker.")

            if show_onchain:
                oc_map = snap.get("crypto_tokens", {}) or snap.get("onchain_data", {}) or {}
                oc = oc_map.get(ticker, {}) if isinstance(oc_map, dict) else {}
                st.markdown("**⛓️ On-Chain Activity (Accumulation/Distribution)**")
                oc_text = _onchain_narrative(oc, ticker)
                if oc_text:
                    st.markdown(oc_text)
                else:
                    st.caption("On-chain data unavailable for this ticker.")

            if show_bandar:
                bandar_map = snap.get("ihsg_broker_proxy", {}) or snap.get("ihsg_broker_data", {}) or {}
                b = bandar_map.get(ticker, {}) if isinstance(bandar_map, dict) else {}
                st.markdown("**🏦 IHSG Bandar Analysis (Cornering / Accumulation / Distribution)**")
                b_text = _bandar_narrative(b, ticker)
                if b_text:
                    st.markdown(b_text)
                else:
                    # Even without specific data, show the framework
                    st.caption(
                        "Bandar data tidak tersedia untuk ticker ini. "
                        "Manual check: broker summary, bid-offer frequency, cross-trade pattern, "
                        "konglomerat group correlation."
                    )

            # Correlation drivers (universal)
            try:
                from engines.chain_reaction_v2 import get_chain_engine
                cre = get_chain_engine()
                parents = cre.find_parents_of(ticker)
                if parents:
                    st.markdown("**🔗 Correlation Drivers (chain reaction)**")
                    for p in parents[:5]:
                        beta = p.get("beta", 0)
                        direction = "↗" if p.get("direction") == "SAME" else "↙"
                        st.caption(f"• **{p['parent']}** {direction} β={beta:.2f}, lag {p.get('lag_days', 0)}d — {p.get('thesis', '')}")
            except Exception:
                pass
