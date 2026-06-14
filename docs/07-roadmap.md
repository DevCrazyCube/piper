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

## Phase 2 — Process (clean / filter / normalize)  ✅ (verified on live DB)
- [x] Date-format normalization + tolerant type coercion (curated health records)
- [x] Cross-file student dedup (1044→662, 382 merged) + schema harmonisation (UCI 2 ⨝ 4 → grade_final_norm)
- [x] Pseudonymisation (app-layer AES-256-GCM identity map) + consent model + RLS subject isolation
- [x] Open Food Facts flattened nutriments → curated.food_reference (50k, 47.6k with nutrition)
- [x] Curated time-series as hourly rollups (27M→206k; analytics-ready, aggregate-by-design)
- [x] Decision log (meta.decision) for dedup/harmonise/aggregation choices
- [x] RLS verified: subject sees only own rows; analyst = aggregate view only, base table denied
- [ ] Meal→food fuzzy matching (best-effort) — deferred to analytics phase

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
