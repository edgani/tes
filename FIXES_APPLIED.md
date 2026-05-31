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
