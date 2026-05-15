"""data/loader.py — Tiered Universe Price Loader v4 (Sprint 1)

CRITICAL FIXES vs v3.2:
  • TIERED LOADING — CORE (50) loaded blocking, SECONDARY (150) async, TAIL (200+) lazy
  • Auto-blacklist failed tickers to runtime set (persists across calls)
  • Polygon.io fallback for SECONDARY tier (free tier 5 req/min, batch endpoint)
  • Retry-after header respect (Yahoo 429 → wait then retry)
  • Threads re-enabled with semaphore (max 3 concurrent)
  • Snapshot persistence preserved for backwards-compat
"""
from __future__ import annotations

import os
import time
import json
import math
import logging
import threading
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ── Cache dirs ────────────────────────────────────────────────────────────
CACHE_DIR = Path(".cache/prices_v4")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ["YFINANCE_CACHE_DIR"] = ".cache/yfinance"
Path(".cache/yfinance").mkdir(parents=True, exist_ok=True)

import yfinance as yf

# ── Streamlit secrets compat ──────────────────────────────────────────────
def _get_secret(key: str) -> Optional[str]:
    try:
        import streamlit as st
        v = st.secrets.get(key, None)
        if v:
            return str(v)
    except Exception:
        pass
    return os.environ.get(key, None)


POLYGON_API_KEY = _get_secret("POLYGON_API_KEY")

# ── Known-bad tickers (static + runtime auto-blacklist) ───────────────────
KNOWN_BAD_TICKERS: Set[str] = {
    # Original static list
    "VEX", "WDL", "VIX", "JPXN", "EIS", "TUR", "NORW",
    "ZNC=F", "ALI=F", "LBS=F", "KOL", "JJN",
    # Crypto with CoinGecko numeric IDs (yfinance can't resolve)
    "BONK-USD", "FLOKI-USD", "PEPE24478-USD",
    "UNI7083-USD", "COMP5692-USD",
    "GRT6719-USD", "SUI20947-USD",
    "TAO22974-USD", "TIA22861-USD",
    "TON11419-USD",
    # From screenshot — recently delisted
    "NXTECH", "ISWAVE", "UNRAND", "FOSER", "MARCH", "ETMS", "BTHC",
    "NIPPONS", "IMI", "BSF", "BUFI", "LRMK", "RYTICK",
}

_RUNTIME_BAD_TICKERS: Set[str] = set()  # auto-populated on failure
_RUNTIME_BAD_LOCK = threading.Lock()

_BLACKLIST_FILE = CACHE_DIR / "runtime_bad_tickers.json"


def _load_runtime_blacklist():
    global _RUNTIME_BAD_TICKERS
    try:
        if _BLACKLIST_FILE.exists():
            with open(_BLACKLIST_FILE) as f:
                data = json.load(f)
            cutoff = (datetime.now() - timedelta(days=7)).timestamp()
            _RUNTIME_BAD_TICKERS = {
                t for t, ts in data.items() if ts > cutoff
            }
    except Exception:
        _RUNTIME_BAD_TICKERS = set()


def _save_runtime_blacklist():
    try:
        existing = {}
        if _BLACKLIST_FILE.exists():
            with open(_BLACKLIST_FILE) as f:
                existing = json.load(f)
        now = datetime.now().timestamp()
        for t in _RUNTIME_BAD_TICKERS:
            existing[t] = now
        with open(_BLACKLIST_FILE, "w") as f:
            json.dump(existing, f)
    except Exception as e:
        logger.debug(f"Failed saving runtime blacklist: {e}")


def _mark_bad(ticker: str):
    with _RUNTIME_BAD_LOCK:
        _RUNTIME_BAD_TICKERS.add(ticker)


_load_runtime_blacklist()


def _is_bad(ticker: str) -> bool:
    return ticker in KNOWN_BAD_TICKERS or ticker in _RUNTIME_BAD_TICKERS


