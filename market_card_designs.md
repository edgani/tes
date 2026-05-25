# Market-Specific Ticker Card Design System

## Overview
A comprehensive UI design system for trading dashboard ticker cards across 5 market categories (US Stocks, Forex, Commodities, Crypto, IHSG). Each card combines price action, market-specific data layers, options/Greeks recommendations, thesis panel, and execution checklist into a single readable layout.

---

## Design Tokens & Shared CSS Foundation

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Market Ticker Cards</title>
<style>
/* ============================================
   ROOT TOKENS - Dark Theme
   ============================================ */
:root {
  /* Background Layers */
  --bg-base: #0a0e17;
  --bg-card: #111827;
  --bg-section: #1a2236;
  --bg-hover: #232d45;

  /* Border Colors */
  --border-subtle: #1e293b;
  --border-active: #334155;

  /* Text Colors */
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;

  /* Signal Colors */
  --bull: #10b981;
  --bull-dim: rgba(16,185,129,0.15);
  --bear: #ef4444;
  --bear-dim: rgba(239,68,68,0.15);
  --neutral: #3b82f6;
  --neutral-dim: rgba(59,130,246,0.15);
  --warning: #f59e0b;
  --warning-dim: rgba(245,158,11,0.15);

  /* Market Category Accents */
  --accent-stocks: #10b981;
  --accent-forex: #8b5cf6;
  --accent-commodities: #f59e0b;
  --accent-crypto: #06b6d4;
  --accent-ihsg: #ec4899;

  /* Spacing */
  --gap-xs: 4px;
  --gap-sm: 8px;
  --gap-md: 12px;
  --gap-lg: 16px;
  --gap-xl: 24px;

  /* Typography */
  --font-mono: 'SF Mono', 'Fira Code', monospace;
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

  /* Border Radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
}

/* ============================================
   BASE STYLES
   ============================================ */
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: var(--font-sans);
  padding: 20px;
  line-height: 1.5;
}

/* ============================================
   SHARED CARD SHELL
   ============================================ */
.ticker-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  max-width: 480px;
  margin: 0 auto 24px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.ticker-card:hover {
  border-color: var(--border-active);
  box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}

/* Category accent top border */
.ticker-card.stocks { border-top: 3px solid var(--accent-stocks); }
.ticker-card.forex { border-top: 3px solid var(--accent-forex); }
.ticker-card.commodities { border-top: 3px solid var(--accent-commodities); }
.ticker-card.crypto { border-top: 3px solid var(--accent-crypto); }
.ticker-card.ihsg { border-top: 3px solid var(--accent-ihsg); }

/* ============================================
   CARD HEADER (Shared)
   ============================================ */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--gap-md) var(--gap-lg);
  border-bottom: 1px solid var(--border-subtle);
}
.ticker-info { display: flex; align-items: center; gap: var(--gap-md); }
.ticker-symbol {
  font-family: var(--font-mono);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.5px;
}
.ticker-name {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: -2px;
}
.ticker-badge {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 3px 8px;
  border-radius: 20px;
}
.badge-stocks { background: var(--bull-dim); color: var(--bull); }
.badge-forex { background: rgba(139,92,246,0.15); color: var(--accent-forex); }
.badge-commodities { background: var(--warning-dim); color: var(--accent-commodities); }
.badge-crypto { background: rgba(6,182,212,0.15); color: var(--accent-crypto); }
.badge-ihsg { background: rgba(236,72,153,0.15); color: var(--accent-ihsg); }

.price-display { text-align: right; }
.price-current {
  font-family: var(--font-mono);
  font-size: 22px;
  font-weight: 700;
}
.price-change {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
}
.up { color: var(--bull); }
.down { color: var(--bear); }
.neutral { color: var(--neutral); }

/* ============================================
   ENTRY ZONE BAR (Shared Component)
   ============================================ */
.entry-zone-section {
  padding: var(--gap-md) var(--gap-lg);
  border-bottom: 1px solid var(--border-subtle);
}
.zone-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
  margin-bottom: var(--gap-sm);
  display: flex;
  justify-content: space-between;
}
.zone-bar-container {
  position: relative;
  height: 36px;
  background: var(--bg-section);
  border-radius: var(--radius-sm);
  overflow: hidden;
  display: flex;
}
.zone-stop {
  flex: 0 0 20%;
  background: linear-gradient(90deg, rgba(239,68,68,0.3), rgba(239,68,68,0.1));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  color: var(--bear);
  border-right: 1px dashed rgba(239,68,68,0.3);
}
.zone-entry {
  flex: 0 0 35%;
  background: linear-gradient(90deg, rgba(59,130,246,0.25), rgba(59,130,246,0.1));
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 2px;
  border-right: 1px dashed rgba(59,130,246,0.3);
  position: relative;
}
.zone-entry::after {
  content: '';
  position: absolute;
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
  width: 0; height: 0;
  border-left: 6px solid var(--neutral);
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
}
.zone-entry-label {
  font-size: 9px;
  font-weight: 600;
  color: var(--neutral);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.zone-entry-price {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  color: var(--neutral);
}
.zone-targets {
  flex: 1;
  display: flex;
  position: relative;
}
.zone-t1, .zone-t2, .zone-t3 {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 2px;
  position: relative;
}
.zone-t1 {
  background: linear-gradient(90deg, rgba(16,185,129,0.15), rgba(16,185,129,0.08));
}
.zone-t2 {
  background: linear-gradient(90deg, rgba(16,185,129,0.25), rgba(16,185,129,0.12));
}
.zone-t3 {
  background: linear-gradient(90deg, rgba(16,185,129,0.4), rgba(16,185,129,0.2));
}
.zone-target-label {
  font-size: 9px;
  font-weight: 600;
  color: var(--bull);
  text-transform: uppercase;
}
.zone-target-price {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  color: var(--bull);
}

/* ============================================
   THESIS PANEL (Shared Component)
   ============================================ */
.thesis-section {
  padding: var(--gap-md) var(--gap-lg);
  border-bottom: 1px solid var(--border-subtle);
}
.thesis-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
  margin-bottom: var(--gap-sm);
}
.thesis-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--gap-xs);
}
.thesis-item {
  display: flex;
  align-items: flex-start;
  gap: var(--gap-sm);
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  padding: 4px 0;
}
.thesis-icon {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  flex-shrink: 0;
  margin-top: 1px;
}
.icon-bull { background: var(--bull-dim); color: var(--bull); }
.icon-bear { background: var(--bear-dim); color: var(--bear); }
.icon-neutral { background: var(--neutral-dim); color: var(--neutral); }
.icon-warning { background: var(--warning-dim); color: var(--warning); }

/* ============================================
   EXECUTION CHECKLIST (Shared Component)
   ============================================ */
