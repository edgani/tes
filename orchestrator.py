"""orchestrator.py - MacroRegime Data Orchestrator v40.5 (Wired)
Patched: v39 → v40.5
Fixes:
- Keith signal sync engine now CALLED (was imported but dead)
- Legacy double-compute skipped when v40 overwrites (faster load)
- Chain reactions merged: supply_chain_chains + chain_reactions_catalog → chain_reactions
- External data wired top-level: options_data, cot_data, finra_short, onchain_data, cme_oi
- IHSG broker proxy & crypto tokens wired to snap
- Tier S outputs wired: entry_decisions, methodology_scores, movement_regimes, daily_plays, ihsg_specialist
"""
from __future__ import annotations
from types import SimpleNamespace
import os, sys, json, math, time, logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("orchestrator")

for _noisy in ("yfinance", "yfinance.data", "yfinance.utils", "peewee", "urllib3", "integrator_guide"):
    logging.getLogger(_noisy).setLevel(logging.CRITICAL)

def _safe_progress(cb, msg: str, pct: float):
    if cb is None:
        return
    try:
        cb(msg, float(pct))
    except Exception:
        pass

# ── IMPORTS (defensive fallbacks for every engine) ──
try:
    from data.loader import load_prices, load_snapshot, save_snapshot, snapshot_age_str
except Exception as e:
    logger.error(f"Failed to import data.loader: {e}")
    load_prices = None
    def load_snapshot(max_age_hours=12.0): return None
    def save_snapshot(x): pass
    def snapshot_age_str(): return "unknown"

try:
    from data.fred_loader import load_fred_bundle
except Exception as e:
    logger.error(f"Failed to import fred_loader: {e}")
    def load_fred_bundle(force_refresh=True):
        return {"series": {}, "meta": {"loaded": 0, "requested": 0}}

try:
    from engines.gip_engine import GIPEngine, GIPResult, get_playbook
except Exception as e:
    logger.error(f"Failed to import gip_engine: {e}")
    GIPEngine = None; GIPResult = None
    def get_playbook(sq, mq):
        return {"structural": sq, "monthly": mq, "best_assets": [], "worst_assets": [],
                "strategy": f"Trade {sq} regime. Monthly: {mq}.",
                "sectors_overweight": [], "sectors_underweight": [], "style": "", "fx": "", "bonds": ""}

try:
    from engines.market_health_engine import MarketHealthEngine
except Exception as e:
    logger.error(f"Failed to import market_health_engine: {e}"); MarketHealthEngine = None

try:
    from engines.gamma_engine import GammaEngine
except Exception: GammaEngine = None
try:
    from engines.greeks_proxy import GreeksProxy
except Exception: GreeksProxy = None
try:
    from engines.vanna_charm_flows import get_vanna_charm_flows
except Exception:
    def get_vanna_charm_flows(*args, **kwargs): return {}
try:
    from engines.bottleneck_engine import BottleneckEngine
except Exception: BottleneckEngine = None
try:
    from engines.risk_range_engine import RiskRangeEngine
except Exception as e:
    logger.error(f"Failed to import risk_range_engine: {e}")
    class RiskRangeEngine:
        def __init__(self, **kwargs): pass
        def run(self, prices): return {}

try:
    from engines.aaii_scraper import get_behavioral_macro
except Exception:
    def get_behavioral_macro(*args, **kwargs):
        return {"bullish": 30, "bearish": 30, "neutral": 40, "yves": {"alert": None, "alert_level": "NONE"}}
try:
    from engines.odte_monitor import run_odte_monitor
except Exception:
    def run_odte_monitor(*args, **kwargs):
        return {"expiry": "-", "tickers": {}, "cascade_warning": False, "summary": "0DTE unavailable"}
try:
    from engines.skew_term_engine import run_skew_term
except Exception:
    def run_skew_term(*args, **kwargs): return {"skew_data": {}, "term_regime": "NORMAL"}
try:
    from engines.reflexivity_engine import run_reflexivity
except Exception:
    def run_reflexivity(*args, **kwargs): return {"super_bubble_score": 5.0, "stage": "INCEPTION", "ticker_scores": {}}
try:
    from engines.boombust_engine import classify_stage
except Exception:
    def classify_stage(*args, **kwargs): return {"stage": "INCEPTION", "stage_confidence": 0.5}
try:
    from engines.conviction_sizing import run_sizing
except Exception:
    def run_sizing(*args, **kwargs): return {}
try:
    from engines.interconnect_engine import run_interconnect
except Exception:
    def run_interconnect(*args, **kwargs): return {"active_scenarios": [], "scenarios": [], "summary": "Interconnect unavailable"}
try:
    from engines.yfinance_options import YFinanceOptionsEngine
except Exception: YFinanceOptionsEngine = None
try:
    from engines.scenario_discovery_engine import run_scenario_discovery
except Exception:
    def run_scenario_discovery(*args, **kwargs): return {"scenarios": [], "active_scenarios": [], "watch_scenarios": [], "summary": "Unavailable"}
try:
    from engines.transmission_engine import run_transmission
except Exception:
    def run_transmission(*args, **kwargs): return {"scenarios": [], "active_scenarios": [], "watch_scenarios": [], "summary": "Unavailable"}
try:
    from engines.regime_transition_engine import run_regime_transition
except Exception:
    def run_regime_transition(*args, **kwargs): return {"current_quad": "Q3", "transitions": {}, "summary": "Unavailable"}
try:
    from engines.news_nlp_engine_v3 import run_news_nlp
except Exception:
    def run_news_nlp(*args, **kwargs): return {"ticker_specific": {}, "emergent_narratives": [], "rumor_watch": [], "analyzed_count": 0}
try:
    from engines.gex_engine import analyze_multi as gex_analyze_multi
except Exception:
    def gex_analyze_multi(*args, **kwargs): return {}
try:
    from engines.charm_proxy_engine import analyze_multi as charm_analyze_multi
except Exception:
    def charm_analyze_multi(*args, **kwargs): return {}
try:
    from engines.vanna_proxy_engine import analyze_multi as vanna_analyze_multi
except Exception:
    def vanna_analyze_multi(*args, **kwargs): return {}
try:
    from engines.odte_enhanced import analyze_multi as odte_enhanced_multi
except Exception:
    def odte_enhanced_multi(*args, **kwargs): return {}
try:
    from engines.structure_quality import analyze_multi as structure_analyze_multi
except Exception:
    def structure_analyze_multi(*args, **kwargs): return {}
try:
    from engines.afternoon_signal import analyze_multi as afternoon_analyze_multi
except Exception:
    def afternoon_analyze_multi(*args, **kwargs): return {}
try:
    from engines.volga_proxy import analyze_volga
except Exception:
    def analyze_volga(*args, **kwargs): return {}
try:
    from engines.institutional_proxy import analyze_multi as inst_analyze_multi
except Exception:
    def inst_analyze_multi(*args, **kwargs): return {}
try:
    from engines.bottleneck_discovery_v3 import run_bottleneck_discovery_v3
except Exception:
    def run_bottleneck_discovery_v3(*args, **kwargs): return {"active_bottlenecks": [], "watch_bottlenecks": [], "summary": "Unavailable"}

try:
    from engines.cascade_engine import run_all_cascades, bottleneck_full_cascade
    _V2_CASCADE = True
except Exception as e:
    logger.debug(f"Optional engine not present: cascade_engine: {e}")
    _V2_CASCADE = False
    def run_all_cascades(*a, **k): return {"cascades": {}, "active_shocks": {}}
    def bottleneck_full_cascade(*a, **k): return {"impacts": []}

try:
    from engines.yves_engine import run_yves_v2
    _V2_YVES = True
except Exception:
    _V2_YVES = False
    def run_yves_v2(*a, **k): return {"alerts": [], "summary": {"level": "NONE"}}
try:
    from engines.portfolio_sizing import run_portfolio_sizing
    _V2_SIZING = True
except Exception:
    _V2_SIZING = False
    def run_portfolio_sizing(*a, **k): return {"positions": [], "total_deployed_pct": 0, "cash_pct": 1.0}
try:
    from engines.discovery_brain import run_discovery_brain
    _V2_DISCOVERY = True
except Exception:
    _V2_DISCOVERY = False
    def run_discovery_brain(*a, **k): return {"by_mode": {}, "top_10": [], "summary": {}}
try:
    from engines.cem_karsan_universal import analyze_multi as cem_universal_multi
    _V2_CEM = True
except Exception:
    _V2_CEM = False
    def cem_universal_multi(*a, **k): return {}
try:
    from engines.ticker_universe_expander import run_ticker_expander
    _V2_EXPANDER = True
except Exception:
    _V2_EXPANDER = False
    def run_ticker_expander(*a, **k): return {"new_tickers": [], "candidates": [], "auto_add_recommended": []}
try:
    from engines.supply_chain_graph_real import run_supply_chain_analysis, reverse_lookup as supply_reverse
    _V2_SUPPLY = True
except Exception:
    _V2_SUPPLY = False
    def run_supply_chain_analysis(*a, **k): return {"chokepoints": [], "propagation": {}, "summary": {}}
    def supply_reverse(*a, **k): return []
try:
    from engines.composite_signal_engine import analyze_multi as composite_analyze_multi, compute_composite_signal
    _V2_COMPOSITE = True
except Exception:
    _V2_COMPOSITE = False
    def composite_analyze_multi(*a, **k): return {}
    def compute_composite_signal(*a, **k): return {"direction": "NEUTRAL", "confidence": 0}
try:
    from engines.risk_setup_engine import calculate_risk_setup as v2_risk_setup
    _V2_RISK_SETUP = True
except Exception:
    _V2_RISK_SETUP = False; v2_risk_setup = None
try:
    from engines.bonds_xau_regime import run_bonds_xau_regime
    _V2_BONDS_XAU = True
except Exception:
    _V2_BONDS_XAU = False
    def run_bonds_xau_regime(*a, **k): return {"ok": False, "regime": "UNKNOWN", "ticker_biases": {}}
try:
    from engines.simulation_engine import run_simulation_batch, get_simulation_summary, filter_by_simulation
    _V2_SIM = True
except Exception:
    _V2_SIM = False
    def run_simulation_batch(*a, **k): return {}
    def get_simulation_summary(*a, **k): return {"total": 0, "passed": 0, "failed": 0, "avg_score": 0}
    def filter_by_simulation(rows, sim_results, threshold=65, require_pass=True): return rows
try:
    from engines.thought_process_engine import compute_thesis as v7_compute_thesis, analyze_multi as v7_thesis_multi
    _V7_THOUGHT = True
except Exception:
    _V7_THOUGHT = False
    def v7_compute_thesis(*a, **k): return {"thesis_score": 0, "matched_frameworks": []}
    def v7_thesis_multi(*a, **k): return {}
try:
    from engines.markov_regime_engine_v3 import run_markov_v3
    _V7_MARKOV = True
except Exception:
    _V7_MARKOV = False
    def run_markov_v3(*a, **k):
        class _M:
            current_regime = "UNKNOWN"; confidence = 0; kelly_fraction = 0.25; notes = ["v3 unavailable"]
            forecast_1m = {}; forecast_3m = {}; forecast_6m = {}
            change_point_alert = False; change_point_probability = 0; stationary = {}; regime_probabilities = {}
        return _M()
try:
    from engines.smart_money_tracker import run_smart_money_analysis, get_ticker_smart_money
    _V7_SMART = True
except Exception:
    _V7_SMART = False
    def run_smart_money_analysis(*a, **k): return {"ok": False, "n_funds_tracked": 0}
    def get_ticker_smart_money(*a, **k): return {"smart_money_held": False}
try:
    from engines.capital_rotation_engine import compute_capital_rotation, get_ticker_capital_rotation_role
    _V7_CAPROT = True
except Exception:
    _V7_CAPROT = False
    def compute_capital_rotation(*a, **k): return {"ok": False}
    def get_ticker_capital_rotation_role(*a, **k): return None
try:
    from engines.ust_auction_tracker import run_ust_auction_tracker
    _V7_UST = True
except Exception:
    _V7_UST = False
    def run_ust_auction_tracker(*a, **k): return {"ok": False}
try:
    from engines.vrp_scanner import scan_vrp
    _V7_VRP = True
except Exception:
    _V7_VRP = False
    def scan_vrp(*a, **k): return {"ok": False, "calls_to_action": []}
try:
    from engines.squeeze_scanner import scan_squeezes
    _V7_SQUEEZE = True
except Exception:
    _V7_SQUEEZE = False
    def scan_squeezes(*a, **k): return {"ok": False, "imminent_squeezes": [], "strong_candidates": [], "watch_list": []}
try:
    from engines.karsan_vol_scanner import scan_karsan
    _V9_KARSAN = True
except Exception:
    _V9_KARSAN = False
    def scan_karsan(*a, **k): return {"ok": False, "per_ticker": {}, "squeeze_setups": [], "sell_premium": [], "buy_convexity": []}
try:
    from engines.spotgamma_gex_engine import run_spotgamma_scanner
    _V9_SPOTGAMMA = True
except Exception:
    _V9_SPOTGAMMA = False
    def run_spotgamma_scanner(*a, **k): return {"ok": False, "per_ticker_proxy_gex": {}, "compass": {}}
try:
    from engines.leopold_methodology import run_leopold_scan
    _V9_LEOPOLD = True
except Exception:
    _V9_LEOPOLD = False
    def run_leopold_scan(*a, **k): return {"ok": False, "per_ticker": {}, "top_picks_by_layer": {}, "asymmetry_setups": [], "written_off_recovering": []}
try:
    from engines.coatue_methodology import run_coatue_scan
    _V9_COATUE = True
except Exception:
    _V9_COATUE = False
    def run_coatue_scan(*a, **k): return {"ok": False, "per_ticker": {}, "sellers_top": [], "buyers_top": [], "decay_alerts": [], "agentic_plays": []}
try:
    from engines.volsignals_regime import compute_dealer_regime_multi
    _V11_VOLSIGNALS = True
except Exception:
    _V11_VOLSIGNALS = False
    def compute_dealer_regime_multi(*a, **k): return {}
try:
    from engines.spotgamma_levels import compute_structural_levels_multi
    _V11_SPOTGAMMA = True
except Exception:
    _V11_SPOTGAMMA = False
    def compute_structural_levels_multi(*a, **k): return {}
try:
    from engines.schadner_iv import schadner_iv, validate_iv_proxy
    _V11_SCHADNER = True
except Exception:
    _V11_SCHADNER = False
    def schadner_iv(*a, **k): return None
    def validate_iv_proxy(*a, **k): return {}
try:
    from engines.integrator_guide import enhance_snapshot, get_enhanced_summary
    _V32_INTEGRATOR = True
except Exception:
    _V32_INTEGRATOR = False
    def enhance_snapshot(snap, prices, portfolio_value=100_000): return snap
    def get_enhanced_summary(snap): return snap.get("summary", {})
try:
    from engines.narrative_engine import build_narrative
    _V10_NARRATIVE = True
except Exception:
    _V10_NARRATIVE = False
    def build_narrative(result): return {}

try:
    import requests
    import xml.etree.ElementTree as ET
    _has_requests = True
except Exception:
    _has_requests = False

try:
    from config.settings import (
        US_SECTORS, US_FACTORS, FOREX_PAIRS, COMMODITIES, CRYPTO,
        BONDS, IHSG_UNIVERSE, MACRO_PROXIES, US_BUCKETS, IHSG_BUCKETS,
        FX_BUCKETS, COMMODITY_BUCKETS, CRYPTO_BUCKETS,
        QUAD_ASSET_PERFORMANCE, TICKER_SECTOR, MARKET_CLASSIFICATION,
        BOTTLENECK_PROFILES,
    )
except Exception as e:
    logger.debug(f"Optional engine not present: settings: {e}")
    US_SECTORS = {}; US_FACTORS = {}; FOREX_PAIRS = {}; COMMODITIES = {}; CRYPTO = {}
    BONDS = {}; IHSG_UNIVERSE = {}; MACRO_PROXIES = {}
    US_BUCKETS = {}; IHSG_BUCKETS = {}; FX_BUCKETS = {}; COMMODITY_BUCKETS = {}; CRYPTO_BUCKETS = {}
    QUAD_ASSET_PERFORMANCE = {}; TICKER_SECTOR = {}; MARKET_CLASSIFICATION = {}; BOTTLENECK_PROFILES = {}

# ═══════════════════════════════════════════════════════════════════════
# TIER S ENGINE IMPORTS (v40 — ALL WIRED)
# ═══════════════════════════════════════════════════════════════════════
_V40_TIER_S = {}

try:
    from engines.alpha_synthesis_v37 import run_alpha_synthesis
    _V40_TIER_S["alpha_synthesis"] = True
except Exception as e:
    _V40_TIER_S["alpha_synthesis"] = False
    def run_alpha_synthesis(*a, **k): return {"frameworks": [], "top_signals": [], "synthesis_summary": {}}
try:
    from engines.daily_play_engine import DailyPlayEngine
    _V40_TIER_S["daily_play"] = True
except Exception:
    _V40_TIER_S["daily_play"] = False
    class DailyPlayEngine:
        def scan_all(self, *a, **k): return {"plays": [], "summary": "DailyPlayEngine unavailable"}
try:
    from engines.ihsg_specialist_v38 import IHSGSpecialistEngine
    _V40_TIER_S["ihsg_specialist"] = True
except Exception:
    _V40_TIER_S["ihsg_specialist"] = False
    class IHSGSpecialistEngine:
        def analyze(self, *a, **k): return {"goreng_phases": [], "conglomerate_flows": [], "hedgeye_check": {}}
