"""bottleneck_map.py — Bottleneck Ticker Universe & Supply Chain Graph
Maps tickers to bottleneck layers, catalysts, and correlated assets.
"""

# ═══════════════════════════════════════════════════════════════════
# BOTTLENECK TICKER UNIVERSE
# ═══════════════════════════════════════════════════════════════════
BOTTLENECK_TICKERS = [
    # AI Compute
    "NVDA", "AMD", "AVGO", "TSM", "MU", "SKHYNIX", "COHR", "MRVL", "NXT", "AMPH", "LITE",
    # Power / Cooling
    "VST", "CEG", "BE", "NEE", "D",
    # Raw Materials
    "SCCO", "FCX", "ALB", "MP", "PLS.AX",
    # Oil / Energy
    "CL=F", "USO", "XOM", "CVX", "COP", "OXY", "FANG",
    # Tankers / Shipping
    "FRO", "TK", "INSW", "NAT", "ZIM", "MATX", "DAC",
    # Refining
    "VLO", "MPC", "PSX", "DK",
    # Fertilizer / Ag
    "NTR", "MOS", "CF", "UAN",
    # Defense
    "LMT", "NOC", "RTX", "GD", "BA",
    # Indonesia
    "NCKL.JK", "ANTM.JK", "INCO.JK", "AALI.JK", "LSIP.JK", "SMAR.JK",
    "ADRO.JK", "ITMG.JK", "PTBA.JK", "BBRI.JK", "BMRI.JK", "BBCA.JK", "BBNI.JK", "BRIS.JK",
    "TLKM.JK", "EXCL.JK", "UNTR.JK", "BYAN.JK", "ICBP.JK", "INDF.JK", "KLBF.JK", "PGEO.JK", "WINS.JK",
    # Semiconductors
    "ASML", "LRCX", "AMAT", "KLAC", "ENTG", "MKSI",
    # Uranium
    "CCJ", "UUUU", "UEC", "DNN", "URA",
    # Copper / Grid
    "WIRE", "GNRC", "CHPT", "EVGO",
    # Rare Earth
    "MP", "NEO", "MPCO", "REEMF",
    # Bitcoin / Crypto
    "BTC-USD", "ETH-USD", "SOL-USD", "MSTR", "COIN", "RIOT", "MARA",
    # Container / Logistics
    "UPS", "FDX", "CHRW", "EXPD",
]

# Supply chain edges: upstream -> downstream
SUPPLY_CHAIN_EDGES = {
    # AI Compute
    "NVDA": ["TSM", "MU", "AVGO", "COHR", "MRVL"],
    "TSM": ["ASML", "LRCX", "AMAT", "KLAC"],
    "MU": ["SKHYNIX"],
    "COHR": ["NXT", "AMPH", "LITE"],
    "MRVL": ["NXT", "AMPH"],
    "NXT": ["AMPH"],
    # Power
    "VST": ["SCCO", "FCX"],  # power needs copper
    "CEG": ["CCJ", "UUUU"],  # nuclear needs uranium
    "BE": ["GNRC", "WIRE"],
    # Oil cascade
    "CL=F": ["FRO", "TK", "INSW", "NAT"],
    "FRO": ["VLO", "MPC", "PSX"],
    "VLO": ["NTR", "MOS", "CF"],
    "NTR": ["MOS", "CF"],
    # Indonesia
    "NCKL.JK": ["ANTM.JK", "INCO.JK"],
    "ADRO.JK": ["ITMG.JK", "PTBA.JK"],
    "AALI.JK": ["LSIP.JK", "SMAR.JK"],
    # Uranium
    "CCJ": ["UUUU", "UEC", "DNN"],
    "URA": ["NEE", "CEG", "VST"],
    # Copper/Grid
    "SCCO": ["FCX", "WIRE", "GNRC"],
    "WIRE": ["CHPT", "EVGO", "BE"],
    # Semiconductors
    "ASML": ["LRCX", "AMAT", "KLAC"],
    "ENTG": ["MKSI"],
    # Rare Earth
    "MP": ["NEO", "MPCO"],
    # Crypto
    "BTC-USD": ["MSTR", "COIN", "RIOT", "MARA"],
    "ETH-USD": ["COIN", "SOL-USD"],
}

