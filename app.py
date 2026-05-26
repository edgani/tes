"""
MacroRegime Pro v51 — Dashboard Tab Fix
Fixed: spacing, gaps, font sizing, layout compact
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS — Dark Mode Palette
# ═══════════════════════════════════════════════════════════════════
BG_DARK = "#0d1117"
CARD_BG = "#161b22"
BORDER = "#30363d"
TEXT_PRIMARY = "#c9d1d9"
TEXT_SECONDARY = "#8b949e"
GREEN = "#3FB950"
RED = "#F85149"
AMBER = "#D29922"
BLUE = "#58A6FF"
PURPLE = "#A371F7"

QUAD_COLORS = {"Q1": "#3FB950", "Q2": "#D29922", "Q3": "#F85149", "Q4": "#A371F7"}

# ═══════════════════════════════════════════════════════════════════
# PLOTLY CHART HELPERS — v51 Compact
# ═══════════════════════════════════════════════════════════════════

def _plotly_gauge(value, title, max_val=100, color=None, subtitle="", suffix="%", height=55):
    """Compact gauge with bigger font."""
    if color is None:
        color = GREEN if value >= 70 else AMBER if value >= 40 else RED

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": f"<b>{title}</b>", "font": {"size": 11, "color": TEXT_SECONDARY}},
        number={"suffix": suffix, "font": {"size": 18, "color": TEXT_PRIMARY, "family": "Inter"},
                "valueformat": ".0f" if suffix=="%" else ".1f"},
        gauge={
            "axis": {"range": [0, max_val], "tickwidth": 0, "tickfont": {"size": 8, "color": TEXT_SECONDARY}},
            "bar": {"color": color, "thickness": 0.75},
            "bgcolor": "#21262d",
            "borderwidth": 1,
            "bordercolor": BORDER,
            "steps": [
                {"range": [0, max_val*0.33], "color": "rgba(248,81,73,0.08)"},
                {"range": [max_val*0.33, max_val*0.66], "color": "rgba(210,153,34,0.08)"},
                {"range": [max_val*0.66, max_val], "color": "rgba(63,185,80,0.08)"},
            ],
        },
        domain={"x": [0, 1], "y": [0, 1]},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": TEXT_PRIMARY, "family": "Inter", "size": 10},
        height=height,
        margin={"t": 2, "b": 2, "l": 2, "r": 2},
    )
    if subtitle:
        fig.add_annotation(
            text=f"<span style='font-size:9px;color:{TEXT_SECONDARY}'>{subtitle}</span>",
            x=0.5, y=-0.08, showarrow=False
        )
    return fig

def _plotly_crash_meter(snap, height=75):
    """Compact 5-mini-gauge crash meter."""
    cm = snap.get("crash_meter", {}) if isinstance(snap.get("crash_meter"), dict) else {}
    indicators = [
        {"name": "YC", "value": cm.get("yield_curve_score", 1), "max": 5, "full": "Yield Curve"},
        {"name": "CS", "value": cm.get("credit_spread_score", 1), "max": 5, "full": "Credit Sprd"},
        {"name": "CAPE", "value": cm.get("cape_score", 1), "max": 5, "full": "CAPE"},
        {"name": "VIX", "value": cm.get("vix_percentile_score", 1), "max": 5, "full": "VIX %ile"},
        {"name": "MG", "value": cm.get("margin_score", 1), "max": 5, "full": "Margin"},
    ]
    for ind in indicators:
        v = ind["value"]
        ind["color"] = GREEN if v <= 1 else AMBER if v <= 2 else RED

    fig = make_subplots(
        rows=1, cols=5,
        specs=[[{"type": "indicator"}] * 5],
        subplot_titles=[ind["name"] for ind in indicators],
    )
    for i, ind in enumerate(indicators):
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=ind["value"],
            number={"font": {"size": 11, "color": TEXT_PRIMARY}},
            gauge={
                "axis": {"range": [0, ind["max"]], "tickwidth": 0, "tickfont": {"size": 6, "color": TEXT_SECONDARY}},
                "bar": {"color": ind["color"], "thickness": 0.8},
                "bgcolor": "#21262d",
                "borderwidth": 1,
                "bordercolor": BORDER,
                "steps": [
                    {"range": [0, 1.5], "color": "rgba(63,185,80,0.08)"},
                    {"range": [1.5, 2.5], "color": "rgba(210,153,34,0.08)"},
                    {"range": [2.5, 5], "color": "rgba(248,81,73,0.08)"},
                ],
            },
        ), row=1, col=i+1)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": TEXT_PRIMARY, "family": "Inter", "size": 9},
        height=height,
        margin={"t": 18, "b": 2, "l": 2, "r": 2},
        annotations=[{"text": f"<b>🚨 Crash Meter</b> — {'AMAN' if all(i['value']<=2 for i in indicators) else 'WASPADA' if any(i['value']>=3 for i in indicators) else 'KRITIS'}",
                      "x": 0.5, "y": -0.02, "showarrow": False,
                      "font": {"size": 9, "color": TEXT_SECONDARY}}],
    )
    return fig

def _plotly_asset_pulse(snap, prices, height=60):
    """Ultra-compact asset pulse."""
    pulse_assets = [
        ("SPY", "SPY"), ("QQQ", "QQQ"), ("IWM", "IWM"), ("GLD", "GLD"),
        ("TLT", "TLT"), ("UUP", "DXY"), ("BTC-USD", "BTC"), ("ETH-USD", "ETH"),
    ]
    labels, values, colors = [], [], []
    for t, label in pulse_assets:
        ret = _price_ret(t, prices, 21)
        if ret is not None:
            labels.append(label)
            values.append(ret * 100)
            colors.append(GREEN if ret > 0.03 else "#2EA043" if ret > 0 else "#DA3633" if ret < -0.03 else RED if ret < 0 else AMBER)

    fig = go.Figure(go.Bar(
        y=labels, x=values, orientation="h",
        marker={"color": colors, "opacity": 0.9},
        text=[f"{v:+.1f}%" for v in values],
        textposition="outside",
        textfont={"color": TEXT_PRIMARY, "size": 9},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": TEXT_PRIMARY, "family": "Inter", "size": 9},
        height=height,
        margin={"t": 2, "b": 2, "l": 2, "r": 40},
        xaxis={"visible": False},
        yaxis={"tickfont": {"size": 9, "color": TEXT_PRIMARY}, "gridcolor": "#21262d"},
        showlegend=False,
    )
    return fig

def _plotly_boombust_timeline(snap):
    """HTML timeline instead of gauge — more intuitive."""
    bb = snap.get("boom_bust", {}) or {}
    stage = bb.get("stage", "INCEPTION") if isinstance(bb, dict) else "INCEPTION"
    reflex = snap.get("reflexivity", {}) or {}
    score = reflex.get("super_bubble_score", 0) if isinstance(reflex, dict) else 0

    stages = ["INCEPTION", "ACCELERATION", "EUPHORIA", "CRISIS", "AUCTION"]
    stage_colors = {"INCEPTION": GREEN, "ACCELERATION": AMBER, "EUPHORIA": RED, "CRISIS": RED, "AUCTION": GREEN}
    color = stage_colors.get(stage, AMBER)

    # Build timeline HTML
    idx = stages.index(stage) if stage in stages else 0
    nodes = []
    for i, s in enumerate(stages):
        if i < idx:
            nodes.append(f'<span style="color:{GREEN};font-size:10px;">● {s}</span>')
        elif i == idx:
            nodes.append(f'<span style="color:{color};font-size:11px;font-weight:bold;">● {s}</span>')
        else:
            nodes.append(f'<span style="color:{TEXT_SECONDARY};font-size:9px;">○ {s}</span>')

    timeline = "━━".join(nodes)
    bar_width = int(score * 10)

    html = f"""
    <div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:6px;padding:6px 8px;">
        <div style="font-size:10px;color:{TEXT_SECONDARY};margin-bottom:3px;">🌀 Boom-Bust Stage</div>
        <div style="font-size:11px;color:{TEXT_PRIMARY};margin-bottom:4px;">{timeline}</div>
        <div style="font-size:10px;color:{color};font-weight:bold;">Score: {score:.1f}/10</div>
        <div style="background:#21262d;height:6px;border-radius:3px;margin-top:3px;">
            <div style="background:{color};width:{bar_width}%;height:6px;border-radius:3px;"></div>
        </div>
    </div>
    """
    return html

def _plotly_behavioral_bar(snap, height=50):
    """Compact sentiment bar."""
    behavioral = snap.get("behavioral_macro", {}) or {}
    bullish = behavioral.get("bullish", 30) or 30
    bearish = behavioral.get("bearish", 30) or 30
    neutral = behavioral.get("neutral", 40) or 40
    total = bullish + bearish + neutral
    if total == 0:
        total = 1

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Bull", y=[""], x=[bullish/total*100], marker={"color": GREEN}, text=[f"🐂{bullish:.0f}%"], textposition="inside", textfont={"size": 9, "color": "white"}))
    fig.add_trace(go.Bar(name="Neut", y=[""], x=[neutral/total*100], marker={"color": TEXT_SECONDARY}, text=[f"⚖{neutral:.0f}%"], textposition="inside", textfont={"size": 9, "color": "white"}))
    fig.add_trace(go.Bar(name="Bear", y=[""], x=[bearish/total*100], marker={"color": RED}, text=[f"🐻{bearish:.0f}%"], textposition="inside", textfont={"size": 9, "color": "white"}))

    casino = min(100, max(0, (bullish - 45) * 3))
    status = "🟢 Aman" if casino <= 30 else "🟡 Waspada" if casino <= 60 else "🔴 Casino"

    fig.update_layout(
        barmode="stack", showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": TEXT_PRIMARY, "size": 9},
        height=height,
        margin={"t": 2, "b": 14, "l": 2, "r": 2},
        xaxis={"visible": False}, yaxis={"visible": False},
        annotations=[{"text": f"<b>{status}</b> · Score: {casino:.0f}/100", "x": 0.5, "y": -0.15,
                      "showarrow": False, "font": {"size": 9, "color": TEXT_SECONDARY}}],
    )
    return fig

def _penjelasan(text):
    """Format penjelasan teks."""
    return f'<div style="font-size:0.65rem;color:#8b949e;margin-top:3px;line-height:1.4;background:#161b22;border:1px solid #30363d;border-radius:4px;padding:4px 6px;">📖 {text}</div>'

# ═══════════════════════════════════════════════════════════════════
# PAGE DASHBOARD — v51 Layout Fix
# ═══════════════════════════════════════════════════════════════════

def page_dashboard():
    st.markdown("## 🏠 Macro Dashboard")

    # Get snap and prices from global scope
    snap = globals().get("snap", {})
    prices = globals().get("prices", {})
    vix_now = globals().get("vix_now", 20)

    # ── ROW 1: Regime Cards (kiri) + Gauge Grid (kanan) ──
    r1_left, r1_right = st.columns([1.2, 1])

    with r1_left:
        # Regime Cards — compact
        summary = snap.get("summary", {}) or {}
        health = snap.get("health", {}) or {}
        markov = snap.get("markov_v3", {}) or {}
        behavioral = snap.get("behavioral_macro", {}) or {}

        gip_data = snap.get("gip")
        structural = "Q3"
        monthly = "Q2"
        markov_q = "Q1"
        conf = 0
        kelly = 0.25

        if gip_data and hasattr(gip_data, 'structural_probs'):
            probs = gip_data.structural_probs
            if probs:
                structural = max(probs, key=probs.get)
                conf = probs.get(structural, 0) * 100

        # 3 mini cards
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:6px;padding:6px;text-align:center;">
                <div style="font-size:9px;color:{TEXT_SECONDARY}">STRUCTURAL</div>
                <div style="font-size:14px;color:{RED};font-weight:bold;">{structural}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:6px;padding:6px;text-align:center;">
                <div style="font-size:9px;color:{TEXT_SECONDARY}">MONTHLY</div>
                <div style="font-size:14px;color:{AMBER};font-weight:bold;">{monthly}</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:6px;padding:6px;text-align:center;">
                <div style="font-size:9px;color:{TEXT_SECONDARY}">MARKOV</div>
                <div style="font-size:14px;color:{GREEN};font-weight:bold;">{markov_q}</div>
            </div>
            """, unsafe_allow_html=True)

        # Sentiment mini bar
        fig_sent = _plotly_behavioral_bar(snap, height=45)
        st.plotly_chart(fig_sent, use_container_width=True, config={"displayModeBar": False}, key="sent_v51")

        # Proyeksi transisi
        st.markdown(f"""
        <div style="background:{CARD_BG};border:1px solid {BORDER};border-radius:6px;padding:5px 8px;margin-top:3px;">
            <div style="font-size:9px;color:{TEXT_SECONDARY}">📅 PROYEKSI TRANSI</div>
            <div style="font-size:11px;color:{TEXT_PRIMARY};font-weight:bold;">{structural} → {monthly}</div>
            <div style="font-size:9px;color:{TEXT_SECONDARY}">Prob: {conf:.0f}% · Est: ~30-60 hari</div>
        </div>
        """, unsafe_allow_html=True)

    with r1_right:
        # 2x2 Gauge Grid — compact, no gaps
        g1, g2 = st.columns(2)
        with g1:
            vix_color = GREEN if vix_now < 18 else AMBER if vix_now < 25 else RED
            fig = _plotly_gauge(vix_now, "VIX", max_val=40, color=vix_color, subtitle="Tenang", suffix="", height=55)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="vix_v51")
        with g2:
            health_score = health.get("composite_score", 50) if isinstance(health, dict) else 50
            hcolor = GREEN if health_score >= 70 else AMBER if health_score >= 50 else RED
            fig = _plotly_gauge(health_score, "HEALTH", max_val=100, color=hcolor, subtitle="Sedang", height=55)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="health_v51")

        g3, g4 = st.columns(2)
        with g3:
            kelly_val = markov.get("kelly_fraction", 0.25) if isinstance(markov, dict) else 0.25
            kcolor = GREEN if kelly_val >= 0.5 else AMBER if kelly_val >= 0.25 else RED
            fig = _plotly_gauge(kelly_val*100, "KELLY", max_val=100, color=kcolor, subtitle="Normal", suffix="%", height=55)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="kelly_v51")
        with g4:
            n_alerts = len((snap.get("yves_v2", {}) or {}).get("alerts", [])) if isinstance(snap.get("yves_v2"), dict) else 0
            acolor = RED if n_alerts > 2 else AMBER if n_alerts > 0 else GREEN
            fig = _plotly_gauge(n_alerts, "ALERTS", max_val=10, color=acolor, subtitle="Aman", suffix="", height=55)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="alerts_v51")

    # ── ROW 2: Crash Meter (kiri) + Bubble (kanan) ──
    r2_left, r2_right = st.columns([1, 1])

    with r2_left:
        fig_crash = _plotly_crash_meter(snap, height=75)
        st.plotly_chart(fig_crash, use_container_width=True, config={"displayModeBar": False}, key="crash_v51")

    with r2_right:
        bubble_html = _plotly_boombust_timeline(snap)
        st.markdown(bubble_html, unsafe_allow_html=True)

    # ── ROW 3: Asset Pulse (full width) ──
    fig_pulse = _plotly_asset_pulse(snap, prices, height=55)
    st.plotly_chart(fig_pulse, use_container_width=True, config={"displayModeBar": False}, key="pulse_v51")

    # ── Deep Technical (expander, collapsed) ──
    with st.expander("🔬 Deep Technical", expanded=False):
        st.caption("CRI v2 · Squeeze · VRP data")

# Utility function placeholder
def _price_ret(ticker, prices, days):
    """Calculate return over N days."""
    if ticker not in prices or len(prices[ticker]) < days + 1:
        return None
    hist = prices[ticker]
    if len(hist) < 2:
        return None
    return (hist[-1] / hist[-days-1]) - 1 if hist[-days-1] != 0 else None
