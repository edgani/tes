"""engines/thought_process_engine.py — Investment Thinking Frameworks (Sprint 7)

Encodes the THOUGHT PROCESS of legendary investors, not just their portfolios.
For each ticker, evaluates the stock against multiple framework lenses:

1. LEOPOLD ASCHENBRENNER  — Counting OOMs, Bottleneck Investing, AI infrastructure
2. COATUE                 — Sellers vs Buyers of Shortage, Capital Rotation, Agentic Big Bang
3. CITRINI RESEARCH       — Thematic bottleneck, second-order beneficiary, factor purity
4. HEDGEYE                — Quad-aware, rate-of-change, Risk Range
5. DRUCKENMILLER          — Liquidity-driven, fed reaction function
6. SOROS REFLEXIVITY      — Boom-bust cycle stage, market participants' bias

Output per ticker:
{
  "thesis_score": 0-100,        # composite conviction across all frameworks
  "matched_frameworks": [...],   # which frameworks rate this favorably
  "thesis_rationale": str,       # human-readable WHY  
  "framework_breakdown": {
    "leopold": {...},
    "coatue": {...},
    "citrini": {...},
    ...
  },
  "primary_thesis": str,         # the strongest framework match
  "ticker_role": str,            # "Seller of Shortage", "Bottleneck", "Capital Rotation Beneficiary", etc.
}

This becomes the "WHY" column in ticker detail cards.
"""
from __future__ import annotations

import math
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════
# FRAMEWORK 1: LEOPOLD ASCHENBRENNER (Situational Awareness)
# ════════════════════════════════════════════════════════════════════════

LEOPOLD_BOTTLENECK_TICKERS = {
    # Tier 1: Compute (GPU/TPU/Custom Silicon)
    "NVDA": {"layer": "GPU", "moat": "CUDA lock-in + ecosystem", "score": 95},
    "TSM":  {"layer": "Foundry", "moat": "Manufacturing monopoly", "score": 92},
    "AVGO": {"layer": "Custom Silicon", "moat": "Hyperscaler ASIC partnerships", "score": 88},
    "INTC": {"layer": "Foundry+CPU", "moat": "Contrarian fab comeback", "score": 70},
    "AMD":  {"layer": "GPU+CPU", "moat": "Server share growing", "score": 80},
    
    # Tier 2: Memory & Storage (HBM bottleneck for AI training)
    "MU":   {"layer": "Memory", "moat": "HBM3 demand, capacity-constrained", "score": 82},
    "005930.KS": {"layer": "Memory+Foundry", "moat": "Samsung scale", "score": 78},  # Samsung
    "000660.KS": {"layer": "Memory", "moat": "SK Hynix HBM3E lead", "score": 85},   # Hynix
    "STX":  {"layer": "Storage", "moat": "Mass storage for training data", "score": 70},
    "SNDK": {"layer": "Storage NAND", "moat": "Solid state for inference", "score": 65},
    "WDC":  {"layer": "Storage", "moat": "Hyperscaler HDD/SSD", "score": 60},
    
    # Tier 3: Optical/Photonic (data transfer bottleneck)
    "LITE": {"layer": "Optical/Laser", "moat": "Datacenter optics", "score": 88},
    "COHR": {"layer": "Photonic", "moat": "Laser systems + photonic components", "score": 85},
    "MRVL": {"layer": "Optical DSP", "moat": "Datacenter interconnect", "score": 80},
    
    # Tier 4: Power infrastructure (electricity bottleneck)
    "VST":  {"layer": "Power Gen", "moat": "Texas grid + nuclear", "score": 85},
    "CEG":  {"layer": "Nuclear Power", "moat": "Existing reactor fleet", "score": 88},
    "TLN":  {"layer": "Nuclear Power", "moat": "Nuclear restart story", "score": 82},
    "GEV":  {"layer": "Grid Equipment", "moat": "Power gen equipment", "score": 80},
    "BE":   {"layer": "Fuel Cells", "moat": "On-site power for datacenters (Oracle validated)", "score": 90},
    "PWR":  {"layer": "Power Infrastructure", "moat": "Grid buildout services", "score": 75},
    "ETN":  {"layer": "Electrical Equipment", "moat": "Datacenter electrical", "score": 70},
    "VRT":  {"layer": "Cooling/Power", "moat": "Datacenter cooling", "score": 78},
    
    # Tier 5: Bitcoin Miners pivoting to AI hosting
    "CORZ": {"layer": "Miner→AI", "moat": "CoreWeave 12-year HPC contracts", "score": 85},
    "IREN": {"layer": "Miner→AI", "moat": "AI hosting pivot", "score": 80},
    "APLD": {"layer": "Miner→AI", "moat": "Applied Digital pivot", "score": 78},
    "CIFR": {"layer": "Miner→AI", "moat": "Cipher Mining", "score": 70},
    "BTDR": {"layer": "Miner→AI", "moat": "Bitdeer", "score": 70},
    "RIOT": {"layer": "Miner→AI", "moat": "Riot AI hosting", "score": 70},
    "MARA": {"layer": "Miner→AI", "moat": "MARA Exaion acquisition", "score": 70},
    
    # Tier 6: Compute clouds (GPU rental)
    "CRWV": {"layer": "GPU Cloud", "moat": "Nvidia-backed neocloud, hyper-growth", "score": 90},
    "ORCL": {"layer": "Cloud+OCI", "moat": "Dependent on Nvidia/OpenAI hosting", "score": 65},
}