# Reverse lookup
DOWNSTREAM_MAP = {}
for upstream, downstreams in SUPPLY_CHAIN_EDGES.items():
    for d in downstreams:
        DOWNSTREAM_MAP.setdefault(d, []).append(upstream)

# ═══════════════════════════════════════════════════════════════════
# BOTTLENECK METADATA
# ═══════════════════════════════════════════════════════════════════
BOTTLENECK_META = {
    "NVDA": {"layer": "AI GPU", "priority": "P0", "bottleneck": "CoWoS capacity", "catalyst": "Blackwell ramp Q3", "thesis": "Every $1 GPU pulls $3-5 infrastructure. CoWoS/HBM constrained.", "correlates_with": ["TSM", "MU", "AVGO", "VST"]},
    "AMD": {"layer": "AI GPU", "priority": "P1", "bottleneck": "MI300 yield", "catalyst": "MI350 2026", "thesis": "Alternative AI chip play. Memory bandwidth gap vs NVDA.", "correlates_with": ["TSM", "MU"]},
    "TSM": {"layer": "Foundry", "priority": "P0", "bottleneck": "3nm capacity", "catalyst": "AZ fab 2027", "thesis": "Monopoly on advanced nodes. Geopolitical tail risk.", "correlates_with": ["ASML", "NVDA", "AVGO"]},
    "MU": {"layer": "Memory / HBM", "priority": "P0", "bottleneck": "HBM3E yield", "catalyst": "HBM4 2026", "thesis": "HBM supply inelastic. 3-5x content per AI server.", "correlates_with": ["SKHYNIX", "TSM", "NVDA"]},
    "AVGO": {"layer": "Networking / ASIC", "priority": "P1", "bottleneck": "Tomahawk 6 supply", "catalyst": "Custom AI ASICs", "thesis": "Networking + custom silicon for hyperscalers.", "correlates_with": ["MRVL", "COHR"]},
    "COHR": {"layer": "Optics", "priority": "P1", "bottleneck": "800G/1.6T capacity", "catalyst": "L-band expansion", "thesis": "Data center interconnect bottleneck. CPO transition.", "correlates_with": ["MRVL", "LITE", "NXT"]},
    "MRVL": {"layer": "Networking / DSP", "priority": "P1", "bottleneck": "PAM4 DSP supply", "catalyst": "CPO integration", "thesis": "Optical DSP leader. AI cluster scaling driver.", "correlates_with": ["COHR", "AVGO", "NXT"]},
    "NXT": {"layer": "CPO / Connectors", "priority": "P0", "bottleneck": "Co-packaged optics", "catalyst": "1.6T CPO 2027", "thesis": "Leopold bottleneck: CPO is the last mile of AI infra.", "correlates_with": ["AMPH", "COHR", "MRVL"]},
    "AMPH": {"layer": "CPO / Connectors", "priority": "P1", "bottleneck": "High-speed connector capacity", "catalyst": "224G PAM4", "thesis": "Backplane + optical connector play. Undervalued vs buildout.", "correlates_with": ["NXT", "COHR"]},
    "VST": {"layer": "Power / Utility", "priority": "P0", "bottleneck": "Interconnection queue", "catalyst": "Data center PPA backlog", "thesis": "Power is the new oil for AI. Interconnection queue 3-5 years.", "correlates_with": ["CEG", "BE", "SCCO"]},
    "CEG": {"layer": "Power / Nuclear", "priority": "P0", "bottleneck": "Nuclear restart permits", "catalyst": "Three Mile Island restart", "thesis": "Nuclear renaissance for baseload AI power. Uranium demand pull.", "correlates_with": ["CCJ", "VST", "NEE"]},
    "BE": {"layer": "Power / Battery", "priority": "P1", "bottleneck": "Grid-scale storage", "catalyst": "DOE loan guarantees", "thesis": "Grid balancing for renewables + AI load. Battery storage gap.", "correlates_with": ["VST", "GNRC"]},
    "SCCO": {"layer": "Copper Mining", "priority": "P0", "bottleneck": "Grade decline + permit delays", "catalyst": "Chile water restrictions", "thesis": "Copper supercycle: EV + grid + datacenter. 5-7M tonne deficit by 2030.", "correlates_with": ["FCX", "WIRE", "VST"]},
    "FCX": {"layer": "Copper / Gold", "priority": "P1", "bottleneck": "Grasberg transition", "catalyst": "Underground ramp", "thesis": "Diversified copper + gold. Grasberg underground expansion.", "correlates_with": ["SCCO", "GLD"]},
    "ALB": {"layer": "Lithium", "priority": "P2", "bottleneck": "Brine evaporation", "catalyst": "Chile contract renegotiation", "thesis": "Lithium oversupplied short-term. Long-term EV penetration.", "correlates_with": ["SQM", "LAC"]},
    "CL=F": {"layer": "Crude Oil", "priority": "P0", "bottleneck": "Strait of Hormuz", "catalyst": "Iran escalation / OPEC+ spare capacity", "thesis": "15-20% of global supply at risk. VLCC rates + insurance spike.", "correlates_with": ["USO", "XOM", "CVX", "FRO"]},
    "FRO": {"layer": "Tankers / VLCC", "priority": "P0", "bottleneck": "VLCC rates + insurance", "catalyst": "Red Sea / Hormuz disruption", "thesis": "Geopolitical risk premium flows to tanker rates. FRO = pure-play VLCC.", "correlates_with": ["TK", "INSW", "NAT", "CL=F"]},
    "TK": {"layer": "Tankers / Product", "priority": "P1", "bottleneck": "Product tanker fleet age", "catalyst": "Russian shadow fleet sanctions", "thesis": "Product tanker tightness. LR2 rates at multi-year highs.", "correlates_with": ["FRO", "INSW"]},
    "VLO": {"layer": "Refining", "priority": "P1", "bottleneck": "Crack spreads", "catalyst": "Summer driving season", "thesis": "Refining margin expansion on heavy/sour crude discount.", "correlates_with": ["MPC", "PSX", "CL=F"]},
    "NTR": {"layer": "Fertilizer", "priority": "P1", "bottleneck": "Natural gas -> ammonia", "catalyst": "Spring planting demand", "thesis": "Gas-to-fertilizer spread. European gas price = margin driver.", "correlates_with": ["MOS", "CF", "NG=F"]},
    "LMT": {"layer": "Defense", "priority": "P1", "bottleneck": "Munitions replenishment", "catalyst": "NATO 2% GDP target", "thesis": "Multi-year defense upcycle. JASSM + THAAD backlog.", "correlates_with": ["NOC", "RTX", "GD"]},
    "NCKL.JK": {"layer": "Nickel / EV", "priority": "P0", "bottleneck": "Nickel processing quota", "catalyst": "Indonesia export ban escalation", "thesis": "Resource nationalism. HPAL capacity constrained. Battery-grade nickel deficit.", "correlates_with": ["ANTM.JK", "INCO.JK", "ALB"]},
    "ADRO.JK": {"layer": "Coal / Power", "priority": "P1", "bottleneck": "Domestic Market Obligation", "catalyst": "DMO quota enforcement", "thesis": "Coal export volume capped by DMO. Domestic price cap squeezes margins.", "correlates_with": ["ITMG.JK", "PTBA.JK"]},
    "AALI.JK": {"layer": "Palm Oil / CPO", "priority": "P1", "bottleneck": "EU Deforestation Regulation", "catalyst": "EUDR traceability deadline", "thesis": "Supply tightness from EUDR compliance costs. India/China demand resilient.", "correlates_with": ["LSIP.JK", "SMAR.JK"]},
    "BBRI.JK": {"layer": "Banking", "priority": "P1", "bottleneck": "BI rate duration", "catalyst": "Rate cut cycle 2026", "thesis": "High NIM from elevated BI rate. Micro-loan dominance = sticky funding.", "correlates_with": ["BMRI.JK", "BBCA.JK"]},
    "ASML": {"layer": "Lithography", "priority": "P0", "bottleneck": "High-NA EUV delivery", "catalyst": "EXE:5000 2028", "thesis": "Monopoly on sub-2nm lithography. Geopolitical export controls.", "correlates_with": ["TSM", "INTC", "NVDA"]},
    "CCJ": {"layer": "Uranium Mining", "priority": "P0", "bottleneck": "Kazakhstan supply uncertainty", "catalyst": "US SPUT restart / utility contracting", "thesis": "Nuclear renaissance + supply concentration risk. Long-term contracting wave.", "correlates_with": ["UUUU", "UEC", "URA", "CEG"]},
    "MP": {"layer": "Rare Earth", "priority": "P1", "bottleneck": "Separation capacity", "catalyst": "DoD stockpile mandate", "thesis": "Only US rare earth mine. Downstream magnet gap = vertical integration play.", "correlates_with": ["NEO", "MPCO"]},
    "BTC-USD": {"layer": "Crypto / Store of Value", "priority": "P1", "bottleneck": "Exchange balance", "catalyst": "Halving supply squeeze + ETF flows", "thesis": "Post-halving supply shock. Exchange BTC at 5-year low. Whale accumulation.", "correlates_with": ["ETH-USD", "MSTR", "COIN"]},
    "ETH-USD": {"layer": "Crypto / Smart Contract", "priority": "P1", "bottleneck": "L2 fragmentation", "catalyst": "ETH ETF staking approval", "thesis": "Smart contract platform. ETF approval = institutional bid. Staking yield = bond proxy.", "correlates_with": ["BTC-USD", "SOL-USD", "COIN"]},
    "ZIM": {"layer": "Container Shipping", "priority": "P2", "bottleneck": "Red Sea diversion capacity", "catalyst": "Houthi escalation / ceasefire", "thesis": "Red Sea diversion = +15% fleet miles. Rate volatility extreme.", "correlates_with": ["MATX", "DAC"]},
}

