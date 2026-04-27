# Retail ETF Guardian — Handoff Prompt for Claude Code

## Project identity

You are implementing **Retail ETF Guardian**, a risk-aware ETF trading decision system for individual investors targeting A-share exchange-traded ETFs. This is the FTEC 4320 Track B practical final project.

The system combines three components:
- **A — Risk-aware ETF rotation**: weekly portfolio allocation under drawdown, turnover, concentration, and volatility constraints.
- **B — Backtest audit gatekeeper**: walk-forward, parameter stability, cost stress, leakage checks, and robustness scoring before a strategy is allowed into paper trading.
- **C — Do-Not-Trade risk overlay**: daily checks that can suppress trades, reduce risk, or require manual confirmation under abnormal market conditions.

The ultimate deadline is **May 29, 2026**. The presentation may be earlier. Keep moving.

## Frozen decisions — do not redesign

- **Product**: Fused A+B+C. Name: Retail ETF Guardian.
- **Market**: A-share ETFs only for MVP.
- **Users**: Individual investors, USD 5k–100k account size, low-frequency.
- **Objective**: Risk-adjusted return improvement, not raw return maximization.
- **Frequency**: Weekly rebalance, daily risk checks, intraday warnings only.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic.
- **Data stores**: PostgreSQL 16, Redis 7.
- **Data sources**: AKShare primary, Tushare/efinance optional fallback.
- **Backtest**: Self-built lightweight engine (not a generic framework). vectorbt optional for research.
- **Frontend**: Tauri + React + TypeScript. Electron fallback only if Tauri blocks.
- **Deployment**: Backend-first Docker Compose. The Compose stack is the PRIMARY deployment path, not an afterthought. GUI runs outside Docker as a desktop client connecting via HTTP/WebSocket.
- **Non-goals for MVP**: No real-money auto-trading. No HFT. No Kubernetes. No GUI containerization. No reinforcement learning.

## Architecture

```
Tauri Desktop GUI (outside Docker)
        |
        | HTTP/WebSocket → localhost:8000
        v
+------------------------------------------+
| Docker Compose backend stack              |
|                                          |
|  FastAPI API Server                      |
|       |                                  |
|       +---------------+                  |
|       |               |                  |
|       v               v                  |
|  PostgreSQL        Redis / Queue         |
|       |               |                  |
|       v               v                  |
|  Data Worker    Strategy / Backtest      |
|                 / Audit Workers          |
|                 + Scheduler              |
+------------------------------------------+
        |
        v
AKShare / Tushare / efinance
```

## Repository structure (target)

```
retail-etf-guardian/
  backend/
    app/
      api/           # FastAPI routes
      core/          # config, settings
      db/            # session, base, migrations (Alembic)
      data/          # instrument models, bars, AKShare adapter, quality checks
      features/      # feature registry, trend/momentum/vol/drawdown/liquidity features
      strategy/      # risk_aware_etf_rotation_v1, scoring, constraints, explanation logs
      risk/          # do-not-trade state machine, rule checks, overlay decisions
      backtest/      # portfolio simulator, rebalance, costs, metrics
      audit/         # leakage, walk-forward, param stability, cost stress, grading
      paper/         # simulated portfolio, order ledger
      reports/       # report figure/data generation
      workers/       # Celery or background task workers
      tests/
    pyproject.toml
    Dockerfile
  frontend/
    src/             # React + TypeScript app
    src-tauri/       # Tauri native shell
    package.json
  ops/
    docker-compose.yml
    docker-compose.dev.yml
    .env.example
  config/
    universe/        # ETF symbol lists
    strategies/      # strategy configs (JSON)
    risk_profiles/   # risk profile definitions
  docs/
  scripts/
  README.md
```

## Dependency graph and execution order

```
Phase 0 (scaffold) ─────────────────────────────────────────┐
        |                                                    |
        v                                                    |
Phase 1 (data ingestion) ───────┐                           |
        |                        |                           |
        v                        v                           |
Phase 2 (features)          Phase 5 (risk overlay)          |
        |                        |                           |
        v                        |                           |
Phase 3 (strategy engine)       |                           |
        |                        |                           |
        v                        |                           |
Phase 4 (backtest engine)       |                           |
        |                        |                           |
        +──────────┬─────────────+                           |
        |          |                                         |
        v          v                                         |
Phase 6 (audit)   Phase 7 (paper portfolio)                 |
        |          |                                         |
        +────┬─────+                                         |
        |    |                                               |
        v    v                                               |
Phase 8 (frontend polish) <─────────────────────────────────┘
        |
        v
Phase 9 (report/demo)
```

