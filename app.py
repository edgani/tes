"""app.py — MacroRegime Pro v28.0 CLEAN
Complete UI rewrite:
- Modular page functions (no spaghetti)
- Consolidated sub-tabs (max 3 per page)
- Card-based ticker display
- Unified regime banner across all pages
- Fixed: vix_val NameError → vix_now
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

st.set_page_config(page_title="MacroRegime Pro v28", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════════════
# DESIGN SYSTEM CSS
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Base ── */
.block-container { padding-top: 1rem !important; padding-bottom: 0.8rem !important; padding-left: 1.2rem !important; padding-right: 1.2rem !important; max-width: 1400px !important; }
h1 { font-size: 1.6rem !important; margin: 0.4rem 0 0.5rem !important; font-weight: 700 !important; }
h2 { font-size: 1.25rem !important; margin: 0.5rem 0 0.4rem !important; font-weight: 700 !important; letter-spacing: -0.3px; }
h3 { font-size: 1.05rem !important; margin: 0.6rem 0 0.3rem !important; font-weight: 600 !important; }
hr { margin: 0.6rem 0 !important; opacity: 0.12; border-color: #30363D; }

/* ── Metrics ── */
[data-testid="stMetric"] { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; padding: 6px 10px !important; }
[data-testid="stMetricLabel"] { font-size: 0.65rem !important; font-weight: 600 !important; letter-spacing: 0.6px; text-transform: uppercase; opacity: 0.6; }
[data-testid="stMetricValue"] { font-size: 1.15rem !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"] { font-size: 0.7rem !important; }

/* ── Cards ── */
.mr-card { background: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 10px 12px; margin: 6px 0; transition: border-color 0.2s; }
.mr-card:hover { border-color: #484F58; }
.mr-card-title { font-size: 0.65rem; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; color: #8B949E; margin-bottom: 4px; }
.mr-card-value { font-size: 1.1rem; font-weight: 700; color: #E6EDF3; }
.mr-card-sub { font-size: 0.72rem; color: #8B949E; margin-top: 2px; }

/* ── Pills ── */
.mr-pill { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: 600; margin-right: 4px; margin-bottom: 4px; border: 1px solid transparent; }
.pill-long { background: rgba(34,197,94,0.12); color: #22c55e; border-color: rgba(34,197,94,0.3); }
.pill-short { background: rgba(239,68,68,0.12); color: #ef4444; border-color: rgba(239,68,68,0.3); }
.pill-neut { background: rgba(234,179,8,0.12); color: #eab308; border-color: rgba(234,179,8,0.3); }
.pill-info { background: rgba(88,166,255,0.12); color: #58A6FF; border-color: rgba(88,166,255,0.3); }
.pill-grad-a { background: rgba(34,197,94,0.15); color: #3FB950; border-color: #3FB950; }
.pill-grad-b { background: rgba(234,179,8,0.15); color: #D29922; border-color: #D29922; }
.pill-grad-c { background: rgba(139,148,158,0.15); color: #8B949E; border-color: #8B949E; }

/* ── Risk Range Bar ── */
.rr-track { position: relative; height: 22px; background: #21262D; border-radius: 4px; overflow: hidden; margin: 6px 0; }
.rr-zone { position: absolute; top: 2px; bottom: 2px; border-radius: 2px; }
.rr-dot { position: absolute; top: 50%; transform: translate(-50%, -50%); width: 10px; height: 10px; border-radius: 50%; background: #E6EDF3; border: 2px solid #58A6FF; z-index: 10; }

/* ── Ticker Card (horizontal) ── */
.ticker-row { display: flex; align-items: center; gap: 12px; padding: 8px 10px; background: #161B22; border: 1px solid #30363D; border-radius: 8px; margin: 4px 0; font-size: 0.85rem; }
.ticker-row:hover { border-color: #484F58; }
.ticker-symbol { font-weight: 700; font-size: 0.95rem; min-width: 60px; }
.ticker-price { font-weight: 600; font-variant-numeric: tabular-nums; min-width: 70px; text-align: right; }
.ticker-rr { flex: 1; min-width: 120px; }
.ticker-badges { display: flex; gap: 4px; flex-wrap: wrap; }

/* ── Tables ── */
[data-testid="stDataFrame"] { font-size: 0.82rem !important; }
[data-testid="stDataFrame"] td { padding: 4px 8px !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 2px !important; margin-bottom: 8px !important; }
.stTabs [data-baseweb="tab"] { padding: 5px 14px !important; font-size: 0.82rem !important; font-weight: 500 !important; border-radius: 6px 6px 0 0 !important; }

/* ── Expander ── */
[data-testid="stExpander"] { border: 1px solid #30363D !important; border-radius: 8px !important; margin-bottom: 8px !important; }
[data-testid="stExpander"] > details > summary { padding: 8px 12px !important; font-size: 0.85rem !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] .block-container { padding-top: 0.8rem !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# CONFIG & FALLBACKS
# ═══════════════════════════════════════════════════════════════════
try:
    from config.settings import (FOREX_PAIRS, COMMODITIES, CRYPTO, IHSG_UNIVERSE,
                                 IHSG_SECTOR_MAP, TICKER_SECTOR, US_SECTORS, US_BUCKETS)
except ImportError:
    FOREX_PAIRS = {}; COMMODITIES = {}; CRYPTO = {}; IHSG_UNIVERSE = {}; TICKER_SECTOR = {}; US_SECTORS = {}; US_BUCKETS = {}
    IHSG_SECTOR_MAP = {
        "ADRO.JK": "Coal", "ITMG.JK": "Coal", "PTBA.JK": "Coal",
        "NCKL.JK": "Nickel", "ANTM.JK": "Nickel", "INCO.JK": "Nickel",
        "AALI.JK": "CPO", "LSIP.JK": "CPO", "SMAR.JK": "CPO",
        "BBRI.JK": "Banking", "BMRI.JK": "Banking", "BBCA.JK": "Banking", "BBNI.JK": "Banking", "BRIS.JK": "Banking",
        "TLKM.JK": "Telco", "EXCL.JK": "Telco",
        "UNTR.JK": "Mining Contractor", "BYAN.JK": "Mining",
        "ICBP.JK": "Consumer", "INDF.JK": "Consumer", "KLBF.JK": "Pharma",
        "PGEO.JK": "Geothermal", "WINS.JK": "Shipping",
        "EIDO": "ETF", "^JKSE": "Index",
    }

# ═══════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════
def _safe_float(v):
    if v is None: return None
    try:
        if isinstance(v, pd.Series): v = v.iloc[0]
        f = float(v)
        return f if math.isfinite(f) else None
    except: return None

def fp(v):
    try: return f"{float(v):.1%}" if v is not None and math.isfinite(float(v)) else "—"
    except: return "—"

def ff(v, d=2):
    try: return f"{float(v):,.{d}f}" if v is not None and math.isfinite(float(v)) else "—"
    except: return "—"

def _price_ret(ticker, prices, days=21):
    s = prices.get(ticker)
    if s is None: return None
    s = pd.to_numeric(s, errors="coerce").dropna()
    if len(s) < days + 1: return None
    try: return float(s.iloc[-1] / s.iloc[-(days+1)] - 1)
    except: return None

def _quad_color(q):
    return {"Q1": "#3FB950", "Q2": "#D29922", "Q3": "#F85149", "Q4": "#A371F7"}.get(q, "#8B949E")

def _quad_name(q):
    return {"Q1": "Goldilocks", "Q2": "Reflation", "Q3": "Stagflation", "Q4": "Deflation"}.get(q, q)

def _grade_pill(grade):
    g = str(grade).upper()
    if g in ("A", "A+"): return '<span class="mr-pill pill-grad-a">A</span>'
    if g == "B": return '<span class="mr-pill pill-grad-b">B</span>'
    return '<span class="mr-pill pill-grad-c">C</span>'

def _direction_pill(direction):
    d = str(direction).upper()
    if "LONG" in d: return '<span class="mr-pill pill-long">🟢 LONG</span>'
    if "SHORT" in d: return '<span class="mr-pill pill-short">🔴 SHORT</span>'
    return '<span class="mr-pill pill-neut">⚪ NEUTRAL</span>'

def _regime_banner(quad, conf=0.0, monthly=None):
    color = _quad_color(quad)
    name = _quad_name(quad)
    mq_html = f' <span style="opacity:0.6;font-size:0.75rem;">Monthly: {monthly}</span>' if monthly else ''
    return f"""
    <div style="background: linear-gradient(90deg, {color}15 0%, transparent 70%); border-left: 4px solid {color}; 
                border-radius: 8px; padding: 10px 14px; margin: 8px 0; display: flex; align-items: center; gap: 12px;">
        <div style="font-size: 1.4rem; font-weight: 800; color: {color}; letter-spacing: -0.5px;">{quad}</div>
        <div>
            <div style="font-size: 0.95rem; font-weight: 700; color: #E6EDF3;">{name}</div>
            <div style="font-size: 0.75rem; color: #8B949E;">Confidence: {conf:.0%}{mq_html}</div>
        </div>
    </div>
    """

def _kpi_card(title, value, subtitle="", color="#E6EDF3"):
    return f"""
    <div class="mr-card">
        <div class="mr-card-title">{title}</div>
        <div class="mr-card-value" style="color: {color};">{value}</div>
        {f'<div class="mr-card-sub">{subtitle}</div>' if subtitle else ''}
    </div>
    """

# ═══════════════════════════════════════════════════════════════════
# RISK RANGE ENGINE
# ═══════════════════════════════════════════════════════════════════
def _rr_levels(px, lrr, trr, side="long"):
    px = _safe_float(px) or 0; lrr = _safe_float(lrr) or 0; trr = _safe_float(trr) or 0
    if not (lrr > 0 and trr > 0 and trr > lrr): return None
    spread = trr - lrr
    pos = (px - lrr) / spread if spread > 0 else 0.5
    if side == "long":
        entry = round(lrr, 2); tp1 = round(lrr + spread * 0.5, 2); tp2 = round(trr, 2); stop = round(lrr - spread * 0.25, 2)
        near_entry = pos <= 0.35
    else:
        entry = round(trr, 2); tp1 = round(trr - spread * 0.5, 2); tp2 = round(lrr, 2); stop = round(trr + spread * 0.25, 2)
        near_entry = pos >= 0.65
    rr = round(abs(tp1 - entry) / max(abs(entry - stop), 0.01), 2)
    return {"entry": entry, "tp1": tp1, "tp2": tp2, "stop": stop, "rr": rr, "pos": round(pos, 2), "near_entry": near_entry, "side": side}

def _build_row(ticker, prices, ar, vix_now=20, gamma_data=None, greeks_data=None, market_type="us_equity", news=None):
    """Build a clean ticker row dict with all needed fields."""
    v = ar.get(ticker, {}) if ar else {}
    s = prices.get(ticker)
    if not v and (s is None or len(s) < 60):
        return None

    # Build risk range from price if no ar data
    if not v and s is not None:
        s_clean = pd.to_numeric(s, errors="coerce").dropna()
        if len(s_clean) < 60: return None
        px = float(s_clean.iloc[-1]); sma20 = float(s_clean.tail(20).mean()); std20 = float(s_clean.tail(20).std())
        if not all(math.isfinite(v) for v in [px, sma20, std20]): return None
        lrr = round(sma20 - 1.5 * std20, 4); trr = round(sma20 + 1.5 * std20, 4)
        comp = "bullish" if px < lrr else "bearish" if px > trr else "neutral"
        if comp == "neutral": return None
        v = {"px": px, "trade": {"lrr": lrr, "trr": trr}, "composite": comp, "quality": "B", "market": market_type}

    tr = v.get("trade", {}); px = _safe_float(v.get("px")); lrr = _safe_float(tr.get("lrr")); trr = _safe_float(tr.get("trr"))
    if not px or not lrr or not trr: return None

    composite = v.get("composite", "neutral")
    side = "long" if composite == "bullish" else "short"
    rl = _rr_levels(px, lrr, trr, side)
    if not rl: return None

    # 3-tier ranges
    trend_l = trend_r = tail_l = tail_r = None
    if s is not None and len(s) >= 50:
        s_clean = pd.to_numeric(s, errors="coerce").dropna()
        if len(s_clean) >= 50:
            sma50 = float(s_clean.tail(50).mean()); std50 = float(s_clean.tail(50).std())
            if math.isfinite(sma50) and math.isfinite(std50):
                trend_l = round(sma50 - 1.5 * std50, 4); trend_r = round(sma50 + 1.5 * std50, 4)
        if len(s_clean) >= 200:
            sma200 = float(s_clean.tail(200).mean()); std200 = float(s_clean.tail(200).std())
            if math.isfinite(sma200) and math.isfinite(std200):
                tail_l = round(sma200 - 2.0 * std200, 4); tail_r = round(sma200 + 2.0 * std200, 4)
        elif len(s_clean) >= 100:
            sma100 = float(s_clean.tail(100).mean()); std100 = float(s_clean.tail(100).std())
            if math.isfinite(sma100) and math.isfinite(std100):
                tail_l = round(sma100 - 2.0 * std100, 4); tail_r = round(sma100 + 2.0 * std100, 4)

    # Greeks proxy
    gamma = {"ok": False}; greek = {"ok": False}
    if s is not None and len(s) >= 20:
        s_clean = pd.to_numeric(s, errors="coerce").dropna()
        if len(s_clean) >= 20:
            sma20 = float(s_clean.tail(20).mean()); std20 = float(s_clean.tail(20).std())
            gamma = {
                "ok": True, "regime": "TRANSITION", "max_pain": round(sma20, 2),
                "put_wall": round(sma20 - std20 * 2.0, 2), "call_wall": round(sma20 + std20 * 2.0, 2),
                "gamma_flip_up": round(sma20 + std20 * 1.5, 2), "gamma_flip_down": round(sma20 - std20 * 1.5, 2),
            }
            r1m = _price_ret(ticker, prices, 21) or 0
            greek = {
                "ok": True, "composite": "NEUTRAL ⚪", "delta": "Long 🟢" if r1m > 0.03 else ("Short 🔴" if r1m < -0.03 else "Neutral ⚪"),
                "gamma": "Flat ⚪", "vanna": "Mixed 🟡", "charm": "Stable 🟡", "vol": "Normal 🟢" if vix_now < 20 else ("Elevated 🟡" if vix_now < 25 else "High 🔴"),
            }

    # News
    news_signal = ""; news_headline = ""; news_sentiment = 0
    if news and news.get("ticker_specific"):
        tn = news["ticker_specific"].get(ticker, {})
        news_signal = tn.get("front_run_signal", "")
        news_headline = (tn.get("headlines") or [""])[0] if tn else ""
        news_sentiment = tn.get("sentiment_score", 0) or 0

    # Composite direction (simplified)
    direction = "LONG" if composite == "bullish" else "SHORT"
    grade = v.get("quality", "B").replace("short_", "").upper()

    return {
        "ticker": ticker, "price": px, "entry": rl["entry"], "target_1": rl["tp1"], "target_2": rl["tp2"],
        "stop": rl["stop"], "rr": rl["rr"], "direction": direction, "grade": grade,
        "near_entry": rl["near_entry"], "pos_in_range": rl["pos"], "side": rl["side"],
        "trade_l": lrr, "trade_r": trr, "trend_l": trend_l, "trend_r": trend_r, "tail_l": tail_l, "tail_r": tail_r,
        "r1m": _price_ret(ticker, prices, 21), "r3m": _price_ret(ticker, prices, 63),
        "composite": composite, "market_type": market_type,
        "gamma_regime": gamma.get("regime"), "max_pain": gamma.get("max_pain"),
        "put_wall": gamma.get("put_wall"), "call_wall": gamma.get("call_wall"),
        "gamma_flip_up": gamma.get("gamma_flip_up"), "gamma_flip_down": gamma.get("gamma_flip_down"),
        "greek_delta": greek.get("delta"), "greek_gamma": greek.get("gamma"),
        "greek_vanna": greek.get("vanna"), "greek_charm": greek.get("charm"), "greek_vol": greek.get("vol"),
        "news_signal": news_signal, "news_headline": news_headline, "news_sentiment": news_sentiment,
        "options_source": "PROXY",
    }

def _build_ihsg_row(ticker, prices, ar, **kwargs):
    row = _build_row(ticker, prices, ar, market_type="ihsg", **kwargs)
    if not row: return None
    row["direction"] = "LONG"  # IHSG only long
    sector = IHSG_SECTOR_MAP.get(ticker, "Indonesia")
    row["sector"] = sector
    r1m = row.get("r1m", 0) or 0
    if r1m > 0.05: row["recommendation"] = f"Strong momentum +{r1m:.1%} — {sector} play"
    elif r1m < -0.05: row["recommendation"] = f"Weak momentum {r1m:.1%} — avoid {sector}"
    else: row["recommendation"] = f"{sector} — range bound, wait for breakout"
    return row

# ═══════════════════════════════════════════════════════════════════
# SESSION & SIDEBAR
# ═══════════════════════════════════════════════════════════════════
if "snap" not in st.session_state: st.session_state.snap = None
if "loading" not in st.session_state: st.session_state.loading = False
if "mq_override" not in st.session_state: st.session_state.mq_override = "Auto"

with st.sidebar:
    st.markdown("## 📊 MacroRegime Pro")
    st.caption("v28.0 Clean | Hedgeye + Forward AI")
    st.divider()

    page = st.radio("Navigation", [
        "🏠 Dashboard", "⚡ Alpha Center", "🇺🇸 US Stocks", "💱 Forex",
        "🛢️ Commodities", "₿ Crypto", "🌍 Global & EM", "📖 Themes"
    ], label_visibility="collapsed")

    st.divider()
    try:
        from data.loader import snapshot_age_str
        st.caption(f"Last update: {snapshot_age_str()}")
    except:
        st.caption("Last update: unknown")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Update", use_container_width=True): st.session_state.loading = True
    with c2:
        if st.button("⚡ Rebuild", use_container_width=True):
            st.session_state.loading = True; st.session_state.snap = None

    with st.expander("⚙️ Settings"):
        inc_us = st.checkbox("US Stocks", True)
        inc_fx = st.checkbox("Forex", True)
        inc_comm = st.checkbox("Commodities", True)
        inc_cryp = st.checkbox("Crypto", True)
        inc_ihsg = st.checkbox("Indonesia", True)

    with st.expander("💰 Portfolio"):
        pv = st.number_input("Value", min_value=1000, max_value=1_000_000_000,
                            value=int(st.session_state.get("portfolio_value", 100_000)), step=10_000)
        st.session_state["portfolio_value"] = pv

    with st.expander("🔧 Quad Override"):
        mq_ov = st.selectbox("Monthly", ["Auto", "Q1", "Q2", "Q3", "Q4"],
                            index=["Auto", "Q1", "Q2", "Q3", "Q4"].index(st.session_state.mq_override))
        st.session_state.mq_override = mq_ov

    st.divider()
    _s = st.session_state.snap
    if _s and _s.get("ok"):
        _g = _s.get("gip")
        _sq = _g.structural_quad if _g else "—"
        _mq = _g.monthly_quad if _g else "—"
        color = _quad_color(_sq)
        st.markdown(f"""
        <div style="background:#161B22; border:1px solid #30363D; border-radius:8px; padding:10px; text-align:center;">
            <div style="font-size:0.65rem; color:#8B949E; text-transform:uppercase; letter-spacing:0.5px;">REGIME</div>
            <div style="font-size:1.1rem; font-weight:700; color:{color}; margin:4px 0;">{_sq} / {_mq}</div>
            <div style="font-size:0.7rem; color:#8B949E;">{_quad_name(_sq)}</div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════
