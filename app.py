"""app.py - MacroRegime Pro v32.1 FIX
Major rewrite:
- Dashboard: regime + narrative + metrics + boom-bust + behavioral + allocation + scenarios + bottlenecks + asset pulse + deep technical
- Alpha Center: bottleneck + front-run + quad rotation candidates
- Market tabs: ticker cards enriched with MM positioning (max pain, gamma, gex, vanna, charm, skew)
- US Stocks aggregate: SPY/QQQ/IWM/GLD/TLT options section
- Dark Pool proxy prints
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
st.set_page_config(page_title="MacroRegime Pro v32", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap");
html, body, [class*="css"] { font-family: "Inter", sans-serif; }
.block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; padding-left: 1rem !important; padding-right: 1rem !important; max-width: 1440px !important; }
h1 { font-size: 1.4rem !important; margin: 0.2rem 0 0.3rem !important; font-weight: 800 !important; letter-spacing: -0.5px; }
h2 { font-size: 1.05rem !important; margin: 0.4rem 0 0.2rem !important; font-weight: 700 !important; letter-spacing: -0.3px; }
h3 { font-size: 0.9rem !important; margin: 0.3rem 0 0.15rem !important; font-weight: 600 !important; }
hr { margin: 0.4rem 0 !important; opacity: 0.08; border-color: #30363D; }
[data-testid="stMetric"] { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 6px; padding: 5px 8px !important; }
[data-testid="stMetricLabel"] { font-size: 0.58rem !important; font-weight: 600 !important; letter-spacing: 0.6px; text-transform: uppercase; opacity: 0.55; }
[data-testid="stMetricValue"] { font-size: 1.05rem !important; font-weight: 700 !important; }

.ticker-card-v4 { display: flex; align-items: center; gap: 10px; padding: 7px 10px; background: #161B22; border: 1px solid #30363D; border-radius: 8px; margin: 3px 0; transition: border-color 0.2s; flex-wrap: wrap; }
.ticker-card-v4:hover { border-color: #484F58; }
.tc-v4-left { min-width: 80px; }
.tc-v4-symbol { font-weight: 800; font-size: 0.9rem; color: #E6EDF3; letter-spacing: -0.3px; }
.tc-v4-price { font-weight: 600; font-size: 0.75rem; color: #8B949E; font-variant-numeric: tabular-nums; }
.tc-v4-badges { display: flex; gap: 3px; flex-wrap: wrap; margin-top: 2px; }
.tc-v4-spark { width: 80px; height: 24px; display: flex; align-items: flex-end; gap: 1px; flex-shrink: 0; }
.tc-v4-rr { flex: 1; min-width: 120px; }
.tc-v4-meta { display: flex; gap: 8px; font-size: 0.68rem; color: #8B949E; font-variant-numeric: tabular-nums; min-width: 110px; }

.badge { display: inline-flex; align-items: center; padding: 1px 5px; border-radius: 10px; font-size: 0.6rem; font-weight: 700; letter-spacing: 0.3px; border: 1px solid transparent; line-height: 1.3; }
.badge-long { background: rgba(34,197,94,0.12); color: #3FB950; border-color: rgba(34,197,94,0.3); }
.badge-short { background: rgba(239,68,68,0.12); color: #F85149; border-color: rgba(239,68,68,0.3); }
.badge-neut { background: rgba(234,179,8,0.12); color: #eab308; border-color: rgba(234,179,8,0.3); }
.badge-grade-a { background: rgba(34,197,94,0.15); color: #3FB950; border-color: #3FB950; }
.badge-grade-b { background: rgba(234,179,8,0.15); color: #D29922; border-color: #D29922; }
.badge-grade-c { background: rgba(139,148,158,0.15); color: #8B949E; border-color: #8B949E; }
.badge-news { background: rgba(88,166,255,0.12); color: #58A6FF; border-color: rgba(88,166,255,0.3); }
.badge-mm { background: rgba(168,85,247,0.12); color: #A855F7; border-color: rgba(168,85,247,0.3); }

.sp-bar-v4 { width: 3px; border-radius: 1px; opacity: 0.85; }
.rr-track-v4 { position: relative; height: 16px; background: #21262D; border-radius: 4px; overflow: hidden; }
.rr-zone-v4 { position: absolute; top: 2px; bottom: 2px; border-radius: 2px; }
.rr-dot-v4 { position: absolute; top: 50%; transform: translate(-50%, -50%); width: 7px; height: 7px; border-radius: 50%; background: #E6EDF3; border: 2px solid #58A6FF; z-index: 10; box-shadow: 0 0 4px rgba(88,166,255,0.4); }
.rr-labels-v4 { display: flex; justify-content: space-between; font-size: 0.58rem; color: #8B949E; margin-top: 1px; font-variant-numeric: tabular-nums; }

.gauge-track { position: relative; height: 12px; background: #21262D; border-radius: 6px; overflow: hidden; margin: 3px 0; }
.gauge-fill { position: absolute; top: 0; bottom: 0; left: 0; border-radius: 6px; transition: width 0.5s ease; }
.gauge-label { display: flex; justify-content: space-between; font-size: 0.6rem; color: #8B949E; margin-top: 1px; }

.hm-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; }
.hm-cell { padding: 5px 3px; border-radius: 4px; text-align: center; font-size: 0.68rem; font-weight: 600; color: #E6EDF3; border: 1px solid rgba(255,255,255,0.05); }

.pulse-hbox { min-width: 90px; height: 52px; border-radius: 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; color: #E6EDF3; border: 1px solid rgba(255,255,255,0.06); flex-shrink: 0; }
.pulse-hlabel { font-size: 0.6rem; font-weight: 500; color: rgba(255,255,255,0.5); text-transform: uppercase; margin-top: 1px; }

.timeline { display: flex; align-items: center; gap: 0px; margin: 6px 0; }
.tl-node { width: 12px; height: 12px; border-radius: 50%; border: 2px solid #30363D; background: #21262D; flex-shrink: 0; }
.tl-node.active { border-color: #58A6FF; background: #58A6FF; box-shadow: 0 0 5px rgba(88,166,255,0.35); }
.tl-node.past { border-color: #3FB950; background: #3FB950; }
.tl-line { flex: 1; height: 2px; background: #30363D; min-width: 16px; }
.tl-line.active { background: #58A6FF; }
.tl-labels { display: flex; justify-content: space-between; font-size: 0.58rem; color: #8B949E; margin-top: 3px; }

.stack-bar { display: flex; height: 20px; border-radius: 4px; overflow: hidden; background: #21262D; }
.stack-seg { display: flex; align-items: center; justify-content: center; font-size: 0.6rem; font-weight: 700; color: #fff; }

.skew-row { display: flex; align-items: center; gap: 6px; margin: 3px 0; }
.skew-label { width: 32px; font-size: 0.65rem; color: #8B949E; font-weight: 600; }
.skew-track { flex: 1; height: 14px; background: #21262D; border-radius: 4px; position: relative; overflow: hidden; }
.skew-fill { height: 100%; border-radius: 4px; transition: width 0.4s ease; }
.skew-value { width: 36px; font-size: 0.65rem; color: #E6EDF3; font-weight: 700; text-align: right; font-variant-numeric: tabular-nums; }

.gex-track { position: relative; height: 18px; background: #21262D; border-radius: 4px; overflow: hidden; display: flex; align-items: center; }
.gex-center { position: absolute; left: 50%; top: 0; bottom: 0; width: 1px; background: #8B949E; opacity: 0.3; }

.stTabs [data-baseweb="tab-list"] { gap: 2px !important; margin-bottom: 5px !important; }
.stTabs [data-baseweb="tab"] { padding: 4px 10px !important; font-size: 0.78rem !important; font-weight: 600 !important; border-radius: 6px 6px 0 0 !important; }
[data-testid="stExpander"] { border: 1px solid #30363D !important; border-radius: 8px !important; margin-bottom: 5px !important; }
[data-testid="stExpander"] > details > summary { padding: 7px 10px !important; font-size: 0.78rem !important; font-weight: 600 !important; }
[data-testid="stSidebar"] .block-container { padding-top: 0.6rem !important; }

.narrative-card { background: #161B22; border-left: 3px solid #58A6FF; border-radius: 8px; padding: 10px 14px; margin: 6px 0; }
.narrative-headline { font-size: 0.85rem; font-weight: 600; color: #E6EDF3; line-height: 1.4; }
.narrative-sub { font-size: 0.7rem; color: #8B949E; margin-top: 4px; }

.metric-grid-card { background: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 10px 12px; }
.metric-grid-title { font-size: 0.6rem; color: #8B949E; text-transform: uppercase; letter-spacing: 0.6px; font-weight: 600; margin-bottom: 4px; }
.metric-grid-value { font-size: 1.05rem; font-weight: 700; color: #E6EDF3; }
.metric-grid-sub { font-size: 0.65rem; color: #8B949E; margin-top: 2px; }

.compass-container { background: #161B22; border: 1px solid #30363D; border-radius: 10px; padding: 12px 14px; margin: 6px 0; }
.compass-title { font-size: 0.75rem; color: #8B949E; text-transform: uppercase; letter-spacing: 0.6px; font-weight: 600; }
.compass-quad { font-size: 1.2rem; font-weight: 800; letter-spacing: -1px; }
.compass-sub { font-size: 0.7rem; color: #8B949E; }

.dp-row { display: flex; align-items: center; gap: 8px; padding: 5px 8px; background: #161B22; border-bottom: 1px solid #21262D; font-size: 0.75rem; }
.dp-time { width: 60px; color: #8B949E; font-variant-numeric: tabular-nums; }
.dp-ticker { width: 55px; color: #E6EDF3; font-weight: 700; }
.dp-price { width: 60px; color: #E6EDF3; font-variant-numeric: tabular-nums; }
.dp-size { width: 70px; color: #8B949E; font-variant-numeric: tabular-nums; text-align: right; }
.dp-amt { width: 65px; color: #3FB950; font-weight: 700; font-variant-numeric: tabular-nums; text-align: right; }
.dp-amt.sell { color: #F85149; }

.mm-box { background: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 10px 12px; margin: 4px 0; }
.mm-title { font-size: 0.7rem; color: #A855F7; text-transform: uppercase; font-weight: 600; margin-bottom: 6px; letter-spacing: 0.5px; }
.mm-line { display: flex; justify-content: space-between; font-size: 0.75rem; padding: 2px 0; }
.mm-label { color: #8B949E; }
.mm-value { color: #E6EDF3; font-weight: 600; font-variant-numeric: tabular-nums; }

.skew-curve-container { background: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 10px; margin: 4px 0; }
.skew-curve-title { font-size: 0.7rem; color: #8B949E; text-transform: uppercase; font-weight: 600; margin-bottom: 6px; }
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

class _GipProxy:
    def __init__(self, data):
        self._is_dict = isinstance(data, dict)
        if self._is_dict: self._d = data
        else: self._obj = data
    def __getattr__(self, name):
        if self._is_dict: return self._d.get(name)
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
    except: return None
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

def _sparkline_html(series, width=80, height=24, bars=18):
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
        bars_html += f'<div class="sp-bar-v4" style="height:{pct}%;background:{color};"></div>'
    return f'<div class="tc-v4-spark" style="width:{width}px;height:{height}px;display:flex;align-items:flex-end;gap:1px;">{bars_html}</div>'

def _risk_range_html(px, lrr, trr, width_pct=100):
    if not all(v is not None and math.isfinite(float(v)) for v in [px, lrr, trr]):
        return '<div class="rr-track-v4" style="height:16px;background:#21262D;border-radius:4px;"></div><div class="rr-labels-v4"><span>-</span><span>-</span></div>'
    px, lrr, trr = float(px), float(lrr), float(trr)
    spread = trr - lrr
    pos = max(0, min(1, (px - lrr) / spread)) if spread > 0 else 0.5
    left_pct = pos * 100
    color = "#3FB950" if pos <= 0.35 else "#F85149" if pos >= 0.65 else "#8B949E"
    return (
        f'<div class="rr-track-v4" style="width:{width_pct}%;">'
        f'<div class="rr-zone-v4" style="left:0%;width:100%;background:#21262D;"></div>'
        f'<div class="rr-zone-v4" style="left:0%;width:{left_pct:.0f}%;background:{color}15;"></div>'
        f'<div class="rr-dot-v4" style="left:{max(3,min(97,left_pct)):.0f}%;border-color:{color};"></div>'
        f'</div>'
        f'<div class="rr-labels-v4" style="width:{width_pct}%;"><span>{ff(lrr)}</span><span>{ff(px)}</span><span>{ff(trr)}</span></div>'
    )

def _gauge_html(value, max_val=100, color=None, height=12, label_left="0", label_right="100"):
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
    cls = {"long":"badge-long","short":"badge-short","neut":"badge-neut","a":"badge-grade-a","b":"badge-grade-b","c":"badge-grade-c","news":"badge-news","mm":"badge-mm"}.get(kind,"badge-neut")
    return f'<span class="badge {cls}">{text}</span>'

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
    nodes = ""; labels = ""
    for i, s in enumerate(stages):
        cls = "past" if i < idx else "active" if i == idx else ""
        line_cls = "active" if i < idx else ""
        nodes += f'<div class="tl-node {cls}"></div>'
        if i < len(stages) - 1: nodes += f'<div class="tl-line {line_cls}"></div>'
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
        return '<div class="gex-track" style="height:18px;background:#21262D;border-radius:4px;"></div>'
    v = float(gex_val)
    color = "#3FB950" if v > 0 else "#F85149"
    pct = min(100, abs(v) * 100)
    side = "Pos" if v > 0 else "Neg"
    margin = "margin-left:0;left:50%;" if v > 0 else f"margin-left:-{pct}%;left:50%;"
    return (
        f'<div class="gex-track" style="height:18px;">'
        f'<div class="gex-center"></div>'
        f'<div style="position:absolute;{margin}width:{pct:.0f}%;background:{color}25;height:100%;border-radius:4px;"></div>'
        f'<div style="position:absolute;width:100%;text-align:center;font-size:0.6rem;font-weight:700;color:{color};line-height:18px;">{side} {abs(v):.2f}</div>'
        f'</div>'
    )

def _heatmap_grid_html(items, key_label="name", key_quad="quad"):
    html = '<div class="hm-grid">'
    for it in items:
        q = it.get(key_quad, "Q3")
        color = _quad_color(q)
        name = it.get(key_label, "-")
        html += f'<div class="hm-cell" style="background:{color}15;border-color:{color}35;">{name}<div style="font-size:0.52rem;color:{color};margin-top:1px;">{q}</div></div>'
    html += '</div>'
    return html

def _asset_pulse_box_h(label, ret, sub=""):
    c = _ret_color(ret)
    txt = f"{ret:+.1%}" if ret is not None else "-"
    sub_html = f'<div style="font-size:0.52rem;color:#8B949E;margin-top:1px;">{sub}</div>' if sub else ""
    return f'<div class="pulse-hbox" style="background:{c}12;border-color:{c}25;"><div>{txt}</div><div class="pulse-hlabel">{label}</div>{sub_html}</div>'

# ═══════════════════════════════════════════════════════════════════
# OPTIONS / GREEKS / MM DATA ENRICHMENT
# ═══════════════════════════════════════════════════════════════════
def _get_options_data(ticker, snap):
    out = {
        "max_pain": None, "put_wall": None, "call_wall": None,
        "gamma_flip_up": None, "gamma_flip_down": None, "gamma_regime": None,
        "gex": None, "vanna": None, "charm": None,
        "skew_30d": None, "skew_60d": None, "skew_90d": None,
        "pin_risk": None, "expected_move_pct": None,
        "oi_call": None, "oi_put": None, "pc_ratio": None,
        "iv_rank": None, "iv_percentile": None,
        "mm_positioning": "NEUTRAL", "mm_recommendation": "—",
        "source": "PROXY", "next_expiry": None, "days_to_expiry": None,
    }
    yf = snap.get("yfinance_options", {}).get(ticker, {}) if isinstance(snap.get("yfinance_options"), dict) else {}
    if isinstance(yf, dict) and yf.get("ok"):
        out["max_pain"] = yf.get("max_pain")
        out["put_wall"] = yf.get("put_wall")
        out["call_wall"] = yf.get("call_wall")
        out["gamma_flip_up"] = yf.get("gamma_flip_up")
        out["gamma_flip_down"] = yf.get("gamma_flip_down")
        out["gamma_regime"] = yf.get("gamma_regime")
        out["pc_ratio"] = yf.get("put_call_ratio")
        out["source"] = "YF"
        if yf.get("next_expiry"):
            out["next_expiry"] = yf.get("next_expiry")
        if yf.get("days_to_expiry"):
            out["days_to_expiry"] = yf.get("days_to_expiry")
    greeks = snap.get("greeks_data", {}).get(ticker, {}) if isinstance(snap.get("greeks_data"), dict) else {}
    if isinstance(greeks, dict):
        out["gex"] = greeks.get("net_gex") or greeks.get("gex")
        out["vanna"] = greeks.get("vanna")
        out["charm"] = greeks.get("charm")
        out["skew_30d"] = greeks.get("skew_30d") or greeks.get("skew")
    gamma = snap.get("gamma_data", {}).get(ticker, {}) if isinstance(snap.get("gamma_data"), dict) else {}
    if isinstance(gamma, dict):
        if not out["gamma_regime"]: out["gamma_regime"] = gamma.get("regime")
        if not out["max_pain"]: out["max_pain"] = gamma.get("max_pain")
    gex = snap.get("gex_data", {}).get(ticker, {}) if isinstance(snap.get("gex_data"), dict) else {}
    if isinstance(gex, dict):
        if not out["gex"]: out["gex"] = gex.get("net_gex") or gex.get("gex") or gex.get("total_gex")
    vanna = snap.get("vanna_data", {}).get(ticker, {}) if isinstance(snap.get("vanna_data"), dict) else {}
    if isinstance(vanna, dict):
        if not out["vanna"]: out["vanna"] = vanna.get("vanna")
    charm = snap.get("charm_data", {}).get(ticker, {}) if isinstance(snap.get("charm_data"), dict) else {}
    if isinstance(charm, dict):
        if not out["charm"]: out["charm"] = charm.get("charm")
    skew = snap.get("skew_term", {}).get("skew_data", {}) if isinstance(snap.get("skew_term"), dict) else {}
    if isinstance(skew, dict):
        for k, v in skew.items():
            if isinstance(v, dict):
                val = v.get("skew") or v.get("value") or v.get("90_10")
                if ticker in str(k).upper() or (ticker.replace("-","") in str(k).upper()):
                    if "30" in str(k).lower() or "1m" in str(k).lower(): out["skew_30d"] = _safe_float(val)
                    if "60" in str(k).lower() or "2m" in str(k).lower(): out["skew_60d"] = _safe_float(val)
                    if "90" in str(k).lower() or "3m" in str(k).lower(): out["skew_90d"] = _safe_float(val)
    odte = snap.get("odte_monitor", {}).get("tickers", {}).get(ticker, {}) if isinstance(snap.get("odte_monitor"), dict) else {}
    if isinstance(odte, dict):
        out["pin_risk"] = odte.get("pin_risk")
        out["vanna"] = odte.get("vanna") or out["vanna"]
        out["charm"] = odte.get("charm") or out["charm"]
    vrp = snap.get("vrp_scanner", {}) if isinstance(snap.get("vrp_scanner"), dict) else {}
    if isinstance(vrp, dict) and vrp.get("ok"):
        for item in vrp.get("high_vrp_sell_premium", []):
            if isinstance(item, dict) and item.get("ticker") == ticker:
                out["iv_rank"] = item.get("iv_rank")
                out["expected_move_pct"] = item.get("expected_move_pct")
        for item in vrp.get("low_vrp_buy_premium", []):
            if isinstance(item, dict) and item.get("ticker") == ticker:
                out["iv_rank"] = item.get("iv_rank")

    # ── More engine fallbacks ──
    cem = snap.get("cem_karsan_universal", {}) if isinstance(snap.get("cem_karsan_universal"), dict) else {}
    if isinstance(cem, dict):
        for item in cem.get("per_ticker", {}).values() if isinstance(cem.get("per_ticker"), dict) else []:
            if isinstance(item, dict) and item.get("ticker") == ticker:
                if not out["skew_30d"]: out["skew_30d"] = _safe_float(item.get("skew_30d") or item.get("skew"))
                if not out["gex"]: out["gex"] = _safe_float(item.get("gex") or item.get("net_gex"))
                if not out["vanna"]: out["vanna"] = item.get("vanna")
                if not out["charm"]: out["charm"] = item.get("charm")
                if not out["gamma_regime"]: out["gamma_regime"] = item.get("gamma_regime")
                if not out["max_pain"]: out["max_pain"] = _safe_float(item.get("max_pain"))
                if not out["expected_move_pct"]: out["expected_move_pct"] = _safe_float(item.get("expected_move"))

    spot = snap.get("spotgamma_scanner", {}) if isinstance(snap.get("spotgamma_scanner"), dict) else {}
    if isinstance(spot, dict) and spot.get("ok"):
        pt = spot.get("per_ticker_proxy_gex", {}) if isinstance(spot.get("per_ticker_proxy_gex"), dict) else {}
        if ticker in pt and isinstance(pt[ticker], dict):
            if not out["gex"]: out["gex"] = _safe_float(pt[ticker].get("gex") or pt[ticker].get("net_gex") or pt[ticker].get("total_gex"))
            if not out["gamma_regime"]: out["gamma_regime"] = pt[ticker].get("gamma_regime")
            if not out["max_pain"]: out["max_pain"] = _safe_float(pt[ticker].get("max_pain"))

    karsan = snap.get("karsan_scanner", {}) if isinstance(snap.get("karsan_scanner"), dict) else {}
    if isinstance(karsan, dict) and karsan.get("ok"):
        for item in karsan.get("per_ticker", {}).values() if isinstance(karsan.get("per_ticker"), dict) else []:
            if isinstance(item, dict) and item.get("ticker") == ticker:
                if not out["skew_30d"]: out["skew_30d"] = _safe_float(item.get("skew") or item.get("skew_30d"))
                if not out["expected_move_pct"]: out["expected_move_pct"] = _safe_float(item.get("expected_move"))

    aft = snap.get("afternoon_data", {}) if isinstance(snap.get("afternoon_data"), dict) else {}
    if isinstance(aft, dict) and ticker in aft:
        a = aft[ticker]
        if isinstance(a, dict):
            if not out["vanna"]: out["vanna"] = a.get("vanna")
            if not out["charm"]: out["charm"] = a.get("charm")

    struct = snap.get("structure_data", {}) if isinstance(snap.get("structure_data"), dict) else {}
    if isinstance(struct, dict) and ticker in struct:
        s = struct[ticker]
        if isinstance(s, dict):
            if not out["gamma_regime"]: out["gamma_regime"] = s.get("gamma_regime")

    volga = snap.get("volga_data", {}) if isinstance(snap.get("volga_data"), dict) else {}
    if isinstance(volga, dict) and volga.get("ok"):
        vt = volga.get("per_ticker", {}) if isinstance(volga.get("per_ticker"), dict) else {}
        if ticker in vt and isinstance(vt[ticker], dict):
            if not out["skew_30d"]: out["skew_30d"] = _safe_float(vt[ticker].get("skew"))

    px = None
    prices = snap.get("prices", {})
    if ticker in prices:
        try: px = float(pd.to_numeric(pd.Series(prices[ticker]), errors="coerce").dropna().iloc[-1])
        except: pass
    mp = out["max_pain"]
    if px and mp:
        mp_dist = (px - mp) / mp
        out["mp_dist"] = mp_dist
        if abs(mp_dist) < 0.02:
            out["mm_positioning"] = "PINNED"
            out["mm_recommendation"] = "MM pinned — expect range-bound until expiry. Sell straddles or wait for breakout."
        elif mp_dist > 0.03 and out["gamma_regime"] in ("POSITIVE", "DEEP_POSITIVE"):
            out["mm_positioning"] = "CALL_WALL"
            out["mm_recommendation"] = "Price above max pain + positive gamma — MM will sell into rallies. Fade strength above call wall."
        elif mp_dist < -0.03 and out["gamma_regime"] in ("NEGATIVE", "DEEP_NEGATIVE"):
            out["mm_positioning"] = "PUT_WALL"
            out["mm_recommendation"] = "Price below max pain + negative gamma — MM will buy dips. Support at put wall likely holds."
        else:
            out["mm_positioning"] = "TRANSITION"
            out["mm_recommendation"] = "Between walls — directional play valid. Watch vanna/charm for momentum shift."
    else:
        out["mm_positioning"] = "UNKNOWN"
        out["mm_recommendation"] = "Insufficient options data for MM positioning."

    # ── Fallback proxy: fill any missing fields from price action ──
    proxy = _options_proxy_for_ticker_local(ticker, snap.get("prices", {}))
    if proxy:
        for k, v in proxy.items():
            if out.get(k) is None:
                out[k] = v

    return out

def _skew_curve_proxy_html(ticker, options_data, width=300, height=120):
    skew_val = options_data.get("skew_30d") or options_data.get("skew_60d") or 0
    if skew_val is None: skew_val = 0
    if skew_val > 0.05:
        shape = "smirk"; left_h = 85; mid_h = 40; right_h = 25; color = "#F85149"
    elif skew_val < -0.05:
        shape = "reverse_smirk"; left_h = 25; mid_h = 40; right_h = 85; color = "#3FB950"
    else:
        shape = "smile"; left_h = 70; mid_h = 30; right_h = 70; color = "#D29922"
    bars = 15
    bar_width = int(width / bars)
    bars_html = ""
    for i in range(bars):
        x = (i - bars//2) / (bars//2)
        if shape == "smirk": h = int(30 + 55 * math.exp(-x))
        elif shape == "reverse_smirk": h = int(30 + 55 * math.exp(x))
        else: h = int(30 + 55 * (x**2))
        h = max(10, min(95, h))
        bars_html += f'<div style="width:{bar_width-2}px;height:{h}%;background:{color}40;border-radius:2px;opacity:0.8;"></div>'
    return (
        f'<div class="skew-curve-container">'
        f'<div class="skew-curve-title">{ticker} Skew · {shape.replace("_"," ").title()} ({skew_val:+.2f})</div>'
        f'<div style="display:flex;align-items:flex-end;gap:1px;height:{height}px;padding:0 4px;">'
        f'{bars_html}'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;font-size:0.55rem;color:#8B949E;margin-top:2px;">'
        f'<span>OTM Puts</span><span>ATM</span><span>OTM Calls</span></div>'
        f'</div>'
    )

def _build_dark_pool_proxy(snap, prices):
    prints = []
    inst = snap.get("institutional_data", {}) if isinstance(snap.get("institutional_data"), dict) else {}
    if inst.get("per_ticker"):
        for t, data in inst.get("per_ticker", {}).items():
            if not isinstance(data, dict): continue
            if data.get("anomaly_score", 0) > 0.6:
                px = None
                if t in prices:
                    try: px = float(pd.to_numeric(pd.Series(prices[t]), errors="coerce").dropna().iloc[-1])
                    except: pass
                if px:
                    size = int(data.get("volume_anomaly", 0) * 1000)
                    amt = size * px
                    side = "BUY" if data.get("buy_pressure", 0) > data.get("sell_pressure", 0) else "SELL"
                    prints.append({"time": "Live", "ticker": t, "price": px, "size": size, "amount": amt, "side": side})
    fr = snap.get("front_run_candidates", []) or []
    for item in fr[:5]:
        if not isinstance(item, dict): continue
        t = item.get("ticker", "")
        if any(p["ticker"] == t for p in prints): continue
        px = None
        if t in prices:
            try: px = float(pd.to_numeric(pd.Series(prices[t]), errors="coerce").dropna().iloc[-1])
            except: pass
        if px:
            size = 250000
            amt = size * px
            prints.append({"time": "Consensus", "ticker": t, "price": px, "size": size, "amount": amt, "side": "BUY"})
    prints.sort(key=lambda x: x["amount"], reverse=True)
    return prints[:15]

def _get_next_expiry(days_to_add=21):
    """Proxy: next monthly options expiry (3rd Friday) or just +21 days"""
    from datetime import datetime, timedelta
    d = datetime.now() + timedelta(days=days_to_add)
    while d.weekday() != 4:
        d += timedelta(days=1)
    return d.strftime("%b %d")

def _options_proxy_for_ticker_local(ticker, prices):
    """Local fallback when snap options data is empty."""
    s = prices.get(ticker)
    if s is None or (hasattr(s, "__len__") and len(s) < 20):
        return {}
    try:
        s_clean = pd.to_numeric(pd.Series(s), errors="coerce").dropna()
        if len(s_clean) < 20:
            return {}
        px = float(s_clean.iloc[-1])
        sma20 = float(s_clean.tail(20).mean())
        std20 = float(s_clean.tail(20).std())
        if std20 == 0 or not all(math.isfinite(v) for v in [px, sma20, std20]):
            return {}
        max_pain = round(sma20, 2)
        put_wall = round(sma20 - std20 * 2.0, 2)
        call_wall = round(sma20 + std20 * 2.0, 2)
        gamma_flip_up = round(sma20 + std20 * 1.5, 2)
        gamma_flip_down = round(sma20 - std20 * 1.5, 2)
        mp_dist = (px - max_pain) / max_pain if max_pain != 0 else 0
        r5d = float(s_clean.iloc[-1] / s_clean.iloc[-6] - 1) if len(s_clean) >= 6 else 0
        r20d = float(s_clean.iloc[-1] / s_clean.iloc[-21] - 1) if len(s_clean) >= 21 else 0
        if r5d > 0.03 and r20d > 0.05:
            gamma_regime = "DEEP_POSITIVE"
        elif r5d > 0.01 and r20d > 0.02:
            gamma_regime = "POSITIVE"
        elif r5d < -0.03 and r20d < -0.05:
            gamma_regime = "DEEP_NEGATIVE"
        elif r5d < -0.01 and r20d < -0.02:
            gamma_regime = "NEGATIVE"
        else:
            gamma_regime = "TRANSITION"
        returns = s_clean.tail(20).pct_change().dropna()
        skew_val = float(returns.skew()) if len(returns) > 5 else 0.0
        skew_30d = skew_val * 0.5
        gex_proxy = -mp_dist * 5.0
        vanna_proxy = r5d * 10.0
        r11 = float(s_clean.iloc[-6] / s_clean.iloc[-11] - 1) if len(s_clean) >= 11 else r5d
        charm_proxy = (r5d - r11) * 20.0
        vol_20 = float(returns.std() * math.sqrt(252)) if len(returns) > 1 else 0.2
        hist_vol = float(s_clean.tail(60).pct_change().dropna().std() * math.sqrt(252)) if len(s_clean) >= 60 else vol_20
        iv_rank = min(100, max(0, (vol_20 / hist_vol * 50))) if hist_vol > 0 else 50
        expected_move = vol_20 / math.sqrt(12)
        pc_ratio = 0.8 if r20d > 0.05 else (1.2 if r20d < -0.05 else 1.0)
        return {
            "max_pain": max_pain, "put_wall": put_wall, "call_wall": call_wall,
            "gamma_flip_up": gamma_flip_up, "gamma_flip_down": gamma_flip_down,
            "gamma_regime": gamma_regime, "gex": gex_proxy, "vanna": vanna_proxy,
            "charm": charm_proxy, "skew_30d": skew_30d, "skew_60d": skew_30d * 0.8,
            "skew_90d": skew_30d * 0.6, "mp_dist": mp_dist, "iv_rank": iv_rank,
            "expected_move_pct": expected_move, "pc_ratio": pc_ratio,
            "source": "PROXY", "next_expiry": _get_next_expiry(), "days_to_expiry": 21,
        }
    except Exception:
        return {}

def _get_dark_pool_for_ticker(ticker, snap):
    """Get dark pool print for specific ticker from snap."""
    if not snap:
        return None
    inst = snap.get("institutional_data", {}) if isinstance(snap.get("institutional_data"), dict) else {}
    if inst.get("per_ticker"):
        data = inst.get("per_ticker", {}).get(ticker)
        if isinstance(data, dict) and data.get("anomaly_score", 0) > 0.6:
            px = None
            prices = snap.get("prices", {})
            if ticker in prices:
                try: px = float(pd.to_numeric(pd.Series(prices[ticker]), errors="coerce").dropna().iloc[-1])
                except: pass
            if px:
                size = int(data.get("volume_anomaly", 0) * 1000)
                return {"size": size, "price": px, "amount": size * px,
                        "side": "BUY" if data.get("buy_pressure", 0) > data.get("sell_pressure", 0) else "SELL",
                        "time": "Live"}
    fr = snap.get("front_run_candidates", []) or []
    for item in fr:
        if not isinstance(item, dict): continue
        if item.get("ticker") == ticker:
            px = None
            prices = snap.get("prices", {})
            if ticker in prices:
                try: px = float(pd.to_numeric(pd.Series(prices[ticker]), errors="coerce").dropna().iloc[-1])
                except: pass
            if px:
                return {"size": 250000, "price": px, "amount": 250000 * px, "side": "BUY", "time": "Consensus"}
    return None

# ═══════════════════════════════════════════════════════════════════
# RISK RANGE / ROW BUILDERS (ENRICHED WITH OPTIONS)
# ═══════════════════════════════════════════════════════════════════
def _build_row(ticker, prices, ar, vix_now=20, gamma_data=None, greeks_data=None, market_type="us_equity", news=None, snap=None):
    v = ar.get(ticker, {}) if ar else {}
    s = prices.get(ticker)
    if not v and (s is None or len(s) < 15): return None
    if not v and s is not None:
        try:
            s_clean = pd.to_numeric(pd.Series(s), errors="coerce").dropna()
        except: return None
        if len(s_clean) < 15: return None
        px = float(s_clean.iloc[-1])
        sma20 = float(s_clean.tail(20).mean()) if len(s_clean) >= 20 else float(s_clean.mean())
        std20 = float(s_clean.tail(20).std()) if len(s_clean) >= 20 else float(s_clean.std())
        if not all(math.isfinite(v) for v in [px, sma20, std20]) or std20 == 0:
            lrr = round(px * 0.95, 2); trr = round(px * 1.05, 2); comp = "neutral"
        else:
            lrr = round(sma20 - 1.5 * std20, 4); trr = round(sma20 + 1.5 * std20, 4)
            comp = "bullish" if px < lrr else "bearish" if px > trr else "neutral"
        if comp == "neutral":
            r5 = _price_ret(ticker, prices, 5) or 0
            comp = "bullish" if r5 >= 0 else "bearish"
        v = {"px": px, "trade": {"lrr": lrr, "trr": trr}, "composite": comp, "quality": "B", "market": market_type}

    tr = v.get("trade", {})
    px = _safe_float(v.get("px")); lrr = _safe_float(tr.get("lrr")); trr = _safe_float(tr.get("trr"))
    if not px or not lrr or not trr: return None

    composite = v.get("composite", "neutral")
    side = "long" if composite == "bullish" else "short"
    spread = trr - lrr
    pos = (px - lrr) / spread if spread > 0 else 0.5

    options = _get_options_data(ticker, snap) if snap else {}
    mp = options.get("max_pain")
    pw = options.get("put_wall")
    cw = options.get("call_wall")
    gf_up = options.get("gamma_flip_up")
    gf_down = options.get("gamma_flip_down")

    if side == "long":
        entry_candidates = [lrr]
        if pw and pw > lrr: entry_candidates.append(pw)
        if gf_down and gf_down > lrr: entry_candidates.append(gf_down)
        entry = round(min(entry_candidates), 2)
        tp1_candidates = [round(lrr + spread * 0.5, 2)]
        if mp: tp1_candidates.append(round(mp, 2))
        if gf_up: tp1_candidates.append(round(gf_up, 2))
        tp1 = round(max([x for x in tp1_candidates if x > entry], default=round(lrr + spread * 0.5, 2)), 2)
        tp2_candidates = [trr]
        if cw: tp2_candidates.append(cw)
        if gf_up: tp2_candidates.append(gf_up)
        tp2 = round(max(tp2_candidates), 2)
        stop_candidates = [round(lrr - spread * 0.25, 2)]
        if pw: stop_candidates.append(round(pw - spread * 0.1, 2))
        stop = round(min(stop_candidates), 2)
        near_entry = pos <= 0.35
    else:
        entry_candidates = [trr]
        if cw and cw < trr: entry_candidates.append(cw)
        if gf_up and gf_up < trr: entry_candidates.append(gf_up)
        entry = round(max(entry_candidates), 2)
        tp1_candidates = [round(trr - spread * 0.5, 2)]
        if mp: tp1_candidates.append(round(mp, 2))
        if gf_down: tp1_candidates.append(round(gf_down, 2))
        tp1 = round(min([x for x in tp1_candidates if x < entry], default=round(trr - spread * 0.5, 2)), 2)
        tp2_candidates = [lrr]
        if pw: tp2_candidates.append(pw)
        if gf_down: tp2_candidates.append(gf_down)
        tp2 = round(min(tp2_candidates), 2)
        stop_candidates = [round(trr + spread * 0.25, 2)]
        if cw: stop_candidates.append(round(cw + spread * 0.1, 2))
        stop = round(max(stop_candidates), 2)
        near_entry = pos >= 0.65

    rr = round(abs(tp1 - entry) / max(abs(entry - stop), 0.01), 2)
    grade = "A" if near_entry and rr >= 2.0 else "B" if near_entry else "C"

    mm_rec = options.get("mm_recommendation", "—")
    mm_pos = options.get("mm_positioning", "UNKNOWN")
    if mm_pos == "CALL_WALL" and side == "long":
        mm_rec += " ⚠️ Call wall resistance — consider taking profit at call wall."
    elif mm_pos == "PUT_WALL" and side == "short":
        mm_rec += " ⚠️ Put wall support — consider covering at put wall."
    elif mm_pos == "PINNED":
        mm_rec += " 🔄 Pinned — directional edge low. Prefer range strategies."

    news_signal = ""; news_headline = ""; news_sentiment = 0
    if news and isinstance(news, dict) and news.get("ticker_specific"):
        tn = news["ticker_specific"].get(ticker, {})
        if isinstance(tn, dict):
            news_signal = tn.get("front_run_signal", "")
            news_headline = (tn.get("headlines") or [""])[0] if tn else ""
            news_sentiment = tn.get("sentiment_score", 0) or 0

    return {
        "ticker": ticker, "price": px, "entry": entry, "target_1": tp1, "target_2": tp2,
        "stop": stop, "rr": rr, "direction": "LONG" if side == "long" else "SHORT", "grade": grade,
        "near_entry": near_entry, "pos_in_range": round(pos, 2), "side": side,
        "trade_l": lrr, "trade_r": trr, "r1m": _price_ret(ticker, prices, 21), "r3m": _price_ret(ticker, prices, 63),
        "composite": composite, "market_type": market_type,
        "options": options,
        "mm_positioning": mm_pos, "mm_recommendation": mm_rec,
        "news_signal": news_signal, "news_headline": news_headline, "news_sentiment": news_sentiment,
    }

def _build_ihsg_row(ticker, prices, ar, **kwargs):
    row = _build_row(ticker, prices, ar, market_type="ihsg", **kwargs)
    if not row: return None
    row["direction"] = "LONG"
    sector = IHSG_SECTOR_MAP.get(ticker, "Indonesia")
    row["sector"] = sector
    r1m = row.get("r1m", 0) or 0
    if r1m > 0.05: row["recommendation"] = f"Strong momentum +{r1m:.1%} — {sector} play"
    elif r1m < -0.05: row["recommendation"] = f"Weak momentum {r1m:.1%} — avoid {sector}"
    else: row["recommendation"] = f"{sector} — range bound, wait breakout"
    return row

def build_ticker_rows(tickers, market_type="us_equity", vix_now=20, gamma_data=None, greeks_data=None, news=None, prices=None, ar=None, snap=None):
    rows = []
    for t in tickers:
        if market_type == "ihsg": r = _build_ihsg_row(t, prices, ar, snap=snap)
        else: r = _build_row(t, prices, ar, vix_now=vix_now, gamma_data=gamma_data, greeks_data=greeks_data, market_type=market_type, news=news, snap=snap)
        if r: rows.append(r)
    return rows

def split_long_short(rows):
    longs = [r for r in rows if "LONG" in r.get("direction", "")]
    shorts = [r for r in rows if "SHORT" in r.get("direction", "")]
    return sorted(longs, key=lambda x: x.get("rr", 0), reverse=True), sorted(shorts, key=lambda x: x.get("rr", 0), reverse=True)

# ═══════════════════════════════════════════════════════════════════
# VISUAL RENDERERS v4
# ═══════════════════════════════════════════════════════════════════
def render_ticker_card_v4(row, expanded=False):
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
    mm_pos = row.get("mm_positioning", "")
    options = row.get("options", {})
    prices_series = None
    if st.session_state.snap is not None:
        prices_series = st.session_state.snap.get("prices", {}).get(ticker)

    dir_kind = "long" if "LONG" in direction else "short" if "SHORT" in direction else "neut"
    dir_label = "LONG" if "LONG" in direction else "SHORT"
    grade_kind = grade.lower().replace("+", "")

    badges = _badge_html(dir_label, dir_kind) + _badge_html(grade, grade_kind)
    if rr_val and rr_val >= 2: badges += _badge_html(f"RR {rr_val}x", "news")
    if news_sig and "BULLISH" in str(news_sig): badges += _badge_html("NEWS+", "news")
    if news_sig and "BEARISH" in str(news_sig): badges += _badge_html("NEWS-", "news")
    if mm_pos and mm_pos != "UNKNOWN": badges += _badge_html(mm_pos, "mm")
    alpha_src = row.get("alpha_source", "")
    alpha_score = row.get("alpha_score", 0)
    if alpha_src:
        src_emoji = {"bottleneck":"🚧","front_run":"🔮","leopold":"🏗️","karsan_squeeze":"📊","karsan_convexity":"📐","coatue":"💱"}.get(alpha_src,"⚡")
        badges += _badge_html(f"{src_emoji} {alpha_src.replace('_',' ').title()}", "mm")
    if alpha_score:
        badges += _badge_html(f"α{alpha_score}", "a" if alpha_score >= 80 else "b" if alpha_score >= 70 else "c")

    spark = _sparkline_html(prices_series, width=80, height=24, bars=18)
    rr_html = _risk_range_html(px, trade_l, trade_r, width_pct=100)

    card_html = (
        f'<div class="ticker-card-v4">'
        f'<div class="tc-v4-left"><div class="tc-v4-symbol">{ticker}</div><div class="tc-v4-price">{ff(px)}</div><div class="tc-v4-badges">{badges}</div></div>'
        f'{spark}'
        f'<div class="tc-v4-rr">{rr_html}</div>'
        f'<div class="tc-v4-meta"><div>Entry {ff(entry)}</div><div>RR {ff(rr_val)}x</div><div>1M {fp(r1m)}</div></div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    with st.expander("🎯 Trade Setup", expanded=expanded):
        # Alpha thesis if present
        alpha_thesis = row.get("alpha_thesis", "")
        alpha_src = row.get("alpha_source", "")
        if alpha_thesis:
            src_emoji = {"bottleneck":"🚧","front_run":"🔮","leopold":"🏗️","karsan_squeeze":"📊","karsan_convexity":"📐","coatue":"💱"}.get(alpha_src,"⚡")
            st.markdown(f'<div style="font-size:0.78rem;color:#E6EDF3;margin-bottom:6px;padding:6px 8px;background:#161B22;border-left:3px solid #A855F7;border-radius:4px;"><b>{src_emoji} {alpha_src.replace("_"," ").title()} Thesis:</b> {alpha_thesis}</div>', unsafe_allow_html=True)
        # Basis explanation
        basis_html = '<div style="font-size:0.7rem;color:#8B949E;margin-bottom:8px;">'
        basis_parts = []
        if options.get("max_pain"): basis_parts.append(f"Max Pain {ff(options['max_pain'])}")
        if options.get("put_wall"): basis_parts.append(f"Put Wall {ff(options['put_wall'])}")
        if options.get("call_wall"): basis_parts.append(f"Call Wall {ff(options['call_wall'])}")
        if row.get("trade_l"): basis_parts.append(f"LRR {ff(row['trade_l'])}")
        if row.get("trade_r"): basis_parts.append(f"TRR {ff(row['trade_r'])}")
        if basis_parts:
            basis_html += "Basis: " + " · ".join(basis_parts)
        basis_html += '</div>'
        st.markdown(basis_html, unsafe_allow_html=True)

        st.markdown(
            f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:8px 12px;margin:4px 0;">'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:0.74rem;color:#8B949E;">'
            f'<div>📍 <b>Entry:</b> {ff(entry)}</div><div>🎯 <b>Target 1:</b> {ff(t1)}</div>'
            f'<div>🎯 <b>Target 2:</b> {ff(t2)}</div><div>🛑 <b>Stop Loss:</b> {ff(stop)}</div>'
            f'</div>'
            f'<div style="margin-top:6px;padding-top:6px;border-top:1px solid #30363D;font-size:0.74rem;color:#E6EDF3;">'
            f'💡 <b>Rekomendasi:</b> {row.get("recommendation", row.get("thesis", "Tunggu setup dekat entry level dengan RR minimal 2x."))}'
            f'</div></div>',
            unsafe_allow_html=True
        )

        # MM Positioning Box
        if mm_pos and mm_pos != "UNKNOWN":
            st.markdown(
                f'<div class="mm-box">'
                f'<div class="mm-title">🧠 Market Maker Positioning</div>'
                f'<div class="mm-line"><span class="mm-label">Position</span><span class="mm-value" style="color:{"#3FB950" if mm_pos=="PUT_WALL" else "#F85149" if mm_pos=="CALL_WALL" else "#D29922"};">{mm_pos}</span></div>'
                f'<div class="mm-line"><span class="mm-label">Max Pain Dist</span><span class="mm-value">{options.get("mp_dist",0):+.1%}</span></div>'
                f'<div style="margin-top:6px;padding-top:6px;border-top:1px solid #30363D;font-size:0.72rem;color:#A855F7;">'
                f'{row.get("mm_recommendation", "—")}'
                f'</div></div>',
                unsafe_allow_html=True
            )

        # Dark Pool for this ticker
        market_type = row.get("market_type", "us_equity")
        show_options = market_type != "ihsg"
        if show_options:
            dp = _get_dark_pool_for_ticker(ticker, st.session_state.snap)
            if dp:
                st.markdown(
                    f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:8px 12px;margin:4px 0;">'
                    f'<div style="font-size:0.65rem;color:#A855F7;text-transform:uppercase;font-weight:600;margin-bottom:4px;">🌑 Dark Pool Print</div>'
                    f'<div style="display:flex;justify-content:space-between;font-size:0.72rem;color:#E6EDF3;">'
                    f'<span>{dp.get("side","—")} {dp.get("size",0):,.0f} @ ${ff(dp.get("price"))}</span>'
                    f'<span style="color:#3FB950;font-weight:700;">${dp.get("amount",0)/1e6:.1f}M</span></div></div>',
                    unsafe_allow_html=True
                )

        # Options detail columns
        if show_options and (options.get("gamma_regime") or options.get("max_pain")):
            o1, o2, o3, o4, o5 = st.columns(5)
            o1.metric("Gamma", options.get("gamma_regime", "-"))
            o2.metric("Max Pain", ff(options.get("max_pain")))
            o3.metric("Put Wall", ff(options.get("put_wall")))
            o4.metric("Call Wall", ff(options.get("call_wall")))
            expiry_text = f"{options.get('days_to_expiry','—')}D" if options.get('days_to_expiry') else "—"
            expiry_date = options.get("next_expiry", "")
            if expiry_date and options.get("days_to_expiry"):
                o5.metric("Expiry", f"{expiry_date} ({expiry_text})")
            else:
                o5.metric("Expiry", expiry_text)

        # Skew Curve Proxy
        if show_options and (options.get("skew_30d") is not None or options.get("skew_60d") is not None):
            st.markdown(_skew_curve_proxy_html(ticker, options, width=300, height=100), unsafe_allow_html=True)

        # Greeks mini
        if show_options and (options.get("gex") is not None or options.get("vanna") is not None or options.get("charm") is not None):
            g1, g2, g3 = st.columns(3)
            g1.metric("GEX", f"{options.get('gex',0):+.2f}" if options.get('gex') is not None else "-")
            g2.metric("Vanna", str(options.get("vanna","-"))[:10])
            g3.metric("Charm", str(options.get("charm","-"))[:10])

        if row.get("news_headline"):
            st.markdown(f'<div style="font-size:0.72rem;color:#58A6FF;margin-top:3px;">📰 {row.get("news_headline")[:120]}</div>', unsafe_allow_html=True)

def render_ticker_cards_v4(rows, max_rows=30):
    if not rows:
        st.info("No setups pass filter.")
        return
    st.markdown(f'<div style="font-size:0.72rem;color:#8B949E;margin-bottom:4px;">Showing {min(len(rows), max_rows)} of {len(rows)} setups</div>', unsafe_allow_html=True)
    for i, r in enumerate(rows[:max_rows]):
        render_ticker_card_v4(r, expanded=(i < 2))

# ═══════════════════════════════════════════════════════════════════
# REGIME COMPASS
# ═══════════════════════════════════════════════════════════════════
def render_regime_compass(snap):
    gip_local = snap.get("gip")
    if gip_local is not None and not isinstance(gip_local, dict): gip_local = _GipProxy(gip_local)
    elif isinstance(gip_local, dict): gip_local = _GipProxy(gip_local)
    else: return

    q_probs = getattr(gip_local, "structural_probs", {}) or {}
    m_probs = getattr(gip_local, "monthly_probs", {}) or {}
    sq = getattr(gip_local, "structural_quad", "Q3") or "Q3"
    mq = getattr(gip_local, "monthly_quad", "Q2") or "Q2"

    markov = snap.get("markov_v3", {}) or {}
    markov_regime = markov.get("current_regime", "UNKNOWN") if isinstance(markov, dict) else "UNKNOWN"
    markov_conf = markov.get("confidence", 0) if isinstance(markov, dict) else 0
    markov_kelly = markov.get("kelly_fraction", 0.25) if isinstance(markov, dict) else 0.25
    cp_alert = markov.get("change_point_alert", False) if isinstance(markov, dict) else False

    rf = snap.get("regime_forecast", {})
    rf3 = rf.get("3m", {}) if isinstance(rf, dict) else {}
    fq = rf3.get("predicted_quad", "Q3") if isinstance(rf3, dict) else "Q3"
    fc = rf3.get("prediction_confidence", 0) if isinstance(rf3, dict) else 0

    c1, c2 = st.columns([1, 1.6])
    with c1:
        sq_color = _quad_color(sq); mq_color = _quad_color(mq)
        markov_color = "#58A6FF" if "BULL" in str(markov_regime).upper() else "#F85149" if "BEAR" in str(markov_regime).upper() else "#D29922"
        cp_badge = '<span style="background:#F8514922;color:#F85149;padding:1px 5px;border-radius:4px;font-size:0.6rem;font-weight:700;border:1px solid #F85149;margin-left:6px;">⚠ CP</span>' if cp_alert else ""
        st.markdown(
            f'<div class="compass-container">'
            f'<div style="display:flex;gap:10px;align-items:center;margin-bottom:8px;">'
            f'<div style="text-align:center;min-width:70px;"><div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;font-weight:600;">Structural</div>'
            f'<div class="compass-quad" style="color:{sq_color};">{sq}</div><div class="compass-sub">{_quad_name(sq)}</div></div>'
            f'<div style="width:1px;height:36px;background:#30363D;"></div>'
            f'<div style="text-align:center;min-width:70px;"><div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;font-weight:600;">Monthly</div>'
            f'<div class="compass-quad" style="color:{mq_color};">{mq}</div><div class="compass-sub">{_quad_name(mq)}</div></div>'
            f'<div style="width:1px;height:36px;background:#30363D;"></div>'
            f'<div style="flex:1;"><div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;font-weight:600;">Markov {cp_badge}</div>'
            f'<div style="font-size:1.05rem;font-weight:700;color:{markov_color};margin-top:2px;">{str(markov_regime).replace("_"," ")}</div>'
            f'<div class="compass-sub">Conf {markov_conf:.0%} · Kelly {markov_kelly:.0%}</div></div>'
            f'</div>'
            f'{_gauge_html(markov_conf*100, max_val=100, color=markov_color, height=10, label_left="0%", label_right="100%")}'
            f'</div>', unsafe_allow_html=True
        )
    with c2:
        fig = go.Figure()
        quads = ["Q1","Q2","Q3","Q4"]; colors = [_quad_color(q) for q in quads]
        q_vals = [q_probs.get(q, 0) if isinstance(q_probs, dict) else 0 for q in quads]
        m_vals = [m_probs.get(q, 0) if isinstance(m_probs, dict) else 0 for q in quads]
        f_vals = [fc if q == fq else (1-fc)/3 for q in quads]
        fig.add_trace(go.Bar(name="Structural", x=quads, y=q_vals, marker_color=colors, opacity=1.0,
                             text=[f"{v:.0%}" for v in q_vals], textposition="outside", textfont=dict(size=10, color="#E6EDF3"), showlegend=True))
        fig.add_trace(go.Bar(name="Monthly", x=quads, y=m_vals, marker_color=colors, opacity=0.55,
                             text=[f"{v:.0%}" for v in m_vals], textposition="outside", textfont=dict(size=9, color="#8B949E"), showlegend=True))
        fig.add_trace(go.Bar(name="Forward 3M", x=quads, y=f_vals, marker_color=colors, opacity=0.25,
                             text=[f"{v:.0%}" for v in f_vals], textposition="outside", textfont=dict(size=8, color="#484F58"), showlegend=True))
        fig.update_layout(height=160, margin=dict(t=10,b=20,l=20,r=20), paper_bgcolor="#0D1117", plot_bgcolor="#0D1117",
                          font=dict(color="#E6EDF3", size=10, family="Inter"),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
                          yaxis=dict(range=[0,1.15], tickformat=".0%", showgrid=True, gridcolor="#21262D", dtick=0.25),
                          barmode="group", bargap=0.35, bargroupgap=0.1)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="regime_compass_bars")

# ═══════════════════════════════════════════════════════════════════
# SESSION & SIDEBAR
# ═══════════════════════════════════════════════════════════════════
if "snap" not in st.session_state: st.session_state.snap = None
if "loading" not in st.session_state: st.session_state.loading = False
if "mq_override" not in st.session_state: st.session_state.mq_override = "Auto"

with st.sidebar:
    st.markdown("## 📊 MacroRegime Pro")
    st.caption("v32.1 FIX | Deep Options")
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
        if _g is not None and not isinstance(_g, dict): _g = _GipProxy(_g)
        elif isinstance(_g, dict): _g = _GipProxy(_g)
        _sq = getattr(_g, "structural_quad", "—") if _g is not None else "—"
        _mq = getattr(_g, "monthly_quad", "—") if _g is not None else "—"
        color = _quad_color(_sq)
        st.markdown(f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:10px;text-align:center;">'
                    f'<div style="font-size:0.6rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.5px;">REGIME</div>'
                    f'<div style="font-size:1rem;font-weight:700;color:{color};margin:4px 0;">{_sq} / {_mq}</div>'
                    f'<div style="font-size:0.65rem;color:#8B949E;">{_quad_name(_sq)}</div></div>', unsafe_allow_html=True)

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
            st.session_state.snap = snap; st.session_state.loading = False; pb.empty(); pt.empty(); st.rerun()
        except Exception as e:
            st.session_state.loading = False; st.error(f"Build failed: {e}"); st.stop()

if not snap or not snap.get("ok"):
    st.error("Build failed. Click Rebuild to retry."); st.stop()

gip_raw = snap.get("gip")
if gip_raw is not None and not isinstance(gip_raw, dict): gip = _GipProxy(gip_raw)
elif isinstance(gip_raw, dict): gip = _GipProxy(gip_raw)
else: gip = None
prices = snap.get("prices", {}) or {}
rr = snap.get("risk_ranges", {}) or {}
ar = rr.get("asset_ranges", {}) if isinstance(rr, dict) else {}
sq = getattr(gip, "structural_quad", None) or "Q3" if gip is not None else "Q3"
mq_raw = getattr(gip, "monthly_quad", None) or "Q2" if gip is not None else "Q2"
mq = st.session_state.mq_override if st.session_state.mq_override != "Auto" else mq_raw

_vix_raw = prices.get("^VIX")
vix_now = 20.0
if _vix_raw is not None:
    try:
        if hasattr(_vix_raw, "tail"): vix_now = _safe_float(_vix_raw.tail(1)) or 20.0
        elif hasattr(_vix_raw, "__len__") and len(_vix_raw) > 0: vix_now = _safe_float(pd.Series(_vix_raw).iloc[-1]) or 20.0
        else: vix_now = _safe_float(_vix_raw) or 20.0
    except Exception: vix_now = 20.0

# ═══════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════
def page_dashboard():
    st.markdown("## 🏠 Macro Dashboard")
    render_regime_compass(snap)

    narrative = snap.get("narrative", {}) or {}
    macro_nar = (narrative.get("macro_narrative") or {}) if isinstance(narrative, dict) else {}
    if macro_nar.get("headline") or macro_nar.get("narrative"):
        headline = macro_nar.get("headline", macro_nar.get("narrative", ""))
        st.markdown(f'<div class="narrative-card">'
                    f'<div class="narrative-headline">{str(headline)[:180]}{"..." if len(str(headline)) > 180 else ""}</div>'
                    f'<div class="narrative-sub">{macro_nar.get("sub_narrative", "")[:120]}</div></div>', unsafe_allow_html=True)

    st.divider()

    summary = snap.get("summary", {}) or {}
    health = snap.get("health", {}) or {}
    markov = snap.get("markov_v3", {}) or {}
    behavioral = snap.get("behavioral_macro", {}) or {}

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        vix_color = "#3FB950" if vix_now < 18 else "#D29922" if vix_now < 25 else "#F85149"
        st.markdown(f'<div class="metric-grid-card">'
                    f'<div class="metric-grid-title">Volatility (VIX)</div>'
                    f'<div class="metric-grid-value" style="color:{vix_color};">{vix_now:.1f}</div>'
                    f'{_gauge_html(vix_now, max_val=40, color=vix_color, height=8, label_left="Low", label_right="High")}'
                    f'</div>', unsafe_allow_html=True)
    with k2:
        health_score = health.get("composite_score", 50) if isinstance(health, dict) else 50
        hcolor = "#3FB950" if health_score >= 70 else "#D29922" if health_score >= 50 else "#F85149"
        st.markdown(f'<div class="metric-grid-card">'
                    f'<div class="metric-grid-title">Market Health</div>'
                    f'<div class="metric-grid-value" style="color:{hcolor};">{health_score:.0f}</div>'
                    f'{_gauge_html(health_score, max_val=100, color=hcolor, height=8, label_left="Weak", label_right="Strong")}'
                    f'</div>', unsafe_allow_html=True)
    with k3:
        yves = behavioral.get("yves", {}) if isinstance(behavioral, dict) else {}
        alert_level = yves.get("alert_level", "NONE") if isinstance(yves, dict) else "NONE"
        n_alerts = len((snap.get("yves_v2", {}) or {}).get("alerts", [])) if isinstance(snap.get("yves_v2"), dict) else 0
        alert_color = "#F85149" if alert_level in ("HIGH", "CRITICAL") or n_alerts > 2 else "#D29922" if alert_level == "MEDIUM" or n_alerts > 0 else "#3FB950"
        st.markdown(f'<div class="metric-grid-card">'
                    f'<div class="metric-grid-title">Behavioral Alerts</div>'
                    f'<div class="metric-grid-value" style="color:{alert_color};">{n_alerts}</div>'
                    f'<div class="metric-grid-sub">Yves / AAII · {alert_level}</div>'
                    f'</div>', unsafe_allow_html=True)
    with k4:
        kelly = markov.get("kelly_fraction", 0.25) if isinstance(markov, dict) else 0.25
        kelly_color = "#3FB950" if kelly >= 0.5 else "#D29922" if kelly >= 0.25 else "#F85149"
        st.markdown(f'<div class="metric-grid-card">'
                    f'<div class="metric-grid-title">Kelly Fraction</div>'
                    f'<div class="metric-grid-value" style="color:{kelly_color};">{kelly:.0%}</div>'
                    f'<div class="metric-grid-sub">Optimal bet size</div>'
                    f'</div>', unsafe_allow_html=True)

    st.divider()

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("### 📋 Regime Playbook")
        pb = snap.get("playbook", {}) or {}
        if isinstance(pb, dict):
            best = pb.get("best_assets", [])[:6]; worst = pb.get("worst_assets", [])[:6]; strategy = pb.get("strategy", "")
            if strategy: st.markdown(f'<div style="font-size:0.8rem;color:#E6EDF3;line-height:1.5;margin-bottom:8px;">{strategy}</div>', unsafe_allow_html=True)
            if best or worst:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("<div style='font-size:0.65rem; color:#3FB950; text-transform:uppercase; font-weight:600; margin-bottom:3px;'>Overweight</div>", unsafe_allow_html=True)
                    for b in best: st.markdown(f"<div style='font-size:0.78rem; color:#E6EDF3;'>• {b}</div>", unsafe_allow_html=True)
                with c2:
                    st.markdown("<div style='font-size:0.65rem; color:#F85149; text-transform:uppercase; font-weight:600; margin-bottom:3px;'>Underweight</div>", unsafe_allow_html=True)
                    for w in worst: st.markdown(f"<div style='font-size:0.78rem; color:#E6EDF3;'>• {w}</div>", unsafe_allow_html=True)

        st.markdown("### 💼 Allocation")
        allocation = {"Q1": {"long": 75, "short": 5, "cash": 20}, "Q2": {"long": 70, "short": 10, "cash": 20}, "Q3": {"long": 60, "short": 15, "cash": 25}, "Q4": {"long": 50, "short": 20, "cash": 30}}
        alloc = allocation.get(sq, allocation["Q3"])
        st.markdown(_stacked_bar_html(alloc["long"], alloc["short"], alloc["cash"]), unsafe_allow_html=True)

    with right:
        st.markdown("### 🔮 Scenarios")
        scenarios = (narrative.get("scenarios") or {}) if isinstance(narrative, dict) else {}
        if scenarios:
            dom = scenarios.get("dominant_scenario", "base") if isinstance(scenarios, dict) else "base"
            for scen_name in ["bull", "base", "bear"]:
                scen = scenarios.get(scen_name, {}) if isinstance(scenarios, dict) else {}
                p = scen.get("probability", 0) if isinstance(scen, dict) else 0
                color = "#3FB950" if scen_name == "bull" else "#D29922" if scen_name == "base" else "#F85149"
                is_dom = " ★" if dom == scen_name else ""
                st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid #21262D;">'
                            f'<span style="font-size:0.78rem;color:#E6EDF3;">{scen_name.title()}{is_dom}</span>'
                            f'<span style="font-size:0.82rem;font-weight:700;color:{color};">{p:.0%}</span></div>', unsafe_allow_html=True)

        st.markdown("### 🚧 Bottlenecks")
        bottlenecks = ((snap.get("narrative", {}) or {}).get("active_bottlenecks", []) or []) if isinstance(snap.get("narrative"), dict) else []
        if bottlenecks:
            for b in bottlenecks[:3]:
                if not isinstance(b, dict): continue
                st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;font-size:0.78rem;">'
                            f'<span style="color:#E6EDF3;">• {str(b.get("name","")).replace("_"," ").title()}</span>'
                            f'<span style="color:#F85149;font-weight:600;">{len(b.get("beneficiaries",[]))} plays</span></div>', unsafe_allow_html=True)
        else: st.caption("No active bottlenecks")

        dxy_corr = snap.get("dxy_correlation", {}) or {}
        if isinstance(dxy_corr, dict) and dxy_corr.get("strongest_positive_corr"):
            st.markdown("### 💱 DXY Correlation")
            pos = dxy_corr.get("strongest_positive_corr", [])[:2]
            neg = dxy_corr.get("strongest_negative_corr", [])[:2]
            for t, data in pos + neg:
                if not isinstance(data, dict): continue
                corr = data.get("correlation", 0)
                color = "#3FB950" if corr > 0 else "#F85149"
                st.markdown(f'<div style="font-size:0.75rem;color:#8B949E;">{t}: <span style="color:{color};font-weight:700;">{corr:+.2f}</span></div>', unsafe_allow_html=True)

    st.divider()

    # Boom-Bust + Behavioral row
    bb = snap.get("boom_bust", {}) or {}
    stage = bb.get("stage", "INCEPTION") if isinstance(bb, dict) else "INCEPTION"
    reflex = snap.get("reflexivity", {}) or {}
    score = reflex.get("super_bubble_score", 0) if isinstance(reflex, dict) else 0

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🌀 Boom-Bust Stage")
        st.markdown(_timeline_html(stage), unsafe_allow_html=True)
        st.markdown(f'<div style="margin-top:6px;font-size:0.75rem;color:#8B949E;">Super Bubble Score: <span style="color:#E6EDF3;font-weight:700;">{score:.1f}</span>/10</div>', unsafe_allow_html=True)
        st.markdown(_gauge_html(score, max_val=10, color="#D29922", height=8, label_left="0", label_right="10"), unsafe_allow_html=True)
    with c2:
        st.markdown("### 🧠 Behavioral Macro (Yves)")
        yves = behavioral.get("yves", {}) if isinstance(behavioral, dict) else {}
        if isinstance(yves, dict):
            alert = yves.get("alert", "No alert")
            level = yves.get("alert_level", "NONE")
            color = "#F85149" if level in ("HIGH", "CRITICAL") else "#D29922" if level == "MEDIUM" else "#3FB950"
            st.markdown(f'<div style="font-size:0.85rem;color:{color};font-weight:600;">{level}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:0.75rem;color:#8B949E;">{alert}</div>', unsafe_allow_html=True)
        else:
            st.caption("Behavioral macro unavailable")

    st.divider()

    # Asset Pulse
    st.markdown("### ⚡ Asset Pulse (21D)")
    pulse_assets = [("SPY", "US Eq"), ("QQQ", "Tech"), ("IWM", "Small"), ("GLD", "Gold"), ("TLT", "Bonds"), ("UUP", "DXY"), ("BTC-USD", "BTC"), ("ETH-USD", "ETH")]
    pulse_html = '<div style="display:flex;gap:6px;overflow-x:auto;padding:2px 0;">'
    for t, label in pulse_assets:
        ret = _price_ret(t, prices, 21)
        pulse_html += _asset_pulse_box_h(label, ret, t)
    pulse_html += '</div>'
    st.markdown(pulse_html, unsafe_allow_html=True)

    st.divider()

    st.divider()

    with st.expander("🔬 Deep Technical", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Skew Term**")
            skew = snap.get("skew_term", {}) or {}; skew_data = skew.get("skew_data", {}) if isinstance(skew, dict) else {}
            d30 = d60 = d90 = None
            if isinstance(skew_data, dict):
                for k, v in skew_data.items():
                    if isinstance(v, dict):
                        val = v.get("skew") or v.get("value") or v.get("90_10")
                        if "30" in str(k).lower() or "1m" in str(k).lower(): d30 = _safe_float(val)
                        if "60" in str(k).lower() or "2m" in str(k).lower(): d60 = _safe_float(val)
                        if "90" in str(k).lower() or "3m" in str(k).lower(): d90 = _safe_float(val)
            st.markdown(_skew_bars_html(d30, d60, d90), unsafe_allow_html=True)
            st.markdown("**GEX**")
            gex = snap.get("gex_data", {}) or {}; gex_val = None
            if isinstance(gex, dict):
                for k, v in gex.items():
                    if isinstance(v, dict):
                        gv = v.get("net_gex") or v.get("gex") or v.get("total_gex")
                        if gv is not None: gex_val = _safe_float(gv); break
            st.markdown(_gex_bar_html(gex_val), unsafe_allow_html=True)
        with c2:
            st.markdown("**VRP**")
            vrp = snap.get("vrp_scanner", {}) or {}
            if isinstance(vrp, dict) and vrp.get("ok"):
                for item in vrp.get("high_vrp_sell_premium", [])[:3]:
                    if isinstance(item, dict):
                        score = item.get("vrp_pct", 0)
                        st.markdown(f'<div style="display:flex;align-items:center;gap:6px;margin:3px 0;">'
                                    f'<span style="font-size:0.72rem;color:#E6EDF3;min-width:45px;">{item.get("ticker","—")}</span>'
                                    f'<div class="gauge-track" style="flex:1;height:8px;"><div class="gauge-fill" style="width:{min(100,abs(score)*5):.0f}%;background:#F85149;"></div></div>'
                                    f'<span style="font-size:0.65rem;color:#F85149;font-weight:700;width:35px;text-align:right;">{score:.0f}%</span></div>', unsafe_allow_html=True)
            else: st.caption("VRP unavailable")
            st.markdown("**Squeeze**")
            sq_scan = snap.get("squeeze_scanner", {}) or {}
            if isinstance(sq_scan, dict) and sq_scan.get("ok"):
                for item in sq_scan.get("imminent_squeezes", [])[:3]:
                    if isinstance(item, dict):
                        score = item.get("squeeze_score", 0)
                        st.markdown(f'<div style="display:flex;align-items:center;gap:6px;margin:3px 0;">'
                                    f'<span style="font-size:0.72rem;color:#E6EDF3;min-width:45px;">{item.get("ticker","—")}</span>'
                                    f'<div class="gauge-track" style="flex:1;height:8px;"><div class="gauge-fill" style="width:{min(100,score):.0f}%;background:#D29922;"></div></div>'
                                    f'<span style="font-size:0.65rem;color:#D29922;font-weight:700;width:35px;text-align:right;">{score:.0f}</span></div>', unsafe_allow_html=True)
            else: st.caption("Squeeze unavailable")
            st.markdown("**Vol Forecast**")
            vol_f = snap.get("vol_forecast", {}) or {}
            if isinstance(vol_f, dict):
                for k, v in list(vol_f.items())[:3]:
                    if isinstance(v, dict):
                        regime = v.get("vol_regime", "-")
                        color = "#3FB950" if regime == "LOW" else "#D29922" if regime == "NORMAL" else "#F85149"
                        st.markdown(f'<div style="font-size:0.75rem;color:#8B949E;">{k}: <span style="color:{color};font-weight:700;">{v.get("current_ann_vol",0):.1f}%</span> ({regime})</div>', unsafe_allow_html=True)
            else: st.caption("Vol forecast unavailable")
        st.markdown("**Engine Status**")
        engines = [("GIP v10", snap.get("gip_v10") is not None), ("Markov V3", snap.get("markov_v3") is not None), ("Yves v2", snap.get("yves_v2") is not None),
                   ("Cascade", snap.get("cascade_analysis") is not None), ("VRP", snap.get("vrp_scanner") is not None), ("Squeeze", snap.get("squeeze_scanner") is not None),
                   ("Smart Money", snap.get("smart_money") is not None), ("Discovery", snap.get("discovery_brain") is not None)]
        cols = st.columns(4)
        for i, (name, ok) in enumerate(engines):
            color = "#3FB950" if ok else "#F85149"
            cols[i % 4].markdown(f"<span style='color:{color};font-size:0.75rem;'>● {name}</span>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# PAGE: ALPHA CENTER — Bottleneck + Front-Run + Quad Rotation
# ═══════════════════════════════════════════════════════════════════
def page_alpha():
    st.markdown("## ⚡ Alpha Center")
    render_regime_compass(snap)

    summary = snap.get("summary", {}) or {}
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Markov Regime", str(summary.get("v7_markov_regime", "—")).split("_")[0] if summary.get("v7_markov_regime") else "—")
    k2.metric("Smart $ Consensus", summary.get("v7_smart_money_consensus", 0))
    k3.metric("Top Theses", summary.get("v7_top_theses_count", 0))
    k4.metric("Kelly", f"{summary.get('v7_markov_kelly', 0.25):.0%}")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["🏆 Top Picks", "🔮 Front-Run", "📊 Vol & Squeeze", "🧠 Discovery"])

    with tab1:
        # Alpha Center basis: bottleneck + quad rotation + asymmetry
        alpha_candidates = []

        # 1. Bottleneck candidates
        bottleneck = snap.get("bottleneck_v3", {}) or {}
        if isinstance(bottleneck, dict):
            for item in bottleneck.get("active_bottlenecks", []) or []:
                if not isinstance(item, dict): continue
                for t in item.get("beneficiaries", [])[:5]:
                    alpha_candidates.append({"ticker": t, "source": "bottleneck", "score": 85, "thesis": f"Bottleneck: {item.get('name','').replace('_',' ').title()}", "direction": "LONG"})

        # 2. Front-run candidates
        fr = snap.get("front_run_candidates", []) or []
        for item in fr[:15]:
            if not isinstance(item, dict): continue
            alpha_candidates.append({"ticker": item.get("ticker",""), "source": "front_run", "score": 75, "thesis": item.get("why_front_run", "")[:80], "direction": "LONG", "options": item.get("options", {})})

        # 3. Leopold asymmetry setups
        leopold = snap.get("leopold_scan", {}) or {}
        if isinstance(leopold, dict):
            for t in leopold.get("asymmetry_setups", []) or []:
                if isinstance(t, dict):
                    alpha_candidates.append({"ticker": t.get("ticker",""), "source": "leopold", "score": 80, "thesis": t.get("thesis", "Asymmetry setup"), "direction": t.get("direction", "LONG")})

        # 4. Karsan squeeze setups
        karsan = snap.get("karsan_scanner", {}) or {}
        if isinstance(karsan, dict):
            for t in karsan.get("squeeze_setups", []) or []:
                if isinstance(t, dict):
                    alpha_candidates.append({"ticker": t.get("ticker",""), "source": "karsan_squeeze", "score": 78, "thesis": f"Squeeze setup · Score {t.get('squeeze_score',0):.0f}", "direction": "LONG"})
            for t in karsan.get("buy_convexity", []) or []:
                if isinstance(t, dict):
                    alpha_candidates.append({"ticker": t.get("ticker",""), "source": "karsan_convexity", "score": 72, "thesis": "Buy convexity — vol expansion play", "direction": "LONG"})

        # 5. COATUE agentic plays
        coatue = snap.get("coatue_scan", {}) or {}
        if isinstance(coatue, dict):
            for t in coatue.get("agentic_plays", []) or []:
                if isinstance(t, dict):
                    alpha_candidates.append({"ticker": t.get("ticker",""), "source": "coatue", "score": 70, "thesis": t.get("thesis", "Agentic play"), "direction": "LONG"})

        # Deduplicate by ticker, keep highest score
        seen = {}
        for c in alpha_candidates:
            t = c.get("ticker", "")
            if not t: continue
            if t not in seen or c.get("score", 0) > seen[t].get("score", 0):
                seen[t] = c
        alpha_candidates = list(seen.values())
        alpha_candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_alpha = [c for c in alpha_candidates if c.get("score", 0) >= 60][:25]

        if not top_alpha:
            st.info(f"No alpha candidates this snapshot. Total analyzed: {len(alpha_candidates)}. Run orchestrator with all engines enabled.")
        else:
            st.markdown(f"**{len(top_alpha)} alpha candidates** from {len(alpha_candidates)} total (bar: ≥60/100)")
            # Build visual rows for alpha tickers
            alpha_tickers = [c["ticker"] for c in top_alpha if c.get("ticker")]
            alpha_rows = build_ticker_rows(alpha_tickers, "us_equity", vix_now, snap.get("gamma_data"), snap.get("greeks_data"), snap.get("news_narratives"), prices=prices, ar=ar, snap=snap)
            # Enrich with alpha metadata
            for row in alpha_rows:
                c = seen.get(row.get("ticker"), {})
                if c:
                    row["alpha_source"] = c.get("source", "")
                    row["alpha_score"] = c.get("score", 0)
                    row["alpha_thesis"] = c.get("thesis", "")
                    row["direction"] = c.get("direction", row.get("direction", "LONG"))
            # Split long/short and render
            longs, shorts = split_long_short(alpha_rows)
            if longs:
                st.markdown(f"<div style='font-size:0.68rem; color:#3FB950; text-transform:uppercase; font-weight:600; margin:8px 0 4px;'>🟢 Long Setups ({len(longs)})</div>", unsafe_allow_html=True)
                render_ticker_cards_v4(longs, max_rows=20)
            if shorts:
                st.markdown(f"<div style='font-size:0.68rem; color:#F85149; text-transform:uppercase; font-weight:600; margin:8px 0 4px;'>🔴 Short Setups ({len(shorts)})</div>", unsafe_allow_html=True)
                render_ticker_cards_v4(shorts, max_rows=20)

    with tab2:
        st.markdown("### 🔮 Front-Run Candidates")
        fr = snap.get("front_run_candidates", []) or []
        if fr:
            for item in fr[:10]:
                if not isinstance(item, dict): continue
                with st.expander(f"{item.get('ticker','—')} · {item.get('priority','MEDIUM')} · {item.get('source','')}"):
                    st.markdown(f'<div style="font-size:0.78rem;color:#E6EDF3;">{item.get("why_front_run","—")}</div>', unsafe_allow_html=True)
                    if item.get("catalyst"):
                        cat = item["catalyst"]
                        st.markdown(f'<div style="font-size:0.72rem;color:#D29922;margin-top:4px;">Catalyst: {cat.get("event","—")} ({cat.get("quarter","—")})</div>', unsafe_allow_html=True)
                    opt = item.get("options", {})
                    if isinstance(opt, dict) and opt.get("max_pain"):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Max Pain", ff(opt.get("max_pain")))
                        c2.metric("Gamma", opt.get("gamma_regime", "—"))
                        c3.metric("Conviction", opt.get("conviction", "—"))
        else:
            st.info("No front-run candidates this snapshot.")

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 VRP Scanner")
            vrp = snap.get("vrp_scanner", {}) or {}
            if isinstance(vrp, dict) and vrp.get("ok"):
                sell = vrp.get("high_vrp_sell_premium", [])
                buy = vrp.get("low_vrp_buy_premium", [])
                st.metric("Sell Premium", len(sell))
                st.metric("Buy Premium", len(buy))
                if sell:
                    for item in sell[:5]:
                        if isinstance(item, dict):
                            st.markdown(f"• **{item.get('ticker')}** · VRP +{item.get('vrp_pct', 0):.0f}% · IV Rank {item.get('iv_rank', '—')}")
                else: st.caption("No sell premium setups")
            else: st.info("VRP scanner unavailable")
        with col2:
            st.markdown("### 🔥 Squeeze Scanner")
            sq_scan = snap.get("squeeze_scanner", {}) or {}
            if isinstance(sq_scan, dict) and sq_scan.get("ok"):
                imm = sq_scan.get("imminent_squeezes", [])
                strong = sq_scan.get("strong_candidates", [])
                st.metric("Imminent", len(imm))
                st.metric("Strong", len(strong))
                if imm:
                    for item in imm[:5]:
                        if isinstance(item, dict):
                            st.markdown(f"• **{item.get('ticker')}** · Score {item.get('squeeze_score', 0):.0f}/100 · {item.get('tier', '—')}")
                else: st.caption("No imminent squeezes")
            else: st.info("Squeeze scanner unavailable")

    with tab4:
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
        else: st.info("Discovery Brain — no candidates this snapshot")

        st.markdown("### 💰 Position Sizing")
        sizing = snap.get("portfolio_sizing_v2", {}) or {}
        if isinstance(sizing, dict) and sizing.get("positions"):
            st.metric("Deployed", f"{sizing.get('total_deployed_pct', 0):.1%}")
            st.metric("Cash", f"{sizing.get('cash_pct', 0):.1%}")
            df = pd.DataFrame([{"Ticker": p.get("ticker"), "Size %": f"{p.get('target_pct', 0):.2f}%",
                                "Size $": f"{p.get('target_dollar', 0):,.0f}", "Mode": p.get("mode"), "Sector": p.get("sector")}
                               for p in sizing.get("positions", []) if isinstance(p, dict)])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else: st.info("No sized positions yet.")

        conv = snap.get("conviction_sizing", {}) or {}
        if isinstance(conv, dict) and conv.get("positions"):
            st.markdown("### 🎯 Conviction Sizing (Soros)")
            for p in conv.get("positions", [])[:5]:
                if not isinstance(p, dict): continue
                st.markdown(f'<div style="display:flex;justify-content:space-between;font-size:0.78rem;padding:3px 0;">'
                            f'<span style="color:#E6EDF3;">{p.get("ticker","—")}</span>'
                            f'<span style="color:#8B949E;">{p.get("conviction","—")} · {p.get("size_pct",0):.1f}%</span></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# PAGE: US STOCKS — With aggregate options for SPY/QQQ/IWM/GLD/TLT
# ═══════════════════════════════════════════════════════════════════
def page_us_stocks():
    st.markdown("## 🇺🇸 US Stocks")

    playbook = {
        "Q1": {"beli": ["QQQ","XLK","NVDA","AAPL","MSFT","GOOGL","META","AMD","ARKK"], "short": ["XLU","XLP","TLT","GLD"]},
        "Q2": {"beli": ["XLF","XLE","XLI","XLB","KRE","IWM","XOM","CVX"], "short": ["TLT","IEF"]},
        "Q3": {"beli": ["XLE","XLP","XLU","ITA","GLD","SLV","VST","CEG","BE","LITE","CCJ"], "short": ["QQQ","XLK","IWM","ARKK","KRE"]},
        "Q4": {"beli": ["TLT","IEF","GLD","XLU","XLP","XLV"], "short": ["QQQ","XLK","IWM","XLY","XLF","XLE"]},
    }
    pb = playbook.get(sq, playbook["Q3"])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div style='font-size:0.68rem; color:#3FB950; text-transform:uppercase; font-weight:600; margin-bottom:3px;'>Overweight</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.8rem; line-height:1.5;'>" + " · ".join(pb["beli"][:10]) + "</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='font-size:0.68rem; color:#F85149; text-transform:uppercase; font-weight:600; margin-bottom:3px;'>Underweight</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.8rem; line-height:1.5;'>" + " · ".join(pb["short"][:8]) + "</div>", unsafe_allow_html=True)

    # Index ETF visual setups
    st.divider()
    st.markdown("### 📊 Index / ETF Setups (SPY · QQQ · IWM · GLD · TLT)")
    key_etfs = ["SPY", "QQQ", "IWM", "GLD", "TLT"]
    etf_rows = build_ticker_rows(key_etfs, "us_equity", vix_now, snap.get("gamma_data"), snap.get("greeks_data"), snap.get("news_narratives"), prices=prices, ar=ar, snap=snap)
    etf_longs, etf_shorts = split_long_short(etf_rows)
    if etf_longs:
        st.markdown(f"<div style='font-size:0.68rem; color:#3FB950; text-transform:uppercase; font-weight:600; margin-bottom:4px;'>🟢 Long Bias</div>", unsafe_allow_html=True)
        render_ticker_cards_v4(etf_longs, max_rows=10)
    if etf_shorts:
        st.markdown(f"<div style='font-size:0.68rem; color:#F85149; text-transform:uppercase; font-weight:600; margin-bottom:4px;'>🔴 Short Bias</div>", unsafe_allow_html=True)
        render_ticker_cards_v4(etf_shorts, max_rows=10)
    # Fallback: if no rows built (missing price data), show raw options
    if not etf_rows:
        for etf in key_etfs:
            opt = _get_options_data(etf, snap)
            if opt.get("max_pain") or opt.get("gamma_regime"):
                with st.expander(f"{etf} · Gamma: {opt.get('gamma_regime','—')} · Max Pain: {ff(opt.get('max_pain'))}", expanded=False):
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("Max Pain", ff(opt.get("max_pain")))
                    c2.metric("Put Wall", ff(opt.get("put_wall")))
                    c3.metric("Call Wall", ff(opt.get("call_wall")))
                    c4.metric("GEX", f"{opt.get('gex',0):+.2f}" if opt.get('gex') is not None else "-")
                    c5.metric("Expiry", f"{opt.get('days_to_expiry','—')}D")
                    if opt.get("skew_30d") is not None or opt.get("skew_60d") is not None:
                        st.markdown(_skew_curve_proxy_html(etf, opt, width=280, height=90), unsafe_allow_html=True)
                    if opt.get("mm_recommendation"):
                        st.markdown(f'<div style="font-size:0.75rem;color:#A855F7;margin-top:4px;">🧠 {opt["mm_recommendation"]}</div>', unsafe_allow_html=True)

    st.divider()

    us_tickers = list(US_SECTORS.keys()) if US_SECTORS else []
    for bucket in ["Growth","Quality","Defensives","Semis","Energy","Industrials","Financials","AI_Infra","PreciousMetals"]:
        us_tickers += US_BUCKETS.get(bucket, []) if US_BUCKETS else []
    if not us_tickers: us_tickers = FALLBACK_US
    us_tickers = list(dict.fromkeys(us_tickers))

    rows = build_ticker_rows(us_tickers, "us_equity", vix_now, snap.get("gamma_data"), snap.get("greeks_data"), snap.get("news_narratives"), prices=prices, ar=ar, snap=snap)
    longs, shorts = split_long_short(rows)

    st.markdown(f"**{len(rows)} setups** · 🟢 {len(longs)} Long · 🔴 {len(shorts)} Short")
    tab_l, tab_s = st.tabs([f"🟢 Long ({len(longs)})", f"🔴 Short ({len(shorts)}))"])
    with tab_l: render_ticker_cards_v4(longs)
    with tab_s: render_ticker_cards_v4(shorts)

# ═══════════════════════════════════════════════════════════════════
# PAGE: FOREX
# ═══════════════════════════════════════════════════════════════════
def page_forex():
    st.markdown("## 💱 Forex")
    playbook = {
        "Q1": {"beli": ["EURUSD","AUDUSD","EM FX"], "short": ["DXY/UUP"]},
        "Q2": {"beli": ["GBPUSD","CADUSD"], "short": ["JPY"]},
        "Q3": {"beli": ["UUP","CHF"], "short": ["EURUSD","GBPUSD","EM FX"]},
        "Q4": {"beli": ["JPY","CHF"], "short": ["AUDUSD","EM FX"]},
    }
    pb = playbook.get(sq, playbook["Q3"])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div style='font-size:0.68rem; color:#3FB950; text-transform:uppercase; font-weight:600; margin-bottom:3px;'>Buy</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.8rem; line-height:1.5;'>" + " · ".join(pb["beli"]) + "</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='font-size:0.68rem; color:#F85149; text-transform:uppercase; font-weight:600; margin-bottom:3px;'>Short</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.8rem; line-height:1.5;'>" + " · ".join(pb["short"]) + "</div>", unsafe_allow_html=True)
    dxy_corr = snap.get("dxy_correlation", {}) or {}
    if isinstance(dxy_corr, dict) and (dxy_corr.get("strongest_positive_corr") or dxy_corr.get("strongest_negative_corr")):
        st.divider()
        st.markdown("### 💱 DXY Correlation (20D)")
        pos = dxy_corr.get("strongest_positive_corr", [])[:5]
        neg = dxy_corr.get("strongest_negative_corr", [])[:5]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div style='font-size:0.65rem; color:#3FB950; text-transform:uppercase; font-weight:600; margin-bottom:3px;'>Positive</div>", unsafe_allow_html=True)
            for t, data in pos:
                if isinstance(data, dict):
                    st.markdown(f"<div style='font-size:0.78rem; color:#E6EDF3;'>• {t}: <span style='color:#3FB950;font-weight:700;'>{data.get('correlation',0):+.2f}</span></div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div style='font-size:0.65rem; color:#F85149; text-transform:uppercase; font-weight:600; margin-bottom:3px;'>Negative</div>", unsafe_allow_html=True)
            for t, data in neg:
                if isinstance(data, dict):
                    st.markdown(f"<div style='font-size:0.78rem; color:#E6EDF3;'>• {t}: <span style='color:#F85149;font-weight:700;'>{data.get('correlation',0):+.2f}</span></div>", unsafe_allow_html=True)
    st.divider()
    fx_tickers = list(FOREX_PAIRS.keys()) if FOREX_PAIRS else FALLBACK_FX
    rows = build_ticker_rows(fx_tickers, "forex", vix_now, snap.get("gamma_data"), snap.get("greeks_data"), snap.get("news_narratives"), prices=prices, ar=ar, snap=snap)
    longs, shorts = split_long_short(rows)
    st.markdown(f"**{len(rows)} pairs** · 🟢 {len(longs)} Long · 🔴 {len(shorts)} Short")
    tab_l, tab_s = st.tabs([f"🟢 Long ({len(longs)})", f"🔴 Short ({len(shorts)}))"])
    with tab_l: render_ticker_cards_v4(longs)
    with tab_s: render_ticker_cards_v4(shorts)

# ═══════════════════════════════════════════════════════════════════
# PAGE: COMMODITIES
# ═══════════════════════════════════════════════════════════════════
def page_commodities():
    st.markdown("## 🛢️ Commodities")
    playbook = {
        "Q1": {"beli": ["Copper","Industrial Metals"], "short": ["Gold (counter-trend)"]},
        "Q2": {"beli": ["CL=F","USO","XLE","Energy"], "short": []},
        "Q3": {"beli": ["GLD","SLV","CL=F","CCJ","URA"], "short": []},
        "Q4": {"beli": ["GLD","TLT"], "short": ["CL=F","Industrial metals"]},
    }
    pb = playbook.get(sq, playbook["Q3"])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div style='font-size:0.68rem; color:#3FB950; text-transform:uppercase; font-weight:600; margin-bottom:3px;'>Buy</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.8rem; line-height:1.5;'>" + " · ".join(pb["beli"]) + "</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='font-size:0.68rem; color:#F85149; text-transform:uppercase; font-weight:600; margin-bottom:3px;'>Short</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.8rem; line-height:1.5;'>" + (" · ".join(pb["short"]) if pb["short"] else "—") + "</div>", unsafe_allow_html=True)
    st.divider()
    comm_tickers = list(COMMODITIES.keys()) if COMMODITIES else FALLBACK_COMM
    rows = build_ticker_rows(comm_tickers, "commodity", vix_now, snap.get("gamma_data"), snap.get("greeks_data"), snap.get("news_narratives"), prices=prices, ar=ar, snap=snap)
    longs, shorts = split_long_short(rows)
    st.markdown(f"**{len(rows)} commodities** · 🟢 {len(longs)} Long · 🔴 {len(shorts)} Short")
    tab_l, tab_s = st.tabs([f"🟢 Long ({len(longs)})", f"🔴 Short ({len(shorts)}))"])
    with tab_l: render_ticker_cards_v4(longs)
    with tab_s: render_ticker_cards_v4(shorts)

# ═══════════════════════════════════════════════════════════════════
# PAGE: CRYPTO
# ═══════════════════════════════════════════════════════════════════
def page_crypto():
    st.markdown("## ₿ Crypto")
    playbook = {
        "Q1": {"beli": ["BTC","ETH","SOL","alts"], "short": []},
        "Q2": {"beli": ["BTC","MSTR","CORZ","IREN"], "short": []},
        "Q3": {"beli": ["BTC","MSTR","IBIT"], "short": ["alts (ETH/SOL relative)"]},
        "Q4": {"beli": ["BTC (hedge ONLY)"], "short": ["alts","ETH","memecoin"]},
    }
    pb = playbook.get(sq, playbook["Q3"])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div style='font-size:0.68rem; color:#3FB950; text-transform:uppercase; font-weight:600; margin-bottom:3px;'>Buy</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.8rem; line-height:1.5;'>" + " · ".join(pb["beli"]) + "</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='font-size:0.68rem; color:#F85149; text-transform:uppercase; font-weight:600; margin-bottom:3px;'>Short</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.8rem; line-height:1.5;'>" + (" · ".join(pb["short"]) if pb["short"] else "—") + "</div>", unsafe_allow_html=True)
    cc = snap.get("crypto_center", {}) or {}
    if isinstance(cc, dict) and (cc.get("capital_flows") or cc.get("market_structure")):
        st.divider()
        st.markdown("### ₿ On-Chain / Market Structure")
        flows = cc.get("capital_flows", {})
        if isinstance(flows, dict):
            st.markdown(f'<div style="font-size:0.78rem;color:#8B949E;">Stablecoin: <span style="color:#E6EDF3;font-weight:700;">{flows.get("total_b",0):.1f}B</span> ({flows.get("change_7d_b",0):+.1f}B 7D)</div>', unsafe_allow_html=True)
        structure = cc.get("market_structure", {})
        if isinstance(structure, dict) and structure.get("funding"):
            st.markdown("<div style='font-size:0.65rem; color:#8B949E; text-transform:uppercase; font-weight:600; margin-top:6px; margin-bottom:3px;'>Funding Rates</div>", unsafe_allow_html=True)
            for sym, data in list(structure.get("funding", {}).items())[:4]:
                if isinstance(data, dict):
                    rate = data.get("rate", 0)
                    color = "#3FB950" if rate < 0 else "#F85149" if rate > 0.0005 else "#8B949E"
                    st.markdown(f'<div style="font-size:0.75rem;color:#8B949E;">{sym}: <span style="color:{color};font-weight:700;">{rate:.4f}</span></div>', unsafe_allow_html=True)
        narrative_crypto = cc.get("narrative", {})
        if isinstance(narrative_crypto, dict) and narrative_crypto.get("fear_greed"):
            fg = narrative_crypto.get("fear_greed", {})
            st.markdown(f'<div style="margin-top:6px;font-size:0.78rem;color:#8B949E;">Fear & Greed: <span style="color:#E6EDF3;font-weight:700;">{fg.get("value",50)}</span> ({fg.get("label","Neutral")})</div>', unsafe_allow_html=True)
    st.divider()
    crypto_tickers = list(CRYPTO.keys()) if CRYPTO else FALLBACK_CRYPTO
    rows = build_ticker_rows(crypto_tickers, "crypto", vix_now, snap.get("gamma_data"), snap.get("greeks_data"), snap.get("news_narratives"), prices=prices, ar=ar, snap=snap)
    longs, shorts = split_long_short(rows)
    st.markdown(f"**{len(rows)} coins** · 🟢 {len(longs)} Long · 🔴 {len(shorts)} Short")
    tab_l, tab_s = st.tabs([f"🟢 Long ({len(longs)})", f"🔴 Short ({len(shorts)}))"])
    with tab_l: render_ticker_cards_v4(longs)
    with tab_s: render_ticker_cards_v4(shorts)

# ═══════════════════════════════════════════════════════════════════
# PAGE: GLOBAL & EM
# ═══════════════════════════════════════════════════════════════════
def page_global():
    st.markdown("## 🌍 Global & EM")
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
            for c in countries: country_list.append({"country": c, "quad": q, "regime_name": _quad_name(q)})
    st.markdown("### 🗺️ Country Regime Map")
    st.markdown(_heatmap_grid_html(country_list[:16], key_label="country", key_quad="quad"), unsafe_allow_html=True)
    if len(country_list) > 16: st.markdown(_heatmap_grid_html(country_list[16:32], key_label="country", key_quad="quad"), unsafe_allow_html=True)
    st.divider()
    st.markdown("### 🇮🇩 IHSG Report")
    ihsg_tickers = list(IHSG_UNIVERSE.keys()) if IHSG_UNIVERSE else FALLBACK_IHSG
    ihsg_rows = build_ticker_rows(ihsg_tickers, "ihsg", vix_now, prices=prices, ar=ar, snap=snap)
    by_sector = {}
    for r in ihsg_rows: by_sector.setdefault(IHSG_SECTOR_MAP.get(r.get("ticker"), "Other"), []).append(r)
    if by_sector:
        sectors = list(by_sector.keys()); counts = [len(v) for v in by_sector.values()]
        colors = [_ret_color(sum(x.get("r1m",0) or 0 for x in by_sector[s])/max(len(by_sector[s]),1)) for s in sectors]
        fig = go.Figure(go.Bar(y=sectors, x=counts, orientation="h", marker_color=colors, text=[str(c) for c in counts], textposition="outside", textfont=dict(size=11, color="#E6EDF3")))
        fig.update_layout(height=max(250, len(sectors)*35), margin=dict(l=120,r=40,t=20,b=20), paper_bgcolor="#0D1117", plot_bgcolor="#0D1117", font=dict(color="#E6EDF3", size=11, family="Inter"), xaxis=dict(showgrid=True, gridcolor="#21262D"), yaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="ihsg_sector_bar_v4")
    st.markdown(f"**{len(ihsg_rows)} stocks** · Sectors: {', '.join(by_sector.keys())}")
    for sector, items in by_sector.items():
        with st.expander(f"**{sector}** ({len(items)} stocks)", expanded=False):
            render_ticker_cards_v4(items, max_rows=10)

# ═══════════════════════════════════════════════════════════════════
# PAGE: THEMES
# ═══════════════════════════════════════════════════════════════════
def page_themes():
    st.markdown("## 📖 Themes & Playbook")
    allocation = {
        "Q1": {"long": 75, "short": 5, "cash": 20, "style": "Tech 30% | Growth 20% | Crypto 15% | EM 5% | Defensives 5%"},
        "Q2": {"long": 70, "short": 10, "cash": 20, "style": "Cyclicals 25% | Financials 15% | Energy 15% | Materials 10% | Small Caps 5%"},
        "Q3": {"long": 60, "short": 15, "cash": 25, "style": "Energy/Infra 20% | Real Assets 15% | Crypto 10% | EM/LatAm 8% | IHSG Energy 7%"},
        "Q4": {"long": 50, "short": 20, "cash": 30, "style": "TLT 15% | Gold 10% | Utilities 10% | Staples 10% | Healthcare 5%"},
    }
    alloc = allocation.get(sq, allocation["Q3"])
    st.markdown("### 💼 Portfolio Allocation")
    st.markdown(_stacked_bar_html(alloc["long"], alloc["short"], alloc["cash"]), unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:0.78rem; color:#8B949E; margin-top:6px;'>**Style:** {alloc['style']}</div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("### ⚡ Cem Karsan / 0DTE")
    odte = snap.get("odte_monitor", {}) or {}
    if isinstance(odte, dict) and odte.get("tickers"):
        for t, data in list(odte.get("tickers", {}).items())[:3]:
            if not isinstance(data, dict): continue
            pin = data.get("pin_risk", 50)
            vanna_dir = data.get("vanna", "neutral"); charm_dir = data.get("charm", "neutral")
            v_arrow = "⬆" if "up" in str(vanna_dir).lower() or "pos" in str(vanna_dir).lower() else "⬇" if "down" in str(vanna_dir).lower() or "neg" in str(vanna_dir).lower() else "➡"
            c_arrow = "⬆" if "up" in str(charm_dir).lower() or "pos" in str(charm_dir).lower() else "⬇" if "down" in str(charm_dir).lower() or "neg" in str(charm_dir).lower() else "➡"
            st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin:5px 0;padding:7px 10px;background:#161B22;border:1px solid #30363D;border-radius:6px;">'
                        f'<span style="font-weight:700;font-size:0.85rem;color:#E6EDF3;min-width:45px;">{t}</span>'
                        f'<div style="flex:1;"><div style="font-size:0.58rem;color:#8B949E;text-transform:uppercase;font-weight:600;">Pin Risk</div>'
                        f'{_gauge_html(pin, max_val=100, color="#D29922", height=9, label_left="0", label_right="100")}</div>'
                        f'<div style="font-size:0.75rem;color:#58A6FF;font-weight:700;">Vanna {v_arrow}</div>'
                        f'<div style="font-size:0.75rem;color:#A371F7;font-weight:700;">Charm {c_arrow}</div></div>', unsafe_allow_html=True)
    else:
        st.caption("0DTE data unavailable — showing proxy")
        for t in ["SPY","QQQ","IWM"]:
            st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin:5px 0;padding:7px 10px;background:#161B22;border:1px solid #30363D;border-radius:6px;">'
                        f'<span style="font-weight:700;font-size:0.85rem;color:#E6EDF3;min-width:45px;">{t}</span>'
                        f'<div style="flex:1;"><div style="font-size:0.58rem;color:#8B949E;text-transform:uppercase;font-weight:600;">Pin Risk</div>'
                        f'{_gauge_html(50, max_val=100, color="#30363D", height=9, label_left="0", label_right="100")}</div>'
                        f'<div style="font-size:0.75rem;color:#8B949E;font-weight:700;">Vanna ➡</div>'
                        f'<div style="font-size:0.75rem;color:#8B949E;font-weight:700;">Charm ➡</div></div>', unsafe_allow_html=True)
    st.divider()
    st.markdown("### 🧪 Stress Test")
    stress = snap.get("stress_test", []) or []
    if stress:
        for s in stress[:3]:
            if not isinstance(s, dict): continue
            with st.expander(f"{s.get('scenario','—')} · DD {s.get('portfolio_dd',0):.0%}"):
                st.markdown(f'<div style="font-size:0.78rem;color:#8B949E;">Worst: <span style="color:#F85149;font-weight:700;">{s.get("worst_asset","—")} {s.get("worst_dd",0):.0%}</span> · Best: <span style="color:#3FB950;font-weight:700;">{s.get("best_asset","—")} {s.get("best_dd",0):.0%}</span></div>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:0.78rem;color:#8B949E;margin-top:4px;">Hedge: <span style="color:#E6EDF3;">{s.get("hedge","—")}</span></div>', unsafe_allow_html=True)
    else: st.caption("Stress test unavailable")
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
        with st.expander(f"{status} {name} — {desc}", expanded=False):
            if data: st.json({k: str(v)[:100] for k, v in list(data.items())[:3]})
            else: st.caption("Data not loaded this snapshot.")

# ═══════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ═══════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard": page_dashboard()
elif page == "⚡ Alpha Center": page_alpha()
elif page == "🇺🇸 US Stocks": page_us_stocks()
elif page == "💱 Forex": page_forex()
elif page == "🛢️ Commodities": page_commodities()
elif page == "₿ Crypto": page_crypto()
elif page == "🌍 Global & EM": page_global()
elif page == "📖 Themes": page_themes()

st.divider()
flip_note = f" · {snap.get('summary', {}).get('v2_composite_flipped_count', 0)} flipped" if snap.get("summary", {}).get("v2_composite_flipped_count") else ""
st.caption(f"MacroRegime Pro v32.1 FIX · Built {snap.get('build_time_s', 0):.0f}s ago · {snap.get('prices_loaded', 0)} assets · {snap.get('fred_coverage', 0)} indicators{flip_note}")
