# MacroRegime Pro — S0–S3 Audit Fixes + Confluence Scorer (applied)

This is the full v40 system with the audit fixes merged in-place + one new engine.

## Changed engines
- engines/risk_range_engine.py   — S0-a: main path now delegates to v20.3b (calibrated
                                    realized-vol/IV bands), keeps v39 output shape so all
                                    ~30 downstream consumers work unchanged. Legacy v39
                                    ATR engine kept only as fallback.
- engines/gex_engine.py          — S0-b + S1-c: per-strike IV (skew), spot²·0.01 scaling
                                    + index/equity sign aligned to spotgamma engine,
                                    ratio-based regime (fixes inverted POSITIVE/DEEP bug).
- engines/risk_range_v20.py      — S1-a: phase score anchored to per-duration MA (no more
                                    silent collapse to MA-cross). S2-a: honest in-sample
                                    calibration note. S3-b: true ATR from OHLCV when present.
- engines/charm_proxy_engine.py  — S1-b: real Black-Scholes charm (∂Δ/∂t) instead of theta;
                                    scale-invariant charm-imbalance instead of magic ±5e5.
- engines/gip_engine.py          — S1-d: proxy gate (haircut confidence + warning when FRED
                                    missing → quad is coincident not leading). S2-b: monthly
                                    weights hoisted to named constants w/ overfit warning.
- engines/hedgeye_position_sizing.py — S3-a: VIX buckets 9-19/20-29/29+. S3-c: 6% position
                                    envelope (current_position_bps param + clamp).
- engines/vanna_proxy_engine.py  — S2-c: real price-based skew proxy (downside/upside
                                    semideviation asymmetry) instead of RV term-structure.

## New engine (ELEVATION)
- engines/confluence_scorer.py   — regime-aware multi-engine scorer with HARD-VETO
                                    multiplicative gating. score_ticker() + rank_universe().
                                    Intended consumers: pages_lib/market_page_base.py and
                                    engines/alpha_center_curator.py (NOT yet wired — see below).

## NOT yet wired (your call)
confluence_scorer is built + tested but not yet called by market pages / Alpha Center.
To activate: import rank_universe and feed it the per-ticker engine outputs you already
compute (rr_map, gex_map, vanna_map, charm_map, keith_map).

## Verification done
- Full-tree syntax check (python -m compileall .) → clean across all 116 .py files.
- 8 changed/new engines compiled + behavior smoke-tested (veto gates, envelope, proxy
  gate, charm imbalance, skew sign, risk-range shim shape).
- NOT done: full Streamlit boot (needs full dep stack + FRED/Gemini keys + live server).

---

# SESSION 2 — RESTORE + WIRE PASS (from old macroregime.zip)

The old zip supplied 20 of the 21 modules the v40 refactor had dropped. Restored
(compiled, zero missing cascade-deps, API verified against orchestrator's call sites):
  vix_bucket_engine, vanna_charm_flows, bottleneck_engine, odte_monitor,
  conviction_sizing, news_nlp_engine_v3, odte_enhanced, bottleneck_discovery_v3,
  supply_chain_graph_real, ust_auction_tracker, ihsg_specialist_v38,
  walkforward_backtest_engine, walkforward_engine, signal_decay_engine,
  reflexivity_coefficient, anti_fragility_engine, fractional_kelly_engine,
  bayesian_fusion_engine, duration_hmm_engine, cri_v2_engine.
→ Missing-module imports dropped 21 → 1 (only curated_picks_engine remains; guarded).

IHSG specialist (your primary market) — was double-broken: orchestrator imported a
missing v38 AND called `.analyze(prices)` which no version shipped. Restored v38 + added
a defensive `analyze()` adapter mapping to the real methods (detect_goreng_phase +
get_conglomerate_context + check_indonesia_quad), returning the exact
{goreng_phases, conglomerate_flows, hedgeye_check} shape. Smoke-tested: detects goreng
phases + conglomerate flows, never raises. Data file data/ihsg_conglomerates.json present.

ELEVATION WIRED — confluence_scorer is now called by pages_lib/market_page_base.py:
the picks tab has a new default sort "🎯 Confluence (regime-gated)" that ranks each
market's tickers by the gated score (quad-fit × GEX structure × risk-range timing ×
overlays, hard vetoes). Fully wrapped in try/except → if anything is off it silently
falls back to the existing R/R sort (non-regressive). confluence_scorer is no longer dead.