.execution-section {
  padding: var(--gap-md) var(--gap-lg);
}
.execution-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
  margin-bottom: var(--gap-sm);
}
.checklist {
  display: flex;
  flex-direction: column;
  gap: var(--gap-xs);
}
.check-item {
  display: flex;
  align-items: center;
  gap: var(--gap-sm);
  font-size: 12px;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  transition: background 0.15s;
}
.check-item:hover { background: var(--bg-hover); }
.check-box {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-active);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  flex-shrink: 0;
  transition: all 0.15s;
}
.check-item.passed .check-box {
  background: var(--bull);
  border-color: var(--bull);
  color: #fff;
}
.check-item.pending .check-box {
  border-color: var(--warning);
  color: var(--warning);
}
.check-item.failed .check-box {
  background: var(--bear);
  border-color: var(--bear);
  color: #fff;
}
.check-text { color: var(--text-secondary); }
.check-item.passed .check-text { color: var(--text-primary); }

/* ============================================
   MARKET-SPECIFIC PANEL STYLES
   ============================================ */
.market-panel {
  padding: var(--gap-md) var(--gap-lg);
  border-bottom: 1px solid var(--border-subtle);
  background: var(--bg-section);
}
.panel-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
  margin-bottom: var(--gap-md);
  display: flex;
  align-items: center;
  gap: var(--gap-sm);
}
.data-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--gap-md);
}
.data-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.data-label {
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.data-value {
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 700;
}
.data-sublabel {
  font-size: 10px;
  color: var(--text-secondary);
}

/* Mini gauge bar */
.gauge-bar {
  height: 4px;
  background: var(--bg-hover);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 4px;
}
.gauge-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}
.gauge-green { background: var(--bull); }
.gauge-red { background: var(--bear); }
.gauge-blue { background: var(--neutral); }
.gauge-yellow { background: var(--warning); }

/* Options recommendation box */
.options-rec {
  margin-top: var(--gap-md);
  padding: var(--gap-md);
  border-radius: var(--radius-sm);
  border-left: 3px solid;
}
.options-rec.buy-call {
  background: var(--bull-dim);
  border-left-color: var(--bull);
}
.options-rec.buy-put {
  background: var(--bear-dim);
  border-left-color: var(--bear);
}
.options-rec.neutral {
  background: var(--neutral-dim);
  border-left-color: var(--neutral);
}
.options-rec-title {
  font-size: 11px;
  font-weight: 700;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: var(--gap-sm);
}
.options-rec-desc {
  font-size: 11px;
  line-height: 1.5;
  color: var(--text-secondary);
}
.rec-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  margin-top: 6px;
}
.tag-buy { background: rgba(16,185,129,0.3); color: var(--bull); }
.tag-avoid { background: rgba(239,68,68,0.3); color: var(--bear); }
.tag-caution { background: rgba(245,158,11,0.3); color: var(--warning); }

/* Progress ring */
.ring-container {
  display: flex;
  align-items: center;
  gap: var(--gap-md);
}
.ring-wrap {
  position: relative;
  width: 60px;
  height: 60px;
}
.ring-svg { transform: rotate(-90deg); }
.ring-bg {
  fill: none;
  stroke: var(--bg-hover);
  stroke-width: 6;
}
.ring-progress {
  fill: none;
  stroke-width: 6;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.5s ease;
}
.ring-text {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
}

/* Flow indicator */
.flow-indicator {
  display: flex;
  align-items: center;
  gap: var(--gap-sm);
}
.flow-arrow {
  font-size: 18px;
  font-weight: 700;
}
.flow-in { color: var(--bull); }
.flow-out { color: var(--bear); }
.flow-value {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
}

/* ============================================
   RESPONSIVE
   ============================================ */
