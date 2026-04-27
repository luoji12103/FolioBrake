# Retail ETF Guardian — Handoff Pack

Generated: 2026-04-27  
Version: v2 — backend Docker Compose priority clarified

This handoff pack freezes the current product and engineering decisions for the FTEC 4320 Track B practical final project. It is intended for implementation by Claude Code / Codex with minimal re-discussion.

## Project positioning

**Retail ETF Guardian** is a risk-aware ETF trading decision system for individual investors. The first market is **A-share exchange-traded ETFs**. The system combines:

1. **A — Risk-aware ETF rotation**: weekly portfolio allocation under drawdown, turnover, concentration and volatility constraints.
2. **B — Backtest audit gatekeeper**: walk-forward, parameter stability, cost stress, leakage checks and robustness scoring before a strategy is allowed into paper trading.
3. **C — Do-Not-Trade risk overlay**: daily and optional intraday checks that can suppress trades, reduce risk, or require manual confirmation under abnormal market conditions.

The project is not a generic backtesting framework and not a high-frequency trading bot. It uses existing open-source infrastructure where useful, but its distinct contribution is the retail-investor product layer: explainable low-frequency ETF allocation + strategy audit + do-not-trade risk controls + cross-platform GUI + Docker Compose-first backend deployment.

## Deployment boundary clarification

For MVP and handoff implementation, **Docker Compose is the priority deployment method for the backend server stack**. The backend stack includes FastAPI, PostgreSQL, Redis, workers, scheduler, migrations, and smoke-test commands.

The desktop GUI is a Tauri-first, Electron-fallback client and is not required to be containerized. It should connect to the Compose-managed backend through `http://localhost:8000` and WebSocket endpoints.

Do not treat Docker Compose as an optional afterthought. A clean checkout should be able to start the backend with one Compose command before the GUI is launched.

## Recommended reading order

1. `docs/00_master_project_brief.md`
2. `docs/01_course_requirements_and_grading.md`
3. `docs/02_current_decisions.md`
4. `docs/03_mvp_scope_and_roadmap.md`
5. `docs/04_architecture.md`
6. `docs/05_strategy_specification.md`
7. `docs/06_data_specification.md`
8. `docs/07_backtest_audit_gatekeeper.md`
9. `docs/08_do_not_trade_overlay.md`
10. `docs/09_api_contracts.md`
11. `docs/10_database_schema.md`
12. `docs/11_frontend_gui_spec.md`
13. `docs/12_devops_and_deployment.md`
14. `docs/13_claudecode_codex_task_plan.md`
15. `docs/14_report_and_presentation_outline.md`
16. `docs/15_references.md`
17. `CHANGELOG.md`

## Implementation principle

Freeze the direction before coding. Implement in vertical slices:

1. Data ingestion and normalized ETF price table.
2. Feature registry and weekly scoring engine.
3. Minimal backtest engine with costs and no look-ahead.
4. Audit gatekeeper.
5. Do-not-trade overlay.
6. FastAPI backend.
7. Docker Compose backend demo.
8. Tauri GUI connecting to the backend over HTTP/WebSocket.

## Safety and compliance boundary

This is an educational system and should not present itself as investment advice or promise returns. Real-money A-share auto-trading is explicitly out of MVP scope. The first release supports backtesting, signal generation, paper/simulated trading, and manual review.
