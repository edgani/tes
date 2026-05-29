"""alpha_center.py — Alpha Center UI v2.0

Renders:
 • High Asymmetry Picks (100-1000% upside) — Bottleneck stage + Market cap + Revenue growth + TAM + Keith
 • Short-term Swing (legacy R:R 2:1) — Entry/stop/target/grade
 • Keith Fractal Breadth Meter — "X of 37 signals bullish"
 • Backward compatible dengan alpha_center_curator v1 (get_curator) dan v2 (AlphaCenterCurator)
"""
import streamlit as st


def _stars_html(n: int) -> str:
    return "⭐" * int(n or 0)


def _conviction_badge(conviction: str) -> str:
    return {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴"}.get(conviction, "⚪")


def _upside_badge(potential: str) -> str:
    return {"MOON": "🚀🚀🚀", "HIGH": "🚀🚀", "MEDIUM": "🚀", "LOW": "📈"}.get(potential, "—")


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
        "target_near": round(trade_trr, 2),
        "target_mid": round(trend_trr, 2),
        "target_far": round(tail_trr, 2),
        "current_px": round(px, 2),
    }


def _render_v2(snap: dict):
    """Render Alpha Center v2 (AlphaCenterCurator v2)."""
    st.title("⚡ Alpha Center v2")

    # ── KEITH BREADTH METER ──────────────────────────────────────────────
    keith_breadth = snap.get("keith_breadth", {})
    if keith_breadth and keith_breadth.get("total_signals", 0) > 0:
        total = keith_breadth["total_signals"]
        bullish = keith_breadth.get("bullish", 0)
        bearish = keith_breadth.get("bearish", 0)
        neutral = keith_breadth.get("neutral", 0)
        bullish_pct = keith_breadth.get("bullish_pct", 0)

        st.markdown("### 🔥 Keith Fractal Breadth Meter")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Signals", total)
        c2.metric("🟢 Bullish", bullish, f"{bullish_pct}%")
        c3.metric("🔴 Bearish", bearish)
        c4.metric("⚪ Neutral", neutral)

        st.progress(bullish_pct / 100)
        st.caption(f"Keith: 'Only {bearish} of the {total} Risk Range™ Signals signaling Bearish TREND'")

        if bullish_pct > 60:
            st.success(f"📈 BULLISH BREADTH — {bullish_pct}% of Keith's 37 signals are bullish. Slim pickings on short side.")
        elif bearish > (total * 0.4):
            st.error(f"📉 BEARISH BREADTH — {bearish}/{total} signals bearish. Defensive posture.")
        else:
            st.info(f"⚖️ NEUTRAL BREADTH — Mixed signals. Curation required.")
        st.divider()

    # ── HIGH ASYMMETRY PICKS (100-1000% upside) ─────────────────────────
    ac = snap.get("alpha_center", {})
    high_asym = ac.get("high_asymmetry", {}) if isinstance(ac, dict) else {}
    passed = high_asym.get("passed", []) if isinstance(high_asym, dict) else []
    meta = high_asym.get("meta", {}) if isinstance(high_asym, dict) else {}

    st.markdown("### 🚀 High Asymmetry Picks (100-1000% upside potential)")
    st.caption(f"Quad: {meta.get('quad', '—')} | Candidates: {meta.get('total_candidates', 0)} | Passed: {meta.get('passed_count', 0)}")

    if not passed:
        st.info("No high-asymmetry candidates match current filters. Check Keith breadth or loosen filters.")
    else:
        for pick in passed:
            ticker = pick.get("ticker", "—")
            layer = pick.get("layer", "—")
            stage = pick.get("stage", 0)
            mcap_b = pick.get("mcap_b")
            rev_growth = pick.get("revenue_growth")
            tam_b = pick.get("tam_b", 0)
            moat = pick.get("moat", "—")
            keith = pick.get("keith_signal", "NEUTRAL")
            composite = pick.get("composite_signal", "NEUTRAL")
            score = pick.get("asymmetry_score", 0)
            upside = pick.get("upside_potential", "—")
            conviction = pick.get("conviction", "C")
            catalyst = pick.get("catalyst", "")

            with st.container(border=True):
                hc1, hc2, hc3, hc4 = st.columns([2, 1, 1, 1])
                with hc1:
                    st.markdown(f"### {ticker}  {_upside_badge(upside)}")
                    st.caption(f"{layer} · Stage {stage} · TAM: ${tam_b}B · Moat: {moat}")
                    if catalyst:
                        st.caption(f"📌 {catalyst}")
                with hc2:
                    st.metric("Asymmetry Score", score)
                    st.caption(f"Conviction: {_conviction_badge(conviction)} {conviction}")
                with hc3:
                    if mcap_b:
                        st.metric("Market Cap", f"${mcap_b}B")
                    if rev_growth is not None:
                        st.caption(f"Revenue Growth: {rev_growth*100:.0f}%")
                with hc4:
                    st.metric("Keith", keith)
                    st.metric("Composite", composite)
                st.progress(min(score / 100, 1.0))
    st.divider()

    # ── SHORT-TERM SWING (Legacy) ──────────────────────────────────────
    short_term = ac.get("short_term", {}) if isinstance(ac, dict) else {}
    st_swings = short_term.get("passed", []) if isinstance(short_term, dict) else []

    st.markdown("### ⚡ Short-Term Swing Setups (R:R 2:1+)")
    if not st_swings:
        st.info("No short-term setups available.")
    else:
        for swing in st_swings:
            t = swing.get("ticker", "—")
            entry = swing.get("entry")
            stop = swing.get("stop")
            target = swing.get("target")
            rr = swing.get("r_r", 0)
            grade = swing.get("grade", "C")
            keith = swing.get("keith", "NEUTRAL")

            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                with c1:
                    st.markdown(f"**{t}** — Grade {grade}")
                    if entry and stop and target:
                        st.caption(f"Entry: ${entry:.2f} → Stop: ${stop:.2f} → Target: ${target:.2f}")
                with c2:
                    st.metric("R:R", rr)
                with c3:
                    st.metric("Keith", keith)
                with c4:
                    st.caption(f"Direction: {swing.get('type', '—')}")

    # ── REJECTED / META ────────────────────────────────────────────────
    if meta and meta.get("rejected_count", 0) > 0:
        with st.expander(f"❌ Rejected ({meta.get('rejected_count', 0)} candidates)"):
            st.caption("Filtered out due to Keith BEARISH, low conviction, or missing fundamentals.")


