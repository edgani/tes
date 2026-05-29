"""engines/keith_market_filter.py — Keith Fractal Market Filter v2.0

REDESIGN 2026-05-29:
- Define Keith's 37 Risk Range™ Signals universe (research-backed)
- keith_breadth_summary ONLY counts tickers in KEITH_UNIVERSE_37
- apply_keith_market_filter works for ANY ticker list (full universe or curated)
"""

import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# KEITH'S 37 RISK RANGE™ SIGNALS — Representative Universe
# Source: Mark Bunting Substack (Hedgeye subscriber) + Keith podcast
# "37 bonds, global stock indices, currencies, commodities, major tech, Bitcoin"
# ═══════════════════════════════════════════════════════════════════════
KEITH_UNIVERSE_37 = {
    # US Equity Indices (5)
    "SPY", "QQQ", "IWM", "DIA", "VIX",
    # US Sectors (8)
    "XLK", "XLF", "XLE", "XLI", "XLB", "XLU", "XLP", "XLY",
    # Bonds / Rates (5)
    "TLT", "IEF", "HYG", "LQD", "SHY",
    # FX / DXY (5)
    "DX-Y.NYB", "UUP", "EURUSD=X", "GBPUSD=X", "JPY=X",
    # Commodities (6)
    "GLD", "SLV", "CL=F", "GC=F", "SI=F", "NG=F",
    # Major Tech / Individual Names (6)
    "AAPL", "MSFT", "NVDA", "TSLA", "META", "GOOGL",
    # Crypto (1)
    "BTC-USD",
    # Global / EM (1)
    "EEM",
}

# Quad → favored sectors/assets (dynamic)
QUAD_SECTOR_MAP = {
    "Q1": {
        "favored": ["XLK", "XLY", "XLF", "XLC", "BTC-USD", "QQQ", "SPY", "IWM", "AAPL", "MSFT", "NVDA"],
        "avoid": ["XLU", "XLP", "TLT", "GLD", "DX-Y.NYB", "UUP"],
        "theme": "Goldilocks — growth + low volatility",
    },
    "Q2": {
        "favored": ["XLE", "XLI", "XLB", "XLF", "IWM", "CL=F", "GC=F", "SI=F", "NG=F", "GLD", "SLV"],
        "avoid": ["TLT", "IEF", "XLK", "QQQ", "BTC-USD"],
        "theme": "Reflation — commodity breakout, value over growth",
    },
    "Q3": {
        "favored": ["GLD", "SLV", "XLP", "XLU", "TLT", "IEF", "DX-Y.NYB", "UUP"],
        "avoid": ["XLY", "XLK", "IWM", "XLE", "CL=F", "BTC-USD"],
        "theme": "Stagflation — defensive + real assets + duration",
    },
    "Q4": {
        "favored": ["TLT", "IEF", "XLU", "XLP", "GLD", "SHY", "DX-Y.NYB"],
        "avoid": ["XLE", "XLI", "XLB", "IWM", "BTC-USD", "QQQ", "XLK"],
        "theme": "Deflation — duration + quality + cash proxies",
    },
}

# Ticker → sector mapping (simplified)
TICKER_SECTOR_MAP = {
    "SPY": "SPY", "QQQ": "QQQ", "IWM": "IWM", "DIA": "DIA", "VIX": "VIX",
    "XLK": "XLK", "XLF": "XLF", "XLE": "XLE", "XLI": "XLI", "XLB": "XLB",
    "XLU": "XLU", "XLP": "XLP", "XLY": "XLY", "XLC": "XLC",
    "TLT": "TLT", "IEF": "IEF", "HYG": "HYG", "LQD": "LQD", "SHY": "SHY",
    "DX-Y.NYB": "DXY", "UUP": "DXY", "EURUSD=X": "FX", "GBPUSD=X": "FX",
    "JPY=X": "FX", "AUDUSD=X": "FX", "CADUSD=X": "FX",
    "GLD": "GLD", "SLV": "SLV", "CL=F": "CL=F", "GC=F": "GC=F",
    "SI=F": "SI=F", "NG=F": "NG=F", "HG=F": "HG=F",
    "AAPL": "AAPL", "MSFT": "MSFT", "NVDA": "NVDA", "TSLA": "TSLA",
    "META": "META", "GOOGL": "GOOGL", "AMZN": "AMZN", "AMD": "AMD",
    "BTC-USD": "BTC-USD", "ETH-USD": "ETH-USD", "EEM": "EEM", "VWO": "VWO",
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
    """Summary 37 signals style (Keith tweet: '5 of 37 bearish').

    Hanya count ticker yang ada di KEITH_UNIVERSE_37.
    Ticker di universe yang tidak punya signal di-count sebagai NEUTRAL.
    """
    # Filter cuma keith signals untuk ticker di Keith universe
    keith_universe_signals = {t: v for t, v in keith_signals.items() if t in KEITH_UNIVERSE_37}

    bullish = sum(1 for v in keith_universe_signals.values() if v.get("keith_trade") == "BULLISH")
    bearish = sum(1 for v in keith_universe_signals.values() if v.get("keith_trade") == "BEARISH")
    neutral = sum(1 for v in keith_universe_signals.values() if v.get("keith_trade") not in ("BULLISH", "BEARISH"))

    # Ticker di universe yang tidak ada signal = NEUTRAL
    missing = KEITH_UNIVERSE_37 - set(keith_universe_signals.keys())
    neutral += len(missing)
    total = len(KEITH_UNIVERSE_37)

    return {
        "total_signals": total,
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral,
        "bullish_pct": round(bullish / total * 100, 1) if total else 0,
        "bearish_pct": round(bearish / total * 100, 1) if total else 0,
        "keith_quote": f"Only {bearish} of the {total} Risk Range™ Signals signaling Bearish TREND",
        "missing_tickers": sorted(missing),
    }

def is_keith_universe(ticker: str) -> bool:
    """Check if ticker is in Keith's 37 Risk Range™ Signals."""
    return ticker in KEITH_UNIVERSE_37
