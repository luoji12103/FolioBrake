# Handoff Pack Changelog

## v2 — Backend Docker Compose Priority Clarification

Clarified that Docker Compose is the **primary backend deployment path**, not merely an optional full-stack packaging choice.

Deployment boundary:

- Backend server stack is deployed through Docker Compose first.
- Backend stack includes FastAPI API server, PostgreSQL, Redis, background workers, scheduler, migrations, and backend smoke tests.
- Cross-platform GUI is a Tauri-first, Electron-fallback desktop client that runs outside Docker in MVP and connects to the Compose-managed backend through HTTP/WebSocket.
- Containerizing the GUI is not required for the course MVP.
- Alternative backend deployment targets such as Kubernetes, one-click backend installers, or managed cloud services are long-term options only.

Updated files:

- README.md
- docs/00_master_project_brief.md
- docs/02_current_decisions.md
- docs/03_mvp_scope_and_roadmap.md
- docs/04_architecture.md
- docs/12_devops_and_deployment.md
- docs/13_claudecode_codex_task_plan.md
- docs/15_references.md
- adr/ADR-0004-backend-docker-compose-first.md
- prompts/claudecode_start_prompt.md
- prompts/codex_start_prompt.md
- scaffolding/ops/docker-compose.yml