@media (max-width: 480px) {
  .data-grid { grid-template-columns: 1fr; }
  .zone-stop span, .zone-target-label { display: none; }
  .zone-entry-label { font-size: 8px; }
  .zone-entry-price { font-size: 11px; }
}
</style>
</head>
<body>
```

---

## 1. US STOCKS Card

**Market-Specific Data**: Barchart IV Rank, IV Percentile, Expected Move, Max Pain, Earnings Date, Put/Call Ratio

**Options Recommendation**: "Beli calls kalau IV percentile < 30% (cheap vol), jangan beli kalau > 80% (expensive vol)"

```html
<!-- ==================== US STOCKS CARD ==================== -->
<div class="ticker-card stocks">

  <!-- HEADER -->
  <div class="card-header">
    <div class="ticker-info">
      <div>
        <div class="ticker-symbol">AAPL</div>
        <div class="ticker-name">Apple Inc.</div>
      </div>
      <span class="ticker-badge badge-stocks">US Stock</span>
    </div>
    <div class="price-display">
      <div class="price-current up">$189.52</div>
      <div class="price-change up">+2.34 (+1.25%)</div>
    </div>
  </div>

  <!-- ENTRY ZONE BAR -->
  <div class="entry-zone-section">
    <div class="zone-label">
      <span>Entry Zone</span>
      <span style="color:var(--text-muted);">R:R = 1:2.8</span>
    </div>
    <div class="zone-bar-container">
      <div class="zone-stop">
        <span>STOP</span>
      </div>
      <div class="zone-entry">
        <span class="zone-entry-label">Entry</span>
        <span class="zone-entry-price">$185.00</span>
      </div>
      <div class="zone-targets">
        <div class="zone-t1">
          <span class="zone-target-label">T1</span>
          <span class="zone-target-price">$192</span>
        </div>
        <div class="zone-t2">
          <span class="zone-target-label">T2</span>
          <span class="zone-target-price">$198</span>
        </div>
        <div class="zone-t3">
          <span class="zone-target-label">T3</span>
          <span class="zone-target-price">$205</span>
        </div>
      </div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:6px;padding:0 2px;">
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--bear);">$182.50</span>
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--neutral);">$185.00 - $187.00</span>
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--bull);">$205.00</span>
    </div>
  </div>

  <!-- MARKET-SPECIFIC: IV DATA PANEL -->
  <div class="market-panel">
    <div class="panel-label">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2v20M2 12h20M17 7l-5 5-5-5M17 17l-5-5-5 5"/>
      </svg>
      Implied Volatility Analysis
    </div>
    <div class="data-grid">
      <div class="data-cell">
        <span class="data-label">IV Rank</span>
        <span class="data-value" style="color:var(--bull);">22%</span>
        <div class="gauge-bar"><div class="gauge-fill gauge-green" style="width:22%"></div></div>
      </div>
      <div class="data-cell">
        <span class="data-label">IV Percentile</span>
        <span class="data-value" style="color:var(--bull);">18%</span>
        <div class="gauge-bar"><div class="gauge-fill gauge-green" style="width:18%"></div></div>
      </div>
      <div class="data-cell">
        <span class="data-label">Expected Move</span>
        <span class="data-value" style="color:var(--neutral);">+- 4.2%</span>
        <span class="data-sublabel">Until Jan 17 expiry</span>
      </div>
      <div class="data-cell">
        <span class="data-label">Max Pain</span>
        <span class="data-value" style="color:var(--warning);">$185.00</span>
        <span class="data-sublabel">Monthly expiry</span>
      </div>
      <div class="data-cell">
        <span class="data-label">Earnings Date</span>
        <span class="data-value" style="color:var(--text-primary);">Jan 29</span>
        <span class="data-sublabel">18 days away</span>
      </div>
      <div class="data-cell">
        <span class="data-label">Put/Call Ratio</span>
        <span class="data-value" style="color:var(--bull);">0.72</span>
        <span class="data-sublabel">Bullish sentiment</span>
      </div>
    </div>

    <!-- OPTIONS RECOMMENDATION -->
    <div class="options-rec buy-call">
      <div class="options-rec-title" style="color:var(--bull);">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M7 17l9.2-9.2M17 17V8H8"/>
        </svg>
        CALL SETUP - VOLATILITY CHEAP
      </div>
      <div class="options-rec-desc">
        IV Percentile <strong style="color:var(--bull);">18%</strong> (below 30% threshold) = cheap volatility. 
        Ideal for buying calls. Earnings in 18 days provides vol expansion catalyst.
        <br><br>
        <strong>Strategy:</strong> Buy Feb $190 Calls or Call Spread $190/$200
      </div>
      <span class="rec-tag tag-buy">BUY CALLS</span>
    </div>
  </div>

  <!-- THESIS PANEL -->
  <div class="thesis-section">
    <div class="thesis-label">Thesis</div>
    <ul class="thesis-list">
      <li class="thesis-item">
        <span class="thesis-icon icon-bull">&#8593;</span>
        <span>Price bouncing from demand zone $182-185 (confluence with Max Pain)</span>
      </li>
      <li class="thesis-item">
        <span class="thesis-icon icon-bull">&#8593;</span>
        <span>IV cheap at 18th percentile - favorable for long option positions</span>
      </li>
      <li class="thesis-item">
        <span class="thesis-icon icon-neutral">&#9679;</span>
        <span>Earnings Jan 29 = volatility expansion expected, manage before event</span>
      </li>
      <li class="thesis-item">
        <span class="thesis-icon icon-warning">!</span>
        <span>P/C ratio 0.72 shows complacency - monitor for sentiment shift</span>
      </li>
    </ul>
  </div>

  <!-- EXECUTION CHECKLIST -->
  <div class="execution-section">
    <div class="execution-label">Execution Checklist</div>
    <div class="checklist">
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">IV Percentile &lt; 30% (vol cheap)</span>
      </div>
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">Entry zone above Max Pain level</span>
      </div>
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">Expected move covers T1 target</span>
      </div>
      <div class="check-item pending">
        <div class="check-box">&#8635;</div>
        <span class="check-text">Earnings vol crush hedge (sell spread)</span>
      </div>
      <div class="check-item pending">
        <div class="check-box">&#8635;</div>
        <span class="check-text">Set stop below $182.50 (demence zone break)</span>
      </div>
    </div>
  </div>