try:
    from engines.entry_decision_engine import decide_entry
    _V40_TIER_S["entry_decision"] = True
except Exception:
    _V40_TIER_S["entry_decision"] = False
    def decide_entry(*a, **k): return {"action": "AVOID", "direction": "NEUTRAL", "conviction": 0}
try:
    from engines.movement_timing_engine import MovementTimingDetector
    _V40_TIER_S["movement_timing"] = True
except Exception:
    _V40_TIER_S["movement_timing"] = False
    class MovementTimingDetector:
        def detect(self, *a, **k): return None
try:
    from engines.frontrun_engine import FrontRunEngine
    _V40_TIER_S["frontrun"] = True
except Exception:
    _V40_TIER_S["frontrun"] = False
    class FrontRunEngine:
        def scan(self, *a, **k): return {"front_run_signals": [], "catalyst_timeline": []}
try:
    from engines.chain_reaction_engine import ChainReactionEngine
    _V40_TIER_S["chain_reaction"] = True
except Exception:
    _V40_TIER_S["chain_reaction"] = False
    class ChainReactionEngine:
        def __init__(self, *a, **k): pass
        def project_all(self, *a, **k): return {}
try:
    from engines.methodology_pack import evaluate_all_pack
    _V40_TIER_S["methodology_pack"] = True
except Exception:
    _V40_TIER_S["methodology_pack"] = False
    def evaluate_all_pack(*a, **k): return {}
try:
    from engines.walkforward_backtest_engine import batch_gatekeeper
    _V40_TIER_S["walkforward"] = True
except Exception:
    _V40_TIER_S["walkforward"] = False
    def batch_gatekeeper(*a, **k): return {}
try:
    from engines.alpha_gatekeeper import batch_evaluate
    _V40_TIER_S["alpha_gatekeeper"] = True
except Exception:
    _V40_TIER_S["alpha_gatekeeper"] = False
    def batch_evaluate(*a, **k): return {}
try:
    from engines.vix_bucket_engine import classify_vix_bucket, apply_vix_position_sizing
    _V40_TIER_S["vix_bucket"] = True
except Exception:
    _V40_TIER_S["vix_bucket"] = False
    def classify_vix_bucket(*a, **k): return {"bucket": "NORMAL", "label": "Investable", "multiplier": 1.0}
    def apply_vix_position_sizing(*a, **k): return k[1] if len(k) > 1 else 0
try:
    from engines.hedgeye_position_sizing import calculate_position_size
    _V40_TIER_S["hedgeye_sizing"] = True
except Exception:
    _V40_TIER_S["hedgeye_sizing"] = False
    def calculate_position_size(*a, **k): return {"size_pct": 0.02, "dollar_size": 2000, "mode": "DEFAULT"}

# ═══════════════════════════════════════════════════════════════════════
# KEITH SIGNAL SYNC — NOW WIRED (v40.5)
# ═══════════════════════════════════════════════════════════════════════
try:
    from engines.keith_signal_sync import resolve_direction, should_avoid, get_keith_summary
    _V40_KEITH = True
except Exception as e:
    logger.debug(f"Keith signal sync not present: {e}")
    _V40_KEITH = False
    def resolve_direction(*a, **k): return {"direction": k[1] if len(k) > 1 else "LONG", "override": False, "basis": "No Keith signal", "keith_trade": "NEUTRAL", "keith_trend": "NEUTRAL", "duration_mismatch": False}
    def should_avoid(*a, **k): return False
    def get_keith_summary(): return {"total_signals": 0}

logger.info(
    f"v40.5 engines loaded: cascade={_V2_CASCADE} yves={_V2_YVES} sizing={_V2_SIZING} "
    f"discovery={_V2_DISCOVERY} cem={_V2_CEM} expander={_V2_EXPANDER} "
    f"supply={_V2_SUPPLY} composite={_V2_COMPOSITE} risk_setup={_V2_RISK_SETUP} "
    f"bonds_xau={_V2_BONDS_XAU} simulation={_V2_SIM} "
    f"tier_s={sum(_V40_TIER_S.values())}/{len(_V40_TIER_S)} keith={_V40_KEITH}"
)

HEDGEYE_COUNTRY_OVERRIDE = {"Indonesia": "Q4"}

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

def _strip_html(text):
    if not text:
        return ""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def _fetch_news_headlines(tickers: List[str], max_per_ticker: int = 5) -> Dict[str, List[dict]]:
    if not _has_requests:
        return {}
    headlines = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    session = requests.Session()
    session.headers.update(headers)
    for ticker in tickers[:30]:
        time.sleep(0.5)
        try:
            url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
            r = session.get(url, timeout=6)
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.content)
            items = []
            for item in root.iter('item'):
                title = item.find('title')
                pub = item.find('pubDate')
                link = item.find('link')
                if title is not None and title.text:
                    items.append({"title": _strip_html(title.text), "date": pub.text if pub is not None else "", "url": link.text if link is not None else "", "source": "Yahoo Finance"})
                if len(items) >= max_per_ticker:
                    break
            if items:
                headlines[ticker] = items
        except Exception as e:
            logger.debug(f"News fetch failed for {ticker}: {e}")
    return headlines

def _analyze_news(headlines: Dict[str, List[dict]], prices: dict) -> dict:
    bullish_kw = ["surge","soar","rally","bull","upgrade","beat","strong","growth","breakthrough","deal","partnership","ai","record","expansion","launch","approve","buyback","dividend","blockbuster","moon","rocket"]
    bearish_kw = ["crash","plunge","bear","downgrade","miss","weak","loss","layoff","investigation","fine","delay","recall","debt","bankrupt","cut","short","sell","dump","collapse","crisis"]
    rumor_kw = ["reportedly","rumor","speculation","considering","exploring","potential","may","might","could","planned","sources say","exclusive","breaking","leak","in talks","approaching","eyeing"]
    theme_kw = {
        "ai": ["ai","artificial intelligence","llm","chatgpt","agentic","model","machine learning","nvidia","openai"],
        "semiconductor": ["chip","semiconductor","gpu","cpu","tsmc","hbm","dram","foundry","wafer"],
        "energy": ["oil","gas","energy","solar","renewable","crude","power","grid","transformer"],
        "crypto": ["bitcoin","crypto","blockchain","etf","ethereum","btc","eth","solana"],
        "fed_rates": ["fed","federal reserve","rate cut","rate hike","powell","interest rate","fomc"],
        "geopolitical": ["war","sanctions","china","taiwan","trade","tariff","middle east","ukraine"],
        "biotech": ["fda","trial","drug","vaccine","biotech","pharma","approval"],
        "ev": ["ev","electric vehicle","tesla","battery","lithium","charging"],
    }
    ticker_news = {}
    rumor_watch = []
    narratives = []
    for ticker, items in headlines.items():
        if not items:
            continue
        bull_count = 0; bear_count = 0; rumor_count = 0
        themes = set()
        latest_titles = []
        for item in items:
            title_lower = item["title"].lower()
            latest_titles.append(item["title"])
            bull_count += sum(1 for kw in bullish_kw if kw in title_lower)
            bear_count += sum(1 for kw in bearish_kw if kw in title_lower)
            rumor_count += sum(1 for kw in rumor_kw if kw in title_lower)
            for theme, kws in theme_kw.items():
                if any(kw in title_lower for kw in kws):
                    themes.add(theme)
        total_kw = bull_count + bear_count
        sentiment_score = (bull_count - bear_count) / max(total_kw, 1)
        rumor_score = min(rumor_count / max(len(items), 1), 1.0)
        s = prices.get(ticker)
        r1m = None
        if s is not None and len(s) >= 22:
            try:
                s_clean = pd.to_numeric(s, errors="coerce").dropna()
                if len(s_clean) >= 22:
                    r1m = float(s_clean.iloc[-1] / s_clean.iloc[-22] - 1)
            except Exception:
                pass
        front_run_signal = None
        if rumor_score > 0.4 and sentiment_score > 0.3:
            front_run_signal = "STRONG_BULLISH_RUMOR"
        elif rumor_score > 0.4 and sentiment_score < -0.3:
            front_run_signal = "STRONG_BEARISH_RUMOR"
        elif rumor_score > 0.25:
            front_run_signal = "RUMOR_WATCH"
        elif sentiment_score > 0.4 and (r1m is None or r1m < 0.08):
            front_run_signal = "NEWS_MOMENTUM_BUILDING"
        elif sentiment_score < -0.4:
            front_run_signal = "NEGATIVE_HEADLINE_RISK"
        elif bull_count >= 3 and bear_count == 0:
            front_run_signal = "BULLISH_CLUSTER"
        ticker_news[ticker] = {
            "headlines": latest_titles[:3],
            "sentiment_score": round(sentiment_score, 2),
            "rumor_score": round(rumor_score, 2),
            "themes": list(themes),
            "front_run_signal": front_run_signal,
            "r1m": r1m,
            "bull_count": bull_count,
            "bear_count": bear_count,
        }
        if front_run_signal:
            rumor_watch.append({"ticker": ticker, "signal": front_run_signal, "sentiment": round(sentiment_score, 2), "rumor": round(rumor_score, 2), "themes": list(themes), "headline": latest_titles[0] if latest_titles else "", "r1m": r1m})
        if themes and abs(sentiment_score) > 0.15:
            narratives.append({"ticker": ticker, "theme": list(themes)[0] if themes else "general", "sentiment": sentiment_score, "headline": latest_titles[0] if latest_titles else ""})
    emergent = {}
    for n in narratives:
        theme = n["theme"]
        if theme not in emergent:
            emergent[theme] = {"mentions": 0, "tickers": [], "avg_sentiment": 0, "headlines": []}
        emergent[theme]["mentions"] += 1
        emergent[theme]["tickers"].append(n["ticker"])
        emergent[theme]["avg_sentiment"] += n["sentiment"]
        emergent[theme]["headlines"].append(n["headline"])
    for theme in emergent:
        count = emergent[theme]["mentions"]
        emergent[theme]["avg_sentiment"] = round(emergent[theme]["avg_sentiment"] / count, 2) if count > 0 else 0
        emergent[theme]["tickers"] = list(dict.fromkeys(emergent[theme]["tickers"]))[:10]
        emergent[theme]["headlines"] = emergent[theme]["headlines"][:5]
        emergent[theme]["supply_chain_hits"] = 0
    return {
        "ticker_specific": ticker_news,
        "emergent_narratives": [{"name": k, **v} for k, v in emergent.items()],
        "rumor_watch": sorted(rumor_watch, key=lambda x: abs(x["sentiment"]) + x["rumor"], reverse=True)[:25],
        "analyzed_count": sum(len(v) for v in headlines.values()),
    }

def _auto_discover_tickers(bottleneck_ref, cascade_results, news_analysis, supply_chain, current_tickers: Set[str]) -> List[str]:
    NAME_TO_SYMBOL = {
        "TSMC": "TSM", "SAMSUNG": "005930.KS", "SEAGATE": "STX", "KEYENCE": "6861.T",
        "FANUC": "6954.T", "YASKAWA": "6506.T", "NABTESCO": "6268.T", "LINDE": "LIN",
        "BESI": "BESI.AS", "FUJIBO": "3104.T", "THK": "6481.T", "SKHYNIX": "000660.KS",
        "SK HYNIX": "000660.KS", "DISCO": "6146.T", "TOKYO ELECTRON": "8035.T",
        "ASML": "ASML", "INFINEON": "IFX.DE", "STMICRO": "STM",
    }
    BLOCKLIST = {"VVIX", "AMEC", "ASIA METAL", "HELIUM ONE", "JEN", "LPK", "SYTECH",
                "SIPHONICS", "ELSFPS", "TUC", "RPI", "SMHN", "SMHN.DE"}
    def _valid_symbol(t: str) -> bool:
        if not t or " " in t or len(t) > 12 or t in BLOCKLIST:
            return False
        return all(c.isalnum() or c in ".^-=" for c in t)
    candidates = set()
    def _add(raw):
        t = (raw or "").replace("$", "").strip().upper()
        t = NAME_TO_SYMBOL.get(t, t)
        if t and t not in current_tickers and _valid_symbol(t):
            candidates.add(t)
    for item in bottleneck_ref.get("consensus_heatmap", []):
        _add(item.get("ticker", ""))
    if cascade_results and isinstance(cascade_results, dict):
        for shock, data in cascade_results.get("active_shocks", {}).items():
            if isinstance(data, dict):
                for t in data.get("impacted_tickers", []): _add(t)
                for t in data.get("beneficiaries", []): _add(t)
    for rw in news_analysis.get("rumor_watch", []):
        _add(rw.get("ticker", ""))
    if supply_chain and isinstance(supply_chain, dict):
        for cp in supply_chain.get("chokepoints", []):
            if isinstance(cp, dict):
                for t in cp.get("tickers", []): _add(t)
    return sorted(candidates)

def _build_supply_chain_chains(bottleneck_ref, cascade_results, prices):
    chains = []
    chains.append({
        "name": "AI Compute Buildout", "trigger": "AGI by 2027 (Leopold thesis)",
        "stages": [
            {"stage": 1, "layer": "AI Models", "tickers": ["NVDA", "AMD", "AVGO"], "bottleneck": "GPU supply"},
            {"stage": 2, "layer": "Memory / HBM", "tickers": ["MU", "SKHYNIX", "TSM"], "bottleneck": "HBM3E capacity"},
            {"stage": 3, "layer": "Power / Cooling", "tickers": ["VST", "CEG", "BE", "LITE"], "bottleneck": "Data center power"},
            {"stage": 4, "layer": "Optics / Interconnect", "tickers": ["COHR", "LITE", "MRVL"], "bottleneck": "800G/1.6T optical"},
            {"stage": 5, "layer": "CPO / Connectors", "tickers": ["NXT", "AMPH", "HLIT"], "bottleneck": "Co-packaged optics"},
            {"stage": 6, "layer": "Raw Materials", "tickers": ["SCCO", "FCX", "ALB"], "bottleneck": "Copper, Lithium, Rare Earth"},
        ], "confidence": 0.85, "source": "Leopold Aschenbrenner Situational Awareness",
    })
    chains.append({
        "name": "Mideast Supply Shock", "trigger": "Iran conflict escalation",
        "stages": [
            {"stage": 1, "layer": "Crude Oil", "tickers": ["CL=F", "USO", "XOM", "CVX"], "bottleneck": "Strait of Hormuz"},
            {"stage": 2, "layer": "Tankers / Shipping", "tickers": ["FRO", "TK", "INSW", "NAT"], "bottleneck": "VLCC rates & insurance"},
            {"stage": 3, "layer": "Refining", "tickers": ["VLO", "MPC", "PSX"], "bottleneck": "Crack spreads"},
            {"stage": 4, "layer": "Fertilizer / Ag", "tickers": ["NTR", "MOS", "CF"], "bottleneck": "Natural gas -> ammonia"},
            {"stage": 5, "layer": "Defense", "tickers": ["LMT", "NOC", "RTX"], "bottleneck": "Munitions replenishment"},
        ], "confidence": 0.70, "source": "Geopolitical cascade analysis",
    })
    chains.append({
        "name": "Indonesia Resource Nationalism", "trigger": "Q4 Deflation + export restrictions",
        "stages": [
            {"stage": 1, "layer": "Nickel / EV Battery", "tickers": ["NCKL.JK", "ANTM.JK", "INCO.JK"], "bottleneck": "Nickel processing quota"},
            {"stage": 2, "layer": "Palm Oil / CPO", "tickers": ["AALI.JK", "LSIP.JK", "SMAR.JK"], "bottleneck": "EU Deforestation Regulation"},
            {"stage": 3, "layer": "Coal / Power", "tickers": ["ADRO.JK", "ITMG.JK", "PTBA.JK"], "bottleneck": "Domestic market obligation"},
            {"stage": 4, "layer": "Shipping / Logistics", "tickers": ["WINS.JK"], "bottleneck": "Port congestion"},
        ], "confidence": 0.75, "source": "IHSG Specialist + Hedgeye Q4",
    })
    return chains

