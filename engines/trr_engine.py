
"""
TRR/LRR Engine v20.3 — Ported from Pine Script MQA v20.2 [Hedgeye Final + vPOC Enhanced]
Basis: previous close (not SMA) — matches forum subscriber confirmation.
Inputs: Price, Volume (validation only), Volatility (IV preferred, RV fallback).
Asymmetric bands: bullish lower 2.3× wider than upper; bearish reverse.
Fractal: Hurst R/S adjustment.
"""
import numpy as np
import pandas as pd

def hurst_rs(series, max_lag=20):
    """Rescaled Range (R/S) Hurst exponent — Pine f_hurst equivalent."""
    if len(series) < max_lag * 2:
        return 0.5
    lags = range(2, min(max_lag, len(series)//4) + 1)
    tau = []
    for lag in lags:
        diffs = np.abs(np.diff(series[::lag])) if len(series[::lag]) > 1 else [0]
        if len(diffs) > 0 and np.mean(diffs) > 0:
            tau.append(np.log(np.mean(diffs)))
        else:
            tau.append(np.log(1e-9))
    if len(tau) < 2:
        return 0.5
    x = np.log(list(lags))
    y = np.array(tau)
    # Linear regression
    A = np.vstack([x, np.ones(len(x))]).T
    m, c = np.linalg.lstsq(A, y, rcond=None)[0]
    H = max(0.1, min(0.9, m))
    return H

def calc_trr_lrr(s: pd.Series,
                 trade_len=15, trend_len=63, tail_len=252,
                 m_trade=1.50, m_trend=2.75, m_tail=5.50,
                 skew_mag=0.55,
                 vol_len=14,
                 use_fractal=True, fractal_weight=0.35,
                 hurst_max_lag=20,
                 use_v19model=True):
    """
    Returns dict with trade/trend/tail TRR/LRR + phase + formation.
    s: price series (daily)
    """
    s = pd.to_numeric(s, errors="coerce").dropna()
    if len(s) < 60:
        return None

    px = float(s.iloc[-1])

    # Log returns
    log_ret = np.log(s / s.shift(1)).dropna()

    # Realized vol (annualized)
    realized_vol = log_ret.tail(vol_len).std() * np.sqrt(252)
    if pd.isna(realized_vol) or realized_vol == 0:
        realized_vol = 0.20

    # Vol-of-Vol + RV momentum (VASP)
    vol_of_vol = log_ret.rolling(20).std().tail(20).std()
    if pd.isna(vol_of_vol): vol_of_vol = 0.0
    rv_sma50 = log_ret.rolling(50).std().mean()
    rv_momentum = (realized_vol / rv_sma50 - 1.0) if rv_sma50 and rv_sma50 > 0 else 0.0

    vov_term = 1.0 + max(vol_of_vol * 0.30, -0.5)
    rv_term  = 1.0 + rv_momentum * 0.10
    vasp_mult = max(vov_term * rv_term, 0.30)
    vasp_vol = realized_vol * vasp_mult
    daily_vol = vasp_vol / np.sqrt(252)

    # Hurst (fractal)
    def get_hurst(length):
        if not use_fractal or len(s) < length * 2:
            return 0.5
        return hurst_rs(s.tail(length).values, max_lag=min(hurst_max_lag, length//4))

    H_trade = get_hurst(trade_len)
    H_trend = get_hurst(trend_len)
    H_tail  = get_hurst(tail_len) if len(s) >= tail_len else 0.5

    f_trade = 1.0 + (2.0 - H_trade - 1.5) * fractal_weight
    f_trend = 1.0 + (2.0 - H_trend - 1.5) * fractal_weight
    f_tail  = 1.0 + (2.0 - H_tail  - 1.5) * fractal_weight

    # Basis = previous close (v19 model)
    basis = float(s.iloc[-2]) if len(s) >= 2 else px

    # Widths
    base_trade_w = px * daily_vol * m_trade * f_trade
    base_trend_w = px * daily_vol * m_trend * f_trend
    base_tail_w  = px * daily_vol * m_tail  * f_tail

    # Trend signal (21/63 SMA cross)
    sma21 = s.tail(63).rolling(21).mean().iloc[-1] if len(s) >= 21 else px
    sma63 = s.tail(63).rolling(63).mean().iloc[-1] if len(s) >= 63 else px
    if pd.isna(sma21) or pd.isna(sma63):
        trend_signal = 0
    else:
        if sma21 > sma63 * 1.005:
            trend_signal = 1
        elif sma21 < sma63 * 0.995:
            trend_signal = -1
        else:
            trend_signal = 0

    # Asymmetric skew
    def apply_skew(w, phase, skew):
        if phase == 1:   # bullish
            return w * (1.0 + skew), w * (1.0 - skew * 0.6)
        elif phase == -1: # bearish
            return w * (1.0 - skew * 0.6), w * (1.0 + skew)
        else:
            return w, w

    eff_phase = trend_signal if use_v19model else 0

    trade_lower_w, trade_upper_w = apply_skew(base_trade_w, eff_phase, skew_mag)
    trend_lower_w, trend_upper_w = apply_skew(base_trend_w, eff_phase, skew_mag * 0.6)
    tail_lower_w,  tail_upper_w  = apply_skew(base_tail_w,  eff_phase, skew_mag * 0.3)

    trade_trr = basis + trade_upper_w
    trade_lrr = basis - trade_lower_w
    trend_trr = basis + trend_upper_w
    trend_lrr = basis - trend_lower_w
    tail_trr  = basis + tail_upper_w
    tail_lrr  = basis - tail_lower_w

    # Formation
    if px > trend_trr and px > tail_trr:
        formation = "BULLISH"
        side = "long"
    elif px < trend_lrr and px < tail_lrr:
        formation = "BEARISH"
        side = "short"
    elif px > trend_trr:
        formation = "BULLISH_BIAS"
        side = "long"
    elif px < trend_lrr:
        formation = "BEARISH_BIAS"
        side = "short"
    else:
        formation = "NEUTRAL"
        side = "neutral"

    # Trade-range override
    if formation == "NEUTRAL":
        spread = trade_trr - trade_lrr
        pos = (px - trade_lrr) / spread if spread > 0 else 0.5
        if pos <= 0.35:
            formation = "OVERSOLD"; side = "long"
        elif pos >= 0.65:
            formation = "OVERBOUGHT"; side = "short"

    return {
        "price": px,
        "basis": basis,
        "trade_trr": trade_trr, "trade_lrr": trade_lrr,
        "trend_trr": trend_trr, "trend_lrr": trend_lrr,
        "tail_trr": tail_trr,   "tail_lrr": tail_lrr,
        "formation": formation,
        "side": side,
        "trend_signal": trend_signal,
        "hurst": {"trade": H_trade, "trend": H_trend, "tail": H_tail},
        "daily_vol": daily_vol,
        "realized_vol": realized_vol,
    }
