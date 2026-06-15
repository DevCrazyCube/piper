# Data Security Policy — Piper Learning Analytics Pipeline

**Owner:** Joyren (Security pillar) · **Project:** PR10 Data Engineering group project
**Scope:** the full data lifecycle of the Piper pipeline (ingest → delete)
**Frameworks:** GDPR (EU 2016/679), ISO/IEC 27001, EU Data Act, and the **DELICATE** checklist
**Status:** controls are *implemented and exercised on the live stack* unless marked **_planned_**
or **_deployment step_**. "Verified" means demonstrated by a command/test in this session, not a
formal certification. (Hardened following the 2026-06-15 internal audit — see `docs/audit-findings.md`.)

> This is the data-security policy the project requires. It is structured around **DELICATE**
> (Drachsler & Greller, 2016) so policy and technical design co-evolve, and every clause cites the
> concrete control + where to find it in the codebase. Research basis: no single control suffices →
> **defence in depth** (Liu & Khalil 2023; Daries et al. 2014 on re-identification).

---

## D — Determination (purpose)
Each data source has a single, documented analytics purpose (wellness/academic insight for the
Comenius personalised-education research). Purpose is recorded in `meta.source`; processing outside
it is out of scope. *GDPR Art. 5(1)(b) purpose limitation.*

## E — Explain (transparency)
- Subjects are told what is collected, why, and who can see it (the dashboard's Consent & Security
  views; `docs/03-data-sources.md`).
- All access + changes are recorded in an append-only **audit log** (`meta.audit_log`, triggers on
  `consent.consent` and `id.subject`). *Week 5 Accounting; ISO A.12.4 logging.*

## L — Legitimate (lawful basis)
Lawful basis per scope is stored in `consent.consent.lawful_basis` (consent for wearable/health;
public-task for institutional grades). *GDPR Art. 6.*

## I — Involve (the data subject)
Subjects can **read/export** their own data (`export` command → JSON, Art. 15/20) and request
**erasure** (`erase`). RLS scopes a `data_subject` session to its own rows.

## C — Consent
- Per-subject, per-scope consent records (`consent.consent`), individually grantable/revocable
  (`consent grant|revoke`).
- **Consent is enforced, not just recorded:** revoking a scope deletes the curated data derived
  under it (scoped erasure — `process/consent.py`). Every consent change is audit-logged. *GDPR Art. 7.*

## A — Anonymise (and verify it holds)
- **Pseudonymisation** at processing: real source ids → random `subject_pid`. The pseudonymisation
  map lives in the **access-controlled `id` schema** (reachable only by the app role — engineers,
  analysts and subjects have no grant on it). The real id is **also stored AES-256-GCM
  application-layer encrypted** in `id.subject.enc_identity` (HKDF purpose-separated key + AAD, key
  from env, never in the DB — ADR-0008). *Honest caveat:* the source-local id (`source_local_id`,
  e.g. `p01`) is retained in plaintext **within that restricted schema** for joins — re-identification
  therefore requires access to schema `id`, which is locked down, rather than the encryption key alone.
- Analytics expose **aggregates only**, with a **k-anonymity floor `k=3` on every query** (`analyse`).
- We explicitly **do not** treat anonymisation as a silver bullet — re-identification is real
  (Daries et al. 2014), so pseudonymisation is layered with access control + aggregation + audit.

## T — Technical safeguards (the core)
Mapped to the **CIA triad** and **AAA model** (Week 5):

