# ADR-0003 — Consolidated PostgreSQL + TimescaleDB (not polyglot)

- **Status:** accepted
- **Date:** 2026-06-13
- **Deciders:** Joyren, Claude

## Context
Data spans time-series (HR/sleep/steps, ~20M rows), relational (grades, students), free-form
(wellness/meal notes), and a large nutrition reference (Open Food Facts). The group pptx proposed
a polyglot stack (Postgres + TimescaleDB + MongoDB + InfluxDB). The project is **security-first**.

## Decision
Use a **single PostgreSQL 16 engine with the TimescaleDB extension**:
- Time-series → **hypertables** + continuous aggregates
- Relational → standard tables/joins
- Free-form → **JSONB** columns
- Nutrition → read-only **reference table**

## Consequences
- Positive: **one** surface to encrypt, patch, back up, and apply RBAC/RLS/`pgcrypto` to — the
  core security-first argument. Real engineering (Timescale handles the volume/velocity story).
  Joins across personal + institutional data without cross-DB glue.
- Negative: less "tech breadth" to show than 4 databases; very high write throughput would
  eventually favor a dedicated TSDB (not our scale).

## Alternatives considered
- **Add MongoDB** for free-form docs — JSONB covers it; not worth the extra attack surface.
- **Full polyglot** (the pptx) — 3–4× the security/ops burden for no benefit at our scale.
  Documented as "considered & rejected"; Influx/Mongo noted as scale-out options.
