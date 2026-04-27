# 12 — DevOps and Deployment

## Deployment target

The MVP deployment target is **backend-first Docker Compose** on a local machine or small VPS. Docker Compose is not just a convenience script; it is the primary backend deployment path for the handoff.

The cross-platform desktop GUI is launched separately during MVP development and connects to the Compose-managed backend through HTTP/WebSocket. The GUI may be packaged later, but GUI containerization is not required for the course project.

## Deployment boundary

Inside Docker Compose:

- FastAPI API server.
- PostgreSQL.
- Redis.
- Data worker.
- Strategy worker.
- Backtest worker.
- Audit worker.
- Scheduler.
- Migration/smoke-test commands where useful.

Outside Docker Compose in MVP:

- Tauri desktop GUI development server / packaged desktop app.
- Optional Electron fallback GUI.
- User's browser when using a temporary web UI.

This means the backend can be started and validated independently before the GUI is launched.

## Docker Compose services

Initial Phase 0/1 services:

- `api-server`
- `postgres`
- `redis`

Phase 2+ services:

- `data-worker`
- `strategy-worker`
- `backtest-worker`
- `audit-worker`
- `scheduler`

The first Compose file may start with only API/PostgreSQL/Redis, but the architecture must leave space for workers and scheduler.

## Environment variables

Required:

- `DATABASE_URL`
- `REDIS_URL`
- `APP_ENV`
- `SECRET_KEY`
- `DATA_DIR`

Optional:

- `TUSHARE_TOKEN`
- `AKSHARE_HTTP_URL`
- `ENABLE_INTRADAY_MONITORING`
- `DEFAULT_RISK_PROFILE`

## Primary backend command

Expected backend startup from a clean checkout:

```bash
cd ops
docker compose up --build
```

or from repository root:

```bash
docker compose -f ops/docker-compose.yml up --build
```

Expected validation:

```bash
curl http://localhost:8000/health
```

## GUI command

The GUI is started separately and points to the Compose backend:

```bash
cd frontend
npm install
npm run tauri dev
```

The frontend should use an environment setting such as:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Development fallback commands

Local Python-only development is allowed, but it is secondary:

```bash
# start backend dependencies only
docker compose -f ops/docker-compose.yml up -d postgres redis

# run database migrations
cd backend
alembic upgrade head

# run API server locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## CI suggestions

Use GitHub Actions later:

- Python lint/test.
- Frontend lint/build.
- Docker Compose backend smoke test.
- Documentation link check.

Minimum backend CI command:

```bash
docker compose -f ops/docker-compose.yml up --build -d
curl --fail http://localhost:8000/health
docker compose -f ops/docker-compose.yml down -v
```

## Testing requirements

Minimum backend tests:

- Data normalization test.
- Feature no-lookahead test.
- Strategy scoring test.
- Portfolio constraint test.
- Backtest cost application test.
- Audit grade test.
- API health test.
- Compose smoke test.

Minimum frontend tests:

- Dashboard renders.
- Audit result badge renders.
- Backtest API error state.

## Reproducibility requirements

Each backtest result must store:

- Strategy config JSON.
- Config hash.
- Universe list.
- Data version.
- Cost/slippage assumptions.
- Timestamp.
- Git commit if available.

## Release checklist

- Backend Docker Compose runs from clean checkout.
- API health endpoint passes through Compose.
- PostgreSQL and Redis are not required as host-installed services.
- Demo dataset or fetch script works through Compose.
- README contains backend Compose quickstart.
- `.env.example` is complete.
- No real API token committed.
- GUI connects to `localhost:8000` or configurable API base URL.
- All figures in report are reproducible.
- Audit report exported for final selected strategy.
