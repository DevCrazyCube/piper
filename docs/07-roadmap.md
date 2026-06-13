# 07 — Roadmap

> Phased plan. We are at the end of **Phase 0**. Nothing in Phase 2+ starts until the prior
> phase is real and reviewed. Frontend is deliberately late.

---

## Phase 0 — Scope & design  ✅ (current)
- [x] Read all course + group material
- [x] Lock scope, tech stack, data sources, deployment (this `docs/` set + `adr/`)
- [x] Git repo, `.gitignore`, folder structure
- [x] Resolve review findings (ADR-0008 key custody, 0009 domains/linkage, 0010 run model)
- [x] Pick Q4/Q5 within population constraints (recommended in `03-data-sources.md`)
- [ ] Team sign-off on these docs

## Phase 1 — Foundation & ingest (batch)  🛠️ in progress
- [x] `docker-compose.yml`: PostgreSQL + TimescaleDB, healthcheck, (LUKS-backed) volume
- [x] Config + secrets scaffolding (`.env.example`, structlog logging, AES-256-GCM crypto helpers)
- [x] DB schema + Alembic migration 0001 (raw zone, provenance, quarantine, TimescaleDB hypertable)
- [x] Batch connectors for the 4 datasets (PMData JSON/CSV streamed, nested-zip semicolon CSV, ARFF, parquet)
- [x] Raw zone + content-hash idempotency + provenance + dead-letter/quarantine
- [x] CLI (`python -m pipeline ingest <source>`) + Make targets; unit tests for date + ARFF parsers
- [ ] Run end-to-end on a machine with Docker (ingest all 4, confirm row counts) — needs the stack up
- [ ] Note: identity map / curated tables / RLS are Phase 2-3, not Phase 1

## Phase 2 — Process (clean / filter / normalize)
- [ ] Encoding + delimiter + date-format normalization
- [ ] Cross-file student dedup (Dataset 2) + schema harmonisation (Dataset 2 ⨝ 4)
- [ ] Pseudonymisation + consent model wired to RLS
- [ ] Open Food Facts minimised reference table + meal enrichment joins
- [ ] Data-quality checks (pydantic, missing-value handling) + bias-decision logging

## Phase 3 — Secure & store, properly
- [ ] Encryption at rest + `pgcrypto` on sensitive fields/map
- [ ] RBAC roles + least-privilege grants + RLS policies
- [ ] Audit logging + simple anomaly detection
- [ ] Backups (3-2-1), retention policies, erasure (Art. 17) + deletion receipts
- [ ] SAST (`bandit`), deps (`pip-audit`), DAST-light on the API

## Phase 4 — Real-time ingest
- [ ] FastAPI webhook ingest (authenticated, validated) — the future-API seam
- [ ] Auto-export iOS app → webhook for teammates' Apple Watch data
- [ ] Apple Health `export.zip` fallback importer
- [ ] (Optional) Kafka/Redis Streams queue for the distributed-systems angle

## Phase 5 — Analyse
- [ ] Implement the 5 cross-source queries against curated views
- [ ] Continuous aggregates for the time-series queries
- [ ] Confirm + implement Q4/Q5 with the group

## Phase 6 — Deliverable polish
- [ ] Security policy document (DELICATE-structured, GDPR + ISO 27001 cross-ref)
- [ ] Bias-mitigation decision log writeup
- [ ] **Synthetic test fixtures** (mimic each format's messiness — no real PII/datasets in CI)
- [ ] Tests + CI (`bandit`, `pip-audit`, `trivy`, `ruff`, `mypy`, `pytest`); reproducibility check on a clean machine

## Phase 7 — Frontend (deliberate, not slop)
- [ ] Design pass using a real frontend-design skill / crafted master prompt
- [ ] Confirm aesthetic direction with the user FIRST
- [ ] Dashboard: pipeline runs, query results, consent state, audit log — over the existing API

## Cross-cutting (every phase)
- Update `docs/` + add an ADR for any significant decision.
- Keep `claude/PROJECT_CONTEXT.md` current.
- Never commit secrets or data.
