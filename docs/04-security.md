# 04 — Security Design

> This is the backbone deliverable (Joyren's pillar). Every control below maps to a concept
> from the **Week 5 "Data Security & Governance"** lecture, so it grades against the rubric.
> Core thesis from the research: **no single control is enough → defence in depth.**

---

## 1. Guiding principles (Week 5)

- **CIA Triad** — Confidentiality, Integrity, Availability drive every control.
- **Defense in depth** — multiple layers; **no single point of failure**. If one control fails,
  others still protect the data.
- **Least privilege** — every identity gets the minimum access needed.
- **Security is everyone's responsibility** — 95% of breaches involve human error
  (Week 5 / Maastricht example). Process + awareness, not just tech.
- **Proactive, not reactive** — privacy/security designed in from stage 01 (ties to Cavoukian PbD).

## 2. CIA Triad → concrete controls

| Pillar | Technical controls in this pipeline |
|---|---|
> **Post-audit note (2026-06-15):** this is the security *design* doc. For the authoritative
> implemented-vs-planned status see **`docs/security-policy.md`**. Notably: `pgcrypto` was
> **rejected** in favour of app-layer AES (ADR-0008); Argon2id/MFA/`auditor`+`admin` roles and TLS
> are **not implemented** (no human-credential surface exists) — they describe intent, not current state.

| **Confidentiality** | TLS in transit _(planned)_; encryption at rest; **app-layer AES-256-GCM** field encryption; RBAC + Row-Level Security; pseudonymisation; least privilege |
| **Integrity** | Parameterised queries; pydantic validation at ingest; DB constraints + FK; hash/checksum on raw payloads; append-only audit log; 4-eyes on migrations |
| **Availability** | 3-2-1 backups; defined RPO/RTO; health checks; (optional) replication; resource limits to resist resource-exhaustion |

## 3. AAA model (Week 5) → implementation

### Authentication
- Webhook clients authenticate with a **per-device API key/token** (rotatable, scoped), and sign
  each payload with an **HMAC + timestamp + nonce** so replays and tampered bodies are rejected.
- _Planned (not implemented):_ human/admin access with **Argon2id**-hashed credentials + **MFA**.
  There is currently **no human-credential surface** — the only authenticated path is the per-device
  webhook HMAC. Argon2id/MFA apply once an admin/login UI exists.
- Secrets via **`.env` (dev)** → docker secrets (never in code, never committed).
- Principle: **length over complexity**, no reuse, rotation without predictable patterns
  (per the slide).

### Authorization — RBAC + least privilege
Database roles modeled on the Week 5 examples:

| Role | Grants |
|---|---|
| `pipeline_engineer` | write to staging/curated, read curated; **no** read on the pseudonymisation map |
| `analyst` | read-only on curated **views** (aggregates), never raw identifiers |
| `data_subject` | (via API) read/erase **only their own** rows — enforced by **Row-Level Security** |
| `piper_app` | the runtime role — NOSUPERUSER, NOBYPASSRLS (migration 0005) |
| `auditor` / `admin` | _planned_ — not yet created |

**Teachers cannot see raw sleep/HR data by default** (matches the group's privacy stance).
Row-Level Security ties each row to a subject + consent scope so a query physically cannot
return another subject's rows.

### Accounting — logging (→ SIEM-style)
Structured JSON logs (structlog) capture, per Week 5:
- Authentication events (success/failure)
- Data access + modifications
- Configuration changes
- API calls + responses (metadata, not payloads in clear)
- Pipeline run provenance (source, row counts, decisions)

Logs are **append-only**, separated from app data, and feed simple **anomaly detection**
(unusual extraction volumes, off-hours access, geographic anomalies) — the "ML for security
monitoring" idea, kept lightweight.

## 4. Encryption (Week 5: "Encryption Implementation")

| Need | Method | Where |
|---|---|---|
| In transit | **TLS 1.3** | Webhook API, DB connections, internal calls |
| At rest (bulk) | **Host-volume encryption** (LUKS/dm-crypt) | DB data volume on the host |
| At rest (sensitive fields + pseudonymisation map) | **Application-layer AES-256-GCM** (encrypt in Python *before* INSERT) | map, health identifiers — DB stores only ciphertext |
| Key distribution / signing | **RSA / ECC** (asymmetric) | webhook payload signing, audit-log integrity seal |
| Credentials | **Argon2id** (hash, not encrypt) | API keys, admin auth |
| Integrity checks | **SHA-256** | raw payload checksums, log chaining |

> **Honesty note (see ADR-0008):** community PostgreSQL has **no built-in TDE**. So "encryption at
> rest" here means **host-volume encryption + application-layer field encryption**, not a magic DB
> switch. The crown-jewel pseudonymisation map is encrypted **in the application** so the key never
> transits SQL (unlike `pgcrypto`, which decrypts inside the DB and can leak the key into query logs).

- **Symmetric (AES) for bulk** — fast + authenticated (GCM). **Asymmetric (RSA/ECC) only** where
  key exchange or signatures are needed — matches the symmetric-vs-asymmetric slide.
- **Key custody:** master key injected at runtime via **env var / docker secret**, held in memory,
  **never in the DB, never committed** (`.env` gitignored). Documented **rotation** (re-encrypt the
  map under a new key id) and a separately-stored key backup (losing the key loses the data).
- **Post-quantum:** noted as a forward concern (NIST PQC) per the slide; not implemented.

## 5. Backups & resilience (Week 5)

- **3-2-1 strategy:** 3 copies (live + primary + secondary), 2 media types, 1 off-site.
- **RPO/RTO:** define acceptable data loss + downtime; choose backup frequency accordingly
  (document target values with the team — e.g. RPO ≤ 24h, RTO ≤ 4h for a student project).
- **Backups are encrypted** and fall under **deletion obligations** — an erasure request must
  also purge backups (GDPR Art. 17). Snapshots for quick recovery; replication considered for
  availability but noted to **propagate corruption** (per slide) so not a backup substitute.

## 6. Security testing (Week 5: SAST / DAST / pentest)

- **SAST:** `bandit` on our code + `ruff` security rules — code scanning for vulnerabilities.
- **Dependency hygiene:** `pip-audit` for known-vulnerable packages.
- **Container scanning:** `trivy` on the built images (base-image CVEs, misconfig).
- **DAST (light):** test the running webhook API — authn bypass attempts, authorization boundary
  tests, malformed/oversized payloads (incl. zip-bomb / decompression limits), injection attempts.
- **Data-flow pentest mindset:** authentication bypass, data exfiltration, authorization
  boundaries — documented as a checklist even if not a full engagement.

## 7. Per-stage controls (the 8 lifecycle stages)

| Stage | Key security controls |
|---|---|
| 01 Ingest | authn (API key + HMAC/nonce) on webhook; input validation; data minimisation; idempotent loads; raw zone write-once + checksum; failed rows → quarantine |
| 02 Transport | TLS 1.3 everywhere; no clear-text movement |
| 03 Store | encryption at rest; **app-layer AES-256-GCM on the identity map** (not `pgcrypto`); RLS; constraints; least-priv grants |
| 04 Process | pseudonymisation; parameterised SQL; validation; decisions logged (audit + bias doc) |
| 05 Analyse | query curated views only; aggregate outputs; never expose raw identifiers |
| 06 Access | RBAC + least privilege; RLS binds rows to subject + consent; MFA for admin _(planned — not implemented; no human-credential surface yet, see §3)_ |
| 07 Monitor | append-only audit logs; anomaly detection; SAST/DAST in CI |
| 08 Delete | verified erasure incl. backups; deletion receipt; cascade across curated + raw + logs-of-data |

## 8. Threats explicitly addressed (from the research)
- **Re-identification** (Daries et al. 2014): de-identification alone is shaky → pseudonymise
  **+** access control **+** aggregate outputs **+** transparency, together.
- **Insider inference:** RBAC limits who reads what, but insiders can still infer → least
  privilege + audit logging + anomaly detection.
- **Human error (95% of breaches):** secrets management, no shared creds, MFA, awareness notes
  in the security policy.

## 9. What this maps to for grading
This document is the input to the **security policy** deliverable, structured around the
**DELICATE** checklist and cross-referenced with GDPR + ISO/IEC 27001 (see `05-compliance.md`).
