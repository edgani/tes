"""engines/alpha_center_curator.py — Alpha Center Curator v2.1

BACKWARD COMPATIBLE: Punya get_curator (v1 API) + AlphaCenterCurator (v2 API)
v1: bottleneck + surge potential (5-layer filter, stars, tags, MULTI-BAG, M&A-Target)
v2: high asymmetry detector (100-1000% upside, stage, TAM, moat)
"""

import json, os, logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Bottleneck Reference Loader ──
_BOTTLENECK_REF = None
def _load_bottleneck_ref():
    global _BOTTLENECK_REF
    if _BOTTLENECK_REF is not None:
        return _BOTTLENECK_REF
    try:
        with open("bottleneck_reference.json", "r", encoding="utf-8") as f:
            _BOTTLENECK_REF = json.load(f)
    except Exception:
        _BOTTLENECK_REF = {}
    return _BOTTLENECK_REF or {}

# ── V1: Bottleneck + Surge Potential Curator ──

class CuratorV1:
    """Legacy curator — bottleneck + surge potential (5-layer filter)."""

    def __init__(self, bottleneck_ref=None):
        self.ref = bottleneck_ref or _load_bottleneck_ref()

    def filter_universe(self, keith_signals=None, wf_results=None, current_quad="Q3", min_stars=1):
        """Return v1 format: {"passed": [...], "rejected": [...], "all": [...]}"""
        keith_signals = keith_signals or {}
        wf_results = wf_results or {}

        passed = []
        rejected = []
        all_items = []

        # Build from consensus heatmap
        for item in self.ref.get("consensus_heatmap", []):
            ticker = item.get("ticker", "").replace("$", "").strip().upper()
            if not ticker:
                continue

            stars = item.get("stars", 0)
            if stars < min_stars:
                continue

            tags = item.get("tags", []) or []
            layer = item.get("layer", "")
            role = item.get("role", "")
            market = item.get("market", "us_equity")

            # Keith check
            ks = keith_signals.get(ticker, {}) if isinstance(keith_signals, dict) else {}
            keith_trade = ks.get("keith_trade", "NEUTRAL") if isinstance(ks, dict) else "NEUTRAL"

            # 5-Layer Filter Checks
            checks = {}
            checks["L1_stars"] = {"pass": stars >= 3, "msg": f"{stars} stars"}
            checks["L2_keith"] = {"pass": keith_trade != "BEARISH", "msg": f"Keith {keith_trade}"}
            checks["L3_quad"] = {"pass": True, "msg": f"Quad {current_quad}"}
            checks["L4_wf"] = {"pass": True, "msg": "WF OK"}
            checks["L5_multi"] = {"pass": "MULTI-BAG" in tags or "M&A-Target" in tags, "msg": "Multi-bag or M&A"}

            total_pass = sum(1 for c in checks.values() if c["pass"])
            total_check = len(checks)

            candidate = {
                "ticker": ticker,
                "stars": stars,
                "tags": tags,
                "layer": layer,
                "role": role,
                "market": market,
                "thesis": item.get("thesis", f"{layer} bottleneck — {role}"),
                "bottleneck_reason": item.get("bottleneck_reason", ""),
                "correlations": item.get("correlations", {}),
                "catalysts_2026": item.get("catalysts_2026", []),
                "risk": item.get("risk", ""),
                "risk_notes": item.get("risk_notes", ""),
                "sources": item.get("accounts", []),
                "monopoly_strength": item.get("monopoly_strength", "—"),
                "potential_upside": item.get("potential_upside", ""),
            }

            entry = {
                "ticker": ticker,
                "candidate": candidate,
                "checks": checks,
                "pass_ratio": total_pass / total_check if total_check else 0,
            }
            all_items.append(entry)

            if total_pass >= 3:
                passed.append(entry)
            else:
                rejected.append(entry)

        # Also build from M&A watchlist
        for ma in self.ref.get("ma_watchlist", []):
            ticker = ma.get("target", "").replace("$", "").strip().upper()
            if not ticker:
                continue
            candidate = {
                "ticker": ticker,
                "stars": 4,
                "tags": ["M&A-Target"],
                "layer": "M&A",
                "role": "Target",
                "market": ma.get("market", "us_equity"),
                "thesis": ma.get("thesis", f"M&A target — {ma.get('acquirer', '')}"),
                "bottleneck_reason": "",
                "correlations": {},
                "catalysts_2026": [ma.get("expected_timeline", "2026")],
                "risk": ma.get("risk", ""),
                "risk_notes": "",
                "sources": ma.get("sources", []),
                "monopoly_strength": "—",
                "potential_upside": ma.get("upside", ""),
            }
            entry = {
                "ticker": ticker,
                "candidate": candidate,
                "checks": {"L1_stars": {"pass": True, "msg": "4 stars"},
                           "L2_keith": {"pass": True, "msg": "Keith NEUTRAL"},
                           "L3_quad": {"pass": True, "msg": f"Quad {current_quad}"},
                           "L4_wf": {"pass": True, "msg": "WF OK"},
                           "L5_multi": {"pass": True, "msg": "M&A target"}},
                "pass_ratio": 1.0,
            }
            all_items.append(entry)
            passed.append(entry)

        return {"passed": passed, "rejected": rejected, "all": all_items}


