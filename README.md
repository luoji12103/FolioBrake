# Retail ETF Guardian

Risk-aware ETF trading decision system for individual investors targeting A-share ETFs.

## Quickstart

```bash
# Start the backend stack
docker compose -f ops/docker-compose.yml up --build

# Verify health
curl localhost:8000/health
```

## Architecture

- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic
- **Data stores**: PostgreSQL 16, Redis 7
- **Data sources**: AKShare (primary), Tushare/efinance (optional)
- **Frontend**: Tauri + React + TypeScript (desktop client)
- **Deployment**: Docker Compose for backend, desktop GUI connects via HTTP/WebSocket

## Development

See `docs/` for detailed specifications. See `handoff_prompt.md` for the full execution plan.
