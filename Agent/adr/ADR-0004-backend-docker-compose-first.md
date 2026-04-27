# ADR-0004 — Backend Docker Compose First

## Status

Accepted.

## Context

The project needs a reproducible handoff path for Claude Code / Codex and a credible engineering demo for the course. The frontend is a cross-platform desktop GUI, while the backend contains multiple services: API server, data ingestion, workers, scheduler, PostgreSQL, and Redis.

## Decision

Use Docker Compose as the **primary deployment path for the backend server stack**.

The GUI remains outside Docker in MVP. It connects to the backend through HTTP/WebSocket.

## Consequences

Positive:

- Clean checkout can start backend infrastructure consistently.
- PostgreSQL and Redis do not need host installation.
- Demo and testing environments are reproducible.
- Future worker services can be added without changing the product boundary.

Negative:

- Developers need Docker installed.
- Desktop GUI and backend use separate startup commands in MVP.

## Non-goals

- Do not use Kubernetes in MVP.
- Do not containerize the desktop GUI in MVP.
- Do not require real-money broker deployment in MVP.