def _render_v1(snap: dict):
    """Render Alpha Center v1 (legacy get_curator)."""
    st.title("⚡ Alpha Center")
    st.caption("**Bottleneck + Surge Potential** — tickers yang punya potensi surging (bukan yang udah). "
               "Filter strict: monopoly/near-monopoly OR potensi multi-bag (>100% upside).")

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

    rr_data = snap.get("risk_range", {}).get("asset_ranges", {}) if isinstance(snap.get("risk_range"), dict) else {}

    if min_upside > -1e9:
        filtered_pre = filtered
        filtered = []
        for e in filtered_pre:
            rr = rr_data.get(e["ticker"], {})
            if not rr:
                filtered.append(e)
                continue
            um = _calc_upside_metrics(rr)
            tu = um.get("upside_to_tail_trr_pct")
            if tu is None or tu >= min_upside:
                filtered.append(e)

    def _sort_key(e):
        rr = rr_data.get(e["ticker"], {})
        um = _calc_upside_metrics(rr)
        return (-(um.get("upside_to_tail_trr_pct") or 0),
                -e["candidate"].get("stars", 0), e["ticker"])
    filtered.sort(key=_sort_key)

    has_data = [e for e in filtered if rr_data.get(e["ticker"], {}).get("px")]
    no_data = [e for e in filtered if not rr_data.get(e["ticker"], {}).get("px")]
    filtered = has_data

    st.caption(f"📊 **{len(filtered)}** candidates dengan price data (sorted: highest upside first)"
               + (f" · ⚠️ {len(no_data)} pending (no price data — di bawah)" if no_data else ""))
    st.divider()

    for entry in filtered:
        ticker = entry["ticker"]
        cand = entry["candidate"]
        stars = _stars_html(cand.get("stars", 0))
        market = cand.get("market", "?").upper()
        tags = cand.get("tags", [])
        rr = rr_data.get(ticker, {})
        upside = _calc_upside_metrics(rr)

        action = rr.get("signals", {}).get("action", "WATCH") if rr else "NO_DATA"
        if market == "IHSG" and action in ("SHORT_RIP", "COVER"):
            action = "WATCH"
        action_emoji = {"BUY_DIP": "🟢", "ADD": "🟢", "HOLD": "⚪", "WATCH": "⚪",
                        "TRIM": "🟡", "TRIM_RIP": "🟠", "SHORT_RIP": "🔴",
                        "COVER": "🟣", "NO_DATA": "⚫"}.get(action, "⚪")

        tail_upside_val = upside.get("upside_to_tail_trr_pct") or 0
        is_multi_bag = "MULTI-BAG" in tags
        is_ma_target = "M&A-Target" in tags

        with st.container(border=True):
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

            if upside and upside.get("target_near"):
                tn = upside["target_near"]; tm = upside["target_mid"]; tf = upside["target_far"]
                cur = upside["current_px"]
                st.markdown(
                    f"**🎯 Target Prices** (from TRR/LRR): "
                    f"Near **${tn:,.2f}** ({((tn/cur-1)*100):+.1f}%) · "
                    f"Mid **${tm:,.2f}** ({((tm/cur-1)*100):+.1f}%) · "
                    f"Far **${tf:,.2f}** ({((tf/cur-1)*100):+.1f}%)"
                    if cur else ""
                )

            rr_for_entry = snap.get("risk_range", {}).get("asset_ranges", {}).get(ticker, {}) if isinstance(snap.get("risk_range"), dict) else {}
            if rr_for_entry:
                try:
                    from components.rich_ticker_card import compute_optimal_entry
                    mkt = cand.get("market", "us_equity")
                    oe = compute_optimal_entry(rr_for_entry, snap, mkt, ticker)
                    if oe and oe.get("lines"):
                        st.markdown(f"**🎯 Optimal Entry — {oe['direction']}**")
                        for ln in oe["lines"][:3]:
                            st.caption(ln)
                except Exception:
                    pass

            st.markdown(f"**💡 Thesis:** {cand.get('thesis', '')}")
            br = cand.get("bottleneck_reason")
            if br:
                st.info(f"🔒 **Why bottleneck:** {br}")

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

    if rejected:
        with st.expander(f"❌ Rejected ({len(rejected)})"):
            for entry in rejected:
                fail_reasons = [f"{ln.replace('L', 'Layer ').replace('_', ': ')}: {ch['msg']}"
                                for ln, ch in entry["checks"].items() if not ch["pass"]]
                st.caption(f"**{entry['ticker']}** — {' · '.join(fail_reasons)}")


def render(snap: dict):
    """Auto-detect v1 vs v2 alpha_center structure dan render yang cocok."""
    ac = snap.get("alpha_center", {})

    # v2 detection: punya key "high_asymmetry" atau "short_term"
    if isinstance(ac, dict) and ("high_asymmetry" in ac or "short_term" in ac):
        _render_v2(snap)
        return

    # v1 detection: punya key "all" (list) atau "passed" (list dari curator v1)
    if isinstance(ac, dict) and ("all" in ac or "passed" in ac):
        _render_v1(snap)
        return

    # Fallback: coba v2 dulu (kalau AlphaCenterCurator v2 ada)
    try:
        from engines.alpha_center_curator import AlphaCenterCurator
        _render_v2(snap)
        return
    except Exception:
        pass

    # Fallback: coba v1
    try:
        from engines.alpha_center_curator import get_curator
        _render_v1(snap)
        return
    except Exception as e:
        st.error(f"Alpha Center unavailable: {e}")
        return
