# ADR-0002 — Python as the implementation language

- **Status:** accepted
- **Date:** 2026-06-13
- **Deciders:** Joyren, Claude

## Context
We need a language for ingest, cleaning, and analytics over messy multi-format data, runnable by
the whole team and aligned with the course.

## Decision
**Python 3.12.** Process with **pandas**, escalating to **polars** for the ~20M-row PMData
heart-rate data. Validate with **pydantic**.

## Consequences
- Positive: matches Week 6 (pandas ETL); best messy-data + crypto + Postgres ecosystem; teammates know it.
- Negative: raw Python performance on 20M rows needs care → mitigated by polars + pushing
  aggregation into TimescaleDB.

## Alternatives considered
- **SQL-only / dbt** — great for transforms but weak for messy JSON/encoding fixes and the webhook API.
- **Scala/Spark** — overkill for this data size; not taught at this depth; heavier ops.
