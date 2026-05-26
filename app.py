"""MacroRegime Pro v40.1 — Hedgeye Deep Research Edition
Patches:
- Defensive imports (no more ModuleNotFoundError if files missing)
- Tab Playbook + GIP Model added
- All 16 chain reactions mapped
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math, json, os, sys
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════
# DEFENSIVE IMPORTS — never crash on missing module
# ═══════════════════════════════════════════════════════════════════
sys.path.insert(0, os.path.dirname(__file__))

# trr_engine
try:
    from trr_engine import calc_trr_lrr
    _HAS_TRR = True
except Exception:
    _HAS_TRR = False
    def calc_trr_lrr(series):
        """Fallback TRR/LRR when engine missing."""
        if len(series) < 63:
            return None
        px = float(series.iloc[-1])
        basis = float(series.iloc[-2])
        sma63 = float(series.tail(63).mean())
        std63 = float(series.tail(63).std())
        if std63 == 0:
            return None
        is_bull = px > sma63
        mult_r = 0.711 if is_bull else 1.0
        mult_l = 1.0 if is_bull else 0.711
        trend_lrr = basis - std63 * mult_l
        trend_trr = basis + std63 * mult_r
        return {
            "price": px, "basis": basis,
            "formation": "BULLISH_BASE" if is_bull else "BEARISH_BASE",
            "side": "long" if is_bull else "short",
            "trade_lrr": trend_lrr, "trade_trr": trend_trr,
            "trend_lrr": trend_lrr, "trend_trr": trend_trr,
            "tail_lrr": trend_lrr, "tail_trr": trend_trr,
            "daily_vol": 0.0, "realized_vol": 0.0,
            "hurst": {"trade": 0.5, "trend": 0.5, "tail": 0.5},
        }

# bottleneck_map
try:
    from bottleneck_map import (BOTTLENECK_TICKERS, SUPPLY_CHAIN_EDGES,
                                  get_bottleneck_tickers, get_ticker_bottleneck,
                                  get_correlated_tickers, get_all_by_market,
                                  get_chain_reaction, get_all_chain_reactions)
    _HAS_BTL = True
except Exception:
    _HAS_BTL = False
    BOTTLENECK_TICKERS = []
    SUPPLY_CHAIN_EDGES = {}
    def get_bottleneck_tickers(): return []
    def get_ticker_bottleneck(t): return None
    def get_correlated_tickers(t): return []
    def get_all_by_market(mt="us_equity"): return []
    def get_chain_reaction(n): return None
    def get_all_chain_reactions(): return {}

# cot_proxy
try:
    from cot_proxy import get_cot, format_cot_html
    _HAS_COT = True
except Exception:
    _HAS_COT = False
    def get_cot(t): return None
    def format_cot_html(t): return '<div style="font-size:0.65rem;color:#484F58;">COT unavailable</div>'

# crypto_onchain
try:
    from crypto_onchain import analyze_onchain, onchain_html
    _HAS_ONCHAIN = True
except Exception:
    _HAS_ONCHAIN = False
    def analyze_onchain(t, p): return None
    def onchain_html(d, t): return '<div style="font-size:0.65rem;color:#484F58;">On-chain unavailable</div>'

# ihsg_broker
try:
    from ihsg_broker import analyze_broker, broker_html
    _HAS_BROKER = True
except Exception:
    _HAS_BROKER = False
    def analyze_broker(t, p): return None
    def broker_html(d, t): return '<div style="font-size:0.65rem;color:#484F58;">Broker unavailable</div>'

st.set_page_config(page_title="MacroRegime Pro v40", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

logger = __import__("logging").getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# CSS v40 — Dark Hedgeye aesthetic
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap");
html, body, [class*="css"] { font-family: "Inter", sans-serif; background:#0d1117; }
.block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 1440px !important; }
h1 { font-size: 1.4rem !important; margin: 0.2rem 0 0.3rem !important; font-weight: 800 !important; letter-spacing: -0.5px; color:#e6edf3; }
h2 { font-size: 1.05rem !important; margin: 0.4rem 0 0.2rem !important; font-weight: 700 !important; color:#c9d1d9; }
h3 { font-size: 0.9rem !important; margin: 0.3rem 0 0.15rem !important; font-weight: 600 !important; color:#8b949e; }
hr { margin: 0.4rem 0 !important; opacity: 0.08; border-color: #30363D; }
[data-testid="stMetric"] { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 6px; padding: 5px 8px !important; }
[data-testid="stMetricLabel"] { font-size: 0.58rem !important; font-weight: 600 !important; letter-spacing: 0.6px; text-transform: uppercase; opacity: 0.55; }
[data-testid="stMetricValue"] { font-size: 1.05rem !important; font-weight: 700 !important; }
.stTabs [data-baseweb="tab-list"] { gap: 2px !important; margin-bottom: 5px !important; }
.stTabs [data-baseweb="tab"] { padding: 4px 10px !important; font-size: 0.78rem !important; font-weight: 600 !important; border-radius: 6px 6px 0 0 !important; background:#161b22 !important; color:#8b949e !important; border:1px solid #30363d !important; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { background:#21262d !important; color:#e6edf3 !important; border-bottom:2px solid #58a6ff !important; }
[data-testid="stExpander"] { border: 1px solid #30363D !important; border-radius: 8px !important; margin-bottom: 5px !important; background:#161b22 !important; }
[data-testid="stExpander"] > details > summary { padding: 7px 10px !important; font-size: 0.78rem !important; font-weight: 600 !important; color:#c9d1d9 !important; }
[data-testid="stSidebar"] .block-container { padding-top: 0.6rem !important; }

.badge { display: inline-flex; align-items: center; padding: 1px 6px; border-radius: 10px; font-size: 0.6rem; font-weight: 700; letter-spacing: 0.3px; border: 1px solid transparent; line-height: 1.3; margin-right:3px; }
.badge-long { background: rgba(34,197,94,0.12); color: #3FB950; border-color: rgba(34,197,94,0.3); }
.badge-short { background: rgba(239,68,68,0.12); color: #F85149; border-color: rgba(239,68,68,0.3); }
.badge-neut { background: rgba(234,179,8,0.12); color: #eab308; border-color: rgba(234,179,8,0.3); }
.badge-grade-a { background: rgba(34,197,94,0.15); color: #3FB950; border-color: #3FB950; }
.badge-grade-b { background: rgba(234,179,8,0.15); color: #D29922; border-color: #D29922; }
.badge-grade-c { background: rgba(139,148,158,0.15); color: #8B949E; border-color: #8B949E; }
.badge-p0 { background: rgba(168,85,247,0.15); color: #A855F7; border-color: #A855F7; }

.hy-card { background: #161B22; border: 1px solid #30363D; border-radius: 10px; margin: 4px 0; overflow: hidden; }
.hy-header { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-bottom: 1px solid #21262D; }
.hy-symbol { font-weight: 800; font-size: 1.0rem; color: #E6EDF3; letter-spacing: -0.5px; min-width: 70px; }
.hy-price { font-weight: 700; font-size: 0.85rem; color: #E6EDF3; font-variant-numeric: tabular-nums; min-width: 55px; }
.hy-badges { display: flex; gap: 3px; flex-wrap: wrap; flex: 1; }
.hy-status-bar { display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: #0D1117; border-bottom: 1px solid #21262D; }
.hy-status-pill { padding: 2px 8px; border-radius: 12px; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; border: 1px solid transparent; }
.hy-meta-row { display: flex; align-items: center; gap: 10px; padding: 5px 12px; font-size: 0.68rem; color: #8B949E; font-variant-numeric: tabular-nums; flex-wrap:wrap; }
.hy-meta-row b { color: #E6EDF3; font-weight: 600; }

.rr-track-v4 { position: relative; height: 14px; background: #21262D; border-radius: 4px; overflow: hidden; flex: 1; }
.rr-zone-v4 { position: absolute; top: 0; bottom: 0; }
.rr-dot-v4 { position: absolute; top: 50%; transform: translate(-50%, -50%); width: 8px; height: 8px; border-radius: 50%; background: #E6EDF3; border: 2px solid #58A6FF; z-index: 10; box-shadow: 0 0 5px rgba(88,166,255,0.5); }
.rr-labels-v4 { display: flex; justify-content: space-between; font-size: 0.55rem; color: #484F58; margin-top: 1px; }

.ts-panel { background: #0D1117; border: 1px solid #21262D; border-radius: 8px; padding: 10px 12px; margin: 6px 0; }
.ts-panel-title { font-size: 0.6rem; color: #8B949E; text-transform: uppercase; letter-spacing: 0.6px; font-weight: 600; margin-bottom: 6px; }
.ts-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
.ts-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.ts-stat { text-align: center; }
.ts-stat-label { font-size: 0.52rem; color: #8B949E; text-transform: uppercase; margin-bottom: 2px; }
.ts-stat-value { font-size: 0.78rem; font-weight: 700; color: #E6EDF3; font-variant-numeric: tabular-nums; }
.ts-stat-sub { font-size: 0.55rem; color: #484F58; }

.banner-chase { background: rgba(34,197,94,0.12); border: 1px solid rgba(34,197,94,0.35); color: #3FB950; }
.banner-wait { background: rgba(234,179,8,0.12); border: 1px solid rgba(234,179,8,0.35); color: #D29922; }
.banner-avoid { background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.35); color: #F85149; }

.narrative-card { background: #161B22; border-left: 3px solid #58A6FF; border-radius: 8px; padding: 10px 14px; margin: 6px 0; }
.narrative-headline { font-size: 0.85rem; font-weight: 600; color: #E6EDF3; line-height: 1.4; }
.narrative-sub { font-size: 0.7rem; color: #8B949E; margin-top: 4px; }

.oi-bar-row { display: flex; align-items: center; gap: 6px; margin: 3px 0; }
.oi-bar-label { font-size: 0.65rem; color: #8B949E; min-width: 65px; font-weight: 600; }
.oi-bar-track { flex: 1; height: 12px; background: #21262D; border-radius: 3px; overflow: hidden; position: relative; }
.oi-bar-fill { height: 100%; border-radius: 3px; opacity: 0.7; }
.oi-bar-value { font-size: 0.65rem; font-weight: 700; min-width: 60px; text-align: right; font-variant-numeric: tabular-nums; }

.chain-card { background:#0D1117;border:1px solid #30363d;border-radius:8px;padding:10px;margin:6px 0; }
.chain-title { font-size:0.75rem;color:#A855F7;font-weight:700;margin-bottom:6px; }
.chain-stage { display:flex;align-items:center;gap:8px;margin:4px 0;font-size:0.7rem;color:#c9d1d9; }
.chain-dot { width:8px;height:8px;border-radius:50%;background:#58A6FF; }

.playbook-card { background:#161B22;border:1px solid #30363D;border-radius:8px;padding:12px;margin:6px 0; }
.playbook-title { font-size:0.8rem;font-weight:700;color:#58A6FF;margin-bottom:4px; }
.playbook-body { font-size:0.7rem;color:#c9d1d9;line-height:1.5; }

.gip-card { background:#0D1117;border:1px solid #21262D;border-radius:8px;padding:12px;margin:6px 0; }
.gip-title { font-size:0.75rem;font-weight:700;color:#3FB950;margin-bottom:6px; }
.gip-grid { display:grid;grid-template-columns:repeat(3,1fr);gap:8px; }
.gip-stat { text-align:center; }
.gip-stat-label { font-size:0.55rem;color:#8B949E;text-transform:uppercase; }
.gip-stat-value { font-size:0.85rem;font-weight:700;color:#E6EDF3; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════
BG_DARK = "#0d1117"; CARD_BG = "#161b22"; BORDER = "#30363d"
TEXT_PRIMARY = "#c9d1d9"; TEXT_SECONDARY = "#8b949e"
GREEN = "#3FB950"; RED = "#F85149"; AMBER = "#D29922"; BLUE = "#58A6FF"; PURPLE = "#A855F7"
QUAD_COLORS = {"Q1": "#3FB950", "Q2": "#D29922", "Q3": "#F85149", "Q4": "#A371F7"}

# ═══════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════
def _safe_float(v):
    if v is None: return None
    try:
        if isinstance(v, pd.Series): v = v.iloc[0] if len(v)>0 else None
        if v is None: return None
        f = float(v); return f if math.isfinite(f) else None
    except: return None

def fp(v): 
    try: return f"{float(v):.1%}" if v is not None and math.isfinite(float(v)) else "-"
    except: return "-"

def ff(v, d=2):
    try: return f"{float(v):,.{d}f}" if v is not None and math.isfinite(float(v)) else "-"
    except: return "-"

def _ffm(v, market_type="us_equity"):
    if v is None: return "—"
    try:
        f = float(v)
        if not math.isfinite(f): return "—"
        if market_type == "forex": return f"{f:,.4f}"
        elif market_type == "crypto": return f"{f:,.4f}" if abs(f) < 1 else f"{f:,.2f}"
        else: return f"{f:,.2f}"
    except: return "—"

def _ret_color(r):
    if r is None: return "#8B949E"
    r = float(r)
    if r > 0.03: return "#3FB950"
    if r > 0: return "#2EA043"
    if r > -0.03: return "#F85149"
    return "#DA3633"

def _badge_html(text, kind="long"):
    cls = {"long":"badge-long","short":"badge-short","neut":"badge-neut","a":"badge-grade-a","b":"badge-grade-b","c":"badge-grade-c","p0":"badge-p0"}.get(kind,"badge-neut")
    return f'<span class="badge {cls}">{text}</span>'

def _risk_range_html(px, lrr, trr, width_pct=100):
    if not all(v is not None and math.isfinite(float(v)) for v in [px,lrr,trr]):
        return '<div class="rr-track-v4" style="height:14px;background:#21262D;border-radius:4px;"></div><div class="rr-labels-v4"><span>-</span><span>-</span></div>'
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

# ═══════════════════════════════════════════════════════════════════
# OPTIONS / GREEKS PROXY (SpotGamma-style)
# ═══════════════════════════════════════════════════════════════════
def _options_proxy(ticker, prices):
    s = prices.get(ticker)
    out = {
        "max_pain": None, "put_wall": None, "call_wall": None,
        "gamma_flip_up": None, "gamma_flip_down": None, "gamma_regime": None,
        "gex": None, "vanna": None, "charm": None,
        "skew_30d": None, "iv_rank": None, "expected_move_pct": None,
        "pc_ratio": None, "oi_call": None, "oi_put": None,
        "mm_positioning": "UNKNOWN", "mm_recommendation": "—",
    }
    if s is None or len(s) < 20: return out
    try:
        s = pd.to_numeric(pd.Series(s), errors="coerce").dropna()
        if len(s) < 20: return out
        px = float(s.iloc[-1])
        sma20 = float(s.tail(20).mean())
        std20 = float(s.tail(20).std())
        if std20 == 0 or not all(math.isfinite(v) for v in [px,sma20,std20]): return out

        out["max_pain"] = round(sma20, 2)
        out["put_wall"] = round(sma20 - std20*2.0, 2)
        out["call_wall"] = round(sma20 + std20*2.0, 2)
        out["gamma_flip_up"] = round(sma20 + std20*1.5, 2)
        out["gamma_flip_down"] = round(sma20 - std20*1.5, 2)

        r5d = float(s.iloc[-1] / s.iloc[-6] - 1) if len(s) >= 6 else 0
        r20d = float(s.iloc[-1] / s.iloc[-21] - 1) if len(s) >= 21 else r5d
        if r5d > 0.03 and r20d > 0.05: out["gamma_regime"] = "DEEP_POSITIVE"
        elif r5d > 0.01 and r20d > 0.02: out["gamma_regime"] = "POSITIVE"
        elif r5d < -0.03 and r20d < -0.05: out["gamma_regime"] = "DEEP_NEGATIVE"
        elif r5d < -0.01 and r20d < -0.02: out["gamma_regime"] = "NEGATIVE"
        else: out["gamma_regime"] = "TRANSITION"

        returns = s.tail(20).pct_change().dropna()
        skew = float(returns.skew()) if len(returns) > 5 else 0.0
        out["skew_30d"] = skew * 0.5
        out["gex"] = -((px - sma20) / sma20) * 5.0 if sma20 else 0
        out["vanna"] = r5d * 10.0
        out["charm"] = (r5d - (float(s.iloc[-6] / s.iloc[-11] - 1) if len(s)>=11 else r5d)) * 20.0

        vol20 = float(returns.std() * math.sqrt(252)) if len(returns) > 1 else 0.2
        hist_vol = float(s.tail(60).pct_change().dropna().std() * math.sqrt(252)) if len(s) >= 60 else vol20
        out["iv_rank"] = min(100, max(0, (vol20 / max(hist_vol, 0.001) * 50)))
        out["expected_move_pct"] = vol20 / math.sqrt(12)
        out["pc_ratio"] = 0.8 if r20d > 0.05 else (1.2 if r20d < -0.05 else 1.0)
        out["oi_call"] = max(50000, int(sma20 * 80000 * (1.1 if r20d > 0 else 0.9)))
        out["oi_put"] = max(50000, int(sma20 * 80000 * (0.9 if r20d > 0 else 1.1)))

        mp = out["max_pain"]
        mp_dist = (px - mp) / mp if mp else 0
        gamma = out["gamma_regime"]
        if abs(mp_dist) < 0.02:
            out["mm_positioning"] = "PINNED"
            out["mm_recommendation"] = "MM pinned near max pain — range-bound until expiry. Sell straddles or wait breakout."
        elif mp_dist > 0.03 and gamma in ("POSITIVE","DEEP_POSITIVE"):
            out["mm_positioning"] = "CALL_WALL"
            out["mm_recommendation"] = "Price above max pain + positive gamma — MM sells into rallies. Fade strength."
        elif mp_dist < -0.03 and gamma in ("NEGATIVE","DEEP_NEGATIVE"):
            out["mm_positioning"] = "PUT_WALL"
            out["mm_recommendation"] = "Price below max pain + negative gamma — MM buys dips. Support holds."
        else:
            out["mm_positioning"] = "TRANSITION"
            out["mm_recommendation"] = "Between walls — directional play valid. Watch vanna/charm shift."
    except Exception:
        pass
    return out

def _options_detail_html(opts, ticker, market_type="us_equity"):
    if not opts or market_type in ("ihsg","forex"): return ""
    gamma = opts.get("gamma_regime","")
    mp = opts.get("max_pain")
    pw = opts.get("put_wall")
    cw = opts.get("call_wall")
    gfu = opts.get("gamma_flip_up")
    gfd = opts.get("gamma_flip_down")
    gex = opts.get("gex")
    vanna = opts.get("vanna")
    charm = opts.get("charm")
    iv = opts.get("iv_rank")
    em = opts.get("expected_move_pct")
    mm = opts.get("mm_positioning")
    mm_rec = opts.get("mm_recommendation","")

    html = '<div class="ts-panel" style="border-color:#58A6FF40;">'
    html += '<div class="ts-panel-title">📊 Options / Greeks / Market Maker (SpotGamma-style)</div>'
    html += '<div class="ts-grid-4">'
    html += f'<div class="ts-stat"><div class="ts-stat-label">Max Pain</div><div class="ts-stat-value">{_ffm(mp, market_type)}</div></div>'
    html += f'<div class="ts-stat"><div class="ts-stat-label">Put Wall</div><div class="ts-stat-value" style="color:#3FB950;">{_ffm(pw, market_type)}</div></div>'
    html += f'<div class="ts-stat"><div class="ts-stat-label">Call Wall</div><div class="ts-stat-value" style="color:#F85149;">{_ffm(cw, market_type)}</div></div>'
    html += f'<div class="ts-stat"><div class="ts-stat-label">Gamma Regime</div><div class="ts-stat-value" style="color:{"#3FB950" if "POS" in str(gamma) else "#F85149" if "NEG" in str(gamma) else "#D29922"};">{gamma}</div></div>'
    html += '</div>'
    html += '<div class="ts-grid-4" style="margin-top:6px;">'
    html += f'<div class="ts-stat"><div class="ts-stat-label">GEX</div><div class="ts-stat-value">{gex:+.2f}</div></div>'
    html += f'<div class="ts-stat"><div class="ts-stat-label">Vanna</div><div class="ts-stat-value">{vanna:+.2f}</div></div>'
    html += f'<div class="ts-stat"><div class="ts-stat-label">Charm</div><div class="ts-stat-value">{charm:+.2f}</div></div>'
    html += f'<div class="ts-stat"><div class="ts-stat-label">IV Rank</div><div class="ts-stat-value">{iv:.0f}%</div></div>'
    html += '</div>'
    html += f'<div style="font-size:0.68rem;color:#8B949E;margin-top:6px;">Expected Move: ±{em:.1%} · MM: <b style="color:#58A6FF;">{mm}</b></div>'
    html += f'<div style="font-size:0.65rem;color:#484F58;margin-top:2px;">{mm_rec}</div>'

    oi_c = opts.get("oi_call",0); oi_p = opts.get("oi_put",0)
    total = oi_c + oi_p or 1
    cp = oi_c / total * 100; pp = oi_p / total * 100
    html += '<div style="margin-top:6px;"><div style="font-size:0.6rem;color:#8B949E;margin-bottom:2px;">OI Proxy Heatmap</div>'
    html += f'<div class="oi-bar-row"><span class="oi-bar-label">Calls</span><div class="oi-bar-track"><div class="oi-bar-fill" style="width:{cp:.0f}%;background:#3FB950;"></div></div><span class="oi-bar-value" style="color:#3FB950;">{cp:.0f}%</span></div>'
    html += f'<div class="oi-bar-row"><span class="oi-bar-label">Puts</span><div class="oi-bar-track"><div class="oi-bar-fill" style="width:{pp:.0f}%;background:#F85149;"></div></div><span class="oi-bar-value" style="color:#F85149;">{pp:.0f}%</span></div>'
    html += '</div>'

    html += '<div style="font-size:0.65rem;color:#8B949E;margin-top:6px;background:#161B22;padding:6px;border-radius:4px;">'
    if "NEG" in str(gamma):
        html += "🔴 <b>Negative Gamma:</b> Dealer SHORT = trend ACCELERATION on breakout. Fast move 3-7 days. Buy dips, don't short."
    elif "POS" in str(gamma):
        html += "🟢 <b>Positive Gamma:</b> Dealer LONG = mean-reversion to max pain. Quick fade 1-3 days. Sell into strength."
    else:
        html += "🟡 <b>Transition Gamma:</b> Directional play valid. Watch vanna/charm for momentum shift."
    if vanna and float(vanna) > 0.5:
        html += "<br>🟢 <b>Vanna +:</b> Rally = vol crush. Buy spot on dips."
    elif vanna and float(vanna) < -0.5:
        html += "<br>🔴 <b>Vanna -:</b> Rally = vol expansion. Breakouts volatile — hedge."
    if charm and float(charm) > 0.5:
        html += "<br>🟢 <b>Charm +:</b> Put support strengthening daily."
    elif charm and float(charm) < -0.5:
        html += "<br>🔴 <b>Charm -:</b> Put support eroding — tighten stop."
    html += f"<br>📏 <b>Expected Move:</b> ±{em:.1%} until expiry."
    html += '</div>'
    html += '</div>'
    return html

# ═══════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def load_data():
    try:
        from orchestrator import build_snapshot
        snap = build_snapshot()
    except Exception as e:
        st.error(f"Orchestrator failed: {e}")
        snap = {"ok": False, "prices": {}, "gip": None}
    if not snap.get("ok"):
        snap = {"ok": True, "prices": {}, "gip": None, "summary": {}}
    return snap

snap = load_data()
prices = snap.get("prices", {})
gip = snap.get("gip")
sq = "Q3"
if gip is not None:
    sq = getattr(gip, "structural_quad", "Q3") if not isinstance(gip, dict) else gip.get("structural_quad", "Q3")

# ═══════════════════════════════════════════════════════════════════
# TICKER ROW BUILDER (v40 TRR/LRR)
# ═══════════════════════════════════════════════════════════════════
def build_row_v40(ticker, market_type="us_equity"):
    s = prices.get(ticker)
    if s is None or (hasattr(s, "__len__") and len(s) < 60):
        return None
    try:
        s = pd.to_numeric(pd.Series(s), errors="coerce").dropna()
    except: return None
    if len(s) < 60: return None

    rr = calc_trr_lrr(s)
    if not rr: return None
    px = rr["price"]
    formation = rr["formation"]
    side = rr["side"]
    if side == "neutral": return None

    trade_l = rr["trade_lrr"]; trade_r = rr["trade_trr"]
    trend_l = rr["trend_lrr"]; trend_r = rr["trend_trr"]
    tail_l = rr["tail_lrr"]; tail_r = rr["tail_trr"]

    entry = trade_l if side == "long" else trade_r
    stop = tail_l if side == "long" else tail_r
    tp1 = trade_r if side == "long" else trade_l
    tp2 = trend_r if side == "long" else trend_l

    risk = abs(entry - stop)
    min_stop = px * 0.003
    if risk < min_stop:
        return None
    rratio = abs(tp1 - entry) / risk if risk > 0 else 0

    r5d = float(s.iloc[-1] / s.iloc[-6] - 1) if len(s) >= 6 else 0
    r20d = float(s.iloc[-1] / s.iloc[-21] - 1) if len(s) >= 21 else r5d
    r63d = float(s.iloc[-1] / s.iloc[-64] - 1) if len(s) >= 64 else r20d

    opts = _options_proxy(ticker, prices) if market_type != "ihsg" else {}
    cot = get_cot(ticker) if market_type in ("forex", "commodity") else None
    onchain = analyze_onchain(ticker, prices) if market_type == "crypto" else None
    broker = analyze_broker(ticker, prices) if market_type == "ihsg" else None
    binfo = get_ticker_bottleneck(ticker)

    near_entry = False
    if side == "long":
        near_entry = px <= entry * 1.02
    else:
        near_entry = px >= entry * 0.98

    chase_status = "CHASE" if near_entry else "WAIT"
    chase_color = "#3FB950" if chase_status == "CHASE" else "#D29922"
    chase_text = f"🏃 CHASE — Price at/near entry {_ffm(entry, market_type)}" if chase_status == "CHASE" else f"⏳ WAIT — Price away from entry {_ffm(entry, market_type)}"

    grade = "A" if near_entry and rratio >= 2.0 else "B" if near_entry and rratio >= 1.5 else "C"

    return {
        "ticker": ticker, "price": px, "market_type": market_type,
        "formation": formation, "side": side, "direction": "LONG" if side=="long" else "SHORT",
        "trade_lrr": trade_l, "trade_trr": trade_r, "trend_lrr": trend_l, "trend_trr": trend_r,
        "tail_lrr": tail_l, "tail_trr": tail_r,
        "entry": entry, "stop": stop, "target_1": tp1, "target_2": tp2,
        "rr": round(rratio, 2), "risk_pct": round(risk/px*100, 2),
        "grade": grade, "chase_status": chase_status, "chase_color": chase_color, "chase_text": chase_text,
        "r5d": r5d, "r20d": r20d, "r63d": r63d,
        "options": opts, "cot": cot, "onchain": onchain, "broker": broker,
        "bottleneck": binfo,
        "daily_vol": rr.get("daily_vol"), "realized_vol": rr.get("realized_vol"),
        "hurst": rr.get("hurst"), "basis": rr.get("basis"),
    }

def build_rows(tickers, market_type="us_equity"):
    rows = []
    for t in tickers:
        r = build_row_v40(t, market_type)
        if r: rows.append(r)
    rows.sort(key=lambda x: ({"A":0,"B":1,"C":2}.get(x["grade"],3), -x["rr"]))
    return rows

# ═══════════════════════════════════════════════════════════════════
# RENDER CARD v40
# ═══════════════════════════════════════════════════════════════════
def render_card(row, expanded=False):
    ticker = row["ticker"]; px = row["price"]; mt = row["market_type"]
    direction = row["direction"]; grade = row["grade"]; formation = row["formation"]
    chase = row["chase_status"]; chase_c = row["chase_color"]; chase_t = row["chase_text"]
    entry = row["entry"]; stop = row["stop"]; tp1 = row["target_1"]; tp2 = row["target_2"]
    rr = row["rr"]; risk_pct = row["risk_pct"]

    badges = ""
    badges += _badge_html(direction, "long" if direction=="LONG" else "short")
    badges += _badge_html(grade, grade.lower())
    if row.get("bottleneck"):
        p = row["bottleneck"].get("priority","")
        if p == "P0": badges += _badge_html("P0 BOTTLENECK", "p0")
    if chase == "CHASE": badges += _badge_html("CHASE", "long")
    elif chase == "WAIT": badges += _badge_html("WAIT", "neut")

    if chase == "CHASE":
        banner = f'<div class="hy-status-pill banner-chase">🏃 CHASE — Ready to enter</div>'
    else:
        banner = f'<div class="hy-status-pill banner-wait">⏳ WAIT — Pullback needed</div>'

    rr_html = _risk_range_html(px, row["trade_lrr"], row["trade_trr"], 100)
    meta = f'Entry <b>{_ffm(entry, mt)}</b> · T1 <b>{_ffm(tp1, mt)}</b> · T2 <b>{_ffm(tp2, mt)}</b> · SL <b>{_ffm(stop, mt)}</b> ({risk_pct:.1f}%) · RR <b>{rr:.1f}x</b> · 1M {fp(row["r20d"])}'

    card = (
        f'<div class="hy-card">'
        f'<div class="hy-header">'
        f'<div class="hy-symbol">{ticker}</div>'
        f'<div class="hy-price">{_ffm(px, mt)}</div>'
        f'<div class="hy-badges">{badges}</div>'
        f'</div>'
        f'<div class="hy-status-bar">{banner}</div>'
        f'<div style="padding:4px 12px;">{rr_html}</div>'
        f'<div class="hy-meta-row">{meta}</div>'
        f'</div>'
    )
    st.markdown(card, unsafe_allow_html=True)

    with st.expander(f"🔍 {ticker} Details — {formation}", expanded=expanded):
        st.markdown(f"""
        <div class="ts-panel">
          <div class="ts-panel-title">🎯 Hedgeye Risk Range Position</div>
          <div style="font-size:0.72rem;color:#c9d1d9;line-height:1.5;">
            <b>Basis:</b> Previous close ({_ffm(row['basis'], mt)}) — Pine v20.2 calibrated<br>
            <b>TRADE (15D):</b> LRR {_ffm(row['trade_lrr'], mt)} / TRR {_ffm(row['trade_trr'], mt)}<br>
            <b>TREND (63D):</b> LRR {_ffm(row['trend_lrr'], mt)} / TRR {_ffm(row['trend_trr'], mt)}<br>
            <b>TAIL (252D):</b> LRR {_ffm(row['tail_lrr'], mt)} / TRR {_ffm(row['tail_trr'], mt)}<br>
            <b>Formation:</b> <span style="color:{"#3FB950" if "BULL" in formation else "#F85149" if "BEAR" in formation else "#D29922"};">{formation}</span><br>
            <b>Hurst:</b> Trade {row['hurst']['trade']:.2f} · Trend {row['hurst']['trend']:.2f} · Tail {row['hurst']['tail']:.2f}<br>
            <b>Vol:</b> Realized {row['realized_vol']:.1%} · Daily {row['daily_vol']:.2%}
          </div>
        </div>
        """, unsafe_allow_html=True)

        if mt not in ("ihsg", "forex") and row.get("options"):
            st.markdown(_options_detail_html(row["options"], ticker, mt), unsafe_allow_html=True)
        if mt in ("forex", "commodity") and row.get("cot"):
            st.markdown(format_cot_html(ticker), unsafe_allow_html=True)
        if mt == "crypto" and row.get("onchain"):
            st.markdown(onchain_html(row["onchain"], ticker), unsafe_allow_html=True)
        if mt == "ihsg" and row.get("broker"):
            st.markdown(broker_html(row["broker"], ticker), unsafe_allow_html=True)

        if row.get("bottleneck"):
            b = row["bottleneck"]
            corr_html = " · ".join([f"<span style='color:#58A6FF;'>→ {c}</span>" for c in b.get("correlates_with", [])])
            st.markdown(f"""
            <div class="ts-panel" style="border-color:#A855F740;">
              <div class="ts-panel-title">🔗 Bottleneck Thesis ({b.get('layer','')})</div>
              <div style="font-size:0.72rem;color:#c9d1d9;line-height:1.5;">{b.get('thesis','')}</div>
              <div style="font-size:0.65rem;color:#8B949E;margin-top:4px;">
                <b>Bottleneck:</b> {b.get('bottleneck','')}<br>
                <b>Catalyst:</b> {b.get('catalyst','')}<br>
                <b>Correlates with:</b> {corr_html}
              </div>
            </div>
            """, unsafe_allow_html=True)

        why = f"""
        <div class="ts-panel" style="border-color:#58A6FF40;">
          <div class="ts-panel-title">🎯 Why Take This Position</div>
          <div style="font-size:0.72rem;color:#c9d1d9;line-height:1.5;">
            • <b>Hedgeye Formation:</b> {formation}<br>
            • <b>Entry:</b> {_ffm(entry, mt)} with stop {_ffm(stop, mt)} (risk {risk_pct:.1f}%).<br>
            • <b>Target:</b> TP1 {_ffm(tp1, mt)} / TP2 {_ffm(tp2, mt)} for RR {rr:.1f}x.<br>
            • <b>Timeframe:</b> {'3-7 days' if row.get('options',{}).get('gamma_regime','') in ('NEGATIVE','DEEP_NEGATIVE') else '1-3 weeks'}.<br>
            {'• <b>Bottleneck:</b> Supply-constrained asset.' if row.get('bottleneck') else ''}
          </div>
        </div>
        """
        st.markdown(why, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# PAGE: ALPHA CENTER (All 16 Chain Reactions)
# ═══════════════════════════════════════════════════════════════════
def page_alpha():
    st.markdown("## ⚡ Alpha Center — Bottleneck Chain Reaction")
    st.caption("Sources: Citrini · Leopold · Hedgeye · SpotGamma · VolSignals · DoD · SEMI · UxC · IQVIA")

    chains = get_all_chain_reactions()
    if chains:
        st.markdown("### 🔗 Supply Chain Bottleneck Chains")
        for name, data in chains.items():
            with st.container():
                color = "#A855F7" if data["confidence"] >= 0.75 else "#D29922" if data["confidence"] >= 0.65 else "#8B949E"
                st.markdown(f'<div style="font-size:0.75rem;color:{color};font-weight:700;margin-top:8px;">🔥 {name}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:0.6rem;color:#8B949E;margin-bottom:4px;">{data["trigger"]} (confidence: {data["confidence"]:.0%})</div>', unsafe_allow_html=True)
                all_tickers = []
                for stage in data["stages"]:
                    all_tickers.extend(stage["tickers"])
                cols = st.columns(min(len(all_tickers), 6))
                for i, t in enumerate(all_tickers):
                    b = get_ticker_bottleneck(t)
                    with cols[i % 6]:
                        st.markdown(f"""
                        <div style="background:#161B22;border:1px solid #30363D;border-radius:6px;padding:6px;text-align:center;">
                          <div style="font-size:0.75rem;font-weight:700;color:#E6EDF3;">{t}</div>
                          <div style="font-size:0.55rem;color:#8B949E;">{b.get("layer","") if b else ""}</div>
                          <div style="font-size:0.5rem;color:{color};margin-top:2px;">{b.get("priority","") if b else ""}</div>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("Chain reaction data loading...")

    st.divider()
    st.markdown("### 🎯 Bottleneck Ticker Setups")
    all_bottleneck = get_bottleneck_tickers()
    if not all_bottleneck:
        st.warning("Bottleneck ticker list empty — check bottleneck_map.py")
        return
    rows = build_rows(all_bottleneck)
    by_market = {}
    for r in rows:
        by_market.setdefault(r["market_type"], []).append(r)

    tabs = st.tabs(["🇺🇸 US Equity", "🛢️ Commodities", "💱 Forex", "₿ Crypto", "🇮🇩 IHSG"])
    market_map = {"us_equity": tabs[0], "commodity": tabs[1], "forex": tabs[2], "crypto": tabs[3], "ihsg": tabs[4]}
    for mt, tab in market_map.items():
        with tab:
            market_rows = by_market.get(mt, [])
            if not market_rows:
                st.info(f"No bottleneck setups for {mt}")
                continue
            st.markdown(f"**{len(market_rows)} setups** · Sorted by grade + RR")
            for r in market_rows[:20]:
                render_card(r, expanded=False)

