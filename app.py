"""app.py - MacroRegime Pro v30.3 VISUAL
Visual-first rewrite with full audit fixes:
- vix_now: type-safe extraction (handles list/array/Series/None)
- gip: proxy wrapper for dict/object duality
- All getattr() guards for gip attributes
- Ticker fallback lists for all markets
- Threshold lowered to 15 days
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import json, os
from datetime import datetime

logger = __import__("logging").getLogger(__name__)

st.set_page_config(page_title="MacroRegime Pro v30", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════════════
# DESIGN SYSTEM CSS
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap");
html, body, [class*="css"] { font-family: "Inter", sans-serif; }
.block-container { padding-top: 0.6rem !important; padding-bottom: 0.6rem !important; padding-left: 1rem !important; padding-right: 1rem !important; max-width: 1440px !important; }
h1 { font-size: 1.5rem !important; margin: 0.3rem 0 0.4rem !important; font-weight: 800 !important; letter-spacing: -0.5px; }
h2 { font-size: 1.15rem !important; margin: 0.5rem 0 0.3rem !important; font-weight: 700 !important; letter-spacing: -0.3px; }
h3 { font-size: 0.95rem !important; margin: 0.4rem 0 0.2rem !important; font-weight: 600 !important; }
hr { margin: 0.5rem 0 !important; opacity: 0.1; border-color: #30363D; }
[data-testid="stMetric"] { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; padding: 6px 10px !important; }
[data-testid="stMetricLabel"] { font-size: 0.62rem !important; font-weight: 600 !important; letter-spacing: 0.6px; text-transform: uppercase; opacity: 0.6; }
[data-testid="stMetricValue"] { font-size: 1.1rem !important; font-weight: 700 !important; }
.ticker-card { display: flex; align-items: center; gap: 10px; padding: 8px 10px; background: #161B22; border: 1px solid #30363D; border-radius: 8px; margin: 4px 0; transition: border-color 0.2s; flex-wrap: wrap; }
.ticker-card:hover { border-color: #484F58; }
.tc-left { min-width: 90px; }
.tc-symbol { font-weight: 800; font-size: 0.95rem; color: #E6EDF3; letter-spacing: -0.3px; }
.tc-price { font-weight: 600; font-size: 0.8rem; color: #8B949E; font-variant-numeric: tabular-nums; }
.tc-badges { display: flex; gap: 3px; flex-wrap: wrap; margin-top: 3px; }
.tc-spark { width: 90px; height: 28px; display: flex; align-items: flex-end; gap: 1px; flex-shrink: 0; }
.tc-rr { flex: 1; min-width: 140px; }
.tc-metrics { display: flex; gap: 10px; font-size: 0.72rem; color: #8B949E; font-variant-numeric: tabular-nums; min-width: 140px; }
.sp-bar { width: 3px; border-radius: 1px; background: #58A6FF; opacity: 0.85; }
.sp-bar.up { background: #3FB950; }
.sp-bar.down { background: #F85149; }
.rr-track { position: relative; height: 18px; background: #21262D; border-radius: 4px; overflow: hidden; }
.rr-zone { position: absolute; top: 2px; bottom: 2px; border-radius: 2px; }
.rr-dot { position: absolute; top: 50%; transform: translate(-50%, -50%); width: 8px; height: 8px; border-radius: 50%; background: #E6EDF3; border: 2px solid #58A6FF; z-index: 10; box-shadow: 0 0 4px rgba(88,166,255,0.5); }
.rr-labels { display: flex; justify-content: space-between; font-size: 0.6rem; color: #8B949E; margin-top: 2px; font-variant-numeric: tabular-nums; }
.badge { display: inline-flex; align-items: center; padding: 1px 6px; border-radius: 10px; font-size: 0.62rem; font-weight: 700; letter-spacing: 0.3px; border: 1px solid transparent; line-height: 1.3; }
.badge-long { background: rgba(34,197,94,0.15); color: #3FB950; border-color: rgba(34,197,94,0.35); }
.badge-short { background: rgba(239,68,68,0.15); color: #F85149; border-color: rgba(239,68,68,0.35); }
.badge-neut { background: rgba(234,179,8,0.15); color: #eab308; border-color: rgba(234,179,8,0.35); }
.badge-grade-a { background: rgba(34,197,94,0.18); color: #3FB950; border-color: #3FB950; }
.badge-grade-b { background: rgba(234,179,8,0.18); color: #D29922; border-color: #D29922; }
.badge-grade-c { background: rgba(139,148,158,0.18); color: #8B949E; border-color: #8B949E; }
.badge-news { background: rgba(88,166,255,0.15); color: #58A6FF; border-color: rgba(88,166,255,0.35); }
.gauge-track { position: relative; height: 14px; background: #21262D; border-radius: 7px; overflow: hidden; margin: 4px 0; }
.gauge-fill { position: absolute; top: 0; bottom: 0; left: 0; border-radius: 7px; transition: width 0.5s ease; }
.gauge-label { display: flex; justify-content: space-between; font-size: 0.65rem; color: #8B949E; margin-top: 1px; }
.hm-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; }
.hm-cell { padding: 6px 4px; border-radius: 4px; text-align: center; font-size: 0.7rem; font-weight: 600; color: #E6EDF3; border: 1px solid rgba(255,255,255,0.05); }
.pulse-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
.pulse-box { aspect-ratio: 1; border-radius: 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 700; color: #E6EDF3; border: 1px solid rgba(255,255,255,0.06); }
.pulse-label { font-size: 0.55rem; font-weight: 500; color: rgba(255,255,255,0.5); text-transform: uppercase; margin-top: 2px; }
.timeline { display: flex; align-items: center; gap: 0px; margin: 8px 0; }
.tl-node { width: 14px; height: 14px; border-radius: 50%; border: 2px solid #30363D; background: #21262D; flex-shrink: 0; }
.tl-node.active { border-color: #58A6FF; background: #58A6FF; box-shadow: 0 0 6px rgba(88,166,255,0.4); }
.tl-node.past { border-color: #3FB950; background: #3FB950; }
.tl-line { flex: 1; height: 2px; background: #30363D; min-width: 20px; }
.tl-line.active { background: #58A6FF; }
.tl-labels { display: flex; justify-content: space-between; font-size: 0.6rem; color: #8B949E; margin-top: 4px; }
.stack-bar { display: flex; height: 22px; border-radius: 4px; overflow: hidden; background: #21262D; }
.stack-seg { display: flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 700; color: #fff; }
.skew-row { display: flex; align-items: center; gap: 8px; margin: 4px 0; }
.skew-label { width: 36px; font-size: 0.7rem; color: #8B949E; font-weight: 600; }
.skew-track { flex: 1; height: 16px; background: #21262D; border-radius: 4px; position: relative; overflow: hidden; }
.skew-fill { height: 100%; border-radius: 4px; transition: width 0.4s ease; }
.skew-value { width: 40px; font-size: 0.7rem; color: #E6EDF3; font-weight: 700; text-align: right; font-variant-numeric: tabular-nums; }
.gex-track { position: relative; height: 20px; background: #21262D; border-radius: 4px; overflow: hidden; display: flex; align-items: center; }
.gex-center { position: absolute; left: 50%; top: 0; bottom: 0; width: 1px; background: #8B949E; opacity: 0.3; }
.stTabs [data-baseweb="tab-list"] { gap: 2px !important; margin-bottom: 6px !important; }
.stTabs [data-baseweb="tab"] { padding: 5px 12px !important; font-size: 0.8rem !important; font-weight: 600 !important; border-radius: 6px 6px 0 0 !important; }
[data-testid="stExpander"] { border: 1px solid #30363D !important; border-radius: 8px !important; margin-bottom: 6px !important; }
[data-testid="stExpander"] > details > summary { padding: 8px 12px !important; font-size: 0.82rem !important; font-weight: 600 !important; }
[data-testid="stSidebar"] .block-container { padding-top: 0.8rem !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# CONFIG & FALLBACKS
# ═══════════════════════════════════════════════════════════════════
try:
    from config.settings import (FOREX_PAIRS, COMMODITIES, CRYPTO, IHSG_UNIVERSE,
                                 IHSG_SECTOR_MAP, TICKER_SECTOR, US_SECTORS, US_BUCKETS,
                                 FX_BUCKETS, COMMODITY_BUCKETS, CRYPTO_BUCKETS)
except ImportError:
    FOREX_PAIRS = {}; COMMODITIES = {}; CRYPTO = {}; IHSG_UNIVERSE = {}; TICKER_SECTOR = {}; US_SECTORS = {}; US_BUCKETS = {}; FX_BUCKETS = {}; COMMODITY_BUCKETS = {}; CRYPTO_BUCKETS = {}

FALLBACK_US = ["SPY","QQQ","IWM","NVDA","AAPL","MSFT","GOOGL","META","TSLA","AMD","NFLX","AMZN","CRM","AVGO","XOM","JPM","V","MA","UNH","JNJ","XLK","XLF","XLE","XLU","XLP","XLI","XLB","XLRE","XLY","ARKK","TLT","GLD","SLV","GDX","VIXY","SQQQ","TQQQ","UPRO","SPXU"]
FALLBACK_FX  = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","USDCAD=X","USDCHF=X","NZDUSD=X","USDCNY=X","USDIDR=X","DX-Y.NYB","UUP"]
FALLBACK_COMM = ["GC=F","SI=F","CL=F","NG=F","HG=F","PL=F","PA=F","ZW=F","ZC=F","ZS=F","KC=F","CC=F","CT=F"]
FALLBACK_CRYPTO = ["BTC-USD","ETH-USD","SOL-USD","XRP-USD","DOGE-USD","ADA-USD","AVAX-USD","DOT-USD","MATIC-USD","LINK-USD","UNI-USD","LTC-USD"]
FALLBACK_IHSG = ["BBRI.JK","BMRI.JK","BBCA.JK","BBNI.JK","BRIS.JK","TLKM.JK","EXCL.JK","ADRO.JK","ITMG.JK","PTBA.JK","NCKL.JK","ANTM.JK","INCO.JK","AALI.JK","LSIP.JK","SMAR.JK","UNTR.JK","BYAN.JK","ICBP.JK","INDF.JK","KLBF.JK","PGEO.JK","WINS.JK","EIDO","^JKSE"]

_IHSG_FALLBACK = {"ADRO.JK":"Coal","ITMG.JK":"Coal","PTBA.JK":"Coal","NCKL.JK":"Nickel","ANTM.JK":"Nickel","INCO.JK":"Nickel","AALI.JK":"CPO","LSIP.JK":"CPO","SMAR.JK":"CPO","BBRI.JK":"Banking","BMRI.JK":"Banking","BBCA.JK":"Banking","BBNI.JK":"Banking","BRIS.JK":"Banking","TLKM.JK":"Telco","EXCL.JK":"Telco","UNTR.JK":"Mining Contractor","BYAN.JK":"Mining","ICBP.JK":"Consumer","INDF.JK":"Consumer","KLBF.JK":"Pharma","PGEO.JK":"Geothermal","WINS.JK":"Shipping","EIDO":"ETF","^JKSE":"Index"}
if not locals().get("IHSG_SECTOR_MAP"):
    IHSG_SECTOR_MAP = _IHSG_FALLBACK

# GIP proxy - handles both object and dict gip
class _GipProxy:
    def __init__(self, data):
        self._is_dict = isinstance(data, dict)
        if self._is_dict:
            self._d = data
        else:
            self._obj = data
    def __getattr__(self, name):
        if self._is_dict:
            return self._d.get(name)
        return getattr(self._obj, name, None)

# ═══════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════
def _safe_float(v):
    if v is None: return None
    try:
        if isinstance(v, pd.Series): v = v.iloc[0] if len(v) > 0 else None
        if v is None: return None
        f = float(v)
        return f if math.isfinite(f) else None
    except: return None

def fp(v):
    try: return f"{float(v):.1%}" if v is not None and math.isfinite(float(v)) else "-"
    except: return "-"

def ff(v, d=2):
    try: return f"{float(v):,.{d}f}" if v is not None and math.isfinite(float(v)) else "-"
    except: return "-"

def _price_ret(ticker, prices, days=21):
    s = prices.get(ticker)
    if s is None: return None
    try:
        s = pd.to_numeric(pd.Series(s), errors="coerce").dropna()
    except:
        return None
    if len(s) < days + 1: return None
    try: return float(s.iloc[-1] / s.iloc[-(days+1)] - 1)
    except: return None

def _quad_color(q):
    return {"Q1":"#3FB950","Q2":"#D29922","Q3":"#F85149","Q4":"#A371F7"}.get(q, "#8B949E")

def _quad_name(q):
    return {"Q1":"Goldilocks","Q2":"Reflation","Q3":"Stagflation","Q4":"Deflation"}.get(q, q)

def _ret_color(r):
    if r is None: return "#8B949E"
    r = float(r)
    if r > 0.03: return "#3FB950"
    if r > 0: return "#2EA043"
    if r > -0.03: return "#F85149"
    return "#DA3633"

def _sparkline_html(series, width=90, height=28, bars=20):
    if series is None:
        return f'<div style="width:{width}px;height:{height}px;background:#21262D;border-radius:4px;"></div>'
    try:
        s = pd.to_numeric(pd.Series(series), errors="coerce").dropna().tail(bars)
    except:
        return f'<div style="width:{width}px;height:{height}px;background:#21262D;border-radius:4px;"></div>'
    if len(s) < 2:
        return f'<div style="width:{width}px;height:{height}px;background:#21262D;border-radius:4px;"></div>'
    mn, mx = float(s.min()), float(s.max())
    rng = mx - mn if mx != mn else 1
    bars_html = ""
    for i, v in enumerate(s):
        pct = max(2, min(100, int((float(v) - mn) / rng * 100)))
        color = "#3FB950" if (i > 0 and float(v) >= float(s.iloc[i-1])) else "#F85149"
        bars_html += f'<div class="sp-bar" style="height:{pct}%;background:{color};"></div>'
    return f'<div class="tc-spark" style="width:{width}px;height:{height}px;">{bars_html}</div>'

def _risk_range_html(px, lrr, trr, width_pct=100):
    if not all(v is not None and math.isfinite(float(v)) for v in [px, lrr, trr]):
        return '<div class="rr-track" style="height:18px;background:#21262D;border-radius:4px;"></div><div class="rr-labels"><span>-</span><span>-</span></div>'
    px, lrr, trr = float(px), float(lrr), float(trr)
    spread = trr - lrr
    pos = max(0, min(1, (px - lrr) / spread)) if spread > 0 else 0.5
    left_pct = pos * 100
    color = "#3FB950" if pos <= 0.35 else "#F85149" if pos >= 0.65 else "#8B949E"
    return (
        f'<div class="rr-track" style="width:{width_pct}%;">'
        f'<div class="rr-zone" style="left:0%;width:100%;background:#21262D;"></div>'
        f'<div class="rr-zone" style="left:0%;width:{left_pct:.0f}%;background:{color}18;"></div>'
        f'<div class="rr-dot" style="left:{max(3,min(97,left_pct)):.0f}%;border-color:{color};"></div>'
        f'</div>'
        f'<div class="rr-labels" style="width:{width_pct}%;"><span>{ff(lrr)}</span><span>{ff(px)}</span><span>{ff(trr)}</span></div>'
    )

def _gauge_html(value, max_val=100, color=None, height=14, label_left="0", label_right="100"):
    if value is None: value = 0
    try: pct = max(0, min(100, float(value) / float(max_val) * 100))
    except: pct = 0
    c = color or ("#3FB950" if pct > 70 else "#D29922" if pct > 40 else "#F85149")
    return (
        f'<div class="gauge-track" style="height:{height}px;">'
        f'<div class="gauge-fill" style="width:{pct:.0f}%;background:{c};"></div></div>'
        f'<div class="gauge-label"><span>{label_left}</span><span>{ff(value)}</span><span>{label_right}</span></div>'
    )

def _badge_html(text, kind="long"):
    cls = {"long":"badge-long","short":"badge-short","neut":"badge-neut","a":"badge-grade-a","b":"badge-grade-b","c":"badge-grade-c","news":"badge-news"}.get(kind,"badge-neut")
    return f'<span class="badge {cls}">{text}</span>'

def _regime_banner_html(quad, conf=0.0, monthly=None):
    color = _quad_color(quad)
    name = _quad_name(quad)
    mq = f' <span style="opacity:0.6;font-size:0.7rem;">Monthly: {monthly}</span>' if monthly else ''
    return (
        f'<div style="background: linear-gradient(90deg, {color}12 0%, transparent 70%); border-left: 3px solid {color}; '
        f'border-radius: 8px; padding: 8px 12px; margin: 6px 0; display: flex; align-items: center; gap: 10px;">'
        f'<div style="font-size: 1.3rem; font-weight: 800; color: {color}; letter-spacing: -1px;">{quad}</div>'
        f'<div><div style="font-size: 0.9rem; font-weight: 700; color: #E6EDF3;">{name}</div>'
        f'<div style="font-size: 0.7rem; color: #8B949E;">Conf: {conf:.0%}{mq}</div></div></div>'
    )

def _stacked_bar_html(long_pct, short_pct, cash_pct):
    return (
        f'<div class="stack-bar">'
        f'<div class="stack-seg" style="width:{long_pct}%;background:#3FB950;">📈 {long_pct:.0f}%</div>'
        f'<div class="stack-seg" style="width:{short_pct}%;background:#F85149;">📉 {short_pct:.0f}%</div>'
        f'<div class="stack-seg" style="width:{cash_pct}%;background:#8B949E;">💵 {cash_pct:.0f}%</div>'
        f'</div>'
    )

def _timeline_html(stage="INCEPTION"):
    stages = ["INCEPTION","ACCELERATION","EUPHORIA","CRISIS","AUCTION"]
    idx = stages.index(stage) if stage in stages else 0
    nodes = ""
    labels = ""
    for i, s in enumerate(stages):
        cls = "past" if i < idx else "active" if i == idx else ""
        line_cls = "active" if i < idx else ""
        nodes += f'<div class="tl-node {cls}"></div>'
        if i < len(stages) - 1:
            nodes += f'<div class="tl-line {line_cls}"></div>'
        labels += f'<span>{s}</span>'
    return f'<div class="timeline">{nodes}</div><div class="tl-labels">{labels}</div>'

def _skew_bars_html(d30=None, d60=None, d90=None):
    def bar(label, val):
        if val is None:
            return f'<div class="skew-row"><span class="skew-label">{label}</span><div class="skew-track"><div class="skew-fill" style="width:0%;background:#30363D;"></div></div><span class="skew-value">-</span></div>'
        v = float(val)
        pct = max(5, min(100, abs(v) * 200))
        color = "#3FB950" if v > 0.05 else "#F85149" if v < -0.05 else "#D29922"
        label_text = "Rich" if v > 0.05 else "Cheap" if v < -0.05 else "Fair"
        return f'<div class="skew-row"><span class="skew-label">{label}</span><div class="skew-track"><div class="skew-fill" style="width:{pct:.0f}%;background:{color};"></div></div><span class="skew-value" style="color:{color};">{label_text}</span></div>'
    return bar("30D", d30) + bar("60D", d60) + bar("90D", d90)

def _gex_bar_html(gex_val=None):
    if gex_val is None:
        return '<div class="gex-track" style="height:20px;background:#21262D;border-radius:4px;"></div>'
    v = float(gex_val)
    color = "#3FB950" if v > 0 else "#F85149"
    pct = min(100, abs(v) * 100)
    side = "Pos" if v > 0 else "Neg"
    margin = "margin-left:0;left:50%;" if v > 0 else f"margin-left:-{pct}%;left:50%;"
    return (
        f'<div class="gex-track" style="height:20px;">'
        f'<div class="gex-center"></div>'
        f'<div style="position:absolute;{margin}width:{pct:.0f}%;background:{color}30;height:100%;border-radius:4px;"></div>'
        f'<div style="position:absolute;width:100%;text-align:center;font-size:0.65rem;font-weight:700;color:{color};line-height:20px;">{side} {abs(v):.2f}</div>'
        f'</div>'
    )

def _heatmap_grid_html(items, key_label="name", key_quad="quad"):
    html = '<div class="hm-grid">'
    for it in items:
        q = it.get(key_quad, "Q3")
        color = _quad_color(q)
        name = it.get(key_label, "-")
        html += f'<div class="hm-cell" style="background:{color}18;border-color:{color}40;">{name}<div style="font-size:0.55rem;color:{color};margin-top:2px;">{q}</div></div>'
    html += '</div>'
    return html

def _asset_pulse_box(label, ret, sub=""):
    c = _ret_color(ret)
    txt = f"{ret:+.1%}" if ret is not None else "-"
    sub_html = f'<div style="font-size:0.55rem;color:#8B949E;margin-top:1px;">{sub}</div>' if sub else ""
    return f'<div class="pulse-box" style="background:{c}15;border-color:{c}30;"><div>{txt}</div><div class="pulse-label">{label}</div>{sub_html}</div>'

# ═══════════════════════════════════════════════════════════════════
# RISK RANGE ENGINE (proxy)
# ═══════════════════════════════════════════════════════════════════
def _build_row(ticker, prices, ar, vix_now=20, gamma_data=None, greeks_data=None, market_type="us_equity", news=None):
    v = ar.get(ticker, {}) if ar else {}
    s = prices.get(ticker)
    if not v and (s is None or len(s) < 15):
        return None

    if not v and s is not None:
        try:
            s_clean = pd.to_numeric(pd.Series(s), errors="coerce").dropna()
        except:
            return None
        if len(s_clean) < 15: return None
        px = float(s_clean.iloc[-1])
        sma20 = float(s_clean.tail(20).mean()) if len(s_clean) >= 20 else float(s_clean.mean())
        std20 = float(s_clean.tail(20).std()) if len(s_clean) >= 20 else float(s_clean.std())
        if not all(math.isfinite(v) for v in [px, sma20, std20]) or std20 == 0:
            lrr = round(px * 0.95, 2)
            trr = round(px * 1.05, 2)
            comp = "neutral"
        else:
            lrr = round(sma20 - 1.5 * std20, 4)
            trr = round(sma20 + 1.5 * std20, 4)
            comp = "bullish" if px < lrr else "bearish" if px > trr else "neutral"
        if comp == "neutral":
            r5 = _price_ret(ticker, prices, 5) or 0
            comp = "bullish" if r5 >= 0 else "bearish"
        v = {"px": px, "trade": {"lrr": lrr, "trr": trr}, "composite": comp, "quality": "B", "market": market_type}

    tr = v.get("trade", {})
    px = _safe_float(v.get("px"))
    lrr = _safe_float(tr.get("lrr"))
    trr = _safe_float(tr.get("trr"))
    if not px or not lrr or not trr:
        return None

    composite = v.get("composite", "neutral")
    side = "long" if composite == "bullish" else "short"
    spread = trr - lrr
    pos = (px - lrr) / spread if spread > 0 else 0.5

    if side == "long":
        entry = round(lrr, 2)
        tp1 = round(lrr + spread * 0.5, 2)
        tp2 = round(trr, 2)
        stop = round(lrr - spread * 0.25, 2)
        near_entry = pos <= 0.35
    else:
        entry = round(trr, 2)
        tp1 = round(trr - spread * 0.5, 2)
        tp2 = round(lrr, 2)
        stop = round(trr + spread * 0.25, 2)
        near_entry = pos >= 0.65

    rr = round(abs(tp1 - entry) / max(abs(entry - stop), 0.01), 2)
    grade = "A" if near_entry and rr >= 2.0 else "B" if near_entry else "C"

    gamma = {"ok": False}
    if s is not None:
        try:
            s_clean = pd.to_numeric(pd.Series(s), errors="coerce").dropna()
            if len(s_clean) >= 15:
                sma20 = float(s_clean.tail(20).mean()) if len(s_clean) >= 20 else float(s_clean.mean())
                std20 = float(s_clean.tail(20).std()) if len(s_clean) >= 20 else float(s_clean.std())
                gamma = {
                    "ok": True, "regime": "TRANSITION", "max_pain": round(sma20, 2),
                    "put_wall": round(sma20 - std20 * 2.0, 2),
                    "call_wall": round(sma20 + std20 * 2.0, 2),
                    "gamma_flip_up": round(sma20 + std20 * 1.5, 2),
                    "gamma_flip_down": round(sma20 - std20 * 1.5, 2),
                }
        except:
            pass

    news_signal = ""
    news_headline = ""
    news_sentiment = 0
    if news and isinstance(news, dict) and news.get("ticker_specific"):
        tn = news["ticker_specific"].get(ticker, {})
        if isinstance(tn, dict):
            news_signal = tn.get("front_run_signal", "")
            news_headline = (tn.get("headlines") or [""])[0] if tn else ""
            news_sentiment = tn.get("sentiment_score", 0) or 0

    direction = "LONG" if side == "long" else "SHORT"

    return {
        "ticker": ticker, "price": px, "entry": entry, "target_1": tp1, "target_2": tp2,
        "stop": stop, "rr": rr, "direction": direction, "grade": grade,
        "near_entry": near_entry, "pos_in_range": round(pos, 2), "side": side,
        "trade_l": lrr, "trade_r": trr,
        "r1m": _price_ret(ticker, prices, 21), "r3m": _price_ret(ticker, prices, 63),
        "composite": composite, "market_type": market_type,
        "gamma_regime": gamma.get("regime"), "max_pain": gamma.get("max_pain"),
        "put_wall": gamma.get("put_wall"), "call_wall": gamma.get("call_wall"),
        "news_signal": news_signal, "news_headline": news_headline, "news_sentiment": news_sentiment,
        "options_source": "PROXY",
    }

def _build_ihsg_row(ticker, prices, ar, **kwargs):
    row = _build_row(ticker, prices, ar, market_type="ihsg", **kwargs)
    if not row:
        return None
    row["direction"] = "LONG"
    sector = IHSG_SECTOR_MAP.get(ticker, "Indonesia")
    row["sector"] = sector
    r1m = row.get("r1m", 0) or 0
    if r1m > 0.05:
        row["recommendation"] = f"Strong momentum +{r1m:.1%} - {sector} play"
    elif r1m < -0.05:
        row["recommendation"] = f"Weak momentum {r1m:.1%} - avoid {sector}"
    else:
        row["recommendation"] = f"{sector} - range bound, wait for breakout"
    return row

def build_ticker_rows(tickers, market_type="us_equity", vix_now=20, gamma_data=None, greeks_data=None, news=None, prices=None, ar=None):
    rows = []
    for t in tickers:
        if market_type == "ihsg":
            r = _build_ihsg_row(t, prices, ar)
        else:
            r = _build_row(t, prices, ar, vix_now=vix_now, gamma_data=gamma_data, greeks_data=greeks_data, market_type=market_type, news=news)
        if r:
            rows.append(r)
    return rows

def split_long_short(rows):
    longs = [r for r in rows if "LONG" in r.get("direction", "")]
    shorts = [r for r in rows if "SHORT" in r.get("direction", "")]
    return sorted(longs, key=lambda x: x.get("rr", 0), reverse=True), sorted(shorts, key=lambda x: x.get("rr", 0), reverse=True)

# ═══════════════════════════════════════════════════════════════════
# VISUAL RENDERERS
# ═══════════════════════════════════════════════════════════════════
def render_ticker_card(row, expanded=False):
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
    news_sig = row.get("news_signal", "")
    r1m = row.get("r1m")
    prices_series = None
    if st.session_state.snap is not None:
        prices_series = st.session_state.snap.get("prices", {}).get(ticker)

    dir_kind = "long" if "LONG" in direction else "short" if "SHORT" in direction else "neut"
    dir_label = "LONG" if "LONG" in direction else "SHORT"
    grade_kind = grade.lower().replace("+", "")

    badges = _badge_html(dir_label, dir_kind) + _badge_html(grade, grade_kind)
    if rr_val and rr_val >= 2:
        badges += _badge_html(f"RR {rr_val}x", "news")
    if news_sig and "BULLISH" in str(news_sig):
        badges += _badge_html("NEWS+", "news")
    if news_sig and "BEARISH" in str(news_sig):
        badges += _badge_html("NEWS-", "news")

    spark = _sparkline_html(prices_series, width=90, height=28, bars=20)
    rr_html = _risk_range_html(px, trade_l, trade_r, width_pct=100)

    header_html = (
        f'<div class="ticker-card">'
        f'<div class="tc-left"><div class="tc-symbol">{ticker}</div><div class="tc-price">{ff(px)}</div><div class="tc-badges">{badges}</div></div>'
        f'{spark}'
        f'<div class="tc-rr">{rr_html}</div>'
        f'<div class="tc-metrics"><div>Entry {ff(entry)}</div><div>RR {ff(rr_val)}x</div><div>1M {fp(r1m)}</div></div>'
        f'</div>'
    )

    with st.expander(header_html, expanded=expanded):
        st.markdown(
            f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px 14px;margin:6px 0;">'
            f'<div style="font-size:0.8rem;color:#E6EDF3;font-weight:600;margin-bottom:6px;">🎯 Trade Setup</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:0.78rem;color:#8B949E;">'
            f'<div>📍 <b>Entry:</b> {ff(entry)}</div>'
            f'<div>🎯 <b>Target 1:</b> {ff(t1)}</div>'
            f'<div>🎯 <b>Target 2:</b> {ff(t2)}</div>'
            f'<div>🛑 <b>Stop Loss:</b> {ff(stop)}</div>'
            f'</div>'
            f'<div style="margin-top:8px;padding-top:8px;border-top:1px solid #30363D;font-size:0.78rem;color:#E6EDF3;">'
            f'💡 <b>Rekomendasi:</b> {row.get("recommendation", row.get("thesis", "Tunggu setup dekat entry level dengan RR minimal 2x."))}'
            f'</div></div>',
            unsafe_allow_html=True
        )

        if row.get("gamma_regime") or row.get("max_pain"):
            o1, o2, o3, o4 = st.columns(4)
            o1.metric("Gamma", row.get("gamma_regime", "-"))
            o2.metric("Max Pain", ff(row.get("max_pain")))
            o3.metric("Put Wall", ff(row.get("put_wall")))
            o4.metric("Call Wall", ff(row.get("call_wall")))

        if row.get("news_headline"):
            st.markdown(f'<div style="font-size:0.75rem;color:#58A6FF;margin-top:4px;">📰 {row.get("news_headline")[:120]}</div>', unsafe_allow_html=True)

def render_ticker_cards(rows, max_rows=30):
    if not rows:
        st.info("No setups pass filter.")
        return
    st.markdown(f'<div style="font-size:0.75rem;color:#8B949E;margin-bottom:6px;">Showing {min(len(rows), max_rows)} of {len(rows)} setups</div>', unsafe_allow_html=True)
    for i, r in enumerate(rows[:max_rows]):
        render_ticker_card(r, expanded=(i < 2))

def render_regime_bars(snap):
    gip_local = snap.get("gip")
    if gip_local is not None and not isinstance(gip_local, dict):
        gip_local = _GipProxy(gip_local)
    elif isinstance(gip_local, dict):
        gip_local = _GipProxy(gip_local)
    else:
        return
    q_probs = getattr(gip_local, "structural_probs", {}) or {}
    m_probs = getattr(gip_local, "monthly_probs", {}) or {}
    rf = snap.get("regime_forecast", {})
    rf3 = rf.get("3m", {}) if isinstance(rf, dict) else {}
    fq = rf3.get("predicted_quad", "Q3") if isinstance(rf3, dict) else "Q3"
    fc = rf3.get("prediction_confidence", 0) if isinstance(rf3, dict) else 0

    fig = make_subplots(rows=1, cols=3, subplot_titles=("Quarterly", "Monthly", "Forward 3M"),
                        column_widths=[0.33, 0.33, 0.34], horizontal_spacing=0.08)

    def add_bars(probs, col, opacity_map=None):
        for q in ["Q1","Q2","Q3","Q4"]:
            p = probs.get(q, 0) if isinstance(probs, dict) else 0
            color = _quad_color(q)
            op = opacity_map.get(q, 1.0) if opacity_map else 1.0
            fig.add_trace(go.Bar(x=[q], y=[p], marker_color=color, opacity=op,
                                 text=[f"<b>{p:.0%}</b>"], textposition="outside",
                                 textfont=dict(size=11, color="#E6EDF3"),
                                 showlegend=False, hoverinfo="skip"), row=1, col=col)

    add_bars(q_probs, 1)
    add_bars(m_probs, 2)
    fp = {q: (fc if q == fq else (1-fc)/3) for q in ["Q1","Q2","Q3","Q4"]}
    add_bars(fp, 3, opacity_map={q: 1.0 if q == fq else 0.45 for q in ["Q1","Q2","Q3","Q4"]})

    fig.update_layout(height=180, margin=dict(t=30, b=20, l=20, r=20),
                      paper_bgcolor="#0D1117", plot_bgcolor="#0D1117",
                      font=dict(color="#E6EDF3", size=10, family="Inter"),
                      yaxis=dict(range=[0,1.1], tickformat=".0%", showgrid=True, gridcolor="#21262D", dtick=0.25),
                      yaxis2=dict(range=[0,1.1], tickformat=".0%", showgrid=True, gridcolor="#21262D", dtick=0.25),
                      yaxis3=dict(range=[0,1.1], tickformat=".0%", showgrid=True, gridcolor="#21262D", dtick=0.25),
                      bargap=0.45, bargroupgap=0.1)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="regime_bars_top")

# ═══════════════════════════════════════════════════════════════════
# SESSION & SIDEBAR
# ═══════════════════════════════════════════════════════════════════
if "snap" not in st.session_state: st.session_state.snap = None
if "loading" not in st.session_state: st.session_state.loading = False
if "mq_override" not in st.session_state: st.session_state.mq_override = "Auto"

with st.sidebar:
    st.markdown("## 📊 MacroRegime Pro")
    st.caption("v30.3 VISUAL | Audit-Fixed")
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
        if st.button("🔄 Update", use_container_width=True):
            st.session_state.loading = True
    with c2:
        if st.button("⚡ Rebuild", use_container_width=True):
            st.session_state.loading = True
            st.session_state.snap = None

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
        if _g is not None and not isinstance(_g, dict):
            _g = _GipProxy(_g)
        elif isinstance(_g, dict):
            _g = _GipProxy(_g)
        _sq = getattr(_g, "structural_quad", "—") if _g is not None else "—"
        _mq = getattr(_g, "monthly_quad", "—") if _g is not None else "—"
        color = _quad_color(_sq)
        st.markdown(
            f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px;text-align:center;">'
            f'<div style="font-size:0.65rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.5px;">REGIME</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:{color};margin:4px 0;">{_sq} / {_mq}</div>'
            f'<div style="font-size:0.7rem;color:#8B949E;">{_quad_name(_sq)}</div></div>',
            unsafe_allow_html=True
        )

# ═══════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════
snap = st.session_state.snap
if snap is None:
    try:
        from data.loader import load_snapshot
        snap = load_snapshot(max_age_hours=6.0)
        if snap and snap.get("ok"):
            st.session_state.snap = snap
    except Exception as e:
        logger.warning(f"Initial snapshot load failed: {e}")
        snap = None

if snap is None or not snap.get("ok") or st.session_state.loading:
    try:
        from orchestrator import build_snapshot
    except Exception as e:
        st.error(f"Failed to import orchestrator: {e}")
        st.stop()
    _msg = "Updating..." if st.session_state.loading else "Building..."
    with st.spinner(_msg):
        pb = st.progress(0.0)
        pt = st.empty()
        def prog(m, f):
            pb.progress(f)
            pt.caption(f"Loading {m}")
        try:
            snap = build_snapshot(progress_cb=prog, include_us_stocks=inc_us, include_forex=inc_fx,
                                  include_commodities=inc_comm, include_crypto=inc_cryp, include_ihsg=inc_ihsg,
                                  portfolio_value=st.session_state.get("portfolio_value", 100_000))
            st.session_state.snap = snap
            st.session_state.loading = False
            pb.empty()
            pt.empty()
            st.rerun()
        except Exception as e:
            st.session_state.loading = False
            st.error(f"Build failed: {e}")
            st.stop()

if not snap or not snap.get("ok"):
    st.error("Build failed. Click Rebuild to retry.")
    st.stop()

# Extract globals - with robust type handling
gip_raw = snap.get("gip")
if gip_raw is not None and not isinstance(gip_raw, dict):
    gip = _GipProxy(gip_raw)
elif isinstance(gip_raw, dict):
    gip = _GipProxy(gip_raw)
else:
    gip = None
prices = snap.get("prices", {}) or {}
rr = snap.get("risk_ranges", {}) or {}
ar = rr.get("asset_ranges", {}) if isinstance(rr, dict) else {}
sq = getattr(gip, "structural_quad", None) or "Q3" if gip is not None else "Q3"
mq_raw = getattr(gip, "monthly_quad", None) or "Q2" if gip is not None else "Q2"
mq = st.session_state.mq_override if st.session_state.mq_override != "Auto" else mq_raw

# Robust VIX extraction
_vix_raw = prices.get("^VIX")
vix_now = 20.0
if _vix_raw is not None:
    try:
        if hasattr(_vix_raw, "tail"):
            vix_now = _safe_float(_vix_raw.tail(1)) or 20.0
        elif hasattr(_vix_raw, "__len__") and len(_vix_raw) > 0:
            vix_now = _safe_float(pd.Series(_vix_raw).iloc[-1]) or 20.0
        else:
            vix_now = _safe_float(_vix_raw) or 20.0
    except Exception:
        vix_now = 20.0

# ═══════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════
def page_dashboard():
    st.markdown("## 🏠 Dashboard")
    render_regime_bars(snap)

    markov = snap.get("markov_v3", {}) or {}
    health = snap.get("health", {}) or {}
    narrative = snap.get("narrative", {}) or {}

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px 12px;">'
            f'<div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.6px;font-weight:600;">Markov Regime</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:#E6EDF3;margin-top:4px;">{markov.get("current_regime","—").replace("_"," ")}</div>'
            f'<div style="font-size:0.7rem;color:#8B949E;margin-top:2px;">Conf {markov.get("confidence",0):.0%}</div></div>',
            unsafe_allow_html=True
        )
    with k2:
        vix_color = "#3FB950" if vix_now < 18 else "#D29922" if vix_now < 25 else "#F85149"
        st.markdown(
            f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px 12px;">'
            f'<div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.6px;font-weight:600;">VIX</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:{vix_color};margin-top:4px;">{vix_now:.1f}</div>'
            f'{_gauge_html(vix_now, max_val=40, color=vix_color, height=10, label_left="0", label_right="40")}</div>',
            unsafe_allow_html=True
        )
    with k3:
        n_alerts = len((snap.get("yves_v2", {}) or {}).get("alerts", [])) if isinstance(snap.get("yves_v2"), dict) else 0
        alert_color = "#F85149" if n_alerts > 2 else "#D29922" if n_alerts > 0 else "#3FB950"
        st.markdown(
            f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px 12px;">'
            f'<div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.6px;font-weight:600;">Alerts</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:{alert_color};margin-top:4px;">{n_alerts}</div>'
            f'<div style="font-size:0.7rem;color:#8B949E;margin-top:2px;">Behavioral signals</div></div>',
            unsafe_allow_html=True
        )
    with k4:
        n_longs = len([r for r in (snap.get("daily_signals", []) or []) if isinstance(r, dict) and "LONG" in str(r.get("direction", ""))])
        n_shorts = len([r for r in (snap.get("daily_signals", []) or []) if isinstance(r, dict) and "SHORT" in str(r.get("direction", ""))])
        st.markdown(
            f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px 12px;">'
            f'<div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.6px;font-weight:600;">Setups</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:#58A6FF;margin-top:4px;">{n_longs}L / {n_shorts}S</div>'
            f'<div style="font-size:0.7rem;color:#8B949E;margin-top:2px;">Alpha signals</div></div>',
            unsafe_allow_html=True
        )

    st.divider()

    st.markdown("### ⚡ Asset Pulse")
    pulse_assets = [
        ("SPY", "US Eq"), ("QQQ", "Tech"), ("IWM", "Small"), ("GLD", "Gold"),
        ("TLT", "Bonds"), ("UUP", "DXY"), ("BTC-USD", "Crypto")
    ]
    pulse_html = '<div class="pulse-grid">'
    for t, label in pulse_assets:
        ret = _price_ret(t, prices, 21)
        pulse_html += _asset_pulse_box(label, ret, t)
    pulse_html += '</div>'
    st.markdown(pulse_html, unsafe_allow_html=True)

    st.divider()

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown("### 🎯 Top Alpha")
        alpha_items = (snap.get("alpha_center", {}) or {}).get("all", []) or []
        if not isinstance(alpha_items, list):
            alpha_items = []
        top_alpha = sorted([a for a in alpha_items if isinstance(a, dict)], key=lambda x: x.get("priority_score", 0), reverse=True)[:8]

        if top_alpha:
            for item in top_alpha:
                dir_color = "#3FB950" if item.get("direction") == "LONG" else "#F85149" if item.get("direction") == "SHORT" else "#8B949E"
                grade = item.get("grade", "C")
                gc = "#3FB950" if grade in ("A","A+") else "#D29922" if grade=="B" else "#8B949E"
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;padding:6px 10px;background:#161B22;border:1px solid #30363D;border-radius:6px;margin:3px 0;font-size:0.82rem;">'
                    f'<span style="font-weight:700;min-width:50px;color:#E6EDF3;">{item.get("ticker","—")}</span>'
                    f'<span style="color:{dir_color};font-weight:600;min-width:45px;">{item.get("direction","—")}</span>'
                    f'<span style="background:{gc}22;color:{gc};padding:1px 6px;border-radius:4px;font-size:0.7rem;font-weight:600;border:1px solid {gc};">{grade}</span>'
                    f'<span style="color:#8B949E;flex:1;text-align:right;">{str(item.get("thesis",""))[:55]}</span></div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("No alpha signals generated yet.")

        st.markdown("### 📋 Playbook")
        pb = snap.get("playbook", {}) or {}
        best = pb.get("best_assets", [])[:5] if isinstance(pb, dict) else []
        worst = pb.get("worst_assets", [])[:5] if isinstance(pb, dict) else []
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

        health_score = health.get("composite_score", 50) if isinstance(health, dict) else 50
        health_color = "#3FB950" if health_score >= 70 else "#D29922" if health_score >= 50 else "#F85149"
        st.markdown(
            f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px 12px;margin-bottom:8px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
            f'<span style="font-size:0.7rem;color:#8B949E;text-transform:uppercase;font-weight:600;">Market Health</span>'
            f'<span style="font-size:1.1rem;font-weight:700;color:{health_color};">{health_score:.0f}</span></div>'
            f'{_gauge_html(health_score, max_val=100, color=health_color, height=12)}</div>',
            unsafe_allow_html=True
        )

        macro_nar = (narrative.get("macro_narrative") or {}) if isinstance(narrative, dict) else {}
        if macro_nar.get("narrative"):
            st.markdown(f"<div style='font-size:0.8rem;color:#E6EDF3;line-height:1.5;'>📰 {str(macro_nar['narrative'])[:200]}...</div>", unsafe_allow_html=True)

        scenarios = (narrative.get("scenarios") or {}) if isinstance(narrative, dict) else {}
        if scenarios:
            dom = scenarios.get("dominant_scenario", "base") if isinstance(scenarios, dict) else "base"
            for scen_name in ["bull", "base", "bear"]:
                scen = scenarios.get(scen_name, {}) if isinstance(scenarios, dict) else {}
                p = scen.get("probability", 0) if isinstance(scen, dict) else 0
                color = "#3FB950" if scen_name == "bull" else "#D29922" if scen_name == "base" else "#F85149"
                is_dom = " ★" if dom == scen_name else ""
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid #21262D;">'
                    f'<span style="font-size:0.8rem;color:#E6EDF3;">{scen_name.title()}{is_dom}</span>'
                    f'<span style="font-size:0.85rem;font-weight:700;color:{color};">{p:.0%}</span></div>',
                    unsafe_allow_html=True
                )

        rumor = snap.get("rumor_watch", []) or []
        if rumor:
            st.markdown("### 🔮 Front-Run")
            for r in rumor[:3]:
                if not isinstance(r, dict):
                    continue
                sig = r.get("signal", "")
                color = "#3FB950" if "BULLISH" in sig else "#F85149" if "BEARISH" in sig else "#D29922"
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0;">'
                    f'<span style="font-size:0.8rem;color:#E6EDF3;">{r.get("ticker","—")}</span>'
                    f'<span style="font-size:0.75rem;color:{color};font-weight:600;">{str(sig)[:20]}</span></div>',
                    unsafe_allow_html=True
                )

    st.divider()

    with st.expander("🔬 Deep Technical", expanded=False):
        st.markdown("**Skew Term Structure**")
        skew = snap.get("skew_term", {}) or {}
        skew_data = skew.get("skew_data", {}) if isinstance(skew, dict) else {}
        d30 = d60 = d90 = None
        if isinstance(skew_data, dict):
            for k, v in skew_data.items():
                if isinstance(v, dict):
                    val = v.get("skew") or v.get("value") or v.get("90_10")
                    if "30" in str(k).lower() or "1m" in str(k).lower():
                        d30 = _safe_float(val)
                    if "60" in str(k).lower() or "2m" in str(k).lower():
                        d60 = _safe_float(val)
                    if "90" in str(k).lower() or "3m" in str(k).lower():
                        d90 = _safe_float(val)
        st.markdown(_skew_bars_html(d30, d60, d90), unsafe_allow_html=True)

        st.markdown("**GEX Exposure**")
        gex = snap.get("gex_data", {}) or {}
        gex_val = None
        if isinstance(gex, dict):
            for k, v in gex.items():
                if isinstance(v, dict):
                    gv = v.get("net_gex") or v.get("gex") or v.get("total_gex")
                    if gv is not None:
                        gex_val = _safe_float(gv)
                        break
        st.markdown(_gex_bar_html(gex_val), unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**VRP**")
            vrp = snap.get("vrp_scanner", {}) or {}
            if isinstance(vrp, dict) and vrp.get("ok"):
                for item in vrp.get("high_vrp_sell_premium", [])[:3]:
                    if isinstance(item, dict):
                        score = item.get("vrp_pct", 0)
                        st.markdown(
                            f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">'
                            f'<span style="font-size:0.75rem;color:#E6EDF3;min-width:50px;">{item.get("ticker","—")}</span>'
                            f'<div class="gauge-track" style="flex:1;height:10px;"><div class="gauge-fill" style="width:{min(100,abs(score)*5):.0f}%;background:#F85149;"></div></div>'
                            f'<span style="font-size:0.7rem;color:#F85149;font-weight:700;width:40px;text-align:right;">{score:.0f}%</span></div>',
                            unsafe_allow_html=True
                        )
            else:
                st.caption("VRP unavailable")
        with c2:
            st.markdown("**Squeeze**")
            sq_scan = snap.get("squeeze_scanner", {}) or {}
            if isinstance(sq_scan, dict) and sq_scan.get("ok"):
                for item in sq_scan.get("imminent_squeezes", [])[:3]:
                    if isinstance(item, dict):
                        score = item.get("squeeze_score", 0)
                        st.markdown(
                            f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">'
                            f'<span style="font-size:0.75rem;color:#E6EDF3;min-width:50px;">{item.get("ticker","—")}</span>'
                            f'<div class="gauge-track" style="flex:1;height:10px;"><div class="gauge-fill" style="width:{min(100,score):.0f}%;background:#D29922;"></div></div>'
                            f'<span style="font-size:0.7rem;color:#D29922;font-weight:700;width:40px;text-align:right;">{score:.0f}</span></div>',
                            unsafe_allow_html=True
                        )
            else:
                st.caption("Squeeze unavailable")

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
            cols[i % 4].markdown(f"<span style='color:{color};font-size:0.8rem;'>● {name}</span>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# PAGE: ALPHA CENTER
# ═══════════════════════════════════════════════════════════════════
def page_alpha():
    st.markdown("## ⚡ Alpha Center")
    st.markdown(_regime_banner_html(sq, conf=0.6, monthly=mq), unsafe_allow_html=True)

    summary = snap.get("summary", {}) or {}
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Markov Regime", str(summary.get("v7_markov_regime", "—")).split("_")[0] if summary.get("v7_markov_regime") else "—")
    k2.metric("Smart $ Consensus", summary.get("v7_smart_money_consensus", 0))
    k3.metric("Top Theses", summary.get("v7_top_theses_count", 0))
    k4.metric("Kelly", f"{summary.get('v7_markov_kelly', 0.25):.0%}")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["🏆 Top Picks", "📊 Vol & Squeeze", "🔮 Discovery"])

    with tab1:
        alpha_candidates = []
        comp_signals = snap.get("composite_signals", {}) or {}
        if isinstance(comp_signals, dict):
            for ticker, sig in comp_signals.items():
                if not isinstance(sig, dict):
                    continue
                if sig.get("direction") in ("NEUTRAL", "AVOID"):
                    continue
                if sig.get("confidence", 0) < 0.4:
                    continue
                thesis = (snap.get("thought_process", {}) or {}).get(ticker, {})
                if not isinstance(thesis, dict):
                    thesis = {}
                if thesis.get("thesis_score", 0) < 60:
                    continue
                rr = (snap.get("risk_ranges", {}) or {}).get("asset_ranges", {})
                if isinstance(rr, dict):
                    rr_t = rr.get(ticker, {})
                    if not isinstance(rr_t, dict) or rr_t.get("quality") not in ("A+", "A"):
                        continue
                sm = ((snap.get("smart_money", {}) or {}).get("per_ticker", {}) or {}).get(ticker, {})
                if not isinstance(sm, dict):
                    sm = {}
                sm_boost = 15 if sm.get("smart_money_held") else 0
                alpha_candidates.append({
                    "ticker": ticker,
                    "direction": sig.get("direction"),
                    "confidence": sig.get("confidence", 0),
                    "thesis_score": thesis.get("thesis_score", 0),
                    "primary_role": thesis.get("primary_role", "—"),
                    "alpha_score": sig.get("confidence", 0) * 35 + thesis.get("thesis_score", 0) * 0.3 + sm_boost,
                })
        alpha_candidates.sort(key=lambda x: x.get("alpha_score", 0), reverse=True)
        top_alpha = [c for c in alpha_candidates if c.get("alpha_score", 0) >= 70][:20]

        if not top_alpha:
            st.info("No cross-market candidates meet Alpha Center high bar (≥70/100).")
        else:
            st.markdown(f"**{len(top_alpha)} candidates** from {len(alpha_candidates)} total")
            for i, c in enumerate(top_alpha):
                dir_color = "#3FB950" if c["direction"] == "LONG" else "#F85149"
                with st.expander(f"#{i+1} {c['ticker']} · Score {c['alpha_score']:.0f}/100 · {c['direction']}", expanded=(i < 3)):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Confidence", f"{c['confidence']:.0%}")
                    c2.metric("Thesis", f"{c['thesis_score']:.0f}/100")
                    c3.metric("Role", c["primary_role"])

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 VRP Scanner")
            vrp = snap.get("vrp_scanner", {}) or {}
            if isinstance(vrp, dict) and vrp.get("ok"):
                st.metric("Sell Premium", len(vrp.get("high_vrp_sell_premium", [])))
                st.metric("Buy Premium", len(vrp.get("low_vrp_buy_premium", [])))
                for item in vrp.get("high_vrp_sell_premium", [])[:5]:
                    if isinstance(item, dict):
                        st.markdown(f"• **{item.get('ticker')}** · VRP +{item.get('vrp_pct', 0):.0f}% · IV Rank {item.get('iv_rank', '—')}")
            else:
                st.info("VRP scanner unavailable")

        with col2:
            st.markdown("### 🔥 Squeeze Scanner")
            sq_scan = snap.get("squeeze_scanner", {}) or {}
            if isinstance(sq_scan, dict) and sq_scan.get("ok"):
                st.metric("Imminent", len(sq_scan.get("imminent_squeezes", [])))
                st.metric("Strong", len(sq_scan.get("strong_candidates", [])))
                for item in sq_scan.get("imminent_squeezes", [])[:5]:
                    if isinstance(item, dict):
                        st.markdown(f"• **{item.get('ticker')}** · Score {item.get('squeeze_score', 0):.0f}/100 · {item.get('tier', '—')}")
            else:
                st.info("Squeeze scanner unavailable")

    with tab3:
        st.markdown("### 🔮 Discovery Brain")
        disc = snap.get("discovery_brain", {}) or {}
        if isinstance(disc, dict) and disc.get("by_mode"):
            for mode in ("adaptive", "reactive", "proactive"):
                items = disc.get("by_mode", {}).get(mode, [])
                if items:
                    st.markdown(f"**{mode.title()}** ({len(items)})")
                    for item in items[:5]:
                        if isinstance(item, dict):
                            with st.expander(f"{item.get('name', '—').replace('_', ' ')} · conf {item.get('confidence', 0):.0%}"):
                                st.markdown(item.get("thesis", "—"))
        else:
            st.info("Discovery Brain — no candidates this snapshot")

        st.markdown("### 💰 Position Sizing")
        sizing = snap.get("portfolio_sizing_v2", {}) or {}
        if isinstance(sizing, dict) and sizing.get("positions"):
            st.metric("Deployed", f"{sizing.get('total_deployed_pct', 0):.1%}")
            st.metric("Cash", f"{sizing.get('cash_pct', 0):.1%}")
            df = pd.DataFrame([{
                "Ticker": p.get("ticker"),
                "Size %": f"{p.get('target_pct', 0):.2f}%",
                "Size $": f"{p.get('target_dollar', 0):,.0f}",
                "Mode": p.get("mode"),
                "Sector": p.get("sector"),
            } for p in sizing.get("positions", []) if isinstance(p, dict)])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No sized positions yet.")

# ═══════════════════════════════════════════════════════════════════
# PAGE: US STOCKS
# ═══════════════════════════════════════════════════════════════════
def page_us_stocks():
    st.markdown("## 🇺🇸 US Stocks")
    st.markdown(_regime_banner_html(sq, conf=0.6, monthly=mq), unsafe_allow_html=True)

    playbook = {
        "Q1": {"beli": ["QQQ","XLK","NVDA","AAPL","MSFT","GOOGL","META","AMD","ARKK"], "short": ["XLU","XLP","TLT","GLD"]},
        "Q2": {"beli": ["XLF","XLE","XLI","XLB","KRE","IWM","XOM","CVX"], "short": ["TLT","IEF"]},
        "Q3": {"beli": ["XLE","XLP","XLU","ITA","GLD","SLV","VST","CEG","BE","LITE","CCJ"], "short": ["QQQ","XLK","IWM","ARKK","KRE"]},
        "Q4": {"beli": ["TLT","IEF","GLD","XLU","XLP","XLV"], "short": ["QQQ","XLK","IWM","XLY","XLF","XLE"]},
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

    us_tickers = list(US_SECTORS.keys()) if US_SECTORS else []
    for bucket in ["Growth","Quality","Defensives","Semis","Energy","Industrials","Financials","AI_Infra","PreciousMetals"]:
        us_tickers += US_BUCKETS.get(bucket, []) if US_BUCKETS else []
    if not us_tickers:
        us_tickers = FALLBACK_US
    us_tickers = list(dict.fromkeys(us_tickers))

    rows = build_ticker_rows(us_tickers, "us_equity", vix_now, snap.get("gamma_data"), snap.get("greeks_data"), snap.get("news_narratives"), prices=prices, ar=ar)
    longs, shorts = split_long_short(rows)

    st.markdown(f"**{len(rows)} setups** · 🟢 {len(longs)} Long · 🔴 {len(shorts)} Short")

    tab_l, tab_s = st.tabs([f"🟢 Long ({len(longs)})", f"🔴 Short ({len(shorts)}))"])
    with tab_l:
        render_ticker_cards(longs)
    with tab_s:
        render_ticker_cards(shorts)

# ═══════════════════════════════════════════════════════════════════
# PAGE: FOREX
# ═══════════════════════════════════════════════════════════════════
def page_forex():
    st.markdown("## 💱 Forex")
    st.markdown(_regime_banner_html(sq, conf=0.6, monthly=mq), unsafe_allow_html=True)

    playbook = {
        "Q1": {"beli": ["EURUSD","AUDUSD","EM FX"], "short": ["DXY/UUP"]},
        "Q2": {"beli": ["GBPUSD","CADUSD"], "short": ["JPY"]},
        "Q3": {"beli": ["UUP","CHF"], "short": ["EURUSD","GBPUSD","EM FX"]},
        "Q4": {"beli": ["JPY","CHF"], "short": ["AUDUSD","EM FX"]},
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

    fx_tickers = list(FOREX_PAIRS.keys()) if FOREX_PAIRS else FALLBACK_FX
    rows = build_ticker_rows(fx_tickers, "forex", vix_now, snap.get("gamma_data"), snap.get("greeks_data"), snap.get("news_narratives"), prices=prices, ar=ar)
    longs, shorts = split_long_short(rows)

    st.markdown(f"**{len(rows)} pairs** · 🟢 {len(longs)} Long · 🔴 {len(shorts)} Short")

    tab_l, tab_s = st.tabs([f"🟢 Long ({len(longs)})", f"🔴 Short ({len(shorts)}))"])
    with tab_l:
        render_ticker_cards(longs)
    with tab_s:
        render_ticker_cards(shorts)

# ═══════════════════════════════════════════════════════════════════
# PAGE: COMMODITIES
# ═══════════════════════════════════════════════════════════════════
def page_commodities():
    st.markdown("## 🛢️ Commodities")
    st.markdown(_regime_banner_html(sq, conf=0.6, monthly=mq), unsafe_allow_html=True)

    playbook = {
        "Q1": {"beli": ["Copper","Industrial Metals"], "short": ["Gold (counter-trend)"]},
        "Q2": {"beli": ["CL=F","USO","XLE","Energy"], "short": []},
        "Q3": {"beli": ["GLD","SLV","CL=F","CCJ","URA"], "short": []},
        "Q4": {"beli": ["GLD","TLT"], "short": ["CL=F","Industrial metals"]},
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

    comm_tickers = list(COMMODITIES.keys()) if COMMODITIES else FALLBACK_COMM
    rows = build_ticker_rows(comm_tickers, "commodity", vix_now, snap.get("gamma_data"), snap.get("greeks_data"), snap.get("news_narratives"), prices=prices, ar=ar)
    longs, shorts = split_long_short(rows)

    st.markdown(f"**{len(rows)} commodities** · 🟢 {len(longs)} Long · 🔴 {len(shorts)} Short")

    tab_l, tab_s = st.tabs([f"🟢 Long ({len(longs)})", f"🔴 Short ({len(shorts)}))"])
    with tab_l:
        render_ticker_cards(longs)
    with tab_s:
        render_ticker_cards(shorts)

# ═══════════════════════════════════════════════════════════════════
# PAGE: CRYPTO
# ═══════════════════════════════════════════════════════════════════
def page_crypto():
    st.markdown("## ₿ Crypto")
    st.markdown(_regime_banner_html(sq, conf=0.6, monthly=mq), unsafe_allow_html=True)

    playbook = {
        "Q1": {"beli": ["BTC","ETH","SOL","alts"], "short": []},
        "Q2": {"beli": ["BTC","MSTR","CORZ","IREN"], "short": []},
        "Q3": {"beli": ["BTC","MSTR","IBIT"], "short": ["alts (ETH/SOL relative)"]},
        "Q4": {"beli": ["BTC (hedge ONLY)"], "short": ["alts","ETH","memecoin"]},
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

    crypto_tickers = list(CRYPTO.keys()) if CRYPTO else FALLBACK_CRYPTO
    rows = build_ticker_rows(crypto_tickers, "crypto", vix_now, snap.get("gamma_data"), snap.get("greeks_data"), snap.get("news_narratives"), prices=prices, ar=ar)
    longs, shorts = split_long_short(rows)

    st.markdown(f"**{len(rows)} coins** · 🟢 {len(longs)} Long · 🔴 {len(shorts)} Short")

    tab_l, tab_s = st.tabs([f"🟢 Long ({len(longs)})", f"🔴 Short ({len(shorts)}))"])
    with tab_l:
        render_ticker_cards(longs)
    with tab_s:
        render_ticker_cards(shorts)

# ═══════════════════════════════════════════════════════════════════
# PAGE: GLOBAL & EM
# ═══════════════════════════════════════════════════════════════════
def page_global():
    st.markdown("## 🌍 Global & EM")
    st.markdown(_regime_banner_html(sq, conf=0.6, monthly=mq), unsafe_allow_html=True)

    global_ = snap.get("global", {}) or {}
    country_list = global_.get("country_list", []) if isinstance(global_, dict) else []

    if not country_list:
        base_map = {
            "Q1": ["USA","Japan","India","Taiwan","South Korea","Vietnam","Mexico","Singapore","Philippines","Malaysia","UAE","Israel","Poland","Czech Republic","Romania"],
            "Q2": ["China","Brazil","Australia","Canada","South Africa","Saudi Arabia","Chile","Peru","Indonesia","Thailand","Colombia","New Zealand","Norway","Kazakhstan","Angola"],
            "Q3": ["UK","Germany","France","Italy","Russia","Turkey","Argentina","Nigeria","Pakistan","Egypt","Spain","Netherlands","Belgium","Sweden","Switzerland"],
            "Q4": ["Venezuela","Iran","Ukraine","Greece","Portugal","Lebanon","Syria","Yemen","Zimbabwe","Sudan","Afghanistan","North Korea","Myanmar","Belarus","Bolivia"],
        }
        country_list = []
        for q, countries in base_map.items():
            for c in countries:
                country_list.append({"country": c, "quad": q, "regime_name": _quad_name(q)})

    st.markdown("### 🗺️ Country Regime Map")
    st.markdown(_heatmap_grid_html(country_list[:16], key_label="country", key_quad="quad"), unsafe_allow_html=True)
    if len(country_list) > 16:
        st.markdown(_heatmap_grid_html(country_list[16:32], key_label="country", key_quad="quad"), unsafe_allow_html=True)

    st.divider()

    st.markdown("### 🇮🇩 IHSG Report")
    ihsg_tickers = list(IHSG_UNIVERSE.keys()) if IHSG_UNIVERSE else FALLBACK_IHSG
    ihsg_rows = build_ticker_rows(ihsg_tickers, "ihsg", vix_now, prices=prices, ar=ar)

    by_sector = {}
    for r in ihsg_rows:
        sect = IHSG_SECTOR_MAP.get(r.get("ticker"), "Other")
        by_sector.setdefault(sect, []).append(r)

    if by_sector:
        sectors = list(by_sector.keys())
        counts = [len(v) for v in by_sector.values()]
        colors = [_ret_color(sum(x.get("r1m",0) or 0 for x in by_sector[s])/max(len(by_sector[s]),1)) for s in sectors]
        fig = go.Figure(go.Bar(
            y=sectors, x=counts, orientation="h",
            marker_color=colors,
            text=[str(c) for c in counts], textposition="outside",
            textfont=dict(size=11, color="#E6EDF3")
        ))
        fig.update_layout(height=max(250, len(sectors)*35), margin=dict(l=120,r=40,t=20,b=20),
                          paper_bgcolor="#0D1117", plot_bgcolor="#0D1117",
                          font=dict(color="#E6EDF3", size=11, family="Inter"),
                          xaxis=dict(showgrid=True, gridcolor="#21262D"),
                          yaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="ihsg_sector_bar")

    st.markdown(f"**{len(ihsg_rows)} stocks** · Sectors: {', '.join(by_sector.keys())}")

    for sector, items in by_sector.items():
        with st.expander(f"**{sector}** ({len(items)} stocks)", expanded=False):
            render_ticker_cards(items, max_rows=10)

# ═══════════════════════════════════════════════════════════════════
# PAGE: THEMES
# ═══════════════════════════════════════════════════════════════════
def page_themes():
    st.markdown("## 📖 Themes & Playbook")
    st.markdown(_regime_banner_html(sq, conf=0.6, monthly=mq), unsafe_allow_html=True)

    allocation = {
        "Q1": {"long": 75, "short": 5, "cash": 20, "style": "Tech 30% | Growth 20% | Crypto 15% | EM 5% | Defensives 5%"},
        "Q2": {"long": 70, "short": 10, "cash": 20, "style": "Cyclicals 25% | Financials 15% | Energy 15% | Materials 10% | Small Caps 5%"},
        "Q3": {"long": 60, "short": 15, "cash": 25, "style": "Energy/Infra 20% | Real Assets 15% | Crypto 10% | EM/LatAm 8% | IHSG Energy 7%"},
        "Q4": {"long": 50, "short": 20, "cash": 30, "style": "TLT 15% | Gold 10% | Utilities 10% | Staples 10% | Healthcare 5%"},
    }
    alloc = allocation.get(sq, allocation["Q3"])

    st.markdown("### 💼 Portfolio Allocation")
    st.markdown(_stacked_bar_html(alloc["long"], alloc["short"], alloc["cash"]), unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:0.8rem; color:#8B949E; margin-top:8px;'>**Style:** {alloc['style']}</div>", unsafe_allow_html=True)

    st.divider()

    st.markdown("### 🌀 Boom-Bust Stage")
    bb = snap.get("boom_bust", {}) or {}
    stage = bb.get("stage", "INCEPTION") if isinstance(bb, dict) else "INCEPTION"
    st.markdown(_timeline_html(stage), unsafe_allow_html=True)

    st.divider()

    st.markdown("### 🚧 Active Bottlenecks")
    bottlenecks = ((snap.get("narrative", {}) or {}).get("active_bottlenecks", []) or []) if isinstance(snap.get("narrative"), dict) else []
    if bottlenecks:
        for b in bottlenecks[:5]:
            if not isinstance(b, dict):
                continue
            beneficiaries = ", ".join(b.get("beneficiaries", [])[:5])
            st.markdown(
                f'<div style="background:#161B22;border-left:3px solid #F85149;border-radius:6px;padding:8px 12px;margin:4px 0;">'
                f'<div style="font-size:0.85rem;font-weight:700;color:#E6EDF3;">{str(b.get("name","")).replace("_"," ").title()}</div>'
                f'<div style="font-size:0.75rem;color:#8B949E;margin-top:4px;">Beneficiaries: {beneficiaries}</div></div>',
                unsafe_allow_html=True
            )
    else:
        st.info("No active bottlenecks detected.")

    st.divider()

    st.markdown("### ⚡ Cem Karsan / 0DTE")
    odte = snap.get("odte_monitor", {}) or {}
    if isinstance(odte, dict) and odte.get("tickers"):
        for t, data in list(odte.get("tickers", {}).items())[:3]:
            if not isinstance(data, dict):
                continue
            pin = data.get("pin_risk", 50)
            vanna_dir = data.get("vanna", "neutral")
            charm_dir = data.get("charm", "neutral")
            v_arrow = "⬆" if "up" in str(vanna_dir).lower() or "pos" in str(vanna_dir).lower() else "⬇" if "down" in str(vanna_dir).lower() or "neg" in str(vanna_dir).lower() else "➡"
            c_arrow = "⬆" if "up" in str(charm_dir).lower() or "pos" in str(charm_dir).lower() else "⬇" if "down" in str(charm_dir).lower() or "neg" in str(charm_dir).lower() else "➡"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin:6px 0;padding:8px 10px;background:#161B22;border:1px solid #30363D;border-radius:6px;">'
                f'<span style="font-weight:700;font-size:0.9rem;color:#E6EDF3;min-width:50px;">{t}</span>'
                f'<div style="flex:1;">'
                f'<div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;font-weight:600;">Pin Risk</div>'
                f'{_gauge_html(pin, max_val=100, color="#D29922", height=10, label_left="0", label_right="100")}</div>'
                f'<div style="font-size:0.8rem;color:#58A6FF;font-weight:700;">Vanna {v_arrow}</div>'
                f'<div style="font-size:0.8rem;color:#A371F7;font-weight:700;">Charm {c_arrow}</div></div>',
                unsafe_allow_html=True
            )
    else:
        st.caption("0DTE data unavailable - showing proxy")
        for t in ["SPY","QQQ","IWM"]:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin:6px 0;padding:8px 10px;background:#161B22;border:1px solid #30363D;border-radius:6px;">'
                f'<span style="font-weight:700;font-size:0.9rem;color:#E6EDF3;min-width:50px;">{t}</span>'
                f'<div style="flex:1;">'
                f'<div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;font-weight:600;">Pin Risk</div>'
                f'{_gauge_html(50, max_val=100, color="#30363D", height=10, label_left="0", label_right="100")}</div>'
                f'<div style="font-size:0.8rem;color:#8B949E;font-weight:700;">Vanna ➡</div>'
                f'<div style="font-size:0.8rem;color:#8B949E;font-weight:700;">Charm ➡</div></div>',
                unsafe_allow_html=True
            )

    st.divider()

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
        with st.expander(f"{status} {name} - {desc}", expanded=False):
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
st.caption(f"MacroRegime Pro v30.3 VISUAL · Built {snap.get('build_time_s', 0):.0f}s ago · {snap.get('prices_loaded', 0)} assets · {snap.get('fred_coverage', 0)} indicators{flip_note}")
