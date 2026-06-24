> _Draft — AI-assisted scaffold for the Piper project. Every figure here was measured/derived from the repo, but verify against the code and data and put it in your own words before submission._

# 09 — Database Technology Comparison

> Why the store is **one PostgreSQL 16 engine with the TimescaleDB extension** and not InfluxDB,
> ClickHouse, MongoDB, DuckDB, or a polyglot mix. This doc backs `adr/0003` with a criteria matrix
> and states honestly where each alternative *would* win. Decision is **accepted** in
> [`adr/0003`](adr/0003-consolidated-postgres-timescaledb.md); this is the supporting comparison.

---

## 1. The workload we are actually choosing for

A database choice only means something against a real workload. Piper's, taken from the data model
([`06-data-model.md`](06-data-model.md)), the sources ([`03-data-sources.md`](03-data-sources.md)),
and the live schema (`db/schema/schema.sql` + `db/migrations/`):

- **High-volume time-series** — HR / sleep / steps from PMData and the live wearable feed. The
  design budgeted "~20M+ raw heart-rate rows"; the running container is already past that. Measured
  on `datapipeline-db-1` (`timescale/timescaledb:2.17.2-pg16`, PostgreSQL **16.6**):
  - `raw.timeseries` ≈ **27.4M rows** (`SELECT count(*)` → 27,440,613), a TimescaleDB **hypertable**
    chunked at 7-day intervals.
  - `curated.timeseries` ≈ **207k rows** (pseudonymised, keyed by `subject_pid`), also a hypertable.
  - Two hypertables exist today (`raw.timeseries`, `curated.timeseries`); `pg_extension` shows
    `timescaledb 2.17.2` loaded.
- **Relational academic records** — harmonised UCI datasets 2 + 4 in `curated.student_academic`
  (grades, study time, absences, attendance band), plus `id.subject`, `consent.consent`,
  `meta.*` registry/provenance tables — the classic join-and-constraint shape.
- **Free-form / semi-structured** — wellness notes, meal logs, raw payloads and run detail land in
  **JSONB** (`raw.record.payload`, `meta.pipeline_run.detail`, `curated.student_academic.detail`).
- **Reference lookup** — `curated.food_reference`, a minimised subset of Open Food Facts, joined to
  enrich meals (best-effort fuzzy match, not a hard FK — see `03-data-sources.md`).
- **GDPR / security-first constraints** that the database itself must enforce, not just the app:
  - **Pseudonymisation** — the real-id ⇄ `subject_pid` map lives in `id.subject.enc_identity`
    (`BYTEA`), encrypted at the **application layer** (AES-256-GCM in Python before INSERT) so the
    engine only ever stores ciphertext and the key never transits SQL (ADR-0006 / ADR-0008).
  - **Row-Level Security** — `FORCE ROW LEVEL SECURITY` on every curated subject table
    (`timeseries`, `sleep`, `wellness`, `meal`) with a `subject_isolation` policy bound to
    `current_setting('piper.subject_pid')`; the runtime role `piper_app` is **NOSUPERUSER
    NOBYPASSRLS** so RLS is genuinely enforced (migration `0005_rbac_hardening`).
  - **RBAC** — distinct `piper_analyst` / `piper_engineer` / `piper_subject` / `piper_app` roles,
    least-privilege grants, and **no grant on schema `id`** for engineers/analysts (they cannot read
    the pseudonymisation map).
  - **Auditing + erasure** — append-only `meta.audit_log` driven by triggers on the high-value
    tables, plus `meta.deletion_receipt` (sha256-digested) for verifiable Art. 17 erasure, and a
    TimescaleDB **retention policy** on `raw.timeseries` to demonstrate the deletion obligation.
- **Operational envelope** — **single-node Docker Compose**, taught in Week 2 and locked in
  [`adr/0004`](adr/0004-docker-compose-local.md). Reproducible on every teammate's laptop and for
  grading. No cluster, no managed cloud service.

The headline tension: **one workload needs both serious time-series ingestion *and* relational joins
*and* native, in-database GDPR controls, all on a single node.** Few engines do all three well; that
is what the matrix below tests for.

---

## 2. Candidates

Realistic options for this exact shape — not a survey of every database in existence:

| Candidate | Category | Why it's in the running |
|---|---|---|
| **Vanilla PostgreSQL 16** | Relational (RDBMS) | Baseline: does everything except large-scale TS *fast* |
| **PostgreSQL + TimescaleDB** *(chosen)* | RDBMS + TS extension | Postgres' relational/security stack **plus** hypertables |
| **InfluxDB** | Purpose-built TSDB | Built for exactly the HR/steps firehose |
| **ClickHouse** | Columnar OLAP | Extreme analytical scan/aggregate throughput |
| **MongoDB** | Document store | Natural fit for the free-form wellness/meal docs |
| **DuckDB** | Embedded OLAP (columnar) | In-process analytics over Parquet (the 7 GB OFF file) |

The group pptx originally proposed a **polyglot** stack (Postgres + TimescaleDB + MongoDB + InfluxDB
at once); that combination is evaluated as its own option in §5.

