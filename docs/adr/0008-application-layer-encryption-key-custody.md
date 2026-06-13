# ADR-0008 — Application-layer encryption & key custody

- **Status:** accepted
- **Date:** 2026-06-13
- **Deciders:** Joyren, Claude

## Context
ADR-0006 committed to encryption + pseudonymisation but left **key custody** vague, and review
exposed two honesty problems:
1. **Community PostgreSQL has no built-in TDE** ("transparent data encryption"). Saying "encryption
   at rest" without qualification is misleading.
2. **`pgcrypto` decrypts inside the database** — the key is passed in SQL and can leak into query
   logs / `pg_stat_statements`. For the crown-jewel pseudonymisation map, that's weak.

If the encryption key sits next to the data and is readable by the same role that reads the data,
the encryption is theater. Defense in depth (Week 5) requires the key and the ciphertext to be
separable.

## Decision
Layer encryption by sensitivity, with explicit key custody:

| Data | Mechanism | Key location |
|---|---|---|
| Pseudonymisation map + most-sensitive fields | **Application-layer AES-256-GCM** (encrypt in Python *before* INSERT; DB only ever stores ciphertext) | Master key injected at runtime via **env var / docker secret**; **never** in the DB, **never** committed |
| Bulk data at rest | **Host-volume encryption** (LUKS/dm-crypt on the Docker volume host) | Host-managed |
| In transit | **TLS 1.3** | — |
| Specific in-DB needs only | `pgcrypto` (acknowledged trade-off) | runtime-supplied, scrubbed from logs |

- **Key handling:** loaded once at process start from the environment; held in memory; `.env`
  gitignored; documented **rotation** procedure (re-encrypt map under a new key, version the key id).
- **Honesty in docs:** state plainly that "encryption at rest" = host-volume encryption +
  app-layer field encryption, **not** Postgres TDE.

## Consequences
- Positive: a DB-only compromise yields ciphertext for the most sensitive data; key custody is
  explicit and defensible; matches Art. 32 + ISO 27001 cryptography control honestly.
- Negative: app-layer encryption breaks SQL search/joins on those fields (acceptable — the map is
  looked up by exact pid, and sensitive fields aren't query predicates); key management overhead;
  losing the key loses the data (documented backup-of-key procedure, stored separately).

## Alternatives considered
- **`pgcrypto`-only** — simpler but key transits SQL; rejected for the map.
- **Enterprise Postgres TDE / cloud KMS** — out of scope (local, no cloud); revisit if productised.