</div>
```

### US Stocks Card Design Notes
- **IV Rank/Percentile** shown as progress gauge bars for instant visual read
- **Green** IV reading = cheap vol (good for buying options)
- **Red** IV reading = expensive vol (avoid buying, sell instead)
- Max Pain acts as magnetic level - entry above max pain = bullish positioning
- Earnings date prominently displayed as catalyst timer
- Options rec dynamically changes class based on IV percentile reading

---

## 2. FOREX Card

**Market-Specific Data**: COT positioning (non-commercial net), institutional sentiment, DXY correlation

**Options Recommendation**: "COT shows speculators extreme short → contrarian LONG opportunity"

```html
<!-- ==================== FOREX CARD ==================== -->
<div class="ticker-card forex">

  <!-- HEADER -->
  <div class="card-header">
    <div class="ticker-info">
      <div>
        <div class="ticker-symbol">EUR/USD</div>
        <div class="ticker-name">Euro / US Dollar</div>
      </div>
      <span class="ticker-badge badge-forex">Forex</span>
    </div>
    <div class="price-display">
      <div class="price-current down">1.0842</div>
      <div class="price-change down">-0.0034 (-0.31%)</div>
    </div>
  </div>

  <!-- ENTRY ZONE BAR -->
  <div class="entry-zone-section">
    <div class="zone-label">
      <span>Entry Zone</span>
      <span style="color:var(--text-muted);">R:R = 1:3.2</span>
    </div>
    <div class="zone-bar-container">
      <div class="zone-stop">
        <span>STOP</span>
      </div>
      <div class="zone-entry">
        <span class="zone-entry-label">Entry</span>
        <span class="zone-entry-price">1.0780</span>
      </div>
      <div class="zone-targets">
        <div class="zone-t1">
          <span class="zone-target-label">T1</span>
          <span class="zone-target-price">1.092</span>
        </div>
        <div class="zone-t2">
          <span class="zone-target-label">T2</span>
          <span class="zone-target-price">1.098</span>
        </div>
        <div class="zone-t3">
          <span class="zone-target-label">T3</span>
          <span class="zone-target-price">1.105</span>
        </div>
      </div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:6px;padding:0 2px;">
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--bear);">1.0750</span>
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--neutral);">1.0780 - 1.0810</span>
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--bull);">1.1050</span>
    </div>
  </div>

  <!-- MARKET-SPECIFIC: COT & SENTIMENT PANEL -->
  <div class="market-panel">
    <div class="panel-label">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M3 3v18h18"/>
        <path d="M7 16l4-8 4 4 6-10"/>
      </svg>
      COT Positioning & Sentiment
    </div>
    <div class="data-grid">
      <div class="data-cell">
        <span class="data-label">COT Non-Commercial Net</span>
        <div class="flow-indicator">
          <span class="flow-arrow flow-out">&#8595;</span>
          <span class="flow-value" style="color:var(--bear);">-84,230</span>
        </div>
        <span class="data-sublabel">Extreme short positioning</span>
      </div>
      <div class="data-cell">
        <span class="data-label">COT Commercial Net</span>
        <div class="flow-indicator">
          <span class="flow-arrow flow-in">&#8593;</span>
          <span class="flow-value" style="color:var(--bull);">+112,450</span>
        </div>
        <span class="data-sublabel">Smart money hedging/long</span>
      </div>
      <div class="data-cell">
        <span class="data-label">Institutional Sentiment</span>
        <span class="data-value" style="color:var(--bull);">62% Bull</span>
        <div class="gauge-bar"><div class="gauge-fill gauge-green" style="width:62%"></div></div>
      </div>
      <div class="data-cell">
        <span class="data-label">DXY Correlation</span>
        <span class="data-value" style="color:var(--bear);">-0.87</span>
        <span class="data-sublabel">Strong inverse (DXY falling)</span>
      </div>
    </div>

    <!-- COT VISUALIZATION -->
    <div style="margin-top:var(--gap-md);padding:var(--gap-md);background:var(--bg-card);border-radius:var(--radius-sm);">
      <div style="font-size:10px;color:var(--text-muted);margin-bottom:8px;text-transform:uppercase;letter-spacing:0.5px;">
        COT Positioning Distribution
      </div>
      <div style="display:flex;align-items:center;gap:8px;height:28px;">
        <span style="font-size:10px;color:var(--text-muted);width:60px;">Non-Comm</span>
        <div style="flex:1;display:flex;align-items:center;gap:4px;background:var(--bg-section);border-radius:4px;overflow:hidden;height:22px;position:relative;">
          <div style="position:absolute;left:50%;top:0;bottom:0;width:1px;background:var(--border-active);z-index:1;"></div>
          <div style="flex:0 0 65%;height:100%;background:linear-gradient(90deg,rgba(239,68,68,0.5),rgba(239,68,68,0.2));display:flex;align-items:center;justify-content:flex-end;padding-right:8px;">
            <span style="font-family:var(--font-mono);font-size:10px;color:var(--bear);font-weight:600;">84K Short</span>
          </div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;height:28px;margin-top:4px;">
        <span style="font-size:10px;color:var(--text-muted);width:60px;">Commercial</span>
        <div style="flex:1;display:flex;align-items:center;gap:4px;background:var(--bg-section);border-radius:4px;overflow:hidden;height:22px;position:relative;">
          <div style="position:absolute;left:50%;top:0;bottom:0;width:1px;background:var(--border-active);z-index:1;"></div>
          <div style="flex:0 0 78%;height:100%;background:linear-gradient(90deg,rgba(16,185,129,0.2),rgba(16,185,129,0.5));display:flex;align-items:center;padding-left:8px;">
            <span style="font-family:var(--font-mono);font-size:10px;color:var(--bull);font-weight:600;">112K Long</span>
          </div>
        </div>
      </div>
    </div>

    <!-- OPTIONS RECOMMENDATION -->
    <div class="options-rec buy-call">
      <div class="options-rec-title" style="color:var(--bull);">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M7 17l9.2-9.2M17 17V8H8"/>
        </svg>
        CONTRARIAN LONG - COT EXTREME
      </div>
      <div class="options-rec-desc">
        Speculators are <strong style="color:var(--bear);">extremely short (-84K)</strong> while commercials 
        (smart money) are heavily long. This is a classic COT contrarian setup.
        DXY correlation at <strong>-0.87</strong> suggests EUR/USD will rise as DXY weakens.
        <br><br>
        <strong>Strategy:</strong> Buy EUR/USD Call Options / Long Spot with tight stop
      </div>
      <span class="rec-tag tag-buy">CONTRARIAN LONG</span>
    </div>
  </div>

  <!-- THESIS PANEL -->
  <div class="thesis-section">
    <div class="thesis-label">Thesis</div>
    <ul class="thesis-list">
      <li class="thesis-item">
        <span class="thesis-icon icon-bull">&#8593;</span>
        <span>COT extreme short positioning = crowded trade, reversal likely</span>
      </li>
      <li class="thesis-item">
        <span class="thesis-icon icon-bull">&#8593;</span>
        <span>Commercials (smart money) net long +112K = bullish hedge</span>
      </li>
      <li class="thesis-item">
        <span class="thesis-icon icon-bull">&#8593;</span>
        <span>DXY -0.87 correlation with DXY heading lower = EUR/USD tailwind</span>
      </li>
      <li class="thesis-item">
        <span class="thesis-icon icon-neutral">&#9679;</span>
        <span>Entry at 1.0780 key support confluence (fib + structure)</span>
      </li>
    </ul>
  </div>

  <!-- EXECUTION CHECKLIST -->
  <div class="execution-section">
    <div class="execution-label">Execution Checklist</div>
    <div class="checklist">
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">COT non-commercial &gt; 70th percentile short</span>
      </div>
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">Commercial divergence (opposite direction)</span>
      </div>
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">DXY correlation confirming directional edge</span>
      </div>
      <div class="check-item pending">
        <div class="check-box">&#8635;</div>
        <span class="check-text">Price at technical support for entry trigger</span>
      </div>
      <div class="check-item pending">
        <div class="check-box">&#8635;</div>
        <span class="check-text">Stop placed below 1.0750 (structural low)</span>
      </div>
    </div>
  </div>

