
"""
IHSG Broker Proxy v40
Detects: Real Accumulation, Real Distribution, Crossing (wash trade), Cornering Supply
References: Ajaib, IDX broker summary mechanics
"""
import pandas as pd
import numpy as np

def analyze_broker(ticker, prices):
    s = prices.get(ticker)
    if s is None or len(s) < 30:
        return None
    try:
        s = pd.to_numeric(pd.Series(s), errors="coerce").dropna()
        if len(s) < 30: return None
        px = float(s.iloc[-1])
        r5d = float(s.iloc[-1] / s.iloc[-6] - 1) if len(s) >= 6 else 0
        r20d = float(s.iloc[-1] / s.iloc[-21] - 1) if len(s) >= 21 else r5d
        vol5 = float(s.tail(5).std())
        vol20 = float(s.tail(20).std()) if len(s) >= 20 else vol5
        vol60 = float(s.tail(60).std()) if len(s) >= 60 else vol20
        range5 = float(s.tail(5).max() - s.tail(5).min())
        range20 = float(s.tail(20).max() - s.tail(20).min()) if len(s) >= 20 else range5

        # Crossing: high vol but price flat
        crossing = False
        if vol20 > 0 and vol5/vol20 > 1.5 and range5/max(range20, 0.001) < 0.15:
            crossing = True

        # Cornering: volume drying up then spike
        cornering = False
        if vol60 > 0 and vol20/vol60 < 0.5 and r5d > 0.03:
            cornering = True

        real_acc = r5d > 0.03 and r20d > 0.05 and not crossing
        real_dist = r5d < -0.03 and r20d < -0.05 and not crossing

        conf = 0
        signal = "NEUTRAL"
        if real_acc:
            conf = min(100, int(50 + abs(r5d)*500))
            signal = "ACCUMULATION"
        elif real_dist:
            conf = min(100, int(50 + abs(r5d)*500))
            signal = "DISTRIBUTION"
        elif crossing:
            conf = 70
            signal = "CROSSING"
        elif cornering:
            conf = 65
            signal = "CORNERING"

        return {
            "signal": signal, "confidence": conf,
            "real_accumulation": real_acc, "real_distribution": real_dist,
            "crossing_detected": crossing, "cornering_supply": cornering,
            "r5d": round(r5d, 4), "r20d": round(r20d, 4),
            "vol_ratio": round(vol5/vol20, 2) if vol20>0 else 1.0,
            "range_ratio": round(range5/max(range20, 0.001), 2),
        }
    except Exception:
        return None

def broker_html(data, ticker):
    if not data:
        return "<div style='font-size:0.7rem;color:#484F58;'>Broker data unavailable</div>"
    sig = data["signal"]
    color = {"ACCUMULATION":"#3FB950","DISTRIBUTION":"#F85149","CROSSING":"#D29922","CORNERING":"#A855F7","NEUTRAL":"#8B949E"}.get(sig, "#8B949E")
    emoji = {"ACCUMULATION":"📈","DISTRIBUTION":"📉","CROSSING":"⚠️","CORNERING":"🎯","NEUTRAL":"⚪"}.get(sig, "⚪")
    return f"""
    <div style="background:#0D1117;border:1px solid {color}40;border-radius:6px;padding:8px 10px;margin:4px 0;">
      <div style="font-size:0.7rem;color:#8B949E;text-transform:uppercase;font-weight:600;">🇮🇩 Broker Intelligence (IDX)</div>
      <div style="font-size:0.85rem;color:{color};font-weight:700;">{emoji} {sig} ({data['confidence']}%)</div>
      <div style="font-size:0.68rem;color:#E6EDF3;">R5D: {data['r5d']:+.1%} · R20D: {data['r20d']:+.1%}</div>
      <div style="font-size:0.65rem;color:#484F58;">Vol ratio: {data['vol_ratio']:.1f}x · Range ratio: {data['range_ratio']:.1f}x</div>
      <div style="font-size:0.6rem;color:#484F58;margin-top:2px;">
        {'Real accumulation detected — genuine buying pressure' if data['real_accumulation'] else ''}
        {'Real distribution detected — genuine selling pressure' if data['real_distribution'] else ''}
        {'Crossing/wash trade warning — high volume flat price' if data['crossing_detected'] else ''}
        {'Cornering supply — volume dried up then spiked' if data['cornering_supply'] else ''}
      </div>
    </div>
    """
