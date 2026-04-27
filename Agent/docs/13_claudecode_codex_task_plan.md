# 13 — Claude Code / Codex Task Plan

## Instructions for coding agents

Do not redesign the product unless a blocker is found. Follow the current decision files. Implement in small vertical slices and keep tests passing.

## Phase 0 — Repository scaffold

Tasks:

1. Create repository structure.
2. Create backend Python project.
3. Create frontend Tauri project.
4. Create Docker Compose setup.
5. Create `.env.example`.
6. Add README quickstart.

Acceptance criteria:

- `docker compose up` starts Postgres, Redis, and placeholder API.
- API `/health` returns ok.
- Frontend can call `/health`.

## Phase 1 — Data ingestion

Tasks:

1. Implement instrument model.
2. Implement daily bar tables.
3. Implement AKShare adapter.
4. Implement data sync endpoint.
5. Implement data quality checks.
6. Add fixture or small demo data for tests.

Acceptance criteria:

- Can sync at least 5 ETF symbols.
- Cleaned bars stored.
- Data quality report generated.

## Phase 2 — Feature registry

Tasks:

1. Implement feature definitions.
2. Implement trend features.
3. Implement momentum features.
4. Implement volatility features.
5. Implement drawdown features.
6. Implement liquidity features.
7. Add no-lookahead tests.

Acceptance criteria:

- Features generated for ETFs by date.
- Feature values reproduce from config hash.
- Tests confirm feature uses only prior data.

## Phase 3 — Strategy engine

Tasks:

1. Implement `risk_aware_etf_rotation_v1`.
2. Implement risk profiles.
3. Implement ETF scoring.
4. Implement constraints.
5. Implement target weights.
6. Implement explanation logs.

Acceptance criteria:

- Given a date and universe, strategy returns ETF scores and target weights.
- Target weights obey concentration and turnover constraints.
- Each target has explanation.

## Phase 4 — Backtest engine

Tasks:

1. Implement portfolio simulator.
2. Implement weekly rebalance schedule.
3. Implement cost and slippage.
4. Implement benchmark comparison.
5. Implement performance metrics.
6. Implement API endpoints and frontend view.

Acceptance criteria:

- Backtest runs end-to-end.
- Results include equity curve, drawdown, trades, metrics.
- Cost assumptions change results.

## Phase 5 — Do-not-trade overlay

Tasks:

1. Implement risk state machine.
2. Implement trend break rule.
3. Implement volatility spike rule.
4. Implement drawdown rule.
5. Implement liquidity degradation rule.
6. Implement cost coverage rule.
7. Integrate overlay into backtest.

Acceptance criteria:

- Overlay can block/reduce trades.
- Original target and final target are both stored.
- GUI displays triggered rules.

## Phase 6 — Audit gatekeeper

Tasks:

1. Implement leakage check.
2. Implement walk-forward runner.
3. Implement parameter stability runner.
4. Implement cost stress runner.
5. Implement regime slicing.
6. Implement audit scoring.
7. Implement GREEN/YELLOW/RED output.

Acceptance criteria:

- Audit run produces structured report.
- Strategy cannot be applied to paper portfolio unless GREEN by default.

## Phase 7 — Paper/simulated portfolio

Tasks:

1. Implement paper portfolio model.
2. Implement simulated order ledger.
3. Implement apply-signal endpoint.
4. Implement holdings/P&L view.

Acceptance criteria:

- User can create simulated portfolio.
- User can apply approved signal.
- Orders and positions update.

## Phase 8 — Frontend polish

Tasks:

1. Dashboard.
2. Universe page.
3. Signals page.
4. Risk overlay page.
5. Backtest page.
6. Audit page.
7. Paper portfolio page.
8. Settings page.

Acceptance criteria:

- Demo can be conducted entirely through GUI.
- Audit failures are clear.
- Trade explanations are visible.

## Phase 9 — Report/demo outputs

Tasks:

1. Generate report figures.
2. Export key tables.
3. Create demo script.
4. Add documentation for reproducibility.

Acceptance criteria:

- Final report can cite generated outputs.
- Demo video script is runnable.

## Suggested agent prompt

Use `prompts/claudecode_start_prompt.md` and `prompts/codex_start_prompt.md`.

## Deployment instruction for agents

Do not implement the GUI as part of Docker Compose for MVP. Prioritize a backend Compose stack that can be started independently with `docker compose -f ops/docker-compose.yml up --build`. The GUI should be a separate Tauri/Electron client that calls the backend API.

Every backend feature should be designed so it can run inside the Compose stack, even if local Python execution is also supported for debugging.
