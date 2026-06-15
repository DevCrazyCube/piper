# Piper — Responsible Learning Analytics Pipeline

A **security-first data engineering pipeline** that ingests raw, messy multi-source learning &
wellness data, **cleans → normalizes → pseudonymises → secures** it, and lands it in a hardened
PostgreSQL/TimescaleDB database for cross-source analytics — with security, privacy-by-design, and
fairness built in from the first stage.

Built for **PR10 — Introduction to Data Engineering** (Zuyd, Applied Data Science & AI), a
four-person group project. This repo implements the **Security** pillar as the backbone.

---

## How it works (the 30-second version)

```
  4 batch datasets ┐                          ┌── curate: clean · normalize · dedup ·
  (Fitbit, grades, │                          │   harmonise · pseudonymise
   nutrition)      ├─▶  RAW ZONE  ──────────▶  ├──────────────────────────────▶  CURATED ZONE
  live wearables   │   (raw.record,           │                                  (per-subject,
   via webhook ────┘    raw.timeseries)       └── identity map (encrypted)        aggregate-ready)
                                                                                       │
                                                          analytics (aggregate-only) ◀─┘
```

- **Two ways data comes in:** four real **batch datasets** (PMData wearables, two UCI student
  datasets, Open Food Facts) and a **near-real-time webhook** for live wearable data.
- **Raw zone** keeps everything exactly as received (provenance + idempotent by content hash).
- **Curate** cleans/normalizes/deduplicates/harmonises it, **pseudonymises** people (real id →
  random `subject_pid`, the real id encrypted at the application layer), and lands an
  analytics-ready **curated zone**.
- **Analytics** only ever expose **aggregates** (k-anonymity floor), never individual rows.
- Everything runs as a **non-superuser DB role** with **row-level security**, audit logging,
  consent enforcement, GDPR-style erasure, and encrypted backups.

The data lives in PostgreSQL + the **TimescaleDB** extension (time-series rollups). Everything runs
in **Docker** — you don't install Python or Postgres yourself.

> Want the full design rationale? It's all in [`docs/`](docs/) — start with
> [`docs/00-scope.md`](docs/00-scope.md) and [`docs/01-architecture.md`](docs/01-architecture.md).

---

## Prerequisites

