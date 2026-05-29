"""orchestrator_v40_patch.py — COPY-PASTE ke orchestrator.py

INSTRUCTIONS:
1. Buka orchestrator.py
2. Cari baris: `def _v40_fetch_external_data(self, snap, prices, current_quad, cb=None):`
3. Hapus SELURUH isi fungsi itu sampai `return out` (atau sampai fungsi berikutnya)
4. Paste fungsi di bawah ini (termasuk `def _v40_fetch_external_data` dan `_apply_keith_filter_to_snapshot`)
5. Di `build_snapshot`, setelah `keith_sync` selesai, tambah:
       snap = self._apply_keith_filter_to_snapshot(snap, keith_sync, current_quad)
6. Di `build_snapshot`, untuk alpha_center, ganti jadi:
       from engines.alpha_center_curator import curate_alpha_center, curate_short_term
       ac_high = curate_alpha_center(keith_sync, composite, prices, current_quad, max_picks=15)
       ac_short = curate_short_term(wf_results, keith_sync, composite, prices, max_picks=10)
       snap["alpha_center"] = {"high_asymmetry": ac_high, "short_term": ac_short}
"""

# PASTE INI KE orchestrator.py —————————————————————————————————————————————

def _v40_fetch_external_data(self, snap, prices, current_quad, cb=None):
    """Fetch options/COT/OI/on-chain. v40.5 PATCHED — CME 403 fallback + crypto ETF proxy."""
    def _cb(m, p):
        try:
            if cb: cb(m, p)
        except Exception: pass

    out = {"options_data": {}, "cot_data": {}, "cme_oi": {}, "onchain_data": {}}
    price_tickers = list(prices.keys()) if prices else []

    us_tickers = [t for t in price_tickers if not any(s in t.upper() for s in [".JK", "=X", "=F", "-USD", "^"])]
    crypto_tickers = [t for t in price_tickers if "-USD" in t.upper() and not t.startswith("DX")]
    fx_comm_tickers = [t for t in price_tickers if "=X" in t.upper() or "=F" in t.upper()
                       or t in ("DX-Y.NYB", "UUP", "USO", "GLD", "SLV", "UNG", "CPER", "CORN", "WEAT")]

    # ── OPTIONS via yfinance ───────────────────────────────────────────
    _cb("v40: Fetching options (yfinance)…", 95)
    try:
        from engines.live_data_engine import fetch_options_yf
        _commodity_etfs = ["USO", "GLD", "SLV", "UNG", "CPER", "UGA", "CORN", "WEAT", "SOYB"]
        _fx_etfs = ["UUP", "FXE", "FXY", "FXB", "FXA", "FXC"]
        opt_targets = (us_tickers[:25]
                     + [t for t in ("SPY", "QQQ", "IBIT", "TLT", "IWM") if t in price_tickers]
                     + _commodity_etfs + _fx_etfs)
        opt_targets = list(dict.fromkeys(opt_targets))
        out["options_data"] = fetch_options_yf(opt_targets, max_tickers=45)
    except Exception as e:
        logger.warning(f"v40: yfinance options failed: {e}")

    # Crypto options via ETF proxy
    try:
        from engines.live_data_engine import fetch_options_yf
        crypto_etf_map = {"BTC-USD": "IBIT", "ETH-USD": "ETHA"}
        for crypto_t, etf in crypto_etf_map.items():
            if crypto_t in price_tickers:
                etf_opts = fetch_options_yf([etf], max_tickers=1)
                if etf_opts.get(etf):
                    out["options_data"][crypto_t] = {**etf_opts[etf], "proxy_etf": etf}
    except Exception as e:
        logger.debug(f"crypto options proxy: {e}")

    # ── ON-CHAIN via DeFiLlama ─────────────────────────────────────────
    _cb("v40: Fetching on-chain (DeFiLlama)…", 97)
    try:
        from engines.live_data_engine import fetch_onchain_defillama
        chain_map = {}
        name_map = {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana",
                    "AVAX-USD": "Avalanche", "MATIC-USD": "Polygon", "ARB-USD": "Arbitrum",
                    "OP-USD": "OP Mainnet", "BNB-USD": "BSC"}
        for t in crypto_tickers:
            if t in name_map:
                chain_map[t] = name_map[t]
        if chain_map:
            out["onchain_data"] = fetch_onchain_defillama(chain_map)
    except Exception as e:
        logger.warning(f"v40: DeFiLlama failed: {e}")

    # ── COT keyed by ticker ────────────────────────────────────────────
    _cb("v40: Fetching COT (CFTC)…", 98)
    try:
        from engines.live_data_engine import fetch_cot_by_ticker
        out["cot_data"] = fetch_cot_by_ticker(fx_comm_tickers)
    except Exception as e:
        logger.warning(f"v40: COT failed: {e}")

    # ── CME OI (PATCHED v40.5 — auto-fallback ke yfinance) ───────────
    try:
        from engines.cme_scraper import get_cme_volume
        cme_map = {"CL=F": "4250", "GC=F": "133", "SI=F": "84", "NG=F": "4240", "HG=F": "424"}
        cme_success = 0
        cme_fallback = 0
        for tkr, prod in cme_map.items():
            if tkr in price_tickers:
                try:
                    vol = get_cme_volume(prod)
                    if vol:
                        out["cme_oi"][tkr] = vol
                        src = vol.get("source", "")
                        if "yfinance" in src:
                            cme_fallback += 1
                        else:
                            cme_success += 1
                except Exception as e:
                    logger.debug(f"v40: CME OI skip {tkr}: {e}")
                    continue
        if cme_fallback > 0 and cme_success == 0:
            logger.info(f"v40: CME blocked (403) — all {cme_fallback} commodities fallback to yfinance")
        elif cme_success > 0:
            logger.info(f"v40: CME OK — {cme_success} direct, {cme_fallback} fallback")
    except Exception as e:
        logger.debug(f"v40: CME OI module error: {e}")

    logger.info(f"v40: external data — options:{len(out['options_data'])} "
                f"cot:{len(out['cot_data'])} cme:{len(out['cme_oi'])} onchain:{len(out['onchain_data'])}")
    return out


def _apply_keith_filter_to_snapshot(self, snap, keith_sync, current_quad):
    """Apply Keith fractal filter ke semua market tabs."""
    try:
        from engines.keith_market_filter import apply_keith_market_filter, keith_breadth_summary

        # Apply ke masing2 market tab
        for tab_key in ["us_stocks", "forex", "commodities", "crypto", "ihsg"]:
            tab_data = snap.get(tab_key, {})
            if not isinstance(tab_data, dict):
                continue
            tickers = list(tab_data.keys())
            if not tickers:
                continue
            filtered = apply_keith_market_filter(tickers, keith_sync, current_quad)
            snap[f"{tab_key}_keith_filtered"] = filtered["passed"]
            snap[f"{tab_key}_keith_avoided"] = filtered["avoided"]
            snap[f"{tab_key}_keith_meta"] = filtered["meta"]

        # Breadth summary (37 signals style)
        snap["keith_breadth"] = keith_breadth_summary(keith_sync)
        logger.info("Keith filter applied to all market tabs | breadth=%s",
                    snap["keith_breadth"].get("breadth_signal", "N/A"))
    except Exception as e:
        logger.warning(f"Keith filter application failed: {e}")
    return snap

# END PASTE ———————————————————————————————————————————————————————————————
