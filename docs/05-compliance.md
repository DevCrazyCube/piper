# 05 — Compliance & Regulation Mapping

> The project "must follow regulations and laws." This maps each obligation to a concrete
> control in the pipeline, so compliance is demonstrable, not asserted.
> Frameworks named in the course (Week 5) + group research: **GDPR, EU Data Act, ISO/IEC 27001,
> DELICATE, Cavoukian's PbD**.

---

## 1. GDPR — Regulation (EU) 2016/679

| Article | Requirement | How the pipeline satisfies it |
|---|---|---|
| **Art. 5(1)(b)** Purpose limitation | Data used only for stated purpose | Each source documents its analytics purpose; access scoped to purpose |
| **Art. 5(1)(c)** Data minimisation | Collect only what's necessary | Open Food Facts loads only 9 of 150+ columns; **other minimisation is applied at curation** (the raw zone intentionally retains full payloads for provenance + erasure) |
| **Art. 5(1)(e)** Storage limitation | Defined retention | Retention windows per data class; backups included; auto-expiry plan |
| **Art. 6** Lawful basis | Consent / legitimate interest | Consent recorded per subject + scope; institutional joins only under consent |
| **Art. 15–20** Data subject rights | Access, portability | `export` command → JSON (Art. 15/20); RLS-scoped subject read |
| **Art. 17** Right to erasure | Delete | `erase`: cascade curated+raw+map+device+quarantine + keyed receipt. **Existing backups are NOT retroactively purged** — they age out under retention/rotation |
| **Art. 25** Data protection by design & default | Privacy built in | pseudonymisation default; FORCE RLS; minimisation at curation |
| **Art. 32** Security of processing | Encryption, pseudonymisation, resilience | app-layer AES-256-GCM (HKDF-separated keys), RBAC/RLS, backups, logging; **TLS _planned_** (see `04-security.md`) |

**Special-category data note:** health/wellness data (HR, sleep, meals) is Art. 9 special
category → stricter handling: explicit consent, minimisation, strong encryption, tight access.

## 2. ISO/IEC 27001 (ISMS)

| ISO theme | Pipeline evidence |
|---|---|
| Risk-based approach | Threat list + per-stage controls; documented residual risks |
| Access control | RBAC + least privilege + RLS + MFA for admin |
| Cryptography | Encryption at rest + in transit; key management plan |
| Operations security | Logging, monitoring, backups, change control (4-eyes on migrations) |
| Incident management | Anomaly detection + audit trail enabling forensics |
| Continuous improvement | SAST/DAST in CI; documented review cadence |

## 3. EU Data Act
- **Data portability** — subjects can export their own data (structured JSON/CSV).
- **Fair access to IoT data** — wearable data is the subject's; ownership stays with them
  (aligns with the "student-centred, data ownership stays with the individual" project framing).

## 4. DELICATE checklist (Drachsler & Greller 2016)
The security policy will be structured around DELICATE so policy + technical design co-evolve:

| Letter | Meaning | Pipeline anchor |
|---|---|---|
| **D** Determination | Defined purpose | Purpose per source (Art. 5) |
| **E** Explain | Be open about what/why | Transparency notes; privacy info |
| **L** Legitimate | Lawful basis | Consent / legitimate interest (Art. 6) |
| **I** Involve | Involve the subject | Consent flow; subject access |
| **C** Consent | Obtain + manage consent | Consent records + scopes; RLS enforces |
| **A** Anonymise | And verify it holds | Pseudonymisation + aggregate outputs; acknowledge re-identification risk |
| **T** Technical | Technical safeguards | All of `04-security.md` |
| **E** External | Partner governance | Dataset licenses respected; no data leaves the box |

## 5. Cavoukian's 7 PbD principles (Angelina's pillar — kept compatible)
Proactive · privacy-as-default · embedded-in-design · full functionality · end-to-end security ·
visibility/transparency · respect for user privacy — all reflected in the per-stage controls and
the "designed-in from stage 01" approach.

## 6. Dataset licensing compliance
| Dataset | License | Obligation honored |
|---|---|---|
| PMData | CC BY-NC 4.0 | Education/non-commercial use; attribution. **⚠️ Non-commercial: if this ever feeds the Comenius project output or a productised/SaaS version, PMData cannot be used there — swap for a commercially-licensed or synthetic source.** |
| UCI Student Performance | Open / public domain | — |
| Open Food Facts | ODbL | Attribution + share-alike for derived DB if redistributed |
| UCI Student Academics | Open | — |

No dataset is redistributed; all stay local + gitignored.

## 7. Gaps / honest caveats
- This is a **student project**, not a certified system — we *demonstrate* compliance controls,
  we don't claim formal certification.
- Real teammate wearable data raises real GDPR duties → consent must be genuine and documented
  before any live ingest.
- Anonymisation is **not** treated as a silver bullet (re-identification risk acknowledged).
