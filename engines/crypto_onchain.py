
"""
Crypto On-Chain Proxy v40
Whale accumulation, funding extremes, OI proxy, large orders.
"""
import pandas as pd
import numpy as np

def analyze_onchain(ticker, prices):
    s = prices.get(ticker)
    if s is None or len(s) < 22:
        return None
    try:
        s = pd.to_numeric(pd.Series(s), errors="coerce").dropna()
        if len(s) < 22: return None
        px = float(s.iloc[-1])
        r1m = float(s.iloc[-1] / s.iloc[-22] - 1)
        r7d = float(s.iloc[-1] / s.iloc[-8] - 1) if len(s) >= 8 else r1m
        r5d = float(s.iloc[-1] / s.iloc[-6] - 1) if len(s) >= 6 else r1m
        vol20 = float(s.tail(20).std())
        vol40 = float(s.tail(40).std()) if len(s) >= 40 else vol20
        vol5  = float(s.tail(5).std()) if len(s) >= 5 else vol20

        whale = "NEUTRAL"
        if r7d > 0.05 and (vol5/vol20 if vol20>0 else 1) < 1.2:
            whale = "ACCUMULATING"
        elif r7d < -0.05 and (vol5/vol20 if vol20>0 else 1) > 1.3:
            whale = "DISTRIBUTING"

        funding = r1m * 0.001
        funding_extreme = abs(funding) > 0.0005
        oi_proxy = (vol5 / vol20) if vol20 > 0 else 1.0
        large_orders = oi_proxy > 2.0 and abs(r5d) < 0.02

        return {
            "price": px, "r1m": r1m, "r7d": r7d, "r5d": r5d,
            "whale_signal": whale, "funding_proxy": round(funding, 6),
            "funding_extreme": funding_extreme, "oi_proxy": round(oi_proxy, 2),
            "large_orders_detected": large_orders,
            "vol_change": round((vol20/vol40 - 1) if vol40>0 else 0, 4),
        }
    except Exception:
        return None

def onchain_html(data, ticker):
    if not data:
        return "<div style='font-size:0.7rem;color:#484F58;'>On-chain data unavailable</div>"
    w = data["whale_signal"]
    wcolor = "#3FB950" if w == "ACCUMULATING" else "#F85149" if w == "DISTRIBUTING" else "#8B949E"
    return f"""
    <div style="background:#0D1117;border:1px solid {wcolor}40;border-radius:6px;padding:8px 10px;margin:4px 0;">
      <div style="font-size:0.7rem;color:#8B949E;text-transform:uppercase;font-weight:600;">⛓️ On-Chain Intelligence</div>
      <div style="font-size:0.85rem;color:{wcolor};font-weight:700;">🐋 Whale: {w}</div>
      <div style="font-size:0.68rem;color:#E6EDF3;">R7D: {data['r7d']:+.1%} · Funding: {data['funding_proxy']:.6f} {'🚨 EXTREME' if data['funding_extreme'] else ''}</div>
      <div style="font-size:0.65rem;color:#484F58;">OI proxy: {data['oi_proxy']:.1f}x · Large orders: {'YES' if data['large_orders_detected'] else 'NO'}</div>
    </div>
    """
