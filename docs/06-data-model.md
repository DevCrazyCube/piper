# 06 — Data Model

> Conceptual model for the consolidated PostgreSQL + TimescaleDB store. This is a design
> sketch to align the team — concrete DDL lives in `db/migrations/` once we start building.

---

## 1. Zones

- **Raw zone** — write-once landing for raw payloads (file rows, webhook JSON). Access-restricted,
  checksummed, kept for provenance/erasure. Never queried for analytics.
- **Curated zone** — cleaned, normalized, pseudonymised, harmonised data. Analytics run here, via
  **views** that never expose direct identifiers.
- **Reference** — read-only lookups (Open Food Facts nutrition).

## 2. Identity & pseudonymisation

```
real identity (name, email, device id)        surrogate key
        │  ── kept ONLY in ──┐                      ▲
        ▼                    │                      │
  id.subject  ──────────────┘  (app-layer AES-256-GCM encrypted `enc_identity BYTEA`, restricted role)
        │  maps real_id  ⇄  subject_pid (random UUID)
        ▼
  everything else references subject_pid, never the real identity
```

- The **mapping table** (`id.subject`, column `enc_identity BYTEA`) is the crown jewel: encrypted at
  the **application layer** (AES-256-GCM in Python *before* INSERT, so the DB only ever stores
  ciphertext and the key never transits SQL — see ADR-0008). pgcrypto is **not** used (no
  `CREATE EXTENSION pgcrypto` in any migration). Readable only by a restricted role, excluded from
  analyst/engineer grants and from backups shared with the team.
- Curated tables key on `subject_pid`. Re-identification requires the map → defense in depth.

## 3. Core entities (curated)

| Table | Type | Notes |
|---|---|---|
| `id.subject` | relational | `subject_pid` (PK), `enc_identity BYTEA` (app-layer AES-256-GCM), source provenance |
| `consent.consent` | relational | per subject + purpose/scope + timestamp + status (drives consent enforcement) |
| `curated.timeseries` | **hypertable** | `(subject_pid, metric, ts, value)` — generic metric store holding heart-rate / steps / active-minutes etc. by `metric` label; PMData ~20M rows, Timescale partitioned |
| `curated.sleep` | **hypertable** | (subject_pid, ts, stage/score fields) |
| `curated.wellness` | relational + **JSONB** | self-reported; irregular fields in JSONB |
| `curated.meal` | relational + JSONB | meal logs; links to `food_reference` for nutrition enrichment |
| `curated.food_reference` | reference | curated subset of Open Food Facts (minimised columns; `nutriments` flattened per-100g) |
| `curated.student_academic` | relational | harmonised UCI datasets 2 + 4 (grades, study time, absences) |
| `meta.decision` | relational | provenance: source, rows in/out, decisions, timestamp |
| `meta.quarantine` | relational | rows/payloads that failed validation: raw value + reason (dead-letter, never silently dropped) |
| audit log | append-only | authn, access, modifications, config changes |

> **Not yet built:** there is no `calendar_event` table (and no calendar/LMS connector) — calendar
> remains a planned source, see §7.

> **Idempotency (ADR-0010):** content-hash idempotency lives on **`raw.record`** (a `content_hash`
> column with a unique index, migration 0001); re-ingesting the same file/payload is rejected by that
> index rather than duplicated. **Curated** tables instead dedup by their **natural-key primary keys**
> (no content_hash column). Webhook events dedup on the time-series grain `(source, participant,
> metric, ts)` via `ON CONFLICT DO NOTHING`, with a separate **`meta.webhook_nonce`** store for
> replay protection — there is no device + event-id idempotency key.

## 4. Row-Level Security (RLS)
- **FORCE RLS** on all curated subject tables; a `data_subject` session sees only rows where
  `subject_pid = current_setting('piper.subject_pid')`. The app runs as a NOSUPERUSER role so RLS
  is genuinely enforced (migration 0005).
- **Consent is enforced separately** (not inside the RLS predicate): revoking a scope deletes that
  scope's curated data (`process/consent.py`), which is simpler and stronger than encoding a
  metric→scope join into every policy.
- `analyst` sees only aggregate **views**; base subject tables are not granted to it.

## 5. Time-series design (TimescaleDB)
- `curated.timeseries` (the generic `(subject_pid, metric, ts, value)` store) and `curated.sleep`
  are **hypertables** chunked by time → fast range scans for Q1/Q2 (daily active minutes,
  wellness-vs-schedule).
- Daily/weekly rollups are computed **on the fly** with `time_bucket(...)` in the analytics queries
  (`src/pipeline/analyse/queries.py`), and **only aggregate outputs are exposed** (privacy win).
- TimescaleDB **continuous aggregates** (materialised rollups) are **not** implemented; they remain a
  planned optional optimisation (see roadmap) for if/when query cost matters.

## 6. Schema harmonisation (datasets 2 ⨝ 4)
- Dataset 2 and Dataset 4 use different column names + scales for overlapping concepts (grades,
  study time, background). A **mapping layer** normalizes both into `student_academic` with a
  `source` provenance column and reconciled scales. Dedup of students appearing in both Dataset 2
  files happens before the merge.

## 7. The 5 queries against this model (sketch)
- **Q1** daily active minutes → on-the-fly `time_bucket` over `curated.timeseries` (active-minutes
  metrics), exclude scheduled rest windows. (Calendar source not yet built — see §3.)
- **Q2** schedule vs wellness → (planned `calendar_event`) ⨝ (`curated.sleep` / `curated.timeseries`
  / `curated.meal`), per-subject, consented. Calendar input is a planned seam, not yet implemented.
- **Q3** study time vs grades → `curated.student_academic` ⨝ study logs (institutional, pseudonymous join).
- **Q4** meal nutrition vs wellness → `curated.meal` ⨝ `curated.food_reference` ⨝ `curated.wellness` (candidate).
- **Q5** cross-institutional harmonised view → `curated.student_academic` (datasets 2+4) (candidate).

## 8. Retention & erasure
- Each table has a retention class; Timescale data-retention policies auto-drop aged chunks.
- Erasure (Art. 17) cascades across live data: `curated.*` rows → `raw.*` payloads → the `id.subject`
  mapping entry → `meta.quarantine` / `meta.device` / `consent.consent` (`process/erase.py`). Deleting
  the `id.subject` row destroys the link to the real identity, so the remaining pseudonymous data
  cannot be re-identified.
- **Backups are not edited per row.** Existing encrypted backups are not retroactively purged; they
  age out under retention / rotation (see `docs/05-compliance.md` and `erase.py`'s docstring).
- A deletion receipt records what was erased + when (verifiable, not symbolic).