- **Docker** + **Docker Compose** (that's it — Python, Postgres, all libraries run inside containers).
- The four datasets placed in `datasets/` (gitignored; not shipped). See
  [`docs/03-data-sources.md`](docs/03-data-sources.md) for exactly which files and where to get them.

---

## First-run setup

```bash
# 1. Create your local config from the template
cp .env.example .env

# 2. Fill in the three secrets in .env:
#    - PIPER_DB_PASSWORD     : any strong password
#    - PIPER_APP_PASSWORD    : any strong password (the non-superuser runtime role)
#    - PIPER_MASTER_KEY      : generate with the command below
python -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"
#    paste the output as PIPER_MASTER_KEY=...

# 3. Start the stack + create the schema + create the app role
make setup        # = docker compose up -d  +  migrate  +  bootstrap
```

`make setup` starts three services (`db`, `app`, `api`), applies all DB migrations (schema,
TimescaleDB hypertables, roles, row-level security), and sets the runtime role's password.

---

## Load the data

```bash
make ingest       # land all 4 datasets into the raw zone (PMData is large: ~40 min)
make curate       # build the curated zone (clean, pseudonymise, dedup, harmonise)
```

> 👥 **Teammates / quick testing:** the full PMData ingest is heavy (~40 min, can freeze a laptop).
> Set `PIPER_PMDATA_MAX_PARTICIPANTS=2` in `.env` for a fast, low-memory run — or skip PMData and
> test the academic/food domains. Full walkthrough: **[`docs/TESTING.md`](docs/TESTING.md)**.

Individual sources/domains if you don't want the full run:

```bash
make ingest-uci-perf ingest-uci-academics ingest-food   # the fast ones
make curate D=academic        # or D=health | D=food | D=all
```

Every ingest is **idempotent** — re-running never duplicates (safe to retry).

---

## Use it

```bash
# Analytics (aggregate-only; q1..q5 or all)
make analyse                 # all five queries
make analyse Q=q3            # just one

# Privacy / data-subject rights  (subject ids are the pseudonymous UUIDs)
docker compose exec app python -m pipeline export <subject_pid>          # GDPR Art.15/20 -> JSON
docker compose exec app python -m pipeline consent revoke <pid> sleep    # revoke = deletes that data
docker compose exec app python -m pipeline consent grant  <pid> sleep
make erase PID=<subject_pid>                                             # GDPR Art.17 erasure + receipt

# Operations
make backup                  # encrypted logical backup
make logs                    # tail container logs
make shell                   # shell inside the app container
make down                    # stop everything
```

Find subject ids with: `docker compose exec db psql -U piper -d piper -c "SELECT subject_pid, source FROM id.subject LIMIT 10;"`

### Live wearable data (webhook)

```bash
# Register a device (prints a one-time secret — store it on the device)
docker compose exec app python -m pipeline register-device watch-01 teammate-a
```

The phone's auto-export app then POSTs signed JSON to `http://<host>:8000/v1/ingest` with headers
`X-Piper-Device`, `X-Piper-Timestamp`, `X-Piper-Nonce`, `X-Piper-Signature` (HMAC-SHA256 over
`timestamp.nonce.body`). Tampered, replayed, or stale requests are rejected with `401`. See
[`docs/04-security.md`](docs/04-security.md) §AAA for the exact scheme.

---

## What's in the box

| Service (`docker compose`) | What it is |
|---|---|
| `db` | PostgreSQL 16 + TimescaleDB |
| `app` | the pipeline CLI (`python -m pipeline …`) — ingest, curate, analyse, privacy commands |
| `api` | FastAPI webhook ingest + read endpoints on port `8000` |
| `frontend` | the **Piper dashboard** (React + Vite) on port `5173` — neon-cyber, live pipeline view |

> **Open the dashboard:** after `make up`, browse to **http://localhost:5173**. It shows the live
> pipeline, runs, sources, analytics, security/audit, and consent. It reads the API's `/v1/*`
> endpoints and falls back to seeded demo data if the API isn't up. (Source in `frontend/`.)

**Database schemas:** `raw` (landing) · `curated` (analytics-ready) · `id` (encrypted
pseudonymisation map, app-only) · `consent` · `meta` (provenance, audit log, quarantine, receipts).

**The CLI** (`docker compose exec app python -m pipeline --help`): `ingest`, `curate`, `analyse`,
`consent`, `export`, `erase`, `register-device`, `bootstrap`.

---

## Project layout

```
src/pipeline/
  ingest/    batch connectors (PMData/UCI/OpenFoodFacts) + run engine
  api/       FastAPI webhook ingest
  process/   curate: clean/normalize/dedup/harmonise + pseudonymise/consent/erase/export
  analyse/   the 5 aggregate queries
  common/    config, logging, crypto, db, date+ARFF parsers
db/migrations/   Alembic migrations (schema, hypertables, RLS, roles)
docs/            full design + deliverables (scope, architecture, security policy, compliance, bias)
tests/           pytest unit tests
```

---

## Checks

```bash
make check        # ruff (lint) + mypy (types) + pytest + bandit (SAST)
make audit        # dependency CVE scan (pip-audit)
```

CI runs the same on every push (`.github/workflows/ci.yml`).

---

## Good to know

- **It's a course project**, not a certified production system — it *demonstrates* the controls.
  The honest "implemented vs planned" status is in [`docs/security-policy.md`](docs/security-policy.md)
  and [`docs/audit-findings.md`](docs/audit-findings.md).
- **PMData ingest is slow** (~40 min — it streams ~27M points). The other sources are seconds.
- **TLS** is not enabled in the local stack (terminate it at a gateway for a real deploy).
- **Nothing sensitive is committed**: `datasets/`, `.env`, `pgdata/`, `backups/` are gitignored.
