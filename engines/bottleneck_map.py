
"""
Bottleneck Chain Reaction Map v40
Sources: Citrini Research (AI bottleneck), Leopold Aschenbrenner (Situational Awareness),
         Hedgeye (Risk Range + Quad Playbook), SpotGamma (Options flow), VolSignals (Dealer regime)
"""

# Format: ticker -> {thesis, layer, correlation_to, bottleneck_type, catalyst, target_quad, market}
BOTTLENECK_TICKERS = {
    # AI Compute Buildout (Leopold / Citrini Phase 1)
    "NVDA": {
        "thesis": "GPU supply constraint — AI datacenter buildout demand exceeds TSMC CoWoS capacity. Every $1 of NVDA GPU pulls $3-5 of downstream infrastructure.",
        "layer": "AI Compute / GPU", "correlates_with": ["TSM", "AVGO", "COHR", "VST", "NXT"],
        "bottleneck": "HBM3E + CoWoS packaging capacity", "catalyst": "AGI by 2027 thesis — compute per dollar doubling every 6mo",
        "target_quad": ["Q1", "Q2"], "market": "us_equity", "priority": "P0"
    },
    "AMD": {
        "thesis": "Alternative GPU supplier — MI300X gaining share in hyperscaler. Bottleneck is memory bandwidth, not compute.",
        "layer": "AI Compute / GPU", "correlates_with": ["TSM", "MU", "SKHYNIX"],
        "bottleneck": "HBM supply allocation", "catalyst": "Datacenter revenue inflection",
        "target_quad": ["Q1", "Q2"], "market": "us_equity", "priority": "P1"
    },
    "AVGO": {
        "thesis": "Custom AI ASIC + networking — Google TPUv5/Amazon Trainium2 partner. Optical interconnect bottleneck.",
        "layer": "Networking / ASIC", "correlates_with": ["NVDA", "MRVL", "LITE", "COHR"],
        "bottleneck": "800G/1.6T SerDes yield", "catalyst": "Hyperscaler custom silicon ramp",
        "target_quad": ["Q1", "Q2"], "market": "us_equity", "priority": "P0"
    },
    "TSM": {
        "thesis": "Foundry chokepoint — 100% of advanced AI silicon passes through TSMC. CoWoS capacity expanding but still constrained.",
        "layer": "Foundry / Packaging", "correlates_with": ["NVDA", "AMD", "AVGO", "AMPH", "NXT"],
        "bottleneck": "CoWoS + advanced node capacity", "catalyst": "Capacity expansion capex $40B+",
        "target_quad": ["Q1", "Q2"], "market": "us_equity", "priority": "P0"
    },
    "MU": {
        "thesis": "HBM3E supply — only SK Hynix, Samsung, and Micron produce HBM. Micron is the US proxy.",
        "layer": "Memory / HBM", "correlates_with": ["NVDA", "AMD", "TSM"],
        "bottleneck": "HBM3E yield and burn-in time", "catalyst": "NVDA H200 ramp",
        "target_quad": ["Q1", "Q2"], "market": "us_equity", "priority": "P1"
    },
    "COHR": {
        "thesis": "Optical transceivers — 800G/1.6T datacenter interconnect. Every GPU cluster needs 2-3x optical ports.",
        "layer": "Optics / Interconnect", "correlates_with": ["NVDA", "AVGO", "MRVL", "LITE"],
        "bottleneck": "DSP + laser supply", "catalyst": "1.6T transceiver ramp 2H26",
        "target_quad": ["Q1", "Q2"], "market": "us_equity", "priority": "P1"
    },
    "MRVL": {
        "thesis": "Custom silicon + electro-optics — Inphi acquisition gives DSP dominance. AI datacenter switching.",
        "layer": "Networking / DSP", "correlates_with": ["AVGO", "COHR", "LITE", "NVDA"],
        "bottleneck": "5nm DSP yield", "catalyst": "AI backend switching upgrade cycle",
        "target_quad": ["Q1", "Q2"], "market": "us_equity", "priority": "P1"
    },
    "LITE": {
        "thesis": "Lasers and 3D sensing — datacenter optical components. Supply constrained due to rare earth materials.",
        "layer": "Optical Components", "correlates_with": ["COHR", "MRVL", "NVDA"],
        "bottleneck": "Indium Phosphide substrate", "catalyst": "Datacenter laser demand 2x YoY",
        "target_quad": ["Q1", "Q2"], "market": "us_equity", "priority": "P2"
    },
    "NXT": {
        "thesis": "Co-packaged optics (CPO) — next-gen packaging reduces power by 30%. Critical for 1.6T+ networks.",
        "layer": "Advanced Packaging / CPO", "correlates_with": ["TSM", "COHR", "AMPH"],
        "bottleneck": "CPO assembly yield", "catalyst": "NVDA Rubin architecture CPO adoption",
        "target_quad": ["Q1", "Q2"], "market": "us_equity", "priority": "P1"
    },
    "AMPH": {
        "thesis": "High-speed connectors — every GPU needs 8-16 high-speed connectors. Supply tight due to precision stamping.",
        "layer": "Interconnect / Connectors", "correlates_with": ["NVDA", "TSM", "NXT"],
        "bottleneck": "Precision stamping capacity", "catalyst": "NVDA B100/Rubin connector upgrade",
        "target_quad": ["Q1", "Q2"], "market": "us_equity", "priority": "P2"
    },
    "VST": {
        "thesis": "Power generation — AI datacenter power demand growing 20%+ CAGR. Grid interconnection queue is 3-5 years.",
        "layer": "Power / Infrastructure", "correlates_with": ["NVDA", "CEG", "BE"],
        "bottleneck": "Grid interconnection queue + transformer shortage", "catalyst": "Microsoft/Google 10GW+ datacenter deals",
        "target_quad": ["Q2", "Q3"], "market": "us_equity", "priority": "P0"
    },
    "CEG": {
        "thesis": "Nuclear restart — only viable 24/7 carbon-free baseload for AI. Three Mile Island restart for Microsoft.",
        "layer": "Power / Nuclear", "correlates_with": ["VST", "BE"],
        "bottleneck": "NRC licensing + fuel supply", "catalyst": "AI datacenter PPA announcements",
        "target_quad": ["Q2", "Q3"], "market": "us_equity", "priority": "P1"
    },
    "BE": {
        "thesis": "Small modular reactors — long-term nuclear solution. Nuscale competitor with faster regulatory path.",
        "layer": "Power / SMR", "correlates_with": ["VST", "CEG"],
        "bottleneck": "NRC certification timeline", "catalyst": "DOE loan guarantee awards",
        "target_quad": ["Q2", "Q3"], "market": "us_equity", "priority": "P2"
    },
    "SCCO": {
        "thesis": "Copper — AI datacenter uses 4x more copper than traditional. Grid electrification + EV double demand.",
        "layer": "Raw Materials / Copper", "correlates_with": ["FCX", "NVDA", "VST"],
        "bottleneck": "Grade decline + permitting delays", "catalyst": "Copper deficit 2026-2028",
        "target_quad": ["Q2", "Q3"], "market": "us_equity", "priority": "P1"
    },
    "FCX": {
        "thesis": "Copper + Gold — Grasberg expansion. Copper is the new oil for electrification.",
        "layer": "Raw Materials / Copper", "correlates_with": ["SCCO", "GC=F"],
        "bottleneck": "Indonesia export permit", "catalyst": "Grasberg underground ramp",
        "target_quad": ["Q2", "Q3"], "market": "us_equity", "priority": "P1"
    },
    "ALB": {
        "thesis": "Lithium — battery materials for grid storage. AI datacenter backup power needs lithium-ion.",
        "layer": "Raw Materials / Lithium", "correlates_with": ["SCCO", "TSLA"],
        "bottleneck": "Chile brine expansion delays", "catalyst": "Grid storage IRA credits",
        "target_quad": ["Q2", "Q3"], "market": "us_equity", "priority": "P2"
    },

    # Geopolitical / Energy (Mideast Supply Shock)
    "CL=F": {
        "thesis": "Crude oil — Strait of Hormuz risk premium. Iran escalation could remove 15-20% of global supply.",
        "layer": "Energy / Crude", "correlates_with": ["USO", "XOM", "CVX", "FRO"],
        "bottleneck": "Strait of Hormuz chokepoint", "catalyst": "Iran missile strikes on shipping",
        "target_quad": ["Q2", "Q3"], "market": "commodity", "priority": "P0"
    },
    "USO": {
        "thesis": "WTI ETF — direct crude exposure. Front-month roll cost negative in backwardation.",
        "layer": "Energy / ETF", "correlates_with": ["CL=F", "XLE"],
        "bottleneck": "Storage capacity", "catalyst": "SPR refill + geopolitical risk",
        "target_quad": ["Q2", "Q3"], "market": "commodity", "priority": "P1"
    },
    "XOM": {
        "thesis": "Supermajor — Permian + Guyana growth. Best FCF yield among oil majors.",
        "layer": "Energy / Integrated", "correlates_with": ["CVX", "CL=F", "XLE"],
        "bottleneck": "Permian pipeline capacity", "catalyst": "Q2 earnings beat + buyback",
        "target_quad": ["Q2", "Q3"], "market": "us_equity", "priority": "P1"
    },
    "CVX": {
        "thesis": "Supermajor — Tengiz expansion + PDC acquisition. Dividend aristocrat.",
        "layer": "Energy / Integrated", "correlates_with": ["XOM", "CL=F"],
        "bottleneck": "Kazakhstan logistics", "catalyst": "Tengiz FGP startup",
        "target_quad": ["Q2", "Q3"], "market": "us_equity", "priority": "P1"
    },
    "FRO": {
        "thesis": "VLCC tanker — rates spike when Hormuz disrupted. Floating storage demand rises.",
        "layer": "Shipping / Tankers", "correlates_with": ["CL=F", "TK", "INSW"],
        "bottleneck": "VLCC orderbook at 30-year low", "catalyst": "Hormuz insurance premium surge",
        "target_quad": ["Q2", "Q3"], "market": "us_equity", "priority": "P1"
    },

    # Indonesia Resource Nationalism
    "NCKL.JK": {
        "thesis": "Nickel — EV battery cathode. Indonesia processing quota restricts supply.",
        "layer": "Nickel / EV Battery", "correlates_with": ["ANTM.JK", "INCO.JK", "TSLA"],
        "bottleneck": "RKAB export quota", "catalyst": "EU battery regulation compliance",
        "target_quad": ["Q3", "Q4"], "market": "ihsg", "priority": "P1"
    },
    "ANTM.JK": {
        "thesis": "Nickel + Bauxite — diversified miner. Beneficiary of downstream policy.",
        "layer": "Nickel / Diversified", "correlates_with": ["NCKL.JK", "INCO.JK"],
        "bottleneck": "Smelter capacity", "catalyst": "HPAL plant commissioning",
        "target_quad": ["Q3", "Q4"], "market": "ihsg", "priority": "P1"
    },
    "ADRO.JK": {
        "thesis": "Coal — DMO (Domestic Market Obligation) restricts export volume. Metallurgical coal premium rising.",
        "layer": "Coal / Mining", "correlates_with": ["ITMG.JK", "PTBA.JK"],
        "bottleneck": "DMO quota + rail capacity", "catalyst": "Seaborne thermal coal price spike",
        "target_quad": ["Q3", "Q4"], "market": "ihsg", "priority": "P1"
    },
    "AALI.JK": {
        "thesis": "Palm Oil — EU Deforestation Regulation (EUDR) creates supply tightness. CPO price support.",
        "layer": "CPO / Agri", "correlates_with": ["LSIP.JK", "SMAR.JK"],
        "bottleneck": "EUDR traceability compliance", "catalyst": "El Niño supply disruption",
        "target_quad": ["Q3", "Q4"], "market": "ihsg", "priority": "P1"
    },
    "BBRI.JK": {
        "thesis": "Banking — largest micro-lending franchise. NIM expansion as BI rate stays elevated.",
        "layer": "Banking", "correlates_with": ["BMRI.JK", "BBCA.JK"],
        "bottleneck": "Credit growth ceiling", "catalyst": "Q2 earnings + dividend",
        "target_quad": ["Q3", "Q4"], "market": "ihsg", "priority": "P1"
    },

    # Crypto (On-chain accumulation)
    "BTC-USD": {
        "thesis": "Bitcoin — halving supply shock + ETF inflows. Whale accumulation at $60-70k zone.",
        "layer": "Crypto / Store of Value", "correlates_with": ["MSTR", "COIN", "ETH-USD"],
        "bottleneck": "Exchange BTC balance at 5-year low", "catalyst": "Halving supply squeeze",
        "target_quad": ["Q1", "Q2"], "market": "crypto", "priority": "P0"
    },
    "ETH-USD": {
        "thesis": "Ethereum — staking yield + ETF speculation. Smart contract platform dominance.",
        "layer": "Crypto / Smart Contract", "correlates_with": ["BTC-USD", "SOL-USD"],
        "bottleneck": "L2 fragmentation", "catalyst": "Spot ETH ETF approval",
        "target_quad": ["Q1", "Q2"], "market": "crypto", "priority": "P1"
    },
    "SOL-USD": {
        "thesis": "Solana — high throughput L1. Firedancer upgrade doubles TPS. DePIN narrative.",
        "layer": "Crypto / L1", "correlates_with": ["ETH-USD", "BTC-USD"],
        "bottleneck": "Network stability history", "catalyst": "Firedancer mainnet",
        "target_quad": ["Q1", "Q2"], "market": "crypto", "priority": "P1"
    },

    # Forex (COT + DXY correlation)
    "DX-Y.NYB": {
        "thesis": "DXY — Fed hawkish pivot vs ECB dovish. Safe haven bid on geopolitical risk.",
        "layer": "Forex / DXY", "correlates_with": ["EURUSD=X", "USDJPY=X", "UUP"],
        "bottleneck": "Fed policy divergence", "catalyst": "CPI sticky + Fed dot plot",
        "target_quad": ["Q2", "Q3"], "market": "forex", "priority": "P0"
    },
    "USDJPY=X": {
        "thesis": "USD/JPY — BoJ intervention zone at 160. Carry trade unwind risk.",
        "layer": "Forex / Major", "correlates_with": ["DX-Y.NYB", "EURUSD=X"],
        "bottleneck": "BoJ FX intervention", "catalyst": "BoJ rate hike surprise",
        "target_quad": ["Q2", "Q3"], "market": "forex", "priority": "P1"
    },
    "GC=F": {
        "thesis": "Gold — central bank buying + real yields falling. Hedgeye Q3 playbook long.",
        "layer": "Commodity / Precious Metal", "correlates_with": ["SLV", "GLD", "DX-Y.NYB"],
        "bottleneck": "Physical delivery squeeze", "catalyst": "Fed rate cut cycle",
        "target_quad": ["Q3", "Q4"], "market": "commodity", "priority": "P0"
    },
}

