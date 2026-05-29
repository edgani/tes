"""engines/keith_market_filter.py — Keith Fractal Market Filter v1.0

Taro di folder engines/, lalu di orchestrator.py import:
    from engines.keith_market_filter import apply_keith_market_filter, get_favored_sectors
"""

import logging
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

# Quad → favored sectors/assets (dynamic, bukan hardcode Q2)
QUAD_SECTOR_MAP = {
    "Q1": {
        "favored": ["XLK", "XLY", "XLF", "XLC", "BTC-USD", "ETH-USD", "IBIT", "QQQ", "SPY"],
        "avoid": ["XLU", "XLP", "TLT", "GLD", "DXY", "UUP"],
        "theme": "Goldilocks — growth + low volatility",
    },
    "Q2": {
        "favored": ["XLE", "XLI", "XLB", "KRE", "IWM", "CL=F", "GC=F", "HG=F", "SI=F", "UNG", "USO"],
        "avoid": ["TLT", "IEF", "XLK", "QQQ"],  # tech suffers in reflation early
        "theme": "Reflation — commodity breakout, value over growth",
    },
    "Q3": {
        "favored": ["GLD", "SLV", "XLP", "XLU", "TLT", "IEF", "VZ", "T"],
        "avoid": ["XLY", "XLK", "KRE", "IWM", "XLE", "CL=F"],
        "theme": "Stagflation — defensive + real assets + duration",
    },
    "Q4": {
        "favored": ["TLT", "IEF", "XLU", "XLP", "GLD", "BIL", "SHY"],
        "avoid": ["XLE", "XLI", "XLB", "KRE", "IWM", "BTC-USD", "ETH-USD"],
        "theme": "Deflation — duration + quality + cash proxies",
    },
}

# Ticker → sector mapping (simplified, expand as needed)
TICKER_SECTOR_MAP = {
    "SPY": "XLK", "QQQ": "XLK", "IWM": "IWM", "XLK": "XLK", "XLY": "XLY",
    "XLF": "XLF", "XLE": "XLE", "XLI": "XLI", "XLB": "XLB", "XLU": "XLU",
    "XLP": "XLP", "XLC": "XLC", "KRE": "KRE", "TLT": "TLT", "IEF": "IEF",
    "GLD": "GLD", "SLV": "SLV", "USO": "USO", "UNG": "UNG", "CPER": "CPER",
    "CL=F": "XLE", "GC=F": "GLD", "SI=F": "SLV", "HG=F": "XLB", "NG=F": "UNG",
    "BTC-USD": "BTC-USD", "ETH-USD": "ETH-USD", "IBIT": "BTC-USD", "ETHA": "ETH-USD",
    "DXY": "DXY", "UUP": "DXY", "EURUSD=X": "FX", "GBPUSD=X": "FX", "JPY=X": "FX",
    "NXT": "XLK", "AMPH": "XLK", "HLIT": "XLK", "COHR": "XLK", "LITE": "XLK", "MRVL": "XLK",
    "VST": "XLU", "CEG": "XLU", "BE": "XLU", "SMR": "XLU", "OKLO": "XLU",
    "FRO": "XLE", "TK": "XLE", "INSW": "XLE", "STNG": "XLE",
    "NTR": "XLB", "MOS": "XLB", "CF": "XLB",
    "MP": "XLB", "LYSDY": "XLB", "UROY": "XLU", "CCJ": "XLU",
    "MSTR": "BTC-USD", "COIN": "XLK", "HOOD": "XLK",
    "ADRO.JK": "XLE", "ITMG.JK": "XLE", "NCKL.JK": "XLB", "ANTM.JK": "GLD",
    "BRMS.JK": "GLD", "BBRI.JK": "XLF", "BMRI.JK": "XLF",
}

def get_favored_sectors(current_quad: str) -> Dict[str, List[str]]:
    """Return favored/avoid lists untuk quad saat ini."""
    quad = current_quad.upper() if current_quad else "Q2"
    if quad not in QUAD_SECTOR_MAP:
        quad = "Q2"
    return QUAD_SECTOR_MAP[quad]

def apply_keith_market_filter(tickers: List[str],
                                keith_signals: Dict[str, Dict],
                                current_quad: str) -> Dict[str, List[str]]:
    """
    Filter ticker list per market tab berdasarkan:
    1. Keith fractal signal (skip BEARISH)
    2. Quad sector alignment (skip AVOID sectors)
    3. Breadth signal (kalau <20% bullish, warning)

    Returns: {"passed": [...], "avoided": [...], "meta": {...}}
    """
    quad_data = get_favored_sectors(current_quad)
    favored_sectors = set(quad_data["favored"])
    avoid_sectors = set(quad_data["avoid"])

    passed = []
    avoided = []
    keith_bullish = 0
    keith_bearish = 0
    keith_neutral = 0

    for t in tickers:
        ks = keith_signals.get(t, {})
        keith_trade = ks.get("keith_trade", "NEUTRAL")
        sector = TICKER_SECTOR_MAP.get(t, "UNKNOWN")

        if keith_trade == "BEARISH":
            avoided.append({"ticker": t, "reason": "Keith BEARISH", "sector": sector})
            keith_bearish += 1
            continue

        if sector in avoid_sectors:
            avoided.append({"ticker": t, "reason": f"Quad avoid sector ({sector})", "sector": sector})
            continue

        passed.append(t)
        if keith_trade == "BULLISH":
            keith_bullish += 1
        else:
            keith_neutral += 1

    total = len(tickers)
    bullish_pct = round(keith_bullish / total * 100, 1) if total else 0

    meta = {
        "quad": current_quad,
        "theme": quad_data["theme"],
        "total": total,
        "passed": len(passed),
        "avoided": len(avoided),
        "keith_bullish": keith_bullish,
        "keith_bearish": keith_bearish,
        "keith_neutral": keith_neutral,
        "bullish_pct": bullish_pct,
        "breadth_signal": "BULLISH" if bullish_pct > 60 else "BEARISH" if keith_bearish > (total * 0.4) else "NEUTRAL",
    }

    logger.info("Keith filter: %d passed, %d avoided | breadth=%s", len(passed), len(avoided), meta["breadth_signal"])
    return {"passed": passed, "avoided": avoided, "meta": meta}

def keith_breadth_summary(keith_signals: Dict[str, Dict]) -> Dict:
    """Summary 37 signals style (Keith tweet: '5 of 37 bearish')."""
    bullish = sum(1 for v in keith_signals.values() if v.get("keith_trade") == "BULLISH")
    bearish = sum(1 for v in keith_signals.values() if v.get("keith_trade") == "BEARISH")
    neutral = sum(1 for v in keith_signals.values() if v.get("keith_trade") not in ("BULLISH", "BEARISH"))
    total = bullish + bearish + neutral
    return {
        "total_signals": total,
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral,
        "bullish_pct": round(bullish / total * 100, 1) if total else 0,
        "bearish_pct": round(bearish / total * 100, 1) if total else 0,
        "keith_quote": f"Only {bearish} of the {total} Risk Range Signals signaling Bearish TREND",
    }