</div>
```

### Forex Card Design Notes
- **COT positioning** visualized with horizontal bar showing non-commercial vs commercial
- Extreme readings trigger contrarian signal automatically
- DXY correlation shown as inverse - strong negative = bullish for EUR/USD
- Flow indicators with arrows (↑↓) for intuitive directional read
- Institutional sentiment as a gauge bar (0-100% bullish)

---

## 3. COMMODITIES Card

**Market-Specific Data**: COT positioning, term structure (contango/backwardation), seasonality

**Options Recommendation**: "Backwardation + COT commercial buying → bullish structure"

```html
<!-- ==================== COMMODITIES CARD ==================== -->
<div class="ticker-card commodities">

  <!-- HEADER -->
  <div class="card-header">
    <div class="ticker-info">
      <div>
        <div class="ticker-symbol">GC=F</div>
        <div class="ticker-name">Gold Futures</div>
      </div>
      <span class="ticker-badge badge-commodities">Commodity</span>
    </div>
    <div class="price-display">
      <div class="price-current up">$2,045.80</div>
      <div class="price-change up">+12.40 (+0.61%)</div>
    </div>
  </div>

  <!-- ENTRY ZONE BAR -->
  <div class="entry-zone-section">
    <div class="zone-label">
      <span>Entry Zone</span>
      <span style="color:var(--text-muted);">R:R = 1:2.5</span>
    </div>
    <div class="zone-bar-container">
      <div class="zone-stop">
        <span>STOP</span>
      </div>
      <div class="zone-entry">
        <span class="zone-entry-label">Entry</span>
        <span class="zone-entry-price">$2,028</span>
      </div>
      <div class="zone-targets">
        <div class="zone-t1">
          <span class="zone-target-label">T1</span>
          <span class="zone-target-price">$2,065</span>
        </div>
        <div class="zone-t2">
          <span class="zone-target-label">T2</span>
          <span class="zone-target-price">$2,085</span>
        </div>
        <div class="zone-t3">
          <span class="zone-target-label">T3</span>
          <span class="zone-target-price">$2,110</span>
        </div>
      </div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:6px;padding:0 2px;">
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--bear);">$2,015</span>
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--neutral);">$2,028 - $2,035</span>
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--bull);">$2,110</span>
    </div>
  </div>

  <!-- MARKET-SPECIFIC: COT + TERM STRUCTURE PANEL -->
  <div class="market-panel">
    <div class="panel-label">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 6v6l4 2"/>
      </svg>
      Commodity Structure & Positioning
    </div>
    <div class="data-grid">
      <div class="data-cell">
        <span class="data-label">Term Structure</span>
        <span class="data-value" style="color:var(--bull);">Backwardation</span>
        <span class="data-sublabel">Spot &gt; Front month = tight supply</span>
      </div>
      <div class="data-cell">
        <span class="data-label">COT Producer Net</span>
        <div class="flow-indicator">
          <span class="flow-arrow flow-in">&#8593;</span>
          <span class="flow-value" style="color:var(--bear);">-156K</span>
        </div>
        <span class="data-sublabel">Producers short hedging (normal)</span>
      </div>
      <div class="data-cell">
        <span class="data-label">Money Manager Net</span>
        <div class="flow-indicator">
          <span class="flow-arrow flow-in">&#8593;</span>
          <span class="flow-value" style="color:var(--bull);">+89,400</span>
        </div>
        <span class="data-sublabel">Speculators accumulating longs</span>
      </div>
      <div class="data-cell">
        <span class="data-label">Seasonality</span>
        <span class="data-value" style="color:var(--bull);">+2.8% avg</span>
        <span class="data-sublabel">January seasonal strength</span>
      </div>
    </div>

    <!-- TERM STRUCTURE VISUALIZATION -->
    <div style="margin-top:var(--gap-md);padding:var(--gap-md);background:var(--bg-card);border-radius:var(--radius-sm);">
      <div style="font-size:10px;color:var(--text-muted);margin-bottom:10px;text-transform:uppercase;letter-spacing:0.5px;">
        Futures Curve (Term Structure)
      </div>
      <div style="display:flex;align-items:flex-end;gap:6px;height:70px;justify-content:center;">
        <div style="display:flex;flex-direction:column;align-items:center;gap:4px;">
          <span style="font-family:var(--font-mono);font-size:9px;color:var(--bull);font-weight:600;">$2,048</span>
          <div style="width:28px;height:55px;background:linear-gradient(to top,rgba(16,185,129,0.4),rgba(16,185,129,0.7));border-radius:4px 4px 0 0;display:flex;align-items:flex-end;justify-content:center;">
            <span style="font-size:8px;color:#fff;font-weight:700;padding-bottom:4px;">Spot</span>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:4px;">
          <span style="font-family:var(--font-mono);font-size:9px;color:var(--bull);font-weight:600;">$2,046</span>
          <div style="width:28px;height:48px;background:linear-gradient(to top,rgba(16,185,129,0.3),rgba(16,185,129,0.5));border-radius:4px 4px 0 0;display:flex;align-items:flex-end;justify-content:center;">
            <span style="font-size:8px;color:#fff;font-weight:700;padding-bottom:4px;">M1</span>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:4px;">
          <span style="font-family:var(--font-mono);font-size:9px;color:var(--neutral);font-weight:600;">$2,040</span>
          <div style="width:28px;height:40px;background:linear-gradient(to top,rgba(59,130,246,0.2),rgba(59,130,246,0.4));border-radius:4px 4px 0 0;display:flex;align-items:flex-end;justify-content:center;">
            <span style="font-size:8px;color:#fff;font-weight:700;padding-bottom:4px;">M2</span>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:4px;">
          <span style="font-family:var(--font-mono);font-size:9px;color:var(--neutral);font-weight:600;">$2,035</span>
          <div style="width:28px;height:33px;background:linear-gradient(to top,rgba(59,130,246,0.15),rgba(59,130,246,0.3));border-radius:4px 4px 0 0;display:flex;align-items:flex-end;justify-content:center;">
            <span style="font-size:8px;color:#fff;font-weight:700;padding-bottom:4px;">M3</span>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:4px;">
          <span style="font-family:var(--font-mono);font-size:9px;color:var(--text-secondary);font-weight:600;">$2,028</span>
          <div style="width:28px;height:28px;background:linear-gradient(to top,rgba(148,163,184,0.15),rgba(148,163,184,0.3));border-radius:4px 4px 0 0;display:flex;align-items:flex-end;justify-content:center;">
            <span style="font-size:8px;color:#fff;font-weight:700;padding-bottom:4px;">M6</span>
          </div>
        </div>
      </div>
      <div style="display:flex;align-items:center;justify-content:center;gap:6px;margin-top:8px;">
        <span style="font-size:10px;color:var(--bull);font-weight:600;">&#9660; Backwardation</span>
        <span style="font-size:10px;color:var(--text-muted);">= Bullish supply tightness</span>
      </div>
    </div>

    <!-- OPTIONS RECOMMENDATION -->
    <div class="options-rec buy-call">
      <div class="options-rec-title" style="color:var(--bull);">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2v20M2 12h20"/>
        </svg>
        STRUCTURAL LONG - BACKWARDATION + COT
      </div>
      <div class="options-rec-desc">
        Backwardation (spot &gt; futures) indicates <strong style="color:var(--bull);">physical supply tightness</strong>. 
        Combined with money managers net long +89K and positive January seasonality (+2.8% avg), 
        the structure supports bullish positioning.
        <br><br>
        <strong>Strategy:</strong> Buy Gold Calls or Call Spread. Backwardation means futures roll yields positive carry for longs.
      </div>
      <span class="rec-tag tag-buy">STRUCTURAL LONG</span>
    </div>
  </div>

  <!-- THESIS PANEL -->
  <div class="thesis-section">
    <div class="thesis-label">Thesis</div>
    <ul class="thesis-list">
      <li class="thesis-item">
        <span class="thesis-icon icon-bull">&#8593;</span>
        <span>Backwardation structure = physical demand exceeding supply</span>
      </li>
      <li class="thesis-item">
        <span class="thesis-icon icon-bull">&#8593;</span>
        <span>Money managers accumulating longs (+89K) = institutional interest</span>
      </li>
      <li class="thesis-item">
        <span class="thesis-icon icon-bull">&#8593;</span>
        <span>January seasonality +2.8% average = tailwind</span>
      </li>
      <li class="thesis-item">
        <span class="thesis-icon icon-warning">!</span>
        <span>Watch for contango flip if futures curve inverts = supply relief</span>
      </li>
    </ul>
  </div>

  <!-- EXECUTION CHECKLIST -->
  <div class="execution-section">
    <div class="execution-label">Execution Checklist</div>
    <div class="checklist">
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">Term structure in backwardation</span>
      </div>
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">COT money manager net long &gt; 50K</span>
      </div>
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">Seasonality window favorable (Jan)</span>
      </div>
      <div class="check-item pending">
        <div class="check-box">&#8635;</div>
        <span class="check-text">Entry at $2,028 support (200 DMA)</span>
      </div>
      <div class="check-item pending">
        <div class="check-box">&#8635;</div>
        <span class="check-text">Stop below $2,015 (curve support break)</span>
      </div>
    </div>
  </div>

