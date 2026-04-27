# 03 — MVP Scope and Roadmap

## Course MVP

Must complete:

1. A-share ETF daily data ingestion.
2. ETF universe management.
3. Weekly ETF rotation strategy.
4. Daily do-not-trade overlay.
5. Transaction cost and slippage assumptions.
6. Lightweight backtest engine.
7. Performance metrics.
8. Backtest audit gatekeeper.
9. Simulated/paper trading ledger.
10. FastAPI backend.
11. Docker Compose as the primary backend deployment path.
12. Tauri GUI with core screens connecting to the Compose backend.
13. Technical report.
14. Demo video or live walkthrough.

## Backend deployment priority

The MVP is considered deployable only when the backend can be started from a clean checkout with Docker Compose. Local Python-only execution is useful for development, but it is not the primary handoff path. The backend Compose stack must be sufficient for demo, testing, and report reproducibility.

The desktop GUI is built and run separately as a client. It should not block backend deployment validation.

## Stretch goals before submission

- Intraday ETF snapshot monitoring for warnings only.
- ETF category/sector/factor exposure labels.
- Parameter stability heatmap.
- Cost sensitivity report.
- Strategy explanation log viewer.
- User risk profile editor.

## Long-term open-source goals

- US ETF support.
- Hong Kong ETF support.
- IBKR or Alpaca paper trading adapter for non-A-share markets.
- More data adapters.
- Strategy plugin system.
- Broker abstraction layer.
- Web dashboard mode.
- Community-contributed strategies.
- Cloud deployment templates.
- Optional Kubernetes deployment for advanced users.

## Explicitly deferred

- Real-money A-share auto-trading.
- High-frequency strategy logic.
- Complex reinforcement learning.
- Full-fledged tax optimization.
- Enterprise multi-user SaaS.
