"""alpha_center.py — Curated surge candidates (5-layer filter) + Upside metrics"""
import streamlit as st


def _calc_upside_metrics(rr: dict, ticker: str) -> dict:
    """Compute thesis-progress metrics: TAIL position, distance to TRR, etc."""
    if not rr or not isinstance(rr, dict):
        return {}
    px = rr.get("px", 0)
    trade = rr.get("trade", {})
    trend = rr.get("trend", {})
    tail = rr.get("tail", {})
    # Position in TAIL (0% = at LRR/early, 100% = at TRR/late thesis)
    tail_lrr = tail.get("lrr", 0)
    tail_trr = tail.get("trr", 0)
    tail_pos = None
    if tail_trr > tail_lrr > 0:
        tail_pos = max(0, min(100, (px - tail_lrr) / (tail_trr - tail_lrr) * 100))
    # Upside to TRR
    upside_trade = ((trade.get("trr", px) - px) / px * 100) if px > 0 else 0
    upside_trend = ((trend.get("trr", px) - px) / px * 100) if px > 0 else 0
    upside_tail = ((tail_trr - px) / px * 100) if px > 0 and tail_trr > 0 else 0
    # Interpretation
    if tail_pos is None:
        thesis_stage = "—"
    elif tail_pos < 25:
        thesis_stage = "🟢 EARLY (banyak ruang naik)"
    elif tail_pos < 50:
        thesis_stage = "🟡 MID (masih ada upside)"
    elif tail_pos < 75:
        thesis_stage = "🟠 LATE-MID (hati-hati)"
    else:
        thesis_stage = "🔴 LATE (sebagian besar move sudah jalan)"
    return {
        "tail_position_pct": tail_pos,
        "upside_to_trade_trr_pct": round(upside_trade, 2),
        "upside_to_trend_trr_pct": round(upside_trend, 2),
        "upside_to_tail_trr_pct": round(upside_tail, 2),
        "thesis_stage": thesis_stage,
    }