snap = st.session_state.snap
if snap is None:
    try:
        from data.loader import load_snapshot
        snap = load_snapshot(max_age_hours=6.0)
        if snap and snap.get("ok"): st.session_state.snap = snap
    except Exception as e:
        logger.warning(f"Initial snapshot load failed: {e}")
        snap = None

if snap is None or not snap.get("ok") or st.session_state.loading:
    try:
        from orchestrator import build_snapshot
    except Exception as e:
        st.error(f"Failed to import orchestrator: {e}"); st.stop()
    _msg = "Updating..." if st.session_state.loading else "Building..."
    with st.spinner(_msg):
        pb = st.progress(0.0); pt = st.empty()
        def prog(m, f): pb.progress(f); pt.caption(f"Loading {m}")
        try:
            snap = build_snapshot(progress_cb=prog, include_us_stocks=inc_us, include_forex=inc_fx,
                                  include_commodities=inc_comm, include_crypto=inc_cryp, include_ihsg=inc_ihsg,
                                  portfolio_value=st.session_state.get("portfolio_value", 100_000))
            st.session_state.snap = snap; st.session_state.loading = False
            pb.empty(); pt.empty(); st.rerun()
        except Exception as e:
            st.session_state.loading = False; st.error(f"Build failed: {e}"); st.stop()

