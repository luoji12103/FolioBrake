# 00 — Master Project Brief

## Project name

**Retail ETF Guardian**

## Track

FTEC 4320 Final Project — Track B: Practical Track / AI Trading System Development.

## One-line description

A risk-aware ETF trading decision system for individual investors, starting with A-share exchange-traded ETFs, combining weekly ETF rotation, backtest audit, and daily do-not-trade risk overlay.

## Core problem

Individual investors can access many indicators, backtesting notebooks, and open-source trading engines, but they usually lack a practical system that answers three operational questions:

1. What ETF portfolio should I hold now under my risk constraints?
2. Is the backtest robust enough to trust?
3. When should the system explicitly avoid trading?

## Product thesis

The project should not compete with mature general-purpose trading frameworks. It should build the retail-investor product layer above reusable infrastructure:

- Low-frequency ETF allocation.
- Risk-constrained portfolio construction.
- Backtest audit gatekeeper.
- Do-not-trade risk overlay.
- Explainable signal and trade logs.
- Backend-first Docker Compose deployment.
- Cross-platform desktop GUI as a client.

## Target users

Individual investors with approximately USD 5,000–100,000 equivalent account size who:

- Cannot watch the market all day.
- Prefer systematic low-frequency decisions.
- Care about maximum drawdown, volatility, and turnover.
- Need clear reasons for buy/sell/do-not-trade decisions.

## Initial market

A-share exchange-traded ETFs.

Long-term expansion:

- US ETFs.
- Hong Kong ETFs.
- Multi-asset global ETF universe.

## MVP outcome

A working engineering prototype with a technical report and demo video/live walkthrough. The backend prototype should be runnable locally through Docker Compose. The cross-platform Tauri desktop GUI should connect to that backend through HTTP/WebSocket. The GUI itself does not need to run inside Docker for MVP.

## Long-term outcome

A maintainable open-source project with modular backend, desktop client, data adapters, strategy modules, audit modules, and deployment scripts.

## Non-goals for MVP

- No real-money automatic trading.
- No high-frequency trading.
- No claim of guaranteed returns.
- No generic all-market quant platform.
- No complex reinforcement learning as the core strategy.
- No Kubernetes requirement.
- No GUI containerization requirement.

## Deployment interpretation

“Docker Compose deployment” means **backend-first Compose deployment**. The backend must be reproducible as a multi-container stack. The GUI remains a cross-platform desktop client. This avoids mixing desktop packaging concerns with backend service orchestration.
