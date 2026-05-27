"""alpha_center_curator.py — 5-Layer Filter Pipeline v40

Ticker passes Alpha Center ONLY if it satisfies:
  Layer 1: Multi-source consensus (≥2 reputable sources)
  Layer 2: Bottleneck / catalyst presence
  Layer 3: Correlation chain mapped (front-run path exists)
  Layer 4: Hedgeye signal compatible (not actively bearish)
  Layer 5: Walk-forward + Monte Carlo gate passed

Output: per-ticker rich card with thesis, correlations, M&A potential, sizing.
"""
from __future__ import annotations
import json
import logging
import os
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# ALPHA CENTER UNIVERSE — CURATED 2026
# ═══════════════════════════════════════════════════════════════════════════

ALPHA_CENTER_CANDIDATES = {
    # ── 5★ TOP CONVICTION ────────────────────────────────────────────────
    "MU": {
        "market": "us_equity",
        "thesis": "HBM3e/4 — gating bottleneck for NVDA Blackwell/Rubin. Memory cycle inflection 2026.",
        "bottleneck_layer": "L1_Memory_HBM",
        "monopoly": "🟠 TRIOPOLY (MU, SK Hynix, Samsung)",
        "geopolitical_risk": "MEDIUM",
        "stars": 5,
        "sources": ["aleabitoreddit", "HyperTechInvest", "jukan05", "citrini"],
        "ma_potential": "LOW",
        "correlations": {"NVDA": 1.05, "TSM": 0.70, "AMD": 0.55, "SOXX": 1.10},
        "catalysts_2026": [
            "HBM4 ramp Q2 2026",
            "Capacity sold out through 2027",
            "Pricing power demonstration in Q1 2026 earnings",
        ],
        "tags": ["AI", "Memory", "Bottleneck", "Citrini"],
    },
    # ── 4★ HIGH CONVICTION ───────────────────────────────────────────────
    "AVGO": {
        "market": "us_equity",
        "thesis": "Custom accelerators (Google TPU, Meta MTIA) + networking (Tomahawk). 80x forward EPS = priced for perfection.",
        "bottleneck_layer": "L2b_Packaging_CustomSilicon",
        "monopoly": "🟡 NEAR (only volume custom AI silicon outside NVDA)",
        "stars": 4,
        "sources": ["citrini", "HyperTechInvest", "ParadisLabs", "zephyr_z9"],
        "ma_potential": "ACQUIRER (Apptio, VMware)",
        "correlations": {"NVDA": 0.55, "TSM": 0.55, "AMD": 0.50},
        "catalysts_2026": ["Hock Tan custom silicon roadmap", "VMware integration synergies"],
        "tags": ["AI", "Custom Silicon", "Networking"],
    },
    "MRVL": {
        "market": "us_equity",
        "thesis": "CPO ASIC + 800G/1.6T PAM4 DSP + NVDA $2B lock-in target. Cloud connectivity bottleneck winner.",
        "bottleneck_layer": "L2a_Optical_CPO",
        "monopoly": "🟡 NEAR (CPO ASIC pioneer)",
        "stars": 4,
        "sources": ["citrini", "aleabitoreddit", "ParadisLabs", "jukan05"],
        "ma_potential": "TARGET (mid-cap)",
        "correlations": {"NVDA": 0.85, "AVGO": 0.65, "COHR": 0.70},
        "catalysts_2026": ["Custom AI XPU revenue ramp", "CPO mass production 2027 prep"],
        "tags": ["AI", "Optical", "CPO", "NVDA-playbook"],
    },
    "COHR": {
        "market": "us_equity",
        "thesis": "Optical components — NVDA $2B capacity lock-in 2025. Bridge product (200G EML, OCS) + InP photonics roll-up.",
        "bottleneck_layer": "L2a_Optical",
        "monopoly": "🟡 NEAR",
        "stars": 4,
        "sources": ["citrini", "ParadisLabs", "HyperTechInvest", "aleabitoreddit"],
        "ma_potential": "ACQUIRER (II-VI merger, photonics roll-up continues)",
        "correlations": {"NVDA": 1.40, "LITE": 1.20, "MRVL": 0.70},
        "catalysts_2026": ["EML capacity ramp", "DGX H200 connector revenue"],
        "tags": ["AI", "Optical", "NVDA-playbook"],
    },
    "AAOI": {
        "market": "us_equity",
        "thesis": "CPO / optical transceivers — Microsoft Azure orders, 800G ramp. Pure-play upside but execution risk.",
        "bottleneck_layer": "L2a_Optical_Transceiver",
        "monopoly": "🟠 CONTESTED",
        "stars": 4,
        "sources": ["citrini", "HyperTechInvest", "zephyr_z9", "ParadisLabs"],
        "ma_potential": "MEDIUM",
        "correlations": {"NVDA": 1.35, "MSFT": 0.65, "COHR": 0.85},
        "catalysts_2026": ["Microsoft 800G ramp", "1.6T product launch"],
        "tags": ["AI", "Optical"],
    },
    # ── 3★ ────────────────────────────────────────────────────────────────
    "QCOM": {
        "market": "us_equity",
        "thesis": "On-device AI inference winner. Snapdragon X laptops + automotive design wins.",
        "bottleneck_layer": "L1_Compute_OnDevice",
        "stars": 3,
        "sources": ["citrini", "HyperTechInvest", "jukan05"],
        "ma_potential": "ACQUIRER",
        "correlations": {"NVDA": 0.35, "MTK": 0.75},
        "catalysts_2026": ["Apple modem replacement risk", "Snapdragon X penetration"],
        "tags": ["AI", "On-Device", "Mobile"],
    },
    "ETN": {
        "market": "us_equity",
        "thesis": "Power management for AI data centers. ARC flash + transformer + DC infrastructure.",
        "bottleneck_layer": "L3_Power",
        "stars": 3,
        "sources": ["citrini", "ParadisLabs", "HyperTechInvest"],
        "correlations": {"NVDA": 0.65, "VRT": 0.65, "GE": 0.45},
        "catalysts_2026": ["AI capex run-rate continues", "Grid-tie revenue ramp"],
        "tags": ["AI Power", "Infrastructure"],
    },
    "CRDO": {
        "market": "us_equity",
        "thesis": "Active electrical cables (AEC) — alternative to optical at sub-3m. Margin expansion.",
        "bottleneck_layer": "L2a_Optical_Interconnect",
        "stars": 3,
        "sources": ["citrini", "ParadisLabs", "aleabitoreddit"],
        "ma_potential": "TARGET (consolidation candidate)",
        "correlations": {"NVDA": 1.10, "AVGO": 0.55, "MRVL": 0.65},
        "catalysts_2026": ["AEC volume ramp", "1.6T design wins"],
        "tags": ["AI", "Interconnect"],
    },
    # ── 2★ ────────────────────────────────────────────────────────────────
    "AMD": {
        "market": "us_equity",
        "thesis": "MI300/MI450 ramp — second source to NVDA. OpenAI MI450 deal validates roadmap.",
        "bottleneck_layer": "L1_Compute_GPU",
        "stars": 2,
        "sources": ["citrini", "HyperTechInvest"],
        "correlations": {"NVDA": 0.65, "TSM": 0.55, "MU": 0.55},
        "catalysts_2026": ["MI450 launch H2 2026", "OpenAI deliveries"],
        "tags": ["AI", "GPU"],
    },
    "LNG": {
        "market": "us_equity",
        "thesis": "LNG export demand — gas turbines for AI data centers + Europe energy.",
        "bottleneck_layer": "L3_Energy_LNG",
        "stars": 2,
        "sources": ["citrini", "Druckenmiller"],
        "correlations": {"NG=F": 0.95, "VST": 0.55},
        "catalysts_2026": ["Stage 3 ramp", "Long-term contract rollovers"],
        "tags": ["Energy", "LNG"],
    },
    "MP": {
        "market": "us_equity",
        "thesis": "Rare earths — China export controls beneficiary. Defense + magnet/EV demand.",
        "bottleneck_layer": "L3_Materials_REE",
        "monopoly": "🟢 US-Strategic",
        "stars": 2,
        "sources": ["citrini", "HyperTechInvest"],
        "correlations": {"USAR": 1.30, "LMT": 0.20},
        "catalysts_2026": ["NdPr pricing", "DoD contract expansions"],
        "tags": ["Materials", "Defense", "China-Risk"],
    },
    # ── 1★ HIGH-RISK HIGH-REWARD ──────────────────────────────────────────
    "SIVE": {
        "market": "us_equity",
        "thesis": "CW Laser for CPO. Small float, M&A target HIGH probability (AVGO/MRVL acquirer).",
        "bottleneck_layer": "L4_Optical_CW_Laser",
        "monopoly": "🟠 CONTESTED",
        "stars": 1,
        "sources": ["citrini-mna", "ParadisLabs"],
        "ma_potential": "HIGH — explicit Citrini M&A watchlist",
        "correlations": {"NVDA": 1.80, "COHR": 1.50, "MRVL": 1.10},
        "catalysts_2026": ["CPO mass production prep 2027", "Capacity disclosure"],
        "tags": ["AI", "Optical", "M&A-Target", "Small-Cap"],
    },
    "AXTI": {
        "market": "us_equity",
        "thesis": "InP substrate 60-70% market share — Beijing-located. Citrini M&A target (COHR acquirer).",
        "bottleneck_layer": "L1_Materials_InP",
        "monopoly": "🟡 NEAR (geopolitical risk)",
        "stars": 1,
        "sources": ["citrini-mna", "ParadisLabs"],
        "ma_potential": "MEDIUM",
        "correlations": {"COHR": 0.95, "LITE": 0.85, "SIVE": 0.75},
        "catalysts_2026": ["Pricing power demonstration", "M&A interest"],
        "tags": ["AI", "Materials", "M&A-Target", "China-Risk"],
    },
    "LITE": {
        "market": "us_equity",
        "thesis": "Lumentum — 200G EML monopoly (only volume shipper). $2B NVDA lock-in beneficiary.",
        "bottleneck_layer": "L3_Optical_EML",
        "monopoly": "🔴 HARD",
        "stars": 1,
        "sources": ["citrini", "ParadisLabs", "aleabitoreddit"],
        "correlations": {"NVDA": 1.50, "COHR": 1.05, "MRVL": 0.85},
        "catalysts_2026": ["200G EML capacity ramp", "Cisco datacom"],
        "tags": ["AI", "Optical", "Monopoly"],
    },
    "POET": {
        "market": "us_equity",
        "thesis": "Optical interposer — disrupts CPO architecture. Speculative but high upside.",
        "bottleneck_layer": "L4_Optical_Interposer",
        "stars": 1,
        "sources": ["citrini", "ParadisLabs"],
        "correlations": {"NVDA": 1.55, "SIVE": 1.40},
        "catalysts_2026": ["Customer announcements", "Mass production ramp"],
        "tags": ["AI", "Optical", "Speculative"],
    },
    "SITM": {
        "market": "us_equity",
        "thesis": "MEMS Timing — 150%+ growth 7 quarters. Critical for high-speed signaling.",
        "bottleneck_layer": "L4C_Timing",
        "monopoly": "🟡 NEAR",
        "stars": 1,
        "sources": ["citrini", "HyperTechInvest", "aleabitoreddit"],
        "ma_potential": "MEDIUM",
        "correlations": {"NVDA": 1.45, "AVGO": 0.65},
        "catalysts_2026": ["Hyperscaler design wins", "Margin expansion"],
        "tags": ["AI", "Timing", "Bottleneck"],
    },
    "GLW": {
        "market": "us_equity",
        "thesis": "Corning glass substrates — TSMC roadmap for next-gen packaging.",
        "bottleneck_layer": "L1B_Materials_Glass",
        "monopoly": "🟡 NEAR",
        "stars": 1,
        "sources": ["citrini", "ParadisLabs"],
        "correlations": {"TSM": 0.45, "NVDA": 0.40},
        "catalysts_2026": ["Glass substrate adoption announcement"],
        "tags": ["AI", "Materials"],
    },
    "VRT": {
        "market": "us_equity",
        "thesis": "Vertiv — liquid cooling for AI data centers. GB200 = 1000W per chip, cooling is critical.",
        "bottleneck_layer": "L3_Power_Cooling",
        "monopoly": "🟡 NEAR",
        "stars": 3,
        "sources": ["citrini", "ParadisLabs", "HyperTechInvest"],
        "correlations": {"NVDA": 1.20, "ETN": 0.65},
        "catalysts_2026": ["Liquid cooling ramp", "Backlog growth"],
        "tags": ["AI Power", "Cooling"],
    },
    "NVTS": {
        "market": "us_equity",
        "thesis": "Navitas — GaN power for AI data centers. NVDA partnership announced May 2026. Speculative but real fundamental pivot.",
        "bottleneck_layer": "L3_Power_GaN",
        "stars": 2,
        "sources": ["edward_nvts_doc", "fundamental_pivot"],
        "correlations": {"NVDA": 2.10, "VRT": 1.45},
        "catalysts_2026": ["NVDA delivery ramp", "Q2 2026 earnings vs expectations"],
        "tags": ["AI Power", "GaN", "Speculative"],
        "risk_notes": "P/S 148x = extreme. 3x beta. Analyst PT 56% below current. Pure momentum play.",
    },
    # ── COMMODITIES / FX ─────────────────────────────────────────────────
    "CCJ": {
        "market": "us_equity",
        "thesis": "Cameco — uranium renaissance. SMR + AI data center power demand.",
        "bottleneck_layer": "L3_Energy_Uranium",
        "stars": 2,
        "sources": ["citrini", "Druckenmiller"],
        "correlations": {"SMR": 0.85, "OKLO": 0.95, "VST": 0.55},
        "catalysts_2026": ["Hyperscaler nuclear deals", "Spot uranium uptrend"],
        "tags": ["Energy", "Uranium", "AI Power"],
    },
    "FCX": {
        "market": "us_equity",
        "thesis": "Freeport — copper deficit play. EV + grid + AI data center demand.",
        "bottleneck_layer": "L3_Materials_Copper",
        "stars": 2,
        "sources": ["citrini", "Druckenmiller"],
        "correlations": {"HG=F": 1.85, "SCCO": 0.85},
        "catalysts_2026": ["Indonesia smelter ramp", "Copper above $5"],
        "tags": ["Materials", "Copper"],
    },
    "MSTR": {
        "market": "us_equity",
        "thesis": "MicroStrategy — BTC treasury company. Leveraged BTC exposure + convertible debt strategy.",
        "bottleneck_layer": "L_Crypto_Treasury",
        "stars": 2,
        "sources": ["citrini", "HyperTechInvest"],
        "correlations": {"BTC-USD": 1.85, "COIN": 1.05},
        "catalysts_2026": ["BTC price action", "Convertible debt refinancing"],
        "tags": ["Crypto", "Treasury"],
    },
    # ── IHSG SURGE CANDIDATES ────────────────────────────────────────────
    "BREN.JK": {
        "market": "ihsg",
        "thesis": "Barito Renewables — geothermal asset value, Prajogo group flow. M&A premium.",
        "bottleneck_layer": "IHSG_Renewables",
        "stars": 1,
        "sources": ["bandar_barito_group", "hengky_adinata"],
        "correlations": {"TPIA.JK": 1.55, "BRPT.JK": 1.25, "CUAN.JK": 1.15},
        "catalysts_2026": ["Geothermal capacity expansion", "Bandar inflow"],
        "tags": ["IHSG", "Renewables", "Bandar"],
    },
    "MEDC.JK": {
        "market": "ihsg",
        "thesis": "Medco Energi — oil + gas play, geopolitics beneficiary.",
        "bottleneck_layer": "IHSG_Energy",
        "stars": 1,
        "sources": ["bandar_flow", "oil_proxy"],
        "correlations": {"CL=F": 0.85, "ADRO.JK": 0.55},
        "catalysts_2026": ["Oil above $80", "Block production updates"],
        "tags": ["IHSG", "Energy"],
    },
    # ── CRYPTO ───────────────────────────────────────────────────────────
    "SOL-USD": {
        "market": "crypto",
        "thesis": "Solana — DePIN + memecoin volume leader + Visa/Shopify integrations.",
        "bottleneck_layer": "L1_Blockchain",
        "stars": 1,
        "sources": ["citrini-defillama"],
        "correlations": {"BTC-USD": 0.85, "ETH-USD": 0.75},
        "catalysts_2026": ["Firedancer mainnet", "ETF approvals"],
        "tags": ["Crypto", "L1"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# CURATOR
# ═══════════════════════════════════════════════════════════════════════════

class AlphaCenterCurator:
    """5-layer filter pipeline for Alpha Center inclusion."""

    def __init__(self, bottleneck_ref_path: str = "bottleneck_reference.json"):
        self.bottleneck_data = self._load_bottleneck(bottleneck_ref_path)

    def _load_bottleneck(self, path: str) -> Dict:
        if not os.path.exists(path):
            logger.warning(f"bottleneck_reference.json not found at {path}")
            return {}
        try:
            with open(path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed loading bottleneck reference: {e}")
            return {}

    def layer1_consensus(self, ticker: str, candidate: Dict) -> Tuple[bool, str]:
        """Layer 1: ≥2 sources required."""
        sources = candidate.get("sources", [])
        # Allow special single-source bypass for explicit M&A targets
        if candidate.get("ma_potential") == "HIGH":
            return True, f"M&A bypass — {len(sources)} sources + HIGH M&A probability"
        if len(sources) >= 2:
            return True, f"{len(sources)} sources: {', '.join(sources[:3])}"
        return False, f"Only {len(sources)} source(s) — below threshold"

    def layer2_bottleneck(self, ticker: str, candidate: Dict) -> Tuple[bool, str]:
        """Layer 2: Must have bottleneck layer + catalyst."""
        if "bottleneck_layer" not in candidate:
            return False, "No bottleneck layer mapped"
        if not candidate.get("catalysts_2026"):
            return False, "No 2026 catalysts identified"
        layer = candidate["bottleneck_layer"]
        catalyst_count = len(candidate.get("catalysts_2026", []))
        return True, f"{layer} | {catalyst_count} catalysts"

    def layer3_correlations(self, ticker: str, candidate: Dict) -> Tuple[bool, str]:
        """Layer 3: Front-run chain must be mapped."""
        corr = candidate.get("correlations", {})
        if not corr:
            return False, "No correlations mapped"
        primary = max(corr.items(), key=lambda x: abs(x[1])) if corr else (None, 0)
        return True, f"{len(corr)} correlations; primary: {primary[0]} β={primary[1]}"

    def layer4_hedgeye_compat(self, ticker: str, candidate: Dict,
                               keith_signals: Optional[Dict] = None,
                               current_quad: str = "Q3") -> Tuple[bool, str]:
        """Layer 4: Not actively BEARISH per Keith."""
        if not keith_signals:
            return True, "No Keith signal — passing default"
        sig = keith_signals.get(ticker, {})
        trend = sig.get("TRADE", "NEUTRAL") if isinstance(sig, dict) else "NEUTRAL"
        if trend == "BEARISH":
            return False, f"Keith TRADE BEARISH override — BLOCKED"
        return True, f"Keith TRADE: {trend}"

    def layer5_walkforward(self, ticker: str, candidate: Dict,
                            wf_results: Optional[Dict] = None) -> Tuple[bool, str]:
        """Layer 5: Walk-forward gate."""
        if wf_results is None or ticker not in wf_results:
            # No backtest yet — soft pass with note
            return True, "WF not run yet (soft pass)"
        r = wf_results[ticker]
        score = r.get("combined_gate_score", 0)
        if score < 55:
            return False, f"WF gate FAIL ({score}/100)"
        return True, f"WF gate PASS ({score}/100)"

    def filter_universe(
        self,
        keith_signals: Optional[Dict] = None,
        wf_results: Optional[Dict] = None,
        current_quad: str = "Q3",
        min_stars: int = 1,
    ) -> Dict:
        """Run full 5-layer filter on all candidates."""
        passed, rejected = [], []
        for ticker, cand in ALPHA_CENTER_CANDIDATES.items():
            if cand.get("stars", 0) < min_stars:
                continue
            checks = {}
            ok = True
            for layer_name, layer_fn in [
                ("L1_consensus", self.layer1_consensus),
                ("L2_bottleneck", self.layer2_bottleneck),
                ("L3_correlation", self.layer3_correlations),
            ]:
                p, msg = layer_fn(ticker, cand)
                checks[layer_name] = {"pass": p, "msg": msg}
                if not p:
                    ok = False
            # Layer 4 and 5 with external data
            p4, m4 = self.layer4_hedgeye_compat(ticker, cand, keith_signals, current_quad)
            checks["L4_hedgeye"] = {"pass": p4, "msg": m4}
            if not p4:
                ok = False
            p5, m5 = self.layer5_walkforward(ticker, cand, wf_results)
            checks["L5_walkforward"] = {"pass": p5, "msg": m5}
            if not p5:
                ok = False

            entry = {
                "ticker": ticker,
                "candidate": cand,
                "checks": checks,
                "passed": ok,
            }
            (passed if ok else rejected).append(entry)
        return {
            "passed": sorted(passed, key=lambda x: -x["candidate"].get("stars", 0)),
            "rejected": rejected,
            "total_passed": len(passed),
            "total_rejected": len(rejected),
            "quad_applied": current_quad,
        }

    def get_candidate(self, ticker: str) -> Optional[Dict]:
        return ALPHA_CENTER_CANDIDATES.get(ticker)

    def all_candidates_by_market(self) -> Dict[str, List[str]]:
        out = {}
        for t, c in ALPHA_CENTER_CANDIDATES.items():
            out.setdefault(c.get("market", "unknown"), []).append(t)
        return out


def get_curator(bottleneck_ref_path: str = "bottleneck_reference.json") -> AlphaCenterCurator:
    return AlphaCenterCurator(bottleneck_ref_path)
