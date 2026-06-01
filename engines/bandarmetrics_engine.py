"""engines/bandarmetrics_engine.py — Bandarmology indicators from OHLCV (LPM/DTE/VolRot/Intensity)

Implements the OHLCV-derivable bandarmology indicators (calibrated VWAP-delta / ADV formulas):
  • LPM  — Liquidity Pressure Model (cumulative VWAP-delta, EMA-smoothed) → silent accumulation
  • DTE / Real DTE — days-to-exit from average daily $-volume (how trapped the inventory is)
  • Volume Rotation — efficiency of share transfer (green=clean / yellow=noise / red=distribution)
  • Intensity — LPM rate-of-change z-score spikes (fires BEFORE price moves)
  • Phase — rule-based Wyckoff (ACCUMULATION / MARKUP / DISTRIBUTION / MARKDOWN)
  • Score — 0-100 composite

HONEST CEILING: this is the OHLCV approximation. The real bandarmetrics edge (foreign Type-F
flow + broker-summary clustering / nominee detection) needs IDX broker data the user does NOT
have. So treat phases/score as price/volume inference, not the broker-confirmed article version.
Requires OHLCV+Volume (Close-only is not enough). Returns {} if data insufficient.
"""
from __future__ import annotations
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def _ema(s, span):
    return s.ewm(span=span, adjust=False).mean()


def compute(df, vwap_win: int = 20, lpm_smooth: int = 20, adv_win: int = 60) -> Dict:
    """df: DataFrame with columns Open, High, Low, Close, Volume (daily). Returns indicator dict."""
    import pandas as pd
    import numpy as np
    if df is None or len(df) < max(adv_win, 60):
        return {}
    try:
        o, h, l, c, v = (pd.to_numeric(df[k], errors="coerce")
                         for k in ("Open", "High", "Low", "Close", "Volume"))
    except (KeyError, TypeError):
        return {}
    if c.dropna().empty or v.fillna(0).sum() == 0:
        return {}

    typ = (h + l + c) / 3.0
    # ── LPM: cumulative VWAP-delta, EMA-smoothed ──
    vwap = (typ * v).rolling(vwap_win).sum() / v.rolling(vwap_win).sum().replace(0, np.nan)
    delta = (c - vwap) * v
    lpm = _ema(delta.fillna(0).cumsum(), lpm_smooth)

    # ── DTE / Real DTE: |LPM| over average daily $-volume ──
    adv = (v * typ).rolling(adv_win).mean()
    dte = (lpm.abs() / adv.replace(0, np.nan))
    real_dte = (lpm.abs() / (adv.replace(0, np.nan) * 0.35))

    # ── Volume Rotation: efficiency of transfer ──
    rng = (h - l).replace(0, np.nan)
    close_pos = ((c - l) / rng).clip(0, 1)
    direction = np.sign(c - o)
    vol_z = ((v - v.rolling(20).mean()) / v.rolling(20).std().replace(0, np.nan))
    efficiency = direction * (2 * close_pos - 1)
    rot_score = efficiency * vol_z.abs().clip(upper=3) / 3.0

    def _rot_color(x):
        if pd.isna(x):
            return "yellow"
        return "green" if x > 0.3 else "red" if x < -0.3 else "yellow"

    # ── Intensity: LPM ROC z-score spikes ──
    lpm_roc = lpm - lpm.shift(10)
    z = (lpm_roc - lpm_roc.rolling(20).mean()) / lpm_roc.rolling(20).std().replace(0, np.nan)
    intensity = z.abs().where(z.abs() > 1.5, 0.0)

    # ── latest readings ──
    def _last(s, d=0.0):
        try:
            x = float(s.dropna().iloc[-1]); return x if np.isfinite(x) else d
        except (IndexError, ValueError):
            return d

    lpm_now = _last(lpm); lpm_slope = lpm_now - _last(lpm.shift(20))
    dte_now = _last(dte); intensity_now = _last(intensity)
    rot_now = _last(rot_score)
    price_chg_20 = _pct(_last(c), _last(c.shift(20)))

    # ── rule-based phase ──
    phase = _phase(lpm_slope, intensity_now, rot_now, price_chg_20)
    # ── composite score 0-100 (accumulation-positive) ──
    score = _score(lpm_slope, intensity_now, rot_now, dte_now, phase)

    # avg-cost proxy = exponentially-weighted VWAP (recent weighted more)
    avgcost = _last(_ema(typ, 60))

    # rotation distribution over last 20d
    rot_tail = rot_score.dropna().tail(20)
    green = int((rot_tail > 0.3).sum()); red = int((rot_tail < -0.3).sum())
    yellow = int(len(rot_tail) - green - red)

    return {
        "ok": True,
        "lpm": round(lpm_now, 2), "lpm_slope_20": round(lpm_slope, 2),
        "lpm_rising": lpm_slope > 0,
        "dte": round(dte_now, 1), "real_dte": round(_last(real_dte), 1),
        "intensity": round(intensity_now, 2), "intensity_firing": intensity_now > 0,
        "rotation": _rot_color(rot_now), "rotation_score": round(rot_now, 3),
        "rotation_dist": {"green": green, "yellow": yellow, "red": red},
        "phase": phase, "score": int(round(score)),
        "avgcost": round(avgcost, 2),
        "series": {  # for charting (last ~252)
            "index": [str(x)[:10] for x in c.dropna().index[-252:]],
            "price": [round(x, 2) for x in c.dropna().tolist()[-252:]],
            "lpm": [round(x, 2) for x in lpm.reindex(c.dropna().index).fillna(0).tolist()[-252:]],
            "intensity": [round(x, 2) for x in intensity.reindex(c.dropna().index).fillna(0).tolist()[-252:]],
        },
        "note": "OHLCV approximation — foreign-flow + broker clustering need IDX broker data (unavailable).",
    }