if not snap or not snap.get("ok"):
    st.error("Build failed. Click Rebuild to retry."); st.stop()

# Extract globals
gip = snap.get("gip")
prices = snap.get("prices", {})
rr = snap.get("risk_ranges", {})
ar = rr.get("asset_ranges", {}) if rr else {}
sq = gip.structural_quad if gip else "Q3"
mq_raw = gip.monthly_quad if gip else "Q2"
mq = st.session_state.mq_override if st.session_state.mq_override != "Auto" else mq_raw
vix_now = _safe_float(prices.get("^VIX", pd.Series()).tail(1)) if prices.get("^VIX") is not None else 20.0

# ═══════════════════════════════════════════════════════════════════
# SHARED COMPONENTS
# ═══════════════════════════════════════════════════════════════════
def render_regime_banner():
    gip_v10 = snap.get("gip_v10", {}) or {}
    sq = gip_v10.get("structural_quad", "Q3")
    mq = gip_v10.get("monthly_quad", sq)
    sc = gip_v10.get("structural_confidence", 0) or 0
    mc = gip_v10.get("monthly_confidence", 0) or 0
    c = _quad_color(sq)
    cm = _quad_color(mq)
    diverge = "<span style='color:#F85149; font-size:0.75rem; font-weight:600; margin-left:8px;'>DIVERGENCE</span>" if sq != mq else ""
    st.markdown(
        f"<div style='display:flex; gap:10px; align-items:center; margin-bottom:10px; flex-wrap:wrap;'>"
        f"<div style='background:{c}15; border-left:3px solid {c}; border-radius:6px; padding:8px 12px;'>"
        f"<div style='font-size:0.6rem; color:#8B949E; text-transform:uppercase; letter-spacing:0.8px;'>Quarterly</div>"
        f"<div style='font-size:1.1rem; font-weight:800; color:{c};'>{sq}</div>"
        f"<div style='font-size:0.7rem; color:#8B949E;'>{_quad_name(sq)} {sc:.0%}</div></div>"
        f"<div style='background:{cm}15; border-left:3px solid {cm}; border-radius:6px; padding:8px 12px;'>"
        f"<div style='font-size:0.6rem; color:#8B949E; text-transform:uppercase; letter-spacing:0.8px;'>Monthly</div>"
        f"<div style='font-size:1.1rem; font-weight:800; color:{cm};'>{mq}</div>"
        f"<div style='font-size:0.7rem; color:#8B949E;'>{_quad_name(mq)} {mc:.0%}</div></div>{diverge}</div>",
        unsafe_allow_html=True
    )