# Supply chain adjacency list for graph visualization
SUPPLY_CHAIN_EDGES = [
    ("NVDA", "TSM", "GPU silicon"),
    ("NVDA", "MU", "HBM memory"),
    ("NVDA", "COHR", "Optical interconnect"),
    ("NVDA", "VST", "Datacenter power"),
    ("NVDA", "NXT", "CPO packaging"),
    ("AVGO", "MRVL", "DSP + switching"),
    ("AVGO", "COHR", "Optical components"),
    ("TSM", "NXT", "CoWoS packaging"),
    ("TSM", "AMPH", "High-speed connectors"),
    ("VST", "CEG", "Nuclear baseload"),
    ("VST", "BE", "SMR development"),
    ("SCCO", "FCX", "Copper supply"),
    ("CL=F", "FRO", "Tanker transport"),
    ("CL=F", "XOM", "Upstream production"),
    ("BTC-USD", "MSTR", "Corporate treasury"),
    ("BTC-USD", "COIN", "Exchange infrastructure"),
    ("NCKL.JK", "ANTM.JK", "Nickel processing"),
    ("ADRO.JK", "ITMG.JK", "Coal export"),
    ("AALI.JK", "LSIP.JK", "CPO supply"),
]

def get_bottleneck_tickers():
    return list(BOTTLENECK_TICKERS.keys())

def get_ticker_bottleneck(ticker):
    return BOTTLENECK_TICKERS.get(ticker.upper(), None)

def get_correlated_tickers(ticker):
    info = get_ticker_bottleneck(ticker)
    if not info:
        return []
    return info.get("correlates_with", [])

def get_all_by_market(market_type):
    return {k:v for k,v in BOTTLENECK_TICKERS.items() if v["market"] == market_type}
