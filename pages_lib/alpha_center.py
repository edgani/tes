"""alpha_center.py — Alpha Center UI v40.6

Sections:
 1. 🔥 Keith Fractal Breadth Meter — "X of 37 signals bullish"
 2. 🚀 High Asymmetry Picks (100-1000x% upside) — Ticker dengan potensi MASSIVE upside
 3. ⚡ Bottleneck + Surge Potential (legacy v1) — Stars, tags, MULTI-BAG, M&A-Target
 4. 📊 Short-Term Swing (R:R 2:1+)
"""
import streamlit as st


def _stars_html(n: int) -> str:
    return "⭐" * int(n or 0)


def _calc_upside_metrics(rr: dict) -> dict:
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


def _render_keith_breadth(snap: dict):
    keith_breadth = snap.get("keith_breadth", {})
    if not keith_breadth or keith_breadth.get("total_signals", 0) == 0:
        return
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
        st.success(f"📈 BULLISH BREADTH — {bullish_pct}% bullish. Slim pickings on short side.")
    elif bearish > (total * 0.4):
        st.error(f"📉 BEARISH BREADTH — {bearish}/{total} bearish. Defensive posture.")
    else:
        st.info(f"⚖️ NEUTRAL BREADTH — Mixed signals.")
    st.divider()


def _render_high_asymmetry(snap: dict):
    """Section 2: High Asymmetry (100-1000x% upside) — dari ticker universe, bukan bottleneck_ref."""
    st.markdown("### 🚀 High Asymmetry Picks (100-1000x% upside potential)")
    st.caption("Ticker dengan market cap kecil + stage 1-2 bottleneck + Keith BULLISH. Bukan MSFT +5%.")

    # High asymmetry ticker universe (stage 1-2 = highest potential)
    HIGH_ASYM_TICKERS = {
        "NXT": {"layer": "CPO/Connectors", "stage": 5, "thesis": "AI datacenter CPO adoption inflection — dari $5 ke $50+"},
        "AMPH": {"layer": "CPO/Connectors", "stage": 5, "thesis": "Co-packaged optics — NVIDIA supplier"},
        "HLIT": {"layer": "CPO/Connectors", "stage": 5, "thesis": "Optical networking — AI backbone"},
        "COHR": {"layer": "Optics", "stage": 4, "thesis": "800G/1.6T transceiver — supply constrained"},
        "LITE": {"layer": "Optics", "stage": 4, "thesis": "Lumentum — Apple + AI datacenter"},
        "MRVL": {"layer": "Optics", "stage": 4, "thesis": "Marvell — custom silicon + optics"},
        "VST": {"layer": "Power/Cooling", "stage": 3, "thesis": "Nuclear renaissance + AI power density"},
        "CEG": {"layer": "Power/Cooling", "stage": 3, "thesis": "Constellation Energy — nuclear + AI contracts"},
        "BE": {"layer": "Power/Cooling", "stage": 3, "thesis": "Bloom Energy — fuel cells for datacenters"},
        "SMR": {"layer": "Nuclear/SMR", "stage": 3, "thesis": "Small modular reactors — regulatory inflection"},
        "OKLO": {"layer": "Nuclear/SMR", "stage": 3, "thesis": "Oklo — Sam Altman backed, SMR pioneer"},
        "FRO": {"layer": "Tankers", "stage": 2, "thesis": "Frontline — VLCC rates + Red Sea disruption"},
        "TK": {"layer": "Tankers", "stage": 2, "thesis": "Teekay — tanker fleet aging + supply inelastic"},
        "INSW": {"layer": "Tankers", "stage": 2, "thesis": "International Seaways — M&A + rate surge"},
        "STNG": {"layer": "Tankers", "stage": 2, "thesis": "Scorpio Tankers — product tanker squeeze"},
        "NTR": {"layer": "Fertilizer", "stage": 4, "thesis": "Nutrien — natgas cost squeeze + food security"},
        "MOS": {"layer": "Fertilizer", "stage": 4, "thesis": "Mosaic — phosphate + potash oligopoly"},
        "CF": {"layer": "Fertilizer", "stage": 4, "thesis": "CF Industries — ammonia + hydrogen pivot"},
        "MP": {"layer": "Rare Earth", "stage": 1, "thesis": "MP Materials — US rare earth, China export controls"},
        "LYSDY": {"layer": "Rare Earth", "stage": 1, "thesis": "Lynas — only Western rare earth miner"},
        "UROY": {"layer": "Uranium", "stage": 1, "thesis": "Uranium Royalty — leverage to uranium price"},
        "CCJ": {"layer": "Uranium", "stage": 1, "thesis": "Cameco — uranium supply deficit + reactor restart"},
        "MSTR": {"layer": "BTC Proxy", "stage": 2, "thesis": "MicroStrategy — BTC leverage play, 2x+ BTC upside"},
        "COIN": {"layer": "Exchange", "stage": 3, "thesis": "Coinbase — crypto infra + derivatives growth"},
        "HOOD": {"layer": "Retail/Trading", "stage": 3, "thesis": "Robinhood — crypto + international expansion"},
        "ADRO.JK": {"layer": "Coal", "stage": 2, "thesis": "Adaro — seaborne thermal + Indonesia export"},
        "ITMG.JK": {"layer": "Coal", "stage": 2, "thesis": "Indo Tambangraya — coal royalty model"},
        "NCKL.JK": {"layer": "Nickel", "stage": 1, "thesis": "Nickel Industries — EV battery + Indonesia dominance"},
        "ANTM.JK": {"layer": "Gold", "stage": 2, "thesis": "Aneka Tambang — gold + central bank buying"},
        "BRMS.JK": {"layer": "Gold", "stage": 1, "thesis": "Bumi Resources Minerals — gold explorer, micro cap"},
        "BBRI.JK": {"layer": "Banking", "stage": 3, "thesis": "BRI — NIM expansion + credit growth"},
        "BMRI.JK": {"layer": "Banking", "stage": 3, "thesis": "Mandiri — largest bank, dividend yield"},
    }

    keith_signals = snap.get("keith_signals", {}) or {}
    rr_data = snap.get("risk_range", {}).get("asset_ranges", {}) if isinstance(snap.get("risk_range"), dict) else {}
    prices = snap.get("prices", {})

    picks = []
    for ticker, meta in HIGH_ASYM_TICKERS.items():
        ks = keith_signals.get(ticker, {})
        keith_trade = ks.get("keith_trade", "NEUTRAL") if isinstance(ks, dict) else "NEUTRAL"
        if keith_trade == "BEARISH":
            continue

        rr = rr_data.get(ticker, {})
        px = rr.get("px") if isinstance(rr, dict) else None
        if px is None and ticker in prices:
            try:
                import pandas as pd
                s = pd.to_numeric(pd.Series(prices[ticker]), errors="coerce").dropna()
                if len(s) > 0:
                    px = float(s.iloc[-1])
            except Exception:
                pass

        # Estimate upside potential
        upside_potential = "HIGH"
        if meta["stage"] <= 2:
            upside_potential = "MOON"
        elif meta["stage"] == 3:
            upside_potential = "HIGH"
        else:
            upside_potential = "MEDIUM"

        picks.append({
            "ticker": ticker,
            "layer": meta["layer"],
            "stage": meta["stage"],
            "thesis": meta["thesis"],
            "keith": keith_trade,
            "px": px,
            "upside_potential": upside_potential,
        })

    picks.sort(key=lambda x: x["stage"])

    if not picks:
        st.info("No high-asymmetry candidates. Check Keith breadth or loosen filters.")
        return

    for pick in picks:
        ticker = pick["ticker"]
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                badge = "🚀🚀🚀" if pick["upside_potential"] == "MOON" else "🚀🚀" if pick["upside_potential"] == "HIGH" else "🚀"
                st.markdown(f"### {ticker} {badge}")
                st.caption(f"{pick['layer']} · Stage {pick['stage']}")
                st.caption(f"💡 {pick['thesis']}")
            with c2:
                if pick["px"]:
                    st.metric("Price", f"${pick['px']:.2f}")
                st.caption(f"Keith: {pick['keith']}")
            with c3:
                st.metric("Upside Pot.", pick["upside_potential"])
                st.caption("100-1000x% potential" if pick["upside_potential"] == "MOON" else "100-300x% potential")
    st.divider()


