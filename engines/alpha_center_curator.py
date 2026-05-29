"""engines/alpha_center_curator.py — Alpha Center v2.0

REDESIGN 2026-05-29:
- OLD: short-term swing setup (R:R 2:1, entry/stop/target)
- NEW: asymmetric opportunity detector (100-1000% upside potential)
- Layers: Bottleneck stage + Market cap + Revenue growth + TAM/Moat + Keith fractal
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# ── Bottleneck Chain Reaction Map (stage 1-2 = highest asymmetry) ──
BOTTLENECK_TICKERS = {
    # Stage 5 (AI infra — mature but still growing)
    "NXT": {"layer": "CPO/Connectors", "stage": 5, "tam_b": 80, "moat": "duopoly"},
    "AMPH": {"layer": "CPO/Connectors", "stage": 5, "tam_b": 60, "moat": "niche"},
    "HLIT": {"layer": "CPO/Connectors", "stage": 5, "tam_b": 45, "moat": "niche"},
    "COHR": {"layer": "Optics", "stage": 4, "tam_b": 50, "moat": "oligopoly"},
    "LITE": {"layer": "Optics", "stage": 4, "tam_b": 40, "moat": "oligopoly"},
    "MRVL": {"layer": "Optics", "stage": 4, "tam_b": 120, "moat": "wide"},
    # Stage 3 (Power/Cooling — mid growth, high demand)
    "VST": {"layer": "Power/Cooling", "stage": 3, "tam_b": 200, "moat": "regulatory"},
    "CEG": {"layer": "Power/Cooling", "stage": 3, "tam_b": 150, "moat": "regulatory"},
    "BE": {"layer": "Power/Cooling", "stage": 3, "tam_b": 30, "moat": "niche"},
    "SMR": {"layer": "Nuclear/SMR", "stage": 3, "tam_b": 100, "moat": "regulatory"},
    "OKLO": {"layer": "Nuclear/SMR", "stage": 3, "tam_b": 50, "moat": "regulatory"},
    # Stage 2 (Tankers — early reflation, supply inelastic)
    "FRO": {"layer": "Tankers", "stage": 2, "tam_b": 25, "moat": "fleet"},
    "TK": {"layer": "Tankers", "stage": 2, "tam_b": 15, "moat": "fleet"},
    "INSW": {"layer": "Tankers", "stage": 2, "tam_b": 20, "moat": "fleet"},
    "STNG": {"layer": "Tankers", "stage": 2, "tam_b": 18, "moat": "fleet"},
    # Stage 4 (Fertilizer — commodity downstream)
    "NTR": {"layer": "Fertilizer", "stage": 4, "tam_b": 40, "moat": "scale"},
    "MOS": {"layer": "Fertilizer", "stage": 4, "tam_b": 30, "moat": "scale"},
    "CF": {"layer": "Fertilizer", "stage": 4, "tam_b": 25, "moat": "scale"},
    # Stage 1 (Rare earth / critical minerals — highest asymmetry)
    "MP": {"layer": "Rare Earth", "stage": 1, "tam_b": 10, "moat": "geographic"},
    "LYSDY": {"layer": "Rare Earth", "stage": 1, "tam_b": 8, "moat": "geographic"},
    "UROY": {"layer": "Uranium", "stage": 1, "tam_b": 12, "moat": "geographic"},
    "CCJ": {"layer": "Uranium", "stage": 1, "tam_b": 80, "moat": "scale"},
    # Crypto infra (high beta, early)
    "MSTR": {"layer": "BTC Proxy", "stage": 2, "tam_b": 60, "moat": "brand"},
    "COIN": {"layer": "Exchange", "stage": 3, "tam_b": 100, "moat": "network"},
    "HOOD": {"layer": "Retail/Trading", "stage": 3, "tam_b": 40, "moat": "userbase"},
    # Indonesia (IHSG — commodity exporters + banking)
    "ADRO.JK": {"layer": "Coal", "stage": 2, "tam_b": 15, "moat": "resource"},
    "ITMG.JK": {"layer": "Coal", "stage": 2, "tam_b": 10, "moat": "resource"},
    "NCKL.JK": {"layer": "Nickel", "stage": 1, "tam_b": 8, "moat": "resource"},
    "ANTM.JK": {"layer": "Gold", "stage": 2, "tam_b": 12, "moat": "resource"},
    "BRMS.JK": {"layer": "Gold", "stage": 1, "tam_b": 3, "moat": "resource"},
    "BBRI.JK": {"layer": "Banking", "stage": 3, "tam_b": 50, "moat": "branch"},
    "BMRI.JK": {"layer": "Banking", "stage": 3, "tam_b": 60, "moat": "branch"},
}

@dataclass
class AsymmetryPick:
    ticker: str
    layer: str
    stage: int
    mcap_b: Optional[float]
    revenue_growth: Optional[float]
    tam_b: int
    moat: str
    keith_signal: str
    composite_signal: str
    asymmetry_score: float
    upside_potential: str  # "MOON" (>1000%), "HIGH" (300-1000%), "MEDIUM" (100-300%)
    conviction: str  # "A" / "B" / "C"
    entry_zone: Optional[str] = None
    catalyst: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class AlphaCenterCurator:
    def __init__(self, keith_signals: Dict[str, Dict] = None,
                 composite_signals: Dict[str, Dict] = None,
                 prices: Dict[str, float] = None,
                 current_quad: str = "Q2") -> None:
        self.keith = keith_signals or {}
        self.composite = composite_signals or {}
        self.prices = prices or {}
        self.quad = current_quad
        self.yf_cache: Dict[str, Dict] = {}

    def _fetch_yf_info(self, ticker: str) -> Dict:
        """Fetch yfinance info dengan cache."""
        if ticker in self.yf_cache:
            return self.yf_cache[ticker]
        try:
            import yfinance as yf
            tk = yf.Ticker(ticker)
            info = tk.info
            result = {
                "mcap": info.get("marketCap"),
                "revenue_growth": info.get("revenueGrowth"),
                "ebitda_margins": info.get("ebitdaMargins"),
                "debt_to_equity": info.get("debtToEquity"),
                "short_ratio": info.get("shortRatio"),
                "float_shares": info.get("floatShares"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
            }
            self.yf_cache[ticker] = result
            return result
        except Exception as e:
            logger.debug("yf info failed for %s: %s", ticker, e)
            self.yf_cache[ticker] = {}
            return {}

    def _stage_multiplier(self, stage: int) -> float:
        """Stage 1 = highest asymmetry, Stage 5 = lowest."""
        return {1: 2.0, 2: 1.7, 3: 1.3, 4: 1.0, 5: 0.7}.get(stage, 1.0)

    def _mcap_upside(self, mcap_b: Optional[float]) -> str:
        if mcap_b is None: return "UNKNOWN"
        if mcap_b < 2: return "MOON"
        if mcap_b < 10: return "HIGH"
        if mcap_b < 50: return "MEDIUM"
        return "LOW"

    def _score(self, pick: AsymmetryPick) -> float:
        base = 30
        # Stage multiplier (1-5)
        base += self._stage_multiplier(pick.stage) * 20
        # Market cap (smaller = higher score)
        if pick.mcap_b is not None:
            if pick.mcap_b < 2: base += 30
            elif pick.mcap_b < 10: base += 20
            elif pick.mcap_b < 50: base += 10
        # Revenue growth
        if pick.revenue_growth is not None:
            if pick.revenue_growth > 1.0: base += 25  # >100%
            elif pick.revenue_growth > 0.5: base += 15
            elif pick.revenue_growth > 0.3: base += 10
        # Keith alignment
        if pick.keith_signal == "BULLISH": base *= 1.5
        elif pick.keith_signal == "BEARISH": base *= 0.3
        # Composite alignment
        if pick.composite_signal == "LONG": base *= 1.2
        elif pick.composite_signal == "SHORT": base *= 0.5
        return round(base, 1)

    def _conviction(self, score: float) -> str:
        if score >= 90: return "A"
        if score >= 70: return "B"
        if score >= 50: return "C"
        return "D"

    def _catalyst_text(self, ticker: str, layer: str, stage: int) -> str:
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

    def curate(self, max_picks: int = 15) -> Dict[str, Any]:
        """Main entry: return high-asymmetry picks + meta."""
        picks: List[AsymmetryPick] = []
        for ticker, meta in BOTTLENECK_TICKERS.items():
            # Skip if Keith BEARISH
            ks = self.keith.get(ticker, {})
            keith_trade = ks.get("keith_trade", "NEUTRAL")
            if keith_trade == "BEARISH":
                logger.debug("Alpha skip %s: Keith BEARISH", ticker)
                continue

            # yfinance fundamentals
            yf_info = self._fetch_yf_info(ticker)
            mcap_b = round(yf_info.get("mcap", 0) / 1e9, 1) if yf_info.get("mcap") else None
            rev_growth = yf_info.get("revenue_growth")

            # Composite signal
            cs = self.composite.get(ticker, {})
            composite_trade = cs.get("trade", "NEUTRAL")

            pick = AsymmetryPick(
                ticker=ticker,
                layer=meta["layer"],
                stage=meta["stage"],
                mcap_b=mcap_b,
                revenue_growth=round(rev_growth, 2) if rev_growth else None,
                tam_b=meta["tam_b"],
                moat=meta["moat"],
                keith_signal=keith_trade,
                composite_signal=composite_trade,
                asymmetry_score=0.0,  # placeholder, filled below
                upside_potential=self._mcap_upside(mcap_b),
                conviction="C",
                catalyst=self._catalyst_text(ticker, meta["layer"], meta["stage"]),
            )
            pick.asymmetry_score = self._score(pick)
            pick.conviction = self._conviction(pick.asymmetry_score)

            # Only A/B/C pass
            if pick.conviction in ("A", "B", "C"):
                picks.append(pick)

        picks.sort(key=lambda x: x.asymmetry_score, reverse=True)
        top = picks[:max_picks]

        return {
            "passed": [p.to_dict() for p in top],
            "rejected_count": len(BOTTLENECK_TICKERS) - len(picks),
            "meta": {
                "version": "v2.0_asymmetry",
                "quad": self.quad,
                "total_candidates": len(BOTTLENECK_TICKERS),
                "passed_count": len(top),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        }

    def curate_short_term(self, wf_results: Dict, max_picks: int = 10) -> Dict[str, Any]:
        """Legacy short-term swing (kept for backward compatibility)."""
        picks = []
        for ticker, wf in (wf_results or {}).items():
            if not isinstance(wf, dict): continue
            ks = self.keith.get(ticker, {})
            if ks.get("keith_trade") == "BEARISH": continue
            composite = self.composite.get(ticker, {})
            if composite.get("trade") not in ("LONG", "BULLISH"): continue
            price = self.prices.get(ticker)
            if price is None: continue
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
                        "keith": ks.get("keith_trade", "NEUTRAL"),
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
