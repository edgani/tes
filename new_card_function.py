def render_ticker_card_v4(row, expanded=False):
    """Redesigned ticker card v41 — Multi-Target Trade Plan + Visual Entry Bar + Thesis + Checklist."""
    ticker = row.get("ticker", "?")
    px = row.get("price", 0)
    direction = row.get("direction", "NEUTRAL")
    grade = row.get("grade", "C")
    rr_val = row.get("rr", 0)
    entry = row.get("entry")
    t1 = row.get("target_1")
    t2 = row.get("target_2")
    stop = row.get("stop")
    trade_l = row.get("trade_low")
    trade_r = row.get("trade_top")
    trend_top = row.get("trend_top")
    tail_top = row.get("tail_top")
    market_type = row.get("market_type", "us_equity")
    snap_local = st.session_state.get("snap")
    options = row.get("options", {})

    formation = row.get("formation", "NEUTRAL")
    setup_valid = row.get("setup_valid", True)
    risk_pct = row.get("risk_pct", 0)
    chase_status = row.get("chase_status", "NEUTRAL")
    chase_text = row.get("chase_text", "")
    chase_color = row.get("chase_color", "#8B949E")
    confluence = row.get("confluence", {})

    # ── Multi-Target: T3 from tail_top ──
    t3 = row.get("target_3") or tail_top

    # Timelines
    t1_time = "1-4w"
    t2_time = "1-3m"
    t3_time = "3-6m+"

    dir_kind = "long" if "LONG" in direction else "short" if "SHORT" in direction else "neut"
    dir_label = "LONG" if "LONG" in direction else "SHORT"
    grade_kind = grade.lower().replace("+", "")

    # ── Build badges ──
    badges = ""
    ks = row.get("keith_sync", {})
    if ks and isinstance(ks, dict) and ks.get("override"):
        kt = ks.get("keith_trade", "BEARISH")
        kcolor = "#F85149" if kt == "BEARISH" else "#3FB950"
        badges += f'<span style="background:{kcolor}22;color:{kcolor};padding:2px 8px;border-radius:12px;font-size:0.65rem;font-weight:700;border:1px solid {kcolor}50;letter-spacing:0.3px;">🎙️ KEITH {kt[:4]}</span>'
    badges += _badge_html(dir_label, dir_kind)
    badges += _badge_html(grade, grade_kind)
    if formation == "BULLISH":
        badges += _badge_html("📈 Bull", "long")
    elif formation == "BEARISH":
        badges += _badge_html("📉 Bear", "short")
    elif formation == "OVERSOLD":
        badges += _badge_html("📉 Oversold", "long")
    elif formation == "OVERBOUGHT":
        badges += _badge_html("📈 Overbought", "short")
    if not setup_valid:
        badges += _badge_html("🚫 INVALID", "short")
    if chase_status == "CHASE":
        badges += _badge_html("🏃 CHASE", "chase")
    elif chase_status == "WAIT":
        badges += _badge_html("⏳ WAIT", "wait")
    elif chase_status == "AVOID":
        badges += _badge_html("🚫 AVOID", "short")

    # ── Price change + Sparkline ──
    r1m = row.get("r20d")
    chg_pct = r1m * 100 if r1m is not None else 0
    chg_color = "#3FB950" if chg_pct >= 0 else "#F85149"
    chg_sign = "+" if chg_pct >= 0 else ""

    spark_html = ""
    if snap_local and snap_local.get("prices") and ticker in snap_local["prices"]:
        spark_html = _sparkline_html(snap_local["prices"][ticker], width=80, height=22, bars=16)

    # ── Status banner ──
    status_banner = ""
    if ks and isinstance(ks, dict) and ks.get("override"):
        kt = ks.get("keith_trade", "BEARISH")
        status_banner = f'<div class="hy-status-pill banner-avoid">🚫 AVOID — Keith {kt.title()} Override</div>'
    elif not setup_valid:
        status_banner = f'<div class="hy-status-pill banner-avoid">🚫 INVALID — Stop too tight / Risk &lt; min</div>'
    elif chase_status == "CHASE":
        if row.get("breakout_note"):
            status_banner = f'<div class="hy-status-pill banner-chase">{row["breakout_note"][:80]}</div>'
        else:
            status_banner = f'<div class="hy-status-pill banner-chase">🏃 CHASE — Ready to enter</div>'
    elif chase_status == "WAIT":
        if row.get("breakdown_note"):
            status_banner = f'<div class="hy-status-pill banner-avoid">{row["breakdown_note"][:80]}</div>'
        else:
            status_banner = f'<div class="hy-status-pill banner-wait">⏳ WAIT — Pullback needed</div>'
    elif chase_status == "AVOID":
        status_banner = f'<div class="hy-status-pill banner-avoid">🚫 AVOID — Setup broken</div>'
    else:
        status_banner = f'<div class="hy-status-pill banner-hold">⏸ HOLD — Monitor</div>'

    # ── Assemble compact card header ──
    card_html = (
        f'<div class="hy-card">'
        f'<div class="hy-header">'
        f'<div class="hy-symbol">{ticker}</div>'
        f'<div style="display:flex;align-items:center;gap:8px;">'
        f'<div class="hy-price">{_ffm(px, market_type)}</div>'
        f'<div style="font-size:0.72rem;color:{chg_color};font-weight:700;">{chg_sign}{chg_pct:.1f}%</div>'
        f'{spark_html}'
        f'</div>'
        f'<div class="hy-badges">{badges}</div>'
        f'</div>'
        f'<div class="hy-status-bar">{status_banner}</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════
    # 📊 TRADE PLAN (expanded by default — THE KEY PANEL)
    # ═══════════════════════════════════════════════════════════
    with st.expander("📊 TRADE PLAN", expanded=True):
        # ── Multi-target grid: Entry | Stop | T1 | T2 ──
        t1_rr = round(abs(t1 - entry) / abs(entry - stop), 1) if t1 and entry and stop and abs(entry - stop) > 0 else 0
        t2_rr = round(abs(t2 - entry) / abs(entry - stop), 1) if t2 and entry and stop and abs(entry - stop) > 0 else 0
        t3_rr = round(abs(t3 - entry) / abs(entry - stop), 1) if t3 and entry and stop and abs(entry - stop) > 0 else 0

        plan_html = '<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1fr;gap:6px;margin-bottom:10px;">'
        # Entry
        plan_html += f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:8px;text-align:center;">'
        plan_html += f'<div style="font-size:0.55rem;color:#8B949E;text-transform:uppercase;font-weight:600;margin-bottom:4px;">🎯 Entry Zone</div>'
        plan_html += f'<div style="font-size:0.85rem;font-weight:700;color:#58A6FF;font-variant-numeric:tabular-nums;">{_ffm(entry, market_type)}</div>'
        plan_html += f'</div>'
        # Stop
        plan_html += f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:8px;text-align:center;">'
        plan_html += f'<div style="font-size:0.55rem;color:#8B949E;text-transform:uppercase;font-weight:600;margin-bottom:4px;">🛑 Stop Loss</div>'
        plan_html += f'<div style="font-size:0.85rem;font-weight:700;color:#F85149;font-variant-numeric:tabular-nums;">{_ffm(stop, market_type)}</div>'
        plan_html += f'<div style="font-size:0.55rem;color:#F85149;margin-top:2px;">Risk {risk_pct:.1f}%</div>'
        plan_html += f'</div>'
        # T1
        plan_html += f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:8px;text-align:center;">'
        plan_html += f'<div style="font-size:0.55rem;color:#8B949E;text-transform:uppercase;font-weight:600;margin-bottom:4px;">🥇 T1 (Swing)</div>'
        plan_html += f'<div style="font-size:0.85rem;font-weight:700;color:#3FB950;font-variant-numeric:tabular-nums;">{_ffm(t1, market_type)}</div>'
        plan_html += f'<div style="font-size:0.55rem;color:#3FB950;margin-top:2px;">RR {t1_rr:.1f}x · {t1_time}</div>'
        plan_html += f'</div>'
        # T2
        plan_html += f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:8px;text-align:center;">'
        plan_html += f'<div style="font-size:0.55rem;color:#8B949E;text-transform:uppercase;font-weight:600;margin-bottom:4px;">🥈 T2 (Trend)</div>'
        plan_html += f'<div style="font-size:0.85rem;font-weight:700;color:#2EA043;font-variant-numeric:tabular-nums;">{_ffm(t2, market_type)}</div>'
        plan_html += f'<div style="font-size:0.55rem;color:#2EA043;margin-top:2px;">RR {t2_rr:.1f}x · {t2_time}</div>'
        plan_html += f'</div>'
        # T3
        plan_html += f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:8px;text-align:center;">'
        plan_html += f'<div style="font-size:0.55rem;color:#8B949E;text-transform:uppercase;font-weight:600;margin-bottom:4px;">🥉 T3 (Tail)</div>'
        plan_html += f'<div style="font-size:0.85rem;font-weight:700;color:#238636;font-variant-numeric:tabular-nums;">{_ffm(t3, market_type)}</div>'
        plan_html += f'<div style="font-size:0.55rem;color:#238636;margin-top:2px;">RR {t3_rr:.1f}x · {t3_time}</div>'
        plan_html += f'</div>'
        plan_html += '</div>'
        st.markdown(plan_html, unsafe_allow_html=True)

        # ── Visual Entry Zone Bar ──
        entry_bar_html = _build_entry_zone_bar(px, entry, stop, t1, t2, t3, market_type)
        st.markdown(entry_bar_html, unsafe_allow_html=True)

        # ── THESIS: Why this trade ──
        thesis_items = _build_thesis_items(row, market_type)
        thesis_html = '<div style="background:#0D1117;border:1px solid #21262D;border-radius:8px;padding:10px 12px;margin:8px 0;">'
        thesis_html += '<div style="font-size:0.6rem;color:#58A6FF;text-transform:uppercase;font-weight:600;margin-bottom:8px;letter-spacing:0.5px;">🎯 THESIS: Why This Position</div>'
        for icon, text, color in thesis_items:
            thesis_html += f'<div style="display:flex;align-items:flex-start;gap:6px;margin-bottom:5px;padding:3px 0;border-bottom:1px solid #21262D;">'
            thesis_html += f'<span style="font-size:0.75rem;line-height:1.3;flex-shrink:0;">{icon}</span>'
            thesis_html += f'<span style="font-size:0.7rem;color:#E6EDF3;line-height:1.4;">{text}</span>'
            thesis_html += f'</div>'
        thesis_html += '</div>'
        st.markdown(thesis_html, unsafe_allow_html=True)

        # ── EXECUTION CHECKLIST ──
        checklist_items = _build_execution_checklist(row, px, entry, stop, t1, t2, rr_val, chase_status)
        checklist_html = '<div style="background:#0D1117;border:1px solid #21262D;border-radius:8px;padding:10px 12px;margin:8px 0;">'
        checklist_html += '<div style="font-size:0.6rem;color:#D29922;text-transform:uppercase;font-weight:600;margin-bottom:8px;letter-spacing:0.5px;">📋 EXECUTION CHECKLIST</div>'
        for icon, text in checklist_items:
            checklist_html += f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;font-size:0.68rem;color:#E6EDF3;">{icon} {text}</div>'
        checklist_html += '</div>'
        st.markdown(checklist_html, unsafe_allow_html=True)

        # ── Phase + Formation row ──
        phase_parts = []
        if snap_local:
            ar = snap_local.get("risk_ranges", {}).get("asset_ranges", {})
            if ticker in ar and isinstance(ar[ticker], dict):
                trade_data = ar[ticker].get("trade", {})
                trend_data = ar[ticker].get("trend", {})
                if trade_data and trend_data:
                    trade_lrr = trade_data.get("lrr")
                    trade_trr = trade_data.get("trr")
                    trend_lrr = trend_data.get("lrr")
                    trend_trr = trend_data.get("trr")
                    if all(v is not None for v in [trade_lrr, trade_trr, trend_lrr, trend_trr]):
                        if float(px) > float(trend_trr):
                            phase_parts.append(f'<span style="color:#3FB950;font-weight:700;">📈 TREND (Above Trend Top)</span>')
                        elif float(px) < float(trend_lrr):
                            phase_parts.append(f'<span style="color:#F85149;font-weight:700;">📉 TREND (Below Trend Low)</span>')
                        elif float(px) > float(trade_trr):
                            phase_parts.append(f'<span style="color:#D29922;font-weight:700;">⚠️ TRADE (Above Trade Top)</span>')
                        elif float(px) < float(trade_lrr):
                            phase_parts.append(f'<span style="color:#3FB950;font-weight:700;">📉 TRADE (Below Trade Low — Oversold)</span>')
                        else:
                            phase_parts.append(f'<span style="color:#8B949E;font-weight:700;">⬜ TRADE (Inside Range)</span>')
        if formation == "BULLISH":
            phase_parts.append(f'<span style="color:#3FB950;">📈 Formation: Bullish</span>')
        elif formation == "BEARISH":
            phase_parts.append(f'<span style="color:#F85149;">📉 Formation: Bearish</span>')
        elif formation == "OVERSOLD":
            phase_parts.append(f'<span style="color:#3FB950;">📉 Formation: Oversold</span>')
        elif formation == "OVERBOUGHT":
            phase_parts.append(f'<span style="color:#F85149;">📈 Formation: Overbought</span>')
        if phase_parts:
            st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:8px;font-size:0.7rem;margin:6px 0;">{" · ".join(phase_parts)}</div>', unsafe_allow_html=True)

        # ── Composite signal ──
        conv = row.get("entry_convergence")
        if conv and isinstance(conv, dict):
            conv_signal = conv.get("signal", "—")
            conv_conf = conv.get("confidence", 0)
            conv_color = "#3FB950" if conv_signal == "BUY" else "#F85149" if conv_signal == "SELL" else "#D29922" if conv_signal == "HOLD" else "#8B949E"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;font-size:0.7rem;margin:4px 0;">'
                f'<span style="background:{conv_color}18;color:{conv_color};padding:2px 8px;border-radius:4px;font-size:0.7rem;font-weight:700;border:1px solid {conv_color}40;">{conv_signal}</span>'
                f'<span style="color:#8B949E;">Composite Signal · Confidence <b style="color:{conv_color};">{conv_conf:.0f}%</b></span></div>',
                unsafe_allow_html=True)

        # ── Key news ──
        if row.get("news_headline"):
            st.markdown(f'<div style="font-size:0.72rem;color:#58A6FF;margin-top:4px;">📰 {row.get("news_headline")[:160]}</div>', unsafe_allow_html=True)

        # ── Setup validity note ──
        if not setup_valid:
            setup_note = row.get("setup_note", "")
            st.markdown(f'<div style="font-size:0.72rem;color:#F85149;font-weight:700;margin:4px 0;">🚫 {setup_note}</div>', unsafe_allow_html=True)

        # ── CHASE/WAIT banner ──
        if chase_text:
            st.markdown(
                f'<div style="background:{chase_color}15;border:1px solid {chase_color}50;border-radius:8px;padding:6px 10px;margin:6px 0;font-size:0.72rem;color:{chase_color};font-weight:700;">'
                f'{chase_text}</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════
    # ⚙️ BACKGROUND DATA (collapsed by default)
    # ═══════════════════════════════════════════════════════════
    with st.expander("⚙️ Background Data", expanded=False):
        # Proxy warning
        if options.get("source") == "PROXY" and market_type != "ihsg":
            st.markdown(
                '<div style="background:#F8514918;border:1px solid #F8514940;border-radius:4px;padding:4px 8px;margin:4px 0;font-size:0.6rem;color:#F85149;font-weight:700;">'
                '⚠️ PROXY: Options data estimated from price action. NOT real market data.</div>', unsafe_allow_html=True)

        # ── Alpha Thesis ──
        alpha_thesis = row.get("alpha_thesis", "")
        alpha_src = row.get("alpha_source", "")
        if alpha_thesis:
            src_emoji = {"bottleneck":"🚧","front_run":"🔮","leopold":"🏗️","karsan_squeeze":"📊","karsan_convexity":"📐","coatue":"💱"}.get(alpha_src,"⚡")
            st.markdown(
                f'<div class="alpha-thesis-card">'
                f'<div class="alpha-thesis-title">{src_emoji} {alpha_src.replace("_"," ").title()} Thesis</div>'
                f'<div class="alpha-thesis-sub">{alpha_thesis}</div>'
                f'</div>', unsafe_allow_html=True)

        # ── Simulation Panel ──
        sim = row.get("simulation")
        if sim:
            score = sim.get("robustness_score", 0)
            score_c = "#3FB950" if score >= 80 else "#D29922" if score >= 65 else "#F85149"
            sim_html = f'<div class="ts-panel" style="border-color: {score_c}40; margin-bottom: 8px;">'
            sim_html += f'<div class="ts-panel-title">🎲 Monte Carlo Simulation (100 runs)</div>'
            sim_html += f'<div class="ts-grid-4">'
            sim_html += f'<div class="ts-stat"><div class="ts-stat-label">Robustness</div><div class="ts-stat-value" style="color:{score_c};">{score:.0f}/100</div></div>'
            sim_html += f'<div class="ts-stat"><div class="ts-stat-label">Win Rate</div><div class="ts-stat-value" style="color:#3FB950;">{sim.get("win_rate",0):.0f}%</div></div>'
            sim_html += f'<div class="ts-stat"><div class="ts-stat-label">Exp Return</div><div class="ts-stat-value" style="color:#E6EDF3;">{sim.get("exp_return_pct",0):+.1f}%</div></div>'
            sim_html += f'<div class="ts-stat"><div class="ts-stat-label">Sharpe-like</div><div class="ts-stat-value" style="color:#8B949E;">{sim.get("sharpe_like",0):.2f}</div></div>'
            sim_html += f'</div></div>'
            st.markdown(sim_html, unsafe_allow_html=True)

        # ── Gatekeeper Status ──
        gk = row.get("gatekeeper", {})
        if gk and isinstance(gk, dict):
            gk_status = gk.get("gate_status", "—")
            gk_score = gk.get("combined_score", 0)
            gk_color = "#3FB950" if gk_status == "PASS" else "#D29922" if gk_status == "MARGINAL" else "#F85149" if gk_status == "FAIL" else "#8B949E"
            gk_html = f'<div class="ts-panel" style="border-color: {gk_color}30; margin-bottom: 8px;">'
            gk_html += f'<div class="ts-panel-title">🛡️ Alpha Gatekeeper (8 Gates)</div>'
            gk_html += f'<span style="background:{gk_color}18;color:{gk_color};padding:3px 10px;border-radius:6px;font-size:0.75rem;font-weight:700;border:1px solid {gk_color}40;">{gk_status}</span>'
            gk_html += f' <span style="font-size:0.7rem;color:#8B949E;">Score <b style="color:{gk_color};">{gk_score:.1f}</b></span>'
            gk_html += f'</div>'
            st.markdown(gk_html, unsafe_allow_html=True)

        # ── Walkforward Status ──
        wf = row.get("walkforward", {})
        if wf and isinstance(wf, dict):
            wf_score = wf.get("combined_gate_score", 0)
            wf_status = wf.get("gate_status", "—")
            wf_color = "#3FB950" if wf_status == "PASS" else "#D29922" if wf_status == "MARGINAL" else "#F85149"
            wf_html = f'<div class="ts-panel" style="border-color: {wf_color}30; margin-bottom: 8px;">'
            wf_html += f'<div class="ts-panel-title">🎲 Walkforward Backtest (MC 100x)</div>'
            wf_html += f'<span style="background:{wf_color}18;color:{wf_color};padding:3px 10px;border-radius:6px;font-size:0.75rem;font-weight:700;border:1px solid {wf_color}40;">{wf_status}</span>'
            wf_html += f' <span style="font-size:0.7rem;color:#8B949E;">Gate Score <b style="color:{wf_color};">{wf_score:.1f}</b></span>'
            wf_html += f'</div>'
            st.markdown(wf_html, unsafe_allow_html=True)

        # ── Hedgeye Position Sizing ──
        hp = row.get("hedgeye_size")
        if hp and isinstance(hp, dict):
            hp_pct = hp.get("size_pct", 0)
            hp_dollar = hp.get("dollar_size", 0)
            hp_mode = hp.get("mode", "—")
            hp_conv = hp.get("conviction", 0)
            hp_color = "#3FB950" if hp_pct >= 0.04 else "#D29922" if hp_pct >= 0.02 else "#8B949E"
            hp_html = f'<div class="ts-panel" style="border-color: {hp_color}30; margin-bottom: 8px;">'
            hp_html += f'<div class="ts-panel-title">💰 Hedgeye Position Sizing</div>'
            hp_html += f'<div class="ts-grid-4">'
            hp_html += f'<div class="ts-stat"><div class="ts-stat-label">Size %</div><div class="ts-stat-value" style="color:{hp_color};">{hp_pct:.2%}</div></div>'
            hp_html += f'<div class="ts-stat"><div class="ts-stat-label">Size $</div><div class="ts-stat-value" style="color:#E6EDF3;">${hp_dollar:,.0f}</div></div>'
            hp_html += f'<div class="ts-stat"><div class="ts-stat-label">Mode</div><div class="ts-stat-value" style="color:#8B949E;">{hp_mode}</div></div>'
            hp_html += f'<div class="ts-stat"><div class="ts-stat-label">Conviction</div><div class="ts-stat-value" style="color:{"#3FB950" if hp_conv>=0.8 else "#D29922" if hp_conv>=0.5 else "#F85149"};">{hp_conv:.0%}</div></div>'
            hp_html += f'</div></div>'
            st.markdown(hp_html, unsafe_allow_html=True)

        # ── Keith Signal Sync ──
        if ks and isinstance(ks, dict) and ks.get("keith_trade") != "NEUTRAL":
            ktrade = ks.get("keith_trade", "—")
            ktrend = ks.get("keith_trend", "—")
            kfinal = ks.get("direction", "—")
            kbasis = ks.get("basis", "")[:120]
            k_override = ks.get("override", False)
            tc = "#3FB950" if ktrade == "BULLISH" else "#F85149" if ktrade == "BEARISH" else "#8B949E"
            k_html = f'<div class="ts-panel" style="border-color: {tc}30; margin-bottom: 8px;">'
            k_html += f'<div class="ts-panel-title">🎙️ Keith McCullough Signal Sync (P0)</div>'
            k_html += f'<span style="background:{tc}18;color:{tc};padding:2px 8px;border-radius:4px;font-size:0.7rem;font-weight:700;border:1px solid {tc}40;">🎙️ TRADE: {ktrade}</span>'
            if k_override:
                k_html += f' <span style="background:#F8514918;color:#F85149;padding:2px 8px;border-radius:4px;font-size:0.7rem;font-weight:700;border:1px solid #F8514940;">⚠️ OVERRIDE</span>'
            k_html += f'<div style="font-size:0.7rem;color:#E6EDF3;margin-top:4px;">Dashboard → <b>{kfinal}</b></div>'
            k_html += f'<div style="font-size:0.65rem;color:#484F58;margin-top:2px;">{kbasis}</div>'
            k_html += f'</div>'
            st.markdown(k_html, unsafe_allow_html=True)

        # ── Greeks ──
        show_options = market_type != "ihsg"
        if show_options:
            opts = row.get("options", {})
            gex_val = opts.get("gex")
            vanna_val = opts.get("vanna")
            charm_val = opts.get("charm")
            skew_30d = opts.get("skew_30d")
            gamma_regime = opts.get("gamma_regime", "")
            greeks_html = f'<div class="ts-panel" style="border-color: #D2992230; margin-bottom: 8px;">'
            greeks_html += f'<div class="ts-panel-title">📊 Greeks · Source: {opts.get("source","PROXY")}</div>'
            if gamma_regime:
                gcolor = "#3FB950" if "POSITIVE" in gamma_regime else "#F85149" if "NEGATIVE" in gamma_regime else "#D29922"
                greeks_html += f'<div style="font-size:0.7rem;margin-bottom:4px;">Gamma: <b style="color:{gcolor};">{gamma_regime}</b></div>'
            if gex_val is not None:
                greeks_html += f'<div style="font-size:0.65rem;color:#8B949E;">GEX: <b>{float(gex_val):+.2f}</b></div>'
            if vanna_val is not None:
                greeks_html += f'<div style="font-size:0.65rem;color:#8B949E;">Vanna: <b>{float(vanna_val):+.2f}</b></div>'
            if charm_val is not None:
                greeks_html += f'<div style="font-size:0.65rem;color:#8B949E;">Charm: <b>{float(charm_val):+.2f}</b></div>'
            if skew_30d is not None:
                greeks_html += f'<div style="font-size:0.65rem;color:#8B949E;">Skew 30D: <b>{float(skew_30d):+.2f}</b></div>'
            if opts.get("max_pain"):
                greeks_html += f'<div style="font-size:0.65rem;color:#8B949E;">Max Pain: <b>{_ffm(opts["max_pain"], market_type)}</b></div>'
            greeks_html += f'</div>'
            st.markdown(greeks_html, unsafe_allow_html=True)

        # ── Dark Pool ──
        dp = row.get("dark_pool")
        if dp and isinstance(dp, dict):
            div = dp.get("divergence", "NEUTRAL")
            zf = dp.get("zero_flag")
            dp_color = "#3FB950" if div == "HIDDEN_ACCUMULATION" else "#F85149" if div == "HIDDEN_DISTRIBUTION" else "#8B949E"
            dp_html = f'<div class="ts-panel" style="border-color: {dp_color}30; margin-bottom: 8px;">'
            dp_html += f'<div class="ts-panel-title">🌑 Dark Pool Intelligence</div>'
            if div != "NEUTRAL":
                dp_html += f'<span style="background:{dp_color}18;color:{dp_color};padding:2px 8px;border-radius:4px;font-size:0.65rem;font-weight:700;border:1px solid {dp_color}40;">{div.replace("_"," ")}</span>'
            if zf:
                zcolor = "#3FB950" if zf == "ZERO_SELLS" else "#F85149"
                dp_html += f' <span style="background:{zcolor}18;color:{zcolor};padding:2px 8px;border-radius:4px;font-size:0.65rem;font-weight:700;border:1px solid {zcolor}40;">{zf}</span>'
            dp_html += f'</div>'
            st.markdown(dp_html, unsafe_allow_html=True)

        # ── Entry Convergence ──
        if conv and isinstance(conv, dict):
            conv_layers = conv.get("layers", [])
            conv_html = f'<div class="ts-panel" style="border-color: {conv_color}40; margin-bottom: 8px;">'
            conv_html += f'<div class="ts-panel-title">🎯 Entry Convergence ({len(conv_layers)} layers)</div>'
            conv_html += f'<div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(140px, 1fr));gap:4px;">'
            for layer in conv_layers[:12]:
                lcolor = layer.get("color", "#8B949E")
                lw = layer.get("weight", 0)
                sign = "+" if lw > 0 else ""
                conv_html += f'<div style="padding:3px 6px;background:#0D1117;border-radius:4px;font-size:0.6rem;display:flex;justify-content:space-between;">'
                conv_html += f'<span style="color:#8B949E;">{layer.get("name","—")}</span>'
                conv_html += f'<span style="color:{lcolor};font-weight:700;">{layer.get("signal","—")} {sign}{lw}</span>'
                conv_html += f'</div>'
            conv_html += f'</div></div>'
            st.markdown(conv_html, unsafe_allow_html=True)

        # ── Recommendation ──
        if market_type == "ihsg":
            broker = row.get("broker", {})
            if broker and isinstance(broker, dict):
                b_sig = broker.get("signal", "NEUTRAL")
                b_conf = broker.get("confidence", 0)
                b_color = "#3FB950" if broker.get("real_accumulation") else "#F85149" if broker.get("real_distribution") else "#D29922" if broker.get("crossing_detected") else "#8B949E"
                rec_html = f'<div class="ts-panel" style="border-color: {b_color}40;">'
                rec_html += f'<span style="background:{b_color}20;border:1px solid {b_color}50;border-radius:6px;padding:4px 10px;font-size:0.75rem;color:{b_color};font-weight:700;">🎯 {b_sig}</span>'
                rec_html += f' <span style="font-size:0.7rem;color:#8B949E;">Confidence <b>{b_conf}%</b></span>'
                rec_html += f'</div>'
                st.markdown(rec_html, unsafe_allow_html=True)
        else:
            cot_data = None; onchain_data = None
            if market_type in ("forex", "commodity"):
                cot_data = _get_cot_proxy(ticker)
            if market_type == "crypto":
                onchain_data = _get_onchain_proxy(ticker, st.session_state.snap.get("prices", {}))
            rec = _get_single_recommendation(
                options, direction=row.get("direction", "LONG"), market_type=market_type,
                cot_data=cot_data, onchain_data=onchain_data, ticker=ticker, row=row,
                dark_pool=row.get("dark_pool")
            )
            rec_color = {"BELI SPOT / AKUMULASI":"#3FB950","AKUMULASI SPOT":"#3FB950","BELI CALL / LONG SPOT":"#3FB950",
                         "BELI SPOT + JUAL PUT":"#2EA043","BELI SPOT":"#3FB950",
                         "JUAL COVERED CALL":"#D29922","JUAL PUT PROTEKTIF":"#F85149",
                         "JUAL / REDUKSI":"#F85149","HEDGE POSISI":"#F85149",
                         "HOLD + JUAL PREMIUM":"#D29922","WASPADA / TUNGGU":"#D29922",
                         "HOLD / TUNGGU":"#8B949E","HOLD":"#8B949E"}.get(rec["action"], "#58A6FF")
            conf_pct = rec.get("confidence", 50)
            rec_html = f'<div class="ts-panel" style="border-color: {rec_color}40;">'
            rec_html += f'<span style="background:{rec_color}20;border:1px solid {rec_color}50;border-radius:6px;padding:4px 10px;font-size:0.75rem;color:{rec_color};font-weight:700;">🎯 {rec["action"]}</span>'
            rec_html += f' <span style="font-size:0.7rem;color:#8B949E;">Confidence <b style="color:{rec_color};">{conf_pct:.0f}%</b></span>'
            rec_html += f'<div style="font-size:0.68rem;color:#8B949E;margin-top:6px;line-height:1.5;">{rec["rationale"]}</div>'
            rec_html += f'</div>'
            st.markdown(rec_html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# HELPER: Visual Entry Zone Bar
# ═══════════════════════════════════════════════════════════════════
def _build_entry_zone_bar(px, entry, stop, t1, t2, t3, market_type):
    """Build a visual horizontal bar showing stop → entry → current → targets."""
    if not all(v is not None and v > 0 for v in [px, entry, stop, t1]):
        return '<div style="height:12px;background:#21262D;border-radius:6px;margin:8px 0;"></div>'

    px_f = float(px); entry_f = float(entry); stop_f = float(stop)
    t1_f = float(t1); t2_f = float(t2) if t2 else t1_f * 1.3
    t3_f = float(t3) if t3 else t2_f * 1.2

    # Calculate relative positions (0-100%)
    full_range = t3_f - stop_f
    if full_range <= 0:
        full_range = t3_f * 0.1

    stop_pct = 0
    entry_pct = max(5, min(35, (entry_f - stop_f) / full_range * 100))
    px_pct = max(5, min(95, (px_f - stop_f) / full_range * 100))
    t1_pct = max(entry_pct + 10, min(70, (t1_f - stop_f) / full_range * 100))
    t2_pct = max(t1_pct + 5, min(85, (t2_f - stop_f) / full_range * 100))
    t3_pct = min(100, (t3_f - stop_f) / full_range * 100)

    # Widths
    stop_width = entry_pct
    entry_width = max(3, px_pct - entry_pct) if px_pct > entry_pct else 3
    safe_width = max(3, t1_pct - px_pct) if t1_pct > px_pct else 3
    t1_width = max(5, t2_pct - t1_pct) if t2_pct > t1_pct else 5
    t2_width = max(5, t3_pct - t2_pct) if t3_pct > t2_pct else 5

    bar_html = '<div style="margin:10px 0;">'
    # Labels
    bar_html += '<div style="display:flex;justify-content:space-between;font-size:0.6rem;color:#8B949E;margin-bottom:3px;font-variant-numeric:tabular-nums;">'
    bar_html += f'<span>SL {_ffm(stop_f, market_type)}</span>'
    bar_html += f'<span>Entry {_ffm(entry_f, market_type)}</span>'
    bar_html += f'<span style="color:#E6EDF3;font-weight:700;">Now {_ffm(px_f, market_type)}</span>'
    bar_html += f'<span>T1 {_ffm(t1_f, market_type)}</span>'
    bar_html += f'<span>T2 {_ffm(t2_f, market_type)}</span>'
    bar_html += f'<span>T3 {_ffm(t3_f, market_type)}</span>'
    bar_html += '</div>'

    # The bar
    bar_html += '<div style="height:14px;background:#21262D;border-radius:7px;position:relative;overflow:hidden;">'
    # Stop zone (red, left 0 to entry)
    bar_html += f'<div style="position:absolute;left:0;width:{stop_width:.0f}%;height:100%;background:linear-gradient(90deg,#F85149,#F8514980);border-radius:7px 0 0 7px;"></div>'
    # Entry zone (blue)
    bar_html += f'<div style="position:absolute;left:{entry_pct:.0f}%;width:{entry_width:.0f}%;height:100%;background:linear-gradient(90deg,#58A6FF,#58A6FF80);"></div>'
    # Safe zone (dark, between entry and t1)
    bar_html += f'<div style="position:absolute;left:{entry_pct + entry_width:.0f}%;width:{safe_width:.0f}%;height:100%;background:#21262D;"></div>'
    # T1 zone (green)
    bar_html += f'<div style="position:absolute;left:{t1_pct:.0f}%;width:{t1_width:.0f}%;height:100%;background:linear-gradient(90deg,#3FB95060,#3FB950);"></div>'
    # T2 zone (brighter green)
    bar_html += f'<div style="position:absolute;left:{t2_pct:.0f}%;width:{t2_width:.0f}%;height:100%;background:linear-gradient(90deg,#2EA04360,#2EA043);"></div>'
    # T3 zone (subtle)
    bar_html += f'<div style="position:absolute;left:{t3_pct:.0f}%;width:{100 - t3_pct:.0f}%;height:100%;background:linear-gradient(90deg,#23863640,#23863620);border-radius:0 7px 7px 0;"></div>'
    # Current price marker (white dot)
    bar_html += f'<div style="position:absolute;left:{px_pct:.0f}%;top:50%;transform:translate(-50%,-50%);width:8px;height:8px;background:#fff;border-radius:50%;border:2px solid #58A6FF;box-shadow:0 0 6px rgba(88,166,255,0.6);z-index:10;"></div>'
    bar_html += '</div>'

    # Legend
    bar_html += '<div style="display:flex;justify-content:center;gap:12px;margin-top:4px;font-size:0.55rem;color:#8B949E;">'
    bar_html += '<span><span style="display:inline-block;width:8px;height:8px;background:#F85149;border-radius:2px;margin-right:2px;"></span>Stop</span>'
    bar_html += '<span><span style="display:inline-block;width:8px;height:8px;background:#58A6FF;border-radius:2px;margin-right:2px;"></span>Entry</span>'
    bar_html += '<span><span style="display:inline-block;width:8px;height:8px;background:#fff;border:1px solid #58A6FF;border-radius:50%;margin-right:2px;"></span>Current</span>'
    bar_html += '<span><span style="display:inline-block;width:8px;height:8px;background:#3FB950;border-radius:2px;margin-right:2px;"></span>T1 Swing</span>'
    bar_html += '<span><span style="display:inline-block;width:8px;height:8px;background:#2EA043;border-radius:2px;margin-right:2px;"></span>T2 Trend</span>'
    bar_html += '<span><span style="display:inline-block;width:8px;height:8px;background:#238636;border-radius:2px;margin-right:2px;"></span>T3 Tail</span>'
    bar_html += '</div>'
    bar_html += '</div>'
    return bar_html


# ═══════════════════════════════════════════════════════════════════
# HELPER: Build Thesis Items
# ═══════════════════════════════════════════════════════════════════
def _build_thesis_items(row, market_type):
    """Build list of (icon, text, color) thesis items explaining why this trade."""
    items = []
    px = row.get("price", 0)
    formation = row.get("formation", "NEUTRAL")
    direction = row.get("direction", "NEUTRAL")
    opts = row.get("options", {})
    rr = row.get("rr", 0)
    entry = row.get("entry")
    stop = row.get("stop")
    trade_l = row.get("trade_low", 0)
    trade_r = row.get("trade_top", 0)

    # 1. Setup type (highest priority)
    if formation == "OVERSOLD":
        dist = ((px - trade_l) / trade_l * 100) if trade_l else 0
        items.append(("📉", f"<b>OVERSOLD SETUP:</b> Price {abs(dist):.1f}% below Trade Low. Mean-reversion play dengan asimetrik upside.", "#3FB950"))
    elif formation == "OVERBOUGHT":
        dist = ((px - trade_r) / trade_r * 100) if trade_r else 0
        items.append(("📈", f"<b>OVERBOUGHT SETUP:</b> Price {dist:.1f}% above Trade Top. Fade rally setup.", "#F85149"))
    elif formation == "BULLISH":
        items.append(("📈", f"<b>BULLISH FORMATION:</b> Price above Trend Top AND Tail Top. Trend-following entry.", "#3FB950"))
    elif formation == "BEARISH":
        items.append(("📉", f"<b>BEARISH FORMATION:</b> Price below Trend Low AND Tail Low. Trend-following short.", "#F85149"))
    elif formation in ("BULLISH_BIAS", "BEARISH_BIAS"):
        items.append(("📊", f"<b>BIAS SETUP:</b> {formation.replace('_', ' ')} — directional favorable untuk {direction}.", "#D29922"))

    # 2. Risk/Reward
    if rr >= 2.0:
        items.append(("🎯", f"<b>ASYMMETRIC RR:</b> Risk/Reward {rr:.1f}x — highly asymmetric. Reward lebih besar 2x dari risk.", "#3FB950"))
    elif rr >= 1.5:
        items.append(("⚠️", f"<b>MODERATE RR:</b> Risk/Reward {rr:.1f}x — valid tapi jangan oversize posisi.", "#D29922"))

    # 3. Greeks / Options signals
    if market_type != "ihsg" and opts:
        gamma = opts.get("gamma_regime", "")
        mp = opts.get("max_pain")
        vanna = opts.get("vanna")
        charm = opts.get("charm")
        gex = opts.get("gex")

        if gamma in ("NEGATIVE", "DEEP_NEGATIVE") and "LONG" in direction:
            items.append(("🔴", "<b>Negative Gamma:</b> Dealer short gamma = trend ACCELERATION on breakout. Target bisa lebih agresif.", "#3FB950"))
        elif gamma in ("POSITIVE", "DEEP_POSITIVE") and "LONG" in direction:
            items.append(("🟢", "<b>Positive Gamma:</b> Dealer long = mean-reversion ke max pain. Range-bound behavior — tighten target.", "#D29922"))

        if mp and px:
            mp_dist = (px - mp) / mp * 100
            if abs(mp_dist) < 2:
                items.append(("📍", f"<b>Max Pain Pin:</b> Price {mp_dist:+.1f}% dari max pain (${_ffm(mp, market_type)}). MM trapped — range-bound until expiry.", "#D29922"))
            elif mp_dist < -3 and gamma in ("NEGATIVE", "DEEP_NEGATIVE"):
                items.append(("📉", f"<b>Put Wall Support:</b> Price {mp_dist:.1f}% below max pain + neg gamma. <b>Support holds — buy dips.</b>", "#3FB950"))
            elif mp_dist > 3 and gamma in ("POSITIVE", "DEEP_POSITIVE"):
                items.append(("📈", f"<b>Call Wall Resistance:</b> Price +{mp_dist:.1f}% above max pain + pos gamma. <b>Fade strength.</b>", "#F85149"))

        if vanna is not None:
            try:
                v = float(vanna)
                if v > 0.5:
                    items.append(("🟢", f"<b>Vanna +{v:.2f}:</b> Rally = vol crush. Buy spot on dips — vol expansion mendukung upside.", "#3FB950"))
                elif v < -0.5:
                    items.append(("🔴", f"<b>Vanna {v:.2f}:</b> Rally = vol expansion. Breakouts volatile — hedge dengan put.", "#D29922"))
            except:
                pass

        if charm is not None:
            try:
                c = float(charm)
                if c > 0.5:
                    items.append(("🟢", f"<b>Charm +{c:.2f}:</b> Put support strengthening daily. Theta decay mendukung longs.", "#3FB950"))
                elif c < -0.5:
                    items.append(("🔴", f"<b>Charm {c:.2f}:</b> Put support eroding — downside acceleration risk. Tighten stop.", "#F85149"))
            except:
                pass

        if gex is not None:
            try:
                g = float(gex)
                if g < -0.5:
                    items.append(("🔴", f"<b>GEX {g:.2f}:</b> Extreme negative GEX = trend acceleration. Dips get bought.", "#3FB950"))
                elif g > 0.5:
                    items.append(("🟢", f"<b>GEX +{g:.2f}:</b> Extreme positive GEX = strong mean-reversion. Sell rallies.", "#D29922"))
            except:
                pass

    # 4. Dark Pool
    dp = row.get("dark_pool")
    if dp and isinstance(dp, dict):
        div = dp.get("divergence", "NEUTRAL")
        if div == "HIDDEN_ACCUMULATION":
            items.append(("🟢", "<b>Hidden Accumulation:</b> Dark Pool BUY + Lit Tape SELL. Institutions stealth buying — contrarian bullish.", "#3FB950"))
        elif div == "HIDDEN_DISTRIBUTION":
            items.append(("🔴", "<b>Hidden Distribution:</b> Dark Pool SELL + Lit Tape BUY. Institutions dumping ke retail.", "#F85149"))
        elif div == "BOTH_AGREE":
            items.append(("✅", f"<b>Both Tapes Agree:</b> Dark Pool + Lit Tape {dp.get('dp_signal','')} — strong conviction.", "#3FB950"))
        zf = dp.get("zero_flag")
        if zf == "ZERO_SELLS":
            items.append(("🔥", "<b>ZERO Dark Sells:</b> Pure institutional accumulation detected. Very bullish.", "#3FB950"))
        elif zf == "ZERO_BUYS":
            items.append(("❄️", "<b>ZERO Dark Buys:</b> Pure institutional distribution. Very bearish.", "#F85149"))

    # 5. Entry Convergence layers
    conv = row.get("entry_convergence")
    if conv and isinstance(conv, dict):
        layers = conv.get("layers", [])
        for layer in layers[:3]:  # Top 3 layers
            name = layer.get("name", "")
            signal = layer.get("signal", "")
            weight = layer.get("weight", 0)
            color = "#3FB950" if weight > 0 else "#F85149" if weight < 0 else "#8B949E"
            icon = "🟢" if weight > 0 else "🔴" if weight < 0 else "⚪"
            items.append((icon, f"<b>{name}:</b> {signal} ({weight:+.0f} pts)", color))

    # 6. Macro narrative
    snap_local = st.session_state.get("snap")
    if snap_local:
        narrative = snap_local.get("narrative", {}) or {}
        scenarios = narrative.get("scenarios", {}) if isinstance(narrative, dict) else {}
        if scenarios:
            dom = scenarios.get("dominant_scenario", "base")
            bull_p = scenarios.get("bull", {}).get("probability", 0) if isinstance(scenarios.get("bull"), dict) else 0
            if dom == "bull" and "LONG" in direction:
                items.append(("📰", f"<b>Macro Tailwind:</b> Dominant BULLISH scenario ({bull_p:.0%} prob). Macro environment mendukung longs.", "#3FB950"))
            elif dom == "bear" and "SHORT" in direction:
                items.append(("📰", "<b>Macro Tailwind:</b> Dominant BEARISH scenario. Macro environment mendukung shorts.", "#3FB950"))

    # 7. Quality score
    qscore = row.get("quality_score", 0)
    if qscore >= 80:
        items.append(("⭐", f"<b>Grade A Quality ({qscore}):</b> High conviction setup — multiple signals align.", "#3FB950"))
    elif qscore >= 60:
        items.append(("⭐", f"<b>Grade B Quality ({qscore}):</b> Good setup — valid entry dengan risk management ketat.", "#D29922"))

    if not items:
        items.append(("⚪", "Data tidak cukup untuk reasoning kuat. Setup didasarkan price action saja.", "#8B949E"))

    return items


# ═══════════════════════════════════════════════════════════════════
# HELPER: Build Execution Checklist
# ═══════════════════════════════════════════════════════════════════
def _build_execution_checklist(row, px, entry, stop, t1, t2, rr, chase_status):
    """Build execution checklist items with pass/fail icons."""
    items = []

    # 1. Price dalam entry zone?
    in_zone = False
    if entry and stop and px:
        if "LONG" in row.get("direction", ""):
            in_zone = px <= entry * 1.02 and px >= stop * 0.98
        else:
            in_zone = px >= entry * 0.98 and px <= stop * 1.02
    zone_icon = "✅" if in_zone else "❌"
    zone_text = f"Price dalam entry zone ({_ffm(entry, row.get('market_type','us_equity'))})" if in_zone else f"Wait for pullback ke entry ({_ffm(entry, row.get('market_type','us_equity'))})"
    items.append((zone_icon, zone_text))

    # 2. Stop loss valid?
    risk_pct = row.get("risk_pct", 0)
    stop_valid = risk_pct >= 0.5
    stop_icon = "✅" if stop_valid else "❌"
    stop_text = f"Stop loss valid — Risk {risk_pct:.1f}%" if stop_valid else f"Stop loss terlalu dekat — Risk {risk_pct:.1f}% (min 0.5%)"
    items.append((stop_icon, stop_text))

    # 3. RR > 2.0?
    rr_good = rr >= 2.0
    rr_icon = "✅" if rr_good else "⚠️"
    rr_text = f"RR ratio bagus — {rr:.1f}x (target > 2.0x)" if rr_good else f"RR ratio {rr:.1f}x — di bawah optimal 2.0x, kurangi size"
    items.append((rr_icon, rr_text))

    # 4. Hedgeye playbook alignment?
    snap_local = st.session_state.get("snap")
    in_favor = False
    if snap_local:
        pb = _get_hedgeye_playbook(snap_local)
        ticker = row.get("ticker", "")
        in_favor = ticker in pb.get("beli", []) if "LONG" in row.get("direction", "") else ticker in pb.get("short", [])
    hedge_icon = "✅" if in_favor else "⚠️"
    hedge_text = "Hedgeye playbook alignment: FAVORED" if in_favor else "Hedgeye playbook: NOT in favor list — extra caution"
    items.append((hedge_icon, hedge_text))

    # 5. Position size calculated?
    hp = row.get("hedgeye_size")
    if hp and isinstance(hp, dict):
        hp_pct = hp.get("size_pct", 0)
        items.append(("✅", f"Position size: {hp_pct:.2%} of portfolio (Hedgeye sizing)"))
    else:
        suggested = 0.025 if rr >= 2.0 else 0.015
        items.append(("⬜", f"Set position size: ~{suggested:.1%} of portfolio (suggested for RR {rr:.1f}x)"))

    # 6. Stop order placed?
    items.append(("⬜", f"Place stop order at {_ffm(stop, row.get('market_type','us_equity'))}"))

    # 7. Target orders?
    if t1:
        items.append(("⬜", f"Set T1 (swing) take-profit at {_ffm(t1, row.get('market_type','us_equity'))}"))
    if t2:
        items.append(("⬜", f"Set T2 (trend) take-profit at {_ffm(t2, row.get('market_type','us_equity'))}"))

    return items
