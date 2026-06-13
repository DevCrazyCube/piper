# ADR-0009 — Analytical domains & honest dataset linkage

- **Status:** accepted
- **Date:** 2026-06-13
- **Deciders:** Joyren, Claude

## Context
Review exposed a correctness problem: the test datasets describe **different populations**.
PMData = 16 lifelogging subjects; UCI Student Performance = Portuguese secondary students; UCI
Academics = another cohort; the live wearable feed = our 2 teammates. A query like "study time
vs grades" requires the **same individual** to have both wearable and academic data — which only
the teammates do. Joining health to grades *across* these datasets would fabricate relationships
that don't exist.

## Decision
Three explicit data domains, with honest linkage rules:

1. **Personal-health domain** — PMData + live wearable. Health analytics (Q1, wellness patterns).
2. **Academic domain** — UCI datasets 2 + 4 (harmonised). Academic analytics (study time vs grades).
3. **Cross-source (true)** — only on the **teammate cohort**, who genuinely supply wearable +
   their own study logs + grades. Small but real.

For demo scale, an **explicitly-labeled synthetic linkage** may generate a fictional cohort that
links health + academic records — but it MUST be flagged in UI/output/docs as *synthetic, for
demonstration only*, never presented as a finding.

The 5 queries are assigned to domains accordingly (see `03-data-sources.md`); cross-domain queries
run on the teammate cohort or the labeled synthetic cohort, never on silently-joined strangers.

## Consequences
- Positive: analytical integrity; we can still demonstrate cross-source capability honestly; teaches
  a real data-engineering lesson (provenance + linkage ≠ a JOIN you can fake).
- Negative: the "wow" cross-source joins are limited to a small real cohort unless we use the
  clearly-labeled synthetic data; Q4/Q5 must be chosen within these constraints.

## Alternatives considered
- **Silently join across datasets** — fabricates relationships; rejected (dishonest, bad analytics).
- **Health-only or academic-only** — loses the cross-source story the project is about.
