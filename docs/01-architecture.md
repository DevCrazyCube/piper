# 01 — System Architecture

> Grounded in the PR10 8-stage pipeline model and the Week 5 security lecture.
> Every stage carries Security / Privacy / Fairness controls (detailed in `04-security.md`).

---

## 1. The 8 lifecycle stages

```
   ┌──────────┐   ┌───────────┐   ┌────────┐   ┌──────────┐
   │01 INGEST │──▶│02 TRANSPORT│──▶│03 STORE│──▶│04 PROCESS│
   └──────────┘   └───────────┘   └────────┘   └──────────┘
        │                                            │
   raw, messy                                  clean/filter/
   multi-source                                normalize/dedup/
                                               harmonise/pseudonymise
                                                    │
   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │08 DELETE │◀──│07 MONITOR│◀──│06 ACCESS │◀──│05 ANALYSE│
   └──────────┘   └──────────┘   └──────────┘   └──────────┘
   verified         audit logs    RBAC + RLS     5 cross-source
   erasure          anomaly det.  least-priv     queries
   (incl backups)
```

Your own phrasing — *"cleans, filters, normalizes, encrypts, then drops into a database"* —
is stages **01 → 04 → 03**. The full lifecycle adds the controls around it.

## 2. Component view

```
                        ┌─────────────────────── INGEST ───────────────────────┐
  BATCH SOURCES         │                                                       │
  ┌─────────────┐       │  ┌────────────────┐      ┌────────────────────────┐  │
  │ PMData zip   │──────┼─▶│ Batch connectors│      │  Webhook Ingest API     │◀─┼── teammates'
  │ UCI Student  │      │  │ (file readers,  │      │  (authenticated POST,   │  │   Apple Watch
  │ Open Food F. │      │  │  format-aware)  │      │   JSON health events)   │  │   via auto-export
  │ UCI Academics│      │  └───────┬─────────┘      └───────────┬─────────────┘  │   iOS app
  └─────────────┘       │          │                            │                │
  Apple Health export ──┼──────────┘         (optional queue:   │   + Calendar API
       (fallback)       │                     Kafka/Redis Stream)│   + LMS export
                        └──────────────────────┬─────────────────┘
                                                ▼
                                    ┌───────────────────────┐
                                    │  PROCESS (Python)      │   clean · filter · normalize
                                    │  pandas / polars       │   dedup · harmonise schemas
                                    │  validation (pydantic) │   pseudonymise · quality checks
                                    └───────────┬───────────┘
                                                ▼ (encrypted in transit, TLS)
                                    ┌───────────────────────┐
                                    │  STORE                 │   encryption at rest
                                    │  PostgreSQL +          │   hypertables (time-series)
                                    │  TimescaleDB           │   JSONB (free-form)
                                    │  RBAC · RLS · pgcrypto │   reference tables (food)
                                    └───────────┬───────────┘
                                                ▼
                       ┌────────────────────────────────────────────────┐
                       │ ANALYSE: 5 cross-source queries (curated views) │
                       │ ACCESS: role-scoped, least privilege            │
                       │ MONITOR: audit logs + anomaly detection         │
                       │ DELETE: verified erasure incl. backups (Art.17) │
                       └────────────────────────────────────────────────┘
                              (clean seam here for a future API + dashboard)
```

## 3. Data flow (happy path)

1. **Ingest** — a connector reads a source (file or webhook payload) into a typed staging
   record. Raw payloads land in a quarantined **raw zone** (write-once, access-restricted).
2. **Transport** — all movement is over TLS; internal service-to-service too. Nothing in clear.
3. **Process** — format-specific cleaning (delimiters, encoding fixes, date parsing), filtering
   (drop junk / out-of-range), normalization (units, scales), deduplication (cross-file student
   merge), schema harmonisation (dataset 2 vs 4), and **pseudonymisation** (replace direct
   identifiers with surrogate keys; mapping table is separately encrypted + access-controlled).
4. **Store** — curated data written to PostgreSQL/TimescaleDB; encryption at rest on the volume;
   sensitive columns additionally protected via `pgcrypto`; row-level security ties rows to a
   subject + consent scope.
5. **Analyse** — the 5 queries run against curated **views**, never raw identifiers; aggregate
   outputs only where individual exposure isn't needed.
6. **Access** — consumers authenticate; RBAC roles (e.g. `engineer`, `analyst`, `subject`) get
   least-privilege grants; teachers cannot see raw wearable data by default.
7. **Monitor** — every authn event, data access, config change, and pipeline run is logged;
   anomaly detection flags unusual access/extraction patterns.
8. **Delete** — a subject's erasure request removes their data across curated store **and**
   backups, with a verifiable deletion record.

## 3a. How it runs (see ADR-0010)

- **CLI + Make targets** drive batch flows (`python -m pipeline ingest|process|analyse ...`); the
  webhook ingest runs as a long-lived FastAPI service. No heavyweight orchestrator at this scale.
- **Idempotent** loads (natural key + content hash) make re-runs safe — no duplicates.
- **Quarantine / dead-letter:** rows or payloads that fail validation are written to a `quarantine`
  table with the raw value + failure reason. Nothing crashes the run; nothing is silently dropped.

## 4. Architectural seams (deliberate extension points)

- **Ingest is pluggable** — a connector interface lets us add sources (new dataset, new wearable,
  new LMS) without touching processing.
- **Webhook API == the future app API** — the authenticated ingest service is the same seam a
  later dashboard/frontend will read from. Building it now means the frontend is additive, not a
  rewrite.
- **Optional message queue** — for the "fancier"/distributed-systems angle (Week 4), a queue
  (Kafka or Redis Streams) can sit between ingest and process to decouple bursty real-time pushes
  from batch processing. Start without it; add if we want the volume/velocity story.

## 5. Repository structure (target)

```
DataPipeline/
├── docs/                  # this documentation (gitignored per request)
├── claude/                # Claude working notes (gitignored)
├── assignments/           # course material (gitignored)
├── datasets/              # raw test data, multi-GB (gitignored)
├── src/
│   └── pipeline/
│       ├── ingest/        # batch connectors + run engine
│       ├── api/           # FastAPI webhook ingest (real-time)
│       ├── process/       # curate: clean/normalize/dedup/harmonise + pseudonymise/consent/erase/export
│       ├── analyse/       # the 5 aggregate queries
│       └── common/        # config, logging, crypto, db, dates, arff, errors
├── db/
│   ├── migrations/        # schema migrations
│   └── schema/            # reference schema SQL (tracked)
├── tests/
├── docker/                # Dockerfiles
├── docker-compose.yml     # whole-stack runtime
├── .env.example           # documented config (no secrets)
└── README.md              # tracked overview
```

See `02-tech-stack.md` for the technology choices and `06-data-model.md` for the schema.
