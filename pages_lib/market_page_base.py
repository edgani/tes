"""market_page_base.py — Generic 2-tab market page (Picks + Front-Run)

Used by US Stocks, Forex, Commodities, Crypto, IHSG with their specific overlays.
"""
import streamlit as st
from components.ticker_card import render_ticker_card, render_action_filter
from components.options_layer import render_options_layer
from components.market_panels import (
    render_cot_panel, render_onchain_panel, render_bandar_panel, render_chain_reaction_panel
)


def render_market_page(
    snap: dict,
    market_key: str,           # 'us_equity', 'forex', 'commodity', 'crypto', 'ihsg'
    title: str,
    icon: str,
    show_options: bool = False,
    show_cot: bool = False,
    show_onchain: bool = False,
    show_bandar: bool = False,
):
    st.title(f"{icon} {title}")
    
    # ── Filter tickers by market ─────────────────────────────────────────
    rr_data = snap.get("risk_range", {}).get("asset_ranges", {})
    sizing_data = snap.get("sizing", {})
    keith_signals = snap.get("keith_signals", {})
    options_map = snap.get("options_data", {})
    cot_map = snap.get("cot_data", {})
    onchain_map = snap.get("onchain_data", {})
    bandar_map = snap.get("ihsg_broker_data", {})
    
    def _market_match(ticker: str) -> bool:
        t = ticker.upper()
        if market_key == "us_equity":
            return not any(s in t for s in [".JK", "=X", "=F", "-USD", "^"])
        elif market_key == "forex":
            return "=X" in t or t in ("DX-Y.NYB", "UUP", "FXE", "FXY", "FXB", "UDN")
        elif market_key == "commodity":
            return "=F" in t or t in ("USO", "GLD", "SLV", "UNG", "CPER", "DBC", "XOP", "OIH")
        elif market_key == "crypto":
            return "-USD" in t and t.split("-")[0] not in ("DX",) or t in ("BTC", "ETH", "SOL")
        elif market_key == "ihsg":
            return ".JK" in t or t == "^JKSE" or t == "EIDO"
        return False
    
    # ── Build per-ticker rows ────────────────────────────────────────────
    rows = []
    for t, rr in rr_data.items():
        if not _market_match(t):
            continue
        if not rr or "px" not in rr:
            continue
        sig = rr.get("signals", {})
        sizing = sizing_data.get(t, {})
        keith = keith_signals.get(t, {})
        rows.append({
            "ticker": t,
            "px": rr.get("px"),
            "phase": rr.get("phase", "NEUTRAL"),
            "action": sig.get("action", "HOLD"),
            "quality": sig.get("quality", "C"),
            "formation": sig.get("formation"),
            "trade_lrr": rr.get("trade", {}).get("lrr"),
            "trade_trr": rr.get("trade", {}).get("trr"),
            "trend_lrr": rr.get("trend", {}).get("lrr"),
            "trend_trr": rr.get("trend", {}).get("trr"),
            "tail_lrr": rr.get("tail", {}).get("lrr"),
            "tail_trr": rr.get("tail", {}).get("trr"),
            "trade_pos_pct": sig.get("trade_position_pct"),
            "dist_to_lrr_pct": sig.get("distance_to_lrr_pct"),
            "dist_to_trr_pct": sig.get("distance_to_trr_pct"),
            "rr_ratio": sig.get("rr_ratio"),
            "recommended_pct": sizing.get("recommended_pct"),
            "quad_fit": sizing.get("quad_fit", {}).get("fit") if isinstance(sizing.get("quad_fit"), dict) else None,
            "keith_trade": keith.get("TRADE") if isinstance(keith, dict) else None,
            "keith_trend": keith.get("TREND") if isinstance(keith, dict) else None,
        })
    
    if not rows:
        st.info(f"No {market_key} tickers in current snapshot. Enable in sidebar Markets settings + Rebuild.")
        return
    
    # ── KPI summary ──────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Tickers", len(rows))
    with c2:
        buy_count = sum(1 for r in rows if r["action"] in ("BUY_DIP", "ADD"))
        st.metric("BUY/ADD", buy_count)
    with c3:
        trim_count = sum(1 for r in rows if r["action"] in ("TRIM", "TRIM_RIP"))
        st.metric("TRIM", trim_count)
    with c4:
        a_grade = sum(1 for r in rows if r["quality"].startswith("A"))
        st.metric("A-grade", a_grade)
    
    st.divider()
    
    # ── 2 TABS ───────────────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["🎯 Picks (Hedgeye-style)", "🔮 Front-Run (Pre-positioning)"])
    
    with tab1:
        _render_picks_tab(rows, snap, market_key, show_options, show_cot, show_onchain, show_bandar,
                          options_map, cot_map, onchain_map, bandar_map)
    
    with tab2:
        _render_frontrun_tab(rows, snap, market_key, show_options, show_cot, show_onchain, show_bandar,
                             options_map, cot_map, onchain_map, bandar_map)


