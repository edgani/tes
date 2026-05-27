"""dashboard.py — Main dashboard page"""
import streamlit as st


def render(snap: dict):
    st.title("📊 Dashboard")
    
    gip = snap.get("gip", {})
    if not isinstance(gip, dict):
        gip = {"structural_quad": getattr(gip, "structural_quad", "?"),
               "monthly_quad": getattr(gip, "monthly_quad", "?")}
    
    # ── Top KPIs ─────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Structural Quad", gip.get("structural_quad", "—"))
    with c2:
        st.metric("Monthly Quad", gip.get("monthly_quad", "—"))
    with c3:
        vix = snap.get("vix", 0)
        st.metric("VIX", f"{vix:.2f}")
    with c4:
        dxy = snap.get("dxy", 0)
        st.metric("DXY", f"{dxy:.2f}")
    with c5:
        health = snap.get("market_health", {})
        score = health.get("composite_score", 50) if isinstance(health, dict) else 50
        st.metric("Health", f"{score:.0f}/100")
    
    st.divider()
    
    # ── Quad Probabilities (from discovery_brain Bayesian) ───────────────
    st.subheader("🎯 Quad Probability Distribution")
    quad_probs = gip.get("structural_probabilities") or snap.get("quad_probabilities", {})
    if quad_probs:
        cols = st.columns(4)
        for i, q in enumerate(["Q1", "Q2", "Q3", "Q4"]):
            with cols[i]:
                p = quad_probs.get(q, 0) * 100 if isinstance(quad_probs.get(q), float) and quad_probs.get(q) < 1.5 else quad_probs.get(q, 0)
                color = {"Q1": "#3FB950", "Q2": "#D29922", "Q3": "#F85149", "Q4": "#A371F7"}[q]
                st.markdown(f"""<div style='background:#161B22;border:1px solid {color};border-radius:8px;padding:10px;text-align:center;'>
                    <div style='font-size:0.7rem;color:{color};text-transform:uppercase;font-weight:700;'>{q}</div>
                    <div style='font-size:1.3rem;font-weight:800;color:{color};'>{p:.1f}%</div>
                    <div style='font-size:0.55rem;color:#8B949E;'>{_quad_label(q)}</div>
                </div>""", unsafe_allow_html=True)
    else:
        st.info("Quad probability data not available.")
    
    st.divider()
    
    # ── Active Scenarios ────────────────────────────────────────────────
    st.subheader("🌐 Active Macro Scenarios")
    scenarios = snap.get("scenarios", []) or snap.get("active_scenarios", [])
    if scenarios:
        for sc in scenarios[:5]:
            if isinstance(sc, dict):
                st.markdown(f"""<div class='narrative-card'>
                    <div style='font-size:0.85rem;font-weight:600;color:#E6EDF3;'>{sc.get('name', '?')}</div>
                    <div style='font-size:0.7rem;color:#8B949E;margin-top:4px;'>{sc.get('thesis', '')}</div>
                    <div style='font-size:0.65rem;color:#58A6FF;margin-top:6px;'>
                        <b>Long:</b> {', '.join(sc.get('tickers_long', [])[:5])}
                    </div>
                    <div style='font-size:0.6rem;color:#8B949E;margin-top:2px;'>
                        Probability: {sc.get('probability', 0)*100:.0f}% · Catalyst: {sc.get('catalyst', '')}
                    </div>
                </div>""", unsafe_allow_html=True)
    else:
        st.info("No active scenarios detected.")
    
    st.divider()
    
    # ── Macro Transmission ──────────────────────────────────────────────
    st.subheader("🔗 Active Chain Reactions")
    transmissions = snap.get("transmissions", {}) or snap.get("active_transmissions", {})
    if isinstance(transmissions, dict) and transmissions.get("active_transmissions"):
        for t in transmissions["active_transmissions"][:5]:
            driver = t.get("driver", "?")
            shock = t.get("shock_pct", 0)
            top = t.get("top_impact", [])
            shock_color = "#3FB950" if shock > 0 else "#F85149"
            st.markdown(f"""<div style='background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px;margin:4px 0;'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <span style='font-weight:700;color:#E6EDF3;'>{driver}</span>
                    <span style='color:{shock_color};font-weight:700;font-size:0.9rem;'>{shock:+.2f}%</span>
                </div>
                <div style='font-size:0.65rem;color:#8B949E;margin-top:4px;'>
                    Top impacts: {', '.join([f"{x.get('ticker', '?')} ({x.get('expected_pct', 0):+.1f}%)" for x in top[:5]])}
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No active shocks detected (no driver moved >3% in 5d).")


def _quad_label(q):
    return {
        "Q1": "Growth↑ Inflation↓",
        "Q2": "Growth↑ Inflation↑",
        "Q3": "Growth↓ Inflation↑",
        "Q4": "Growth↓ Inflation↓",
    }.get(q, "")