LEOPOLD_BUYERS_OF_SHORTAGE = {  # Hyperscaler capex absorbers
    "MSFT": {"thesis": "Largest AI revenue but OpenAI dependence risk", "score": 70},
    "GOOGL": {"thesis": "Cleanest — TPU + Gemini + Cloud 63% YoY + Waymo physical AI", "score": 85},
    "AMZN": {"thesis": "AWS fastest 15Q + Trainium + agentic commerce + robotics", "score": 82},
    "META": {"thesis": "Capex defensive — ad business + Reality Labs drag", "score": 60},
    "AAPL": {"thesis": "Not in AI race directly", "score": 50},
}


def evaluate_leopold(ticker: str, quad: str, prices: Dict, fred: Dict) -> Dict:
    """Apply Leopold's framework to a ticker."""
    t = ticker.upper()
    result = {
        "framework": "Leopold",
        "matched": False,
        "score": 0,
        "role": None,
        "thesis": None,
        "ooms_relevant": False,
    }
    
    # Check bottleneck list
    if t in LEOPOLD_BOTTLENECK_TICKERS:
        b = LEOPOLD_BOTTLENECK_TICKERS[t]
        result.update({
            "matched": True,
            "score": b["score"],
            "role": f"AI Bottleneck — {b['layer']}",
            "thesis": f"Counting OOMs: {b['layer']} layer bottleneck. {b['moat']}.",
            "ooms_relevant": True,
        })
    # Check hyperscaler buyers
    elif t in LEOPOLD_BUYERS_OF_SHORTAGE:
        b = LEOPOLD_BUYERS_OF_SHORTAGE[t]
        result.update({
            "matched": True,
            "score": b["score"],
            "role": "Hyperscaler — Capex Absorber",
            "thesis": b["thesis"],
            "ooms_relevant": True,
        })
    
    # Geopolitics modifier: if Q2/Q1 → US semis preferred over China
    if result["matched"] and "China" in (result.get("thesis") or "") and quad in ("Q1", "Q2"):
        result["score"] = max(0, result["score"] - 10)
    
    return result


# ════════════════════════════════════════════════════════════════════════
# FRAMEWORK 2: COATUE — Sellers vs Buyers of Shortage
# ════════════════════════════════════════════════════════════════════════

COATUE_SELLERS = {
    # AI Picks-and-Shovels: structurally exposed to shortage premium
    "NVDA": {"category": "GPU Lock-in", "structural_moat": True, "score": 92},
    "AVGO": {"category": "Custom Silicon", "structural_moat": True, "score": 88},
    "TSM":  {"category": "Foundry Monopoly", "structural_moat": True, "score": 90},
    
    # Cyclical shortage premium (watch for capacity decay)
    "MU":   {"category": "Memory Cyclical", "structural_moat": False, "decay_warning": True, "score": 70},
    "STX":  {"category": "Storage Cyclical", "structural_moat": False, "decay_warning": True, "score": 65},
    "SNDK": {"category": "NAND Cyclical", "structural_moat": False, "decay_warning": True, "score": 60},
    
    # Photonics shortage
    "LITE": {"category": "Optical Shortage", "structural_moat": False, "score": 80},
    "COHR": {"category": "Photonic Shortage", "structural_moat": False, "score": 78},
    "MRVL": {"category": "Optical DSP", "structural_moat": False, "score": 75},
    
    # Power generation shortage
    "VST":  {"category": "Power Sellers", "structural_moat": True, "score": 85},
    "CEG":  {"category": "Nuclear Power", "structural_moat": True, "score": 88},
    "BE":   {"category": "Fuel Cell Power", "structural_moat": True, "score": 88},
    "GEV":  {"category": "Power Equipment", "structural_moat": True, "score": 80},
}