# ═══════════════════════════════════════════════════════════════════
# CHAIN REACTION DEFINITIONS (v40 expanded)
# ═══════════════════════════════════════════════════════════════════
CHAIN_REACTIONS = {
    "AI_COMPUTE_BUILDOUT": {
        "trigger": "AGI by 2027 (Leopold thesis)",
        "confidence": 0.85,
        "source": "Leopold Aschenbrenner / Citrini Research",
        "stages": [
            {"stage": 1, "layer": "AI Models / GPU", "tickers": ["NVDA", "AMD"], "bottleneck": "CoWoS + HBM supply"},
            {"stage": 2, "layer": "Foundry / Wafer", "tickers": ["TSM", "INTC"], "bottleneck": "3nm capacity + AZ fab"},
            {"stage": 3, "layer": "Memory / HBM", "tickers": ["MU", "SKHYNIX"], "bottleneck": "HBM3E yield + TSV capacity"},
            {"stage": 4, "layer": "Semiconductor Equipment", "tickers": ["ASML", "LRCX", "AMAT", "KLAC"], "bottleneck": "High-NA EUV + ALD tools"},
            {"stage": 5, "layer": "Networking / Optics", "tickers": ["AVGO", "MRVL", "COHR", "LITE"], "bottleneck": "800G/1.6T optical + DSP"},
            {"stage": 6, "layer": "CPO / Connectors", "tickers": ["NXT", "AMPH"], "bottleneck": "Co-packaged optics + 224G PAM4"},
            {"stage": 7, "layer": "Power / Cooling", "tickers": ["VST", "CEG", "BE", "NEE"], "bottleneck": "Interconnection queue + nuclear restart"},
            {"stage": 8, "layer": "Raw Materials", "tickers": ["SCCO", "FCX", "ALB", "MP"], "bottleneck": "Copper deficit + lithium brine + rare earth separation"},
        ]
    },
    "MIDEAST_SUPPLY_SHOCK": {
        "trigger": "Iran conflict escalation / Strait of Hormuz closure risk",
        "confidence": 0.70,
        "source": "Geopolitical cascade analysis",
        "stages": [
            {"stage": 1, "layer": "Crude Oil", "tickers": ["CL=F", "USO", "XOM", "CVX", "COP"], "bottleneck": "Strait of Hormuz (15-20% global supply)"},
            {"stage": 2, "layer": "Tankers / Shipping", "tickers": ["FRO", "TK", "INSW", "NAT"], "bottleneck": "VLCC rates + war risk insurance"},
            {"stage": 3, "layer": "Refining / Crack Spreads", "tickers": ["VLO", "MPC", "PSX", "DK"], "bottleneck": "Heavy/sour crude discount + capacity"},
            {"stage": 4, "layer": "Fertilizer / Ammonia", "tickers": ["NTR", "MOS", "CF", "UAN"], "bottleneck": "Natural gas -> ammonia (feedstock cost)"},
            {"stage": 5, "layer": "Agriculture / Food Security", "tickers": ["ZS=F", "ZW=F", "ZC=F"], "bottleneck": "Fertilizer cost pass-through + drought"},
            {"stage": 6, "layer": "Defense / Munitions", "tickers": ["LMT", "NOC", "RTX", "GD"], "bottleneck": "Munitions replenishment + drone supply"},
        ]
    },
    "INDONESIA_RESOURCE_NATIONALISM": {
        "trigger": "Q4 Deflation + export restrictions + downstream mandate",
        "confidence": 0.75,
        "source": "IHSG Specialist + Hedgeye Q4",
        "stages": [
            {"stage": 1, "layer": "Nickel / EV Battery", "tickers": ["NCKL.JK", "ANTM.JK", "INCO.JK"], "bottleneck": "HPAL capacity + export quota"},
            {"stage": 2, "layer": "Palm Oil / CPO", "tickers": ["AALI.JK", "LSIP.JK", "SMAR.JK"], "bottleneck": "EU Deforestation Regulation traceability"},
            {"stage": 3, "layer": "Coal / Domestic Obligation", "tickers": ["ADRO.JK", "ITMG.JK", "PTBA.JK"], "bottleneck": "DMO quota enforcement + price cap"},
            {"stage": 4, "layer": "Banking / NIM", "tickers": ["BBRI.JK", "BMRI.JK", "BBCA.JK", "BBNI.JK"], "bottleneck": "BI rate duration + credit cycle"},
            {"stage": 5, "layer": "Shipping / Logistics", "tickers": ["WINS.JK"], "bottleneck": "Port congestion + toll road tariffs"},
            {"stage": 6, "layer": "Consumer / Pharma", "tickers": ["ICBP.JK", "INDF.JK", "KLBF.JK"], "bottleneck": "Rupiah stability + import cost"},
        ]
    },
    "COPPER_ELECTRIFICATION": {
        "trigger": "EV + grid + datacenter = 5-7M tonne deficit by 2030",
        "confidence": 0.80,
        "source": "Glencore / Wood Mackenzie supply models",
        "stages": [
            {"stage": 1, "layer": "Copper Mining", "tickers": ["SCCO", "FCX", "GLEN.L"], "bottleneck": "Grade decline + water + permit delays"},
            {"stage": 2, "layer": "Wire / Cable", "tickers": ["WIRE", "GNRC"], "bottleneck": "Grid interconnection queue + transformer shortage"},
            {"stage": 3, "layer": "Grid Infrastructure", "tickers": ["VST", "NEE", "D", "BE"], "bottleneck": "Transmission buildout + NIMBY"},
            {"stage": 4, "layer": "EV Charging", "tickers": ["CHPT", "EVGO", "BLNK"], "bottleneck": "Utilization rate + grid connection"},
            {"stage": 5, "layer": "EV OEM", "tickers": ["TSLA", "RIVN", "LCID"], "bottleneck": "Copper motor winding + battery cost"},
        ]
    },
    "URANIUM_NUCLEAR_RENAISSANCE": {
        "trigger": "AI power demand + net-zero = nuclear restart + new builds",
        "confidence": 0.75,
        "source": "UxC / Yellow Cake supply-demand model",
        "stages": [
            {"stage": 1, "layer": "Uranium Mining", "tickers": ["CCJ", "UUUU", "UEC", "DNN"], "bottleneck": "Kazakhstan supply concentration + ISR capacity"},
            {"stage": 2, "layer": "Enrichment / Conversion", "tickers": ["URA", "LEU"], "bottleneck": "SWU capacity + Russian sanctions risk"},
            {"stage": 3, "layer": "Nuclear Utilities", "tickers": ["CEG", "VST", "NEE", "EXC"], "bottleneck": "NRC restart permits + waste storage"},
            {"stage": 4, "layer": "SMR / Advanced Reactor", "tickers": ["OKLO", "SMR", "BWXT"], "bottleneck": "NRC licensing + fuel fabrication"},
            {"stage": 5, "layer": "Grid / Backup", "tickers": ["BE", "GNRC"], "bottleneck": "Baseload complement + storage"},
        ]
    },
    "SEMICONDUCTOR_EQUIPMENT": {
        "trigger": "Sub-2nm transition + China embargo = equipment supercycle",
        "confidence": 0.80,
        "source": "SEMI / TechInsights capex tracker",
        "stages": [
            {"stage": 1, "layer": "Lithography", "tickers": ["ASML"], "bottleneck": "High-NA EUV delivery + spare parts"},
            {"stage": 2, "layer": "Deposition / Etch", "tickers": ["LRCX", "AMAT"], "bottleneck": "GAA transistor complexity + chamber lead time"},
            {"stage": 3, "layer": "Metrology / Inspection", "tickers": ["KLAC", "MKSI"], "bottleneck": "EUV mask inspection + yield ramp"},
            {"stage": 4, "layer": "Materials / Chemicals", "tickers": ["ENTG", "CCMP"], "bottleneck": "High-purity chemicals + EUV resist"},
            {"stage": 5, "layer": "Substrate / Advanced Packaging", "tickers": ["AMKR", "INTC"], "bottleneck": "Glass core substrate + RDL capacity"},
        ]
    },
    "RARE_EARTH_DEFENSE": {
        "trigger": "China export controls + DoD stockpile mandate",
        "confidence": 0.70,
        "source": "DoD Critical Minerals Report",
        "stages": [
            {"stage": 1, "layer": "Rare Earth Mining", "tickers": ["MP"], "bottleneck": "Mountain Pass throughput + separation"},
            {"stage": 2, "layer": "Separation / Magnet", "tickers": ["NEO", "MPCO"], "bottleneck": "NdFeB magnet capacity + heavy rare earth sourcing"},
            {"stage": 3, "layer": "Defense / Aerospace", "tickers": ["LMT", "NOC", "RTX", "BA"], "bottleneck": "F-35 motor + missile guidance magnet supply"},
            {"stage": 4, "layer": "EV Motors", "tickers": ["TSLA", "GM", "F"], "bottleneck": "Permanent magnet motor vs induction switch"},
        ]
    },
    "RED_SEA_CONTAINER_CRISIS": {
        "trigger": "Houthi attacks + cape routing = +15% fleet miles + rate spike",
        "confidence": 0.65,
        "source": "Drewry / Freightos container index",
        "stages": [
            {"stage": 1, "layer": "Container Shipping", "tickers": ["ZIM", "MATX"], "bottleneck": "Red Sea diversion capacity + newbuild delivery"},
            {"stage": 2, "layer": "Air Freight", "tickers": ["UPS", "FDX"], "bottleneck": "Sea-air substitution + e-commerce volume"},
            {"stage": 3, "layer": "Logistics / Brokerage", "tickers": ["CHRW", "EXPD"], "bottleneck": "Rate volatility + carrier contract renegotiation"},
            {"stage": 4, "layer": "Retail Inventory", "tickers": ["AMZN", "WMT", "TGT"], "bottleneck": "Safety stock rebuild + working capital"},
            {"stage": 5, "layer": "Manufacturing", "tickers": ["AAPL", "NKE", "DE"], "bottleneck": "Component lead times + just-in-sea disruption"},
        ]
    },
    "BITCOIN_HALVING_SQUEEZE": {
        "trigger": "Post-halving supply shock + ETF inflows + exchange balance low",
        "confidence": 0.75,
        "source": "Glassnode / Coin Metrics on-chain data",
        "stages": [
            {"stage": 1, "layer": "Bitcoin Mining", "tickers": ["RIOT", "MARA", "CLSK", "BITF"], "bottleneck": "Hashrate competition + energy cost"},
            {"stage": 2, "layer": "Bitcoin Treasury", "tickers": ["MSTR", "TSLA"], "bottleneck": "Corporate adoption + accounting rules"},
            {"stage": 3, "layer": "Exchange / Custody", "tickers": ["COIN", "HOOD"], "bottleneck": "ETF creation/redemption + custody insurance"},
            {"stage": 4, "layer": "Layer 2 / Payments", "tickers": ["BTC-USD", "ETH-USD", "SOL-USD"], "bottleneck": "Lightning adoption + fee market"},
            {"stage": 5, "layer": "Mining Equipment", "tickers": ["NVDA", "AMD"], "bottleneck": "ASIC supply + immersion cooling"},
        ]
    },
    "BIOTECH_GLP1_SUPPLY": {
        "trigger": "GLP-1 demand outstrips manufacturing capacity 10:1",
        "confidence": 0.70,
        "source": "IQVIA / Evaluate Pharma demand model",
        "stages": [
            {"stage": 1, "layer": "GLP-1 Drug", "tickers": ["LLY", "NVO"], "bottleneck": "Peptide API capacity + fill-finish"},
            {"stage": 2, "layer": "CDMO / Manufacturing", "tickers": ["DHR", "TECD", "CTLT"], "bottleneck": "Sterile injectable capacity + dual-source"},
            {"stage": 3, "layer": "Peptide API", "tickers": ["AMPH", "PETQ"], "bottleneck": "Solid-phase synthesis + resin supply"},
            {"stage": 4, "layer": "Delivery Device", "tickers": ["DXCM", "TNDM"], "bottleneck": "Auto-injector pen + cold chain"},
            {"stage": 5, "layer": "Complications / Insurance", "tickers": ["UNH", "CI"], "bottleneck": "Coverage expansion + obesity classification"},
        ]
    },
}

