# Codex Start Prompt

Implement the Retail ETF Guardian project according to this handoff pack. Treat the product direction as frozen:

- A-share ETF first.
- Weekly ETF rotation.
- Daily do-not-trade risk overlay.
- Backtest audit gatekeeper.
- Cross-platform Tauri GUI, with Electron fallback only if necessary.
- FastAPI backend.
- Docker Compose as the primary backend deployment path.
- No real-money auto-trading in MVP.

Prioritize correctness and reproducibility over feature breadth. Create small PR-sized changes. Include tests and docstrings. Use configuration files for ETF universe, strategy parameters, risk profiles, and data sources.

Deployment clarification: implement the backend so it can be started with Docker Compose from a clean checkout. The Tauri/Electron GUI should run separately and call the backend.

Start with:

1. Backend app skeleton.
2. Docker Compose backend stack for API/PostgreSQL/Redis.
3. Database models and migrations.
4. Data ingestion interfaces.
5. Minimal ETF data sync workflow.
6. API health and data sync endpoints.
