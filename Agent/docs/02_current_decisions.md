# 02 — Current Decision Record

This file freezes the decisions made before implementation.

## Product decision

Build a fused A+B+C practical project:

- A: Risk-aware ETF rotation.
- B: Backtest audit gatekeeper.
- C: Do-not-trade risk overlay.

The project is named **Retail ETF Guardian**.

## Market decision

Start with **A-share exchange-traded ETFs**.

Long-term expansion:

- US ETFs.
- Hong Kong ETFs.
- Multi-asset global ETF universe.

## User decision

Target user:

- Account size: approximately USD 5,000–100,000 equivalent.
- Cannot watch the market all day.
- Prefers low-frequency systematic decisions.
- Cares about maximum drawdown, volatility, and trading frequency.
- Wants interpretable reasons for buy/sell/do-not-trade decisions.

## Objective decision

The system objective is not maximum raw return. The objective is:

**Improve risk-adjusted return while controlling maximum drawdown and trading frequency.**

## Trading frequency decision

- Primary portfolio rebalance: **weekly**.
- Risk monitoring: **daily**, with optional intraday ETF real-time observation.
- Intraday data is used for warnings, risk suppression, and manual-confirmation prompts, not for high-frequency alpha in MVP.

## Deployment decision

Recommended deployment, now frozen as **backend Docker Compose first**:

- Backend: FastAPI service with worker processes.
- Data store: PostgreSQL.
- Queue/cache: Redis.
- Backend deployment: **Docker Compose is the primary and required MVP deployment path**.
- Compose-managed backend services: `api-server`, `postgres`, `redis`, and later `data-worker`, `strategy-worker`, `backtest-worker`, `audit-worker`, and `scheduler`.
- Frontend: Tauri desktop app using React/TypeScript.
- Frontend deployment boundary: the Tauri/Electron GUI runs outside Docker in MVP and connects to the Compose-managed backend through HTTP/WebSocket.
- Electron is fallback only if implementation friction with Tauri becomes material.
- Kubernetes, cloud-native orchestration, or one-click packaged backend installers are long-term options, not MVP requirements.

## Backtesting decision

Use a **self-built lightweight backtest engine** for the canonical system because the strategy is narrow: ETF portfolio allocation + weekly rebalance + daily risk overlay + costs + audit logs.

Optional adapters:

- vectorbt for parameter grid, fast robustness tests, and comparison.
- Existing backtesting frameworks may be studied, but should not dominate the project identity.

## Data decision

Recommended data sources:

- AKShare as primary source for A-share ETF historical data and broad China market data.
- Tushare as optional enhanced/backup source if access token and points allow.
- efinance as optional real-time/backup source with caution because it is a personal open-source library and should be treated as best-effort.

## MVP real-money decision

No real-money auto-trading in MVP. Support:

- Backtesting.
- Signal-only mode.
- Simulated/paper trading ledger.
- Manual trade review.

## GUI decision

Use a cross-platform desktop GUI:

- Preferred: Tauri + React + TypeScript.
- Electron fallback if Tauri becomes a schedule risk.
- Charts: ECharts or Recharts.
- State/query: TanStack Query.
- Styling: Tailwind or a minimal component library.

## Documentation decision

Document everything needed for Claude Code / Codex implementation:

- Product scope.
- Architecture.
- Strategy.
- Data.
- Audit.
- Do-not-trade layer.
- API contracts.
- Database schema.
- Frontend screens.
- DevOps.
- Implementation task plan.
- Report and presentation outline.
