# Claude Code Start Prompt

You are implementing the Retail ETF Guardian project from the provided handoff pack. Do not redesign the product. Read these files first:

1. README.md
2. docs/00_master_project_brief.md
3. docs/02_current_decisions.md
4. docs/04_architecture.md
5. docs/12_devops_and_deployment.md
6. docs/13_claudecode_codex_task_plan.md

Implement Phase 0 and Phase 1 first. Keep work incremental. Use typed Python, FastAPI, PostgreSQL, Redis, backend-first Docker Compose, and Tauri/React/TypeScript. Add tests for every backend domain module. Do not implement real-money trading. Do not introduce high-frequency trading logic. Preserve auditability: every backtest and signal must be reproducible from config and data version.

Deployment clarification: Docker Compose is for the backend stack first. Do not containerize the Tauri GUI for MVP; make it connect to the Compose backend.

First deliverable:

- Repository scaffold.
- Backend `/health` endpoint.
- Docker Compose backend stack with Postgres/Redis/API as the required primary deployment path.
- Placeholder Tauri frontend calling `/health`.
- Initial instrument and daily bar models.
- AKShare adapter interface stub and tests.