def render_ticker_compact(row, expanded=False):
    ticker = row.get("ticker", "?")
    px = row.get("price", 0)
    direction = row.get("direction", "NEUTRAL")
    grade = row.get("grade", "C")
    rr_val = row.get("rr", 0)
    entry = row.get("entry")
    t1 = row.get("target_1")
    t2 = row.get("target_2")
    stop = row.get("stop")
    trade_l = row.get("trade_l")
    trade_r = row.get("trade_r")
    tail_l = row.get("tail_l")
    tail_r = row.get("tail_r")
    news_sig = row.get("news_signal", "")

    dir_emoji = "L" if "LONG" in direction else "S" if "SHORT" in direction else "N"
    dir_color = "#3FB950" if "LONG" in direction else "#F85149" if "SHORT" in direction else "#8B949E"

    badges = []
    if grade in ("A", "A+"): badges.append("<span class='mr-pill pill-grad-a'>A</span>")
    elif grade == "B": badges.append("<span class='mr-pill pill-grad-b'>B</span>")
    else: badges.append("<span class='mr-pill pill-grad-c'>C</span>")
    if "LONG" in direction: badges.append("<span class='mr-pill pill-long'>LONG</span>")
    elif "SHORT" in direction: badges.append("<span class='mr-pill pill-short'>SHORT</span>")
    if rr_val and rr_val >= 2: badges.append(f"<span class='mr-pill pill-info'>RR {rr_val}x</span>")
    if news_sig and "BULLISH" in str(news_sig): badges.append("<span class='mr-pill pill-long'>NEWS+</span>")
    if news_sig and "BEARISH" in str(news_sig): badges.append("<span class='mr-pill pill-short'>NEWS-</span>")
    badge_html = " ".join(badges)

    header = f"{dir_emoji} {ticker} @ {ff(px)} | Entry {ff(entry)} | RR {ff(rr_val)}x"

    with st.expander(header, expanded=expanded):
        st.markdown(
            f"<div style='background:{dir_color}10; border:1px solid {dir_color}35; border-radius:8px; padding:10px 14px; margin:6px 0;'>"
            f"<div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;'>"
            f"<div style='font-size:1.05rem; font-weight:800; color:{dir_color};'>{direction}</div>"
            f"<div style='font-size:0.8rem; color:#8B949E;'>Grade {grade} | RR {ff(rr_val)}x</div></div>"
            f"<div style='font-size:0.8rem; color:#E6EDF3; margin-top:4px;'>{(row.get('recommendation') or row.get('thesis') or '—')[:120]}</div></div>",
            unsafe_allow_html=True
        )

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Price", ff(px)); m2.metric("Entry", ff(entry)); m3.metric("T1", ff(t1))
        m4.metric("T2", ff(t2)); m5.metric("Stop", ff(stop)); m6.metric("RR", f"{ff(rr_val)}x")

        if trade_l and trade_r and px:
            st.markdown("**Risk Range**")
            pos_trade = (px - trade_l) / max(trade_r - trade_l, 0.001)
            st.markdown(
                f"<div class='rr-track'>"
                f"<div class='rr-zone' style='left:0%; width:100%; background:#21262D;'></div>"
                f"<div class='rr-zone' style='left:0%; width:{max(0, min(100, pos_trade * 100)):.0f}%; background:{dir_color}25;'></div>"
                f"<div class='rr-dot' style='left:{max(2, min(98, pos_trade * 100)):.0f}%'></div></div>"
                f"<div style='display:flex; justify-content:space-between; font-size:0.65rem; color:#8B949E; margin-top:2px;'>"
                f"<span>{ff(trade_l)}</span><span>{ff(px)}</span><span>{ff(trade_r)}</span></div>",
                unsafe_allow_html=True
            )

        if row.get("gamma_regime") or row.get("max_pain"):
            o1, o2, o3, o4 = st.columns(4)
            o1.metric("Gamma", row.get("gamma_regime", "—"))
            o2.metric("Max Pain", ff(row.get("max_pain")))
            o3.metric("Put Wall", ff(row.get("put_wall")))
            o4.metric("Call Wall", ff(row.get("call_wall")))

        if row.get("news_headline"):
            st.markdown(f"<div class='news-ticker'>📰 {row.get('news_headline')[:100]}</div>", unsafe_allow_html=True)

def render_ticker_table(rows, max_rows=20):
    if not rows:
        st.info("No setups pass filter."); return
    df_data = []
    for r in rows[:max_rows]:
        df_data.append({
            "Ticker": r.get("ticker"), "Dir": "L" if "LONG" in r.get("direction", "") else "S",
            "Price": ff(r.get("price")), "Entry": ff(r.get("entry")), "T1": ff(r.get("target_1")),
            "Stop": ff(r.get("stop")), "RR": ff(r.get("rr")), "Grade": r.get("grade", "C"), "1M": fp(r.get("r1m")),
        })
    st.dataframe(pd.DataFrame(df_data), use_container_width=True, hide_index=True, height=min(400, len(df_data) * 35 + 50))
    st.caption(f"Showing {len(rows[:max_rows])} of {len(rows)} setups — expand for detail:")
    for i, r in enumerate(rows[:max_rows]):
        render_ticker_compact(r, expanded=(i < 2))

def build_ticker_rows(tickers, market_type="us_equity", vix_now=20, gamma_data=None, greeks_data=None, news=None):
    rows = []
    for t in tickers:
        if market_type == "ihsg":
            r = _build_ihsg_row(t, prices, ar)
        else:
            r = _build_row(t, prices, ar, vix_now=vix_now, gamma_data=gamma_data, greeks_data=greeks_data, market_type=market_type, news=news)
        if r: rows.append(r)
    return rows