COT/OI re-audit fixes (session 2): COT forex polarity (USD-base pairs inverted),
OI heatmap proxy scale (% instead of misleading absolute $), GEX wall regression
(position-anchored walls for all-negative equity books).

REMAINING (needs your Streamlit env to runtime-verify; I cannot boot it here):
- First-run smoke of the wired confluence sort + restored engines with live data/keys.
- curated_picks_engine (1 module not in old zip) — still stubbed in alpha_synthesis_v37.
- ihsg_specialist_v39.py is now an unused orphan (harmless); delete if you want.
- Optional: surface the confluence score as a visible column (currently drives sort only).

---

# SESSION 3 — DEEP SCAN (pyflakes) + ARTICLE METHODOLOGY ENCODING

Deep static scan (pyflakes) across engines/components/pages/orchestrator. Findings:
- LIVE bug fixed: pages_lib/_dashboard_legacy.py used `vix_now` via a broken globals()
  check that ALWAYS fell back to 20 → catalyst-monitor VIX row was always "20". Now reads
  real VIX from snap.
- Dead-file latent bugs (NOT live → not fixed, documented): unified_supply_chain_engine.py
  and unified_macro_engine.py have many undefined names; unified_greeks_engine.py (a v40
  consolidation of 11 engines that was never wired in — referenced only in a comment) is
  missing `import math`/`import pandas as pd`. These are imported nowhere so they can't
  crash anything; fix the imports only if you ever revive the consolidated engine.
- ~100 "f-string missing placeholders" — virtually all harmless (wasted f-prefix), not bugs.
- The 20 restored modules: clean (no undefined-name findings).

NEW ENGINE — engines/maker_framework.py (encodes the "goreng menggoreng saham" essay):
  Detects the IDX maker ROADMAP phase (AKUMULASI → MARKUP → DISTRIBUSI) from PRICE+VOLUME
  structure — faithful to the essay's thesis that broker-summary is *semu* and must NOT be
  read day-to-day. Surfaces per-phase tells, the 'looks-cheap' distribution trap, an
  action (ACCUMULATE_WITH_MAKER / RIDE_DONT_CHASE / AVOID_DISTRIBUTION), and a thought-
  process narrative. Broker-summary, IF provided, is used ONLY for wash-circulation FLAGS
  (net≈0 vs gross, top-buyer==top-seller, broker-buy > shares-outstanding, foreign-in-
  small-cap=nominee) — never as a directional signal. Wired into IHSGSpecialistEngine.
  analyze() → result["ihsg_specialist"]["maker_framework"][ticker].
  (Self-audit caught + fixed a real bug pre-ship: deceleration was computed on cumulative
  returns, which mislabeled steady markups as distribution; now uses per-bar pace.)

CROSS-MARKET: the PRICE/VOLUME phase+trap core is market-agnostic and applies to other
thin, maker-driven markets (US small/micro-cap, low-cap crypto). NOT wired there yet —
awaiting your go (the IDX broksum/nominee specifics are IDX-only; the phase logic ports).

---

# SESSION 4 — POSITIONING DATA (forex/commodities/US) audit + 2 new engines

Audit first: most of what was asked ALREADY EXISTS — did NOT rebuild:
- US stocks: options (yfinance_options), GEX (gex_engine, spotgamma_gex_engine), greeks
  (greeks_proxy, options_greeks_engine), charm/vanna, 0DTE — AND dark pool via
  live_data_engine.fetch_finra_short_volume() + attach_finra_signal() + the dark-pool
  block in rich_ticker_card (FINRA off-exchange short volume = the real free dark-pool
  signal; plus a hook for scraped Unusual-Whales dark-pool prints).
