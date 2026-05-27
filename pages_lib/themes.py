"""themes.py — Scenario narratives consolidated"""
import streamlit as st

def render(snap):
    st.title("📖 Themes & Scenarios")
    st.caption("Macro narratives, active scenarios, and theme exposure.")
    
    scenarios = snap.get("scenarios", []) or snap.get("active_scenarios", [])
    # Normalize wrap before fallback
    if isinstance(scenarios, dict):
        scenarios = scenarios.get("active_scenarios", []) or scenarios.get("all_scenarios", [])
    scenarios = [s for s in (scenarios or []) if isinstance(s, dict)]

    if not scenarios:
        # Fallback: run scenario_discovery directly
        try:
            from engines.scenario_discovery_engine import run_scenario_discovery
            gip = snap.get("gip", {})
            quad = "Q3"
            if isinstance(gip, dict):
                quad = gip.get("monthly_quad") or gip.get("structural_quad") or "Q3"
            elif gip is not None:
                quad = getattr(gip, "monthly_quad", None) or getattr(gip, "structural_quad", None) or "Q3"
            result = run_scenario_discovery(gip_result=gip, current_quad=quad)
            scenarios = result.get("active_scenarios", []) if isinstance(result, dict) else []
        except Exception as e:
            st.warning(f"Scenario discovery error: {e}")
            scenarios = []

    if not scenarios:
        st.info("No scenarios available.")
        return

    # Theme cards
    for sc in scenarios:
        # Normalize fields — handle both run_scenario_discovery format and legacy format
        name = sc.get("name") or sc.get("scenario") or "?"
        thesis = sc.get("thesis", "")
        catalyst = sc.get("catalyst", "")
        prob = sc.get("probability")
        if prob is None:
            prob = sc.get("active_score", 0)
        prob_pct = prob * 100 if prob < 1.5 else prob
        prob_color = "#3FB950" if prob_pct > 70 else "#D29922" if prob_pct > 50 else "#8B949E"

        longs = sc.get("tickers_long") or sc.get("tickers") or []
        shorts = sc.get("tickers_short", [])

        with st.container():
            st.markdown(f"""<div class='narrative-card'>
                <div style='display:flex;align-items:center;justify-content:space-between;'>
                    <span style='font-weight:700;font-size:1rem;color:#E6EDF3;'>{name}</span>
                    <span style='background:{prob_color};color:#0D1117;padding:2px 10px;border-radius:12px;font-size:0.7rem;font-weight:800;'>{prob_pct:.0f}% prob</span>
                </div>
                <div style='font-size:0.78rem;color:#E6EDF3;margin-top:8px;line-height:1.5;'>{thesis}</div>
                <div style='font-size:0.65rem;color:#8B949E;margin-top:6px;'><b>Catalyst:</b> {catalyst}</div>
            </div>""", unsafe_allow_html=True)

            if longs or shorts:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**🟢 Long Exposure**")
                    for t in longs:
                        st.caption(f"• {t}")
                with c2:
                    if shorts:
                        st.markdown("**🔴 Short Exposure**")
                        for t in shorts:
                            st.caption(f"• {t}")
            st.markdown("---")
    
    # Citrini themes (always-on)
    st.subheader("📚 Permanent Themes (Citrini + Hedgeye)")
    permanent = [
        {
            "name": "Atoms Over Bits",
            "thesis": "Citrini thesis — physical AI bottlenecks (packaging, memory, optical, materials) outperform software. Seagate +200% in 2025 = early proof.",
            "tickers": ["MU", "STX", "WDC", "AVGO", "MRVL", "COHR", "LITE", "AMKR", "ASX", "TSM"],
        },
        {
            "name": "AI Power Infrastructure",
            "thesis": "Data center power crisis — 1000W+ chips need liquid cooling, transformers, gas turbines, nuclear baseload, GaN power.",
            "tickers": ["VRT", "ETN", "VST", "CEG", "CCJ", "SMR", "OKLO", "NVTS", "GEV"],
        },
        {
            "name": "China REE Export Controls",
            "thesis": "China weaponizing rare earth exports → Western miners + processors + magnet alternatives.",
            "tickers": ["MP", "USAR", "TMC", "UAMY", "LMT", "NOC"],
        },
        {
            "name": "AI Bureaucracy Alpha",
            "thesis": "Citrini — companies cutting headcount via AI: insurers, consultants, ad agencies, SaaS adopters.",
            "tickers": ["ACN", "CAP", "OMC", "WPP", "SAP"],
        },
        {
            "name": "Quad Rotation (Hedgeye)",
            "thesis": "Current Quad determines sector book — Q2=cyclicals/commodities, Q3=gold/defensives, Q4=duration/USD.",
            "tickers": ["XLE", "XLU", "XLF", "TLT", "UUP", "GLD"],
        },
    ]
    for theme in permanent:
        with st.expander(f"📌 {theme['name']}"):
            st.markdown(theme["thesis"])
            st.caption(f"**Tickers:** {', '.join(theme['tickers'])}")
