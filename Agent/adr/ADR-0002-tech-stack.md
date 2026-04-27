# ADR-0002 — Technology Stack

## Status

Accepted.

## Decision

Backend:

- Python.
- FastAPI.
- PostgreSQL.
- Redis.
- Docker Compose.

Frontend:

- Tauri.
- React.
- TypeScript.

Data:

- AKShare primary.
- Tushare optional.
- efinance optional.

Backtest:

- Self-built canonical engine.
- Optional vectorbt adapter for parameter/robustness research.

## Rationale

Python is appropriate for financial data workflows. FastAPI is suitable for typed API services. Tauri provides cross-platform GUI with smaller desktop footprint than Electron in many cases. Docker Compose supports reproducible multi-container deployment.