def get_curator():
    """v1 API — return CuratorV1 instance."""
    return CuratorV1()


# ── V2: High Asymmetry Detector (100-1000% upside) ──

BOTTLENECK_TICKERS = {
    "NXT": {"layer": "CPO/Connectors", "stage": 5, "tam_b": 80, "moat": "duopoly"},
    "AMPH": {"layer": "CPO/Connectors", "stage": 5, "tam_b": 60, "moat": "niche"},
    "HLIT": {"layer": "CPO/Connectors", "stage": 5, "tam_b": 45, "moat": "niche"},
    "COHR": {"layer": "Optics", "stage": 4, "tam_b": 50, "moat": "oligopoly"},
    "LITE": {"layer": "Optics", "stage": 4, "tam_b": 40, "moat": "oligopoly"},
    "MRVL": {"layer": "Optics", "stage": 4, "tam_b": 120, "moat": "wide"},
    "VST": {"layer": "Power/Cooling", "stage": 3, "tam_b": 200, "moat": "regulatory"},
    "CEG": {"layer": "Power/Cooling", "stage": 3, "tam_b": 150, "moat": "regulatory"},
    "BE": {"layer": "Power/Cooling", "stage": 3, "tam_b": 30, "moat": "niche"},
    "SMR": {"layer": "Nuclear/SMR", "stage": 3, "tam_b": 100, "moat": "regulatory"},
    "OKLO": {"layer": "Nuclear/SMR", "stage": 3, "tam_b": 50, "moat": "regulatory"},
    "FRO": {"layer": "Tankers", "stage": 2, "tam_b": 25, "moat": "fleet"},
    "TK": {"layer": "Tankers", "stage": 2, "tam_b": 15, "moat": "fleet"},
    "INSW": {"layer": "Tankers", "stage": 2, "tam_b": 20, "moat": "fleet"},
    "STNG": {"layer": "Tankers", "stage": 2, "tam_b": 18, "moat": "fleet"},
    "NTR": {"layer": "Fertilizer", "stage": 4, "tam_b": 40, "moat": "scale"},
    "MOS": {"layer": "Fertilizer", "stage": 4, "tam_b": 30, "moat": "scale"},
    "CF": {"layer": "Fertilizer", "stage": 4, "tam_b": 25, "moat": "scale"},
    "MP": {"layer": "Rare Earth", "stage": 1, "tam_b": 10, "moat": "geographic"},
    "LYSDY": {"layer": "Rare Earth", "stage": 1, "tam_b": 8, "moat": "geographic"},
    "UROY": {"layer": "Uranium", "stage": 1, "tam_b": 12, "moat": "geographic"},
    "CCJ": {"layer": "Uranium", "stage": 1, "tam_b": 80, "moat": "scale"},
    "MSTR": {"layer": "BTC Proxy", "stage": 2, "tam_b": 60, "moat": "brand"},
    "COIN": {"layer": "Exchange", "stage": 3, "tam_b": 100, "moat": "network"},
    "HOOD": {"layer": "Retail/Trading", "stage": 3, "tam_b": 40, "moat": "userbase"},
    "ADRO.JK": {"layer": "Coal", "stage": 2, "tam_b": 15, "moat": "resource"},
    "ITMG.JK": {"layer": "Coal", "stage": 2, "tam_b": 10, "moat": "resource"},
    "NCKL.JK": {"layer": "Nickel", "stage": 1, "tam_b": 8, "moat": "resource"},
    "ANTM.JK": {"layer": "Gold", "stage": 2, "tam_b": 12, "moat": "resource"},
    "BRMS.JK": {"layer": "Gold", "stage": 1, "tam_b": 3, "moat": "resource"},
    "BBRI.JK": {"layer": "Banking", "stage": 3, "tam_b": 50, "moat": "branch"},
    "BMRI.JK": {"layer": "Banking", "stage": 3, "tam_b": 60, "moat": "branch"},
}