| Control | Implementation | Evidence |
|---|---|---|
| Encryption in transit | TLS 1.3 (DB connections, webhook) | **_planned_** — not enabled in the local stack; terminate TLS at the gateway |
| Encryption at rest (bulk) | host-volume encryption (LUKS) — community PG has no TDE | **_deployment step_**, not configured in-repo (ADR-0008) |
| Encryption at rest (sensitive) | **AES-256-GCM app-layer**, HKDF **purpose-separated keys** + AAD | `common/crypto.py`, `id.subject` — separate keys for identity/device/receipt |
| Authentication | webhook **API key + HMAC + nonce (DB-backed replay) + timestamp window**; per-device secret AES-encrypted | `api/auth.py`, `api/app.py` — verified: tamper/replay/stale → generic 401 |
| Authorisation (RBAC) | app runs as **NOSUPERUSER `piper_app`** (no RLS bypass); demo roles least-privilege | migration 0005 — verified `rolsuper=f, rolbypassrls=f` |
| Row-level security | **FORCE RLS on all 4 curated subject tables**; subject sees only own rows; analyst = aggregate view only | migrations 0002/0005 — verified isolation under the app role |
| Accounting (logging) | append-only audit log + triggers; anomaly view; engineers cannot write audit/receipts | `meta.audit_log`, migration 0005 |
| Integrity | parameterised SQL (`sql.Identifier`), pydantic validation, content-hash idempotency, FK/PK | `ingest/base.py`, `process/erase.py` |
| Availability / backups | encrypted logical backup, restore-verified; **3-2-1 is the target** (single-site as built) | `scripts/backup.sh` |
| Retention | TimescaleDB retention policy on raw time-series | migration 0003 |
| Erasure (Art. 17) | cascade curated+raw+map+**device+quarantine**, **keyed-HMAC** deletion receipt | `process/erase.py` — verified cascade + MAC validates |
| Quarantine / DLQ | failed rows → `meta.quarantine` (never silently dropped) | `ingest/base.py` |
| Security testing | SAST (`bandit`), deps (`pip-audit`), DAST-light (auth-bypass), container scan (`trivy`) | `make check`, CI |

## E — External partners (governance)
- Dataset licences honoured; **no dataset leaves the machine** (`datasets/` gitignored). The
  PMData **CC BY-NC** restriction is flagged: it cannot feed a commercial/Comenius product output
  (`docs/05-compliance.md`).
- Secrets never committed (`.env` gitignored); key custody documented (ADR-0008).

---

## GDPR article ↔ control quick map
| Article | Control |
|---|---|
| Art. 5(1)(b/c/e) | purpose limitation; **data minimisation applied at curation** (raw zone keeps full payloads for provenance/erasure); retention policy |
| Art. 6 / 7 | lawful basis + consent records; consent revocation enforced (scoped erasure) |
| Art. 15 / 20 | subject read + **`export` command (JSON)** |
| Art. 17 | erasure cascade (curated+raw+map+device+quarantine) + keyed receipt. **Existing backups are NOT retroactively purged** — they age out under retention/rotation. |
| Art. 25 | privacy by design/default — pseudonymisation default, RLS (FORCE), minimisation at curation |
| Art. 32 | encryption (app-layer AES-256-GCM, HKDF key separation), pseudonymisation, RBAC/RLS, backups, logging |

## ISO/IEC 27001 control ↔ implementation
A.9 access control (non-superuser app role + RLS) · A.10 cryptography (AES-256-GCM app-layer +
HKDF-separated keys; TLS _planned_) · A.12 operations security (logging, backups, change control) ·
A.16 incident management (audit trail + anomaly view) · A.18 compliance (GDPR + licence adherence).

## Residual risks (honest)
- **TLS** termination on the published webhook + DB connections is _planned_ (local demo uses a tunnel).
- **At-rest LUKS** volume encryption is a deployment step, not configured in-repo (community PG has no TDE).
- **Backups are not retroactively purged on erasure** — they age out under rotation; a dedicated
  backup key (not the master key) is recommended.
- **The pseudonymisation map keeps the source-local id in plaintext** inside the restricted `id`
  schema for joins; protection relies on schema access control, not the encryption key alone.
- **No human-credential / MFA path** exists (the only authn is per-device HMAC); Argon2id and MFA
  are out of scope until a human admin/login surface is added.
- The in-memory nonce cache in `auth.py` is a fast pre-check; the **DB nonce table is authoritative**
  for replay across workers.
- This is a **student project demonstrating** controls, not a certified production ISMS.
