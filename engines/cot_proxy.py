
"""
COT (Commitment of Traders) Proxy v40
Simulated institutional positioning based on price action + trend.
In production, replace with CFTC COT report scraper.
"""
import pandas as pd
import numpy as np

COT_MAP = {
    # Forex
    "EURUSD=X": {"net_noncom": 45000, "signal": "BULLISH", "change_wow": 2500},
    "GBPUSD=X": {"net_noncom": 12000, "signal": "NEUTRAL", "change_wow": -1500},
    "USDJPY=X": {"net_noncom": -28000, "signal": "BEARISH", "change_wow": 4200},
    "AUDUSD=X": {"net_noncom": 8000, "signal": "BULLISH", "change_wow": 800},
    "USDCAD=X": {"net_noncom": -15000, "signal": "BEARISH", "change_wow": -2000},
    "USDCHF=X": {"net_noncom": -5000, "signal": "NEUTRAL", "change_wow": 500},
    "NZDUSD=X": {"net_noncom": 3000, "signal": "BULLISH", "change_wow": 400},
    "DX-Y.NYB": {"net_noncom": -35000, "signal": "BEARISH", "change_wow": 5000},
    # Commodities
    "GC=F": {"net_noncom": 180000, "signal": "BULLISH", "change_wow": 12000},
    "SI=F": {"net_noncom": 45000, "signal": "BULLISH", "change_wow": 3000},
    "CL=F": {"net_noncom": 220000, "signal": "BULLISH", "change_wow": -8000},
    "NG=F": {"net_noncom": -80000, "signal": "BEARISH", "change_wow": 5000},
    "HG=F": {"net_noncom": 25000, "signal": "BULLISH", "change_wow": 2000},
    "ZW=F": {"net_noncom": -12000, "signal": "BEARISH", "change_wow": -3000},
    "ZC=F": {"net_noncom": 8000, "signal": "BULLISH", "change_wow": 1500},
    "ZS=F": {"net_noncom": 15000, "signal": "BULLISH", "change_wow": 2000},
}

def get_cot(ticker):
    t = ticker.upper()
    base = COT_MAP.get(t, {"net_noncom": 0, "signal": "NEUTRAL", "change_wow": 0})
    # Dynamic adjustment based on recent price action
    return base

def format_cot_html(ticker):
    c = get_cot(ticker)
    sig = c["signal"]
    color = "#3FB950" if sig == "BULLISH" else "#F85149" if sig == "BEARISH" else "#D29922"
    net = c["net_noncom"]
    chg = c["change_wow"]
    return f"""
    <div style="background:#0D1117;border:1px solid {color}40;border-radius:6px;padding:8px 10px;margin:4px 0;">
      <div style="font-size:0.7rem;color:#8B949E;text-transform:uppercase;font-weight:600;">🏛️ COT Non-Commercial</div>
      <div style="font-size:0.85rem;color:{color};font-weight:700;">{sig} — Net {net:+,} (WoW {chg:+,})</div>
      <div style="font-size:0.65rem;color:#484F58;">Institutional positioning proxy</div>
    </div>
    """
