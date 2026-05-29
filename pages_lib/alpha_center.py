"""alpha_center.py — Alpha Center v40.9

UI: v1 style (stars, tags, MULTI-BAG, M&A-Target, 5-layer filter, filters, sort)
Ticker: High Asymmetry universe (100-1000x% upside) — BUKAN MSFT +5%
"""
import streamlit as st

HIGH_ASYM_UNIVERSE = {
    "MP": {"layer": "Rare Earth", "stage": 1, "stars": 5, "tags": ["MULTI-BAG", "Bottleneck"], "market": "us_equity", "thesis": "MP Materials — US rare earth, China export controls, dari $15 ke $150+ (10x)", "monopoly_strength": "Monopoly", "potential_upside": "1000%+", "sources": ["HyperTechInvest"], "risk": "China retaliation", "bottleneck_reason": "Only US rare earth mine, China controls 80% global supply"},
    "LYSDY": {"layer": "Rare Earth", "stage": 1, "stars": 4, "tags": ["MULTI-BAG"], "market": "us_equity", "thesis": "Lynas — only Western rare earth miner, dari $2 ke $20+ (10x)", "monopoly_strength": "Duopoly", "potential_upside": "1000%+", "sources": ["Citrini"], "risk": "Malaysia regulatory", "bottleneck_reason": "Only Western rare earth processing"},
    "UROY": {"layer": "Uranium", "stage": 1, "stars": 4, "tags": ["MULTI-BAG", "Speculative"], "market": "us_equity", "thesis": "Uranium Royalty — leverage to uranium price, dari $1 ke $10+ (10x)", "monopoly_strength": "Niche", "potential_upside": "1000%+", "sources": ["Sprott"], "risk": "Uranium price volatility", "bottleneck_reason": "Royalty model = no operational risk, pure leverage"},
    "CCJ": {"layer": "Uranium", "stage": 1, "stars": 5, "tags": ["MULTI-BAG", "Energy"], "market": "us_equity", "thesis": "Cameco — uranium supply deficit + reactor restart, dari $30 ke $300+ (10x)", "monopoly_strength": "Oligopoly", "potential_upside": "1000%+", "sources": ["Hedgeye", "Sprott"], "risk": "Mine operational", "bottleneck_reason": "World's largest uranium producer, supply deficit 2026+"},
    "BRMS.JK": {"layer": "Gold", "stage": 1, "stars": 5, "tags": ["MULTI-BAG", "IHSG", "Speculative"], "market": "ihsg", "thesis": "Bumi Resources Minerals — gold explorer micro cap, dari $50 ke $500+ (10x)", "monopoly_strength": "Resource", "potential_upside": "1000%+", "sources": ["IHSG Specialist"], "risk": "Exploration failure", "bottleneck_reason": "Micro cap gold, central bank buying trend"},
    "NCKL.JK": {"layer": "Nickel", "stage": 1, "stars": 5, "tags": ["MULTI-BAG", "IHSG"], "market": "ihsg", "thesis": "Nickel Industries — EV battery + Indonesia dominance, dari $100 ke $1000+ (10x)", "monopoly_strength": "Resource", "potential_upside": "1000%+", "sources": ["IHSG Specialist"], "risk": "Nickel price volatility", "bottleneck_reason": "Indonesia nickel processing hub, EV demand"},
    "SMR": {"layer": "Nuclear/SMR", "stage": 1, "stars": 4, "tags": ["MULTI-BAG", "SMR", "Power"], "market": "us_equity", "thesis": "NuScale SMR — regulatory inflection, dari $10 ke $100+ (10x)", "monopoly_strength": "Regulatory", "potential_upside": "1000%+", "sources": ["Leopold"], "risk": "Regulatory delay", "bottleneck_reason": "First US SMR design approved, AI power demand"},
    "OKLO": {"layer": "Nuclear/SMR", "stage": 1, "stars": 4, "tags": ["MULTI-BAG", "SMR", "Speculative"], "market": "us_equity", "thesis": "Oklo — Sam Altman backed SMR pioneer, dari $5 ke $50+ (10x)", "monopoly_strength": "Regulatory", "potential_upside": "1000%+", "sources": ["Altman"], "risk": "Pre-revenue", "bottleneck_reason": "Sam Altman backed, micro-reactor design"},
    "FRO": {"layer": "Tankers", "stage": 2, "stars": 4, "tags": ["MULTI-BAG", "Energy"], "market": "us_equity", "thesis": "Frontline — VLCC rates + Red Sea disruption, dari $15 ke $60+ (4x)", "monopoly_strength": "Fleet", "potential_upside": "400%+", "sources": ["Hedgeye"], "risk": "Oil demand collapse", "bottleneck_reason": "VLCC fleet aging, Red Sea insurance premium"},
    "TK": {"layer": "Tankers", "stage": 2, "stars": 3, "tags": ["MULTI-BAG"], "market": "us_equity", "thesis": "Teekay — tanker fleet aging, dari $5 ke $25+ (5x)", "monopoly_strength": "Fleet", "potential_upside": "500%+", "sources": ["Hedgeye"], "risk": "Rate volatility", "bottleneck_reason": "Fleet consolidation, supply inelastic"},
    "INSW": {"layer": "Tankers", "stage": 2, "stars": 4, "tags": ["MULTI-BAG", "M&A-Target"], "market": "us_equity", "thesis": "International Seaways — M&A + rate surge, dari $40 ke $120+ (3x)", "monopoly_strength": "Fleet", "potential_upside": "300%+", "sources": ["Hedgeye"], "risk": "M&A failure", "bottleneck_reason": "Takeover target, VLCC rate surge"},
    "STNG": {"layer": "Tankers", "stage": 2, "stars": 4, "tags": ["MULTI-BAG"], "market": "us_equity", "thesis": "Scorpio Tankers — product tanker squeeze, dari $60 ke $180+ (3x)", "monopoly_strength": "Fleet", "potential_upside": "300%+", "sources": ["Hedgeye"], "risk": "Product demand", "bottleneck_reason": "Product tanker supply squeeze"},
    "MSTR": {"layer": "BTC Proxy", "stage": 2, "stars": 4, "tags": ["MULTI-BAG", "Crypto"], "market": "us_equity", "thesis": "MicroStrategy — BTC leverage play, 2x+ BTC upside, dari $300 ke $1500+ (5x)", "monopoly_strength": "Brand", "potential_upside": "500%+", "sources": ["Saylor"], "risk": "BTC crash", "bottleneck_reason": "BTC treasury, leverage to BTC price"},
    "ADRO.JK": {"layer": "Coal", "stage": 2, "stars": 4, "tags": ["MULTI-BAG", "IHSG", "Energy"], "market": "ihsg", "thesis": "Adaro — seaborne thermal + Indonesia export, dari $2000 ke $8000+ (4x)", "monopoly_strength": "Resource", "potential_upside": "400%+", "sources": ["IHSG Specialist"], "risk": "Coal demand decline", "bottleneck_reason": "Seaborne thermal coal demand, Indonesia export growth"},
    "ITMG.JK": {"layer": "Coal", "stage": 2, "stars": 4, "tags": ["MULTI-BAG", "IHSG"], "market": "ihsg", "thesis": "Indo Tambangraya — coal royalty model, dari $10000 ke $40000+ (4x)", "monopoly_strength": "Resource", "potential_upside": "400%+", "sources": ["IHSG Specialist"], "risk": "Regulatory", "bottleneck_reason": "Royalty model, low cost producer"},
    "VST": {"layer": "Power/Cooling", "stage": 3, "stars": 4, "tags": ["MULTI-BAG", "Power", "AI"], "market": "us_equity", "thesis": "Vistra — nuclear renaissance + AI power contracts, dari $100 ke $300+ (3x)", "monopoly_strength": "Regulatory", "potential_upside": "300%+", "sources": ["Leopold"], "risk": "Nuclear regulatory", "bottleneck_reason": "AI datacenter power demand, nuclear restart"},
    "CEG": {"layer": "Power/Cooling", "stage": 3, "stars": 4, "tags": ["MULTI-BAG", "Power", "AI"], "market": "us_equity", "thesis": "Constellation Energy — nuclear + AI contracts, dari $200 ke $600+ (3x)", "monopoly_strength": "Regulatory", "potential_upside": "300%+", "sources": ["Leopold"], "risk": "Regulatory delay", "bottleneck_reason": "Largest nuclear fleet, AI power contracts"},
    "BE": {"layer": "Power/Cooling", "stage": 3, "stars": 3, "tags": ["MULTI-BAG", "Power"], "market": "us_equity", "thesis": "Bloom Energy — fuel cells for datacenters, dari $20 ke $80+ (4x)", "monopoly_strength": "Niche", "potential_upside": "400%+", "sources": ["Leopold"], "risk": "Pre-profitability", "bottleneck_reason": "Fuel cells for AI datacenters"},
    "NXT": {"layer": "CPO/Connectors", "stage": 3, "stars": 4, "tags": ["MULTI-BAG", "AI", "Optical"], "market": "us_equity", "thesis": "Nextracker — AI datacenter CPO, dari $40 ke $120+ (3x)", "monopoly_strength": "Duopoly", "potential_upside": "300%+", "sources": ["HyperTechInvest"], "risk": "CPO adoption", "bottleneck_reason": "AI datacenter CPO adoption inflection"},
    "AMPH": {"layer": "CPO/Connectors", "stage": 3, "stars": 4, "tags": ["MULTI-BAG", "AI"], "market": "us_equity", "thesis": "Amphenol — co-packaged optics, dari $30 ke $90+ (3x)", "monopoly_strength": "Duopoly", "potential_upside": "300%+", "sources": ["HyperTechInvest"], "risk": "Competition", "bottleneck_reason": "NVIDIA supplier, CPO connectors"},
    "HLIT": {"layer": "CPO/Connectors", "stage": 3, "stars": 3, "tags": ["MULTI-BAG", "AI"], "market": "us_equity", "thesis": "Harmonic — optical networking AI backbone, dari $10 ke $40+ (4x)", "monopoly_strength": "Niche", "potential_upside": "400%+", "sources": ["HyperTechInvest"], "risk": "Cable competition", "bottleneck_reason": "AI backbone optical networking"},
    "COHR": {"layer": "Optics", "stage": 4, "stars": 3, "tags": ["MULTI-BAG", "Optical"], "market": "us_equity", "thesis": "Coherent — 800G/1.6T transceiver, dari $50 ke $150+ (3x)", "monopoly_strength": "Oligopoly", "potential_upside": "300%+", "sources": ["HyperTechInvest"], "risk": "Demand cyclical", "bottleneck_reason": "800G/1.6T transceiver supply constrained"},
    "LITE": {"layer": "Optics", "stage": 4, "stars": 3, "tags": ["MULTI-BAG", "Optical"], "market": "us_equity", "thesis": "Lumentum — Apple + AI datacenter, dari $60 ke $180+ (3x)", "monopoly_strength": "Oligopoly", "potential_upside": "300%+", "sources": ["HyperTechInvest"], "risk": "Apple dependency", "bottleneck_reason": "Apple VCSEL + AI datacenter optics"},
    "MRVL": {"layer": "Optics", "stage": 4, "stars": 3, "tags": ["MULTI-BAG", "AI"], "market": "us_equity", "thesis": "Marvell — custom silicon + optics, dari $70 ke $210+ (3x)", "monopoly_strength": "Wide", "potential_upside": "300%+", "sources": ["HyperTechInvest"], "risk": "Competition", "bottleneck_reason": "Custom AI silicon + optical interconnect"},
    "COIN": {"layer": "Exchange", "stage": 4, "stars": 3, "tags": ["MULTI-BAG", "Crypto"], "market": "us_equity", "thesis": "Coinbase — crypto infra + derivatives, dari $200 ke $600+ (3x)", "monopoly_strength": "Network", "potential_upside": "300%+", "sources": ["Crypto"], "risk": "Regulatory", "bottleneck_reason": "Crypto derivatives + institutional adoption"},
    "HOOD": {"layer": "Retail/Trading", "stage": 4, "stars": 3, "tags": ["MULTI-BAG", "Crypto"], "market": "us_equity", "thesis": "Robinhood — crypto + international, dari $40 ke $120+ (3x)", "monopoly_strength": "Userbase", "potential_upside": "300%+", "sources": ["Crypto"], "risk": "Regulatory", "bottleneck_reason": "Crypto trading + international expansion"},
    "NTR": {"layer": "Fertilizer", "stage": 5, "stars": 3, "tags": ["MULTI-BAG", "Materials"], "market": "us_equity", "thesis": "Nutrien — natgas squeeze + food security, dari $50 ke $100+ (2x)", "monopoly_strength": "Scale", "potential_upside": "200%+", "sources": ["Hedgeye"], "risk": "Natgas price", "bottleneck_reason": "Natgas cost squeeze, food security demand"},
    "MOS": {"layer": "Fertilizer", "stage": 5, "stars": 3, "tags": ["MULTI-BAG", "Materials"], "market": "us_equity", "thesis": "Mosaic — phosphate oligopoly, dari $30 ke $60+ (2x)", "monopoly_strength": "Scale", "potential_upside": "200%+", "sources": ["Hedgeye"], "risk": "Phosphate price", "bottleneck_reason": "Phosphate + potash oligopoly"},
    "CF": {"layer": "Fertilizer", "stage": 5, "stars": 3, "tags": ["MULTI-BAG", "Materials"], "market": "us_equity", "thesis": "CF Industries — ammonia + hydrogen, dari $70 ke $140+ (2x)", "monopoly_strength": "Scale", "potential_upside": "200%+", "sources": ["Hedgeye"], "risk": "Ammonia price", "bottleneck_reason": "Ammonia + hydrogen pivot"},
    "ANTM.JK": {"layer": "Gold", "stage": 5, "stars": 3, "tags": ["MULTI-BAG", "IHSG"], "market": "ihsg", "thesis": "Aneka Tambang — gold + central bank buying, dari $2000 ke $4000+ (2x)", "monopoly_strength": "Resource", "potential_upside": "200%+", "sources": ["IHSG Specialist"], "risk": "Gold price", "bottleneck_reason": "Gold + central bank buying trend"},
    "BBRI.JK": {"layer": "Banking", "stage": 5, "stars": 3, "tags": ["MULTI-BAG", "IHSG"], "market": "ihsg", "thesis": "BRI — NIM expansion + credit growth, dari $3000 ke $6000+ (2x)", "monopoly_strength": "Branch", "potential_upside": "200%+", "sources": ["IHSG Specialist"], "risk": "NPL", "bottleneck_reason": "NIM expansion, credit growth recovery"},
    "BMRI.JK": {"layer": "Banking", "stage": 5, "stars": 3, "tags": ["MULTI-BAG", "IHSG"], "market": "ihsg", "thesis": "Mandiri — largest bank dividend, dari $4000 ke $8000+ (2x)", "monopoly_strength": "Branch", "potential_upside": "200%+", "sources": ["IHSG Specialist"], "risk": "NPL", "bottleneck_reason": "Largest bank, dividend yield"},
}


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


