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
