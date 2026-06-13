# ADR-0007 — Defer the frontend; preserve a clean API seam

- **Status:** accepted
- **Date:** 2026-06-13
- **Deciders:** Joyren, Claude

## Context
A dashboard to "view the pipeline working" is desirable, but the priority is documentation,
decisions, and a hardened security-first backend. The user explicitly does **not** want a generic
default AI-generated UI.

## Decision
**Defer the frontend** to a later phase (roadmap Phase 7). Build the backend so the FastAPI ingest
service is also the read API a future dashboard consumes — the frontend becomes additive, not a
rewrite. When we do build UI, use a real frontend-design skill or a crafted master prompt, and
**confirm aesthetic direction with the user first** (no AI slop).

## Consequences
- Positive: scope stays focused; the hard/graded parts (security, compliance, pipeline) land first;
  no throwaway UI.
- Negative: no visual demo until later → mitigated by CLI/notebook demos of the queries + logs.

## Alternatives considered
- **Build UI now** — pulls effort from the security backbone and risks generic output.
- **No frontend ever** — loses the "see it working" value the user wants eventually.