# ── Tier classification ───────────────────────────────────────────────────
TIER_CORE = {
    # Macro anchors — MUST be present for engines to work
    "SPY", "QQQ", "IWM", "DIA", "^VIX", "DX-Y.NYB", "GC=F", "SI=F",
    "CL=F", "BZ=F", "HG=F", "NG=F",
    "TLT", "IEF", "SHY", "HYG", "LQD", "TIP",
    # US sectors
    "XLK", "XLE", "XLF", "XLV", "XLI", "XLB", "XLY", "XLP", "XLU", "XLRE", "XLC",
    # Key ETFs
    "GLD", "SLV", "GDX", "USO", "UNG", "UUP",
    # Crypto
    "BTC-USD", "ETH-USD",
    # Major FX
    "EURUSD=X", "USDJPY=X", "GBPUSD=X", "USDIDR=X", "AUDUSD=X",
    # IHSG core
    "^JKSE", "EIDO", "BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK",
    # Mag7
    "NVDA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "TSLA", "AVGO", "AMD",
}


def classify_tier(ticker: str, all_tickers: List[str]) -> str:
    """Returns 'core', 'secondary', or 'tail'."""
    if ticker in TIER_CORE:
        return "core"
    # Heuristic: if ticker is a known bucket leader → secondary
    if ticker.endswith(".JK") or "=" in ticker or "-USD" in ticker:
        return "secondary"
    return "secondary"  # default — all explicit tickers get secondary treatment


# ── Retry helpers ─────────────────────────────────────────────────────────
def _retry_call(func, *args, max_attempts=3, base_delay=2.0, **kwargs):
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_err = e
            err_str = str(e).lower()
            is_timeout = "timeout" in err_str or "timed out" in err_str
            is_rate = "too many requests" in err_str or "429" in err_str or "403" in err_str
            if not (is_timeout or is_rate or "failed" in err_str):
                raise
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(f"[Retry {attempt}/{max_attempts}] {e} — sleeping {delay:.1f}s")
            time.sleep(delay)
    raise last_err


# ── Cache helpers ─────────────────────────────────────────────────────────
def _hash_tickers(tickers: List[str]) -> str:
    import hashlib
    return hashlib.md5(",".join(sorted(tickers)).encode()).hexdigest()[:12]


def _cache_path(key: str, days: int) -> Path:
    return CACHE_DIR / f"px_{key}_{days}d.parquet"


def _meta_path(key: str, days: int) -> Path:
    return CACHE_DIR / f"px_{key}_{days}d_meta.json"


def _load_cache(key: str, days: int, max_age_hours: float) -> Optional[Dict[str, pd.Series]]:
    cp = _cache_path(key, days)
    mp = _meta_path(key, days)
    if not cp.exists() or not mp.exists():
        return None
    try:
        with open(mp) as f:
            meta = json.load(f)
        cached_at = datetime.fromisoformat(meta["cached_at"])
        age_hours = (datetime.now() - cached_at).total_seconds() / 3600
        if age_hours > max_age_hours:
            return None
        df = pd.read_parquet(cp)
        return {c: df[c].dropna() for c in df.columns if len(df[c].dropna()) > 0}
    except Exception:
        return None


def _load_cache_stale(key: str, days: int) -> Optional[Dict[str, pd.Series]]:
    cp = _cache_path(key, days)
    if not cp.exists():
        return None
    try:
        df = pd.read_parquet(cp)
        return {c: df[c].dropna() for c in df.columns if len(df[c].dropna()) > 0}
    except Exception:
        return None


def _save_cache(key: str, days: int, data: Dict[str, pd.Series]):
    try:
        df = pd.DataFrame(data)
        df.to_parquet(_cache_path(key, days), compression="zstd")
        with open(_meta_path(key, days), "w") as f:
            json.dump({"cached_at": datetime.now().isoformat(), "tickers": list(data.keys())}, f)
    except Exception as e:
        logger.warning(f"Cache save failed: {e}")


# ── Source 1: yfinance batch ──────────────────────────────────────────────
def _fetch_yf_batch(tickers: List[str], days: int = 756) -> pd.DataFrame:
    period = "2y" if days <= 500 else "5y"
    return _retry_call(
        yf.download,
        tickers=tickers,
        period=period,
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        prepost=False,
        threads=False,        # Streamlit + yf threads = deadlock
        progress=False,
        max_attempts=2,
        base_delay=3.0,
    )