COATUE_BUYERS = {
    # Hyperscalers — mispriced opposite direction, longer duration
    "GOOGL": {"category": "Cleanest Buyer", "score": 88, "note": "TPU + Gemini + Cloud 63%"},
    "AMZN":  {"category": "Strong Buyer", "score": 85, "note": "AWS + Trainium + agentic commerce"},
    "MSFT":  {"category": "Largest AI Rev but OpenAI risk", "score": 70},
    "META":  {"category": "Defensive Capex", "score": 55, "note": "No enterprise monetization"},
    "ORCL":  {"category": "Sub-scale", "score": 60},
}

# Agentic Big Bang beneficiaries (CPU rotation)
COATUE_AGENTIC_BIG_BANG = {
    "AMD":    {"thesis": "CPU rotation pure-play — server share >50%, taking from Intel", "score": 85},
    "MU":     {"thesis": "Agentic context windows = RAM-intensive demand", "score": 80},
    "000660.KS": {"thesis": "HBM3E for agentic memory persistence", "score": 82},  # SK Hynix
    "ANET":   {"thesis": "Networking for agentic clusters", "score": 75},
}


def evaluate_coatue(ticker: str, quad: str) -> Dict:
    """Apply COATUE's framework."""
    t = ticker.upper()
    result = {"framework": "COATUE", "matched": False, "score": 0, "role": None, "thesis": None}
    
    if t in COATUE_SELLERS:
        s = COATUE_SELLERS[t]
        decay = " ⚠️ Watch for shortage premium decay 24-36mo." if s.get("decay_warning") else ""
        result.update({
            "matched": True,
            "score": s["score"],
            "role": f"Seller of Shortage — {s['category']}",
            "thesis": f"Capital rotation: hyperscaler capex flows TO {ticker}. {'Structural moat' if s.get('structural_moat') else 'Cyclical pricing power'}.{decay}",
            "structural_moat": s.get("structural_moat", False),
        })
    elif t in COATUE_BUYERS:
        b = COATUE_BUYERS[t]
        result.update({
            "matched": True,
            "score": b["score"],
            "role": f"Buyer of Shortage — {b['category']}",
            "thesis": f"Capex compression now → FCF expansion later. {b.get('note', '')}",
        })
    elif t in COATUE_AGENTIC_BIG_BANG:
        a = COATUE_AGENTIC_BIG_BANG[t]
        result.update({
            "matched": True,
            "score": a["score"],
            "role": "Agentic Big Bang Beneficiary",
            "thesis": f"Next-leg rotation: training→agentic = CPU/memory intensive. {a['thesis']}",
        })
    
    return result


# ════════════════════════════════════════════════════════════════════════
# FRAMEWORK 3: CITRINI — Thematic Bottleneck & Second-Order
# ════════════════════════════════════════════════════════════════════════

CITRINI_THEMES = {
    "GLP-1": {
        "tickers": ["LLY", "NVO", "VKTX", "AMGN"],
        "second_order": {"WGT": "Weight loss accelerator", "WMT": "Food consumption pattern shift"},
        "thesis": "Obesity drug TAM $100B+ by 2030",
    },
    "AI_INFRA": {
        "tickers": ["NVDA", "AVGO", "TSM", "VST", "CEG", "BE"],
        "second_order": {
            "GEV": "Grid equipment for AI power",
            "LIN": "Industrial gases for fab",
            "AMAT": "Semicap for fab buildout",
            "ASML": "EUV monopoly for leading-edge",
        },
        "thesis": "AI buildout supply chain bottlenecks",
    },
    "ENERGY_TRANSITION": {
        "tickers": ["CCJ", "URA", "FCX", "MP"],
        "second_order": {"BWXT": "Nuclear small modular", "ALB": "Lithium for batteries"},
        "thesis": "Critical minerals + nuclear renaissance",
    },
    "FISCAL_DOMINANCE": {
        "tickers": ["GLD", "SLV", "BTC-USD", "VST", "CCJ"],
        "second_order": {"NEM": "Gold miners", "GDX": "Mining sector"},
        "thesis": "Real asset bid as fiat debt monetizes",
    },
    "AGING_DEMOGRAPHICS": {
        "tickers": ["UNH", "ELV", "ISRG", "BSX"],
        "second_order": {"GEHC": "Medical imaging", "MDT": "Devices"},
        "thesis": "Healthcare demand inelastic to recession",
    },
    "DEFENSE_REARMAMENT": {
        "tickers": ["LMT", "NOC", "RTX", "GD"],
        "second_order": {"HII": "Naval", "PLTR": "Defense AI", "AVAV": "Drones"},
        "thesis": "Post-Ukraine NATO 3% GDP target",
    },
}