---

## 3. Criteria matrix

Scoring is **for Piper's workload on a single node**, not in the abstract. Legend:
✅ strong · 🟠 within reach / good-enough · ⚠️ weak or needs significant work · ❌ disqualifying gap.

| Criterion | Vanilla PG | **PG + TimescaleDB** | InfluxDB | ClickHouse | MongoDB | DuckDB |
|---|---|---|---|---|---|---|
| **Time-series perf** (27M+ rows, range scans, rollups) | ⚠️ works, but no auto-partitioning/CAGGs | ✅ hypertables + continuous aggregates | ✅ purpose-built | ✅ excellent columnar scans | ⚠️ time-bucketing is manual | ✅ fast *analytical*, embedded |
| **Relational / joins** (academic ⨝ consent ⨝ subject) | ✅ full SQL, FKs, constraints | ✅ same — it *is* Postgres | ⚠️ joins weak/limited | 🟠 joins exist, denormalise-first model | ⚠️ no real joins; `$lookup` is awkward | ✅ rich SQL joins |
| **SQL maturity** | ✅ decades of SQL | ✅ standard SQL + TS funcs | ⚠️ Flux/InfluxQL, non-standard | 🟠 SQL-ish, own dialect/quirks | ❌ no SQL (MQL) | ✅ Postgres-like SQL |
| **RLS / row-level security for GDPR** | ✅ native `FORCE RLS` + policies | ✅ **same native RLS** (in use, migration 0005) | ❌ none | ❌ none (row policies not a feature) | ⚠️ no true RLS; app-enforced | ❌ none (embedded, single-user) |
| **Encryption / extensions** (`pgcrypto`, app-layer `BYTEA`) | ✅ `pgcrypto`, extension ecosystem | ✅ `pgcrypto` available + extension model | ⚠️ TLS + at-rest, no column crypto ext | 🟠 at-rest, some functions | 🟠 field-level (Enterprise/CSFLE) | ⚠️ no server crypto model |
| **Ops / single-node Docker fit** | ✅ one container | ✅ **one container** (`timescaledb:2.17.2-pg16`) | 🟠 separate service to run/secure | 🟠 separate service, ops weight | 🟠 separate service | ✅ no server (in-process lib) |
| **Ecosystem** (SQLAlchemy 2.x, psycopg3, Alembic, pandas/polars) | ✅ first-class | ✅ first-class (it's Postgres on the wire) | ⚠️ bespoke clients | 🟠 decent, separate driver | 🟠 PyMongo, no SQLAlchemy ORM fit | ✅ great for analytics, weak as system-of-record |
| **Attack surface** (security-first thesis) | ✅ one engine | ✅ **one engine** | ⚠️ +1 service to patch/encrypt/RBAC | ⚠️ +1 service | ⚠️ +1 service | 🟠 embedded; no network surface but not a server |

**Read of the matrix:** only two columns are green on **both** the time-series row and the RLS row —
and one of them (vanilla PG) is yellow on time-series performance. **PG + TimescaleDB** is the single
candidate with no ⚠️/❌ in any row for this workload.

---

## 4. Why PostgreSQL + TimescaleDB wins here

Tied directly to `adr/0003`:

1. **It collapses three databases into one engine.** Time-series → hypertables + continuous
   aggregates; relational → standard tables and joins; free-form → JSONB; reference → a plain table.
   Every shape Piper has is covered without cross-database glue. The proof is already in the repo:
   `raw.timeseries`/`curated.timeseries` are hypertables, `curated.student_academic` is relational,
   `raw.record.payload` is JSONB, `curated.food_reference` is a lookup — **all in one schema, one
   container.**

2. **Security-first ⇒ minimise attack surface — the core argument.** One engine to encrypt, patch,
   back up, and apply RBAC/RLS/`pgcrypto` to, instead of three or four. Piper's GDPR controls are
   *native to Postgres and cannot be ported for free* to InfluxDB/ClickHouse/Mongo: `FORCE RLS` +
   per-table policies (migration 0005), least-privilege roles with the identity map walled off
   (migration 0003 `REVOKE ALL ON SCHEMA id`), trigger-based audit logging, and `pgcrypto`
   availability for column crypto. A polyglot stack would have to **re-invent or forgo** each of
   these on every extra engine.

3. **TimescaleDB is real engineering for the volume, not a toy.** Automatic 7-day chunking,
   time-bucketed continuous aggregates (`curated.v_daily_active_minutes` is already a `time_bucket`
   rollup), and data-retention policies (`add_retention_policy('raw.timeseries', …)`) give the
   volume/velocity story the course wants — on the same engine that does the joins. The live
   container holding **27.4M rows** in a hypertable is the evidence it scales to our data.

4. **Ecosystem alignment removes a whole class of risk.** Because it speaks the Postgres wire
   protocol, the chosen stack (SQLAlchemy 2.x + psycopg 3 + Alembic, per
   [`02-tech-stack.md`](02-tech-stack.md)) works unchanged — parameterised queries (no SQL injection),
   reviewable migrations, and `pandas`/`polars` read/write. A TSDB or document store would mean
   bespoke clients and weaker ORM/migration tooling.

5. **It fits the operational envelope exactly.** One Docker Compose service
   (`timescale/timescaledb:2.17.2-pg16`) brings the whole store up identically on every laptop and
   for grading (ADR-0004). No second service to run, secure, and explain.

**Cost honestly stated** (from ADR-0003's "Consequences"): less *visible* tech breadth than showing
four databases, and at genuinely huge **write throughput** a dedicated TSDB would eventually win —
but that is not our scale. We trade a breadth talking-point for a smaller, more defensible security
surface, which is the project's whole thesis.

---

## 5. When each alternative would actually win

Stated fairly, so the choice is defensible rather than dogmatic:

- **Vanilla PostgreSQL (no TimescaleDB)** — would win if the time-series volume were small (say <1M
  rows) or query patterns were point-lookups, not time-range aggregations. At 27M+ rows with daily
  rollups, manual partitioning and hand-rolled aggregates would be a lot of work for what the
  extension gives free. *We're choosing the extension precisely because we're past that line.*

- **InfluxDB** — wins for a **pure** telemetry firehose: millions of writes/sec, downsampling,
  retention, dashboards, and essentially **no relational joins or row-level access control needed**.
  Piper fails two of those: it must join health to academic/consent data and must enforce RLS per
  subject. Influx has no RLS and weak joins → it can't carry the GDPR or cross-source-query
  requirements. Noted in ADR-0003 as a documented **scale-out** option if write volume ever explodes.

- **ClickHouse** — wins when the workload is **analytical OLAP at scale**: scanning billions of rows
  for aggregates with best-in-class columnar speed. If Piper became a read-heavy analytics warehouse
  over fixed, denormalised data, ClickHouse would be compelling. But it lacks native RLS, its joins
  and mutations (needed for Art. 17 erasure and consent revocation) are second-class, and it's
  another service to secure. Overkill and a poor fit for a transactional, GDPR-mutating store.

- **MongoDB** — wins when the data is **document-shaped end-to-end** with evolving schemas and few
  cross-entity joins. Piper's free-form fields are real, but they're a *minority* of the model, and
  **JSONB covers them inside Postgres** (ADR-0003 explicitly: "JSONB covers it; not worth the extra
  attack surface"). Mongo has no SQL, no true RLS, and weak joins — it would force the relational and
  GDPR-control work elsewhere. Adding it buys document ergonomics we don't need at the cost of a
  second engine.

- **DuckDB** — wins for **embedded, single-user analytical** work: querying the 7 GB Open Food Facts
  **Parquet** file in-process during ETL is a genuinely good use (fast columnar scans, no server).
  It is plausibly useful *inside the pipeline* as a transformation tool. But it is **not a
  system-of-record**: no server, no concurrent multi-role access, no RLS, no durable audit/erasure
  surface. It complements the store; it can't be the store.

- **Full polyglot (Postgres + TimescaleDB + MongoDB + InfluxDB — the group pptx)** — would win if the
  goal were to *demonstrate breadth* across four engines, or if each workload were so large it
  demanded a specialist. At our scale it's **3–4× the security/ops burden for no benefit**: four
  things to patch, encrypt, back up, RBAC, and reconcile during erasure, directly against the
  security-first thesis. Documented in ADR-0003 as **considered & rejected**, with Influx/Mongo kept
  as future scale-out notes.

---

## 6. Summary

For a workload that is simultaneously **time-series (27M+ rows)**, **relational (harmonised academic
+ consent + identity)**, **semi-structured (JSONB wellness/meals)**, and **GDPR-bound (RLS,
pseudonymisation, audit, erasure)** on a **single Docker node**, exactly one candidate clears every
criterion without a weak spot: **PostgreSQL 16 + TimescaleDB**. It is the only option that pairs
serious time-series ingestion with native, in-database GDPR controls (RLS, RBAC, `pgcrypto`) on one
engine — minimising the attack surface, which is the project's defining constraint. The alternatives
each win a single axis (Influx: write throughput; ClickHouse: analytical scans; Mongo: document
ergonomics; DuckDB: embedded Parquet analytics) but lose the combination Piper actually needs.

**See:** [`adr/0003`](adr/0003-consolidated-postgres-timescaledb.md) (the decision),
[`adr/0006`](adr/0006-pseudonymisation-and-encryption.md) /
[`adr/0008`](adr/0008-application-layer-encryption-key-custody.md) (pseudonymisation + key custody),
[`02-tech-stack.md`](02-tech-stack.md) (stack), [`06-data-model.md`](06-data-model.md) (schema), and
`db/migrations/0005_rbac_hardening.py` (RLS/RBAC as implemented).

> Figures (27.4M / 207k rows, PostgreSQL 16.6, TimescaleDB 2.17.2, `pgcrypto` available-but-not-yet-
> installed) were measured against the live `datapipeline-db-1` container on 2026-06-23. **Re-measure
> before submission** — your row counts will differ as ingestion progresses.