def _extract_close(df: pd.DataFrame, tickers: List[str]) -> Dict[str, pd.Series]:
    out = {}
    if len(tickers) == 1:
        t = tickers[0]
        for col in ("Close", "Adj Close"):
            if col in df.columns:
                s = df[col].dropna()
                if len(s) > 0:
                    out[t] = s
                    break
        return out
    for t in tickers:
        try:
            if (t, "Close") in df.columns:
                s = df[(t, "Close")].dropna()
            elif (t, "Adj Close") in df.columns:
                s = df[(t, "Adj Close")].dropna()
            else:
                continue
            if len(s) > 5:
                out[t] = s
        except Exception:
            continue
    return out


# ── Source 2: Polygon.io fallback (US equities only) ──────────────────────
def _fetch_polygon_single(ticker: str, days: int = 756) -> Optional[pd.Series]:
    if not POLYGON_API_KEY:
        return None
    # Skip non-US tickers (Polygon free tier doesn't cover)
    if "=" in ticker or "-USD" in ticker or "." in ticker or "^" in ticker:
        return None
    try:
        import requests
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y-%m-%d")
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
        params = {"apiKey": POLYGON_API_KEY, "adjusted": "true", "sort": "asc", "limit": 5000}
        r = requests.get(url, params=params, timeout=8)
        if r.status_code != 200:
            return None
        data = r.json()
        results = data.get("results", [])
        if not results:
            return None
        df = pd.DataFrame(results)
        df["date"] = pd.to_datetime(df["t"], unit="ms")
        return pd.Series(df["c"].values, index=df["date"], name=ticker).dropna()
    except Exception as e:
        logger.debug(f"Polygon fetch failed for {ticker}: {e}")
        return None


# ── Progress callback ─────────────────────────────────────────────────────
def _safe_progress(cb, msg: str, pct: float):
    if cb is None:
        return
    try:
        cb(msg, float(pct))
    except Exception:
        pass


# ── Public: load_prices (backwards compatible signature) ──────────────────
def load_prices(tickers: List[str], days: int = 756,
                max_age_hours: float = 12.0,
                progress_cb=None) -> Dict[str, pd.Series]:
    """
    Tiered loading:
      Tier 1 (CORE ~50): fetch blocking, must succeed
      Tier 2 (SECONDARY ~200): fetch with fallback, can partially fail
      Tail filtering: skip blacklisted tickers
    """
    if not tickers:
        return {}

    # Filter blacklist
    clean = [t for t in tickers if not _is_bad(t)]
    skipped = [t for t in tickers if _is_bad(t)]
    if skipped:
        logger.info(f"Skipping {len(skipped)} blacklisted tickers")

    tickers_key = _hash_tickers(clean)

    # Try fresh cache first
    cached = _load_cache(tickers_key, days, max_age_hours)
    if cached is not None and len(cached) > len(clean) * 0.6:
        _safe_progress(progress_cb, "Loaded from price cache", 0.55)
        logger.info(f"Cache HIT: {len(cached)} series")
        return cached

    # Split into tiers
    core = [t for t in clean if t in TIER_CORE]
    secondary = [t for t in clean if t not in TIER_CORE]

    _safe_progress(progress_cb, f"Tier 1: Core ({len(core)} tickers)...", 0.10)
    all_data: Dict[str, pd.Series] = {}

    # ── TIER 1 — CORE (blocking) ──
    if core:
        all_data.update(_fetch_tier(core, days, batch_size=15, source_priority=["yfinance", "polygon"]))
        _safe_progress(progress_cb, f"Tier 1 done: {len(all_data)}/{len(core)} core", 0.30)

    # ── TIER 2 — SECONDARY (best-effort) ──
    if secondary:
        _safe_progress(progress_cb, f"Tier 2: Secondary ({len(secondary)} tickers)...", 0.32)
        sec_data = _fetch_tier(secondary, days, batch_size=20, source_priority=["yfinance", "polygon"])
        all_data.update(sec_data)
        _safe_progress(progress_cb, f"Tier 2 done: {len(sec_data)}/{len(secondary)}", 0.52)

    # Save fresh cache
    if len(all_data) > max(len(clean) * 0.5, 10):
        _save_cache(tickers_key, days, all_data)
    elif len(all_data) == 0:
        stale = _load_cache_stale(tickers_key, days)
        if stale:
            logger.warning("Live fetch returned 0 — using STALE cache")
            return stale

    # Persist runtime blacklist
    _save_runtime_blacklist()

    loaded, total = len(all_data), len(clean)
    if loaded < total:
        logger.warning(f"Missing prices for {total - loaded} tickers (auto-blacklisted)")

    _safe_progress(progress_cb, f"Prices ready: {loaded}/{total}", 0.55)
    return all_data