def render(snap: dict):
    st.title("⚡ Alpha Center v40.9")
    st.caption("**High Asymmetry ONLY** — Ticker dengan potensi 100-1000x% upside. Bukan MSFT +5%.")

    keith_signals = snap.get("keith_signals", {}) or {}
    rr_data = snap.get("risk_range", {}).get("asset_ranges", {}) if isinstance(snap.get("risk_range"), dict) else {}
    prices = snap.get("prices", {})

    # Build picks from HIGH_ASYM_UNIVERSE (not bottleneck_ref)
    passed = []
    for ticker, cand in HIGH_ASYM_UNIVERSE.items():
        ks = keith_signals.get(ticker, {})
        keith_trade = ks.get("keith_trade", "NEUTRAL") if isinstance(ks, dict) else "NEUTRAL"

        # 5-Layer Filter Checks
        checks = {}
        checks["L1_stars"] = {"pass": cand["stars"] >= 3, "msg": f"{cand['stars']} stars"}
        checks["L2_keith"] = {"pass": keith_trade != "BEARISH", "msg": f"Keith {keith_trade}"}
        checks["L3_multi"] = {"pass": "MULTI-BAG" in cand["tags"], "msg": "Multi-bag"}
        checks["L4_stage"] = {"pass": cand["stage"] <= 3, "msg": f"Stage {cand['stage']} (early)"}
        checks["L5_upside"] = {"pass": True, "msg": cand.get("potential_upside", "—")}

        total_pass = sum(1 for c in checks.values() if c["pass"])
        total_check = len(checks)

        entry = {
            "ticker": ticker,
            "candidate": cand,
            "checks": checks,
            "pass_ratio": total_pass / total_check if total_check else 0,
        }
        if total_pass >= 3:
            passed.append(entry)

    # ── TOP KPIs ─────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Passed", len(passed))
    multi_bag = sum(1 for p in passed if "MULTI-BAG" in p["candidate"].get("tags", []))
    c2.metric("🚀 Multi-bag", multi_bag)
    ma_targets = sum(1 for p in passed if "M&A-Target" in p["candidate"].get("tags", []))
    c3.metric("🎯 M&A targets", ma_targets)
    c4.metric("Universe", "High Asymmetry")
    st.divider()

    # ── FILTERS ──────────────────────────────────────────────────────────
    f1, f2, f3 = st.columns([1, 1.4, 1])
    with f1:
        tier_filter = st.radio("Tier", ["All", "5★", "4★+", "3★+"], horizontal=False)
    with f2:
        market_filter = st.multiselect(
            "Market", ["us_equity", "ihsg", "crypto", "forex", "commodity"],
            default=["us_equity", "ihsg"],
        )
    with f3:
        tag_filter = st.multiselect(
            "Tag focus",
            ["MULTI-BAG", "M&A-Target", "AI", "Energy", "Materials", "Crypto", "IHSG", "Power", "SMR", "Speculative"],
        )

    min_upside_str = st.select_slider(
        "Min potential upside (% per month — 20% = 240% annualized)",
        options=["No filter", "20%", "50%", "100%", "200%", "500%", "1000%"],
        value="20%",
        help="ALPHA = minimum 20% per month (240% annualized). 100% = 10x potential.",
    )
    min_upside_map = {"No filter": 0, "20%": 20, "50%": 50, "100%": 100, "200%": 200, "500%": 500, "1000%": 1000}
    min_upside = min_upside_map[min_upside_str]

    def _tier_ok(c):
        s = c["candidate"].get("stars", 0)
        if tier_filter == "All": return True
        if tier_filter == "5★": return s == 5
        if tier_filter == "4★+": return s >= 4
        if tier_filter == "3★+": return s >= 3
        return True

    def _tag_ok(c):
        if not tag_filter: return True
        tags = c["candidate"].get("tags", [])
        return any(t in tags for t in tag_filter)

    def _upside_ok(c):
        if min_upside == 0: return True
        pot = c["candidate"].get("potential_upside", "")
        # Extract number from "1000%+" or "400%+"
        import re
        m = re.search(r'(\d+)', pot)
        if m:
            return int(m.group(1)) >= min_upside
        return True

    filtered = [c for c in passed if _tier_ok(c) and _tag_ok(c) and _upside_ok(c) and c["candidate"].get("market") in market_filter]

    # Upside filter from RR data
    if min_upside > 0:
        filtered_pre = filtered
        filtered = []
        for e in filtered_pre:
            rr = rr_data.get(e["ticker"], {})
            if not rr:
                filtered.append(e)  # Keep even without RR data
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
    filtered = has_data + no_data  # Show all, data first

    st.caption(f"📊 **{len(filtered)}** candidates (sorted: highest upside first)")
    st.divider()

    # ── RENDER CARDS ────────────────────────────────────────────────────
    for entry in filtered:
        ticker = entry["ticker"]
        cand = entry["candidate"]
        stars = _stars_html(cand.get("stars", 0))
        market = cand.get("market", "?").upper()
        tags = cand.get("tags", [])
        rr = rr_data.get(ticker, {})
        upside = _calc_upside_metrics(rr)

        is_multi_bag = "MULTI-BAG" in tags
        is_ma_target = "M&A-Target" in tags

        with st.container(border=True):
            hc1, hc2, hc3 = st.columns([2.4, 1.2, 1.4])
            with hc1:
                tickline = f"### {ticker} &nbsp;{stars}"
                if is_multi_bag: tickline += " &nbsp;🚀"
                if is_ma_target: tickline += " &nbsp;🎯 M&A"
                st.markdown(tickline)
                st.caption(f"{market} · {cand.get('layer', '—')} · Stage {cand.get('stage', '—')}")
                st.caption(f"💼 Sources: {', '.join(cand.get('sources', [])[:4])}")
            with hc2:
                px_str = f"${(rr.get('px') or 0):.2f}" if rr.get('px') else "—"
                st.metric("Price", px_str)
                st.caption(f"Potential: {cand.get('potential_upside', '—')}")
            with hc3:
                if upside:
                    st.metric("Upside → TAIL TRR",
                             f"{upside['upside_to_tail_trr_pct']:+.1f}%" if upside.get('upside_to_tail_trr_pct') else "—")
                    st.caption(f"🎯 {upside.get('thesis_stage', '—')}")
                else:
                    st.metric("Upside", "N/A")
                    st.caption("Rebuild for RR data")

            if upside and upside.get("target_near"):
                tn = upside["target_near"]; tm = upside["target_mid"]; tf = upside["target_far"]
                cur = upside["current_px"]
                st.markdown(
                    f"**🎯 Target Prices**: Near **${tn:,.2f}** ({((tn/cur-1)*100):+.1f}%) · "
                    f"Mid **${tm:,.2f}** ({((tm/cur-1)*100):+.1f}%) · "
                    f"Far **${tf:,.2f}** ({((tf/cur-1)*100):+.1f}%)"
                    if cur else ""
                )

            st.markdown(f"**💡 Thesis:** {cand.get('thesis', '')}")
            br = cand.get("bottleneck_reason")
            if br:
                st.info(f"🔒 **Why bottleneck:** {br}")

            with st.expander("🔍 Detail — filters, risk, catalysts"):
                dc1, dc2 = st.columns(2)
                with dc1:
                    cats = cand.get("catalysts_2026", [])
                    if cats:
                        st.markdown("**📌 Catalysts 2026**")
                        for cat in cats:
                            st.caption(f"  • {cat}")
                with dc2:
                    risk = cand.get("risk")
                    if risk:
                        st.warning(f"⚠️ **Risk:** {risk}")
                st.markdown("**✅ 5-Layer Filter Pass:**")
                for layer_name, check in entry["checks"].items():
                    icon = "✅" if check["pass"] else "❌"
                    st.caption(f"{icon} {layer_name}: {check['msg']}")

    if not filtered:
        st.info("No candidates match current filters. Loosen the filter to see more.")

    st.divider()
    st.markdown("""
    <div style='background:#161B22;border:1px solid #30363D;border-radius:8px;padding:12px;'>
    <b>🎯 ALPHA DEFINITION:</b> Minimum <b>20% per month</b> (240% annualized). Contoh: SNDK $30 → $1500 (50x).
    <br>Bukan MSFT +5% sebulan. <i>"Kalo 1 bulan naik 5% mending dagang tahu bos"</i>
    </div>
    """, unsafe_allow_html=True)