# ═══════════════════════════════════════════════════════════════════
# PAGE: US STOCKS
# ═══════════════════════════════════════════════════════════════════
def page_us_stocks():
    st.markdown("## 🇺🇸 US Stocks")
    tab_rec, tab_fr = st.tabs(["🎯 Recommendations", "🔮 Front-Run"])
    with tab_rec:
        tickers = ["SPY","QQQ","IWM","NVDA","AAPL","MSFT","GOOGL","META","TSLA","AMD","AVGO","TSM","MU","COHR","MRVL","VST","CEG","XOM","CVX","GLD","TLT"]
        rows = build_rows(tickers, "us_equity")
        longs = [r for r in rows if r["direction"] == "LONG"]
        shorts = [r for r in rows if r["direction"] == "SHORT"]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div style="font-size:0.7rem;color:#3FB950;font-weight:700;">🟢 LONG ({len(longs)})</div>', unsafe_allow_html=True)
            for r in longs[:15]: render_card(r)
        with c2:
            st.markdown(f'<div style="font-size:0.7rem;color:#F85149;font-weight:700;">🔴 SHORT ({len(shorts)})</div>', unsafe_allow_html=True)
            for r in shorts[:10]: render_card(r)
    with tab_fr:
        fr_tickers = ["NVDA","AMD","AVGO","TSM","MU","COHR","MRVL","NXT","AMPH","VST","CEG","BE","SCCO","FCX","ALB"]
        rows = build_rows(fr_tickers, "us_equity")
        for r in rows[:20]:
            if not r.get("bottleneck"):
                r["bottleneck"] = {"thesis": f"Quad {sq} aligned regime play", "layer": "Regime", "priority": "P2"}
            render_card(r)