- Forex/Commodities: COT fully built (cftc_cot_scraper: fetch_all_reports, get_signal,
  get_crowded_trades, institutional_flow_summary).

Genuine gaps filled (2 new engines, both tested):
- engines/fx_carry_engine.py — per-pair rate-differential (CARRY), the major FX
  positioning driver that was missing. Uses FRED harmonized G10 long rates
  (IRLTLT01<CC>M156N); accepts a pre-fetched fred dict OR self-fetches via FRED_API_KEY,
  else neutral. Returns per-pair carry_diff + 3M trend + bias (STRONG_CARRY_LONG …
  STRONG_CARRY_SHORT, in the pair's direction). Wired: result["fx_carry"] in the snapshot.
- engines/seasonality_engine.py — calendar seasonality from price history (avg return for
  the current month across prior years + hit-rate + bias). Fills the slot the commodity
  structure panel already displays (was defaulted to 2.8). Wired: enriches
  result["structure_data"][ticker] with seasonality_month/avg/hit_rate/bias.

Both wired defensively (try/except, non-regressive). NOT runtime-tested live (no FRED/
network in build env) — verified by compile + logic smoke tests (seasonality detected a
synthetic Dec+/Sep- pattern; carry gave USDJPY STRONG_CARRY_LONG, EURUSD STRONG_CARRY_SHORT).

---

# SESSION 5 — currency bug (from screenshot) + AUTOMATED VALIDATION engine

Screenshot bugs fixed in components/rich_ticker_card.py:
- Currency: IHSG (.JK) stocks were shown with "$" — they trade in RUPIAH. Added _cur_for()
  (Rp for ihsg/.JK, blank for forex, $ else) and applied it to EVERY price spot: Price
  metric, setup body (Posisi/Entry/Target/Stop + TRADE range via build_options_recommendation
  fmt), _entry_narrative (all 8 action branches), compute_optimal_entry, _render_targets,
  and the TRADE/TREND/TAIL LRR/TRR detail captions.
- Honesty: "Institutional flow … — CTA/collar supportive" relabeled "(price-based proxy)"
  (it's analyze_institutional, a price proxy — not real CTA/options/collar data).

NEW — engines/validation_engine.py + run_validation.py (AUTOMATED, no manual judgment):
  • walk_forward() — rolling in-sample/out-of-sample split.
  • validate_parameter()/auto_validate() — sweeps each tunable weight and returns a verdict:
      KEEP (robust OOS edge) / OVERFIT (IS-good, OOS-fails) / FRAGILE (OOS swings on tiny
      param change) / NEUTRAL (param doesn't matter → simplify) / WEAK.
    Verified on synthetic data: a real momentum series → KEEP (OOS Sharpe 3.27); a pure
    random walk → NOT KEEP (FRAGILE) — i.e. it refuses to certify noise as proven.
  • ForwardTestLogger — persists each run's actionable setups and scores them as outcomes
    mature, reporting hit-rate + SCORE CALIBRATION (do higher scores → better outcomes —
    the real test of the scoring weights). Wired into the snapshot: build_snapshot now
    auto-logs BUY_DIP/ADD/SHORT_RIP setups + scores matured ones each run (deduped per day).
  • run_validation.py — one command (`python run_validation.py`) runs the full OOS
    backtest/overfit verdicts on a real multi-market universe and saves data/validation_report.json.

HONEST CONSTRAINTS (physical, not laziness):
  - The real BACKTEST needs price history (yfinance) → runs in YOUR env, not the build
    sandbox (no market-data network here). Engine logic proven on synthetic.
  - The FORWARD TEST tests the FUTURE — it cannot produce results instantly; the logger
    accumulates a real track record over calendar days as the app runs.

---

# SESSION 6 — bottleneck import bug + Treasury liquidity source + REAL transition engine

- engines/bottleneck_discovery_v3.py: used `pd` with pandas imported only locally (line 73)
  -> module-level `import pandas as pd`. Fixed a live module that silently failed at line 158.
  Re-scanned all 20 restored modules: clean.
- engines/treasury_liquidity.py (NEW, free/no-key): US Treasury fiscaldata TGA + NY Fed RRP/SOFR
  + net-liquidity (Fed BS - TGA - RRP) -> RISK_ON/NEUTRAL/RISK_OFF. Wired result["liquidity"].
  Parse logic verified on mock payloads. Fills the stubbed UST tracker conceptually.
- engines/regime_transition_engine.py: REPLACED 18-line broken stub. The orchestrator called it
  with 4 args while the stub took 1 -> TypeError every run -> regime_transition was ALWAYS empty
  (feature dead). New engine = inflection/ripeness detector built from GIP's existing signals
  (monthly vs structural quad, flip_hazard, growth/inflation acceleration, feature ROC drivers):
  stages DORMANT -> BUILDING -> RIPE -> (CONFIRMED). RIPE = leading horizon turned, structural
  not yet = the front-run window. Call-site fixed to pass the gip object. Verified across stages.

---

# SESSION 7 — Quad Decoder panel (why / what-changes / where) + Ricky scenarios per quad

- engines/quad_explainer.py (NEW): explain_quad(gip, transition, narrative_module) → data-driven
  WHY (growth/inflation direction + driver features), WHAT CHANGES IT (the two adjacent-quad
  triggers via quad coordinates), WHERE IT GOES (from regime_transition ripeness stage +
  action hint), per-quad strong/weak playbook + honest caveats (crowding/GEX/divergence/bandar/
  liquidity), and the Ricky2212 narratives matching the current quad OR the transition label
  (e.g. Q3->Q2). Verified end-to-end on the real Q3-structural/Q2-monthly divergence.
- Wired result["quad_explainer"] in orchestrator after regime_transition.
- pages_lib/dashboard.py: _render_quad_explainer panel rendered after the legacy dashboard
  (fully guarded; never breaks the page). Stage badge (RIPE/BUILDING/DORMANT), why, what-changes,
  where-it-goes + action, dual playbook (now vs implied-next), caveat expander, Ricky scenarios.

---

# SESSION 8 — Bias Guard / Perspektif (debiasing layer)

- engines/perspective_engine.py (NEW): bias_guard(quad_explainer, gip, vix) embeds the
  cognitive-debiasing playbook (Kahneman/Tversky + consider-an-alternative) into the macro
  call: STEELMAN the opposite, OUTSIDE-VIEW/base-rate caveat (model confidence = hypothesis
  while weights un-validated), context-tuned ACTIVE-BIAS watchlist (confirmation, overconfidence,
  recency, herding, anchoring, loss-aversion; +panic if VIX>28), and a PRE-MORTEM (likeliest
  reason the call fails). Verified on the Q3->Q2 RIPE call.
- Wired result["perspective"] in orchestrator after quad_explainer; rendered as a collapsible
  "🪞 Bias Guard" panel under the Quad Decoder on the dashboard.
NOTE for user: chain-reaction setups (Front-Run tabs + Themes causal chains) and multi-domain
bottlenecks (Power Grid / Uranium / Defense / Fiscal, not just AI) ALREADY exist in-app.

---

# SESSION 9 — Quad Map (visual): 2x2 GIP grid with position + transition arrow

- pages_lib/dashboard.py: _quad_map_figure(qe) — a Plotly 2x2 Hedgeye GIP map (x=inflation RoC,
  y=growth RoC). Four colored quadrants (Q1 Goldilocks / Q2 Reflation / Q3 Stagflation / Q4
  Deflation), a white "Structural" dot + a cyan "Monthly/leading" dot placed in their quads, and
  a dashed amber arrow toward the implied-next quad when a transition is forming. Rendered at the
  top of the Quad Decoder panel with a plain-language "cara baca" caption. Replaces scattered text
  with one canonical picture tying structural + monthly + transition together.
  Caught + fixed a real plotly bug in testing (deprecated `titlefont` → nested `title.font`).
  Verified via full figure serialization across transition / stable / cross-quad cases.

---

# SESSION 10 — Unified DARK GEX + Risk-Range chart (SpotGamma-style) on ticker cards

- engines/gex_engine.py: YF_OPTIONS return now exposes per-strike data (strikes + gex_by_strike)
  so the chart can draw GEX bars + an aggregate cumulative curve (was computed then discarded).
- components/rich_ticker_card.py: _gex_levels_chart(ticker, px, rr, opts, cur) — one DARK chart on
  a price x-axis combining: GEX-by-strike bars (green +gamma / orange -gamma), aggregate gamma curve
  (secondary y), positive/negative gamma shaded regions split at the gamma flip, put/call walls +
  gamma flip + max pain vertical lines, TRADE/TREND/TAIL bands, and Entry/Target/SL as X-markers.
  Degrades gracefully: no options data → bands + last price + entry/target/SL still drawn (futures-
  proxy/forex/IHSG); nothing usable → returns None. Rendered at the top of each card's detail
  expander with a plain-language "cara baca" caption. Verified via full plotly serialization
  (full / degraded / empty cases).
- Quad map markers already differentiated (circle-open=Structural, X=Monthly) + color — left as is.
NOTE: companion charts (vol skew, put/call ratio, greeks mini, expected move; per-market on-chain /
COT / broker) intentionally deferred — cramming all into one chart would kill the clarity that makes
the SpotGamma reference readable.

---

# SESSION 11 — Companion mini-charts (data-gated) under the GEX chart

components/rich_ticker_card.py — three compact DARK charts rendered in a row below the main
GEX+levels chart in each card's detail expander, each shown ONLY when its data exists:
- _expected_move_chart(px, em%, target, entry) — ±1σ/±2σ cone vs target distance (options tickers).
- _pc_oi_chart(opts) — Put/Call OI bars + P/C ratio in title (options tickers).
- _cot_bar(cot) — non-commercial (specs) vs commercial (hedgers) net positioning (forex/commodities).
Greeks numeric chart skipped (vanna/charm not exposed as numbers; the regime is already on the
main GEX chart). IHSG broker-flow and crypto on-chain charts intentionally NOT built — they need
data the user doesn't have (paid broker API) or that's too sparse; empty shells would look broken.
All verified via full plotly serialization + data-gating (return None when empty).

---

# SESSION 12 — Bandarmetrics (OHLCV) engine + OHLCV loader + IHSG chart

- data/loader.py: load_ohlcv(tickers) — fetches FULL OHLCV+Volume (load_prices kept Close only,
  so volume-based engines couldn't run). Parallel/non-breaking; flattens yfinance MultiIndex.
- engines/bandarmetrics_engine.py (NEW): LPM (cumulative VWAP-delta, EMA), DTE/Real-DTE (ADV),
  Volume Rotation (efficiency green/yellow/red), Intensity (LPM-ROC z-spikes), rule-based Wyckoff
  phase, 0-100 composite + series for charting. From the reverse-engineered formulas. HONEST: phase/
  score are unvalidated heuristics (synthetic test was noisy); foreign-flow + broker clustering need
  IDX broker data the user lacks. Series/formulas are the solid part.
- orchestrator: result["bandarmetrics"] — fetches OHLCV for .JK tickers + runs the engine (defensive).
- components/rich_ticker_card.py: _bandarmetrics_chart — DARK 3-panel (Price+AvgCost / LPM filled /
  Intensity bars), rendered on IHSG cards with an honest "read the pattern, not the raw score" caption.
NOTE: TradingView-API (Mathieu2301) NOT wired — Node.js + ToS/ban risk + untestable here; advised
additive Python tvdatafeed for missing symbols instead of replacing yfinance.

---

# SESSION 13 — Declutter / merge (cards + dashboard) per user visual feedback

- components/rich_ticker_card.py: the GEX chart already draws TRR/LRR bands + walls + flip +
  max pain + entry/target/SL, so the duplicated TEXT was removed:
  · TRR/LRR 3-column numeric block (12 lines) → one compact line ("bands on chart above").
  · Call/Put Wall + Gamma Flip + Max Pain bullet list → removed (drawn on chart); kept the
    Gamma Regime interpretation (what the chart can't say). Applies to ALL market tabs (shared card).
- pages_lib/_dashboard_legacy.py: removed the "PROYEKSI TRANSISI 1M" block — fully superseded by
  the Quad Decoder + Quad Map panel (from→implied quad, ripeness stage, triggers). Verified the
  removed locals (qc/target_q/...) weren't used downstream.
- IHSG bandarmetrics chart (session 12) is already wired in this build — deploy + Rebuild to see it.

---

# SESSION 14 — ROOT CAUSE of "still old code": Alpha Center had a DUPLICATE renderer

The user kept screenshotting Alpha Center, which does NOT use render_rich_ticker — it has its own
card layout (pages_lib/alpha_center.py) + calls render_options_recommendation. So every declutter +
the GEX/companion/bandarmetrics charts (all added to render_rich_ticker) NEVER appeared in Alpha
Center. The market tabs were correct; Alpha Center was stale. Fix:
- components/rich_ticker_card.py: extracted the chart stack into a shared public helper
  render_detail_charts(ticker, rr, snap, market_key, px) — GEX+RiskRange+Entry/Target/SL chart +
  companion mini-charts + IHSG bandarmetrics. render_rich_ticker now calls it (no behavior change);
  Alpha Center now calls it too → identical visual treatment, no future drift.
- pages_lib/alpha_center.py: calls render_detail_charts after the options report; condensed its own
  "TRR/LRR v20.3b" 3-line block to one compact line (chart shows the bands).
- app.py: sidebar now shows a BUILD STAMP ("v40 · build 2026-06-02-s14 …") so the user can confirm
  at a glance whether the deployed app is actually running the latest code.

---

# SESSION 15 — Bandarmetrics v2 (A/D-based) + wired into IHSG filter + validation script

- engines/bandarmetrics_engine.py — rebuilt the core on battle-tested accumulation/distribution
  indicators (the fragile custom VWAP-delta LPM is kept only as a secondary line):
  · A/D Line (cumulative Money-Flow-Volume), OBV, Chaikin Money Flow (bounded −1..+1).
  · Divergence detector: price-slope vs ADL-slope → BULLISH_DIV (price↓ + A/D↑ = silent
    accumulation), BEARISH_DIV, ALIGNED_UP/DOWN, FLAT.
  · phase + score now driven by divergence + CMF + A/D slope (robust). Synthetic test now cleanly
    separates accumulation (BULLISH_DIV, score 95) from distribution (CMF −0.6, score 28) — v1 gave
    NEUTRAL for everything.
  · signal_adjustment(bm) → −1..+1 nudge for the pick ranking.
- pages_lib/market_page_base.py — IHSG confluence score now folds in bandarmetrics signal_adjustment
  (±12 pts), so accumulation/divergence raises a ticker's rank and distribution lowers it (wired into
  the actual filter/sort, not just display).
- components/rich_ticker_card.py — bandarmetrics chart upgraded to v2 panels: Price / A/D Line
  (accumulation, filled) / Chaikin Money Flow (signed bars); caption shows divergence + CMF.
- validate_bandarmetrics.py (NEW, repo root) — walk-forward (NO lookahead): computes the signal using
  only data up to T, measures forward N-day return, aggregates avg/median/hit-rate by divergence
  regime + score tier + phase, plus Spearman/Pearson and a verdict (does BULLISH_DIV / high-score
  actually beat BEARISH_DIV / low-score?). Run in YOUR env (needs network); writes
  data/bandarmetrics_validation.json. THIS is the accuracy gate — phase/score stay "unvalidated"
  until this shows a real edge.

---

# SESSION 16 — Ignition detector + foreign-flow interface + compact dashboard

Reverse-engineered from the user's 4 real bandarmetrics.com screenshots (KETR/BBCA/EURO/MSIN). KEY
FINDING: in the "mystery rips" (EURO 10×, MSIN spike) the signal that caught the move was the
FOREIGN FLOW line + foreign participation %, NOT the LPM — and foreign flow needs IDX Type-F broker
data we don't have. Our OHLCV LPM was negative/useless in both. So the gap is DATA, not formula; and
no OHLCV metric can read acquisition/insider INTENT (only the footprint).

- engines/bandarmetrics_engine.py:
  · detect_ignition(df) — OHLCV regime-break / "ignition" detector (volume + range/ATR expansion +
    breakout from base + momentum acceleration → score 0-100). Verified on synthetic: fires score
    72-100 at breakout ONSET, 0 before, decays once mature. Honest framing: flags "abnormal activity,
    investigate the catalyst" — does NOT claim to know why.
  · foreign_flow_metrics(foreign, price) — INTERFACE for IDX Type-F foreign net-flow (the signal that
    actually caught EURO/MSIN). Computes cumulative FF + slope + FF↔price divergence
    (FOREIGN_ACCUM_DIV = price down + foreign buying). Returns available=False when no data (degrades).
  · compute() now returns ignition + foreign_flow; signal_adjustment() folds in ignition (amplifies a
    bullish read) + real foreign-flow divergence when Type-F data is plugged in.
- components/rich_ticker_card.py: bandarmetrics caption now shows a 🚨 IGNITION badge + signals, and a
  note that Foreign Flow needs Type-F data.
- pages_lib/dashboard.py: quad map height 300→230; Quad Decoder playbook + Ricky scenarios moved into
  a collapsed expander → dashboard much shorter (full 1-frame still needs a tabs restructure or content
  cuts — flagged to user).

---

# SESSION 17 — Hidden-accumulation filter (all markets) + dashboard tabs (1-frame) + card merge

- engines/bandarmetrics_engine.py: detect_stealth_accumulation() — HIDDEN accumulation detector
  (A/D rising + CMF>0 + price flat/down + not-yet-ignited = money in while price suppressed). Verified
  on synthetic: stealth score 82/is_stealth=True vs boring-sideways 57/False. Folded into compute()
  output + signal_adjustment (boost).
- orchestrator.py: bandarmetrics now computed for the FULL universe (was IHSG-only) so the filter
  works on every market tab. (Extra OHLCV fetch at build time — defensive.)
- pages_lib/market_page_base.py: bandarmetrics rank-injection now applies to ALL markets (was ihsg
  only); added a "🤫 Hidden Accumulation" sort option (ranks by stealth score); tags is_stealth/
  ignition on items.
- components/rich_ticker_card.py: bandarmetrics chart now shows for ALL markets (was ihsg-only);
  caption surfaces 🤫 HIDDEN ACCUMULATION + 🚨 IGNITION badges. Cara-masuk position lines condensed
  (dropped the entry/target/stop numbers already shown above + on the chart; kept style guidance).
- pages_lib/dashboard.py: dashboard wrapped in 3 TABS (📊 Snapshot / 🧭 Quad Decoder / 🪞 Bias Guard)
  so only one section renders at a time → fits one frame. Quad explainer gets in_tab flag (skips
  divider/heading + avoids double-rendering the bias guard).

---

# SESSION 18 — Blueprint pass 1: Quad Map 3-horizon + Themes playbook-per-quad

Per the user's full layout blueprint. Doing it in tested passes (can't verify render blind).
- pages_lib/dashboard.py: Quad Map now plots THREE horizons — Structural (○ white), Monthly (✕ cyan),
  Global/50-country (◇ gold) — with deterministic offsets so co-located markers stay visible, plus the
  transition arrow toward implied-next quad. Quad Decoder tab gained a Global KPI column + next-quad in
  the transition badge; caption rewritten to explain all three horizons. Verified via serialization
  (3 markers + arrow; all-same-quad offset case).
- pages_lib/themes.py: added "Playbook per Quad" — all 4 GIP quads (strong/weak) in a 4-col grid with
  the current structural/monthly quad highlighted. (Macro narrative, active scenarios, permanent themes,
  next-quad playbook were already present.)
REMAINING blueprint (next tested passes): dashboard block merges (Tier1+AssetPulse, BoomBust+Crash),
single-block reorg of ticker cards per market, per-market Front-Run tabs. Data-limited pieces (OI
heatmap for forex/IHSG = no listed options in yfinance; COT = latest only; on-chain = sparse; dealer
positioning = proxy) will populate where data exists.

---

# SESSION 19 — Bandarmetrics → real BM look (candlesticks, IHSG-only) + dashboard declutter

- engines/bandarmetrics_engine.py: series now exposes OHLC + volume + rotation so the chart can be
  candlestick-based.
- components/rich_ticker_card.py: _bandarmetrics_chart rebuilt in the real bandarmetrics.com style
  (attachment 4) — candlesticks + LPM line overlay (secondary axis, teal) + Intensity panel (purple) +
  Vol Rotation panel (green/yellow/red). Caption trimmed. Chart is IHSG-ONLY again (per user); other
  markets no longer fetch/show bandarmetrics.
- orchestrator.py: bandarmetrics fetch reverted to .JK tickers only.
- pages_lib/dashboard.py: removed the tabs; dashboard renders as one flow with the Quad Decoder block
  (3-horizon) in it. Bias Guard panel removed from the dashboard (not in spec; engine still runs).
- pages_lib/_dashboard_legacy.py: removed Deep Technical + v39 ALPHA build-info panels (not in spec;
  engines still compute in background).
REMAINING (next passes, big blind UI): merge dashboard blocks into single panels (Tier1+AssetPulse;
Quad+Catalyst; BoomBust+Crash) for true 1-frame; aggressive ticker-card cleanup (remove everything not
in each tab's spec) per market.

---

# SESSION 20 — Ticker cards consolidated to ONE block + dashboard quad-first (per annotated screenshots)

TICKER CARDS (market tabs — components/rich_ticker_card.py::render_rich_ticker):
- REMOVED: signal boxes (Signal Strength/Phase/Quality/Hurst/Gamma), the Quality/Phase/Formation caption,
  Accumulation Readiness line, the whole "Detail tambahan" expander (TRR/LRR text, phase/Trending text,
  verbose options/greeks, MM positioning, duplicate COT, OI-heatmap proxy walls, correlation drivers).
- KEPT + MERGED into one block: header (ticker·price·action) → setup box (render_options_recommendation,
  which already carries Posisi/Entry/Target/Stop/Cara-masuk spot+leverage/Dealer/Vanna-charm/Dark-pool/COT)
  → GEX+RiskRange+Entry/Target/SL chart (render_detail_charts; bandarmetrics candlestick for IHSG).
- NEW _render_block1_extras: compact date-based Vanna/Charm OPEX window (equity+crypto) + On-Chain (crypto),
  folded into the same block. OI heatmap omitted for FX/IHSG (no listed options; proxy walls were misleading).

ALPHA CENTER (pages_lib/alpha_center.py):
- REMOVED from card: star rating, monopoly caption, "→ TAIL TRR" metric box, potential caption,
  "Alpha Score N · factors" line, Sources line, Entry/Conviction prose, Readiness line, and the
  TRR/LRR text + trim-zone reason in the detail columns.
- Block 1 = header + setup box + chart. Block 2 = Thesis + why-bottleneck + Correlations + Catalysts +
  Risk + 5-Layer Filter (unchanged).

DASHBOARD (pages_lib/dashboard.py + _dashboard_legacy.py):
- Quad Decoder now renders FIRST (top) — it's the headline macro read, no longer buried at the bottom.
- Removed the redundant STRUCTURAL/MONTHLY/MARKOV/GLOBAL quad row from the Tier1Alpha box (it now lives
  in the Quad Decoder up top).
- Simplified the quad explanation (condensed the "what changes" triggers into one inline line).

REMAINING: dashboard block-MERGES into single panels (Tier1+AssetPulse; BoomBust+Crash) for true 1-frame.