def _pct(a, b):
    try:
        return (float(a) / float(b) - 1.0) if b else 0.0
    except (TypeError, ZeroDivisionError):
        return 0.0


def _phase(lpm_slope, intensity, rot_score, price_chg_20):
    """Wyckoff-style phase from LPM slope + intensity + rotation + recent price."""
    if lpm_slope > 0 and intensity > 0 and price_chg_20 > 0.08:
        return "MARKUP"
    if lpm_slope > 0 and price_chg_20 < 0.05:
        return "ACCUMULATION"          # LPM rising while price flat/down = silent accumulation
    if lpm_slope < 0 and rot_score < -0.2 and price_chg_20 > -0.03:
        return "DISTRIBUTION"          # LPM falling, red rotation, price toppy
    if lpm_slope < 0 and price_chg_20 < -0.05:
        return "MARKDOWN"
    return "NEUTRAL"


def _score(lpm_slope, intensity, rot_score, dte, phase):
    s = 50.0
    s += 18 if lpm_slope > 0 else -18
    s += min(12, intensity * 4) if intensity > 0 else 0
    s += 10 if rot_score > 0.3 else (-10 if rot_score < -0.3 else 0)
    s += {"ACCUMULATION": 12, "MARKUP": 8, "DISTRIBUTION": -15, "MARKDOWN": -20}.get(phase, 0)
    # high DTE = trapped inventory: mildly supportive in accumulation (can't dump), risky in distribution
    if dte > 30:
        s += 4 if phase in ("ACCUMULATION", "MARKUP") else -6
    return max(0, min(100, s))


def analyze_universe(ohlcv: Dict, **kw) -> Dict:
    """ohlcv: {ticker: DataFrame[OHLCV]}. Returns {ticker: indicator dict}."""
    out = {}
    for t, df in (ohlcv or {}).items():
        try:
            r = compute(df, **kw)
            if r:
                out[t] = r
        except Exception as e:
            logger.debug(f"bandarmetrics failed for {t}: {e}")
    return out
