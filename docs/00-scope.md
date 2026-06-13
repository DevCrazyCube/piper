# 00 — Project Scope

**Project:** Responsible Learning Analytics Pipeline
**Course:** PR10 — Introduction to Data Engineering (Zuyd, Applied Data Science & AI), Block 4
**Context:** Comenius applied-research project on personalised education through Learning Analytics
**Status:** Scope locked 2026-06-13

---

## 1. Problem statement

Learning Analytics combines highly sensitive personal data (sleep, heart rate, meals,
calendar) with institutional data (grades, attendance). This data is special-category /
high-risk under GDPR. The project builds a **data engineering pipeline** that ingests
raw, messy multi-source data, **cleans → filters → normalizes → secures** it, and lands it
in a database from which a small set of analytics queries can run — with **security,
privacy-by-design, and fairness built in from the first stage**, not bolted on.

This repository implements **Joyren's pillar (Security)** as the backbone, while remaining
compatible with the group's other pillars (GDPR/legal, Privacy by Design, Bias/fairness).

## 2. Objectives (what "done" means)

1. A **real, running pipeline** (not a toy) that ingests the four test datasets and a
   near-real-time wearable feed, and lands curated data in a hardened database.
2. **Security-first**: every one of the 8 lifecycle stages has explicit controls drawn from
   the Week 5 "Data Security & Governance" lecture (CIA, AAA, defense-in-depth, encryption).
3. **Five cross-source analytics queries** runnable against the curated data.
4. A **security policy** mapped to GDPR + ISO/IEC 27001 (+ EU Data Act, DELICATE).
5. **Documented bias-mitigation decisions** at each preprocessing step.
6. Reproducible via **`docker compose up`** for the whole team.

## 3. In scope

- Dual ingest: **batch** (4 datasets, Apple Health export zip) + **near-real-time webhook**
  (auto-export iOS app POSTing health JSON; same pattern for calendar + LMS).
- Cleaning / filtering / normalization / deduplication / schema harmonisation.
- Pseudonymisation, encryption at rest + in transit, RBAC + row-level security, audit logging.
- Consolidated **PostgreSQL + TimescaleDB** storage.
- The 5 analytics queries + a way to run them (CLI / notebook).
- Compliance + security + bias documentation.

## 4. Out of scope (for now)

- **Frontend / dashboard** — deferred to a later phase, to be designed deliberately
  (no default AI-generated UI). Architecture leaves a clean seam (an API layer) for it.
- Production cloud deployment (local Docker Compose only).
- Building a custom iOS HealthKit app (we use an existing auto-export app + webhook).
- Real ML model training/serving (the pipeline *prepares* ML-ready data per Week 6; modeling
  is a downstream concern). Bias work focuses on the *data engineering* decisions.

## 5. Locked decisions (see `adr/` for rationale)

| Area | Decision |
|---|---|
| Language | **Python** (course is Python/pandas-centric; Week 6) |
| Storage | **PostgreSQL + TimescaleDB**, consolidated single engine |
| Ingest | **Dual**: batch file connectors + authenticated webhook + export-zip fallback |
| Runtime | **Docker Compose**, local |
| Frontend | **Deferred** (clean API seam preserved) |

## 6. Constraints & principles

- **No hallucinated requirements** — everything traces to the course slides, the datasets,
  or an explicit user decision recorded here / in an ADR.
- Real personal data (teammates' wearables) is involved → GDPR obligations are real, not
  academic. Minimise, pseudonymise, consent, secure.
- Security-first ⇒ prefer **fewer moving parts** (smaller attack surface) over breadth-for-show.
- The group's existing AI-generated pptx is a **rough sketch**, not authority.

## 7. Source materials this scope is grounded in

- PR10 weekly slides: Week 2 (Docker, SQL/NoSQL), Week 4 (distributed systems, CAP),
  **Week 5 (Data Security & Governance — the security rubric)**, Week 6 (Python/pandas ETL for ML).
- The four datasets in `datasets/` (see `03-data-sources.md`).
- Group pillar write-ups (security, PbD, GDPR, bias) in `assignments/`.