</div>
```

### Commodities Card Design Notes
- **Term structure** visualized as a futures curve bar chart (spot → M6)
- Downward sloping curve = backwardation (bullish, green gradient)
- Upward sloping curve = contango (bearish, would be red gradient)
- COT shows producer hedging (normal) vs money manager positioning (signal)
- Seasonality displayed as expected average move for the current month
- Flow arrows indicate directional COT changes week-over-week

---

## 4. CRYPTO Card

**Market-Specific Data**: Laevitas GEX, funding rate, DeFiLlama TVL change, on-chain flows

**Options Recommendation**: "Negative GEX + funding negative → short squeeze potential"

```html
<!-- ==================== CRYPTO CARD ==================== -->
<div class="ticker-card crypto">

  <!-- HEADER -->
  <div class="card-header">
    <div class="ticker-info">
      <div>
        <div class="ticker-symbol">BTC</div>
        <div class="ticker-name">Bitcoin</div>
      </div>
      <span class="ticker-badge badge-crypto">Crypto</span>
    </div>
    <div class="price-display">
      <div class="price-current up">$43,250</div>
      <div class="price-change up">+$890 (+2.1%)</div>
    </div>
  </div>

  <!-- ENTRY ZONE BAR -->
  <div class="entry-zone-section">
    <div class="zone-label">
      <span>Entry Zone</span>
      <span style="color:var(--text-muted);">R:R = 1:3.5</span>
    </div>
    <div class="zone-bar-container">
      <div class="zone-stop">
        <span>STOP</span>
      </div>
      <div class="zone-entry">
        <span class="zone-entry-label">Entry</span>
        <span class="zone-entry-price">$42,100</span>
      </div>
      <div class="zone-targets">
        <div class="zone-t1">
          <span class="zone-target-label">T1</span>
          <span class="zone-target-price">$44,200</span>
        </div>
        <div class="zone-t2">
          <span class="zone-target-label">T2</span>
          <span class="zone-target-price">$45,800</span>
        </div>
        <div class="zone-t3">
          <span class="zone-target-label">T3</span>
          <span class="zone-target-price">$48,000</span>
        </div>
      </div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:6px;padding:0 2px;">
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--bear);">$41,500</span>
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--neutral);">$42,100 - $42,600</span>
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--bull);">$48,000</span>
    </div>
  </div>

  <!-- MARKET-SPECIFIC: GEX + FUNDING + ON-CHAIN PANEL -->
  <div class="market-panel">
    <div class="panel-label">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
      </svg>
      Crypto Derivatives & On-Chain
    </div>
    <div class="data-grid">
      <div class="data-cell">
        <span class="data-label">GEX (Gamma Exposure)</span>
        <span class="data-value" style="color:var(--bull);">-$2.4B</span>
        <span class="data-sublabel">Negative = short squeeze fuel</span>
        <div class="gauge-bar"><div class="gauge-fill gauge-red" style="width:75%"></div></div>
      </div>
      <div class="data-cell">
        <span class="data-label">Funding Rate</span>
        <span class="data-value" style="color:var(--bull);">-0.008%</span>
        <span class="data-sublabel">Shorts paying longs = bearish crowded</span>
      </div>
      <div class="data-cell">
        <span class="data-label">DeFiLlama TVL Change</span>
        <div class="flow-indicator">
          <span class="flow-arrow flow-in">&#8593;</span>
          <span class="flow-value" style="color:var(--bull);">+3.2%</span>
        </div>
        <span class="data-sublabel">7-day change ($47.2B total)</span>
      </div>
      <div class="data-cell">
        <span class="data-label">On-Chain Netflow</span>
        <div class="flow-indicator">
          <span class="flow-arrow flow-out">&#8595;</span>
          <span class="flow-value" style="color:var(--bull);">-$285M</span>
        </div>
        <span class="data-sublabel">Exchange outflows (bullish)</span>
      </div>
    </div>

    <!-- GEX HORIZONTAL BAR VISUALIZATION -->
    <div style="margin-top:var(--gap-md);padding:var(--gap-md);background:var(--bg-card);border-radius:var(--radius-sm);">
      <div style="font-size:10px;color:var(--text-muted);margin-bottom:10px;text-transform:uppercase;letter-spacing:0.5px;">
        Gamma Exposure Profile
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
        <span style="font-size:10px;color:var(--text-muted);width:50px;text-align:right;">+$5B</span>
        <div style="flex:1;height:20px;background:var(--bg-section);border-radius:4px;overflow:hidden;position:relative;">
          <div style="position:absolute;left:50%;top:0;bottom:0;width:2px;background:var(--text-muted);z-index:2;"></div>
          <div style="position:absolute;left:45%;top:0;bottom:0;width:25%;background:linear-gradient(90deg,rgba(239,68,68,0.3),rgba(239,68,68,0.6));border-radius:0 4px 4px 0;"></div>
          <div style="position:absolute;right:4px;top:50%;transform:translateY(-50%);font-family:var(--font-mono);font-size:9px;color:var(--bear);font-weight:600;">NEG</div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="font-size:10px;color:var(--text-muted);width:50px;text-align:right;">-$5B</span>
        <div style="flex:1;display:flex;align-items:center;gap:4px;">
          <span style="font-size:10px;color:var(--bull);font-weight:600;">&#9668; Negative GEX zone = magnet higher</span>
        </div>
      </div>
    </div>

    <!-- OPTIONS RECOMMENDATION -->
    <div class="options-rec buy-call">
      <div class="options-rec-title" style="color:var(--bull);">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>
        SHORT SQUEEZE SETUP - NEGATIVE GEX
      </div>
      <div class="options-rec-desc">
        Negative GEX at <strong style="color:var(--bear);">-$2.4B</strong> means dealers are short gamma and must 
        <strong>buy futures as price rises</strong> (buy-high feedback loop). Funding at 
        <strong style="color:var(--bull);">-0.008%</strong> confirms shorts are crowded and paying longs. 
        Combined with exchange outflows (-$285M) = supply squeeze setup.
        <br><br>
        <strong>Strategy:</strong> Buy BTC Call Spreads or Long Perp with negative funding collecting
      </div>
      <span class="rec-tag tag-buy">SHORT SQUEEZE PLAY</span>
    </div>
  </div>

  <!-- THESIS PANEL -->
  <div class="thesis-section">
    <div class="thesis-label">Thesis</div>
    <ul class="thesis-list">
      <li class="thesis-item">
        <span class="thesis-icon icon-bull">&#8593;</span>
        <span>Negative GEX (-$2.4B) = dealer short gamma, reflexive buying above strikes</span>
      </li>
      <li class="thesis-item">
        <span class="thesis-icon icon-bull">&#8593;</span>
        <span>Negative funding (-0.008%) = shorts crowded, contrarian long edge</span>
      </li>
      <li class="thesis-item">
        <span class="thesis-icon icon-bull">&#8593;</span>
        <span>Exchange outflows (-$285M) = coins moving to cold storage = supply shock</span>
      </li>
      <li class="thesis-item">
        <span class="thesis-icon icon-bull">&#8593;</span>
        <span>TVL rising +3.2% = DeFi ecosystem growing = fundamental demand</span>
      </li>
    </ul>
  </div>

  <!-- EXECUTION CHECKLIST -->
  <div class="execution-section">
    <div class="execution-label">Execution Checklist</div>
    <div class="checklist">
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">GEX negative (dealer short gamma environment)</span>
      </div>
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">Funding rate negative (shorts paying longs)</span>
      </div>
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">Exchange net outflows (supply leaving)</span>
      </div>
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">TVL trending up (ecosystem growth)</span>
      </div>
      <div class="check-item pending">
        <div class="check-box">&#8635;</div>
        <span class="check-text">Set stop below $41,500 (GEX flip zone)</span>
      </div>
    </div>
  </div>