def _render_picks_tab(rows, snap, market_key, show_options, show_cot, show_onchain, show_bandar,
                       options_map, cot_map, onchain_map, bandar_map):
    """Picks tab — Hedgeye-style longs/shorts/monitor."""
    
    # Filter + sort
    sort_by = st.selectbox("Sort by", ["Best R/R", "Distance to LRR", "Conviction (Size)", "Quality"],
                           key=f"sort_picks_{market_key}")
    sort_map = {
        "Best R/R": "rr_ratio",
        "Distance to LRR": "dist_to_lrr_pct",
        "Conviction (Size)": "recommended_pct",
        "Quality": "quality",
    }
    sk = sort_map[sort_by]
    
    try:
        if sk == "quality":
            rows_sorted = sorted(rows, key=lambda x: (x["quality"], -(x.get("rr_ratio", 0) or 0)))
        else:
            rows_sorted = sorted(rows, key=lambda x: -(x.get(sk, 0) or 0))
    except Exception:
        rows_sorted = rows
    
    # Action filter pills
    actions = sorted(set(r["action"] for r in rows_sorted))
    selected_actions = st.multiselect("Action", actions, default=actions, key=f"actions_picks_{market_key}")
    rows_filtered = [r for r in rows_sorted if r["action"] in selected_actions]
    
    # IHSG-only rule: cannot short retail. Convert SHORT actions to WATCH.
    is_ihsg = market_key == "ihsg"
    if is_ihsg:
        for r in rows_filtered:
            if r["action"] in ("SHORT_RIP", "COVER"):
                r["action"] = "WATCH"

    # Sub-tabs: longs / shorts / monitor
    longs = [r for r in rows_filtered if r["action"] in ("BUY_DIP", "ADD")]
    shorts = [] if is_ihsg else [r for r in rows_filtered if r["action"] in ("SHORT_RIP", "COVER")]
    monitor = [r for r in rows_filtered if r["action"] in ("TRIM", "TRIM_RIP", "WATCH", "HOLD")]

    if is_ihsg:
        # IHSG: only Long + Monitor (no Short tab)
        sub1, sub3 = st.tabs([f"🟢 Long ({len(longs)})", f"🟡 Monitor ({len(monitor)})"])
        with sub1:
            for row in longs[:30]:
                _render_ticker_with_overlays(row, snap, market_key, show_options, show_cot, show_onchain, show_bandar,
                                              options_map, cot_map, onchain_map, bandar_map)
        with sub3:
            for row in monitor[:30]:
                _render_ticker_with_overlays(row, snap, market_key, show_options, show_cot, show_onchain, show_bandar,
                                              options_map, cot_map, onchain_map, bandar_map)
        return

    sub1, sub2, sub3 = st.tabs([f"🟢 Long ({len(longs)})", f"🔴 Short ({len(shorts)})", f"🟡 Monitor ({len(monitor)})"])
    
    with sub1:
        for row in longs[:30]:
            _render_ticker_with_overlays(row, snap, market_key, show_options, show_cot, show_onchain, show_bandar,
                                          options_map, cot_map, onchain_map, bandar_map)
    with sub2:
        for row in shorts[:30]:
            _render_ticker_with_overlays(row, snap, market_key, show_options, show_cot, show_onchain, show_bandar,
                                          options_map, cot_map, onchain_map, bandar_map)
    with sub3:
        for row in monitor[:30]:
            _render_ticker_with_overlays(row, snap, market_key, show_options, show_cot, show_onchain, show_bandar,
                                          options_map, cot_map, onchain_map, bandar_map)