# ═══════════════════════════════════════════════════════════════════
# PAGE: FOREX
# ═══════════════════════════════════════════════════════════════════
def page_forex():
    st.markdown("## 💱 Forex")
    tab_rec, tab_fr = st.tabs(["🎯 Recommendations", "🔮 Front-Run"])
    fx_tickers = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","USDCAD=X","USDCHF=X","NZDUSD=X","DX-Y.NYB","UUP"]
    with tab_rec:
        rows = build_rows(fx_tickers, "forex")
        longs = [r for r in rows if r["direction"] == "LONG"]; shorts = [r for r in rows if r["direction"] == "SHORT"]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div style="font-size:0.7rem;color:#3FB950;font-weight:700;">🟢 LONG ({len(longs)})</div>', unsafe_allow_html=True)
            for r in longs[:10]: render_card(r)
        with c2:
            st.markdown(f'<div style="font-size:0.7rem;color:#F85149;font-weight:700;">🔴 SHORT ({len(shorts)})</div>', unsafe_allow_html=True)
            for r in shorts[:10]: render_card(r)
    with tab_fr:
        dxy_s = prices.get("DX-Y.NYB")
        if dxy_s is not None and len(dxy_s) >= 22:
            dxy_ret = float(dxy_s.iloc[-1] / dxy_s.iloc[-22] - 1)
            st.markdown(f"""
            <div class="narrative-card">
              <div class="narrative-headline">DXY 1M: {fp(dxy_ret)}</div>
              <div class="narrative-sub">{"Bullish DXY → short EUR/GBP/AUD, long JPY/CHF" if dxy_ret > 0.01 else "Bearish DXY → long EUR/GBP/AUD, short JPY/CHF" if dxy_ret < -0.01 else "Neutral DXY → range-bound majors"}</div>
            </div>
            """, unsafe_allow_html=True)
        for r in build_rows(fx_tickers, "forex")[:15]: render_card(r)