def evaluate_citrini(ticker: str, quad: str) -> Dict:
    """Apply Citrini thematic framework."""
    t = ticker.upper()
    result = {"framework": "Citrini", "matched": False, "score": 0, "role": None, "thesis": None}
    
    for theme_name, theme_data in CITRINI_THEMES.items():
        if t in theme_data["tickers"]:
            result.update({
                "matched": True,
                "score": 80,
                "role": f"Thematic Primary — {theme_name.replace('_', ' ').title()}",
                "thesis": theme_data["thesis"],
                "theme": theme_name,
                "is_second_order": False,
            })
            return result
        elif t in theme_data.get("second_order", {}):
            so = theme_data["second_order"][t]
            result.update({
                "matched": True,
                "score": 70,
                "role": f"Second-Order — {theme_name.replace('_', ' ').title()}",
                "thesis": f"Second-derivative beneficiary: {so}",
                "theme": theme_name,
                "is_second_order": True,
            })
            return result
    
    return result


# ════════════════════════════════════════════════════════════════════════
# FRAMEWORK 4: HEDGEYE — Quad Playbook
# ════════════════════════════════════════════════════════════════════════

HEDGEYE_QUAD_PLAYBOOK = {
    "Q1": {  # Goldilocks: Growth ↑, Inflation ↓
        "long_tickers": {"QQQ", "SPY", "XLK", "XLC", "XLY", "ARKK", "NVDA", "AAPL", "MSFT",
                        "GOOGL", "META", "AMZN", "AMD", "AVGO", "BTC-USD", "ETH-USD", "MAGS"},
        "short_tickers": {"XLU", "XLP", "TLT", "GLD", "USO"},
        "thesis": "Tech and risk-on assets dominate. Defensives drag.",
    },
    "Q2": {  # Reflation: Growth ↑, Inflation ↑
        "long_tickers": {"XLF", "XLE", "XLI", "XLB", "KRE", "IWM", "XOM", "CVX", "OXY", "FCX"},
        "short_tickers": {"TLT", "IEF"},
        "thesis": "Cyclicals, financials, commodities lead. Long-duration bonds fade.",
    },
    "Q3": {  # Stagflation: Growth ↓, Inflation ↑  
        "long_tickers": {"GLD", "SLV", "GDX", "GDXJ", "USO", "XLE", "XLP", "XLU", "XOM"},
        "short_tickers": {"QQQ", "XLK", "XLY", "IWM", "ARKK"},
        "thesis": "Real assets bid. Tech and consumer discretionary fade.",
    },
    "Q4": {  # Deflation: Growth ↓, Inflation ↓
        "long_tickers": {"TLT", "IEF", "GLD", "XLU", "XLP", "XLV"},
        "short_tickers": {"QQQ", "XLK", "IWM", "XLY", "XLF", "XLE", "BTC-USD"},
        "thesis": "Bonds, defensives, gold. Worst for tech.",
    },
}


def evaluate_hedgeye(ticker: str, quad: str) -> Dict:
    """Apply Hedgeye Quad playbook."""
    t = ticker.upper()
    result = {"framework": "Hedgeye", "matched": False, "score": 0, "role": None, "thesis": None}
    
    pb = HEDGEYE_QUAD_PLAYBOOK.get(quad, {})
    longs = pb.get("long_tickers", set())
    shorts = pb.get("short_tickers", set())
    
    if t in longs:
        result.update({
            "matched": True,
            "score": 85,
            "role": f"Regime-Aligned LONG ({quad})",
            "thesis": f"Hedgeye {quad}: {pb.get('thesis', '')}",
            "direction_bias": "LONG",
        })
    elif t in shorts:
        result.update({
            "matched": True,
            "score": 85,
            "role": f"Regime-Aligned SHORT ({quad})",
            "thesis": f"Hedgeye {quad}: {pb.get('thesis', '')} ← {ticker} should be sold/shorted.",
            "direction_bias": "SHORT",
        })
    
    return result