**Parallel opportunities:** Phase 2 and Phase 5 can run concurrently after Phase 1. Phase 6 and Phase 7 can run concurrently after Phases 4+5. Phase 8 can start skeleton work as early as Phase 0.

## Phase-by-phase execution

### Phase 0 — Repository scaffold

**Purpose:** Create repo structure, get Docker Compose backend running with health check, placeholder Tauri frontend.

**Files to create:**
- `backend/pyproject.toml` — Python project with deps: fastapi, uvicorn, pydantic, sqlalchemy, alembic, psycopg[binary], redis, pandas, numpy, akshare; dev deps: pytest, ruff, mypy
- `backend/Dockerfile` — python:3.11-slim, copy pyproject.toml, pip install, copy app/, EXPOSE 8000, CMD uvicorn
- `backend/app/__init__.py`
- `backend/app/main.py` — FastAPI app with `/health` returning `{"status": "ok", "version": "0.1.0"}`
- `backend/app/core/__init__.py`
- `backend/app/core/config.py` — Settings from env vars: DATABASE_URL, REDIS_URL, APP_ENV, SECRET_KEY, DATA_DIR
- `backend/app/db/__init__.py`
- `backend/app/db/base.py` — SQLAlchemy Base, engine, get_db dependency
- `ops/docker-compose.yml` — services: postgres (16, user/pass/db: guardian), redis (7), api-server (build from ../backend, depends_on postgres+redis healthy, port 8000)
- `ops/.env.example` — APP_ENV=dev, DATABASE_URL, REDIS_URL, SECRET_KEY=replace-me, DATA_DIR=./data, TUSHARE_TOKEN=, ENABLE_INTRADAY_MONITORING=false, DEFAULT_RISK_PROFILE=balanced
- `README.md` — short quickstart: `docker compose -f ops/docker-compose.yml up --build` then `curl localhost:8000/health`

**Acceptance:** `docker compose -f ops/docker-compose.yml up --build` starts Postgres, Redis, and API. `curl localhost:8000/health` returns ok. Create Tauri app scaffold (`npm create tauri-app@latest frontend` — React + TypeScript) that calls `/health` and displays result.

---

### Phase 1 — Data ingestion

**Purpose:** A-share ETF daily price data pipeline.

**Dependencies:** Phase 0 complete.

**Files to create:**
- `backend/app/data/__init__.py`
- `backend/app/data/models.py` — SQLAlchemy models:
  - `Instrument`: id, symbol (e.g. "510050"), name, exchange (SH/SZ), type (ETF), category, created_at
  - `DailyBar`: id, instrument_id (FK), trade_date, open, high, low, close, volume, amount, adj_close (if available), data_source, fetched_at
  - `TradingCalendar`: date, is_trading_day
  - `DataQualityReport`: id, instrument_id, check_date, missing_dates (JSON), price_jumps (JSON), zero_volume_dates (JSON), overall_status (OK/WARNING/ERROR)
- `backend/app/data/adapter.py` — `AKShareAdapter` class:
  - `fetch_etf_daily(symbol: str, start_date: str, end_date: str) -> list[dict]` — wraps akshare.fund_etf_hist_em()
  - `normalize_symbol(symbol: str) -> str` — ensures 6-digit format
  - `fetch_trading_calendar() -> list[str]`
- `backend/app/data/quality.py` — `DataQualityChecker`:
  - `check_missing_dates(bars, calendar) -> list[str]`
  - `check_price_jumps(bars, threshold_pct=0.15) -> list[dict]`
  - `check_zero_volume(bars) -> list[str]`
- `backend/app/data/sync.py` — `DataSyncService`:
  - `sync_instrument(symbol) -> Instrument`
  - `sync_daily_bars(instrument_id, start, end) -> int` (returns count)
  - `run_quality_check(instrument_id) -> DataQualityReport`
- `backend/app/api/data.py` — FastAPI router:
  - `POST /data/sync` — trigger sync for a list of symbols
  - `GET /data/instruments` — list universe
  - `GET /data/bars/{symbol}` — get bars with date range filter
  - `GET /data/quality/{symbol}` — latest quality report