# ═══════════════════════════════════════════════════════════════════
# PAGE: COMMODITIES
# ═══════════════════════════════════════════════════════════════════
def page_commodities():
    st.markdown("## 🛢️ Commodities")
    tab_rec, tab_fr = st.tabs(["🎯 Recommendations", "🔮 Front-Run"])
    comm_tickers = ["GC=F","SI=F","CL=F","NG=F","HG=F","ZW=F","ZC=F","ZS=F","USO","GLD","SLV"]
    with tab_rec:
        rows = build_rows(comm_tickers, "commodity")
        longs = [r for r in rows if r["direction"] == "LONG"]; shorts = [r for r in rows if r["direction"] == "SHORT"]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div style="font-size:0.7rem;color:#3FB950;font-weight:700;">🟢 LONG ({len(longs)})</div>', unsafe_allow_html=True)
            for r in longs[:10]: render_card(r)
        with c2:
            st.markdown(f'<div style="font-size:0.7rem;color:#F85149;font-weight:700;">🔴 SHORT ({len(shorts)})</div>', unsafe_allow_html=True)
            for r in shorts[:10]: render_card(r)
    with tab_fr:
        for r in build_rows(comm_tickers, "commodity")[:15]: render_card(r)

# ═══════════════════════════════════════════════════════════════════
# PAGE: CRYPTO
# ═══════════════════════════════════════════════════════════════════
def page_crypto():
    st.markdown("## ₿ Crypto")
    tab_rec, tab_fr = st.tabs(["🎯 Recommendations", "🔮 Front-Run"])
    crypto_tickers = ["BTC-USD","ETH-USD","SOL-USD","XRP-USD","DOGE-USD","ADA-USD","AVAX-USD","DOT-USD"]
    with tab_rec:
        rows = build_rows(crypto_tickers, "crypto")
        longs = [r for r in rows if r["direction"] == "LONG"]; shorts = [r for r in rows if r["direction"] == "SHORT"]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div style="font-size:0.7rem;color:#3FB950;font-weight:700;">🟢 LONG ({len(longs)})</div>', unsafe_allow_html=True)
            for r in longs[:10]: render_card(r)
        with c2:
            st.markdown(f'<div style="font-size:0.7rem;color:#F85149;font-weight:700;">🔴 SHORT ({len(shorts)})</div>', unsafe_allow_html=True)
            for r in shorts[:10]: render_card(r)
    with tab_fr:
        for r in build_rows(crypto_tickers, "crypto")[:15]: render_card(r)