# ════════════════════════════════════════════════════════════════════════
# FRAMEWORK 5: DRUCKENMILLER — Liquidity-Driven
# ════════════════════════════════════════════════════════════════════════

DRUCKENMILLER_LIQUIDITY_PLAYS = {
    # Bid on fed easing/excess liquidity
    "GLD": {"thesis": "Real money — bid when real yields fall", "score": 80},
    "BTC-USD": {"thesis": "Maximum-duration liquidity asset", "score": 85},
    "QQQ": {"thesis": "Long-duration growth = liquidity beneficiary", "score": 75},
    "TSLA": {"thesis": "High-multiple growth + liquidity", "score": 70},
    "NVDA": {"thesis": "Speculative leader benefits from easing", "score": 80},
    
    # Short fed tightening / liquidity drain
    "IWM": {"thesis": "Small caps suffer in tightening", "score": -70, "direction": "SHORT"},
    "KRE": {"thesis": "Regional banks vulnerable to deposit flight", "score": -70, "direction": "SHORT"},
}


def evaluate_druckenmiller(ticker: str, quad: str, fred: Dict) -> Dict:
    """Apply Druckenmiller liquidity framework."""
    t = ticker.upper()
    result = {"framework": "Druckenmiller", "matched": False, "score": 0, "role": None, "thesis": None}
    
    # Detect liquidity regime from fred (M2 growth, fed balance sheet trend)
    liquidity_easing = False
    try:
        import pandas as pd
        walcl = fred.get("WALCL")  # Fed balance sheet
        if walcl is not None:
            s = pd.to_numeric(walcl, errors="coerce").dropna()
            if len(s) >= 60:
                recent = s.tail(60).mean()
                older = s.iloc[-120:-60].mean() if len(s) >= 120 else s.iloc[:-60].mean()
                if recent > older * 1.01:
                    liquidity_easing = True
    except Exception:
        pass
    
    if t in DRUCKENMILLER_LIQUIDITY_PLAYS:
        d = DRUCKENMILLER_LIQUIDITY_PLAYS[t]
        bias = d.get("direction", "LONG")
        # Adjust score based on liquidity regime
        score = abs(d["score"])
        if not liquidity_easing and bias == "LONG":
            score *= 0.7  # liquidity tightening reduces conviction
        result.update({
            "matched": True,
            "score": score,
            "role": f"Druckenmiller {bias} — Liquidity Trade",
            "thesis": d["thesis"] + (f" Liquidity regime: {'EASING' if liquidity_easing else 'TIGHT/NEUTRAL'}"),
            "direction_bias": bias,
        })
    
    return result


# ════════════════════════════════════════════════════════════════════════
# FRAMEWORK 6: SOROS REFLEXIVITY — Boom-Bust Stage Analysis
# ════════════════════════════════════════════════════════════════════════

def evaluate_soros(ticker: str, boom_bust_stage: str, super_bubble_score: float) -> Dict:
    """Apply Soros reflexivity — different stage = different position."""
    result = {"framework": "Soros", "matched": False, "score": 0, "role": None, "thesis": None}
    
    stage_playbook = {
        "INCEPTION":    {"score": 60, "thesis": "Early-cycle: low expectations, high optionality"},
        "ACCELERATION": {"score": 80, "thesis": "Trend self-reinforcing, ride momentum"},
        "TESTING":      {"score": 50, "thesis": "Test of fundamentals — reduce exposure"},
        "TWILIGHT":     {"score": 30, "thesis": "Cracks appearing — exit core, hold trim"},
        "REVERSAL":     {"score": 10, "thesis": "Trend broken — short or short-call setup"},
    }
    
    stage_data = stage_playbook.get(boom_bust_stage, {})
    if stage_data:
        result.update({
            "matched": True,
            "score": stage_data["score"],
            "role": f"Soros — {boom_bust_stage}",
            "thesis": stage_data["thesis"] + (f" Super-bubble: {super_bubble_score:.0f}/100" if super_bubble_score else ""),
            "stage": boom_bust_stage,
        })
    
    return result


# ════════════════════════════════════════════════════════════════════════
# MASTER AGGREGATOR
# ════════════════════════════════════════════════════════════════════════