def _render_frontrun_tab(rows, snap, market_key, show_options, show_cot, show_onchain, show_bandar,
                         options_map, cot_map, onchain_map, bandar_map):
    """Front-run tab — pre-positioning based on chain reactions."""
    try:
        from engines.chain_reaction_v2 import get_chain_engine
        cre = get_chain_engine()
    except Exception:
        cre = None
    
    if cre is None:
        st.warning("Chain reaction engine unavailable")
        return
    
    # Find active shocks and trace to this market's tickers
    transmissions = snap.get("transmissions", {})
    active = transmissions.get("active_transmissions", []) if isinstance(transmissions, dict) else []
    
    # Ticker set for this market
    market_tickers = set(r["ticker"] for r in rows)
    
    # Filter cascades to ones impacting this market
    frontrun_candidates = []
    for t_active in active:
        driver = t_active.get("driver", "")
        shock = t_active.get("shock_pct", 0)
        for impact in t_active.get("top_impact", []):
            tic = impact.get("ticker")
            if tic in market_tickers:
                frontrun_candidates.append({
                    "ticker": tic,
                    "driver": driver,
                    "shock_pct": shock,
                    "expected_pct": impact.get("expected_pct", 0),
                    "lag_days": impact.get("lag_days", 0),
                    "thesis": impact.get("thesis", ""),
                    "chain": impact.get("chain", ""),
                    "confidence": impact.get("confidence", "MEDIUM"),
                })
    
    if not frontrun_candidates:
        st.info("No active front-run setups for this market. Front-run triggers when a driver moves >3% in 5 days.")
        # Show all available chains for this market
        st.markdown("### 📚 Available Chains")
        cre = get_chain_engine() if cre is None else cre
        for ticker in list(market_tickers)[:20]:
            parents = cre.find_parents_of(ticker)
            if parents:
                with st.expander(f"🔗 {ticker} ({len(parents)} drivers)"):
                    for p in parents:
                        st.caption(f"**{p['parent']}** β={p['beta']} lag {p['lag_days']}d — {p['thesis']}")
        return
    
    # Sort by expected impact magnitude
    frontrun_candidates.sort(key=lambda x: abs(x["expected_pct"]), reverse=True)
    
    st.markdown(f"### 🔮 {len(frontrun_candidates)} Active Front-Run Setups")
    
    for fr in frontrun_candidates[:20]:
        # Find original row data
        row = next((r for r in rows if r["ticker"] == fr["ticker"]), None)
        if not row:
            continue
        
        impact_color = "#3FB950" if fr["expected_pct"] > 0 else "#F85149"
        
        st.markdown(f"""<div style='background:#161B22;border-left:3px solid {impact_color};border-radius:8px;padding:10px;margin:6px 0;'>
            <div style='display:flex;align-items:center;justify-content:space-between;'>
                <div>
                    <span style='font-weight:800;font-size:1rem;color:#E6EDF3;'>{fr['ticker']}</span>
                    <span style='font-size:0.65rem;color:#8B949E;margin-left:8px;'>← {fr['driver']} {fr['shock_pct']:+.2f}%</span>
                </div>
                <div style='color:{impact_color};font-weight:700;font-size:0.9rem;'>
                    Expected: {fr['expected_pct']:+.2f}% in {fr['lag_days']}d
                </div>
            </div>
            <div style='font-size:0.7rem;color:#E6EDF3;margin-top:6px;'>{fr['thesis']}</div>
            <div style='font-size:0.6rem;color:#8B949E;margin-top:4px;'>Chain: {fr['chain']} · Confidence: {fr['confidence']}</div>
        </div>""", unsafe_allow_html=True)
        
        # Render small risk range
        render_ticker_card(row)


def _render_ticker_with_overlays(row, snap, market_key, show_options, show_cot, show_onchain, show_bandar,
                                  options_map, cot_map, onchain_map, bandar_map):
    """Render ticker card + applicable market overlays."""
    render_ticker_card(row)
    
    ticker = row["ticker"]
    if show_options and ticker in options_map:
        with st.expander(f"📊 {ticker} — Options"):
            render_options_layer(ticker, options_map[ticker])
    if show_cot and ticker in cot_map:
        with st.expander(f"📋 {ticker} — COT"):
            render_cot_panel(ticker, cot_map[ticker])
    if show_onchain and ticker in onchain_map:
        with st.expander(f"⛓️ {ticker} — On-Chain"):
            render_onchain_panel(ticker, onchain_map[ticker])
    if show_bandar and ticker in bandar_map:
        with st.expander(f"🏦 {ticker} — Bandar Flow"):
            render_bandar_panel(ticker, bandar_map[ticker])
    
    # Chain reaction lookup (universal)
    try:
        from engines.chain_reaction_v2 import get_chain_engine
        cre = get_chain_engine()
        parents = cre.find_parents_of(ticker)
        if parents:
            with st.expander(f"🔗 {ticker} — Correlation Drivers"):
                render_chain_reaction_panel(ticker, {"parent_chains": parents})
    except Exception:
        pass