</div>
```

### Crypto Card Design Notes
- **GEX (Gamma Exposure)** is the primary crypto-specific metric - shown as value + gauge
- Negative GEX visualized with red bar extending left from center = bearish positioning that creates squeeze potential
- **Funding rate** negative = shorts pay longs = contrarian opportunity
- **On-chain netflow** uses flow arrows (↓ outflow = bullish, ↑ inflow = bearish)
- **TVL change** from DeFiLlama as fundamental ecosystem health indicator
- Options rec explains the mechanics: dealer short gamma + negative funding = reflexive squeeze

---

## 5. IHSG Card

**Market-Specific Data**: Broker flow, foreign buying/selling, IDX30 composition

**Options Recommendation**: "Foreign net buy 3 hari berturut + harga di bawah max pain → akumulasi"

```html
<!-- ==================== IHSG CARD ==================== -->
<div class="ticker-card ihsg">

  <!-- HEADER -->
  <div class="card-header">
    <div class="ticker-info">
      <div>
        <div class="ticker-symbol">BBCA</div>
        <div class="ticker-name">Bank Central Asia Tbk</div>
      </div>
      <span class="ticker-badge badge-ihsg">IHSG</span>
    </div>
    <div class="price-display">
      <div class="price-current up">Rp 8,950</div>
      <div class="price-change up">+125 (+1.42%)</div>
    </div>
  </div>

  <!-- ENTRY ZONE BAR -->
  <div class="entry-zone-section">
    <div class="zone-label">
      <span>Entry Zone</span>
      <span style="color:var(--text-muted);">R:R = 1:2.8</span>
    </div>
    <div class="zone-bar-container">
      <div class="zone-stop">
        <span>STOP</span>
      </div>
      <div class="zone-entry">
        <span class="zone-entry-label">Entry</span>
        <span class="zone-entry-price">8,775</span>
      </div>
      <div class="zone-targets">
        <div class="zone-t1">
          <span class="zone-target-label">T1</span>
          <span class="zone-target-price">9,150</span>
        </div>
        <div class="zone-t2">
          <span class="zone-target-label">T2</span>
          <span class="zone-target-price">9,350</span>
        </div>
        <div class="zone-t3">
          <span class="zone-target-label">T3</span>
          <span class="zone-target-price">9,600</span>
        </div>
      </div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:6px;padding:0 2px;">
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--bear);">8,650</span>
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--neutral);">8,775 - 8,850</span>
      <span style="font-family:var(--font-mono);font-size:10px;color:var(--bull);">9,600</span>
    </div>
  </div>

  <!-- MARKET-SPECIFIC: BROKER FLOW + FOREIGN PANEL -->
  <div class="market-panel">
    <div class="panel-label">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>
      </svg>
      Aliran Broker & Asing (3 Hari)
    </div>
    <div class="data-grid">
      <div class="data-cell">
        <span class="data-label">Net Foreign (3D)</span>
        <div class="flow-indicator">
          <span class="flow-arrow flow-in">&#8593;</span>
          <span class="flow-value" style="color:var(--bull);">+Rp 412B</span>
        </div>
        <span class="data-sublabel">3 hari berturut-turut net buy</span>
      </div>
      <div class="data-cell">
        <span class="data-label">Net Broker Local</span>
        <div class="flow-indicator">
          <span class="flow-arrow flow-out">&#8595;</span>
          <span class="flow-value" style="color:var(--bear);">-Rp 198B</span>
        </div>
        <span class="data-sublabel">Local profit taking</span>
      </div>
      <div class="data-cell">
        <span class="data-label">Foreign Ownership</span>
        <span class="data-value" style="color:var(--neutral);">78.4%</span>
        <div class="gauge-bar"><div class="gauge-fill gauge-blue" style="width:78%"></div></div>
        <span class="data-sublabel">Dokumen lawan 79.1%</span>
      </div>
      <div class="data-cell">
        <span class="data-label">IDX30 Weight</span>
        <span class="data-value" style="color:var(--accent-ihsg);">8.2%</span>
        <span class="data-sublabel">Top 3 constituent</span>
      </div>
    </div>

    <!-- FLOW TREND VISUALIZATION -->
    <div style="margin-top:var(--gap-md);padding:var(--gap-md);background:var(--bg-card);border-radius:var(--radius-sm);">
      <div style="font-size:10px;color:var(--text-muted);margin-bottom:10px;text-transform:uppercase;letter-spacing:0.5px;">
        Tren Aliran Asing (5 Sesi Terakhir)
      </div>
      <div style="display:flex;align-items:flex-end;gap:8px;height:55px;justify-content:center;">
        <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
          <span style="font-family:var(--font-mono);font-size:9px;color:var(--bull);font-weight:600;">+85B</span>
          <div style="width:24px;height:22px;background:linear-gradient(to top,rgba(16,185,129,0.4),rgba(16,185,129,0.7));border-radius:3px 3px 0 0;"></div>
          <span style="font-size:8px;color:var(--text-muted);">T-4</span>
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
          <span style="font-family:var(--font-mono);font-size:9px;color:var(--bull);font-weight:600;">+120B</span>
          <div style="width:24px;height:30px;background:linear-gradient(to top,rgba(16,185,129,0.5),rgba(16,185,129,0.8));border-radius:3px 3px 0 0;"></div>
          <span style="font-size:8px;color:var(--text-muted);">T-3</span>
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
          <span style="font-family:var(--font-mono);font-size:9px;color:var(--bull);font-weight:600;">+95B</span>
          <div style="width:24px;height:25px;background:linear-gradient(to top,rgba(16,185,129,0.4),rgba(16,185,129,0.7));border-radius:3px 3px 0 0;"></div>
          <span style="font-size:8px;color:var(--text-muted);">T-2</span>
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
          <span style="font-family:var(--font-mono);font-size:9px;color:var(--bull);font-weight:600;">+112B</span>
          <div style="width:24px;height:28px;background:linear-gradient(to top,rgba(16,185,129,0.6),rgba(16,185,129,0.9));border-radius:3px 3px 0 0;border:1px solid var(--bull);"></div>
          <span style="font-size:8px;color:var(--bull);font-weight:700;">T-1</span>
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
          <span style="font-family:var(--font-mono);font-size:9px;color:var(--neutral);font-weight:600;">--</span>
          <div style="width:24px;height:4px;background:var(--bg-hover);border-radius:3px;"></div>
          <span style="font-size:8px;color:var(--text-muted);">Tdy</span>
        </div>
      </div>
    </div>

    <!-- OPTIONS RECOMMENDATION -->
    <div class="options-rec buy-call">
      <div class="options-rec-title" style="color:var(--bull);">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M7 17l9.2-9.2M17 17V8H8"/>
        </svg>
        AKUMULASI - ASING NET BUY 3 HARI + DI BAWAH MAX PAIN
      </div>
      <div class="options-rec-desc">
        Asing net buy <strong style="color:var(--bull);">3 hari berturut-turut</strong> (total +Rp 412B) sementara 
        harga masih berada di bawah max pain level. Foreign ownership di <strong>78.4%</strong> 
        (dibawah puncak 79.1%) = masih ada ruang akumulasi. Broker lokal net sell 
        mengkonfirmasi distribusi ke tangan lebih kuat.
        <br><br>
        <strong>Strategy:</strong> Akumulasi pelan di zona entry. Gunakan DW/Call option jika tersedia dengan leverage terukur.
      </div>
      <span class="rec-tag tag-buy">AKUMULASI</span>
    </div>
  </div>

  <!-- THESIS PANEL -->
  <div class="thesis-section">
    <div class="thesis-label">Thesis</div>
    <ul class="thesis-list">
      <li class="thesis-item">
        <span class="thesis-icon icon-bull">&#8593;</span>
        <span>Asing net buy 3 hari berturut = akumulasi institusional</span>
      </li>
      <li class="thesis-item">
        <span class="thesis-icon icon-bull">&#8593;</span>
        <span>Harga di bawah max pain = kemungkinan pin ke strike</span>
      </li>
      <li class="thesis-item">
        <span class="thesis-icon icon-bull">&#8593;</span>
        <span>BBCA 8.2% IDX30 = blue chip defensif dengan yield 2.8%</span>
      </li>
      <li class="thesis-item">
        <span class="thesis-icon icon-warning">!</span>
        <span>Monitor foreign ownership limit 79% (hampir penuh)</span>
      </li>
    </ul>
  </div>

  <!-- EXECUTION CHECKLIST -->
  <div class="execution-section">
    <div class="execution-label">Execution Checklist</div>
    <div class="checklist">
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">Foreign net buy 3+ hari berturut-turut</span>
      </div>
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">Harga di bawah max pain level</span>
      </div>
      <div class="check-item passed">
        <div class="check-box">&#10003;</div>
        <span class="check-text">IDX30 top constituent (liquid)</span>
      </div>
      <div class="check-item pending">
        <div class="check-box">&#8635;</div>
        <span class="check-text">Entry di zona 8,775 - 8,850</span>
      </div>
      <div class="check-item pending">
        <div class="check-box">&#8635;</div>
        <span class="check-text">Stop di bawah 8,650 (support struktur)</span>
      </div>
    </div>
  </div>