def split_long_short(rows):
    longs = [r for r in rows if "LONG" in r.get("direction", "")]
    shorts = [r for r in rows if "SHORT" in r.get("direction", "")]
    return sorted(longs, key=lambda x: x.get("rr", 0), reverse=True), sorted(shorts, key=lambda x: x.get("rr", 0), reverse=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════
def page_dashboard():
    st.markdown("## 🏠 Dashboard")
    render_regime_banner()

    # ── TOP KPI ROW (4 cards) ──
    markov = snap.get("markov_v3", {}) or {}
    health = snap.get("health", {}) or {}
    narrative = snap.get("narrative", {}) or {}

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            _kpi_card("Regime", markov.get("current_regime", "—").replace("_", " "),
                     f"Conf: {markov.get('confidence', 0):.0%}", _quad_color(sq)),
            unsafe_allow_html=True
        )
    with k2:
        vix_color = "#3FB950" if vix_now < 18 else "#D29922" if vix_now < 25 else "#F85149"
        st.markdown(
            _kpi_card("VIX", f"{vix_now:.1f}", "Volatility gauge", vix_color),
            unsafe_allow_html=True
        )
    with k3:
        n_alerts = len((snap.get("yves_v2", {}) or {}).get("alerts", []))
        alert_color = "#F85149" if n_alerts > 2 else "#D29922" if n_alerts > 0 else "#3FB950"
        st.markdown(
            _kpi_card("Alerts", str(n_alerts), "Behavioral signals", alert_color),
            unsafe_allow_html=True
        )
    with k4:
        n_longs = len([r for r in (snap.get("daily_signals", []) or []) if "LONG" in str(r.get("direction", ""))])
        n_shorts = len([r for r in (snap.get("daily_signals", []) or []) if "SHORT" in str(r.get("direction", ""))])
        st.markdown(
            _kpi_card("Setups", f"{n_longs}L / {n_shorts}S", "Alpha signals", "#58A6FF"),
            unsafe_allow_html=True
        )

    st.divider()

    # ── MAIN CONTENT: 2 COLUMNS ──
    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("### 🎯 Top Alpha")
        alpha_items = (snap.get("alpha_center", {}) or {}).get("all", []) or []
        top_alpha = sorted(alpha_items, key=lambda x: x.get("priority_score", 0), reverse=True)[:8]
        if top_alpha:
            for item in top_alpha:
                dir_color = "#3FB950" if item.get("direction") == "LONG" else "#F85149" if item.get("direction") == "SHORT" else "#8B949E"
                grade = item.get("grade", "C")
                st.markdown(
                    f"<div style='display:flex; align-items:center; gap:8px; padding:6px 10px; background:#161B22; border:1px solid #30363D; "
                    f"border-radius:6px; margin:3px 0; font-size:0.82rem;'>"
                    f"<span style='font-weight:700; min-width:50px;'>{item.get('ticker', '—')}</span>"
                    f"<span style='color:{dir_color}; font-weight:600; min-width:50px;'>{item.get('direction', '—')}</span>"
                    f"<span style='background:{"#3FB95022" if grade=="A" else "#D2992222" if grade=="B" else "#8B949E22"}; "
                    f"color:{"#3FB950" if grade=="A" else "#D29922" if grade=="B" else "#8B949E"}; "
                    f"padding:1px 6px; border-radius:4px; font-size:0.7rem; font-weight:600; border:1px solid {"#3FB950" if grade=="A" else "#D29922" if grade=="B" else "#8B949E"};'>{grade}</span>"
                    f"<span style='color:#8B949E; flex:1; text-align:right;'>{item.get('thesis', '')[:60]}</span></div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No alpha signals generated yet.")

        # Playbook mini
        st.markdown("### 📋 Playbook")
        pb = snap.get("playbook", {}) or {}
        best = pb.get("best_assets", [])[:5]
        worst = pb.get("worst_assets", [])[:5]
        if best or worst:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div style='font-size:0.7rem; color:#3FB950; text-transform:uppercase; font-weight:600; margin-bottom:4px;'>Overweight</div>", unsafe_allow_html=True)
                for b in best:
                    st.markdown(f"<div style='font-size:0.8rem; color:#E6EDF3;'>• {b}</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div style='font-size:0.7rem; color:#F85149; text-transform:uppercase; font-weight:600; margin-bottom:4px;'>Underweight</div>", unsafe_allow_html=True)
                for w in worst:
                    st.markdown(f"<div style='font-size:0.8rem; color:#E6EDF3;'>• {w}</div>", unsafe_allow_html=True)

    with right:
        st.markdown("### 📰 Macro Pulse")

        # Market health
        health_score = health.get("composite_score", 50) if health else 50
        health_color = "#3FB950" if health_score >= 70 else "#D29922" if health_score >= 50 else "#F85149"
        st.markdown(
            f"<div style='background:#161B22; border:1px solid #30363D; border-radius:8px; padding:10px 12px; margin-bottom:8px;'>"
            f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
            f"<span style='font-size:0.7rem; color:#8B949E; text-transform:uppercase; font-weight:600;'>Market Health</span>"
            f"<span style='font-size:1.1rem; font-weight:700; color:{health_color};'>{health_score:.0f}</span></div></div>",
            unsafe_allow_html=True
        )

        # Narrative
        macro_nar = (narrative.get("macro_narrative") or {}) if narrative else {}
        if macro_nar.get("narrative"):
            st.markdown(f"<div style='font-size:0.8rem; color:#E6EDF3; line-height:1.5;'>📰 {macro_nar['narrative'][:200]}...</div>", unsafe_allow_html=True)

        # Scenarios
        scenarios = (narrative.get("scenarios") or {}) if narrative else {}
        if scenarios:
            dom = scenarios.get("dominant_scenario", "base")
            for scen_name in ["bull", "base", "bear"]:
                scen = scenarios.get(scen_name, {})
                p = scen.get("probability", 0)
                color = "#3FB950" if scen_name == "bull" else "#D29922" if scen_name == "base" else "#F85149"
                is_dom = " ★" if dom == scen_name else ""
                st.markdown(
                    f"<div style='display:flex; justify-content:space-between; align-items:center; padding:4px 0; border-bottom:1px solid #21262D;'>"
                    f"<span style='font-size:0.8rem; color:#E6EDF3;'>{scen_name.title()}{is_dom}</span>"
                    f"<span style='font-size:0.85rem; font-weight:700; color:{color};'>{p:.0%}</span></div>",
                    unsafe_allow_html=True
                )

        # Front-run
        rumor = snap.get("rumor_watch", []) or []
        if rumor:
            st.markdown("### 🔮 Front-Run")
            for r in rumor[:3]:
                sig = r.get("signal", "")
                color = "#3FB950" if "BULLISH" in sig else "#F85149" if "BEARISH" in sig else "#D29922"
                st.markdown(
                    f"<div style='display:flex; justify-content:space-between; align-items:center; padding:4px 0;'>"
                    f"<span style='font-size:0.8rem; color:#E6EDF3;'>{r.get('ticker', '—')}</span>"
                    f"<span style='font-size:0.75rem; color:{color}; font-weight:600;'>{sig[:20]}</span></div>",
                    unsafe_allow_html=True
                )

    st.divider()

    # ── BOTTOM: EXPANDER FOR DEEP TECHNICAL ──
    with st.expander("🔬 Deep Technical (Regime Chart, Engines, Methodologies)", expanded=False):
        # Regime probabilities chart
        if gip and hasattr(gip, 'structural_probs'):
            fig = make_subplots(rows=1, cols=3, subplot_titles=("Quarterly", "Monthly", "Forward 3M"),
                                column_widths=[0.33, 0.33, 0.34], horizontal_spacing=0.08)
            q_probs = gip.structural_probs if hasattr(gip, 'structural_probs') else {}
            for q, p in sorted(q_probs.items()):
                color = {"Q1":"#3FB950","Q2":"#D29922","Q3":"#F85149","Q4":"#A371F7"}.get(q, "#8B949E")
                fig.add_trace(go.Bar(x=[q], y=[p], marker_color=color, text=[f"<b>{p:.0%}</b>"], textposition="outside", showlegend=False), row=1, col=1)
            m_probs = gip.monthly_probs if hasattr(gip, 'monthly_probs') else {}
            for q, p in sorted(m_probs.items()):
                color = {"Q1":"#3FB950","Q2":"#D29922","Q3":"#F85149","Q4":"#A371F7"}.get(q, "#8B949E")
                fig.add_trace(go.Bar(x=[q], y=[p], marker_color=color, text=[f"<b>{p:.0%}</b>"], textposition="outside", showlegend=False), row=1, col=2)
            rf = snap.get("regime_forecast", {})
            if rf and rf.get("3m"):
                rf3 = rf["3m"]
                fq = rf3.get("predicted_quad", "Q3")
                fc = rf3.get("prediction_confidence", 0)
                fp = {q: (fc if q == fq else (1-fc)/3) for q in ["Q1","Q2","Q3","Q4"]}
                for q, p in sorted(fp.items()):
                    color = {"Q1":"#3FB950","Q2":"#D29922","Q3":"#F85149","Q4":"#A371F7"}.get(q, "#8B949E")
                    opacity = 1.0 if q == fq else 0.4
                    fig.add_trace(go.Bar(x=[q], y=[p], marker_color=color, text=[f"<b>{p:.0%}</b>"], textposition="outside", showlegend=False, opacity=opacity), row=1, col=3)
            fig.update_layout(height=200, margin=dict(t=30,b=20,l=20,r=20), paper_bgcolor="#161B22", plot_bgcolor="#161B22",
                              font=dict(color="#E6EDF3", size=10), yaxis=dict(range=[0,1.1], tickformat=".0%", showgrid=True, gridcolor="#21262D"),
                              yaxis2=dict(range=[0,1.1], tickformat=".0%", showgrid=True, gridcolor="#21262D"),
                              yaxis3=dict(range=[0,1.1], tickformat=".0%", showgrid=True, gridcolor="#21262D"), bargap=0.4)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="dash_regime")

        # Engine status
        st.markdown("**Engine Status**")
        engines = [
            ("GIP v10", snap.get("gip_v10") is not None),
            ("Markov V3", snap.get("markov_v3") is not None),
            ("Yves v2", snap.get("yves_v2") is not None),
            ("Cascade", snap.get("cascade_analysis") is not None),
            ("Discovery", snap.get("discovery_brain") is not None),
            ("VRP", snap.get("vrp_scanner") is not None),
            ("Squeeze", snap.get("squeeze_scanner") is not None),
            ("Smart Money", snap.get("smart_money") is not None),
        ]
        cols = st.columns(4)
        for i, (name, ok) in enumerate(engines):
            color = "#3FB950" if ok else "#F85149"
            cols[i % 4].markdown(f"<span style='color:{color}; font-size:0.8rem;'>● {name}</span>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE: ALPHA CENTER
# ═══════════════════════════════════════════════════════════════════
def page_alpha():
    st.markdown("## ⚡ Alpha Center")
    render_regime_banner()

    st.caption("Cross-market best ideas | Composite signal + Thesis + Smart Money | High bar: ≥70/100")

    # ── TOP SUMMARY ──
    summary = snap.get("summary", {}) or {}
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Markov Regime", str(summary.get("v7_markov_regime", "—")).split("_")[0] if summary.get("v7_markov_regime") else "—")
    k2.metric("Smart $ Consensus", summary.get("v7_smart_money_consensus", 0))
    k3.metric("Top Theses", summary.get("v7_top_theses_count", 0))
    k4.metric("Kelly", f"{summary.get('v7_markov_kelly', 0.25):.0%}")

    st.divider()

    # ── SUB-TABS: 3 only (merged from 6) ──
    tab1, tab2, tab3 = st.tabs(["🏆 Top Picks", "📊 Vol & Squeeze", "🔮 Discovery"])

    with tab1:
        # Top alpha candidates
        alpha_candidates = []
        for ticker, sig in (snap.get("composite_signals", {}) or {}).items():
            if not sig or sig.get("direction") in ("NEUTRAL", "AVOID"): continue
            if sig.get("confidence", 0) < 0.4: continue
            thesis = (snap.get("thought_process", {}) or {}).get(ticker, {})
            if thesis.get("thesis_score", 0) < 60: continue
            rr = (snap.get("risk_ranges", {}) or {}).get("asset_ranges", {}).get(ticker, {})
            if rr.get("quality") not in ("A+", "A"): continue
            sm = (snap.get("smart_money", {}) or {}).get("per_ticker", {}).get(ticker, {})
            sm_boost = 15 if sm.get("smart_money_held") else 0
            alpha_candidates.append({
                "ticker": ticker, "direction": sig.get("direction"),
                "confidence": sig.get("confidence", 0), "thesis_score": thesis.get("thesis_score", 0),
                "primary_role": thesis.get("primary_role", "—"),
                "alpha_score": sig.get("confidence", 0) * 35 + thesis.get("thesis_score", 0) * 0.3 + {"A+": 20, "A": 15}.get(rr.get("quality"), 0) + sm_boost,
            })
        alpha_candidates.sort(key=lambda x: x["alpha_score"], reverse=True)
        top_alpha = [c for c in alpha_candidates if c["alpha_score"] >= 70][:20]

        if not top_alpha:
            st.info("No cross-market candidates meet Alpha Center high bar (≥70/100). Lower thresholds in market-specific tabs.")
        else:
            st.markdown(f"**{len(top_alpha)} candidates** from {len(alpha_candidates)} total")
            for i, c in enumerate(top_alpha):
                dir_color = "#3FB950" if c["direction"] == "LONG" else "#F85149"
                sm_badge = " 💼" if c.get("smart_money") else ""
                with st.expander(f"#{i+1} {c['ticker']} · Score {c['alpha_score']:.0f}/100 · {c['direction']}{sm_badge}", expanded=(i < 3)):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Confidence", f"{c['confidence']:.0%}")
                    c2.metric("Thesis", f"{c['thesis_score']:.0f}/100")
                    c3.metric("Role", c["primary_role"])

    with tab2:
        # VRP + Squeeze merged
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 VRP Scanner")
            vrp = snap.get("vrp_scanner", {}) or {}
            if vrp.get("ok"):
                st.metric("Sell Premium", len(vrp.get("high_vrp_sell_premium", [])))
                st.metric("Buy Premium", len(vrp.get("low_vrp_buy_premium", [])))
                for item in vrp.get("high_vrp_sell_premium", [])[:5]:
                    st.markdown(f"• **{item.get('ticker')}** · VRP +{item.get('vrp_pct', 0):.0f}% · IV Rank {item.get('iv_rank', '—')}")
            else:
                st.info("VRP scanner unavailable")

        with col2:
            st.markdown("### 🔥 Squeeze Scanner")
            sq = snap.get("squeeze_scanner", {}) or {}
            if sq.get("ok"):
                st.metric("Imminent", len(sq.get("imminent_squeezes", [])))
                st.metric("Strong", len(sq.get("strong_candidates", [])))
                for item in sq.get("imminent_squeezes", [])[:5]:
                    st.markdown(f"• **{item.get('ticker')}** · Score {item.get('squeeze_score', 0):.0f}/100 · {item.get('tier', '—')}")
            else:
                st.info("Squeeze scanner unavailable")

    with tab3:
        st.markdown("### 🔮 Discovery Brain")
        disc = snap.get("discovery_brain", {}) or {}
        if disc.get("by_mode"):
            for mode in ("adaptive", "reactive", "proactive"):
                items = disc.get("by_mode", {}).get(mode, [])
                if items:
                    st.markdown(f"**{mode.title()}** ({len(items)})")
                    for item in items[:5]:
                        with st.expander(f"{item.get('name', '—').replace('_', ' ')} · conf {item.get('confidence', 0):.0%}"):
                            st.markdown(item.get("thesis", "—"))
        else:
            st.info("Discovery Brain — no candidates this snapshot")

        # Position sizing
        st.markdown("### 💰 Position Sizing")
        sizing = snap.get("portfolio_sizing_v2", {}) or {}
        if sizing.get("positions"):
            st.metric("Deployed", f"{sizing.get('total_deployed_pct', 0):.1%}")
            st.metric("Cash", f"{sizing.get('cash_pct', 0):.1%}")
            df = pd.DataFrame([{
                "Ticker": p.get("ticker"), "Size %": f"{p.get('target_pct', 0):.2%}",
                "Size $": f"{p.get('target_dollar', 0):,.0f}", "Mode": p.get("mode"), "Sector": p.get("sector"),
            } for p in sizing.get("positions", [])])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No sized positions yet.")


# ═══════════════════════════════════════════════════════════════════
# PAGE: US STOCKS
# ═══════════════════════════════════════════════════════════════════
def page_us_stocks():
    st.markdown("## 🇺🇸 US Stocks")
    render_regime_banner()

    # Playbook
    playbook = {
        "Q1": {"beli": ["QQQ", "XLK", "NVDA", "AAPL", "MSFT", "GOOGL", "META", "AMD", "ARKK"], "short": ["XLU", "XLP", "TLT", "GLD"]},
        "Q2": {"beli": ["XLF", "XLE", "XLI", "XLB", "KRE", "IWM", "XOM", "CVX"], "short": ["TLT", "IEF"]},
        "Q3": {"beli": ["XLE", "XLP", "XLU", "ITA", "GLD", "SLV", "VST", "CEG", "BE", "LITE", "CCJ"], "short": ["QQQ", "XLK", "IWM", "ARKK", "KRE"]},
        "Q4": {"beli": ["TLT", "IEF", "GLD", "XLU", "XLP", "XLV"], "short": ["QQQ", "XLK", "IWM", "XLY", "XLF", "XLE"]},
    }
    pb = playbook.get(sq, playbook["Q3"])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div style='font-size:0.7rem; color:#3FB950; text-transform:uppercase; font-weight:600; margin-bottom:4px;'>Overweight</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.82rem; line-height:1.6;'>" + " · ".join(pb["beli"][:10]) + "</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='font-size:0.7rem; color:#F85149; text-transform:uppercase; font-weight:600; margin-bottom:4px;'>Underweight</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.82rem; line-height:1.6;'>" + " · ".join(pb["short"][:8]) + "</div>", unsafe_allow_html=True)

    st.divider()

    # Tickers
    us_tickers = list(US_SECTORS.keys())
    for bucket in ["Growth", "Quality", "Defensives", "Semis", "Energy", "Industrials", "Financials", "AI_Infra", "PreciousMetals"]:
        us_tickers += US_BUCKETS.get(bucket, [])
    us_tickers = list(dict.fromkeys(us_tickers))

    rows = build_ticker_rows(us_tickers, "us_equity", vix_now, snap.get("gamma_data"), snap.get("greeks_data"), snap.get("news_narratives"))
    longs, shorts = split_long_short(rows)

    st.markdown(f"**{len(rows)} setups** · 🟢 {len(longs)} Long · 🔴 {len(shorts)} Short")

    tab_l, tab_s = st.tabs([f"🟢 Long ({len(longs)})", f"🔴 Short ({len(shorts)})"])
    with tab_l:
        render_ticker_table(longs)
    with tab_s:
        render_ticker_table(shorts)

# ═══════════════════════════════════════════════════════════════════
# PAGE: FOREX
# ═══════════════════════════════════════════════════════════════════
def page_forex():
    st.markdown("## 💱 Forex")
    render_regime_banner()

    playbook = {
        "Q1": {"beli": ["EURUSD", "AUDUSD", "EM FX"], "short": ["DXY/UUP"]},
        "Q2": {"beli": ["GBPUSD", "CADUSD"], "short": ["JPY"]},
        "Q3": {"beli": ["UUP", "CHF"], "short": ["EURUSD", "GBPUSD", "EM FX"]},
        "Q4": {"beli": ["JPY", "CHF"], "short": ["AUDUSD", "EM FX"]},
    }
    pb = playbook.get(sq, playbook["Q3"])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div style='font-size:0.7rem; color:#3FB950; text-transform:uppercase; font-weight:600; margin-bottom:4px;'>Buy</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.82rem; line-height:1.6;'>" + " · ".join(pb["beli"]) + "</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='font-size:0.7rem; color:#F85149; text-transform:uppercase; font-weight:600; margin-bottom:4px;'>Short</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.82rem; line-height:1.6;'>" + " · ".join(pb["short"]) + "</div>", unsafe_allow_html=True)

    st.divider()

    rows = build_ticker_rows(list(FOREX_PAIRS.keys()), "forex", vix_now, snap.get("gamma_data"), snap.get("greeks_data"), snap.get("news_narratives"))
    longs, shorts = split_long_short(rows)

    st.markdown(f"**{len(rows)} pairs** · 🟢 {len(longs)} Long · 🔴 {len(shorts)} Short")

    tab_l, tab_s = st.tabs([f"🟢 Long ({len(longs)})", f"🔴 Short ({len(shorts)})"])
    with tab_l:
        render_ticker_table(longs)
    with tab_s:
        render_ticker_table(shorts)

# ═══════════════════════════════════════════════════════════════════
# PAGE: COMMODITIES
# ═══════════════════════════════════════════════════════════════════
def page_commodities():
    st.markdown("## 🛢️ Commodities")
    render_regime_banner()

    playbook = {
        "Q1": {"beli": ["Copper", "Industrial Metals"], "short": ["Gold (counter-trend)"]},
        "Q2": {"beli": ["CL=F", "USO", "XLE", "Energy"], "short": []},
        "Q3": {"beli": ["GLD", "SLV", "CL=F", "CCJ", "URA"], "short": []},
        "Q4": {"beli": ["GLD", "TLT"], "short": ["CL=F", "Industrial metals"]},
    }
    pb = playbook.get(sq, playbook["Q3"])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div style='font-size:0.7rem; color:#3FB950; text-transform:uppercase; font-weight:600; margin-bottom:4px;'>Buy</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.82rem; line-height:1.6;'>" + " · ".join(pb["beli"]) + "</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='font-size:0.7rem; color:#F85149; text-transform:uppercase; font-weight:600; margin-bottom:4px;'>Short</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.82rem; line-height:1.6;'>" + (" · ".join(pb["short"]) if pb["short"] else "—") + "</div>", unsafe_allow_html=True)

    st.divider()

    rows = build_ticker_rows(list(COMMODITIES.keys()), "commodity", vix_now, snap.get("gamma_data"), snap.get("greeks_data"), snap.get("news_narratives"))
    longs, shorts = split_long_short(rows)

    st.markdown(f"**{len(rows)} commodities** · 🟢 {len(longs)} Long · 🔴 {len(shorts)} Short")

    tab_l, tab_s = st.tabs([f"🟢 Long ({len(longs)})", f"🔴 Short ({len(shorts)})"])
    with tab_l:
        render_ticker_table(longs)
    with tab_s:
        render_ticker_table(shorts)


# ═══════════════════════════════════════════════════════════════════
# PAGE: CRYPTO
# ═══════════════════════════════════════════════════════════════════
def page_crypto():
    st.markdown("## ₿ Crypto")
    render_regime_banner()

    playbook = {
        "Q1": {"beli": ["BTC", "ETH", "SOL", "alts"], "short": []},
        "Q2": {"beli": ["BTC", "MSTR", "CORZ", "IREN"], "short": []},
        "Q3": {"beli": ["BTC", "MSTR", "IBIT"], "short": ["alts (ETH/SOL relative)"]},
        "Q4": {"beli": ["BTC (hedge ONLY)"], "short": ["alts", "ETH", "memecoin"]},
    }
    pb = playbook.get(sq, playbook["Q3"])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div style='font-size:0.7rem; color:#3FB950; text-transform:uppercase; font-weight:600; margin-bottom:4px;'>Buy</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.82rem; line-height:1.6;'>" + " · ".join(pb["beli"]) + "</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='font-size:0.7rem; color:#F85149; text-transform:uppercase; font-weight:600; margin-bottom:4px;'>Short</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.82rem; line-height:1.6;'>" + (" · ".join(pb["short"]) if pb["short"] else "—") + "</div>", unsafe_allow_html=True)

    st.divider()

    rows = build_ticker_rows(list(CRYPTO.keys()), "crypto", vix_now, snap.get("gamma_data"), snap.get("greeks_data"), snap.get("news_narratives"))
    longs, shorts = split_long_short(rows)

    st.markdown(f"**{len(rows)} coins** · 🟢 {len(longs)} Long · 🔴 {len(shorts)} Short")

    tab_l, tab_s = st.tabs([f"🟢 Long ({len(longs)})", f"🔴 Short ({len(shorts)})"])
    with tab_l:
        render_ticker_table(longs)
    with tab_s:
        render_ticker_table(shorts)

# ═══════════════════════════════════════════════════════════════════
# PAGE: GLOBAL & EM
# ═══════════════════════════════════════════════════════════════════
def page_global():
    st.markdown("## 🌍 Global & EM")
    render_regime_banner()

    global_ = snap.get("global", {}) or {}
    country_list = global_.get("country_list", [])

    if not country_list:
        base_map = {
            "Q1": ["USA", "Japan", "India", "Taiwan", "South Korea", "Vietnam", "Mexico", "Singapore", "Philippines", "Malaysia"],
            "Q2": ["China", "Brazil", "Australia", "Canada", "South Africa", "Saudi Arabia", "Chile", "Peru", "Indonesia", "Thailand"],
            "Q3": ["UK", "Germany", "France", "Italy", "Russia", "Turkey", "Argentina", "Nigeria", "Pakistan", "Egypt"],
            "Q4": ["Venezuela", "Iran", "Ukraine", "Greece", "Portugal", "Lebanon", "Syria", "Yemen", "Zimbabwe", "Sudan"],
        }
        country_list = []
        for q, countries in base_map.items():
            for c in countries:
                country_list.append({"country": c, "quad": q, "regime_name": _quad_name(q)})

    # Heatmap grid
    st.markdown("### 🗺️ Country Regime Map")

    quad_groups = {"Q1": [], "Q2": [], "Q3": [], "Q4": []}
    for item in country_list:
        q = item.get("quad", "Q3")
        if q in quad_groups: quad_groups[q].append(item)

    cols = st.columns(4)
    for i, q in enumerate(["Q1", "Q2", "Q3", "Q4"]):
        with cols[i]:
            color = _quad_color(q)
            st.markdown(
                f"<div style='background:{color}15; border:1px solid {color}40; border-radius:8px; padding:10px;'>"
                f"<div style='font-size:0.9rem; font-weight:700; color:{color}; margin-bottom:6px;'>{q} · {_quad_name(q)}</div>"
                f"<div style='font-size:0.75rem; color:#E6EDF3; line-height:1.5;'>" +
                "<br>".join([f"• {c['country']}" for c in quad_groups[q][:12]]) +
                (f"<br><span style='color:#8B949E;'>+{len(quad_groups[q]) - 12} more</span>" if len(quad_groups[q]) > 12 else "") +
                f"</div></div>",
                unsafe_allow_html=True
            )

    st.divider()

    # IHSG Report
    st.markdown("### 🇮🇩 IHSG Report")
    ihsg_rows = build_ticker_rows(list(IHSG_UNIVERSE.keys()), "ihsg", vix_now)

    # Group by sector
    by_sector = {}
    for r in ihsg_rows:
        sect = IHSG_SECTOR_MAP.get(r.get("ticker"), "Other")
        by_sector.setdefault(sect, []).append(r)

    st.markdown(f"**{len(ihsg_rows)} stocks** · Sectors: {', '.join(by_sector.keys())}")

    for sector, items in by_sector.items():
        with st.expander(f"**{sector}** ({len(items)} stocks)", expanded=False):
            render_ticker_table(items, max_rows=10)

# ═══════════════════════════════════════════════════════════════════
# PAGE: THEMES
# ═══════════════════════════════════════════════════════════════════
def page_themes():
    st.markdown("## 📖 Themes & Playbook")
    render_regime_banner()

    # Portfolio allocation
    allocation = {
        "Q1": {"long": 75, "short": 5, "cash": 20, "style": "Tech 30% | Growth 20% | Crypto 15% | EM 5% | Defensives 5%"},
        "Q2": {"long": 70, "short": 10, "cash": 20, "style": "Cyclicals 25% | Financials 15% | Energy 15% | Materials 10% | Small Caps 5%"},
        "Q3": {"long": 60, "short": 15, "cash": 25, "style": "Energy/Infra 20% | Real Assets 15% | Crypto 10% | EM/LatAm 8% | IHSG Energy 7%"},
        "Q4": {"long": 50, "short": 20, "cash": 30, "style": "TLT 15% | Gold 10% | Utilities 10% | Staples 10% | Healthcare 5%"},
    }
    alloc = allocation.get(sq, allocation["Q3"])

    st.markdown("### 💼 Portfolio Allocation")
    c1, c2, c3 = st.columns(3)
    c1.metric("📈 Long", f"{alloc['long']}%", "risk-on" if sq in ("Q1", "Q2") else "defensive")
    c2.metric("📉 Short", f"{alloc['short']}%", "tactical hedges")
    c3.metric("💵 Cash", f"{alloc['cash']}%", "dry powder")

    st.markdown(f"<div style='font-size:0.8rem; color:#8B949E; margin-top:8px;'>**Style:** {alloc['style']}</div>", unsafe_allow_html=True)

    st.divider()

    # Bottleneck themes
    st.markdown("### 🚧 Active Bottlenecks")
    bottlenecks = (snap.get("narrative", {}) or {}).get("active_bottlenecks", []) or []
    if bottlenecks:
        for b in bottlenecks[:5]:
            beneficiaries = ", ".join(b.get("beneficiaries", [])[:5])
            st.markdown(
                f"<div style='background:#161B22; border-left:3px solid #F85149; border-radius:6px; padding:8px 12px; margin:4px 0;'>"
                f"<div style='font-size:0.85rem; font-weight:700; color:#E6EDF3;'>{b['name'].replace('_', ' ').title()}</div>"
                f"<div style='font-size:0.75rem; color:#8B949E; margin-top:4px;'>Beneficiaries: {beneficiaries}</div></div>",
                unsafe_allow_html=True
            )
    else:
        st.info("No active bottlenecks detected.")

    st.divider()

    # Methodology summary
    st.markdown("### 🧠 Methodology Lens")

    methodologies = [
        ("🏗️ Leopold", "Bottleneck layers + asymmetry setups", snap.get("leopold_scan")),
        ("💱 COATUE", "Shortage economy + capital rotation", snap.get("coatue_scan")),
        ("📊 Karsan", "Vol surface + squeeze setups", snap.get("karsan_scanner")),
        ("🧠 Yves", "Behavioral relabeling", snap.get("yves_v2")),
        ("🌀 Soros", "Boom-bust reflexivity", snap.get("boom_bust")),
        ("⚡ Vol Decomp", "Black-Scholes IV breakdown", None),
        ("💧 Druckenmiller", "Liquidity-first positioning", None),
    ]

    for name, desc, data in methodologies:
        status = "🟢" if data else "⚪"
        with st.expander(f"{status} {name} — {desc}", expanded=False):
            if data:
                st.json({k: str(v)[:100] for k, v in list(data.items())[:3]})
            else:
                st.caption("Data not loaded this snapshot.")

# ═══════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ═══════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    page_dashboard()
elif page == "⚡ Alpha Center":
    page_alpha()
elif page == "🇺🇸 US Stocks":
    page_us_stocks()
elif page == "💱 Forex":
    page_forex()
elif page == "🛢️ Commodities":
    page_commodities()
elif page == "₿ Crypto":
    page_crypto()
elif page == "🌍 Global & EM":
    page_global()
elif page == "📖 Themes":
    page_themes()

# Footer
st.divider()
flip_note = f" · {snap.get('summary', {}).get('v2_composite_flipped_count', 0)} flipped" if snap.get("summary", {}).get("v2_composite_flipped_count") else ""
st.caption(f"MacroRegime Pro v28.0 · Built {snap.get('build_time_s', 0):.0f}s ago · {snap.get('prices_loaded', 0)} assets · {snap.get('fred_coverage', 0)} indicators{flip_note}")