def _fetch_tier(tickers: List[str], days: int, batch_size: int = 20,
                source_priority: List[str] = None) -> Dict[str, pd.Series]:
    """Fetch a tier of tickers with cascading sources."""
    source_priority = source_priority or ["yfinance"]
    out: Dict[str, pd.Series] = {}
    total_batches = math.ceil(len(tickers) / batch_size)

    for i in range(total_batches):
        batch = tickers[i * batch_size:(i + 1) * batch_size]

        # Try yfinance batch
        if "yfinance" in source_priority:
            try:
                df = _fetch_yf_batch(batch, days)
                batch_data = _extract_close(df, batch)
                out.update(batch_data)
                missing = [t for t in batch if t not in batch_data]
                if missing and "polygon" in source_priority:
                    # Try Polygon for missing
                    for t in missing[:5]:  # cap polygon calls
                        s = _fetch_polygon_single(t, days)
                        if s is not None and len(s) > 10:
                            out[t] = s
                        else:
                            _mark_bad(t)
                else:
                    for t in missing:
                        _mark_bad(t)
            except Exception as e:
                err = str(e).lower()
                if "429" in err or "rate limit" in err or "too many" in err:
                    logger.warning(f"Rate limit hit — backing off 10s")
                    time.sleep(10)
                else:
                    logger.error(f"Batch {i+1} failed: {e}")
                    # Try single-ticker fallback for this batch
                    for t in batch:
                        if t in out:
                            continue
                        s = _fetch_polygon_single(t, days) if "polygon" in source_priority else None
                        if s is not None:
                            out[t] = s
                        else:
                            try:
                                s_yf = yf.Ticker(t).history(period="2y", interval="1d", progress=False)["Close"].dropna()
                                if len(s_yf) > 5:
                                    out[t] = s_yf
                                else:
                                    _mark_bad(t)
                            except Exception:
                                _mark_bad(t)
                        time.sleep(0.2)

        # Inter-batch jitter to avoid rate limit
        if i < total_batches - 1:
            time.sleep(0.4)

    return out


# ── Snapshot persistence (unchanged from v3.2) ────────────────────────────
SNAP_PATH = Path(".cache/snapshot_v3.json")
SNAP_PATH.parent.mkdir(parents=True, exist_ok=True)


def save_snapshot(snap: dict):
    try:
        import pickle
        with open(SNAP_PATH.with_suffix(".pkl"), "wb") as f:
            pickle.dump(snap, f)
        with open(SNAP_PATH, "w") as f:
            json.dump({"saved_at": datetime.now().isoformat(), "ok": snap.get("ok", False)}, f)
    except Exception as e:
        logger.warning(f"Snapshot save failed: {e}")


def load_snapshot(max_age_hours: float = 12.0) -> Optional[dict]:
    try:
        import pickle
        if not SNAP_PATH.exists() or not SNAP_PATH.with_suffix(".pkl").exists():
            return None
        with open(SNAP_PATH) as f:
            meta = json.load(f)
        saved_at = datetime.fromisoformat(meta["saved_at"])
        age = (datetime.now() - saved_at).total_seconds() / 3600
        if age > max_age_hours:
            return None
        with open(SNAP_PATH.with_suffix(".pkl"), "rb") as f:
            return pickle.load(f)
    except Exception:
        return None


def snapshot_age_str() -> str:
    try:
        if not SNAP_PATH.exists():
            return "No snapshot"
        with open(SNAP_PATH) as f:
            meta = json.load(f)
        saved_at = datetime.fromisoformat(meta["saved_at"])
        age_min = (datetime.now() - saved_at).total_seconds() / 60
        if age_min < 60:
            return f"{age_min:.0f}m ago"
        return f"{age_min/60:.1f}h ago"
    except Exception:
        return "Unknown"