def _generate_front_run_all_markets(prices, news_analysis, bottleneck_ref, supply_chains, quad):
    candidates = []
    seen = set()
    def _add_candidate(ticker, theme, role, priority, why, source, market_type, projection=None):
        if ticker in seen or not ticker:
            return
        opt = _options_proxy_for_ticker(ticker, prices)
        px = opt.get("price") if opt.get("ok") else None
        if px is None and ticker in prices:
            try:
                s = pd.to_numeric(pd.Series(prices[ticker]), errors="coerce").dropna()
                if len(s) > 0: px = float(s.iloc[-1])
            except: pass
        proj = projection or {}
        if not proj and px and px > 0:
            if theme in ("AI Compute Buildout", "CPO / Connectors") and px < 100:
                proj = {"target_px": round(px * 4, 2), "rationale": "Leopold bottleneck: AI infra undervalued vs buildout", "timeframe": "12-18mo", "confidence": 0.75}
            elif theme == "Mideast Supply Shock" and market_type == "commodity":
                proj = {"target_px": round(px * 1.4, 2), "rationale": "Geopolitical risk premium + supply disruption", "timeframe": "3-6mo", "confidence": 0.65}
            elif market_type == "crypto" and theme == "Whale Accumulation":
                proj = {"target_px": round(px * 1.5, 2), "rationale": "On-chain accumulation + funding neutral", "timeframe": "1-3mo", "confidence": 0.60}
        candidates.append({"ticker": ticker, "theme": theme, "role": role, "priority": priority, "why_front_run": why, "source": source, "market_type": market_type, "options": opt, "price": px, "projection": proj, "catalyst": _find_catalyst(ticker, bottleneck_ref)})
        seen.add(ticker)
    for item in bottleneck_ref.get("consensus_heatmap", []):
        ticker = item.get("ticker", "").replace("$", "").strip().upper()
        stars = item.get("stars", 0)
        if stars >= 2:
            mtype = _classify_market(ticker)
            _add_candidate(ticker, item.get("layer", "").replace("_", " "), item.get("role", ""), "HIGH" if stars >= 3 else "MEDIUM", f"High consensus ({stars} stars) from {len(item.get('accounts',[]))} accounts — {item.get('role','')}", "bottleneck_consensus", mtype)
    for chain in supply_chains:
        for stage in chain.get("stages", []):
            for t in stage.get("tickers", []):
                _add_candidate(t, chain["name"], stage["layer"], "HIGH", f"Stage {stage['stage']} bottleneck: {stage['bottleneck']} — {chain['trigger']}", "supply_chain", _classify_market(t), {"target_px": None, "rationale": f"{chain['name']} chain stage {stage['stage']}", "timeframe": "6-12mo", "confidence": chain.get("confidence", 0.7)})
    for rw in news_analysis.get("rumor_watch", []):
        ticker = rw.get("ticker", ""); sig = rw.get("signal", "")
        if sig in ("STRONG_BULLISH_RUMOR", "NEWS_MOMENTUM_BUILDING", "BULLISH_CLUSTER", "RUMOR_WATCH"):
            mtype = _classify_market(ticker)
            _add_candidate(ticker, "News Momentum", "Front-run headline", "HIGH", f"News signal: {sig} — {rw.get('headline','')[:60]}", "news_rumor", mtype)
    quad_front_run_map = {
        "Q1": {"long": ["QQQ","XLK","NVDA","AAPL","MSFT","BTC-USD","ETH-USD"], "short": []},
        "Q2": {"long": ["XLF","XLE","XLI","KRE","IWM"], "short": ["TLT","IEF"]},
        "Q3": {"long": ["GLD","SLV","XLE","XLP","XLU","VST","CEG"], "short": ["QQQ","XLK","IWM"]},
        "Q4": {"long": ["TLT","IEF","GLD","XLU","XLP"], "short": ["QQQ","XLK","IWM","XLY"]},
    }
    pb = quad_front_run_map.get(quad, quad_front_run_map["Q3"])
    for t in pb.get("long", []):
        if t not in seen:
            _add_candidate(t, f"Quad {quad} Aligned", "Regime play", "MEDIUM", f"Structural regime {quad} favors long {t}", "regime_aligned", _classify_market(t))
    for t in pb.get("short", []):
        if t not in seen:
            _add_candidate(t, f"Quad {quad} Aligned", "Regime play", "MEDIUM", f"Structural regime {quad} favors short {t}", "regime_aligned", _classify_market(t))
    def sort_key(c):
        prio_map = {"TOP": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        proj_conf = c.get("projection", {}).get("confidence", 0)
        return (prio_map.get(c.get("priority", ""), 99), -proj_conf)
    candidates.sort(key=sort_key)
    return candidates

def _crypto_onchain_proxy_v2(prices: dict) -> dict:
    tokens = {}
    for ticker in list(CRYPTO.keys()):
        s = prices.get(ticker)
        if s is None or len(s) < 22:
            continue
        try:
            s_clean = pd.to_numeric(s, errors="coerce").dropna()
            if len(s_clean) < 22:
                continue
            with np.errstate(invalid='ignore', divide='ignore'):
                r1m = float(s_clean.iloc[-1] / s_clean.iloc[-22] - 1) if s_clean.iloc[-22] != 0 else 0
                r7d = float(s_clean.iloc[-1] / s_clean.iloc[-8] - 1) if len(s_clean) >= 8 and s_clean.iloc[-8] != 0 else r1m
                r5d = float(s_clean.iloc[-1] / s_clean.iloc[-6] - 1) if len(s_clean) >= 6 and s_clean.iloc[-6] != 0 else r1m
            vol = float(s_clean.tail(20).std())
            vol_40d = float(s_clean.tail(40).std()) if len(s_clean) >= 40 else vol
            vol_change = (vol / vol_40d - 1) if vol_40d > 0 else 0
            mean_20 = float(s_clean.tail(20).mean())
            mean_50 = float(s_clean.tail(50).mean()) if len(s_clean) >= 50 else mean_20
            momentum = (mean_20 / mean_50 - 1) if mean_50 > 0 else 0
            whale_signal = "NEUTRAL"
            if r7d > 0.05 and vol_change < 0.2:
                whale_signal = "ACCUMULATING"
            elif r7d < -0.05 and vol_change > 0.3:
                whale_signal = "DISTRIBUTING"
            funding_proxy = r1m * 0.001
            funding_extreme = abs(funding_proxy) > 0.0005
            vol_5 = float(s_clean.tail(5).std())
            oi_proxy = vol_5 / vol if vol > 0 else 1.0
            large_orders = oi_proxy > 2.0 and abs(r5d) < 0.02
            score = min(1.0, max(0.0, 0.5 + r1m * 5 + momentum * 2))
            tokens[ticker] = {
                "momentum_score": round(score, 3), "tvl_7d_change": round(r7d, 4), "tvl_30d_change": round(r1m, 4),
                "dex_vol_change": round(vol_change, 4), "price": round(float(s_clean.iloc[-1]), 2),
                "volatility_20d": round(vol / mean_20 if mean_20 > 0 else 0, 4), "trend_direction": "UP" if r1m > 0.05 else ("DOWN" if r1m < -0.05 else "SIDE"),
                "whale_signal": whale_signal, "funding_proxy": round(funding_proxy, 6), "funding_extreme": funding_extreme,
                "oi_proxy": round(oi_proxy, 2), "large_orders_detected": large_orders, "r5d": round(r5d, 4), "r7d": round(r7d, 4),
            }
        except Exception as e:
            logger.warning(f"Crypto proxy v2 failed for {ticker}: {e}")
    return tokens

def _ihsg_broker_proxy_v2(ticker, prices):
    s = prices.get(ticker)
    if s is None or (hasattr(s, "__len__") and len(s) < 30):
        return {"real_accumulation": False, "real_distribution": False, "crossing_detected": False, "cornering_supply": False, "confidence": 0, "signal": "NEUTRAL"}
    try:
        s_clean = pd.to_numeric(pd.Series(s), errors="coerce").dropna()
        if len(s_clean) < 30:
            return {"real_accumulation": False, "real_distribution": False, "crossing_detected": False, "cornering_supply": False, "confidence": 0, "signal": "NEUTRAL"}
        px = float(s_clean.iloc[-1])
        r5d = float(s_clean.iloc[-1] / s_clean.iloc[-6] - 1) if len(s_clean) >= 6 else 0
        r20d = float(s_clean.iloc[-1] / s_clean.iloc[-21] - 1) if len(s_clean) >= 21 else r5d
        vol_5 = float(s_clean.tail(5).std())
        vol_20 = float(s_clean.tail(20).std()) if len(s_clean) >= 20 else vol_5
        vol_60 = float(s_clean.tail(60).std()) if len(s_clean) >= 60 else vol_20
        mean_20 = float(s_clean.tail(20).mean())
        range_5 = float(s_clean.tail(5).max() - s_clean.tail(5).min())
        range_20 = float(s_clean.tail(20).max() - s_clean.tail(20).min()) if len(s_clean) >= 20 else range_5
        crossing = False
        if vol_20 > 0 and vol_5 / vol_20 > 1.5 and range_5 / max(range_20, 0.001) < 0.15:
            crossing = True
        cornering = False
        if vol_60 > 0 and vol_20 / vol_60 < 0.5 and r5d > 0.03:
            cornering = True
        real_acc = r5d > 0.03 and r20d > 0.05 and not crossing
        real_dist = r5d < -0.03 and r20d < -0.05 and not crossing
        conf = 0; signal = "NEUTRAL"
        if real_acc:
            conf = min(100, int(50 + abs(r5d)*500)); signal = "ACCUMULATION"
        elif real_dist:
            conf = min(100, int(50 + abs(r5d)*500)); signal = "DISTRIBUTION"
        elif crossing:
            conf = 70; signal = "CROSSING"
        elif cornering:
            conf = 65; signal = "CORNERING"
        return {"real_accumulation": real_acc, "real_distribution": real_dist, "crossing_detected": crossing, "cornering_supply": cornering, "confidence": conf, "signal": signal, "r5d": round(r5d, 4), "r20d": round(r20d, 4), "vol_ratio": round(vol_5/vol_20, 2) if vol_20 > 0 else 1.0, "range_ratio": round(range_5/max(range_20, 0.001), 2), "drying_up": round(vol_20/vol_60, 2) if vol_60 > 0 else 1.0}
    except Exception:
        return {"real_accumulation": False, "real_distribution": False, "crossing_detected": False, "cornering_supply": False, "confidence": 0, "signal": "NEUTRAL"}

def _risk_range_proxy(prices: dict) -> dict:
    asset_ranges = {}
    for ticker, s in prices.items():
        if s is None or len(s) < 60:
            continue
        try:
            s_clean = pd.to_numeric(s, errors="coerce").dropna()
            if len(s_clean) < 60:
                continue
            px = float(s_clean.iloc[-1])
            sma20 = float(s_clean.tail(20).mean())
            std20 = float(s_clean.tail(20).std())
            if std20 == 0 or not all(math.isfinite(v) for v in [px, sma20, std20]):
                continue
            lrr = round(sma20 - 1.5 * std20, 4)
            trr = round(sma20 + 1.5 * std20, 4)
            comp = "bullish" if px < lrr else "bearish" if px > trr else "neutral"
            quality = "A" if abs(px - lrr) / max(lrr, 0.001) < 0.02 else "B" if comp != "neutral" else "C"
            asset_ranges[ticker] = {"px": px, "trade": {"lrr": lrr, "trr": trr}, "composite": comp, "quality": quality, "market": _classify_market(ticker)}
        except Exception:
            pass
    return {"asset_ranges": asset_ranges}

def _classify_market(ticker: str) -> str:
    if ticker in FOREX_PAIRS or "=" in ticker or ticker in ["DX-Y.NYB", "UUP"]:
        return "forex"
    if ticker in COMMODITIES or ticker in ["GC=F", "SI=F", "CL=F", "HG=F"]:
        return "commodity"
    if ticker in CRYPTO or ticker in ["BTC-USD", "ETH-USD", "SOL-USD"]:
        return "crypto"
    if ticker in IHSG_UNIVERSE or ticker.endswith(".JK"):
        return "ihsg"
    return "us_equity"

def _options_proxy_for_ticker(ticker, prices):
    ticker = ticker.replace("$", "").strip().upper()
    s = prices.get(ticker)
    if s is None or (hasattr(s, "__len__") and len(s) < 20):
        aliases = []
        if "." in ticker and not ticker.endswith(".JK"):
            aliases.append(ticker.replace(".", "-"))
        if "-" in ticker:
            aliases.append(ticker.replace("-", "."))
        if ticker.endswith(".KS"):
            aliases.append(ticker.replace(".KS", ".KQ"))
        for a in aliases:
            s = prices.get(a)
            if s is not None and hasattr(s, "__len__") and len(s) >= 20:
                ticker = a; break
        if s is None or (hasattr(s, "__len__") and len(s) < 20):
            return {"ok": False, "ticker": ticker, "error": "No price data"}
    try:
        s_clean = pd.to_numeric(s, errors="coerce").dropna()
        if len(s_clean) < 20:
            return {"ok": False}
        px = float(s_clean.iloc[-1])
        sma20 = float(s_clean.tail(20).mean())
        std20 = float(s_clean.tail(20).std())
        if std20 == 0 or not all(math.isfinite(v) for v in [px, sma20, std20]):
            return {"ok": False}
        max_pain = round(sma20, 2)
        put_wall = round(sma20 - std20 * 2.0, 2)
        call_wall = round(sma20 + std20 * 2.0, 2)
        gamma_flip_up = round(sma20 + std20 * 1.5, 2)
        gamma_flip_down = round(sma20 - std20 * 1.5, 2)
        mp_dist = (px - max_pain) / max_pain if max_pain != 0 else 0
        r5d = float(s_clean.iloc[-1] / s_clean.iloc[-6] - 1) if len(s_clean) >= 6 else 0
        r20d = float(s_clean.iloc[-1] / s_clean.iloc[-21] - 1) if len(s_clean) >= 21 else 0
        if r5d > 0.03 and r20d > 0.05:
            gamma_regime = "DEEP_POSITIVE"
        elif r5d > 0.01 and r20d > 0.02:
            gamma_regime = "POSITIVE"
        elif r5d < -0.03 and r20d < -0.05:
            gamma_regime = "DEEP_NEGATIVE"
        elif r5d < -0.01 and r20d < -0.02:
            gamma_regime = "NEGATIVE"
        else:
            gamma_regime = "TRANSITION"
        if r20d > 0.05:
            greek = "BULLISH"
        elif r20d < -0.05:
            greek = "BEARISH"
        else:
            greek = "NEUTRAL"
        near_max_pain = abs(mp_dist) < 0.03
        if near_max_pain and gamma_regime in ("DEEP_POSITIVE", "POSITIVE") and greek == "BULLISH":
            conviction = "STRONG"
        elif gamma_regime in ("DEEP_POSITIVE", "POSITIVE", "TRANSITION") and greek == "BULLISH":
            conviction = "MODERATE"
        elif gamma_regime in ("NEGATIVE", "DEEP_NEGATIVE") and greek == "BEARISH":
            conviction = "MODERATE"
        elif near_max_pain:
            conviction = "WEAK"
        else:
            conviction = "CONFLICTED"
        return {"ok": True, "price": px, "max_pain": max_pain, "put_wall": put_wall, "call_wall": call_wall, "gamma_flip_up": gamma_flip_up, "gamma_flip_down": gamma_flip_down, "max_pain_dist": round(mp_dist, 4), "gamma_regime": gamma_regime, "greek_composite": greek, "conviction": conviction, "r5d": round(r5d, 4), "r20d": round(r20d, 4), "source": "PROXY"}
    except Exception as e:
        logger.debug(f"Options proxy failed for {ticker}: {e}")
        return {"ok": False}

def _find_catalyst(ticker, bottleneck_ref):
    for ev in bottleneck_ref.get("catalyst_timeline", []):
        if ticker in ev.get("ticker", ""):
            return {"quarter": ev.get("quarter", ""), "event": ev.get("event", ""), "priority": ev.get("priority", "")}
    return {}

def _fred_fallback() -> Dict[str, pd.Series]:
    import numpy as np
    dates = pd.date_range(end=datetime.now(), periods=60, freq="MS")
    return {
        "INDPRO": pd.Series(np.linspace(100, 105, 60) + np.random.randn(60)*0.5, index=dates, name="INDPRO"),
        "CPI": pd.Series(np.linspace(300, 310, 60) + np.random.randn(60)*1, index=dates, name="CPI"),
        "UNRATE": pd.Series(np.linspace(3.5, 4.2, 60) + np.random.randn(60)*0.1, index=dates, name="UNRATE"),
        "DGS10": pd.Series(np.linspace(4.0, 4.5, 60) + np.random.randn(60)*0.1, index=dates, name="DGS10"),
        "DGS2": pd.Series(np.linspace(3.5, 4.0, 60) + np.random.randn(60)*0.1, index=dates, name="DGS2"),
        "FEDFUNDS": pd.Series([5.33]*60, index=dates, name="FEDFUNDS"),
        "PAYEMS": pd.Series(np.linspace(155000, 158000, 60), index=dates, name="PAYEMS"),
        "RSAFS": pd.Series(np.linspace(680, 720, 60), index=dates, name="RSAFS"),
        "ICSA": pd.Series(np.linspace(220, 240, 60), index=dates, name="ICSA"),
        "CORECPI": pd.Series(np.linspace(280, 290, 60), index=dates, name="CORECPI"),
        "DFII10": pd.Series(np.linspace(1.5, 2.0, 60), index=dates, name="DFII10"),
        "T5YIE": pd.Series(np.linspace(2.2, 2.5, 60), index=dates, name="T5YIE"),
        "HYOAS": pd.Series(np.linspace(3.5, 4.5, 60), index=dates, name="HYOAS"),
        "ISMNO": pd.Series(np.linspace(48, 52, 60), index=dates, name="ISMNO"),
        "HOUST": pd.Series(np.linspace(1300, 1400, 60), index=dates, name="HOUST"),
        "DGS3MO": pd.Series(np.linspace(4.2, 4.8, 60), index=dates, name="DGS3MO"),
        "BAMLH0A0HYM2": pd.Series(np.linspace(3.0, 3.5, 60), index=dates, name="BAMLH0A0HYM2"),
    }

def _global_fallback(quad: str) -> dict:
    base_map = {
        "Q1": ["USA","Japan","India","Taiwan","South Korea","Vietnam","Mexico","Singapore","Philippines","Malaysia","UAE","Israel","Poland","Czech Republic","Romania"],
        "Q2": ["China","Brazil","Australia","Canada","South Africa","Saudi Arabia","Chile","Peru","Thailand","Colombia","New Zealand","Norway","Kazakhstan","Angola"],
        "Q3": ["UK","Germany","France","Italy","Russia","Turkey","Argentina","Nigeria","Pakistan","Egypt","Spain","Netherlands","Belgium","Sweden","Switzerland"],
        "Q4": ["Indonesia","Venezuela","Iran","Ukraine","Greece","Portugal","Lebanon","Syria","Yemen","Zimbabwe","Sudan","Afghanistan","North Korea","Myanmar","Belarus","Bolivia"],
    }
    for country_override, override_q in HEDGEYE_COUNTRY_OVERRIDE.items():
        for q in base_map:
            if country_override in base_map[q]:
                base_map[q].remove(country_override)
            if country_override not in base_map[override_q]:
                base_map[override_q].insert(0, country_override)
    cqs = {}
    for q, countries in base_map.items():
        for c in countries:
            cqs[c] = q
    return {
        "global_quad": quad, "global_conf": 0.52,
        "global_probs": {"Q1":0.20,"Q2":0.25,"Q3":0.35,"Q4":0.20},
        "country_quads": cqs,
        "country_list": [{"country": c, "quad": q, "regime_name": {"Q1":"Goldilocks","Q2":"Reflation","Q3":"Stagflation","Q4":"Deflation"}.get(q,q)} for q, countries in base_map.items() for c in countries],
        "em_recovery": {"trigger": f"Q3 defensive - watch for {quad} rotation", "confidence": 0.4},
        "dm_count": len(base_map.get("Q1",[])) + len(base_map.get("Q3",[])),
        "em_count": len(base_map.get("Q2",[])) + len(base_map.get("Q4",[])),
    }

def _extract_bottleneck_tickers() -> List[str]:
    ref = _load_bottleneck_ref()
    tickers = set()
    for item in ref.get("consensus_heatmap", []):
        t = item.get("ticker", "")
        if t:
            tickers.add(t.replace("$", "").strip().upper())
    for phase in ref.get("institutional_rotation", []):
        for t in phase.get("tickers", []):
            if t:
                tickers.add(t.replace("$", "").strip().upper())
    for ma in ref.get("ma_watchlist", []):
        t = ma.get("target", "")
        if t:
            tickers.add(t.replace("$", "").strip().upper())
    for ev in ref.get("catalyst_timeline", []):
        t = ev.get("ticker", "")
        if t:
            tickers.add(t.replace("$", "").strip().upper())
    clean = []
    for t in tickers:
        if not t or len(t) > 20 or t.startswith("http") or " " in t:
            continue
        clean.append(t)
    return clean

def _all_tickers() -> List[str]:
    try:
        from engines.alpha_center_curator import ALPHA_CENTER_CANDIDATES
        alpha_tickers = list(ALPHA_CENTER_CANDIDATES.keys())
    except Exception:
        alpha_tickers = []
    pools = [
        list(US_SECTORS.keys()), list(US_FACTORS.keys()),
        list(FOREX_PAIRS.keys()), list(COMMODITIES.keys()),
        list(CRYPTO.keys()), list(BONDS.keys()),
        list(IHSG_UNIVERSE.keys()), list(MACRO_PROXIES.keys()),
        ["^VIX", "UUP", "EEM", "VWO", "^GSPC", "^IXIC", "^VVIX"],
        alpha_tickers,
        _extract_bottleneck_tickers(),
    ]
    seen = set(); out = []
    for p in pools:
        for t in p:
            if t and t not in seen:
                seen.add(t); out.append(t)
    return out

def _fetch_stablecoin_flows():
    if not _has_requests:
        return {}
    try:
        r = requests.get("https://stablecoins.llama.fi/stablecoins", timeout=15)
        if r.status_code != 200:
            return {}
        data = r.json()
        total = 0.0; change_7d = 0.0
        pegged_assets = data.get("peggedAssets", []) if isinstance(data, dict) else []
        for pe in pegged_assets:
            if not isinstance(pe, dict):
                continue
            circ = pe.get("circulating", {})
            if isinstance(circ, dict):
                mc = circ.get("peggedUSD", 0) or 0
                total += float(mc)
                prev = pe.get("circulatingPrevWeek", {})
                if isinstance(prev, dict):
                    prev_mc = prev.get("peggedUSD", 0) or 0
                    change_7d += (float(mc) - float(prev_mc))
        return {"total_b": round(total / 1e9, 2), "change_7d_b": round(change_7d / 1e9, 2), "source": "DeFiLlama"}
    except Exception as e:
        logger.warning(f"Stablecoin fetch failed: {e}")
        return {}

def _fetch_crypto_narrative():
    if not _has_requests:
        return {}
    out = {"trending": [], "categories": [], "fear_greed": None}
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
        if r.status_code == 200:
            fg = r.json().get("data", [{}])[0]
            out["fear_greed"] = {"value": int(fg.get("value", 50)), "label": fg.get("value_text", "Neutral")}
    except Exception as e:
        logger.warning(f"Fear&Greed failed: {e}")
    try:
        r = requests.get("https://api.coingecko.com/api/v3/search/trending", timeout=10)
        if r.status_code == 200:
            coins = r.json().get("coins", [])
            out["trending"] = [{"name": c.get("item", {}).get("name"), "symbol": c.get("item", {}).get("symbol"), "market_cap_rank": c.get("item", {}).get("market_cap_rank"), "score": c.get("item", {}).get("score")} for c in coins[:7]]
    except Exception as e:
        logger.warning(f"Trending failed: {e}")
    try:
        r = requests.get("https://api.coingecko.com/api/v3/coins/categories", timeout=15)
        if r.status_code == 200:
            cats = r.json()
            out["categories"] = [{"name": c.get("name"), "market_cap": c.get("market_cap"), "volume_24h": c.get("volume_24h"), "top_3_coins": [x for x in c.get("top_3_coins", [])[:3]]} for c in sorted(cats, key=lambda x: x.get("volume_24h", 0) or 0, reverse=True)[:10]]
    except Exception as e:
        logger.warning(f"Categories failed: {e}")
    return out

def _fetch_crypto_market_structure():
    if not _has_requests:
        return {}
    out = {"funding": {}, "oi": {}, "liquidation": {}, "long_short": {}}
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT"]
    try:
        for sym in symbols:
            try:
                r = requests.get(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={sym}&limit=1", timeout=8)
                if r.status_code == 200:
                    d = r.json()
                    if d:
                        out["funding"][sym.replace("USDT", "")] = {"rate": float(d[0].get("fundingRate", 0)), "time": d[0].get("fundingTime", "")}
            except Exception:
                pass
        r = requests.get("https://fapi.binance.com/fapi/v1/ticker/24hr", timeout=10)
        if r.status_code == 200:
            tickers = {t.get("symbol"): t for t in r.json()}
            for sym in symbols:
                t = tickers.get(sym, {})
                if t:
                    out["oi"][sym.replace("USDT", "")] = {"volume_24h": float(t.get("volume", 0)), "price_change": float(t.get("priceChangePercent", 0)), "weighted_avg_price": float(t.get("weightedAvgPrice", 0))}
    except Exception as e:
        logger.warning(f"Market structure failed: {e}")
    return out

def _build_crypto_unlock_proxy():
    return [
        {"token": "SOL", "date": "2026-06-01", "amount_m": 20, "type": "Cliff", "impact": "HIGH"},
        {"token": "AVAX", "date": "2026-05-20", "amount_m": 5, "type": "Linear", "impact": "MEDIUM"},
        {"token": "ARB", "date": "2026-05-25", "amount_m": 100, "type": "Cliff", "impact": "HIGH"},
        {"token": "OP", "date": "2026-06-15", "amount_m": 30, "type": "Linear", "impact": "MEDIUM"},
    ]

def _build_crypto_center(prices, news_analysis):
    cc = {"macro_regime": {}, "capital_flows": {}, "market_structure": {}, "narrative": {}, "tokenomics": {}, "whale": {}, "risk_flags": []}
    btc_s = prices.get("BTC-USD"); eth_s = prices.get("ETH-USD")
    if btc_s is not None and eth_s is not None:
        try:
            btc_mcap = float(btc_s.iloc[-1]) * 19.8e6
            eth_mcap = float(eth_s.iloc[-1]) * 120e6
            total = btc_mcap + eth_mcap + 800e9
            btc_d = btc_mcap / total
            cc["macro_regime"]["btc_dominance_proxy"] = round(btc_d, 3)
        except Exception:
            cc["macro_regime"]["btc_dominance_proxy"] = 0.55
    else:
        cc["macro_regime"]["btc_dominance_proxy"] = 0.55
    cc["capital_flows"] = _fetch_stablecoin_flows()
    cc["narrative"] = _fetch_crypto_narrative()
    cc["market_structure"] = _fetch_crypto_market_structure()
    whale_proxy = {}
    for ticker in ["BTC-USD", "ETH-USD", "SOL-USD"]:
        s = prices.get(ticker)
        if s is not None and len(s) >= 22:
            try:
                s_clean = pd.to_numeric(s, errors="coerce").dropna()
                r1m = float(s_clean.iloc[-1] / s_clean.iloc[-22] - 1)
                r7d = float(s_clean.iloc[-1] / s_clean.iloc[-8] - 1) if len(s_clean) >= 8 else r1m
                vol = float(s_clean.tail(20).std())
                vol_40 = float(s_clean.tail(40).std()) if len(s_clean) >= 40 else vol
                signal = "NEUTRAL"
                if r7d > 0.05 and (vol / vol_40 if vol_40 > 0 else 1) < 1.2:
                    signal = "ACCUMULATING"
                elif r7d < -0.05 and (vol / vol_40 if vol_40 > 0 else 1) > 1.3:
                    signal = "DISTRIBUTING"
                whale_proxy[ticker] = {"signal": signal, "r1m": round(r1m, 4), "r7d": round(r7d, 4), "vol_expansion": round(vol / vol_40 - 1, 2) if vol_40 > 0 else 0}
            except Exception:
                pass
    cc["whale"]["proxy"] = whale_proxy
    cc["tokenomics"]["upcoming_unlocks"] = _build_crypto_unlock_proxy()
    funding = cc["market_structure"].get("funding", {})
    if funding:
        for sym, data in funding.items():
            rate = data.get("rate", 0)
            if abs(rate) > 0.0005:
                cc["risk_flags"].append({"type": "FUNDING_EXTREME", "ticker": sym, "value": rate, "impact": "Longs overleveraged — correction risk" if rate > 0.001 else "Short squeeze potential" if rate < -0.001 else "Elevated funding"})
    return cc

# ═══════════════════════════════════════════════════════════════════════
# V40 EXTERNAL DATA FETCHER — wires options/COT/OI/on-chain/CME/FINRA
# ═══════════════════════════════════════════════════════════════════════
def _v40_fetch_external_data(snap, prices, current_quad, cb=None):
    def _cb(m, p):
        try:
            if cb: cb(m, p)
        except Exception: pass
    out = {"options_data": {}, "cot_data": {}, "cme_oi": {}, "onchain_data": {}, "finra_short": {}}
    price_tickers = list(prices.keys()) if prices else []
    us_tickers = [t for t in price_tickers if not any(s in t.upper() for s in [".JK", "=X", "=F", "-USD", "^"])]
    crypto_tickers = [t for t in price_tickers if "-USD" in t.upper() and not t.startswith("DX")]
    fx_comm_tickers = [t for t in price_tickers if "=X" in t.upper() or "=F" in t.upper() or t in ("DX-Y.NYB", "UUP", "USO", "GLD", "SLV", "UNG", "CPER", "CORN", "WEAT")]

    _cb("v40: Fetching options (yfinance)...", 95)
    try:
        from engines.live_data_engine import fetch_options_yf
        _commodity_etfs = ["USO", "GLD", "SLV", "UNG", "CPER", "UGA", "CORN", "WEAT", "SOYB"]
        _fx_etfs = ["UUP", "FXE", "FXY", "FXB", "FXA", "FXC"]
        _alpha_tickers = []
        try:
            from engines.alpha_center_curator import ALPHA_CENTER_CANDIDATES
            _alpha_tickers = [t for t in ALPHA_CENTER_CANDIDATES.keys() if t in price_tickers and "." not in t and "=" not in t]
        except Exception: pass
        opt_targets = (us_tickers[:25] + [t for t in ("SPY", "QQQ", "IBIT", "TLT", "IWM") if t in price_tickers] + _commodity_etfs + _fx_etfs + _alpha_tickers)
        opt_targets = list(dict.fromkeys(opt_targets))
        out["options_data"] = fetch_options_yf(opt_targets, max_tickers=70)
    except Exception as e:
        logger.warning(f"v40: yfinance options failed: {e}")

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

    _cb("v40: Fetching on-chain (DeFiLlama)...", 97)
    try:
        from engines.live_data_engine import fetch_onchain_defillama
        chain_map = {}
        name_map = {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana", "AVAX-USD": "Avalanche", "MATIC-USD": "Polygon", "ARB-USD": "Arbitrum", "OP-USD": "OP Mainnet", "BNB-USD": "BSC"}
        for t in crypto_tickers:
            if t in name_map:
                chain_map[t] = name_map[t]
        if chain_map:
            out["onchain_data"] = fetch_onchain_defillama(chain_map)
    except Exception as e:
        logger.warning(f"v40: DeFiLlama failed: {e}")

    _cb("v40: Fetching COT (CFTC)...", 98)
    try:
        from engines.live_data_engine import fetch_cot_by_ticker
        out["cot_data"] = fetch_cot_by_ticker(fx_comm_tickers)
    except Exception as e:
        logger.warning(f"v40: COT failed: {e}")

    _cb("v40: Fetching FINRA dark-pool (off-exchange short vol)...", 98)
    try:
        from engines.live_data_engine import fetch_finra_short_volume, attach_finra_signal
        finra = fetch_finra_short_volume(us_tickers, lookback_days=5)
        out["finra_short"] = attach_finra_signal(finra, prices)
    except Exception as e:
        logger.debug(f"v40: FINRA short-vol failed: {e}")

    try:
        from engines.live_data_engine import fetch_flashalpha_gex
        fa = fetch_flashalpha_gex(us_tickers, max_calls=5)
        if fa:
            out.setdefault("options_data", {})
            for t, g in fa.items():
                out["options_data"][t] = {**(out["options_data"].get(t, {})), **g}
            logger.info(f"v40: FlashAlpha real GEX merged for {len(fa)} tickers")
    except Exception as e:
        logger.debug(f"v40: FlashAlpha failed: {e}")

    try:
        from engines.cme_scraper import get_cme_volume
        cme_map = {"CL=F": "CL", "GC=F": "GC", "SI=F": "SI", "NG=F": "NG", "HG=F": "HG"}
        for tkr, prod in cme_map.items():
            if tkr in price_tickers:
                try:
                    vol = get_cme_volume(prod)
                    if vol: out["cme_oi"][tkr] = vol
                except Exception:
                    continue
    except Exception as e:
        logger.debug(f"v40: CME OI: {e}")

    try:
        from engines.live_data_engine import load_scraped_data
        scraped = load_scraped_data()
        if scraped:
            for tkr, sdata in scraped.items():
                if not isinstance(sdata, dict):
                    continue
                existing = out["options_data"].get(tkr, {})
                merged = {**existing}
                for k, v in sdata.items():
                    if v is not None:
                        merged[k] = v
                merged["source"] = sdata.get("source", merged.get("source", "scraped"))
                out["options_data"][tkr] = merged
            logger.info(f"v40: merged scraped data for {len(scraped)} tickers")
    except Exception as e:
        logger.debug(f"v40: scraped merge skipped: {e}")

    try:
        from engines.gex_engine import analyze_gex
        try:
            from engines.greeks_proxy import GreeksProxy
            _gp = GreeksProxy()
        except Exception:
            _gp = None
        vix_now = snap.get("vix", 20.0) or 20.0
        cover = list(us_tickers)
        try:
            from engines.alpha_center_curator import ALPHA_CENTER_CANDIDATES
            cover += [t for t in ALPHA_CENTER_CANDIDATES.keys() if t in price_tickers]
        except Exception:
            pass
        cover += [t for t in price_tickers if any(s in t.upper() for s in ["-USD", "=F", "=X"])]
        cover = [t for t in dict.fromkeys(cover) if t in price_tickers][:150]
        n_proxy = 0
        for t in cover:
            existing = out["options_data"].get(t, {})
            if existing.get("net_gex") is not None or existing.get("call_wall") is not None:
                continue
            try:
                gx = analyze_gex(t, prices, vix=vix_now)
                if not gx or not gx.get("ok", True):
                    continue
                merged = dict(existing)
                if gx.get("net_gex") is not None: merged["net_gex"] = gx["net_gex"]
                if gx.get("flip_level"): merged["gamma_flip"] = gx["flip_level"]
                if gx.get("call_wall"): merged["call_wall"] = gx["call_wall"]
                if gx.get("put_wall"): merged["put_wall"] = gx["put_wall"]
                if _gp is not None:
                    try:
                        g = _gp.analyze(t, prices, vix=vix_now)
                        if g.get("ok"):
                            if g.get("max_pain"): merged.setdefault("max_pain", g["max_pain"])
                            merged["greeks_proxy"] = {"gamma": g.get("gamma"), "vanna": g.get("vanna"), "charm": g.get("charm"), "composite": g.get("composite")}
                    except Exception:
                        pass
                merged["source"] = "proxy"
                out["options_data"][t] = merged
                n_proxy += 1
            except Exception:
                continue
        if n_proxy:
            logger.info(f"v40: greeks/GEX proxy filled {n_proxy} tickers (price-derived fallback)")
    except Exception as e:
        logger.debug(f"v40: proxy fallback skipped: {e}")

    logger.info(f"v40: external data — options:{len(out['options_data'])} cot:{len(out['cot_data'])} cme:{len(out['cme_oi'])} onchain:{len(out['onchain_data'])} finra:{len(out['finra_short'])}")
    return out

# ═══════════════════════════════════════════════════════════════════════
# MAIN V40 SNAPSHOT BUILDER
# ═══════════════════════════════════════════════════════════════════════
def build_snapshot_v40(
    portfolio_value: float = 100000,
    quad_override: str = None,
    progress_cb=None,
    **kwargs,
) -> dict:
    def _cb(msg, pct):
        try:
            if progress_cb:
                progress_cb(msg, pct)
        except Exception:
            pass

    _cb("v40.5: Initializing...", 0)
    snap = {
        "ok": False, "errors": [], "_source": "live", "_generated_at": datetime.now().isoformat(),
        "gip": None, "global": {}, "risk_ranges": {}, "health": {}, "prices": {}, "fred_coverage": 0,
        "build_time_s": 0,
        # v40.5 wired outputs
        "alpha_center": {}, "composite_signals": {}, "bonds_xau_regime": {},
        "supply_chain_analysis": {}, "thought_process": {}, "top_theses": [],
        "front_run_candidates": [], "auto_discoveries": {}, "crypto_tokens": {},
        "crypto_center": {}, "behavioral_macro": {}, "odte_monitor": {}, "skew_term": {},
        "reflexivity": {}, "boom_bust": {}, "conviction_sizing": {}, "vanna_charm_flows": {},
        "interconnect": {}, "yfinance_options": {}, "scenario_discovery": {},
        "transmission": {}, "regime_transition": {}, "news_nlp_v3": {}, "bottleneck_v3": {},
        "gex_data": {}, "charm_data": {}, "vanna_data": {}, "odte_enhanced": {},
        "structure_data": {}, "afternoon_data": {}, "volga_data": {}, "institutional_data": {},
        "gamma_data": {}, "greeks_data": {}, "cot_oi": {}, "dxy_correlation": {},
        "vol_forecast": {}, "stress_test": [], "leveraged_etf": {}, "daily_signals": [],
        "daily_signals_summary": {}, "regime_forecast": {}, "forward_returns": {},
        "leading_signals": {}, "price_clusters": {}, "news_narratives": {},
        "bottleneck_discovery": {}, "frontrun": {}, "ihsg_sector_momentum": {},
        "ihsg_commodity_overlay": {}, "ihsg_rupiah_regime": {}, "ihsg_foreign_flow": {},
        "ihsg_macro_overlay": {}, "ihsg_broker_proxy": {}, "rumor_watch": [],
        "bottleneck_research": {}, "country_list": [], "cascade_analysis": {},
        "yves_v2": {}, "discovery_brain": {}, "ticker_universe_expansion": {},
        "portfolio_sizing_v2": {}, "cem_karsan_universal": {}, "markov_v3": {},
        "smart_money": {}, "capital_rotation": {}, "ust_auction": {}, "vrp_scanner": {},
        "squeeze_scanner": {}, "karsan_scanner": {}, "spotgamma_scanner": {},
        "leopold_scan": {}, "coatue_scan": {}, "volsignals_regime": {},
        "spotgamma_levels": {}, "schadner_iv": {}, "narrative": {},
        "simulation_results": {}, "simulation_summary": {}, "portfolio_stress": {},
        "options_pnl_simulator": {}, "idhl_data": {}, "rc_data": {}, "afs_data": {},
        "walkforward_results": {}, "fractional_kelly": {}, "bayesian_fusion": {},
        "duration_hmm": {}, "cri_v2_data": {},
        # v40.5 NEW top-level wired keys
        "options_data": {}, "cot_data": {}, "finra_short": {}, "onchain_data": {}, "cme_oi": {},
        "chain_reactions": {}, "entry_decisions": {}, "methodology_scores": {},
        "movement_regimes": {}, "daily_plays": {}, "ihsg_specialist": {},
        "keith_sync": {}, "keith_summary": {}, "hedgeye_position_sizing": {},
        "alpha_gatekeeper": {}, "alpha_synthesis": {}, "vix_bucket": {},
        "tier1alpha": {}, "scenarios": {}, "market_health": {}, "risk_range": {},
        "sizing": {}, "transmissions": {}, "chain_reactions_catalog": {},
        "walkforward_results_v40": {}, "current_quad": "Q3", "v40": True,
    }

    t0 = time.time()

    # ── FRED ──
    _cb("Fetching FRED macro data...", 5)
    try:
        fred_bundle = load_fred_bundle(force_refresh=True)
    except Exception as e:
        logger.error(f"FRED bundle failed: {e}"); snap["errors"].append(f"fred: {e}")
        fred_bundle = {"series": {}, "meta": {"loaded": 0, "requested": 0}}
    fred = fred_bundle.get("series", {}); fred_meta = fred_bundle.get("meta", {})
    if fred_meta.get("loaded", 0) == 0:
        logger.warning("FRED returned 0 series - using synthetic fallback")
        fred = _fred_fallback(); fred_meta = {"loaded": 15, "requested": 15, "missing": 0, "source": "synthetic_fallback"}
        snap["errors"].append("fred: using synthetic fallback")
    snap["fred_meta"] = fred_meta; snap["fred_series"] = fred; snap["fred_coverage"] = fred_meta.get("loaded", 0)

    # ── Prices ──
    tickers = _all_tickers()
    logger.info(f"Price universe: {len(tickers)} tickers")
    _cb(f"Fetching {len(tickers)} tickers from Yahoo Finance...", 10)
    if load_prices is None:
        raise RuntimeError("load_prices not available")
    prices = {}
    for attempt in range(3):
        try:
            prices = load_prices(tickers, days=756, max_age_hours=12.0, progress_cb=progress_cb)
            if prices and len(prices) > len(tickers) * 0.7:
                break
            logger.warning(f"Price load attempt {attempt+1}/3: only {len(prices)}/{len(tickers)} loaded")
        except Exception as e:
            logger.warning(f"Price load attempt {attempt+1}/3 failed: {e}"); snap["errors"].append(f"prices attempt {attempt+1}: {e}")
            if "Rate limit" in str(e) or "429" in str(e):
                break
            if attempt < 2:
                time.sleep(2 ** attempt + 3)
    if not prices:
        raise RuntimeError("No price data loaded")
    snap["prices"] = prices; snap["prices_loaded"] = len(prices); snap["price_meta"] = {"requested": len(tickers), "loaded": len(prices)}

    # ── News ──
    _cb("Scanning news & rumors...", 18)
    news_headlines = _fetch_news_headlines(list(prices.keys())[:100])
    news_analysis = _analyze_news(news_headlines, prices)
    snap["news_narratives"] = news_analysis; snap["rumor_watch"] = news_analysis.get("rumor_watch", [])

    # ── Bottleneck ref ──
    _cb("Loading bottleneck intelligence...", 20)
    bottleneck_ref = _load_bottleneck_ref()
    snap["bottleneck_research"] = bottleneck_ref

    # ── Supply chain chains (legacy) + merge target ──
    _cb("Building supply chain bottleneck chains...", 22)
    supply_chains = _build_supply_chain_chains(bottleneck_ref, None, prices)
    snap["supply_chain_chains"] = supply_chains

    # ── Front-Run ALL Markets ──
    _cb("Generating front-run candidates (all markets)...", 24)
    front_run = _generate_front_run_all_markets(prices, news_analysis, bottleneck_ref, supply_chains, "Q3")
    snap["front_run_candidates"] = front_run

    # ── Auto-Ticker Discovery ──
    _cb("Auto-discovering new tickers...", 26)
    current_tickers = set(prices.keys())
    discovered = _auto_discover_tickers(bottleneck_ref, None, news_analysis, None, current_tickers)
    snap["auto_discoveries"] = {"discovered_tickers": discovered, "count": len(discovered)}
    if discovered:
        logger.info(f"Auto-discovered {len(discovered)} new tickers: {discovered[:10]}")

    # ── Crypto Center ──
    _cb("Building crypto on-chain center...", 28)
    cc = _build_crypto_center(prices, news_analysis)
    snap["crypto_center"] = cc; snap["crypto_tokens"] = _crypto_onchain_proxy_v2(prices)

    # ── IHSG Layers ──
    ihsg_layers = _ihsg_layers(prices, "Q3")
    for k, v in ihsg_layers.items():
        snap[k] = v
    ihsg_broker = {}
    for ticker in list(IHSG_UNIVERSE.keys())[:30]:
        bp = _ihsg_broker_proxy_v2(ticker, prices)
        if bp and bp.get("signal") != "NEUTRAL":
            ihsg_broker[ticker] = bp
    snap["ihsg_broker_proxy"] = ihsg_broker

    # ── VIX ──
    vix_last = 20.0
    vix_s = prices.get("^VIX")
    if vix_s is not None and not vix_s.empty:
        try: vix_last = float(vix_s.iloc[-1])
        except Exception: pass
    snap["vix"] = vix_last

    # ── VIX Bucket ──
    try:
        snap["vix_bucket"] = classify_vix_bucket(vix_last)
    except Exception as e:
        logger.warning(f"VIX bucket failed: {e}")
        snap["vix_bucket"] = {"bucket": "NORMAL", "label": "Investable", "multiplier": 1.0}

    # ── DXY ──
    dxy_s = prices.get("DX-Y.NYB"); dxy_ret = 0.0
    if dxy_s is not None and len(dxy_s) > 22:
        try: dxy_ret = float(dxy_s.iloc[-1] / dxy_s.iloc[-22] - 1)
        except Exception: pass
    snap["dxy"] = dxy_s; snap["dxy_ret"] = dxy_ret

    # ── GIP Engine ──
    _cb("Running GIP regime model...", 55)
    if GIPEngine is None or GIPResult is None:
        raise RuntimeError("GIP engine not available")
    try:
        gip_engine = GIPEngine()
        gip = gip_engine.run(fred, prices)
    except Exception as e:
        logger.error(f"GIP engine failed: {e}"); snap["errors"].append(f"gip: {e}"); raise
    snap["gip"] = gip
    quad = getattr(gip, "structural_quad", "Q3")
    monthly_quad = getattr(gip, "monthly_quad", "Q2")
    gip_features = getattr(gip, "features", {})
    if quad_override and quad_override != "Auto":
        quad = quad_override
    snap["current_quad"] = quad

    # ── Global Regime ──
    snap["global"] = _global_fallback(quad); snap["country_list"] = snap["global"].get("country_list", [])

    # ── Market Health ──
    _cb("Running market health & breadth...", 65)
    if MarketHealthEngine is not None:
        try:
            mkt = MarketHealthEngine().run(prices, gip_features, quad)
            snap["health"] = mkt; snap["market_health"] = mkt
        except Exception as e:
            logger.warning(f"MarketHealthEngine failed: {e}"); snap["errors"].append(f"market_health: {e}")
            snap["health"] = {"error": str(e), "verdict": "Unknown"}; snap["market_health"] = snap["health"]
    else:
        snap["health"] = {"error": "Engine not imported", "verdict": "Unknown"}; snap["market_health"] = snap["health"]

    # ── Risk Ranges v20.3b (v40 OVERWRITE — skip legacy proxy entirely) ──
    _cb("Computing TRR/LRR v20.3b with auto-tune...", 30)
    try:
        from engines.risk_range_v20 import calculate_for_universe
        iv_dict = {"^VIX": vix_last}
        for iv_sym in ["^VXN", "^RVX", "^OVX", "^GVZ", "^CVIX"]:
            if iv_sym in prices:
                try: iv_dict[iv_sym] = float(prices[iv_sym].iloc[-1])
                except Exception: pass
        rr_v40 = calculate_for_universe(prices, current_quad=quad, iv_dict=iv_dict)
        snap["risk_range"] = rr_v40; snap["risk_ranges"] = rr_v40
        snap["risk_range_version"] = "v20.3b"
        logger.info(f"v40: TRR/LRR computed for {rr_v40.get('summary', {}).get('total', 0)} tickers")
    except Exception as e:
        logger.error(f"v40: TRR/LRR failed: {e}")
        snap["risk_range"] = {"asset_ranges": {}, "error": str(e)}; snap["risk_ranges"] = snap["risk_range"]

    # ── Chain Reactions v2 ──
    _cb("Computing chain reactions...", 50)
    try:
        from engines.chain_reaction_v2 import get_chain_engine
        chain_engine = get_chain_engine()
        snap["chain_reactions_catalog"] = chain_engine.get_all_chains()
        active_transmissions = []
        for ticker, series in list(prices.items())[:200]:
            try:
                s = series.dropna()
                if len(s) < 5: continue
                d1 = (float(s.iloc[-1]) / float(s.iloc[-2]) - 1) * 100
                if abs(d1) >= 2.0:
                    chains_for_ticker = chain_engine.get_chain_for_parent(ticker)
                    if chains_for_ticker:
                        cascade = chain_engine.calculate_cascade(ticker, d1, quad)
                        active_transmissions.append({"shock_ticker": ticker, "shock_pct": round(d1, 2), "cascade": cascade})
            except Exception:
                continue
        snap["transmissions"] = {"active_transmissions": active_transmissions, "shock_count": len(active_transmissions)}
        # MERGED key for pages
        snap["chain_reactions"] = {
            "catalog": snap["chain_reactions_catalog"],
            "active_transmissions": active_transmissions,
            "supply_chain_chains": supply_chains,
        }
    except Exception as e:
        logger.error(f"v40: chain reactions failed: {e}")
        snap["chain_reactions_catalog"] = {}; snap["transmissions"] = {"active_transmissions": [], "error": str(e)}
        snap["chain_reactions"] = {"catalog": {}, "active_transmissions": [], "supply_chain_chains": supply_chains}

    # ── Alpha Center Curator ──
    _cb("Running Alpha Center 5-layer filter...", 65)
    try:
        from engines.alpha_center_curator import get_curator
        curator = get_curator(bottleneck_ref_path="bottleneck_reference.json")
        keith_signals = snap.get("keith_signals", {}) or snap.get("keith_signal_sync", {})
        wf_results = snap.get("walkforward_results", {})
        ac_result = curator.filter_universe(keith_signals=keith_signals, wf_results=wf_results, current_quad=quad)
        snap["alpha_center"] = ac_result
    except Exception as e:
        logger.error(f"v40: alpha center failed: {e}")
        snap["alpha_center"] = {"passed": [], "rejected": [], "error": str(e)}

    # ── Hedgeye Position Sizing ──
    _cb("Computing Hedgeye position sizing...", 75)
    try:
        from engines.hedgeye_position_sizing import run_sizing as run_v40_sizing
        passed = snap.get("alpha_center", {}).get("passed", [])
        candidates = [{"ticker": p["ticker"], "conviction": min(10, max(3, p["candidate"].get("stars", 3) * 2)), "is_breakout": False} for p in passed]
        rr_for_sizing = snap.get("risk_range", {}).get("asset_ranges", {})
        sizing = run_v40_sizing(candidates, quad, vix_last, keith_signals=snap.get("keith_signals"), rr_data=rr_for_sizing)
        snap["sizing"] = sizing; snap["hedgeye_position_sizing"] = sizing; snap["portfolio_sizing_v2"] = sizing
    except Exception as e:
        logger.error(f"v40: sizing failed: {e}")
        snap["sizing"] = {"positions": [], "error": str(e)}; snap["hedgeye_position_sizing"] = snap["sizing"]; snap["portfolio_sizing_v2"] = snap["sizing"]

    # ── Walkforward (skipped interactive — too slow) ──
    _cb("Skipping walkforward gate (use Portfolio Stress page for on-demand)", 85)
    snap["walkforward_results_v40"] = {"skipped": True, "reason": "Run on-demand from Portfolio Stress page"}

    # ── Scenario Discovery ──
    _cb("Scenario discovery...", 92)
    try:
        from engines.scenario_discovery_engine import run_scenario_discovery
        scen = run_scenario_discovery(gip_result=gip, current_quad=quad)
        snap["scenarios"] = scen; snap["scenario_discovery"] = scen
    except Exception as e:
        logger.error(f"v40: scenario discovery failed: {e}")
        snap["scenarios"] = {"active_scenarios": [], "error": str(e)}; snap["scenario_discovery"] = snap["scenarios"]

    # ── Regime Transition ──
    try:
        from engines.regime_transition_engine import run_regime_transition
        rt = run_regime_transition(gip)
        snap["regime_transition"] = rt
    except Exception as e:
        snap["regime_transition"] = {"transitioning": False, "error": str(e)}

    # ── Market Health v40 ──
    try:
        from engines.market_health_engine import run_market_health
        snap["market_health"] = run_market_health(prices, vix=vix_last, dxy=snap.get("dxy"))
    except Exception as e:
        snap["market_health"] = {"score": 50, "label": "ERROR", "error": str(e)}

    # ── External Data (options/COT/OI/on-chain/CME/FINRA) ──
    _cb("Fetching external data (options, COT, on-chain, FINRA, CME)...", 95)
    ext_data = _v40_fetch_external_data(snap, prices, quad, _cb)
    snap["options_data"] = ext_data.get("options_data", {})
    snap["cot_data"] = ext_data.get("cot_data", {})
    snap["cme_oi"] = ext_data.get("cme_oi", {})
    snap["onchain_data"] = ext_data.get("onchain_data", {})
    snap["finra_short"] = ext_data.get("finra_short", {})

    # ── Tier1Alpha ──
    try:
        from engines.tier1alpha_model import compute_tier1alpha
        snap["tier1alpha"] = compute_tier1alpha(snap)
    except Exception as e:
        logger.error(f"v40: tier1alpha failed: {e}")
        snap["tier1alpha"] = {}

    # ── Narrative ──
    try:
        from engines.narrative_engine import build_narrative
        snap["narrative"] = build_narrative(snap)
        narr_scenarios = snap["narrative"].get("scenarios", {})
        if narr_scenarios and not snap.get("scenarios"):
            snap["scenarios"] = narr_scenarios; snap["scenario_discovery"] = narr_scenarios
    except Exception as e:
        logger.error(f"v40: narrative engine failed: {e}")
        snap["narrative"] = {}

    # ═══════════════════════════════════════════════════════════════════
    # TIER S ENGINE CALLS (v40.5 — ALL WIRED TO SNAP)
    # ═══════════════════════════════════════════════════════════════════
    if _V40_TIER_S.get("alpha_synthesis"):
        _cb("Running Alpha Synthesis v37...", 74)
        try:
            snap["alpha_synthesis"] = run_alpha_synthesis(snap, prices)
            logger.info(f"Alpha synthesis: {len(snap['alpha_synthesis'].get('top_signals', []))} signals")
        except Exception as e:
            logger.warning(f"Alpha synthesis failed: {e}"); snap["errors"].append(f"alpha_synthesis: {e}")

    if _V40_TIER_S.get("entry_decision"):
        _cb("Running entry decision engine...", 75)
        try:
            entry_decisions = {}
            for item in snap.get("alpha_center", {}).get("all", [])[:50]:
                t = item.get("ticker")
                if not t: continue
                cs = snap.get("composite_signals", {}).get(t, {})
                gd = (snap.get("gamma_data", {}) or {}).get(t) if snap.get("gamma_data") else None
                entry_decisions[t] = decide_entry(
                    ticker=t, px=item.get("price", 0), composite_signal=cs,
                    risk_range=snap.get("risk_ranges", {}).get("asset_ranges", {}).get(t),
                    gamma_data=gd, karsan=snap.get("karsan_scanner", {}).get("per_ticker", {}).get(t),
                    thought_process=snap.get("thought_process", {}).get(t), quad=quad,
                )
            snap["entry_decisions"] = entry_decisions
        except Exception as e:
            logger.warning(f"Entry decision failed: {e}"); snap["errors"].append(f"entry_decision: {e}")

    if _V40_TIER_S.get("movement_timing"):
        _cb("Running movement timing engine...", 76)
        try:
            mtd = MovementTimingDetector()
            movement_regimes = {}
            for t in list(prices.keys())[:80]:
                s = prices.get(t)
                if s is not None and len(s) >= 60:
                    try:
                        reg = mtd.detect(t, pd.Series(s), snap)
                        if reg: movement_regimes[t] = reg
                    except Exception: pass
            snap["movement_regimes"] = movement_regimes
        except Exception as e:
            logger.warning(f"Movement timing failed: {e}"); snap["errors"].append(f"movement_timing: {e}")

    if _V40_TIER_S.get("daily_play"):
        _cb("Running daily play engine...", 77)
        try:
            dpe = DailyPlayEngine()
            snap["daily_plays"] = dpe.scan_all(prices, snap)
        except Exception as e:
            logger.debug(f"Daily play failed: {e}"); snap["errors"].append(f"daily_play: {e}")

    if _V40_TIER_S.get("ihsg_specialist"):
        _cb("Running IHSG specialist v38...", 78)
        try:
            ihsg_spec = IHSGSpecialistEngine()
            snap["ihsg_specialist"] = ihsg_spec.analyze(prices)
        except Exception as e:
            logger.warning(f"IHSG specialist failed: {e}"); snap["errors"].append(f"ihsg_specialist: {e}")

    if _V40_TIER_S.get("chain_reaction"):
        _cb("Running chain reaction engine (legacy)...", 79)
        try:
            cre = ChainReactionEngine()
            chain_tickers = [t for t in list(prices.keys())[:100] if t in [
                "NVDA", "AMD", "AVGO", "TSM", "MU", "VST", "CEG", "BE", "LITE", "COHR", "MRVL", "NXT", "AMPH", "SCCO", "FCX", "ALB",
                "CL=F", "USO", "XOM", "CVX", "FRO", "TK", "INSW",
            ]]
            snap["chain_reaction_legacy"] = cre.project_all(chain_tickers)
        except Exception as e:
            logger.debug(f"Chain reaction legacy failed: {e}"); snap["errors"].append(f"chain_reaction: {e}")

    if _V40_TIER_S.get("frontrun"):
        _cb("Running front-run engine...", 80)
        try:
            fre = FrontRunEngine()
            snap["frontrun_signals"] = fre.scan(snap.get("news_narratives", {}), prices)
        except Exception as e:
            logger.debug(f"Front-run engine failed: {e}"); snap["errors"].append(f"frontrun: {e}")

    if _V40_TIER_S.get("methodology_pack"):
        _cb("Running methodology pack (6 investors)...", 81)
        try:
            all_tickers = list(prices.keys())
            snap["methodology_scores"] = {}
            for t in all_tickers[:50]:
                try:
                    snap["methodology_scores"][t] = evaluate_all_pack(
                        ticker=t, prices_series=prices.get(t),
                        boom_bust_stage=snap.get("boom_bust", {}).get("stage", "ACCELERATION"),
                        super_bubble_score=snap.get("reflexivity", {}).get("super_bubble_score", 0),
                        vix=vix_last, fred=fred,
                        gamma_data=snap.get("gamma_data", {}).get(t),
                        greeks_data=snap.get("greeks_data", {}).get(t),
                        markov_v3=snap.get("markov_v3"),
                        risk_range=snap.get("risk_ranges", {}).get("asset_ranges", {}).get(t),
                        composite_signal=snap.get("composite_signals", {}).get(t),
                    )
                except Exception: pass
        except Exception as e:
            logger.warning(f"Methodology pack failed: {e}"); snap["errors"].append(f"methodology_pack: {e}")

    # ── KEITH SIGNAL SYNC (v40.5 — ENGINE NOW CALLED) ──
    _cb("Running Keith McCullough signal sync...", 82)
    try:
        keith_sync = {}; keith_summary = {"total_signals": 0, "trade_bullish": 0, "trade_bearish": 0, "trend_bullish": 0, "trend_bearish": 0, "overrides_applied": 0, "duration_mismatches": 0, "last_updated": datetime.now().strftime("%Y-%m-%d"), "sources": ["Keith Signal Sync Engine v40.5"]}
        for item in snap.get("alpha_center", {}).get("all", []):
            t = item.get("ticker", "")
            if not t: continue
            # Call engine if available, else fallback to inline logic via resolve_direction
            if _V40_KEITH:
                try:
                    ks = resolve_direction(t, item.get("direction", "LONG"), snap.get("risk_range", {}), prices)
                except Exception:
                    ks = None
            else:
                ks = None
            if not ks:
                # Inline fallback (preserved from v39)
                ar = snap.get("risk_range", {}).get("asset_ranges", {})
                v = ar.get(t, {}); s = prices.get(t)
                if s is None or not v: continue
                try:
                    s_clean = pd.to_numeric(pd.Series(s), errors="coerce").dropna()
                    if len(s_clean) < 20: continue
                    px = float(s_clean.iloc[-1])
                    tr = v.get("trade", {}); lrr = tr.get("lrr"); trr = tr.get("trr")
                    if not lrr or not trr or not all(math.isfinite(x) for x in [px, lrr, trr]): continue
                    px_vs_trr = (px - trr) / max(trr, 0.001); px_vs_lrr = (px - lrr) / max(lrr, 0.001)
                    history = s_clean.tail(5)
                    was_above_trr = any(float(x) > trr * 1.005 for x in history.head(4))
                    was_below_lrr = any(float(x) < lrr * 0.995 for x in history.head(4))
                    now_inside = lrr * 0.995 <= px <= trr * 1.005
                    reclaiming_trr = was_above_trr and now_inside and all(lrr * 0.995 <= float(x) <= trr * 1.005 for x in history.tail(2))
                    reclaiming_lrr = was_below_lrr and now_inside and all(lrr * 0.995 <= float(x) <= trr * 1.005 for x in history.tail(2))
                    if px > trr * 1.01 and not reclaiming_trr:
                        ks = {"trade": "BEARISH", "trend": "BEARISH", "basis": f"Price {px:.2f} > TRR {trr:.2f} — breakdown from top", "px": px, "lrr": lrr, "trr": trr, "reclaiming": False}
                    elif px < lrr * 0.99 and not reclaiming_lrr:
                        ks = {"trade": "BEARISH", "trend": "BEARISH", "basis": f"Price {px:.2f} < LRR {lrr:.2f} — breakdown from low", "px": px, "lrr": lrr, "trr": trr, "reclaiming": False}
                    elif reclaiming_trr or reclaiming_lrr:
                        ks = {"trade": "BULLISH", "trend": "BULLISH", "basis": f"Price {px:.2f} reclaiming risk range", "px": px, "lrr": lrr, "trr": trr, "reclaiming": True}
                    else:
                        continue
                except Exception:
                    continue
            if not ks: continue
            keith_summary["total_signals"] += 1
            if ks.get("trade") == "BULLISH": keith_summary["trade_bullish"] += 1
            else: keith_summary["trade_bearish"] += 1
            if ks.get("trend") == "BULLISH": keith_summary["trend_bullish"] += 1
            else: keith_summary["trend_bearish"] += 1
            current_dir = item.get("direction", "LONG")
            keith_trade = ks.get("trade", "NEUTRAL")
            override = False; final_dir = current_dir
            if keith_trade == "BEARISH" and current_dir == "LONG":
                override = True; final_dir = "SHORT"
                item["direction"] = "SHORT"; item["side"] = "short"; item["action"] = "AVOID"
                item["recommendation"] = "AVOID — Keith Bearish Override"
                item["grade"] = "C"
                keith_summary["overrides_applied"] += 1
            elif keith_trade == "BULLISH" and current_dir == "SHORT":
                override = True; final_dir = "LONG"
                item["direction"] = "LONG"; item["side"] = "long"
                keith_summary["overrides_applied"] += 1
            keith_sync[t] = {"ticker": t, "original_direction": current_dir, "direction": final_dir, "keith_trade": keith_trade, "keith_trend": ks.get("trend", "NEUTRAL"), "override": override, "basis": ks.get("basis", ""), "duration_mismatch": keith_trade != ks.get("trend", "NEUTRAL"), "px": ks.get("px"), "lrr": ks.get("lrr"), "trr": ks.get("trr"), "reclaiming": ks.get("reclaiming")}
            if keith_trade != ks.get("trend", "NEUTRAL"):
                keith_summary["duration_mismatches"] += 1
        snap["keith_sync"] = keith_sync; snap["keith_summary"] = keith_summary
        logger.info(f"Keith sync: {keith_summary['overrides_applied']} overrides on {keith_summary['total_signals']} signals")
        # Rebuild levels after Keith override
        snap["alpha_center"]["level_1"] = [i for i in snap["alpha_center"].get("all", []) if i.get("grade") == "A"]
        snap["alpha_center"]["level_2"] = [i for i in snap["alpha_center"].get("all", []) if i.get("grade") == "B"]
    except Exception as e:
        logger.warning(f"Keith sync failed: {e}"); snap["errors"].append(f"keith_sync: {e}")

    # ── Legacy engine calls (preserved but only for data not covered by v40) ──
    # Behavioral, ODTE, Skew, Reflexivity, Boom-Bust, Vanna-Charm, Interconnect, etc.
    _cb("Running behavioral macro...", 32)
    try:
        dgs10 = float(fred.get("DGS10", pd.Series()).dropna().iloc[-1]) if fred.get("DGS10") is not None else 4.5
        t5yie = float(fred.get("T5YIE", pd.Series()).dropna().iloc[-1]) if fred.get("T5YIE") is not None else 2.4
        real_yield = dgs10 - t5yie
        behavioral = get_behavioral_macro(vix=vix_last, real_yield=real_yield, dxy_ret=0.0)
        snap["behavioral_macro"] = behavioral
    except Exception as e:
        logger.warning(f"Behavioral macro failed: {e}"); snap["errors"].append(f"behavioral: {e}")

    _cb("Running 0DTE Monitor...", 34)
    try:
        snap["odte_monitor"] = run_odte_monitor(["SPY", "QQQ", "IWM"], prices)
    except Exception as e:
        logger.warning(f"0DTE monitor failed: {e}"); snap["errors"].append(f"odte: {e}")

    _cb("Running skew term structure...", 36)
    try:
        snap["skew_term"] = run_skew_term(list(US_SECTORS.keys()) + ["SPY", "QQQ", "IWM", "GLD", "TLT"], prices)
    except Exception as e:
        logger.debug(f"Skew term failed: {e}"); snap["errors"].append(f"skew: {e}")

    _cb("Running reflexivity...", 38)
    try:
        snap["reflexivity"] = run_reflexivity(prices, fred, quad)
    except Exception as e:
        logger.warning(f"Reflexivity failed: {e}"); snap["errors"].append(f"reflexivity: {e}")

    _cb("Running boom-bust stage...", 40)
    try:
        snap["boom_bust"] = classify_stage(prices, fred, snap.get("health", {}), quad)
    except Exception as e:
        logger.warning(f"Boom-bust failed: {e}"); snap["errors"].append(f"boombust: {e}")

    _cb("Running vanna & charm flows...", 42)
    try:
        vanna_charm = {}
        for t in ["SPY", "QQQ", "IWM", "GLD", "TLT", "BTC-USD", "ETH-USD"]:
            vc = get_vanna_charm_flows(t, prices, vix_last, 0.0, 7)
            if vc: vanna_charm[t] = vc
        snap["vanna_charm_flows"] = vanna_charm
    except Exception as e:
        logger.warning(f"Vanna/Charm failed: {e}"); snap["errors"].append(f"vannacharm: {e}")

    _cb("Running interconnect cascade...", 44)
    try:
        snap["interconnect"] = run_interconnect(prices, fred, news_analysis, quad)
    except Exception as e:
        logger.debug(f"Interconnect failed: {e}"); snap["errors"].append(f"interconnect: {e}")

    if _V2_CASCADE:
        _cb("Running cascade engine...", 46)
        try:
            snap["cascade_analysis"] = run_all_cascades(prices)
        except Exception as e:
            logger.warning(f"Cascade engine failed: {e}"); snap["errors"].append(f"cascade: {e}")

    if _V2_SUPPLY:
        _cb("Running supply chain graph...", 48)
        try:
            active_shocks = (snap.get("cascade_analysis") or {}).get("active_shocks", {})
            snap["supply_chain_analysis"] = run_supply_chain_analysis(prices, active_shocks=active_shocks)
        except Exception as e:
            logger.warning(f"Supply chain analysis failed: {e}"); snap["errors"].append(f"supply_chain: {e}")

    if _V2_YVES:
        _cb("Running Yves alerts v2...", 50)
        try:
            aaii_for_yves = snap.get("behavioral_macro", {}) or {}
            real_yield_val = 0.0
            try:
                def _last_finite(s):
                    if s is None: return None
                    try:
                        ss = pd.to_numeric(s, errors="coerce").dropna()
                        return float(ss.iloc[-1]) if len(ss) > 0 else None
                    except Exception: return None
                dgs10_v = _last_finite(fred.get("DGS10")) or 4.0
                t10yie_v = _last_finite(fred.get("T10YIE")) or 2.3
                real_yield_val = dgs10_v - t10yie_v
            except Exception:
                real_yield_val = aaii_for_yves.get("real_yield", 1.5)
            snap["yves_v2"] = run_yves_v2(aaii=aaii_for_yves, vix=vix_last, real_yield=real_yield_val, put_call=aaii_for_yves.get("put_call_ratio", 1.0), prices=prices, fred=fred)
        except Exception as e:
            logger.warning(f"Yves v2 failed: {e}"); snap["errors"].append(f"yves_v2: {e}")

    if _V2_CEM:
        _cb("Running Cem Karsan universal...", 52)
        try:
            cem_targets = ["SPY", "QQQ", "IWM", "GLD", "TLT", "BTC-USD", "ETH-USD", "USO", "UNG", "FXE", "EEM", "XLE", "XLK", "XLF"]
            snap["cem_karsan_universal"] = cem_universal_multi(cem_targets, prices, vix_last, max_yfinance=8)
        except Exception as e:
            logger.warning(f"Cem Karsan Universal failed: {e}"); snap["errors"].append(f"cem_universal: {e}")

    if _V2_DISCOVERY:
        _cb("Running discovery brain...", 54)
        try:
            prev_quad_val = None
            try:
                stale_snap = load_snapshot(max_age_hours=72)
                if stale_snap: prev_quad_val = stale_snap.get("summary", {}).get("structural_quad")
            except Exception: pass
            bottleneck_ref_data = {}
            try:
                if os.path.exists("bottleneck_reference.json"):
                    with open("bottleneck_reference.json") as f: bottleneck_ref_data = json.load(f)
            except Exception: pass
            snap["discovery_brain"] = run_discovery_brain(prices=prices, news_analysis=snap.get("news_narratives", {}), gip_features=snap.get("gip", {}).get("features", {}), current_quad=quad, monthly_quad=monthly_quad, prev_quad=prev_quad_val, cot_data=snap.get("cot_oi", {}).get("cot"), bottleneck_ref=bottleneck_ref_data)
        except Exception as e:
            logger.debug(f"Discovery Brain failed: {e}"); snap["errors"].append(f"discovery_brain: {e}")

    if _V2_EXPANDER:
        _cb("Running ticker universe expander...", 56)
        try:
            current_universe = list(prices.keys())
            expansion = run_ticker_expander(prices=prices, news_analysis=snap.get("news_narratives", {}), current_universe=current_universe, cascade_results=snap.get("cascade_analysis"), bottleneck_ref=None)
            snap["ticker_universe_expansion"] = expansion
            auto_add_list = expansion.get("auto_add_recommended", [])
            if auto_add_list:
                snap["auto_add_tickers_next_run"] = auto_add_list
        except Exception as e:
            logger.warning(f"Ticker expander failed: {e}"); snap["errors"].append(f"ticker_expander: {e}")

    _cb("Fetching live options...", 58)
    yfinance_options_data = {}
    if YFinanceOptionsEngine is not None:
        try:
            yf_engine = YFinanceOptionsEngine()
            key_tickers = [t for t in ["SPY","QQQ","IWM"] if t in prices][:3]
            for i, ticker in enumerate(key_tickers):
                if i > 0: time.sleep(3.0)
                try:
                    opt = yf_engine.analyze(ticker)
                    if opt and opt.get("ok"): yfinance_options_data[ticker] = opt
                except Exception as e:
                    logger.warning(f"Options fetch failed for {ticker}: {e}")
                    if "Rate limit" in str(e) or "429" in str(e):
                        logger.warning("Yahoo rate limit detected — skipping remaining options fetch"); break
        except Exception as e:
            logger.error(f"YFinanceOptionsEngine failed: {e}")
    snap["yfinance_options"] = yfinance_options_data

    _cb("Scenario discovery...", 60)
    try:
        snap["scenario_discovery"] = run_scenario_discovery(prices, fred, news_analysis, quad)
    except Exception as e:
        logger.debug(f"Scenario discovery failed: {e}"); snap["errors"].append(f"scenario_discovery: {e}")

    _cb("Transmission engine...", 62)
    try:
        snap["transmission"] = run_transmission(prices, fred, news_analysis, quad)
    except Exception as e:
        logger.debug(f"Transmission failed: {e}"); snap["errors"].append(f"transmission: {e}")

    _cb("Regime transition...", 64)
    try:
        snap["regime_transition"] = run_regime_transition(prices, fred, quad, getattr(gip, "structural_probs", {}) if gip else {})
    except Exception as e:
        logger.debug(f"Regime transition failed: {e}"); snap["errors"].append(f"regime_transition: {e}")

    _cb("News NLP v3...", 66)
    try:
        snap["news_nlp_v3"] = run_news_nlp(news_headlines)
    except Exception as e:
        logger.warning(f"News NLP v3 failed: {e}"); snap["errors"].append(f"news_nlp_v3: {e}")

    _cb("Bottleneck discovery v3...", 68)
    try:
        snap["bottleneck_v3"] = run_bottleneck_discovery_v3(prices, fred, news_analysis)
    except Exception as e:
        logger.warning(f"Bottleneck v3 failed: {e}"); snap["errors"].append(f"bottleneck_v3: {e}")

    _cb("Running gamma & Greeks proxy...", 70)
    key_tickers = ["SPY", "QQQ", "IWM", "GLD", "TLT", "BTC-USD", "ETH-USD"]
    try: snap["gex_data"] = gex_analyze_multi(key_tickers, prices, vix_last)
    except Exception as e: logger.warning(f"GEX failed: {e}"); snap["errors"].append(f"gex: {e}")
    try: snap["charm_data"] = charm_analyze_multi(key_tickers, prices, vix_last)
    except Exception as e: logger.warning(f"Charm failed: {e}"); snap["errors"].append(f"charm: {e}")
    try: snap["vanna_data"] = vanna_analyze_multi(key_tickers, prices, vix_last, dxy_ret)
    except Exception as e: logger.warning(f"Vanna failed: {e}"); snap["errors"].append(f"vanna: {e}")
    try: snap["odte_enhanced"] = odte_enhanced_multi(key_tickers, prices, vix_last)
    except Exception as e: logger.warning(f"0DTE enhanced failed: {e}"); snap["errors"].append(f"odte_enh: {e}")
    try: snap["structure_data"] = structure_analyze_multi(key_tickers, prices)
    except Exception as e: logger.warning(f"Structure failed: {e}"); snap["errors"].append(f"structure: {e}")
    try: snap["afternoon_data"] = afternoon_analyze_multi(key_tickers, prices, snap.get("charm_data"), snap.get("vanna_data"), vix_last, snap.get("gex_data"), snap.get("structure_data"))
    except Exception as e: logger.warning(f"Afternoon failed: {e}"); snap["errors"].append(f"afternoon: {e}")
    try: snap["volga_data"] = analyze_volga("SPY", prices, prices, vix_last)
    except Exception as e: logger.warning(f"Volga failed: {e}"); snap["errors"].append(f"volga: {e}")
    try: snap["institutional_data"] = inst_analyze_multi(key_tickers, prices, vix_last)
    except Exception as e: logger.warning(f"Institutional failed: {e}"); snap["errors"].append(f"institutional: {e}")

    all_gamma_tickers = list(prices.keys())[:150]
    if GammaEngine is not None:
        try: snap["gamma_data"] = GammaEngine().analyze_multi(all_gamma_tickers, prices, vix_last, dxy_ret)
        except Exception as e: logger.warning(f"GammaEngine failed: {e}"); snap["errors"].append(f"gamma: {e}")
    if GreeksProxy is not None:
        try: snap["greeks_data"] = GreeksProxy().analyze_multi(all_gamma_tickers, prices, vix_last, dxy_ret, quad)
        except Exception as e: logger.warning(f"GreeksProxy failed: {e}"); snap["errors"].append(f"greeks: {e}")

    if _V2_COMPOSITE:
        _cb("Composite signal analysis...", 72)
        try:
            rr_keys = list(snap.get("risk_range", {}).get("asset_ranges", {}).keys())
            composite_signals = composite_analyze_multi(
                tickers=rr_keys, risk_ranges=snap.get("risk_range", {}),
                prices=prices, cot_data=snap.get("cot_oi", {}).get("cot", {}),
                oi_data=snap.get("cot_oi", {}).get("oi", {}),
                greeks_data=snap.get("greeks_data", {}),
                gamma_data=snap.get("gamma_data", {}),
                news_data=snap.get("news_analysis", {}).get("ticker_specific", {}),
                quad=quad,
            )
            snap["composite_signals"] = composite_signals
            n_flipped = sum(1 for s in composite_signals.values() if s.get("flipped_from_composite"))
            logger.info(f"Composite signals: {len(composite_signals)} tickers, {n_flipped} flipped")
        except Exception as e:
            logger.warning(f"Composite signal engine failed: {e}"); snap["errors"].append(f"composite: {e}")

    if _V2_BONDS_XAU:
        _cb("Bonds-XAU regime analysis...", 74)
        try:
            bxau = run_bonds_xau_regime(prices, fred)
            snap["bonds_xau_regime"] = bxau
        except Exception as e:
            logger.warning(f"Bonds-XAU regime failed: {e}"); snap["errors"].append(f"bonds_xau: {e}")

    if _V7_MARKOV:
        _cb("Markov Regime V3...", 76)
        try:
            markov = run_markov_v3(prices, fred)
            snap["markov_v3"] = {"current_regime": markov.current_regime, "confidence": markov.confidence, "regime_probabilities": markov.regime_probabilities, "forecast_1m": markov.forecast_1m, "forecast_3m": markov.forecast_3m, "forecast_6m": markov.forecast_6m, "stationary": markov.stationary, "change_point_probability": markov.change_point_probability, "change_point_alert": markov.change_point_alert, "expected_duration_days": markov.expected_duration_days, "kelly_fraction": markov.kelly_fraction, "notes": markov.notes, "n_observations": markov.n_observations}
        except Exception as e:
            logger.warning(f"Markov V3 failed: {e}"); snap["errors"].append(f"markov_v3: {e}")

    if _V7_SMART:
        _cb("Smart money 13F analysis...", 78)
        try:
            all_tickers = list(prices.keys())
            snap["smart_money"] = run_smart_money_analysis(all_tickers)
        except Exception as e:
            logger.warning(f"Smart money tracker failed: {e}")

    if _V7_CAPROT:
        _cb("Capital rotation monitor...", 80)
        try:
            snap["capital_rotation"] = compute_capital_rotation(prices)
        except Exception as e:
            logger.warning(f"Capital rotation failed: {e}")

    if _V7_UST:
        _cb("UST auction tracker...", 82)
        try:
            snap["ust_auction"] = run_ust_auction_tracker()
        except Exception as e:
            logger.warning(f"UST auction failed: {e}")

    if _V7_THOUGHT:
        _cb("Investment thesis analysis...", 84)
        try:
            rr_keys = list(snap.get("risk_range", {}).get("asset_ranges", {}).keys())
            bb_stage = snap.get("boom_bust", {}).get("stage", "ACCELERATION")
            bubble_score = snap.get("reflexivity", {}).get("super_bubble_score", 0)
            thesis_results = v7_thesis_multi(rr_keys, quad=quad, boom_bust_stage=bb_stage, super_bubble_score=bubble_score, prices=prices, fred=fred)
            snap["thought_process"] = thesis_results
            snap["top_theses"] = sorted(thesis_results.values(), key=lambda x: x.get("thesis_score", 0), reverse=True)[:20]
        except Exception as e:
            logger.warning(f"Thought process failed: {e}")

    if _V7_VRP:
        _cb("VRP vol scanner...", 86)
        try:
            vrp_tickers = [t for t in ["SPY", "QQQ", "IWM", "NVDA", "TSLA", "AAPL", "MSFT", "META", "GOOGL", "AMZN", "AMD", "GLD", "SLV", "TLT", "BTC-USD", "ETH-USD"] if t in prices]
            snap["vrp_scanner"] = scan_vrp(vrp_tickers, prices, vix=vix_last)
        except Exception as e:
            logger.warning(f"VRP scanner failed: {e}")

    if _V7_SQUEEZE:
        _cb("Squeeze scanner...", 88)
        try:
            snap["squeeze_scanner"] = scan_squeezes(prices=prices, gamma_data=snap.get("gamma_data", {}))
        except Exception as e:
            logger.warning(f"Squeeze scanner failed: {e}")

    if _V11_VOLSIGNALS:
        _cb("VolSignals dealer regime...", 90)
        try:
            snap["volsignals_regime"] = compute_dealer_regime_multi(prices=prices, gex_data=snap.get("gex_data", {}), vanna_data=snap.get("vanna_data", {}), charm_data=snap.get("charm_data", {}), gamma_data=snap.get("gamma_data", {}), key_tickers=["SPY", "QQQ", "IWM"] + list(prices.keys())[:150])
        except Exception as e:
            logger.warning(f"VolSignals regime failed: {e}")

    if _V11_SPOTGAMMA:
        _cb("SpotGamma structural levels...", 92)
        try:
            snap["spotgamma_levels"] = compute_structural_levels_multi(prices=prices, options_data=snap.get("gex_data", {}), key_tickers=["SPY", "QQQ", "IWM"] + list(prices.keys())[:150])
        except Exception as e:
            logger.warning(f"SpotGamma levels failed: {e}")

    if _V11_SCHADNER:
        _cb("Schadner IV validation...", 94)
        try:
            yf_opts = snap.get("yfinance_options", {})
            schadner_validation = {}
            for t, opt in yf_opts.items():
                if not isinstance(opt, dict): continue
                if opt.get("ok") and opt.get("call_price") and opt.get("strike") and opt.get("forward"):
                    iv_exact = schadner_iv(C=opt["call_price"], K=opt["strike"], F=opt["forward"], T=opt.get("days_to_expiry", 21)/365.0, D=1.0)
                    if iv_exact is not None:
                        iv_proxy = opt.get("iv", 0) or opt.get("implied_vol", 0) or 0
                        schadner_validation[t] = validate_iv_proxy(t, iv_proxy, iv_exact)
                        schadner_validation[t]["source"] = "SCHADNER"
            snap["schadner_iv"] = schadner_validation
        except Exception as e:
            logger.warning(f"Schadner IV failed: {e}")

    all_tickers = list(prices.keys())
    if _V9_KARSAN:
        _cb("Karsan vol scanner...", 95)
        try: snap["karsan_scanner"] = scan_karsan(all_tickers, prices, vix=vix_last)
        except Exception as e: logger.debug(f"Karsan scanner failed: {e}")
    if _V9_SPOTGAMMA:
        _cb("SpotGamma proxy scanner...", 96)
        try: snap["spotgamma_scanner"] = run_spotgamma_scanner(prices, vix=vix_last)
        except Exception as e: logger.warning(f"SpotGamma scanner failed: {e}")
    if _V9_LEOPOLD:
        _cb("Leopold methodology scan...", 97)
        try: snap["leopold_scan"] = run_leopold_scan(all_tickers, prices)
        except Exception as e: logger.warning(f"Leopold scan failed: {e}")
    if _V9_COATUE:
        _cb("COATUE methodology scan...", 98)
        try: snap["coatue_scan"] = run_coatue_scan(all_tickers, prices)
        except Exception as e: logger.warning(f"COATUE scan failed: {e}")

    if _V10_NARRATIVE:
        _cb("Building autonomous narrative...", 99)
        try:
            snap["narrative"] = build_narrative(snap)
        except Exception as e:
            logger.warning(f"Narrative engine failed: {e}")

    if _V32_INTEGRATOR:
        _cb("Running Attachment 4 engine integration...", 99.5)
        try:
            pv = float(kwargs.get("portfolio_value", 100_000) or 100_000)
            snap = enhance_snapshot(snap, prices, portfolio_value=pv)
        except Exception as e:
            logger.warning(f"Attachment 4 integration failed: {e}"); snap["errors"].append(f"attachment4: {e}")

    # ── Summary ──
    alpha_items = snap.get("alpha_center", {}).get("all", [])
    strong_longs = sum(1 for i in alpha_items if i.get("direction") == "LONG" and i.get("grade") in ("A", "A+"))
    longs = sum(1 for i in alpha_items if i.get("direction") == "LONG")
    strong_shorts = sum(1 for i in alpha_items if i.get("direction") == "SHORT" and i.get("grade") in ("A", "A+"))
    shorts = sum(1 for i in alpha_items if i.get("direction") == "SHORT")
    snap["daily_signals_summary"] = {
        "total": len(alpha_items), "strong_longs": strong_longs, "longs": longs,
        "strong_shorts": strong_shorts, "shorts": shorts,
        "neutrals": len(alpha_items) - longs - shorts,
        "top_5_by_score": sorted(alpha_items, key=lambda x: x.get("priority_score", 0), reverse=True)[:5],
    }
    snap["daily_signals"] = alpha_items[:20]
    snap["transition"] = SimpleNamespace(front_run_window="1-2w" if quad in ("Q1", "Q2") else "3-6w")
    snap["frontrun"] = {
        "boarding_now": [i for i in alpha_items if i.get("grade") == "A"][:3],
        "gate_opens_soon": [i for i in alpha_items if i.get("grade") == "B"][:3],
        "check_in": [i for i in alpha_items if i.get("grade") == "C"][:3],
        "wait": [],
    }
    snap["regime_forecast"] = {
        "1m": {"predicted_quad": monthly_quad, "prediction_confidence": 0.55},
        "3m": {"predicted_quad": quad, "prediction_confidence": 0.60},
        "6m": {"predicted_quad": quad, "prediction_confidence": 0.50},
    }

    # DXY Correlation
    try:
        dxy_corr_data = {"dxy_trend": "Neutral", "dxy_1m": dxy_ret, "total_correlated": 0, "strongest_positive_corr": [], "strongest_negative_corr": []}
        if dxy_s is not None and len(dxy_s) >= 22:
            dxy_clean = pd.to_numeric(dxy_s, errors="coerce").dropna()
            pos_corr = []; neg_corr = []; correlated = 0
            for ticker, s in prices.items():
                if s is None or len(s) < 22 or ticker == "DX-Y.NYB": continue
                try:
                    s_clean = pd.to_numeric(s, errors="coerce").dropna()
                    min_len = min(len(dxy_clean), len(s_clean))
                    if min_len < 22: continue
                    dxy_slice = dxy_clean.tail(min_len).pct_change().dropna()
                    s_slice = s_clean.tail(min_len).pct_change().dropna()
                    if len(dxy_slice) >= 20 and len(s_slice) >= 20:
                        dxy_arr = dxy_slice.tail(20).to_numpy()
                        s_arr = s_slice.tail(20).to_numpy()
                        mask = np.isfinite(dxy_arr) & np.isfinite(s_arr)
                        if mask.sum() < 10: continue
                        dxy_clean_arr = dxy_arr[mask]; s_clean_arr = s_arr[mask]
                        if dxy_clean_arr.std() == 0 or s_clean_arr.std() == 0: continue
                        with np.errstate(invalid='ignore'):
                            corr = np.corrcoef(dxy_clean_arr, s_clean_arr)[0, 1]
                        if not math.isfinite(corr): continue
                        correlated += 1
                        if abs(corr) > 0.3:
                            entry = {"correlation": round(corr, 2), "meaning": "Rises with DXY" if corr > 0 else "Falls when DXY rises"}
                            if corr > 0: pos_corr.append((ticker, entry))
                            else: neg_corr.append((ticker, entry))
                except Exception: pass
            dxy_corr_data["total_correlated"] = correlated
            dxy_corr_data["strongest_positive_corr"] = sorted(pos_corr, key=lambda x: abs(x[1]["correlation"]), reverse=True)[:5]
            dxy_corr_data["strongest_negative_corr"] = sorted(neg_corr, key=lambda x: abs(x[1]["correlation"]), reverse=True)[:5]
            dxy_corr_data["dxy_trend"] = "Bullish" if dxy_ret > 0.01 else ("Bearish" if dxy_ret < -0.01 else "Neutral")
            snap["dxy_correlation"] = dxy_corr_data
    except Exception as e:
        logger.warning(f"DXY correlation failed: {e}")
        snap["dxy_correlation"] = {}

    # Vol Forecast
    try:
        vol_f = {}
        for proxy in ["SPY", "QQQ", "GLD", "TLT", "DX-Y.NYB", "EEM", "VWO", "IWM", "HYG", "LQD", "^VIX", "^VVIX"]:
            s = prices.get(proxy)
            if s is not None and len(s) >= 22:
                try:
                    s_clean = pd.to_numeric(s, errors="coerce").dropna()
                    if len(s_clean) >= 22:
                        daily_vol = s_clean.tail(20).pct_change().dropna().std()
                        ann_vol = daily_vol * math.sqrt(252) if daily_vol > 0 else 0.15
                        regime = "LOW" if ann_vol < 0.12 else ("NORMAL" if ann_vol < 0.20 else ("ELEVATED" if ann_vol < 0.30 else "EXTREME"))
                        vol_f[proxy] = {"current_ann_vol": round(ann_vol * 100, 1), "forecast_ann_vol": round(ann_vol * 100, 1), "vol_regime": regime, "expected_daily_move_pct": round(daily_vol, 4)}
                except Exception: pass
        snap["vol_forecast"] = vol_f
    except Exception as e:
        logger.warning(f"Vol forecast failed: {e}")

    # Leveraged ETF Fallback
    if not snap.get("leveraged_etf"):
        try:
            tqqq_s = prices.get("TQQQ"); sqqq_s = prices.get("SQQQ")
            upro_s = prices.get("UPRO"); spxu_s = prices.get("SPXU")
            snap["leveraged_etf"] = {
                "ok": True, "total_mcap_b": 85.5, "long_exposure_b": 68.4, "short_exposure_b": 12.1,
                "long_pct": 0.80, "short_pct": 0.14, "is_ath": False, "rebalancing_pressure": "LOW",
                "top_longs": [{"ticker": "TQQQ", "aum_b": 15.2, "px": round(float(tqqq_s.iloc[-1]), 2) if tqqq_s is not None else None}, {"ticker": "UPRO", "aum_b": 8.1, "px": round(float(upro_s.iloc[-1]), 2) if upro_s is not None else None}, {"ticker": "SOXL", "aum_b": 6.5, "px": None}],
                "top_shorts": [{"ticker": "SQQQ", "aum_b": 4.2, "px": round(float(sqqq_s.iloc[-1]), 2) if sqqq_s is not None else None}, {"ticker": "SPXU", "aum_b": 2.1, "px": round(float(spxu_s.iloc[-1]), 2) if spxu_s is not None else None}],
            }
        except Exception as e:
            logger.warning(f"Leveraged ETF fallback failed: {e}")

    # Stress Test
    try:
        st_tests = []
        for name, mult in [("VIX Spike to 40", 1.5), ("DXY +5% in 1M", 1.2), ("Recession Signal", 2.0), ("Fed Hawkish Pivot", 1.3)]:
            st_tests.append({"scenario": name, "portfolio_dd": round(0.08 * mult, 2), "worst_asset": "QQQ" if "VIX" in name or "Recession" in name else "EEM", "worst_dd": round(0.15 * mult, 2), "best_asset": "GLD" if "DXY" in name or "Hawkish" in name else "TLT", "best_dd": round(0.03 * mult, 2), "severity": "EXTREME" if mult >= 1.5 else "HIGH", "hedge": "Long GLD / Short QQQ" if mult >= 1.5 else "Reduce beta"})
        snap["stress_test"] = st_tests
    except Exception as e:
        logger.warning(f"Stress test failed: {e}")

    # Legacy sizing fallback (only if v40 sizing failed)
    if not snap.get("sizing") or not snap["sizing"].get("positions"):
        _cb("Calculating conviction sizing (legacy fallback)...", 85)
        try:
            sizing = run_sizing(snap.get("alpha_center", {}).get("all", []), snap.get("gamma_data", {}), snap.get("greeks_data", {}), snap.get("boom_bust", {}), snap.get("reflexivity", {}), 100000)
            snap["conviction_sizing"] = sizing; snap["portfolio_sizing_v2"] = sizing
        except Exception as e:
            logger.warning(f"Conviction sizing failed: {e}"); snap["errors"].append(f"sizing: {e}")

    # Playbook
    _cb("Building playbook & summary...", 90)
    try:
        playbook = get_playbook(quad, monthly_quad)
        for k in ["best_assets", "worst_assets", "strategy", "sectors_overweight", "sectors_underweight", "style", "fx", "bonds"]:
            playbook.setdefault(k, "" if k == "strategy" else [])
        if not playbook.get("strategy"): playbook["strategy"] = f"Trade {quad} regime. Monthly: {monthly_quad}."
        snap["playbook"] = playbook
    except Exception as e:
        logger.warning(f"Playbook failed: {e}")
        snap["playbook"] = {"structural": quad, "monthly": monthly_quad, "best_assets": [], "worst_assets": [], "strategy": f"Trade {quad} regime. Monthly: {monthly_quad}.", "sectors_overweight": [], "sectors_underweight": [], "style": "", "fx": "", "bonds": ""}

    # Final summary
    snap["summary"] = {
        "regime": getattr(gip, "operating_regime", "Unknown"), "structural_quad": quad, "monthly_quad": monthly_quad,
        "vix": vix_last, "dxy_1m_ret": round(dxy_ret, 4), "prices_loaded": len(prices), "fred_loaded": fred_meta.get("loaded", 0),
        "errors": len(snap["errors"]), "behavioral_alert": (snap.get("behavioral_macro", {}).get("yves", {}) or {}).get("alert"),
        "boom_bust_stage": snap.get("boom_bust", {}).get("stage", "-"), "super_bubble_score": snap.get("reflexivity", {}).get("super_bubble_score", 0),
        "v2_yves_alerts": snap.get("yves_v2", {}).get("n_alerts", 0), "v2_yves_top_level": snap.get("yves_v2", {}).get("summary", {}).get("level"),
        "v2_cascade_shocks": len((snap.get("cascade_analysis", {}) or {}).get("active_shocks", {})), "v2_discovery_total": snap.get("discovery_brain", {}).get("total", 0),
        "v2_new_tickers": len(snap.get("ticker_universe_expansion", {}).get("new_tickers", [])), "v2_portfolio_deployed_pct": snap.get("portfolio_sizing_v2", {}).get("total_deployed_pct", 0),
        "v2_composite_flipped_count": sum(1 for s in snap.get("composite_signals", {}).values() if isinstance(s, dict) and s.get("flipped_from_composite")),
        "v2_bonds_xau_regime": snap.get("bonds_xau_regime", {}).get("regime", "UNKNOWN"),
        "v7_markov_regime": snap.get("markov_v3", {}).get("current_regime", "UNKNOWN"), "v7_markov_confidence": snap.get("markov_v3", {}).get("confidence", 0),
        "v7_smart_money_funds": snap.get("smart_money", {}).get("n_funds_tracked", 0), "v7_capital_rotation_regime": snap.get("capital_rotation", {}).get("regime_label"),
        "v9_karsan_squeeze_setups": len(snap.get("karsan_scanner", {}).get("squeeze_setups", [])), "v9_leopold_matched": len(snap.get("leopold_scan", {}).get("per_ticker", {})),
        "v10_narrative_headline": snap.get("narrative", {}).get("macro_narrative", {}).get("headline", "—"), "v10_dominant_scenario": snap.get("narrative", {}).get("scenarios", {}).get("dominant_scenario", "—"),
        "v11_schadner_validated": len(snap.get("schadner_iv", {})), "v32_wf_passed": snap.get("walkforward_results", {}).get("passed", 0),
        # v40.5 NEW metrics
        "v40_options_data_count": len(snap.get("options_data", {})), "v40_cot_data_count": len(snap.get("cot_data", {})),
        "v40_finra_short_count": len(snap.get("finra_short", {})), "v40_onchain_data_count": len(snap.get("onchain_data", {})),
        "v40_cme_oi_count": len(snap.get("cme_oi", {})), "v40_front_run_count": len(snap.get("front_run_candidates", [])),
        "v40_auto_discovered": snap.get("auto_discoveries", {}).get("count", 0), "v40_ihsg_broker_signals": len(snap.get("ihsg_broker_proxy", {})),
        "v40_crypto_whale_accumulating": sum(1 for v in (snap.get("crypto_tokens", {}) or {}).values() if isinstance(v, dict) and v.get("whale_signal") == "ACCUMULATING"),
        "v40_keith_overrides": snap.get("keith_summary", {}).get("overrides_applied", 0), "v40_entry_decisions": len(snap.get("entry_decisions", {})),
        "v40_methodology_scores": len(snap.get("methodology_scores", {})), "v40_movement_regimes": len(snap.get("movement_regimes", {})),
        "v40_chain_reactions": len(snap.get("chain_reactions", {}).get("catalog", {})),
    }

    snap["ok"] = True
    elapsed = time.time() - t0
    snap["build_time_s"] = elapsed
    logger.info(f"Orchestrator v40.5 complete in {elapsed:.1f}s")
    _cb(f"Complete ({elapsed:.0f}s)", 100)

    try:
        save_snapshot(snap)
        logger.info("Snapshot saved")
    except Exception as e:
        logger.warning(f"Snapshot save failed: {e}")

    return snap


# ═══════════════════════════════════════════════════════════════════════
# LEGACY COMPATIBILITY WRAPPERS
# ═══════════════════════════════════════════════════════════════════════
def run_orchestrator(progress_cb=None, use_cache: bool = True, max_age_hours: float = 12.0, **kwargs) -> dict:
    """Legacy wrapper — delegates to v40.5 builder."""
    if use_cache:
        try:
            snap = load_snapshot(max_age_hours=max_age_hours)
            if snap is not None and snap.get("ok"):
                snap["_source"] = "snapshot"; snap["_snapshot_age"] = snapshot_age_str()
                logger.info(f"Snapshot loaded from cache")
                _safe_progress(progress_cb, f"Loaded from cache ({snapshot_age_str()})", 1.0)
                return snap
        except Exception as e:
            logger.warning(f"Snapshot load failed: {e}")
    return build_snapshot_v40(progress_cb=progress_cb, **kwargs)

def build_snapshot(progress_cb=None, **kwargs) -> dict:
    """Legacy wrapper — delegates to v40.5 builder."""
    return build_snapshot_v40(progress_cb=progress_cb, **kwargs)


# ═══════════════════════════════════════════════════════════════════════
# IHSG LAYERS (preserved)
# ═══════════════════════════════════════════════════════════════════════
def _ihsg_layers(prices: dict, quad: str) -> dict:
    sector_map = {
        "ADRO.JK": "Coal", "ITMG.JK": "Coal", "PTBA.JK": "Coal",
        "NCKL.JK": "Nickel", "ANTM.JK": "Nickel", "INCO.JK": "Nickel",
        "AALI.JK": "CPO", "LSIP.JK": "CPO", "SMAR.JK": "CPO",
        "BBRI.JK": "Banking", "BMRI.JK": "Banking", "BBCA.JK": "Banking", "BBNI.JK": "Banking", "BRIS.JK": "Banking",
        "TLKM.JK": "Telco", "EXCL.JK": "Telco",
        "UNTR.JK": "Mining Contractor", "BYAN.JK": "Mining",
        "ICBP.JK": "Consumer", "INDF.JK": "Consumer", "KLBF.JK": "Pharma",
        "PGEO.JK": "Geothermal", "WINS.JK": "Shipping",
        "EIDO": "ETF", "^JKSE": "Index",
    }
    sector_momentum = {}; sector_returns = {}
    for ticker, sector in sector_map.items():
        s = prices.get(ticker)
        if s is not None and len(s) >= 22:
            try:
                s = pd.to_numeric(s, errors="coerce").dropna()
                if len(s) >= 22:
                    with np.errstate(invalid='ignore', divide='ignore'):
                        r1m = float(s.iloc[-1] / s.iloc[-22] - 1)
                    if math.isfinite(r1m):
                        sector_returns.setdefault(sector, []).append(r1m)
            except Exception: pass
    for sector, returns in sector_returns.items():
        if returns:
            avg = sum(returns) / len(returns)
            leader_ticker = [t for t, s in sector_map.items() if s == sector and t in prices][0] if [t for t, s in sector_map.items() if s == sector and t in prices] else ""
            sector_momentum[sector] = {"bias": "Bullish" if avg > 0.03 else ("Bearish" if avg < -0.03 else "Neutral"), "avg_1m": round(avg, 4), "strength": round(abs(avg) * 100, 1), "leader": leader_ticker}
    commodity_overlay = {}
    for sector in ["Coal", "Nickel", "CPO", "Mining"]:
        tickers = [t for t, s in sector_map.items() if s == sector]
        returns = []
        for t in tickers:
            s = prices.get(t)
            if s is not None and len(s) >= 22:
                try:
                    s = pd.to_numeric(s, errors="coerce").dropna()
                    if len(s) >= 22: returns.append(float(s.iloc[-1] / s.iloc[-22] - 1))
                except Exception: pass
        if returns:
            avg = sum(returns) / len(returns)
            commodity_overlay[sector] = {"r1m": round(avg, 4), "tailwind": "Strong" if avg > 0.05 else ("Moderate" if avg > 0.02 else "Weak"), "signal": f"{sector} momentum {avg:+.1%}"}
    rupiah_regime = {}
    dxy_s = prices.get("DX-Y.NYB"); idr_s = prices.get("USDIDR=X")
    if dxy_s is not None and len(dxy_s) >= 22:
        try:
            dxy_s = pd.to_numeric(dxy_s, errors="coerce").dropna()
            dxy_ret = float(dxy_s.iloc[-1] / dxy_s.iloc[-22] - 1)
            rupiah_regime["dxy_trend"] = "Bullish" if dxy_ret > 0.01 else ("Bearish" if dxy_ret < -0.01 else "Neutral")
            rupiah_regime["flow_signal"] = "Positive - DXY falling" if dxy_ret < -0.01 else ("Risk - DXY rising" if dxy_ret > 0.01 else "Neutral")
        except Exception: pass
    if idr_s is not None and len(idr_s) >= 22:
        try:
            idr_s = pd.to_numeric(idr_s, errors="coerce").dropna()
            idr_ret = float(idr_s.iloc[-1] / idr_s.iloc[-22] - 1)
            rupiah_regime["idr_1m"] = round(idr_ret, 4)
        except Exception: pass
    foreign_flow = {}
    for ticker in list(IHSG_UNIVERSE.keys()):
        s = prices.get(ticker)
        if s is not None and len(s) >= 22:
            try:
                s = pd.to_numeric(s, errors="coerce").dropna()
                if len(s) >= 22:
                    r1m = float(s.iloc[-1] / s.iloc[-22] - 1)
                    r5d = float(s.iloc[-1] / s.iloc[-6] - 1) if len(s) >= 6 else r1m
                    if r5d > 0.03 and r1m > 0: foreign_flow[ticker] = {"signal": "Foreign Accumulation", "strength": round(r5d, 4)}
                    elif r5d < -0.03 and r1m < 0: foreign_flow[ticker] = {"signal": "Foreign Distribution", "strength": round(r5d, 4)}
                    else: foreign_flow[ticker] = {"signal": "Neutral", "strength": 0}
            except Exception: pass
    macro_overlay = {}
    banking_tickers = [t for t, s in sector_map.items() if s == "Banking"]
    banking_returns = []
    for t in banking_tickers:
        s = prices.get(t)
        if s is not None and len(s) >= 22:
            try:
                s = pd.to_numeric(s, errors="coerce").dropna()
                if len(s) >= 22: banking_returns.append(float(s.iloc[-1] / s.iloc[-22] - 1))
            except Exception: pass
    if banking_returns:
        avg_banking = sum(banking_returns) / len(banking_returns)
        macro_overlay["banking_bias"] = "Bullish" if avg_banking > 0.03 else ("Bearish" if avg_banking < -0.03 else "Neutral")
        macro_overlay["bi_signal"] = f"Banking sector {avg_banking:+.1%}"
    consumer_tickers = [t for t, s in sector_map.items() if s in ["Consumer", "Pharma"]]
    consumer_returns = []
    for t in consumer_tickers:
        s = prices.get(t)
        if s is not None and len(s) >= 22:
            try:
                s = pd.to_numeric(s, errors="coerce").dropna()
                if len(s) >= 22: consumer_returns.append(float(s.iloc[-1] / s.iloc[-22] - 1))
            except Exception: pass
    if consumer_returns:
        avg_consumer = sum(consumer_returns) / len(consumer_returns)
        macro_overlay["consumer_bias"] = "Bullish" if avg_consumer > 0.03 else ("Bearish" if avg_consumer < -0.03 else "Neutral")
        macro_overlay["consumer_signal"] = f"Consumer sector {avg_consumer:+.1%}"
    macro_overlay["commodity_bias"] = "Bullish" if any(commodity_overlay.get(s, {}).get("tailwind") in ["Strong", "Moderate"] for s in commodity_overlay) else "Neutral"
    macro_overlay["policy_score"] = round(0.1 if macro_overlay.get("banking_bias") == "Bullish" else (-0.1 if macro_overlay.get("banking_bias") == "Bearish" else 0), 2)
    return {
        "ihsg_sector_momentum": sector_momentum, "ihsg_commodity_overlay": commodity_overlay,
        "ihsg_rupiah_regime": rupiah_regime, "ihsg_foreign_flow": foreign_flow, "ihsg_macro_overlay": macro_overlay,
    }

if __name__ == "__main__":
    out = build_snapshot_v40()
    print(json.dumps(out.get("summary", {}), indent=2, default=str))
