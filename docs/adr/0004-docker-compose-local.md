# ADR-0004 — Local Docker Compose runtime

- **Status:** accepted
- **Date:** 2026-06-13
- **Deciders:** Joyren, Claude

## Context
The stack must run reproducibly for every teammate and for grading, without cloud cost or
credential management. Docker is taught explicitly in Week 2.

## Decision
**Docker Compose**, local. `docker compose up` brings up PostgreSQL/TimescaleDB + the pipeline +
the webhook API (+ optional queue). Each service in its own container with healthchecks; the DB
volume is encrypted.

## Consequences
- Positive: "works on my machine" eliminated; matches the course; trivial to demo/grade; zero cost.
- Negative: the **webhook** needs a public URL for real Apple Watch pushes → during demos use a
  tunnel (e.g. ngrok/cloudflared) or ingest on the same LAN; document this. Not a 24/7 service.

## Alternatives considered
- **Cloud (AWS/GCP/Azure)** — more production-realistic but adds cost, secrets, and infra the
  course doesn't require. Revisit only if this becomes a real product.
- **Bare-metal/venv** — not reproducible across the team.
