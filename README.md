# Piper — Responsible Learning Analytics Pipeline

A **security-first data engineering pipeline** that ingests raw, messy multi-source learning &
wellness data, **cleans → filters → normalizes → secures** it, and lands it in a hardened
database for cross-source analytics — with security, privacy-by-design, and fairness built in
from the first stage.

Built for **PR10 — Introduction to Data Engineering** (Zuyd, Applied Data Science & AI), as part
of a four-person group project. This repository implements the **Security** pillar as the
backbone, compatible with the team's GDPR/legal, Privacy-by-Design, and Bias/fairness pillars.

## Status
Design phase complete. See [`docs/`](docs/) for the full scope, architecture, security design,
compliance mapping, and decision records. No application code yet — building starts at roadmap
Phase 1 after team sign-off.

> Note: `docs/`, `claude/`, `assignments/`, and `datasets/` are intentionally gitignored.
> The documentation set lives in `docs/` (kept local per project preference).

## Stack (see `docs/02-tech-stack.md`)
- **Python 3.12** · pandas / polars · pydantic
- **PostgreSQL 16 + TimescaleDB** (one hardened engine: relational + time-series + JSONB)
- **FastAPI** webhook ingest (also the future API seam)
- **Docker Compose** (local, reproducible)
- Encryption: TLS 1.3 · AES-256-GCM · `pgcrypto` · Argon2id · RSA/ECC for signing

## The 8 pipeline stages
`01 Ingest · 02 Transport · 03 Store · 04 Process · 05 Analyse · 06 Access · 07 Monitor · 08 Delete`
— each with explicit Security / Privacy / Fairness controls (see `docs/01-architecture.md`,
`docs/04-security.md`).

## Quick start (once Phase 1 lands)
```bash
cp .env.example .env      # fill in secrets (never committed)
docker compose up         # brings up DB + pipeline + webhook API
```

## Documentation map
| Doc | What |
|---|---|
| `docs/00-scope.md` | Scope, objectives, locked decisions |
| `docs/01-architecture.md` | System architecture, 8 stages, repo structure |
| `docs/02-tech-stack.md` | Technology choices + justification |
| `docs/03-data-sources.md` | The 4 datasets + real-time wearable feed |
| `docs/04-security.md` | Security design mapped to the Week 5 lecture |
| `docs/05-compliance.md` | GDPR / ISO 27001 / EU Data Act / DELICATE mapping |
| `docs/06-data-model.md` | Database / data model design |
| `docs/07-roadmap.md` | Phased build plan |
| `docs/adr/` | Architecture Decision Records |
