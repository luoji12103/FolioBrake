# Development Guide

## Setup
1. Clone repository
2. Run `docker compose up -d`
3. Access http://localhost:1420

## Architecture
- Backend: FastAPI + SQLAlchemy
- Frontend: React + TypeScript + Vite
- Database: PostgreSQL 16
- Cache: Redis 7

## Testing
```bash
python -m pytest tests/
cd frontend && npx tsc --noEmit
```
