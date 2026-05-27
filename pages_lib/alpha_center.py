"""alpha_center.py — Curated surge candidates (5-layer filter)"""
import streamlit as st


def render(snap: dict):
    st.title("⚡ Alpha Center")
    st.caption("Curated bottleneck + surge candidates across all markets. Filter: 5-layer pipeline.")
    
    try:
        from engines.alpha_center_curator import get_curator
        curator = get_curator()
    except Exception as e:
        st.error(f"Alpha Center curator unavailable: {e}")
        return
    
    # Run filter
    keith_signals = snap.get("keith_signals", {})
    wf_results = snap.get("walkforward_results", {})
    current_quad = snap.get("gip", {}).get("structural_quad", "Q3") if isinstance(snap.get("gip"), dict) else "Q3"
    
    result = curator.filter_universe(
        keith_signals=keith_signals,
        wf_results=wf_results,
        current_quad=current_quad,
        min_stars=1,
    )
    
    passed = result["passed"]
    rejected = result["rejected"]
    
    # ── Summary KPIs ─────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Passed", len(passed))
    with c2:
        st.metric("Rejected", len(rejected))
    with c3:
        ma_count = sum(1 for p in passed if p["candidate"].get("ma_potential") in ("HIGH", "MEDIUM"))
        st.metric("M&A Targets", ma_count)
    with c4:
        st.metric("Current Quad", current_quad)
    
    st.divider()
    
    # ── Tier filter ──────────────────────────────────────────────────────
    tier_filter = st.radio(
        "Tier filter",
        ["All", "5★", "4★+", "3★+", "1-2★ (high-risk high-reward)"],
        horizontal=True,
    )
    
    def _tier_ok(c):
        s = c["candidate"].get("stars", 0)
        if tier_filter == "All": return True
        if tier_filter == "5★": return s == 5
        if tier_filter == "4★+": return s >= 4
        if tier_filter == "3★+": return s >= 3
        if tier_filter == "1-2★ (high-risk high-reward)": return s <= 2
        return True
    
    market_filter = st.multiselect(
        "Market filter",
        ["us_equity", "ihsg", "crypto", "forex", "commodity"],
        default=["us_equity", "ihsg", "crypto"],
    )
    
    filtered = [p for p in passed if _tier_ok(p) and p["candidate"].get("market", "?") in market_filter]
    
    st.markdown(f"### 🎯 {len(filtered)} Candidates")
    
    # ── Render cards ─────────────────────────────────────────────────────
    for entry in filtered:
        ticker = entry["ticker"]
        cand = entry["candidate"]
        stars = "⭐" * cand.get("stars", 0)
        market = cand.get("market", "?").upper()
        bottleneck = cand.get("bottleneck_layer", "—")
        ma = cand.get("ma_potential", "")
        ma_badge = f"<span style='background:rgba(168,85,247,0.20);color:#A855F7;padding:1px 6px;border-radius:10px;font-size:0.6rem;font-weight:700;margin-left:6px;'>M&A {ma}</span>" if ma in ("HIGH", "MEDIUM", "TARGET") else ""
        
        # Pull RR for this ticker if available
        rr_data = snap.get("risk_range", {}).get("asset_ranges", {})
        rr = rr_data.get(ticker, {})
        action = rr.get("signals", {}).get("action", "WATCH") if rr else "NO_DATA"
        action_color = {"BUY_DIP": "#3FB950", "ADD": "#3FB950", "TRIM": "#D29922",
                        "TRIM_RIP": "#D29922", "WATCH": "#8B949E", "HOLD": "#8B949E",
                        "SHORT_RIP": "#F85149", "NO_DATA": "#8B949E"}.get(action, "#8B949E")
        
        with st.container():
            st.markdown(f"""<div class='alpha-card'>
                <div style='display:flex;align-items:center;gap:8px;'>
                    <span style='font-weight:800;font-size:1rem;color:#E6EDF3;'>{ticker}</span>
                    <span style='font-size:0.7rem;color:#D29922;'>{stars}</span>
                    <span style='font-size:0.6rem;color:#8B949E;background:rgba(139,148,158,0.12);padding:1px 6px;border-radius:8px;'>{market}</span>
                    <span style='background:rgba(34,197,94,0.12);color:{action_color};border:1px solid {action_color};padding:2px 8px;border-radius:12px;font-size:0.6rem;font-weight:700;'>{action}</span>
                    {ma_badge}
                </div>
                <div style='font-size:0.7rem;color:#8B949E;margin-top:4px;'>
                    <b>Bottleneck:</b> {bottleneck}
                </div>
                <div style='font-size:0.7rem;color:#E6EDF3;margin-top:6px;line-height:1.4;'>
                    {cand.get('thesis', '')}
                </div>
            </div>""", unsafe_allow_html=True)
            
            with st.expander(f"🔍 {ticker} — Full Detail"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**📌 Catalysts 2026**")
                    for cat in cand.get("catalysts_2026", []):
                        st.caption(f"• {cat}")
                    
                    st.markdown("**🔗 Correlations**")
                    for parent, beta in cand.get("correlations", {}).items():
                        color = "#3FB950" if beta > 0 else "#F85149"
                        st.markdown(f"<span style='color:{color};font-weight:600;'>{parent}: β={beta}</span>", unsafe_allow_html=True)
                
                with c2:
                    if rr:
                        st.markdown("**📊 Risk Range**")
                        t = rr.get("trade", {})
                        st.metric("Current Price", f"${rr.get('px', 0):.2f}")
                        st.metric("TRADE Range", f"${t.get('lrr', 0):.2f} → ${t.get('trr', 0):.2f}")
                        sig = rr.get("signals", {})
                        st.caption(f"💡 {sig.get('reason', '')}")
                    
                    # Risk notes if speculative
                    if cand.get("risk_notes"):
                        st.warning(f"⚠️ {cand['risk_notes']}")
                
                st.markdown("**✅ 5-Layer Filter Pass:**")
                for layer_name, check in entry["checks"].items():
                    icon = "✅" if check["pass"] else "❌"
                    st.caption(f"{icon} {layer_name}: {check['msg']}")
    
    # ── Rejected list (collapsible) ──────────────────────────────────────
    if rejected:
        with st.expander(f"❌ Rejected ({len(rejected)}) — see why"):
            for entry in rejected:
                fail_reasons = [
                    f"{k}: {v['msg']}" for k, v in entry["checks"].items() if not v["pass"]
                ]
                st.caption(f"**{entry['ticker']}**: {' · '.join(fail_reasons)}")
