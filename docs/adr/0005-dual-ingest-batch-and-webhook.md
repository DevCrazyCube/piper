# ADR-0005 — Dual ingest: batch connectors + authenticated webhook (+ export fallback)

- **Status:** accepted
- **Date:** 2026-06-13
- **Deciders:** Joyren, Claude

## Context
We have four batch datasets **and** real near-real-time data from teammates' Apple Watches. You
cannot stream directly off an Apple Watch — data leaves the phone only via export or an app.

## Decision
Two ingest paths behind a common connector interface:
1. **Batch connectors** — format-aware file readers for the 4 datasets + Apple Health `export.zip`.
2. **Authenticated webhook API** (FastAPI) — an auto-export iOS app POSTs health JSON in near-real-time
   micro-batches. Same endpoint pattern later serves calendar (Google Calendar API) and LMS.
Manual `export.zip` import stays as a **fallback/backfill** path.

## Consequences
- Positive: real live data without building an iOS app; webhook doubles as the **future frontend/API
  seam**; pluggable connectors make new sources cheap.
- Negative: a public-facing endpoint is attack surface → must be authenticated, validated, rate-limited,
  TLS-only, logged from day one (see `04-security.md`). Needs a public URL for live demos (ADR-0004).

## Alternatives considered
- **Batch-only (export zips)** — simplest, but no "real-time from real sources" story you wanted.
- **Custom iOS HealthKit app** — true near-live but a whole second project; out of scope.
