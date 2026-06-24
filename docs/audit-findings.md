# Internal Audit & Remediation — 2026-06-15

A full read-only audit (architecture, code quality, security, compliance-vs-docs) was run across
the codebase by four independent reviewers. This records the findings and what was done. Items are
**Fixed**, **Mitigated/Documented** (pragmatic call recorded), or **Deferred**.

## Critical
| # | Finding | Status |
|---|---|---|
| C1 | App connected as a Postgres **superuser → RLS bypassed** (access control void) | **Fixed** — migration 0005 adds NOSUPERUSER/NOBYPASSRLS `piper_app`; runtime connects as it (`bootstrap`); FORCE RLS + policies on all 4 curated subject tables. Verified `rolsuper=f`. |
| C2 | `curate_academic` **not idempotent** — re-run doubled the data | **Fixed** — delete-by-origin before insert; verified re-runs stable. |
| C3 | Hourly rollup **mis-aggregated daily-total** active-minutes | **Fixed** — split grain: intraday→hour, daily-total metrics→day. Verified active-minutes now 100% day-grain. |
| C4 | Pseudonymisation map stored `source_local_id` **in plaintext** next to ciphertext | **Mitigated/Documented** — schema `id` is app-role-only (engineers/analysts/subjects denied); kept plaintext source id for joins is standard pseudonymisation, and the doc now states this honestly (protection = schema access control, not the key alone). Blind-index refactor deferred (pNN data, would force pgcrypto). |
| C5 | **Single master key** for fields + device secrets + backups | **Fixed** — HKDF purpose-separated keys (identity/device/receipt) + AAD; data re-encrypted. Backup key separation recommended (still defaults to master if unset). |

## High
| Finding | Status |
|---|---|
| Consent seeded but never enforced | **Fixed** — `consent grant/revoke`; revoke deletes that scope's curated data (verified 81→0). |
| Replay nonce cache in-process only (multi-worker/restart) | **Fixed** — DB `meta.webhook_nonce` unique-insert is authoritative; in-memory kept as fast pre-check. Verified replay→401. |
| No data-subject export (Art. 15/20) | **Fixed** — `export` command → JSON. |
| `content_hash(default=str)` type-fragile | **Fixed** — canonicalises Decimal/datetime/float/bytes before hashing. |
| DD/MM date parser silently guesses; docstring claimed otherwise | **Documented** — docstring now states the day-first assumption explicitly (correct for the only slash-date source). |
| Webhook: no TLS, leaky auth errors, no rate limit | **Partially fixed** — generic 401 (no oracle); TLS _planned_ (documented); rate limiting deferred to a gateway. |
| Single transaction per run / partial-failure ambiguity | **Documented** — acceptable given content-hash idempotency makes re-runs safe; per-batch commit deferred. |
| Duplicated curate insert logic; no curate provenance; phantom `privacy/`+`store/` packages | **Partially fixed** — phantom packages removed + docs corrected; shared upsert/`Curator` refactor **Deferred** (tracked). |

## Medium
| Finding | Status |
|---|---|
| Erasure missed quarantine/device/decision/backups | **Fixed** for quarantine + device; backups age-out documented; `meta.decision` holds no direct identifiers (kept). |
| Deletion receipt = unkeyed SHA-256 ("signed") | **Fixed** — keyed HMAC (`receipt_mac`); doc says "keyed", not "signed". Verified MAC validates. |
| Engineer role could INSERT audit/receipts | **Fixed** — revoked in migration 0005. Verified denial. |
| k-anonymity only on 2/5 queries | **Fixed** — `HAVING count >= k` on all five. |
| `DELETE FROM {table}` f-string | **Fixed** — `psycopg.sql.Identifier`. |
| AAD never used with GCM | **Fixed** — purpose AAD on all encrypt/decrypt. |
| Academic dedup took non-grade fields from `recs[0]` | **Fixed** — aggregates study/failures/absences across mat+por. |

## Deferred (tracked, lower priority)
- Shared `upsert()` + streaming `raw_records()` helper + a `Curator` abstraction symmetric to
  `Connector` (with its own provenance run-row) — reduces curate duplication structurally.
