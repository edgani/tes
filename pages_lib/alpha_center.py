"""alpha_center.py — Bottleneck + Surge Potential UI v40.2

Renders Edward's enriched curator (alpha_center_curator.py) with full thesis details:
  • Ticker, current price (if available), thesis, bottleneck_reason
  • Correlations (NVDA↔AMKR, AVGO↔CoWoS etc.)
  • Potential upside (multi-bag indicator)
  • Risk + Source attribution
  • Sortable, filterable by tier, market, upside potential
"""
import streamlit as st


def _parse_conviction_upside(upside_str: str) -> float:
    """Extract MAX upside % from the thesis string (e.g. '+300-1000%' → 1000).
    Used to rank true asymmetric alpha (moonshots) above large-cap appreciation."""
    import re
    if not upside_str:
        return 0.0
    nums = re.findall(r'(\d+)', upside_str.replace(",", ""))
    if not nums:
        return 0.0
    return max(float(n) for n in nums)


def _calc_upside_metrics(rr: dict) -> dict:
    """Compute thesis-progress metrics: TAIL position, distance to TRR, TARGET PRICES."""
    if not rr or not isinstance(rr, dict):
        return {}
    px = rr.get("px", 0) or 0
    trade = rr.get("trade", {}) or {}
    trend = rr.get("trend", {}) or {}
    tail = rr.get("tail", {}) or {}
    tail_lrr = tail.get("lrr", 0) or 0
    tail_trr = tail.get("trr", 0) or 0
    trade_trr = trade.get("trr", 0) or 0
    trend_trr = trend.get("trr", 0) or 0
    tail_pos = None
    if tail_trr > tail_lrr > 0 and px > 0:
        tail_pos = max(0, min(100, (px - tail_lrr) / (tail_trr - tail_lrr) * 100))
    upside_trade = ((trade_trr - px) / px * 100) if px > 0 else 0
    upside_trend = ((trend_trr - px) / px * 100) if px > 0 else 0
    upside_tail = ((tail_trr - px) / px * 100) if px > 0 and tail_trr > 0 else 0
    if tail_pos is None:
        thesis_stage = "—"
    elif tail_pos < 25:
        thesis_stage = "🟢 EARLY (banyak ruang surge)"
    elif tail_pos < 50:
        thesis_stage = "🟡 MID (masih ada upside)"
    elif tail_pos < 75:
        thesis_stage = "🟠 LATE-MID (hati-hati)"
    else:
        thesis_stage = "🔴 LATE (sebagian besar move udah jalan)"
    return {
        "tail_position_pct": tail_pos,
        "upside_to_trade_trr_pct": round(upside_trade, 2),
        "upside_to_trend_trr_pct": round(upside_trend, 2),
        "upside_to_tail_trr_pct": round(upside_tail, 2),
        "thesis_stage": thesis_stage,
        # TARGET PRICES (Edward request: bukan cuma %)
        "target_near": round(trade_trr, 2),     # nearest target = TRADE TRR
        "target_mid": round(trend_trr, 2),       # mid target = TREND TRR
        "target_far": round(tail_trr, 2),        # farthest target = TAIL TRR
        "current_px": round(px, 2),
    }


def _stars_html(n: int) -> str:
    return "⭐" * int(n or 0)


