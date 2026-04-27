# 04 — Architecture

## High-level architecture

```
Tauri/Electron Desktop GUI
        |
        | HTTP/WebSocket
        v
+------------------------------------------------------+
| Docker Compose backend stack                         |
|                                                      |
|  FastAPI API Server                                  |
|          |                                           |
|          +-------------------+                       |
|          |                   |                       |
|          v                   v                       |
|     PostgreSQL           Redis / Queue               |
|          |                   |                       |
|          v                   v                       |
|     Data Worker      Strategy / Backtest / Audit     |
|                      Workers + Scheduler             |
+------------------------------------------------------+
        |
        v
External Data Sources: AKShare / Tushare / efinance
```

## Deployment boundary

Backend deployment is Compose-first. The backend service group should be runnable through `docker compose` and should not require the user to manually install PostgreSQL, Redis, or run multiple backend terminals for the demo.

The desktop GUI is intentionally outside the backend Compose boundary in MVP. It is a cross-platform client that talks to the backend through network APIs. This separation keeps backend deployment reproducible while preserving native desktop packaging for Tauri/Electron.

## Services

### `api-server`

Responsibilities:

- User/profile configuration.
- ETF universe CRUD.
- Backtest job submission and status.
- Strategy signal retrieval.
- Portfolio state retrieval.
- Audit report retrieval.
- Simulated paper-trading ledger.
- Frontend API and WebSocket updates.

Recommended stack:

- Python 3.11+.
- FastAPI.
- Pydantic v2.
- SQLAlchemy 2.x or SQLModel.
- Alembic migrations.

### `data-worker`

Responsibilities:

- Download historical ETF prices.
- Download benchmark/index data.
- Normalize symbol format.
- Adjust prices if available.
- Run data quality checks.
- Store raw and cleaned data.

### `strategy-worker`

Responsibilities:

- Compute features.
- Compute ETF scores.
- Construct weekly target weights.
- Apply constraints.
- Generate explainable signal logs.

### `risk-worker`

Responsibilities:

- Daily do-not-trade checks.
- Intraday warning checks if enabled.
- Risk state transitions: NORMAL, CAUTION, DEFENSIVE, HALT.
- Overlay decisions: allow, reduce, block, manual confirm.

### `backtest-worker`

Responsibilities:

- Run canonical backtests.
- Apply transaction costs and slippage.
- Compute performance metrics.
- Produce trade logs and portfolio histories.

### `audit-worker`

Responsibilities:

- Walk-forward tests.
- Parameter stability tests.
- Cost stress tests.
- Regime slicing.
- Leakage checks.
- Audit grade: GREEN, YELLOW, RED.

### `scheduler`

Responsibilities:

- Daily data update.
- Daily risk check.
- Weekly rebalance calculation.
- Nightly audit/report job if configured.

Can be Celery beat, APScheduler, or a simple internal scheduler for MVP.

## Package layout

```
retail-etf-guardian/
  backend/
    app/
      api/
      core/
      db/
      data/
      features/
      strategy/
      risk/
      backtest/
      audit/
      paper/
      reports/
      workers/
      tests/
    pyproject.toml
  frontend/
    src/
    src-tauri/
    package.json
  ops/
    docker-compose.yml
    docker-compose.dev.yml
    .env.example
  config/
    universe/
    strategies/
    risk_profiles/
  docs/
  scripts/
  README.md
```

## Domain modules

### Data module

Entities:

- DataSource.
- Instrument.
- ETFDailyBar.
- ETFRealtimeSnapshot.
- TradingCalendar.
- DataQualityReport.

### Feature module

Entities:

- FeatureDefinition.
- FeatureValue.
- FeatureRun.

### Strategy module

Entities:

- StrategyConfig.
- StrategyRun.
- Signal.
- TargetPortfolio.
- RebalanceDecision.
- ExplanationLog.

### Risk module

Entities:

- RiskProfile.
- RiskState.
- RiskRuleResult.
- RiskOverlayDecision.

### Backtest module

Entities:

- BacktestConfig.
- BacktestRun.
- PortfolioSnapshot.
- SimulatedOrder.
- SimulatedTrade.
- PerformanceMetric.

### Audit module

Entities:

- AuditRun.
- AuditCheckResult.
- AuditGrade.

## Data flow

1. Universe config defines ETF symbols and categories.
2. Data worker fetches OHLCV and stores raw bars.
3. Data quality checks produce cleaned daily bars.
4. Feature registry computes features using only data available at or before decision time.
5. Strategy worker computes weekly scores and target portfolio.
6. Risk worker overlays daily do-not-trade decisions.
7. Backtest engine simulates orders and portfolio state.
8. Audit worker validates robustness and assigns gatekeeper status.
9. API server exposes results to GUI.
10. GUI displays portfolio, signal explanations, risk states, backtest reports, and audit results.

## Design constraints

- No future data may be used in signal generation.
- All signal timestamps must distinguish `data_as_of`, `decision_time`, and `execution_time`.
- All backtests must include transaction costs.
- The audit gatekeeper must be mandatory before paper trading.
- Every generated trade must have an explanation record.
- Backend services must be runnable through Docker Compose for demo and reproducibility.
