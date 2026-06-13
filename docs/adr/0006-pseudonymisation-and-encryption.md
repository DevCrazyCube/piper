# ADR-0006 — Pseudonymisation + layered encryption strategy

- **Status:** accepted
- **Date:** 2026-06-13
- **Deciders:** Joyren, Claude

## Context
We process special-category health data + institutional grades for real people. Research is clear
that de-identification alone is fragile (re-identification — Daries et al. 2014). GDPR Art. 25/32
require protection by design + encryption/pseudonymisation. Defense in depth (Week 5) demands
layers, not one control.

## Decision
- **Pseudonymise at processing:** replace direct identifiers with a random `subject_pid`. The
  real-identity ⇄ pid **mapping table** is column-encrypted (`pgcrypto`/AES-256-GCM) and readable
  only by a restricted role, excluded from analyst/engineer grants and team-shared backups.
- **Encryption layers:** TLS 1.3 in transit; disk/volume encryption at rest; **AES-256-GCM** for
  sensitive fields; **RSA/ECC** only for signing/key exchange (webhook payload signatures, audit-log
  integrity); **Argon2id** for credentials; **SHA-256** for integrity.
- **Aggregate-only outputs** where individual records aren't needed; **RLS** binds rows to subject + consent.

## Consequences
- Positive: re-identification requires breaching multiple independent layers; satisfies Art. 25/32 +
  ISO 27001 cryptography control; matches the "no single control is enough" thesis.
- Negative: key management overhead; pseudonymisation map is a high-value target → strict access +
  encryption + audit on it. Some analytics need careful view design to avoid identifier leakage.

## Alternatives considered
- **Full anonymisation** — kills cross-source joins + erasure ability, and isn't robust anyway.
- **Encryption only, no pseudonymisation** — a single decryption breach exposes identities; violates
  defense in depth.