</div>
```

### IHSG Card Design Notes
- **Broker flow** displayed as foreign vs local with directional arrows
- **Foreign buying streak** (3+ hari) is the key signal for IHSG accumulation
- **Flow trend** visualized as 5-session bar chart showing foreign flow consistency
- **Foreign ownership %** shown with gauge - approaching limit = scarcity premium
- **IDX30 weight** confirms blue-chip status and index support
- Options rec in Bahasa Indonesia reflecting local market context
- Uses Rupiah (Rp) formatting for price display

---

## Complete HTML Page

To view all cards together, wrap the shared CSS above with all 5 card HTML bodies and close the tags:

```html
</body>
</html>
```

Save as a single `.html` file and open in browser to see all 5 market cards rendered.

---

## Design System Summary

| Element | Description | Color Logic |
|---------|-------------|-------------|
| **Entry Zone Bar** | Visual stop → entry → targets | Red → Blue → Green gradient |
| **Zone Labels** | STOP / Entry / T1 / T2 / T3 | Red / Blue / Green text |
| **Thesis Icons** | Bull/bear/neutral/warning signals | Green up / Red down / Blue dot / Yellow ! |
| **Checklist States** | Passed / Pending / Failed | Green check / Yellow refresh / Red X |
| **Options Rec Box** | Strategy recommendation | Green=Buy, Red=Avoid, Blue=Neutral |
| **Data Gauges** | IV rank, sentiment, ownership | Fill width = magnitude, color = direction |
| **Flow Arrows** | COT, on-chain, broker flows | ↑ Green=inflow/bullish, ↓ Red=outflow/bearish |
| **Market Accent** | Top border color per category | Stocks=Green, Forex=Purple, Comm=Yellow, Crypto=Cyan, IHSG=Pink |

---

## Responsive Behavior

- **Desktop (>480px)**: Full layout with 2-column data grids, all labels visible
- **Mobile (≤480px)**: Single column grids, abbreviated zone labels, stacked layout
- All cards max-width 480px centered - designed for mobile-first trading dashboards

---

## Implementation Notes

1. **Dynamic data binding**: Replace hardcoded values with template variables (e.g., `{{iv_percentile}}`)
2. **Conditional classes**: Options rec box class should toggle between `buy-call`, `buy-put`, `neutral` based on logic
3. **Gauge widths**: Set inline `style="width:X%"` dynamically based on data values
4. **Checklist states**: Toggle `passed`/`pending`/`failed` classes based on rule engine output
5. **Entry zone**: The blue arrow (`::after` pseudo-element) marks current price position within the zone
