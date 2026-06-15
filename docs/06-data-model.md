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
  subject_identity_map  ─────┘  (pgcrypto-encrypted, restricted role)
        │  maps real_id  ⇄  subject_pid (random UUID)
        ▼
  everything else references subject_pid, never the real identity
```

- The **mapping table** is the crown jewel: encrypted at the **application layer** (AES-256-GCM in
  Python *before* INSERT, so the DB only ever stores ciphertext and the key never transits SQL — see
  ADR-0008), readable only by a restricted role, excluded from analyst/engineer grants and from
  backups shared with the team.
- Curated tables key on `subject_pid`. Re-identification requires the map → defense in depth.

## 3. Core entities (curated)

| Table | Type | Notes |
|---|---|---|
| `subject` | relational | `subject_pid` (PK), consent scopes, source provenance |
| `consent` | relational | per subject + purpose/scope + timestamp + status (drives RLS) |
| `heart_rate` | **hypertable** | (subject_pid, ts, bpm) — PMData ~20M rows, Timescale partitioned |
| `sleep` | **hypertable** | (subject_pid, ts, stage, score) |
| `activity` | **hypertable** | (subject_pid, ts, steps, active_minutes, kcal) |
| `wellness` | relational + **JSONB** | self-reported; irregular fields in JSONB |
| `meal_log` | relational + JSONB | links to `food_reference` for nutrition enrichment |
| `food_reference` | reference | curated subset of Open Food Facts (minimised columns) |
| `student_academic` | relational | harmonised UCI datasets 2 + 4 (grades, study time, absences) |
| `calendar_event` | relational | (later) calendar source |
| `pipeline_run` | relational | provenance: source, rows in/out, decisions, timestamp |
| `quarantine` | relational | rows/payloads that failed validation: raw value + reason (dead-letter, never silently dropped) |
| `audit_log` | append-only | authn, access, modifications, config changes |

> **Idempotency (ADR-0010):** curated tables carry a **natural key + content hash**; re-ingesting the
> same file/payload **upserts**, never duplicates. Webhook events carry a device + event-id idempotency key.

## 4. Row-Level Security (RLS)
- **FORCE RLS** on all curated subject tables; a `data_subject` session sees only rows where
  `subject_pid = current_setting('aegis.subject_pid')`. The app runs as a NOSUPERUSER role so RLS
  is genuinely enforced (migration 0005).
- **Consent is enforced separately** (not inside the RLS predicate): revoking a scope deletes that
  scope's curated data (`process/consent.py`), which is simpler and stronger than encoding a
  metric→scope join into every policy.
- `analyst` sees only aggregate **views**; base subject tables are not granted to it.

## 5. Time-series design (TimescaleDB)
- `heart_rate`, `sleep`, `activity` are **hypertables** chunked by time → fast range scans +
  continuous aggregates for Q1/Q2 (daily active minutes, wellness-vs-schedule).
- Continuous aggregates (materialized rollups) precompute daily/weekly metrics → cheap queries,
  and **only aggregates are exposed** (privacy + performance win).

## 6. Schema harmonisation (datasets 2 ⨝ 4)
- Dataset 2 and Dataset 4 use different column names + scales for overlapping concepts (grades,
  study time, background). A **mapping layer** normalizes both into `student_academic` with a
  `source` provenance column and reconciled scales. Dedup of students appearing in both Dataset 2
  files happens before the merge.

## 7. The 5 queries against this model (sketch)
- **Q1** daily active minutes → continuous aggregate on `activity`, exclude calendar rest windows.
- **Q2** schedule vs wellness → `calendar_event` ⨝ (`sleep`/`activity`/`meal_log`), per-subject, consented.
- **Q3** study time vs grades → `student_academic` ⨝ study logs (institutional, pseudonymous join).
- **Q4** meal nutrition vs wellness → `meal_log` ⨝ `food_reference` ⨝ `wellness` (candidate).
- **Q5** cross-institutional harmonised view → `student_academic` (datasets 2+4) (candidate).

## 8. Retention & erasure
- Each table has a retention class; Timescale data-retention policies auto-drop aged chunks.
- Erasure (Art. 17) cascades: curated rows → raw payloads → mapping entry → flagged in backups.
- A `deletion_receipt` records what was erased + when (verifiable, not symbolic).