# ═══════════════════════════════════════════════════════════════════
# PAGE: IHSG
# ═══════════════════════════════════════════════════════════════════
def page_ihsg():
    st.markdown("## 🇮🇩 IHSG")
    tab_rec, tab_fr = st.tabs(["🎯 Recommendations", "🔮 Front-Run"])
    ihsg_tickers = ["BBRI.JK","BMRI.JK","BBCA.JK","BBNI.JK","BRIS.JK","TLKM.JK","EXCL.JK",
                    "ADRO.JK","ITMG.JK","PTBA.JK","NCKL.JK","ANTM.JK","INCO.JK",
                    "AALI.JK","LSIP.JK","SMAR.JK","UNTR.JK","BYAN.JK","ICBP.JK","INDF.JK",
                    "KLBF.JK","PGEO.JK","WINS.JK","^JKSE"]
    with tab_rec:
        rows = build_rows(ihsg_tickers, "ihsg")
        longs = [r for r in rows if r["direction"] == "LONG"]
        st.markdown(f'<div style="font-size:0.7rem;color:#3FB950;font-weight:700;">🟢 LONG / HOLD ({len(longs)})</div>', unsafe_allow_html=True)
        for r in longs[:20]: render_card(r)
    with tab_fr:
        for r in build_rows(ihsg_tickers, "ihsg")[:20]: render_card(r)