def compute_thesis(
    ticker: str,
    quad: str = "Q3",
    boom_bust_stage: str = "ACCELERATION",
    super_bubble_score: float = 0,
    prices: Optional[Dict] = None,
    fred: Optional[Dict] = None,
) -> Dict:
    """
    Master thesis composer — runs ticker through all 6 frameworks.
    Returns single dict with composite score + matched frameworks + thesis rationale.
    """
    prices = prices or {}
    fred = fred or {}
    
    frameworks = {
        "leopold": evaluate_leopold(ticker, quad, prices, fred),
        "coatue": evaluate_coatue(ticker, quad),
        "citrini": evaluate_citrini(ticker, quad),
        "hedgeye": evaluate_hedgeye(ticker, quad),
        "druckenmiller": evaluate_druckenmiller(ticker, quad, fred),
        "soros": evaluate_soros(ticker, boom_bust_stage, super_bubble_score),
    }
    
    matched = [name for name, fw in frameworks.items() if fw.get("matched")]
    scores = [fw.get("score", 0) for fw in frameworks.values() if fw.get("matched")]
    
    composite_score = sum(scores) / max(len(scores), 1) if scores else 0
    
    # Identify primary thesis (highest scoring framework)
    primary_fw = max(frameworks.items(), key=lambda x: x[1].get("score", 0) or 0)
    primary_thesis = primary_fw[1].get("thesis", "No matching framework")
    primary_role = primary_fw[1].get("role", "Generic")
    
    # Detect conflicts: if Hedgeye says SHORT but others say LONG, flag it
    conflicts = []
    hedgeye_bias = frameworks["hedgeye"].get("direction_bias")
    if hedgeye_bias == "SHORT":
        for fw_name, fw in frameworks.items():
            if fw_name != "hedgeye" and fw.get("score", 0) >= 70 and fw.get("matched"):
                conflicts.append(f"{fw_name.title()} positive but Hedgeye flags as Q-regime short")
    
    # Build rationale string
    rationale_parts = []
    if matched:
        for fw_name in matched:
            fw = frameworks[fw_name]
            score = fw.get("score", 0)
            role = fw.get("role", "")
            if score >= 70:
                rationale_parts.append(f"• **{fw_name.title()}**: {role} ({score:.0f})")
    
    rationale = "\n".join(rationale_parts) if rationale_parts else "No strong framework match — generic ticker"
    
    return {
        "ticker": ticker,
        "thesis_score": round(composite_score, 1),
        "matched_frameworks": matched,
        "n_matches": len(matched),
        "primary_framework": primary_fw[0] if primary_fw[1].get("matched") else None,
        "primary_role": primary_role if primary_fw[1].get("matched") else "Generic",
        "primary_thesis": primary_thesis,
        "thesis_rationale": rationale,
        "framework_breakdown": frameworks,
        "conflicts": conflicts,
        "ticker_role_tags": [fw.get("role") for fw in frameworks.values() if fw.get("role")],
    }


def analyze_multi(
    tickers: List[str],
    quad: str = "Q3",
    boom_bust_stage: str = "ACCELERATION",
    super_bubble_score: float = 0,
    prices: Optional[Dict] = None,
    fred: Optional[Dict] = None,
) -> Dict:
    """Batch process tickers."""
    results = {}
    for t in tickers:
        try:
            results[t] = compute_thesis(t, quad, boom_bust_stage, super_bubble_score, prices, fred)
        except Exception as e:
            logger.debug(f"Thesis compute failed for {t}: {e}")
    return results


def get_top_theses(results: Dict, top_n: int = 20) -> List[Dict]:
    """Return top N tickers by thesis score."""
    sorted_items = sorted(results.values(), key=lambda x: x.get("thesis_score", 0), reverse=True)
    return sorted_items[:top_n]


def get_framework_picks(results: Dict, framework: str, min_score: float = 70) -> List[Dict]:
    """Return all tickers matched by a specific framework above threshold."""
    out = []
    for ticker, r in results.items():
        fw = r.get("framework_breakdown", {}).get(framework, {})
        if fw.get("matched") and fw.get("score", 0) >= min_score:
            out.append({
                "ticker": ticker,
                "score": fw.get("score"),
                "role": fw.get("role"),
                "thesis": fw.get("thesis"),
            })
    return sorted(out, key=lambda x: x.get("score", 0), reverse=True)
