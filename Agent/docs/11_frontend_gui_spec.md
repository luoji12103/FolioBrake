# 11 — Frontend GUI Specification

## Framework decision

Preferred stack:

- Tauri.
- React.
- TypeScript.
- TanStack Query.
- ECharts or Recharts.
- Tailwind or simple component library.

Electron fallback is acceptable if Tauri becomes a schedule risk.

## Design principle

The GUI must make risk decisions obvious. Do not bury audit failures or do-not-trade warnings behind performance charts.

## Core screens

### 1. Dashboard

Purpose: show current system state.

Widgets:

- Current risk state: NORMAL / CAUTION / DEFENSIVE / HALT.
- Latest strategy signal status.
- Latest audit grade.
- Portfolio value and drawdown.
- Next scheduled rebalance.
- Warnings and blocked trades.

### 2. ETF Universe

Purpose: inspect tradable ETFs.

Columns:

- Symbol.
- Name.
- Category.
- Asset class.
- Latest close.
- Liquidity score.
- Data quality status.
- Active/inactive.

Actions:

- Import universe.
- Toggle ETF active status.
- View ETF chart.

### 3. Strategy Signals

Purpose: explain weekly allocation decision.

Views:

- Ranked ETF score table.
- Signal contribution breakdown.
- Target weights before risk overlay.
- Final weights after risk overlay.
- Buy/sell/hold list.

Required explanation:

- Why buy.
- Why sell.
- Why hold.
- Why not trade.

### 4. Risk Overlay

Purpose: show do-not-trade status.

Panels:

- Risk state timeline.
- Triggered rules.
- Blocked/reduced/manual-confirm trades.
- Market trend status.
- Volatility percentile.
- Portfolio drawdown.
- Liquidity warnings.

### 5. Backtest

Purpose: configure and run backtests.

Inputs:

- Strategy.
- Risk profile.
- Universe.
- Date range.
- Initial cash.
- Cost bps.
- Slippage bps.
- Rebalance frequency.

Outputs:

- Equity curve.
- Drawdown chart.
- Monthly returns heatmap.
- Metrics table.
- Trades table.
- Benchmark comparison.

### 6. Audit Gatekeeper

Purpose: show whether a strategy is deployable.

Visuals:

- GREEN/YELLOW/RED badge.
- Audit score.
- Check table.
- Critical failures.
- Recommendations.

Checks:

- Leakage.
- Walk-forward.
- Parameter stability.
- Cost stress.
- Regime robustness.
- Turnover feasibility.

### 7. Paper Portfolio

Purpose: simulated deployment.

Views:

- Current holdings.
- Cash.
- Orders.
- Trade history.
- Simulated P&L.
- Pending signal application.

Rules:

- Applying signal should require a GREEN audit status by default.
- In dev mode, allow override with warning.

### 8. Settings

Purpose: configure user profile and data sources.

Sections:

- Risk profile.
- Data sources.
- Costs/slippage.
- Scheduler.
- API server URL.
- Local storage.

## UX copy examples

Do not say:

> The strategy will make money.

Say:

> The strategy passed the current audit profile and is eligible for simulated deployment. Historical performance is not a guarantee of future results.

Do not say:

> Buy this ETF now.

Say:

> The model target weight increased. Review the simulated order and risk explanation before taking any real-world action.

## Frontend API rules

- Use typed API client generated from OpenAPI if time permits.
- All user-visible data should include `as_of_date`.
- Charts must identify whether values are backtest, simulated, or live snapshot.
- GUI should handle API offline state gracefully.