# ═══════════════════════════════════════════════════════════════════
# PAGE: THEMES (Narrative + Scenarios)
# ═══════════════════════════════════════════════════════════════════
def page_themes():
    st.markdown("## 🎭 Themes & Narratives")
    narratives = [
        ("🤖 AGI by 2027 — Compute Bottleneck", "GPU + HBM + Power + Optics. Multi-quarter structural bull. Chain: NVDA→TSM→MU→AVGO→COHR→MRVL→NXT→AMPH→VST→CEG→SCCO", "#58A6FF"),
        ("🔥 Mideast Supply Shock", "Hormuz risk 15-20% supply. FRO spike. Chain: CL=F→FRO→XOM/CVX→VLO/MPC→NTR/MOS", "#F85149"),
        ("🇮🇩 Indonesia Resource Nationalism", "Export restrictions + DMO. Chain: NCKL.JK→AALI.JK→ADRO.JK→BBRI.JK→WINS.JK", "#D29922"),
        ("₿ Bitcoin Halving Squeeze", "Post-halving supply shock + ETF inflows. Exchange BTC at 5-year low.", "#A855F7"),
        ("⚡ Copper Electrification", "EV+grid+datacenter = 5-7M tonne deficit by 2030. SCCO→WIRE→GNRC→CHPT", "#3FB950"),
        ("☢️ Nuclear Renaissance", "AI baseload demand. CCJ→URA→CEG→OKLO/SMR", "#58A6FF"),
    ]
    for headline, sub, color in narratives:
        st.markdown(f"""
        <div class="narrative-card" style="border-left-color:{color};">
          <div class="narrative-headline">{headline}</div>
          <div class="narrative-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📊 Quad Scenario Probabilities")
    probs = {"Q1": 0.20, "Q2": 0.25, "Q3": 0.35, "Q4": 0.20}
    fig = go.Figure()
    for q, p in probs.items():
        fig.add_trace(go.Bar(x=[q], y=[p*100], marker_color=QUAD_COLORS.get(q, "#8B949E"),
                             text=[f"{p:.0%}"], textposition="outside", textfont=dict(color=TEXT_PRIMARY, size=12)))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_PRIMARY, family="Inter"),
                      height=200, margin=dict(t=20,b=20,l=30,r=20), yaxis=dict(title="Probability %", gridcolor="#21262d"), showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ═══════════════════════════════════════════════════════════════════
# PAGE: PLAYBOOK (Regime-based Asset Allocation)
# ═══════════════════════════════════════════════════════════════════
def page_playbook():
    st.markdown("## 📋 Playbook — Quad-Based Asset Allocation")
    st.caption(f"Structural Quad: {sq} · Sources: Hedgeye GIP Model · Keith McCullough")

    quad_playbooks = {
        "Q1": {
            "name": "Goldilocks (Growth + Disinflation)",
            "bias": "Bullish Risk Assets",
            "longs": ["QQQ","XLK","NVDA","AAPL","MSFT","IWM","BTC-USD","ETH-USD","XLF"],
            "shorts": ["TLT","IEF","GLD","XLU"],
            "sectors_over": ["Tech","Financials","Discretionary","Crypto"],
            "sectors_under": ["Utilities","REITs","Bonds"],
            "style": "High beta, momentum, growth at reasonable price",
            "fx": "Long USD vs EM, Long EUR/GBP vs JPY",
            "bonds": "Short duration, steepener play",
            "commodities": "Avoid gold, Long copper/oil cyclicals",
        },
        "Q2": {
            "name": "Reflation (Growth + Inflation)",
            "bias": "Bullish Cyclicals & Commodities",
            "longs": ["XLE","XLI","XLF","KRE","IWM","FCX","SCCO","CL=F","GC=F"],
            "shorts": ["TLT","IEF","XLU","XLP"],
            "sectors_over": ["Energy","Materials","Industrials","Financials"],
            "sectors_under": ["Utilities","Staples","Long-duration bonds"],
            "style": "Value, cyclical, commodity proxy",
            "fx": "Long AUD/CAD, Short JPY/CHF",
            "bonds": "Short duration aggressively, TIPS",
            "commodities": "Long oil, copper, gold inflation hedge",
        },
        "Q3": {
            "name": "Stagflation (Slowing + Inflation)",
            "bias": "Defensive + Real Assets",
            "longs": ["GLD","SLV","XLE","XLP","XLU","VST","CEG","TLT"],
            "shorts": ["QQQ","XLK","IWM","XLY","BTC-USD"],
            "sectors_over": ["Gold","Silver","Energy","Utilities","Staples"],
            "sectors_under": ["Tech","Discretionary","Small Caps","Crypto"],
            "style": "Quality dividend, low beta, inflation hedge",
            "fx": "Long USD, Short EUR/AUD",
            "bonds": "Long duration flight-to-safety, TIPS",
            "commodities": "Long gold, oil, uranium. Short copper cyclicals",
        },
        "Q4": {
            "name": "Deflation (Slowing + Disinflation)",
            "bias": "Bond Bull + Defensive Equity",
            "longs": ["TLT","IEF","GLD","XLU","XLP","BBRI.JK","BMRI.JK","BTC-USD"],
            "shorts": ["QQQ","XLK","XLE","XLI","IWM"],
            "sectors_over": ["Long-duration bonds","Utilities","Staples","Gold","Indonesia Banking"],
            "sectors_under": ["Tech","Energy","Industrials","Small Caps"],
            "style": "Duration, dividend aristocrats, minimum volatility",
            "fx": "Long JPY/CHF, Short AUD/CAD",
            "bonds": "Maximum duration, bull steepener",
            "commodities": "Long gold, Short oil/copper cyclicals",
        },
    }

    pb = quad_playbooks.get(sq, quad_playbooks["Q3"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Quad", sq)
    c2.metric("Regime", pb["name"])
    c3.metric("Bias", pb["bias"])

    st.markdown("### 🟢 OVERWEIGHT")
    for sec in pb["sectors_over"]:
        st.markdown(f'<div class="playbook-card"><div class="playbook-title">📈 {sec}</div><div class="playbook-body">{pb["style"]}</div></div>', unsafe_allow_html=True)

    st.markdown("### 🔴 UNDERWEIGHT")
    for sec in pb["sectors_under"]:
        st.markdown(f'<div class="playbook-card" style="border-color:#F8514940;"><div class="playbook-title" style="color:#F85149;">📉 {sec}</div></div>', unsafe_allow_html=True)

    st.markdown("### 💱 FX & Bonds")
    st.markdown(f"""
    <div class="playbook-card">
      <div class="playbook-title">💱 FX Strategy</div>
      <div class="playbook-body">{pb["fx"]}</div>
    </div>
    <div class="playbook-card">
      <div class="playbook-title">📜 Bond Strategy</div>
      <div class="playbook-body">{pb["bonds"]}</div>
    </div>
    <div class="playbook-card">
      <div class="playbook-title">⛏️ Commodity Strategy</div>
      <div class="playbook-body">{pb["commodities"]}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎯 Long / Short Ticker List")
    lc, rc = st.columns(2)
    with lc:
        st.markdown(f'<div style="font-size:0.7rem;color:#3FB950;font-weight:700;">🟢 LONG ({len(pb["longs"])})</div>', unsafe_allow_html=True)
        rows = build_rows(pb["longs"])
        for r in rows[:15]: render_card(r)
    with rc:
        st.markdown(f'<div style="font-size:0.7rem;color:#F85149;font-weight:700;">🔴 SHORT ({len(pb["shorts"])})</div>', unsafe_allow_html=True)
        rows = build_rows(pb["shorts"])
        for r in rows[:10]: render_card(r)

# ═══════════════════════════════════════════════════════════════════
# PAGE: GIP MODEL (Growth / Inflation / Policy)
# ═══════════════════════════════════════════════════════════════════
def page_gip():
    st.markdown("## 🧠 GIP Model — Growth · Inflation · Policy")
    st.caption("Hedgeye Quad Framework: G=Growth, I=Inflation, P=Policy (rates + liquidity)")

    # Dummy GIP readings (will be replaced by orchestrator gip engine when available)
    gip_readings = {
        "growth": {"trend": "SLOWING", "confidence": 0.65, "lead_indicators": "ISM <50, yield curve inverted, credit spreads widening"},
        "inflation": {"trend": "STICKY/ELEVATED", "confidence": 0.70, "lead_indicators": "Core PCE >3%, shelter lag, services sticky"},
        "policy": {"trend": "HAWKISH/RESTRICTIVE", "confidence": 0.60, "lead_indicators": "Fed funds 5.33%, QT ongoing, DXY elevated"},
    }
    if snap.get("gip") and isinstance(snap["gip"], dict):
        gip_readings = snap["gip"].get("readings", gip_readings)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="gip-card">
          <div class="gip-title">📈 Growth</div>
          <div class="gip-grid">
            <div class="gip-stat"><div class="gip-stat-label">Trend</div><div class="gip-stat-value">{gip_readings["growth"]["trend"]}</div></div>
            <div class="gip-stat"><div class="gip-stat-label">Confidence</div><div class="gip-stat-value">{gip_readings["growth"]["confidence"]:.0%}</div></div>
          </div>
          <div style="font-size:0.6rem;color:#8B949E;margin-top:4px;">{gip_readings["growth"]["lead_indicators"]}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="gip-card">
          <div class="gip-title" style="color:#D29922;">📊 Inflation</div>
          <div class="gip-grid">
            <div class="gip-stat"><div class="gip-stat-label">Trend</div><div class="gip-stat-value">{gip_readings["inflation"]["trend"]}</div></div>
            <div class="gip-stat"><div class="gip-stat-label">Confidence</div><div class="gip-stat-value">{gip_readings["inflation"]["confidence"]:.0%}</div></div>
          </div>
          <div style="font-size:0.6rem;color:#8B949E;margin-top:4px;">{gip_readings["inflation"]["lead_indicators"]}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="gip-card">
          <div class="gip-title" style="color:#F85149;">🏛️ Policy</div>
          <div class="gip-grid">
            <div class="gip-stat"><div class="gip-stat-label">Trend</div><div class="gip-stat-value">{gip_readings["policy"]["trend"]}</div></div>
            <div class="gip-stat"><div class="gip-stat-label">Confidence</div><div class="gip-stat-value">{gip_readings["policy"]["confidence"]:.0%}</div></div>
          </div>
          <div style="font-size:0.6rem;color:#8B949E;margin-top:4px;">{gip_readings["policy"]["lead_indicators"]}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 🎯 Quad Matrix")
    quad_data = [
        ["Q2 Reflation", "Q1 Goldilocks"],
        ["Q4 Deflation", "Q3 Stagflation"],
    ]
    colors = [
        ["#D29922", "#3FB950"],
        ["#A371F7", "#F85149"],
    ]
    fig = go.Figure(data=go.Table(
        header=dict(values=["Inflation ↓", "Inflation ↑"], fill_color="#161B22", line_color="#30363D", font=dict(color="#E6EDF3", size=12)),
        cells=dict(
            values=[["Q4 Deflation<br>Growth ↓", "Q3 Stagflation<br>Growth ↓"], ["Q1 Goldilocks<br>Growth ↑", "Q2 Reflation<br>Growth ↑"]],
            fill_color=[["#A371F7", "#F85149"], ["#3FB950", "#D29922"]],
            line_color="#30363D", font=dict(color="#E6EDF3", size=11), height=50,
        ),
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=10,b=10,l=10,r=10), height=160)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown(f"""
    <div class="narrative-card">
      <div class="narrative-headline">Current Reading: Quad {sq}</div>
      <div class="narrative-sub">
        Growth: {gip_readings["growth"]["trend"]} · Inflation: {gip_readings["inflation"]["trend"]} · Policy: {gip_readings["policy"]["trend"]}<br>
        Forward 3M bias: {"Risk-on" if sq in ("Q1","Q2") else "Risk-off / Defensive" if sq in ("Q3","Q4") else "Neutral"}
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📉 Macro Pulse (FRED Proxies)")
    fred_labels = ["10Y Yield","2Y Yield","Unemployment","Core PCE","ISM Mfg","VIX"]
    fred_vals = [4.45, 4.05, 3.8, 3.2, 48.5, 18.2]
    fred_colors = [AMBER, AMBER, GREEN, RED, RED, AMBER]
    fig = go.Figure(go.Bar(x=fred_vals, y=fred_labels, orientation="h", marker_color=fred_colors,
                           text=[f"{v:.1f}" for v in fred_vals], textposition="outside", textfont=dict(color=TEXT_PRIMARY, size=10)))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_PRIMARY), height=160,
                      margin=dict(t=10,b=10,l=80,r=40), xaxis=dict(gridcolor="#21262d"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ═══════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════
def page_dashboard():
    st.markdown("## 🏠 Macro Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Structural Quad", sq)
    c2.metric("Prices Loaded", len(prices))
    c3.metric("Bottleneck Tickers", len(get_bottleneck_tickers()))
    c4.metric("Timestamp", datetime.now().strftime("%H:%M"))

    st.markdown("### 📰 Narrative Snapshot")
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
      <div class="narrative-card"><div class="narrative-headline">🤖 AI Compute</div><div class="narrative-sub">GPU + HBM + Power bottleneck. Multi-quarter bull.</div></div>
      <div class="narrative-card" style="border-left-color:#F85149;"><div class="narrative-headline">🔥 Energy</div><div class="narrative-sub">Hormuz risk + grid interconnection queue.</div></div>
      <div class="narrative-card" style="border-left-color:#D29922;"><div class="narrative-headline">🇮🇩 Indonesia</div><div class="narrative-sub">Resource nationalism + banking NIM.</div></div>
      <div class="narrative-card" style="border-left-color:#A855F7;"><div class="narrative-headline">₿ Crypto</div><div class="narrative-sub">Halving squeeze + ETF flows.</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚡ Asset Pulse (21D)")
    pulse = [("SPY","US Eq"),("QQQ","Tech"),("IWM","Small"),("GLD","Gold"),("TLT","Bonds"),("BTC-USD","BTC"),("ETH-USD","ETH")]
    labels, vals, cols = [], [], []
    for t, l in pulse:
        s = prices.get(t)
        if s is not None and len(s) >= 22:
            try:
                s = pd.to_numeric(pd.Series(s), errors="coerce").dropna()
                ret = float(s.iloc[-1] / s.iloc[-22] - 1)
                labels.append(l); vals.append(ret*100); cols.append(GREEN if ret>0 else RED)
            except: pass
    if labels:
        fig = go.Figure(go.Bar(x=vals, y=labels, orientation="h", marker_color=cols,
                               text=[f"{v:+.1f}%" for v in vals], textposition="outside", textfont=dict(color=TEXT_PRIMARY, size=10)))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_PRIMARY), height=120,
                          margin=dict(t=10,b=10,l=60,r=40), xaxis=dict(gridcolor="#21262d"))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ═══════════════════════════════════════════════════════════════════
# MAIN NAV
# ═══════════════════════════════════════════════════════════════════
def main():
    with st.sidebar:
        st.markdown("## 📊 MacroRegime Pro v40")
        st.markdown("<div style='font-size:0.65rem;color:#484F58;'>Hedgeye Deep Research Edition</div>", unsafe_allow_html=True)
        page = st.radio("Navigate", [
            "🏠 Dashboard", "⚡ Alpha Center", "🇺🇸 US Stocks",
            "💱 Forex", "🛢️ Commodities", "₿ Crypto", "🇮🇩 IHSG",
            "🎭 Themes", "📋 Playbook", "🧠 GIP Model"
        ], label_visibility="collapsed")
        st.divider()
        st.markdown("<div style='font-size:0.6rem;color:#484F58;'>TRR/LRR: Pine v20.2 ported<br>Options: SpotGamma proxy<br>COT: CFTC proxy<br>On-chain: Whale proxy<br>Broker: IDX proxy</div>", unsafe_allow_html=True)

    if page == "🏠 Dashboard": page_dashboard()
    elif page == "⚡ Alpha Center": page_alpha()
    elif page == "🇺🇸 US Stocks": page_us_stocks()
    elif page == "💱 Forex": page_forex()
    elif page == "🛢️ Commodities": page_commodities()
    elif page == "₿ Crypto": page_crypto()
    elif page == "🇮🇩 IHSG": page_ihsg()
    elif page == "🎭 Themes": page_themes()
    elif page == "📋 Playbook": page_playbook()
    elif page == "🧠 GIP Model": page_gip()

if __name__ == "__main__":
    main()