def get_bottleneck_tickers():
    """Return full bottleneck ticker list."""
    return BOTTLENECK_TICKERS

def get_ticker_bottleneck(ticker: str):
    """Return bottleneck metadata for a ticker."""
    return BOTTLENECK_META.get(ticker.upper(), None)

def get_correlated_tickers(ticker: str):
    """Return correlated tickers from bottleneck graph."""
    meta = get_ticker_bottleneck(ticker)
    if meta:
        return meta.get("correlates_with", [])
    return []

def get_all_by_market(market_type: str = "us_equity"):
    """Filter bottleneck tickers by market."""
    if market_type == "us_equity":
        return [t for t in BOTTLENECK_TICKERS if not t.endswith(".JK") and "=" not in t and "-USD" not in t]
    elif market_type == "commodity":
        return [t for t in BOTTLENECK_TICKERS if "=" in t or t in ["USO", "GLD", "SLV", "UNG"]]
    elif market_type == "forex":
        return [t for t in BOTTLENECK_TICKERS if t.endswith("=X") or t in ["DX-Y.NYB", "UUP"]]
    elif market_type == "crypto":
        return [t for t in BOTTLENECK_TICKERS if "-USD" in t or t in ["MSTR", "COIN", "RIOT", "MARA"]]
    elif market_type == "ihsg":
        return [t for t in BOTTLENECK_TICKERS if t.endswith(".JK")]
    return BOTTLENECK_TICKERS

def get_chain_reaction(name: str):
    """Get a chain reaction definition by name."""
    return CHAIN_REACTIONS.get(name, None)

def get_all_chain_reactions():
    """Return all chain reaction definitions."""
    return CHAIN_REACTIONS