- `backend/app/db/migrations/` — Alembic init + initial migration for data models
- `backend/tests/test_data_models.py`
- `backend/tests/test_data_adapter.py`
- `backend/tests/test_data_quality.py`
- `config/universe/default.json` — initial ETF list (at least 5 symbols: 510050, 510300, 510500, 159919, 159915)

**Acceptance:** Can sync at least 5 ETF symbols. Cleaned bars stored in Postgres. Data quality report generated and retrievable via API.

---

### Phase 2 — Feature registry

**Purpose:** Compute features from price data for ETF scoring, with strict no-lookahead guarantees.

**Dependencies:** Phase 1 complete.

**Files to create:**
- `backend/app/features/__init__.py`
- `backend/app/features/registry.py` — `FeatureRegistry`:
  - `register(feature: FeatureDefinition)`
  - `compute_all(instrument_id, as_of_date) -> dict[str, float]`
  - Config hash for reproducibility
- `backend/app/features/models.py`:
  - `FeatureDefinition`: name, category (trend/momentum/volatility/drawdown/liquidity), lookback_days, parameters (JSON)
  - `FeatureValue`: instrument_id, feature_name, date, value
  - `FeatureRun`: id, config_hash, created_at
- `backend/app/features/trend.py` — MA crossover scores, MA slope, price vs MA distance
- `backend/app/features/momentum.py` — N-day return, excess return vs benchmark, Sharpe-like ratio
- `backend/app/features/volatility.py` — rolling std, ATR-normalized, volatility regime indicator
- `backend/app/features/drawdown.py` — current drawdown from N-day peak, drawdown duration, recovery ratio
- `backend/app/features/liquidity.py` — avg daily volume (ADV), volume trend, turnover ratio
- `backend/tests/test_features_no_lookahead.py` — CRITICAL: verify that feature values for date D only use data ≤ D

**Acceptance:** Features generated for ETFs by date. Feature values reproduce from config hash. Tests confirm no lookahead (feature at date D uses only data from ≤ D).

---

### Phase 3 — Strategy engine

**Purpose:** Weekly ETF scoring, risk-constrained portfolio construction, explanation logs.

**Dependencies:** Phase 2 complete.

**Files to create:**
- `backend/app/strategy/__init__.py`
- `backend/app/strategy/models.py`:
  - `StrategyConfig`: name, version, parameters (JSON), universe_filter, risk_profile
  - `StrategyRun`: id, config_id, run_date, status
  - `Signal`: id, run_id, instrument_id, score, rank, reason
  - `TargetPortfolio`: run_id, instrument_id, target_weight, score, constraint_info (JSON)
  - `RebalanceDecision`: run_id, from_portfolio (JSON), to_portfolio (JSON), trades (JSON)
  - `ExplanationLog`: run_id, instrument_id, action (BUY/SELL/HOLD), reason (natural language), score_breakdown (JSON)
- `backend/app/strategy/rotation.py` — `RiskAwareETFRotationV1`:
  - `score_etf(instrument_id, as_of_date) -> float` — composite score from features
  - `build_portfolio(scores, constraints) -> TargetPortfolio[]` — top-N selection with constraints
  - `generate_signals(universe, as_of_date) -> Signal[]`
- `backend/app/strategy/constraints.py`:
  - `apply_concentration_limit(portfolio, max_weight=0.3)`
  - `apply_turnover_limit(portfolio, prev_portfolio, max_turnover=0.5)`
  - `apply_min_positions(portfolio, min_count=3)`
  - `apply_max_drawdown_check(portfolio, instrument_drawdowns, max_dd=-0.15)`
- `backend/app/strategy/explainer.py` — generates natural-language reasons from score breakdown
- `backend/config/strategies/risk_aware_v1.json` — default strategy config
- `backend/config/risk_profiles/` — conservative.json, balanced.json, aggressive.json (each with max_drawdown, max_concentration, max_turnover, volatility_tolerance params)
- `backend/app/api/strategy.py` — FastAPI router:
  - `POST /strategy/run` — trigger weekly scoring
  - `GET /strategy/signals` — latest signals
  - `GET /strategy/portfolio` — current target portfolio
  - `GET /strategy/explanations/{run_id}` — explanation logs
- `backend/tests/test_strategy_scoring.py`
- `backend/tests/test_strategy_constraints.py`

**Acceptance:** Given a date and universe, strategy returns ETF scores and target weights. Target weights obey concentration (<30%), turnover (<50%), and min-count (≥3) constraints. Each target has a natural-language explanation.

---

