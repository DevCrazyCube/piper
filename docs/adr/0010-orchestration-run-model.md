# ADR-0010 — Orchestration / run model

- **Status:** accepted
- **Date:** 2026-06-13
- **Deciders:** Joyren, Claude

## Context
The docs described stages but never said *how the pipeline runs*. Options ranged from a heavy
orchestrator (Airflow/Dagster/Prefect) to a simple CLI. We also need idempotent re-runs and a
place for bad records to go.

## Decision
- **Run model:** a **Python CLI** (e.g. `python -m pipeline ingest <source>`, `... process`,
  `... analyse`) with **Make targets** wrapping common flows. The webhook ingest runs as a
  long-lived FastAPI service; batch flows are invoked on demand / by a simple scheduler if needed.
  No heavyweight orchestrator at this scale.
- **Idempotency:** every batch load is idempotent — records carry a **natural key + content hash**;
  re-ingesting the same file/payload upserts, never duplicates. Webhook payloads carry an idempotency
  key (device + event id/timestamp).
- **Dead-letter / quarantine:** rows/payloads that fail validation go to a **quarantine table** with
  the raw value + failure reason, instead of crashing the run or being silently dropped.

## Consequences
- Positive: simple, debuggable, reproducible; matches course scale; safe re-runs; nothing fails silently.
- Negative: no rich DAG scheduling/retry UI (acceptable; can add Prefect later if it grows).

## Alternatives considered
- **Airflow/Dagster/Prefect** — real orchestration but heavy ops for a 3-person project; deferred.
- **Ad-hoc scripts** — not idempotent, not reproducible; rejected.
