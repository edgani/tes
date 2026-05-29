"""dashboard.py — Restored from tes.zip original (Edward's preferred dashboard)"""
import streamlit as st


def render(snap: dict):
    """Entry point — delegates to legacy dashboard from tes.zip with proper prices/vix extraction."""
    try:
        from pages_lib._dashboard_legacy import render as _legacy_render
    except Exception as e:
        st.error(f"Dashboard legacy module failed to load: {e}")
        _fallback_dashboard(snap)
        return

    prices = snap.get("prices", {}) or {}
    vix_now = snap.get("vix", 20.0)
    if vix_now is None or vix_now == 0:
        # Try other paths
        try:
            vix_series = prices.get("^VIX")
            if vix_series is not None and len(vix_series) > 0:
                vix_now = float(vix_series.iloc[-1])
        except Exception:
            vix_now = 20.0

    try:
        _legacy_render(snap, prices, vix_now)
    except Exception as e:
        import traceback
        st.error(f"Legacy dashboard error: {e}")
        with st.expander("Traceback"):
            st.code(traceback.format_exc())
        _fallback_dashboard(snap)

    # ── TIER1ALPHA MARKET STRUCTURE + GLOBAL QUAD (appended) ─────────────
    _render_tier1alpha_panel(snap)


def _render_tier1alpha_panel(snap: dict):
    """Tier1Alpha-style 4-signal market structure + global quad."""
    import streamlit as st
    st.divider()
    st.markdown("## 📐 Market Structure Report (Tier1Alpha-style)")

    t1a = snap.get("tier1alpha", {})
    if not t1a:
        try:
            from engines.tier1alpha_model import compute_tier1alpha
            t1a = compute_tier1alpha(snap)
        except Exception:
            t1a = {}

    if t1a and t1a.get("signals"):
        sigs = t1a["signals"]

        def _sig_color(name, val):
            green = {"gamma_exposure": "Positive", "systematic_flow": "Bullish",
                     "pv_band_rr": "Long", "strategic_allocation": "Risk On"}
            red = {"gamma_exposure": "Negative", "systematic_flow": "Bearish",
                   "pv_band_rr": "Short", "strategic_allocation": "Risk Off"}
            if val == green.get(name): return "#1a7f37"
            if val == red.get(name): return "#cf222e"
            return "#bf8700"

        labels = {
            "gamma_exposure": "SPX Gamma Exposure",
            "systematic_flow": "Systematic Flow Risk",
            "pv_band_rr": "PV Band Risk/Reward",
            "strategic_allocation": "Strategic Allocation",
        }
        for key, label in labels.items():
            sig = sigs.get(key, {})
            val = sig.get("value", "Neutral")
            color = _sig_color(key, val)
            c1, c2 = st.columns([1, 3])
            with c1:
                st.markdown(
                    f"<div style='background:{color};color:white;padding:6px 12px;"
                    f"border-radius:6px;text-align:center;font-weight:800;'>{label}: {val}</div>",
                    unsafe_allow_html=True)
            with c2:
                st.caption(sig.get("note", ""))

        # SPX key levels
        lv = t1a.get("spx_levels", {})
        if lv.get("last_price"):
            st.markdown("**SPX Key Levels (PV Bands = TRADE TRR/LRR):**")
            lc1, lc2, lc3 = st.columns(3)
            lc1.metric("Last Price", f"{lv['last_price']:,.2f}")
            lc2.metric("Upper PV Band (TRR)", f"{lv.get('upper_pv_band', 0):,.2f}" if lv.get('upper_pv_band') else "—")
            lc3.metric("Lower PV Band (LRR)", f"{lv.get('lower_pv_band', 0):,.2f}" if lv.get('lower_pv_band') else "—")
        if t1a.get("data_quality") == "vix_proxy":
            st.caption("⚠️ Gamma signal using VIX proxy. Connect SPX options data (barchart/laevitas) for precise GEX.")

    # Global quad (Hedgeye)
    st.divider()
    gip = snap.get("gip", {})
    if isinstance(gip, dict):
        global_q = gip.get("global_quad") or gip.get("structural_quad") or snap.get("current_quad", "Q3")
        struct_q = gip.get("structural_quad", "?")
        month_q = gip.get("monthly_quad", "?")
    else:
        global_q = getattr(gip, "global_quad", None) or getattr(gip, "structural_quad", None) or "Q3"
        struct_q = getattr(gip, "structural_quad", "?")
        month_q = getattr(gip, "monthly_quad", "?")

    quad_names = {"Q1": "Goldilocks (Growth↑ Inflation↓)", "Q2": "Reflation (Growth↑ Inflation↑)",
                  "Q3": "Stagflation (Growth↓ Inflation↑)", "Q4": "Deflation (Growth↓ Inflation↓)"}
    gc1, gc2, gc3 = st.columns(3)
    gc1.metric("🌍 Global Quad (Hedgeye)", global_q, quad_names.get(global_q, ""))
    gc2.metric("Structural Quad", struct_q)
    gc3.metric("Monthly Quad", month_q)
    st.caption(f"Hedgeye GIP framework: Global economy currently in **{global_q}** — {quad_names.get(global_q, '')}")


def _fallback_dashboard(snap: dict):
    """Fallback minimal dashboard if legacy fails."""
    st.title("🏠 Dashboard (fallback)")
    gip = snap.get("gip", {})
    if isinstance(gip, dict):
        sq = gip.get("structural_quad", "?")
        mq = gip.get("monthly_quad", "?")
    else:
        sq = getattr(gip, "structural_quad", "?")
        mq = getattr(gip, "monthly_quad", "?")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Structural Quad", sq)
    c2.metric("Monthly Quad", mq)
    c3.metric("VIX", f"{(snap.get('vix') or 0):.2f}")
    c4.metric("DXY", f"{(snap.get('dxy') or 0):.2f}")
    health = snap.get("market_health", {})
    score = health.get("score", 50) if isinstance(health, dict) else 50
    c5.metric("Health", f"{score:.0f}/100")