### Phase 4 — Backtest engine

**Purpose:** Simulate portfolio over historical data with costs, slippage, and benchmark comparison.

**Dependencies:** Phase 3 complete.

**Files to create:**
- `backend/app/backtest/__init__.py`
- `backend/app/backtest/models.py`:
  - `BacktestConfig`: strategy_config_id, start_date, end_date, initial_capital, cost_model (JSON), benchmark_symbol
  - `BacktestRun`: id, config_id, status, started_at, completed_at, config_hash
  - `PortfolioSnapshot`: run_id, date, total_value, cash, positions (JSON), daily_return
  - `SimulatedOrder`: run_id, date, instrument_id, side (BUY/SELL), quantity, price, cost
  - `SimulatedTrade`: run_id, order_id, executed_price, slippage, commission, net_amount
  - `PerformanceMetric`: run_id, metric_name (total_return, annual_return, sharpe, max_drawdown, win_rate, etc.), value
- `backend/app/backtest/engine.py` — `BacktestEngine`:
  - `run(config) -> BacktestRun` — main loop: for each week, compute features, score, build portfolio, simulate trades
  - `_apply_costs(trade) -> float` — commission (0.03%) + slippage (0.1%)
  - `_rebalance(portfolio, targets, date) -> list[SimulatedOrder]`
- `backend/app/backtest/metrics.py`:
  - `compute_returns(equity_curve) -> pd.Series`
  - `compute_sharpe(returns, risk_free=0.02) -> float`
  - `compute_max_drawdown(equity) -> float`
  - `compute_win_rate(trades) -> float`
  - `compute_turnover(trades) -> float`
  - `compare_to_benchmark(strategy_returns, benchmark_returns) -> dict`
- `backend/app/api/backtest.py` — FastAPI router:
  - `POST /backtest/run` — submit backtest job
  - `GET /backtest/status/{run_id}`
  - `GET /backtest/results/{run_id}` — equity curve, metrics, trades
  - `GET /backtest/compare/{run_id}` — benchmark comparison
- `backend/tests/test_backtest_engine.py`
- `backend/tests/test_backtest_costs.py`

**Acceptance:** Backtest runs end-to-end with at least 1 year of data. Results include equity curve, drawdown, trade log, and Sharpe/max_dd/return metrics. Cost assumptions (commission + slippage) measurably affect results.

---

### Phase 5 — Do-Not-Trade risk overlay

**Purpose:** Daily risk checks that can override the weekly strategy signal.