def render(snap: dict):
    st.title("⚡ Alpha Center")
    st.caption("Curated bottleneck + surge candidates. Action = current TRADE signal. Thesis stage = where in long-term move.")

    try:
        from engines.alpha_center_curator import get_curator
        curator = get_curator()
    except Exception as e:
        st.error(f"Alpha Center curator unavailable: {e}")
        return

    keith_signals = snap.get("keith_signals", {}) or {}
    wf_results = snap.get("walkforward_results", {}) or snap.get("walkforward_results_v40", {}) or {}
    gip = snap.get("gip", {})
    current_quad = gip.get("structural_quad", "Q3") if isinstance(gip, dict) else "Q3"

    result = curator.filter_universe(
        keith_signals=keith_signals,
        wf_results=wf_results,
        current_quad=current_quad,
        min_stars=1,
    )

    passed = result["passed"]
    rejected = result["rejected"]

    # ── KPIs ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Passed", len(passed))
    c2.metric("Rejected", len(rejected))
    ma_count = sum(1 for p in passed if p["candidate"].get("ma_potential") in ("HIGH", "MEDIUM", "TARGET"))
    c3.metric("M&A Targets", ma_count)
    c4.metric("Current Quad", current_quad)

    st.divider()

    # ── Filters ──────────────────────────────────────────────────────────
    tier_filter = st.radio("Tier filter", ["All", "5★", "4★+", "3★+", "1-2★ (HRHR)"], horizontal=True)
    market_filter = st.multiselect("Market filter",
                                   ["us_equity", "ihsg", "crypto", "forex", "commodity"],
                                   default=["us_equity", "ihsg", "crypto"])
    stage_filter = st.radio("Thesis stage filter",
                            ["All", "🟢 Early only", "🟢🟡 Early-Mid", "Late not OK"],
                            horizontal=True)

    def _tier_ok(c):
        s = c["candidate"].get("stars", 0)
        if tier_filter == "All": return True
        if tier_filter == "5★": return s == 5
        if tier_filter == "4★+": return s >= 4
        if tier_filter == "3★+": return s >= 3
        if tier_filter == "1-2★ (HRHR)": return s <= 2
        return True

    filtered = [c for c in passed
                if _tier_ok(c) and c["candidate"].get("market") in market_filter]

    # Apply stage filter using RR data
    rr_data = snap.get("risk_range", {}).get("asset_ranges", {})

    def _stage_ok(entry):
        if stage_filter == "All": return True
        rr = rr_data.get(entry["ticker"], {})
        um = _calc_upside_metrics(rr, entry["ticker"])
        tp = um.get("tail_position_pct")
        if tp is None: return True  # no data, allow
        if stage_filter == "🟢 Early only": return tp < 25
        if stage_filter == "🟢🟡 Early-Mid": return tp < 50
        if stage_filter == "Late not OK": return tp < 75
        return True

    filtered = [e for e in filtered if _stage_ok(e)]

    # Surge Potential filter — Edward's rule: "yang punya potensi surging, bukan yang udah surging"
    min_upside_filter = st.select_slider(
        "Min upside to TAIL TRR (% — kalau di bawah ini = udah late stage, hide)",
        options=["No filter", "20%", "50%", "100%", "200%"],
        value="50%",
        help="Edward's rule: Alpha Center = surge potential, bukan udah surging. >100% = real surge candidate.",
    )
    min_upside_map = {"No filter": -100, "20%": 20, "50%": 50, "100%": 100, "200%": 200}
    min_upside = min_upside_map[min_upside_filter]

    if min_upside > -100:
        filtered_pre = filtered
        filtered = []
        for e in filtered_pre:
            rr = rr_data.get(e["ticker"], {})
            um = _calc_upside_metrics(rr, e["ticker"])
            tail_upside = um.get("upside_to_tail_trr_pct")
            # Keep if no data (might not be loaded), or upside above threshold
            if tail_upside is None or tail_upside >= min_upside:
                filtered.append(e)

    # Sort: highest TAIL upside DESC (most surge potential first), then stars
    def _sort_key(e):
        rr = rr_data.get(e["ticker"], {})
        um = _calc_upside_metrics(rr, e["ticker"])
        upside = um.get("upside_to_tail_trr_pct") or 0
        return (-upside, -e["candidate"].get("stars", 0))
    filtered.sort(key=_sort_key)

    st.caption(f"Showing **{len(filtered)}** candidates (sorted by stars desc, then earliest thesis stage first)")
    st.divider()

    # ── RENDER cards — NATIVE STREAMLIT (no HTML escaping issues) ───────
    for entry in filtered:
        ticker = entry["ticker"]
        cand = entry["candidate"]
        stars = "⭐" * cand.get("stars", 0)
        market = cand.get("market", "?").upper()
        rr = rr_data.get(ticker, {})
        upside = _calc_upside_metrics(rr, ticker)

        # IHSG: don't show SHORT actions (Edward rule: IHSG can only buy)
        action = rr.get("signals", {}).get("action", "WATCH") if rr else "NO_DATA"
        if market == "IHSG" and action in ("SHORT_RIP", "COVER"):
            action = "WATCH"

        action_emoji = {"BUY_DIP": "🟢", "ADD": "🟢", "HOLD": "⚪", "WATCH": "⚪",
                        "TRIM": "🟡", "TRIM_RIP": "🟠", "SHORT_RIP": "🔴",
                        "COVER": "🟣", "NO_DATA": "⚫"}.get(action, "⚪")

        with st.container(border=True):
            # Header row
            hc1, hc2, hc3, hc4 = st.columns([2.2, 1.2, 1.2, 1.4])
            hc1.markdown(f"### {ticker} &nbsp;{stars}")
            hc1.caption(f"{market} · {cand.get('bottleneck_layer', '—')}")
            ma = cand.get("ma_potential", "")
            if ma in ("HIGH", "MEDIUM", "TARGET"):
                hc1.markdown(f"🎯 **M&A {ma}**")

            hc2.metric("Price", f"${(rr.get('px') or 0):.2f}" if rr else "—")
            hc2.caption(f"{action_emoji} **{action}**")
            # 🚀 SURGE badge if TAIL upside > 100%
            tail_upside_val = upside.get("upside_to_tail_trr_pct") or 0
            if tail_upside_val >= 100:
                hc2.markdown("🚀 **SURGE CANDIDATE**")
            elif tail_upside_val >= 50:
                hc2.markdown("📈 **High upside**")

            # UPSIDE METRICS — answers Edward's "MU masih jalan ga?" question
            if upside:
                hc3.metric("To TRADE TRR",
                          f"{upside['upside_to_trade_trr_pct']:+.1f}%" if upside.get('upside_to_trade_trr_pct') else "—")
                hc3.caption(f"TAIL TRR: {upside['upside_to_tail_trr_pct']:+.1f}%")

                hc4.markdown(f"**Thesis Stage:**")
                hc4.markdown(f"{upside['thesis_stage']}")
                if upside.get("tail_position_pct") is not None:
                    hc4.caption(f"TAIL pos: {upside['tail_position_pct']:.0f}%")

            # Thesis
            st.markdown(f"**Thesis:** {cand.get('thesis', '')}")

            # Bottom: catalysts + correlations (compact)
            with st.expander("🔍 Detail — catalysts, correlations, RR, filter pass"):
                dc1, dc2 = st.columns(2)
                with dc1:
                    st.markdown("**📌 Catalysts 2026**")
                    for cat in cand.get("catalysts_2026", []):
                        st.caption(f"• {cat}")
                    st.markdown("**🔗 Correlations (β)**")
                    for parent, beta in cand.get("correlations", {}).items():
                        st.caption(f"  {parent}: β={beta}")
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
                        st.caption(f"💡 {sig.get('reason', '')}")
                    if cand.get("risk_notes"):
                        st.warning(f"⚠️ {cand['risk_notes']}")
                st.markdown("**✅ 5-Layer Filter:**")
                for layer_name, check in entry["checks"].items():
                    icon = "✅" if check["pass"] else "❌"
                    st.caption(f"{icon} {layer_name}: {check['msg']}")

    # ── Rejected list ───────────────────────────────────────────────────
    if rejected:
        with st.expander(f"❌ Rejected ({len(rejected)})"):
            for entry in rejected:
                fail_reasons = [f"{ln}: {ch['msg']}"
                                for ln, ch in entry["checks"].items() if not ch["pass"]]
                st.caption(f"**{entry['ticker']}** — {'; '.join(fail_reasons)}")
