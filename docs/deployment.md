# Deployment Guide

## Docker Compose
```bash
cd ops
docker compose up -d
```

## Services
- PostgreSQL: port 5433
- Redis: port 6380
- API Server: port 8000
- Frontend: port 1420
- Prometheus: port 9090

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `APP_ENV` - Environment (dev/prod)