def _render_bottleneck_v1(snap: dict):
    """Section 3: Bottleneck + Surge Potential (legacy v1)."""
    st.markdown("### ⚡ Bottleneck + Surge Potential (Legacy)")
    st.caption("Bottleneck_reference.json — 5-layer filter, stars, tags, MULTI-BAG, M&A-Target")

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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Passed", len(passed))
    multi_bag = sum(1 for p in passed if "MULTI-BAG" in p["candidate"].get("tags", []))
    c2.metric("🚀 Multi-bag", multi_bag)
    ma_targets = sum(1 for p in passed if "M&A-Target" in p["candidate"].get("tags", []))
    c3.metric("🎯 M&A targets", ma_targets)
    c4.metric("Current Quad", current_quad)
    st.divider()

    f1, f2, f3 = st.columns([1, 1.4, 1])
    with f1:
        tier_filter = st.radio("Tier", ["All", "5★", "4★+", "3★+", "1-2★ (HRHR)"], horizontal=False, key="tier_v1")
    with f2:
        market_filter = st.multiselect(
            "Market", ["us_equity", "ihsg", "crypto", "forex", "commodity"],
            default=["us_equity", "ihsg", "crypto"], key="market_v1"
        )
    with f3:
        tag_filter = st.multiselect(
            "Tag focus",
            ["Bottleneck", "MULTI-BAG", "M&A-Target", "AI", "Citrini", "Energy",
             "Materials", "Crypto", "IHSG", "Bandar", "Optical", "Memory",
             "Power", "Storage", "SMR", "Speculative"], key="tag_v1"
        )

    min_upside_str = st.select_slider(
        "Min upside ke TAIL TRR (%)",
        options=["No filter", "0%", "20%", "50%", "100%", "200%"],
        value="0%", key="upside_v1"
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

    filtered = [c for c in passed if _tier_ok(c) and _tag_ok(c) and c["candidate"].get("market") in market_filter]

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
        return (-(um.get("upside_to_tail_trr_pct") or 0), -e["candidate"].get("stars", 0), e["ticker"])
    filtered.sort(key=_sort_key)

    has_data = [e for e in filtered if rr_data.get(e["ticker"], {}).get("px")]
    no_data = [e for e in filtered if not rr_data.get(e["ticker"], {}).get("px")]
    filtered = has_data

    st.caption(f"📊 **{len(filtered)}** candidates dengan price data"
               + (f" · ⚠️ {len(no_data)} pending (no price data)" if no_data else ""))
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
                    f"**🎯 Target Prices**: Near **${tn:,.2f}** ({((tn/cur-1)*100):+.1f}%) · "
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
    """Render Alpha Center v40.6 — 4 sections."""
    st.title("⚡ Alpha Center v40.6")

    # 1. Keith Breadth Meter
    _render_keith_breadth(snap)

    # 2. High Asymmetry (100-1000x%)
    _render_high_asymmetry(snap)

    # 3. Bottleneck v1 (legacy)
    _render_bottleneck_v1(snap)