def render(snap: dict):
    st.title("⚡ Alpha Center — Asymmetric Moonshots")
    st.caption("**Tempat nyari ALPHA sejati**, bukan trade 5%. Buruan buat nangkep "
               "**the next SNDK ($30→$1,500), SIVE, early PLTR** — small/mid-cap dengan thesis "
               "bottleneck/monopoly/M&A yang bisa **3x–50x** kalau theses-nya jalan. "
               "Asymmetric: downside terbatas, upside gila. Ride the wave, jangan scalp.")

    try:
        from engines.alpha_center_curator import get_curator
        curator = get_curator()
    except Exception as e:
        st.error(f"Alpha Center curator unavailable: {e}")
        return

    keith_signals = snap.get("keith_signals", {}) or {}
    wf_results = snap.get("walkforward_results", {}) or snap.get("walkforward_results_v40", {}) or {}
    gip = snap.get("gip", {})
    if isinstance(gip, dict):
        current_quad = gip.get("monthly_quad") or gip.get("structural_quad") or "Q3"
    else:
        current_quad = getattr(gip, "monthly_quad", None) or getattr(gip, "structural_quad", None) or "Q3"

    result = curator.filter_universe(
        keith_signals=keith_signals, wf_results=wf_results,
        current_quad=current_quad, min_stars=1,
    )
    passed = result["passed"]
    rejected = result["rejected"]

    # ── TOP KPIs ─────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Passed", len(passed))
    multi_bag = sum(1 for p in passed if "MULTI-BAG" in p["candidate"].get("tags", []))
    c2.metric("🚀 Multi-bag candidates", multi_bag)
    ma_targets = sum(1 for p in passed if "M&A-Target" in p["candidate"].get("tags", []))
    c3.metric("🎯 M&A targets", ma_targets)
    c4.metric("Current Quad", current_quad)

    st.divider()

    # ── FILTERS ──────────────────────────────────────────────────────────
    f1, f2, f3 = st.columns([1, 1.4, 1])
    with f1:
        tier_filter = st.radio("Tier", ["All", "5★", "4★+", "3★+", "1-2★ (HRHR)"], horizontal=False)
    with f2:
        market_filter = st.multiselect(
            "Market", ["us_equity", "ihsg", "crypto", "forex", "commodity"],
            default=["us_equity", "ihsg", "crypto"],
        )
    with f3:
        tag_filter = st.multiselect(
            "Tag focus",
            ["Bottleneck", "MULTI-BAG", "M&A-Target", "AI", "Citrini", "Energy",
             "Materials", "Crypto", "IHSG", "Bandar", "Optical", "Memory",
             "Power", "Storage", "SMR", "Speculative"],
        )

    min_upside_str = st.select_slider(
        "Min upside ke TAIL TRR (% — di bawah ini = late stage, hide)",
        options=["No filter", "0%", "20%", "50%", "100%", "200%"],
        value="0%",
        help="Edward's rule: Alpha Center = potensi surging, BUKAN udah surging. >100% = true multi-bag.",
    )
    min_upside = {"No filter": -1e9, "0%": 0, "20%": 20, "50%": 50, "100%": 100, "200%": 200}[min_upside_str]

    def _tier_ok(c):
        s = c["candidate"].get("stars", 0)
        if tier_filter == "All": return True
        if tier_filter == "5★": return s == 5
        if tier_filter == "4★+": return s >= 4
        if tier_filter == "3★+": return s >= 3
        if tier_filter == "1-2★ (HRHR)": return s <= 2
        return True

    def _tag_ok(c):
        if not tag_filter: return True
        tags = c["candidate"].get("tags", [])
        return any(t in tags for t in tag_filter)

    filtered = [c for c in passed
                if _tier_ok(c) and _tag_ok(c)
                and c["candidate"].get("market") in market_filter]

    # Upside filter (if RR data available)
    rr_data = snap.get("risk_range", {}).get("asset_ranges", {}) if isinstance(snap.get("risk_range"), dict) else {}

    if min_upside > -1e9:
        filtered_pre = filtered
        filtered = []
        for e in filtered_pre:
            rr = rr_data.get(e["ticker"], {})
            if not rr:
                # No RR data — keep (don't punish for missing data)
                filtered.append(e)
                continue
            um = _calc_upside_metrics(rr)
            tu = um.get("upside_to_tail_trr_pct")
            if tu is None or tu >= min_upside:
                filtered.append(e)

    # Sort: CONVICTION UPSIDE DESC (biggest moonshot potential first), then stars
    def _sort_key(e):
        cand = e["candidate"]
        conv = _parse_conviction_upside(cand.get("potential_upside", ""))
        return (-conv, -cand.get("stars", 0), e["ticker"])
    filtered.sort(key=_sort_key)

    # Split into HAS_DATA and NO_DATA — hide NO_DATA from main list (Edward fix)
    has_data = [e for e in filtered if rr_data.get(e["ticker"], {}).get("px")]
    no_data = [e for e in filtered if not rr_data.get(e["ticker"], {}).get("px")]
    filtered = has_data

    st.caption(f"📊 **{len(filtered)}** candidates dengan price data (sorted: highest upside first)"
               + (f" · ⚠️ {len(no_data)} pending (no price data — di bawah)" if no_data else ""))
    st.divider()

    # ── RENDER CARDS — native Streamlit (no HTML escape issues) ──────────
    for entry in filtered:
        ticker = entry["ticker"]
        cand = entry["candidate"]
        stars = _stars_html(cand.get("stars", 0))
        market = cand.get("market", "?").upper()
        tags = cand.get("tags", [])
        rr = rr_data.get(ticker, {})
        upside = _calc_upside_metrics(rr)

        # IHSG no-short
        action = rr.get("signals", {}).get("action", "WATCH") if rr else "NO_DATA"
        if market == "IHSG" and action in ("SHORT_RIP", "COVER"):
            action = "WATCH"
        action_emoji = {"BUY_DIP": "🟢", "ADD": "🟢", "HOLD": "⚪", "WATCH": "⚪",
                        "TRIM": "🟡", "TRIM_RIP": "🟠", "SHORT_RIP": "🔴",
                        "COVER": "🟣", "NO_DATA": "⚫"}.get(action, "⚪")

        # Compute SURGE flags
        tail_upside_val = upside.get("upside_to_tail_trr_pct") or 0
        is_multi_bag = "MULTI-BAG" in tags
        is_ma_target = "M&A-Target" in tags

        with st.container(border=True):
            # ── Header row ───────────────────────────────────────────────
            hc1, hc2, hc3 = st.columns([2.4, 1.2, 1.4])
            with hc1:
                tickline = f"### {ticker} &nbsp;{stars}"
                if is_multi_bag: tickline += " &nbsp;🚀"
                if is_ma_target: tickline += " &nbsp;🎯 M&A"
                st.markdown(tickline)
                st.caption(f"{market} · {cand.get('monopoly_strength', '—')}")
                st.caption(f"💼 Sources: {', '.join(cand.get('sources', [])[:4])}")
            with hc2:
                px_str = f"${(rr.get('px') or 0):.2f}" if rr.get('px') else "—"
                st.metric("Price", px_str)
                st.caption(f"{action_emoji} **{action}**")
            with hc3:
                if upside:
                    st.metric("Upside → TAIL TRR",
                             f"{upside['upside_to_tail_trr_pct']:+.1f}%" if upside.get('upside_to_tail_trr_pct') else "—")
                    st.caption(f"🎯 {upside.get('thesis_stage', '—')}")
                pot = cand.get("potential_upside", "")
                if pot:
                    st.caption(f"📈 **{pot}**")

            # ── ALPHA ENTRY: accumulation zone + CONVICTION TARGET (ride the wave) ──
            pot = cand.get("potential_upside", "")
            conv_max = _parse_conviction_upside(pot)
            if rr and rr.get("px"):
                px_now = rr.get("px", 0)
                trade = rr.get("trade", {}) or {}
                tail = rr.get("tail", {}) or {}
                lrr = trade.get("lrr", 0) or 0
                trr = trade.get("trr", 0) or 0
                width = trr - lrr if (trr and lrr) else 0
                pos = (px_now - lrr) / width if width > 0 else 0.5
                # Accumulation zone framing (multi-year hold, not scalp)
                acc_lo = lrr
                acc_hi = lrr + width * 0.35 if width else px_now
                if pos < 0.35:
                    acc_note = f"🟢 **AKUMULASI SEKARANG** — harga ${px_now:,.2f} di zona bawah, ideal mulai bangun posisi."
                elif pos < 0.65:
                    acc_note = f"🟡 **Scale-in** — mulai sebagian sekarang (${px_now:,.2f}), tambah di dip ke ${acc_lo:,.2f}–${acc_hi:,.2f}."
                else:
                    acc_note = f"🟠 **Sabar** — harga ${px_now:,.2f} udah di atas range. Tunggu pullback ke ${acc_lo:,.2f}–${acc_hi:,.2f} buat entry asimetris."
                # Conviction target = big thesis upside (NOT the 5% TRADE band)
                conv_price = px_now * (1 + conv_max/100) if conv_max else None
                conv_line = ""
                if conv_price:
                    conv_line = f"  \n🚀 **Conviction target: {pot}** → ~${conv_price:,.2f} kalau thesis full. Ini RIDE multi-tahun, bukan scalp."
                st.markdown(f"**🎯 Alpha Entry (ride-the-wave):** {acc_note}{conv_line}")
            elif pot:
                st.markdown(f"🚀 **Conviction target: {pot}** — ride-the-wave multi-bagger. (Price data pending buat entry zone.)")

            # ── Thesis ───────────────────────────────────────────────────
            st.markdown(f"**💡 Thesis:** {cand.get('thesis', '')}")

            # ── Bottleneck reason ────────────────────────────────────────
            br = cand.get("bottleneck_reason")
            if br:
                st.info(f"🔒 **Why bottleneck:** {br}")

            # ── Correlations + Catalysts + Risk ──────────────────────────
            with st.expander("🔍 Detail — correlations, catalysts, RR, filters"):
                dc1, dc2 = st.columns(2)
                with dc1:
                    corr = cand.get("correlations", {})
                    if corr:
                        st.markdown("**🔗 Correlations**")
                        for parent, val in corr.items():
                            st.caption(f"  • **{parent}** — β/note: {val}")
                    cats = cand.get("catalysts_2026", [])
                    if cats:
                        st.markdown("**📌 Catalysts 2026**")
                        for cat in cats:
                            st.caption(f"  • {cat}")
                with dc2:
                    if rr:
                        st.markdown("**📊 TRR/LRR v20.3b**")
                        t = rr.get("trade", {})
                        tr = rr.get("trend", {})
                        tl = rr.get("tail", {})
                        st.caption(f"TRADE: ${(t.get('lrr') or 0):.2f} → ${(t.get('trr') or 0):.2f}")
                        st.caption(f"TREND: ${(tr.get('lrr') or 0):.2f} → ${(tr.get('trr') or 0):.2f}")
                        st.caption(f"TAIL:  ${(tl.get('lrr') or 0):.2f} → ${(tl.get('trr') or 0):.2f}")
                        sig = rr.get("signals", {})
                        if sig.get("reason"):
                            st.caption(f"💡 {sig['reason']}")
                    risk = cand.get("risk")
                    if risk:
                        st.warning(f"⚠️ **Risk:** {risk}")
                    rn = cand.get("risk_notes")
                    if rn:
                        st.warning(f"⚠️ {rn}")
                st.markdown("**✅ 5-Layer Filter Pass:**")
                for layer_name, check in entry["checks"].items():
                    icon = "✅" if check["pass"] else "❌"
                    st.caption(f"{icon} {layer_name}: {check['msg']}")

    if not filtered:
        st.info("No candidates match current filters. Loosen the filter to see more.")

    # ── Rejected list (compact) ──────────────────────────────────────────
    if rejected:
        with st.expander(f"❌ Rejected ({len(rejected)})"):
            for entry in rejected:
                fail_reasons = [f"{ln.replace('L', 'Layer ').replace('_', ': ')}: {ch['msg']}"
                                for ln, ch in entry["checks"].items() if not ch["pass"]]
                st.caption(f"**{entry['ticker']}** — {' · '.join(fail_reasons)}")
