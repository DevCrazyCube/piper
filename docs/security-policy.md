# Data Security Policy — Aegis Learning Analytics Pipeline

**Owner:** Joyren (Security pillar) · **Project:** PR10 Data Engineering group project
**Scope:** the full data lifecycle of the Aegis pipeline (ingest → delete)
**Frameworks:** GDPR (EU 2016/679), ISO/IEC 27001, EU Data Act, and the **DELICATE** checklist
**Status:** controls below are *implemented and verified on the live stack* unless marked _planned_.

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
Subjects can see their own data (RLS), export it, and request erasure — the `data_subject` role +
`erase` command. *GDPR Arts. 15, 20.*

## C — Consent
- Per-subject, per-scope consent records (`consent.consent`), individually grantable/revocable.
- Consent drives access: revoking a scope removes the lawful basis for that data class.
- Every consent change is audit-logged. *GDPR Art. 7.*

## A — Anonymise (and verify it holds)
- **Pseudonymisation** at processing: real source ids → random `subject_pid`; the real id is stored
  **AES-256-GCM application-layer encrypted** in `id.subject.enc_identity` (key from env, never in
  the DB — ADR-0008). Verified: ciphertext at rest, decrypt round-trip succeeds.
- Analytics expose **aggregates only** (k-anonymity floor `k=3` on grouped queries; `analyse`).
- We explicitly **do not** treat anonymisation as a silver bullet — re-identification is real
  (Daries et al. 2014), so pseudonymisation is layered with access control + aggregation + audit.

## T — Technical safeguards (the core)
Mapped to the **CIA triad** and **AAA model** (Week 5):

| Control | Implementation | Evidence |
|---|---|---|
| Encryption in transit | TLS 1.3 (DB connections, webhook) | _planned: enable TLS on the published endpoint_ |
| Encryption at rest (bulk) | host-volume encryption (LUKS) — community PG has no TDE | `docs/04-security.md`, ADR-0008 |
| Encryption at rest (sensitive) | **AES-256-GCM app-layer** on identity map | `id.subject`, `common/crypto.py` |
| Authentication | webhook **API key + HMAC + nonce + timestamp window**; Argon2id for creds | `api/auth.py` — verified: tamper/replay/stale → 401 |
| Authorisation (RBAC) | roles `aegis_engineer` / `aegis_analyst` / `aegis_subject`, least privilege | migrations 0002/0003 — verified denials |
| Row-level security | subject sees only own rows; analyst = aggregate view only | verified: 0 rows w/o pid; base table denied |
| Accounting (logging) | append-only audit log + triggers; anomaly view | `meta.audit_log`, `meta.v_anomaly` |
| Integrity | parameterised SQL, pydantic validation, content-hash idempotency, FK/PK constraints | `ingest/base.py` |
| Availability / backups | **encrypted 3-2-1** logical backups; restorable | `scripts/backup.sh` — verified 117 MB dump restorable |
| Retention | TimescaleDB retention policy on raw time-series | migration 0003 |
| Erasure (Art. 17) | cascade curated+raw+map, **signed deletion receipt** | `process/erase.py` — verified p16 1.79M → 0 |
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
| Art. 5(1)(b/c/e) | purpose limitation, data minimisation (only needed columns), retention policy |
| Art. 6 / 7 | lawful basis + consent records |
| Art. 15 / 20 | subject read + export |
| Art. 17 | erasure cascade + deletion receipt (incl. raw + map; backups per rotation) |
| Art. 25 | privacy by design/default — pseudonymisation default, RLS, minimisation from ingest |
| Art. 32 | encryption, pseudonymisation, RBAC/RLS, backups, logging |

## ISO/IEC 27001 control ↔ implementation
A.9 access control (RBAC+RLS) · A.10 cryptography (AES/TLS/Argon2) · A.12 operations security
(logging, backups, change control) · A.16 incident management (audit trail + anomaly view) ·
A.18 compliance (GDPR + licence adherence).

## Residual risks (honest)
- TLS termination on the published webhook is _planned_ (local demo uses a tunnel — ADR-0004/0005).
- Backups encrypt with the master key by default; a dedicated backup key is recommended.
- This is a **student project demonstrating** controls, not a certified production ISMS.
