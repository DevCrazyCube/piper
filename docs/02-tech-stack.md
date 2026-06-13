# 02 — Technology Stack

> Every choice is justified against (a) the course material, (b) security-first principles,
> and (c) the actual data. Alternatives considered are recorded so choices are defensible.

---

## Summary

| Layer | Choice | One-line reason |
|---|---|---|
| Language | **Python 3.12** | Course is Python/pandas-centric (Week 6); richest data + crypto ecosystem |
| Data processing | **pandas** (+ **polars** for the 20M-row HR data) | pandas taught in class; polars for memory-heavy time-series |
| Validation | **pydantic v2** | Typed, fail-fast ingest records; rejects malformed data early |
| Database | **PostgreSQL 16 + TimescaleDB** | One hardened engine: relational + time-series + JSONB |
| DB access | **SQLAlchemy 2.x** + **psycopg 3** | Parameterised queries (no SQL injection), migrations |
| Migrations | **Alembic** | Versioned, reviewable schema changes |
| Webhook API | **FastAPI** + **uvicorn** | Async, typed, auto-validated; doubles as the future app API seam |
| Crypto | **cryptography** lib + **pgcrypto** + TLS | App-layer field encryption + DB-layer + transport |
| Secrets | **.env (dev)** → docker secrets / vault-style (prod) | Never hard-coded; `.env` gitignored |
| Containers | **Docker + Docker Compose** | Explicitly taught Week 2; reproducible for the team |
| Logging | **structlog** → JSON logs | Structured audit logs (Week 5 "Accounting") |
| Testing | **pytest** | Standard; unit + integration |
| Lint/format | **ruff** + **mypy** | Static checks; ruff also catches some security smells (SAST-lite) |
| Security scan | **bandit** (SAST), **pip-audit** (deps) | Maps to Week 5 SAST / dependency hygiene |

## Why Python
- Week 6 of the course teaches data selection/transformation with **pandas**; the cycling
  example and exercises are Python. Matching the course lowers grading friction.
- Best-in-class libraries for messy-data wrangling, Postgres access, and cryptography.
- The whole ADSAI program is Python-first; teammates can contribute.

## Why PostgreSQL + TimescaleDB (one engine)
- **Security-first ⇒ minimise attack surface.** One database to encrypt, patch, back up,
  and apply RBAC/row-level-security to — instead of 3–4.
- **Handles all our shapes in one place:**
  - Time-series (HR, sleep, steps — ~20M PMData rows) → **TimescaleDB hypertables**
    (automatic partitioning, fast time-range aggregation).
  - Relational/institutional (grades, attendance, students) → standard tables + joins.
  - Free-form (wellness notes, meal logs) → **JSONB** columns.
  - Nutrition lookup (Open Food Facts) → reference table, joined to enrich meals.
- **Native security primitives:** RBAC roles, **Row-Level Security (RLS)** to bind rows to a
  data subject + consent, `pgcrypto` for column-level encryption, SSL/TLS connections.
- **Considered & rejected:** full polyglot (Postgres+TimescaleDB+MongoDB+InfluxDB) as the group
  pptx proposed — more "breadth" but 3–4× the security/ops surface for no real benefit at our
  scale. MongoDB for free-form docs — JSONB covers it. (See `adr/0003`.)

## Why FastAPI for the webhook ingest
- The teammates' auto-export iOS app POSTs health JSON; we need an **authenticated, validated**
  HTTP endpoint. FastAPI gives request validation (pydantic), async I/O for bursty pushes, and
  built-in auth hooks.
- **Strategic:** this same service is the clean seam for the **future dashboard/API**. Building
  it now means the frontend is additive later, not a rewrite.

## Why Docker Compose
- **Taught explicitly in Week 2** ("benefit your project works and team work greatly").
- `docker compose up` brings up Postgres/TimescaleDB + the pipeline + the webhook API (+ optional
  queue) identically on every teammate's machine and for grading. No "works on my machine".

## Encryption methods (preview — full detail in `04-security.md`)
- **In transit:** TLS 1.3 everywhere (webhook, DB connections, internal service calls).
- **At rest:** volume/disk encryption for the DB; **column-level `pgcrypto`** for the most
  sensitive fields (e.g. the pseudonymisation mapping, health identifiers).
- **Symmetric (AES-256-GCM)** for bulk field/data encryption (fast, authenticated).
- **Asymmetric (RSA/ECC)** only where key distribution / signing is needed (e.g. signing the
  webhook payloads or audit log integrity), not for bulk data.
- **Hashing:** Argon2id for any credentials; SHA-256 for integrity checks. Post-quantum noted as
  a forward concern (NIST PQC) per the Week 5 slide, not implemented.

## Optional / "fancier" (only if we want the distributed-systems angle)
- **Kafka or Redis Streams** between ingest and processing — decouples real-time pushes from
  batch, demonstrates Week 4 (volume/velocity, CAP tradeoffs). Default: omit; add deliberately.
