# Internal Audit & Remediation — 2026-06-15

A full read-only audit (architecture, code quality, security, compliance-vs-docs) was run across
the codebase by four independent reviewers. This records the findings and what was done. Items are
**Fixed**, **Mitigated/Documented** (pragmatic call recorded), or **Deferred**.

## Critical
| # | Finding | Status |
|---|---|---|
| C1 | App connected as a Postgres **superuser → RLS bypassed** (access control void) | **Fixed** — migration 0005 adds NOSUPERUSER/NOBYPASSRLS `aegis_app`; runtime connects as it (`bootstrap`); FORCE RLS + policies on all 4 curated subject tables. Verified `rolsuper=f`. |
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