- Per-batch commit / resumable runs.
- Dedicated backup key (vs master) + key rotation with key-id in ciphertext.
- Rate limiting on the webhook (recommend an API gateway).
- TLS termination + LUKS at-rest (deployment).

## Doc honesty pass
`security-policy.md`, `04-security.md`, `05-compliance.md`, `06-data-model.md` corrected: removed/
flagged `pgcrypto`, Argon2id, MFA, `auditor`/`admin` roles, "TLS in place", "minimisation at ingest",
"erasure incl. backups", "signed receipt", and the "117 MB / 3-2-1 verified" specifics.

---

# Audit pass (automated) — 2026-06-23

A follow-up automated read-only pass surfaced the items below. These are **confirmed important
but RISKY to auto-fix** (they touch access control, GDPR-erasure semantics, consent lawful-basis,
and the DB role/connection model), so they are recorded here as **recommendations for human
review** rather than applied. No source, migration, or crypto was modified.

## Critical
| Finding | Location | Risk | Recommended fix |
|---|---|---|---|
| Read API has **no authn/authz** — entire dashboard read surface is open | `src/pipeline/api/read.py` — `router = APIRouter(prefix="/v1")` (line 15); all `@router.get` endpoints (lines 59–334) | Every read endpoint (`/v1/counts`, `/runs`, `/sources`, `/overview`, `/analytics`, `/consent`, `/security/audit`, `/security/summary`, `/consent/subjects`, `/security/anomalies`, `/security/compliance`) is mounted with no FastAPI dependency, API key, or header check. Ingest (`api/app.py`) is HMAC-protected, but reads are not. CORS (`allow_origins` localhost:5173/4173) is **browser-enforced policy, not server-side access control** — any non-browser client (curl, scripts, a tunnelled attacker; `docker-compose.yml` exposes port 8000 "for live demos behind a tunnel") can call them freely. Leaks operational/security posture, audit-log actor+action history, anomaly actors, and pseudonymous subject handles (`/v1/consent/subjects` exposes `subj_<4hex>` derived from real `subject_pid`). `docs/security-policy.md` asserts RBAC + least privilege under "Access"; the read API enforces neither. | Add a server-side auth dependency to the read router (shared API key / bearer token via FastAPI `Depends`, or place it behind the same authenticated gateway as the webhook). Do not rely on CORS for authorization. At minimum require a token for `/v1/security/*` and `/v1/consent/*`. |