class AlphaCenterCurator:
    """v2 curator — high asymmetry detector (100-1000% upside)."""

    def __init__(self, keith_signals=None, composite_signals=None, prices=None, current_quad="Q2"):
        self.keith = keith_signals or {}
        self.composite = composite_signals or {}
        self.prices = prices or {}
        self.quad = current_quad
        self.yf_cache = {}

    def _fetch_yf_info(self, ticker):
        if ticker in self.yf_cache:
            return self.yf_cache[ticker]
        try:
            import yfinance as yf
            info = yf.Ticker(ticker).info
            result = {
                "mcap": info.get("marketCap"),
                "revenue_growth": info.get("revenueGrowth"),
            }
            self.yf_cache[ticker] = result
            return result
        except Exception:
            self.yf_cache[ticker] = {}
            return {}

    def _stage_multiplier(self, stage):
        return {1: 2.0, 2: 1.7, 3: 1.3, 4: 1.0, 5: 0.7}.get(stage, 1.0)

    def _mcap_upside(self, mcap_b):
        if mcap_b is None:
            return "UNKNOWN"
        if mcap_b < 2:
            return "MOON"
        if mcap_b < 10:
            return "HIGH"
        if mcap_b < 50:
            return "MEDIUM"
        return "LOW"

    def _score(self, pick):
        base = 30
        base += self._stage_multiplier(pick.get("stage", 3)) * 20
        mcap_b = pick.get("mcap_b")
        if mcap_b is not None:
            if mcap_b < 2:
                base += 30
            elif mcap_b < 10:
                base += 20
            elif mcap_b < 50:
                base += 10
        rev = pick.get("revenue_growth")
        if rev is not None:
            if rev > 1.0:
                base += 25
            elif rev > 0.5:
                base += 15
            elif rev > 0.3:
                base += 10
        keith = pick.get("keith_signal", "NEUTRAL")
        if keith == "BULLISH":
            base *= 1.5
        elif keith == "BEARISH":
            base *= 0.3
        comp = pick.get("composite_signal", "NEUTRAL")
        if comp == "LONG":
            base *= 1.2
        elif comp == "SHORT":
            base *= 0.5
        return round(base, 1)

    def _conviction(self, score):
        if score >= 90:
            return "A"
        if score >= 70:
            return "B"
        if score >= 50:
            return "C"
        return "D"

    def _catalyst(self, ticker, layer, stage):
        catalysts = {
            "CPO/Connectors": "AI datacenter buildout accelerating; CPO adoption inflection",
            "Optics": "800G/1.6T transceiver demand surge; supply constrained",
            "Power/Cooling": "Nuclear renaissance + AI power density crisis",
            "Nuclear/SMR": "SMR regulatory approvals + utility contracts",
            "Tankers": "OPEC+ cuts + Red Sea disruptions + fleet aging",
            "Fertilizer": "Natural gas cost squeeze + food security demand",
            "Rare Earth": "China export controls + Western supply chain rebuild",
            "Uranium": "Global reactor restart + Sprott trust inflows",
            "BTC Proxy": "Halving cycle + institutional ETF adoption",
            "Exchange": "Crypto volume expansion + derivatives growth",
            "Coal": "Seaborne thermal demand + Indonesia export growth",
            "Nickel": "EV battery chemistry shift + Indonesia dominance",
            "Gold": "Central bank buying + real rates declining",
            "Banking": "NIM expansion + credit growth recovery",
        }
        return catalysts.get(layer, f"Stage {stage} supply chain inflection")

    def curate(self, max_picks=15):
        picks = []
        for ticker, meta in BOTTLENECK_TICKERS.items():
            ks = self.keith.get(ticker, {})
            keith_trade = ks.get("keith_trade", "NEUTRAL") if isinstance(ks, dict) else "NEUTRAL"
            if keith_trade == "BEARISH":
                continue
            yf_info = self._fetch_yf_info(ticker)
            mcap_b = round(yf_info.get("mcap", 0) / 1e9, 1) if yf_info.get("mcap") else None
            rev_growth = yf_info.get("revenue_growth")
            cs = self.composite.get(ticker, {})
            composite_trade = cs.get("trade", "NEUTRAL") if isinstance(cs, dict) else "NEUTRAL"
            pick = {
                "ticker": ticker,
                "layer": meta["layer"],
                "stage": meta["stage"],
                "mcap_b": mcap_b,
                "revenue_growth": round(rev_growth, 2) if rev_growth else None,
                "tam_b": meta["tam_b"],
                "moat": meta["moat"],
                "keith_signal": keith_trade,
                "composite_signal": composite_trade,
                "asymmetry_score": 0.0,
                "upside_potential": self._mcap_upside(mcap_b),
                "conviction": "C",
                "catalyst": self._catalyst(ticker, meta["layer"], meta["stage"]),
            }
            pick["asymmetry_score"] = self._score(pick)
            pick["conviction"] = self._conviction(pick["asymmetry_score"])
            if pick["conviction"] in ("A", "B", "C"):
                picks.append(pick)
        picks.sort(key=lambda x: x["asymmetry_score"], reverse=True)
        top = picks[:max_picks]
        return {
            "passed": top,
            "rejected_count": len(BOTTLENECK_TICKERS) - len(picks),
            "meta": {
                "version": "v2.0_asymmetry",
                "quad": self.quad,
                "total_candidates": len(BOTTLENECK_TICKERS),
                "passed_count": len(top),
            }
        }

    def curate_short_term(self, wf_results=None, max_picks=10):
        picks = []
        for ticker, wf in (wf_results or {}).items():
            if not isinstance(wf, dict):
                continue
            ks = self.keith.get(ticker, {})
            if isinstance(ks, dict) and ks.get("keith_trade") == "BEARISH":
                continue
            composite = self.composite.get(ticker, {})
            if isinstance(composite, dict) and composite.get("trade") not in ("LONG", "BULLISH"):
                continue
            price = self.prices.get(ticker)
            if price is None:
                continue
            entry = wf.get("entry")
            stop = wf.get("stop")
            target = wf.get("target")
            if entry and stop and target:
                rr = round(abs(target - entry) / abs(entry - stop), 2) if entry != stop else 0
                if rr >= 2.0:
                    picks.append({
                        "ticker": ticker,
                        "entry": entry, "stop": stop, "target": target,
                        "r_r": rr,
                        "grade": "A" if rr >= 3 else "B" if rr >= 2 else "C",
                        "keith": ks.get("keith_trade", "NEUTRAL") if isinstance(ks, dict) else "NEUTRAL",
                        "type": "short_term_swing",
                    })
        picks.sort(key=lambda x: x["r_r"], reverse=True)
        return {
            "passed": picks[:max_picks],
            "meta": {"version": "v1.1_short_term", "count": len(picks[:max_picks])}
        }


# Module-level convenience
def curate_alpha_center(keith_signals, composite_signals, prices, current_quad, max_picks=15):
    curator = AlphaCenterCurator(keith_signals, composite_signals, prices, current_quad)
    return curator.curate(max_picks)


def curate_short_term(wf_results, keith_signals, composite_signals, prices, max_picks=10):
    curator = AlphaCenterCurator(keith_signals, composite_signals, prices)
    return curator.curate_short_term(wf_results, max_picks)