**Dependencies:** Phase 1 complete (needs price data, doesn't need strategy).

**Files to create:**
- `backend/app/risk/__init__.py`
- `backend/app/risk/models.py`:
  - `RiskProfile`: name, max_drawdown, max_volatility, max_concentration, liquidity_threshold
  - `RiskState`: date, state (NORMAL/CAUTION/DEFENSIVE/HALT), transition_reason
  - `RiskRuleResult`: date, rule_name, triggered (bool), severity (INFO/WARNING/CRITICAL), detail
  - `RiskOverlayDecision`: date, original_targets (JSON), final_targets (JSON), suppressed_trades (JSON), reason
- `backend/app/risk/state_machine.py` — `RiskStateMachine`:
  - States: NORMAL → CAUTION → DEFENSIVE → HALT (and back)
  - `evaluate(daily_data) -> RiskState`
  - `transition(current, triggers) -> RiskState`
- `backend/app/risk/rules.py`:
  - `TrendBreakRule` — market index below N-day MA
  - `VolatilitySpikeRule` — VIX-like or realized vol > threshold
  - `DrawdownRule` — portfolio drawdown exceeds risk profile limit
  - `LiquidityDegradationRule` — volume < X% of ADV
  - `CostCoverageRule` — estimated costs > expected return
- `backend/app/risk/overlay.py` — `RiskOverlay`:
  - `apply(state, rule_results, target_portfolio) -> RiskOverlayDecision`
  - Actions: ALLOW (no change), REDUCE (scale down weights), BLOCK (no trades), MANUAL_CONFIRM (flag for user)
- `backend/app/api/risk.py` — FastAPI router:
  - `GET /risk/state` — current risk state
  - `GET /risk/rules` — triggered rules today
  - `POST /risk/evaluate` — run daily check
  - `GET /risk/overlay` — latest overlay decision
- `backend/tests/test_risk_rules.py`
- `backend/tests/test_risk_state_machine.py`
- `backend/tests/test_risk_overlay.py`

**Acceptance:** Overlay can block or reduce trades. Original target and final target are both stored. Each triggered rule has a clear reason. Different risk profiles produce different overlay behavior.

---

### Phase 6 — Audit gatekeeper

**Purpose:** Validate strategy robustness before allowing paper trading.

**Dependencies:** Phase 4 complete (needs backtest), Phase 5 complete (risk overlay integrated).

**Files to create:**
- `backend/app/audit/__init__.py`
- `backend/app/audit/models.py`:
  - `AuditRun`: id, strategy_config_id, backtest_config_id, run_date, grade (GREEN/YELLOW/RED), summary
  - `AuditCheckResult`: audit_run_id, check_name, status (PASS/WARN/FAIL), score, detail (JSON)
- `backend/app/audit/leakage.py` — `LeakageCheck`:
  - Verify no future data in features, signals, or portfolio construction
- `backend/app/audit/walk_forward.py` — `WalkForwardRunner`:
  - Split data into train/test windows, run strategy on test, measure out-of-sample decay
- `backend/app/audit/param_stability.py` — `ParameterStabilityRunner`:
  - Perturb key parameters ±X%, measure result sensitivity
- `backend/app/audit/cost_stress.py` — `CostStressRunner`:
  - Run backtest with 1x, 2x, 5x cost assumptions
- `backend/app/audit/regime_slicing.py` — `RegimeSlicer`:
  - Split backtest period into bull/bear/sideways regimes, check performance consistency
- `backend/app/audit/grading.py` — `AuditGrader`:
  - Weighted scoring of all checks, output GREEN (≥80), YELLOW (60–79), RED (<60)
  - `audit(strategy_config, backtest_config) -> AuditRun`
- `backend/app/api/audit.py` — FastAPI router:
  - `POST /audit/run` — run full audit
  - `GET /audit/status/{run_id}`
  - `GET /audit/report/{run_id}` — full structured report
- `backend/tests/test_audit_grading.py`
- `backend/tests/test_audit_leakage.py`

**Acceptance:** Audit produces structured report with GREEN/YELLOW/RED grade. Strategy cannot enter paper trading without GREEN by default (configurable override for development with stern warning).

---

### Phase 7 — Paper/simulated portfolio

**Purpose:** Simulated trading ledger for tracking hypothetical positions.

**Dependencies:** Phase 4 complete (needs backtest), Phase 5 complete (needs overlay).

**Files to create:**
- `backend/app/paper/__init__.py`
- `backend/app/paper/models.py`:
  - `PaperPortfolio`: id, name, initial_capital, created_at
  - `PaperPosition`: portfolio_id, instrument_id, quantity, avg_cost, current_value
  - `PaperOrder`: portfolio_id, date, instrument_id, side, quantity, price, status (PENDING/FILLED/CANCELLED)
  - `PaperLedger`: portfolio_id, date, entry_type (DEPOSIT/WITHDRAWAL/TRADE/DIVIDEND), amount, description
- `backend/app/paper/engine.py` — `PaperTradingEngine`:
  - `create_portfolio(name, capital) -> PaperPortfolio`
  - `apply_signal(portfolio_id, signal_date) -> list[PaperOrder]`
  - `mark_to_market(portfolio_id, date) -> PaperPortfolio` (update positions with latest prices)
  - `get_pnl(portfolio_id) -> float`
- `backend/app/api/paper.py` — FastAPI router:
  - `POST /paper/portfolio` — create portfolio
  - `POST /paper/apply-signal` — apply approved signal
  - `GET /paper/holdings/{portfolio_id}` — current holdings
  - `GET /paper/pnl/{portfolio_id}` — P&L summary
  - `GET /paper/ledger/{portfolio_id}` — transaction history
- `backend/tests/test_paper_engine.py`

**Acceptance:** User can create a simulated portfolio and apply approved signals. Orders and positions update. P&L is calculated.

---

### Phase 8 — Frontend polish

**Purpose:** Complete Tauri GUI connecting to backend via HTTP/WebSocket.

**Dependencies:** All backend phases complete. Can start skeleton/placeholder work as early as Phase 0.

**Pages to implement:**
- **Dashboard** (`frontend/src/pages/Dashboard.tsx`): Portfolio summary card, risk state badge, latest signals summary, recent alerts.
- **Universe** (`frontend/src/pages/Universe.tsx`): ETF list table, data freshness indicators, quality report badges.
- **Signals** (`frontend/src/pages/Signals.tsx`): Weekly signal table with scores, target weights, and explanations. Rebalance visualization.
- **Risk Overlay** (`frontend/src/pages/Risk.tsx`): Current risk state indicator (NORMAL/CAUTION/DEFENSIVE/HALT with color), triggered rules list, overlay decision table (original vs final weights).
- **Backtest** (`frontend/src/pages/Backtest.tsx`): Backtest run form, equity curve chart (ECharts/Recharts), metrics dashboard, trade log table, benchmark comparison chart.
- **Audit** (`frontend/src/pages/Audit.tsx`): Audit report with GREEN/YELLOW/RED badge, check-by-check results, parameter stability heatmap.
- **Paper Portfolio** (`frontend/src/pages/Paper.tsx`): Holdings table, P&L chart, order history, apply-signal button (disabled if audit not GREEN).
- **Settings** (`frontend/src/pages/Settings.tsx`): Risk profile selector, data source config, API URL config.

**Key frontend infrastructure:**
- `frontend/src/api/client.ts` — Axios or fetch wrapper, base URL from env, error handling
- `frontend/src/api/hooks.ts` — TanStack Query hooks for all backend endpoints
- `frontend/src/components/Layout.tsx` — sidebar navigation, risk state header
- `frontend/src/components/RiskBadge.tsx` — colored badge component
- `frontend/src/App.tsx` — React Router with all page routes
- VITE_API_BASE_URL=http://localhost:8000 in `.env`

**Acceptance:** Full demo can be conducted through GUI. Audit failures are visually clear (RED badge). Trade explanations are visible in Signals page.

---

### Phase 9 — Report/demo outputs

**Purpose:** Generate figures, tables, scripts for final report and demo.

**Dependencies:** All phases complete.

**Files to create:**
- `backend/app/reports/figures.py` — matplotlib/plotly figure generation:
  - Equity curve + benchmark comparison chart
  - Drawdown chart
  - Risk state timeline
  - Feature importance / score breakdown charts
  - Audit heatmap
- `backend/app/reports/tables.py` — Export performance metrics, audit results, trade summary as CSV/Markdown
- `docs/demo_script.md` — Step-by-step walkthrough: start Compose, sync data, run backtest, run audit, apply signal, show GUI
- `docs/reproducibility.md` — Exact commands to reproduce every number and figure

**Acceptance:** Final report can cite generated outputs. Demo script is runnable from clean checkout. All figures are reproducible.

---

## Critical constraints — never violate

1. **No lookahead.** Feature at date D must use only data from ≤ D. This is the #1 source of cheating in financial ML. Test it.
2. **No real-money trading.** Backtest, signal-only, and simulated paper trading only.
3. **No HFT logic.** Low-frequency weekly/daily only.
4. **Costs always included.** Every simulated trade pays commission (≥0.03%) + slippage (≥0.1%).
5. **Audit before paper trading.** The gatekeeper must be GREEN before any paper portfolio can accept signals.
6. **Explainability.** Every trade decision must have a natural-language reason attached.
7. **Backend Compose first.** `docker compose -f ops/docker-compose.yml up --build` must work before any GUI work is considered done.
8. **Reproducibility.** Every backtest stores: strategy config JSON, config hash, universe list, data version, cost assumptions, timestamp.

## Getting started — your first actions

1. Read this entire prompt.
2. Create the repository structure exactly as specified in Phase 0.
3. Get `docker compose -f ops/docker-compose.yml up --build` working — verify `curl localhost:8000/health`.
4. Scaffold the Tauri frontend with a health check call.
5. Move to Phase 1 — AKShare data ingestion.

## Testing requirements

Every backend domain module must have tests. Minimum:
- Data normalization test
- Feature no-lookahead test (CRITICAL)
- Strategy scoring test
- Portfolio constraint test
- Backtest cost application test
- Audit grading test
- API health test
- Compose smoke test (`docker compose up`, curl health, `docker compose down -v`)

## Reference

All detailed specs are available alongside this prompt in the `Agent/` directory:
- Agent/docs/ — architecture, API contracts, DB schema, GUI spec, strategy spec, data spec, etc.
- Agent/adr/ — architectural decision records
- Agent/scaffolding/ — starter templates for backend, frontend, ops
- Agent/checklists/ — MVP acceptance checklist

Consult these when you need more detail than this prompt provides, but follow this prompt as the authoritative execution order.