## Major
| Finding | Location | Risk | Recommended fix |
|---|---|---|---|
| RLS subject-isolation is **never exercised**; runtime runs under permissive `USING(true)` | `db/migrations/versions/0005_rbac_hardening.py` — `CREATE POLICY app_all ... USING (true) WITH CHECK (true)` (lines 60–63); runtime connects as `piper_app` via `common/db.py:pg_connection` | FORCE RLS is correctly enabled on the four curated subject tables, but every runtime path (API reads **and** CLI export/erase/curate) connects as `piper_app`, whose `app_all` policy is `USING(true) WITH CHECK(true)` — it sees all rows. The `subject_isolation` policy is granted only to `piper_subject` and depends on `current_setting('piper.subject_pid')`; nothing in `src/` ever calls `set_config`/`SET ROLE`/`SET LOCAL` or sets `piper.subject_pid` (zero matches). So the per-subject isolation the docs claim is decorative — it cannot trigger in any shipped path. `process/export.py::export_subject` and `process/erase.py::erase_subject` accept an arbitrary `subject_pid` and return/delete that subject's data with no binding between caller and subject; under `piper_app`, RLS does not constrain them. This is an authorization gap, not just doc drift. | For the subject-facing read/export path, open a connection that does `SET ROLE piper_subject` + `SET LOCAL piper.subject_pid = <authenticated subject>` per request so RLS enforces isolation; or implement explicit authz binding the API caller to the `subject_pid` before export/erase. Update docs to state RLS is currently only a defense-in-depth backstop for a future subject session, not active in the app-role path. |
| Special-category **health consent seeded "granted-by-default"** with `lawful_basis` defaulting to `consent` | `src/pipeline/process/curate_health.py` — `_SCOPES` seeding loop (lines 30–35), `INSERT INTO consent.consent ... ON CONFLICT DO NOTHING` with no explicit status | `curate_pmdata` seeds a consent row per participant per health scope (sleep, heart_rate, activity, meals) with no status, relying on the schema default `status='granted'` (`0002_curated.py` line 45) and `lawful_basis` default `'consent'` (line 44). `docs/05-compliance.md` flags HR/sleep/meals as Art. 9 special-category data requiring **explicit, opt-in** consent. Recording `consent=granted` for data the subject never actively gave is the opposite of explicit consent and undermines the Art. 7 / Art. 9(2)(a) basis claimed. Nothing sets `lawful_basis` away from the default, so `read.py`'s `/v1/consent` mapping (consent vs public_task vs legitimate_interest, line 239) can only ever report `consent`, and `security-policy.md` §L's claim that grades use a `public-task` basis is unreflected in any code that writes `lawful_basis`. | Seed health/wellness consent as `status='pending'` or `'revoked'` until an explicit grant is recorded, rather than `'granted'`. Set `lawful_basis` explicitly per scope when seeding (`consent` for health, `public_task` for institutional grades) instead of relying on a blanket default. Document the opt-in flow. |
| Quarantine erasure uses **unanchored substring `LIKE`** on source-local id — over- and under-deletes | `src/pipeline/process/erase.py` — `erase_subject`, `DELETE FROM meta.quarantine WHERE source = %s AND raw_value LIKE %s` (lines 60–64), pattern `f"%{local_id}%"` | (1) **Over-deletion:** PMData ids are `pNN` (e.g. `p1`), so `'%p1%'` also matches `p10..p19` and any unrelated `raw_value` text containing `p1`, deleting **other subjects'** quarantine rows. (2) **Under-deletion:** `local_id` is interpolated raw into the `LIKE` pattern; if it contains `%`, `_`, or `\` those act as wildcards/escapes and the match misbehaves — quarantined PII for the subject may survive an Art. 17 erasure. (3) `raw_value` is a free-text blob (`str(raw_value)[:2000]` in `ingest/base.py`) that may not even contain the id (e.g. a bad-timestamp value, or `None`), so genuinely PII-bearing quarantined rows can be missed. The erasure is thus both **incomplete** (compliance failure) and **destructive to other subjects'** records. `record_ref` is set to `f"{pid}/{metric}"` in pmdata and is a far more precise key. | Stop keying quarantine erasure on substring matching of free text. Add a structured subject/participant column (or use `record_ref`) to `meta.quarantine` populated at ingest, and erase by exact equality on that column (e.g. `record_ref LIKE source_local_id || '/%'` — anchored, with separator). If substring matching must remain temporarily, at minimum escape `LIKE` metacharacters and anchor the match, keying off `record_ref` rather than free-form `raw_value`. |
| Runtime DB connection **silently falls back to the superuser** when no app password is set (fail-open) | `src/pipeline/common/config.py` — `psycopg_conninfo` property (lines 61–66): returns `admin_conninfo` when `app_password` is empty | `psycopg_conninfo` returns the non-superuser `piper_app` DSN only if `app_password` is configured; otherwise it returns `admin_conninfo` — the superuser `piper`, which has **BYPASSRLS**. A deployment that forgets `PIPER_APP_PASSWORD` runs the entire runtime (API ingest + all reads) as the superuser, silently bypassing every RLS policy and voiding the access-control layer — exactly the **C1** finding 0005 claims to have fixed. There is no startup assertion that the runtime role is non-superuser, and port 8000 is exposed for tunnelled demos. | Make the app role mandatory outside trivial dev: raise a `ConfigError` (or warn loudly) if `app_password` is empty when serving the API, or verify `SELECT current_setting('is_superuser') = 'off'` on first connection and refuse to start otherwise. |
