# Documentation

Read in order for the full picture; each doc is self-contained.

1. [`00-scope.md`](00-scope.md) — what we're building and why; locked decisions
2. [`01-architecture.md`](01-architecture.md) — 8-stage pipeline, components, data flow, repo layout
3. [`02-tech-stack.md`](02-tech-stack.md) — every technology choice + justification + rejected options
4. [`03-data-sources.md`](03-data-sources.md) — the 4 datasets + the Apple Watch real-time feed
5. [`04-security.md`](04-security.md) — security design mapped to the Week 5 lecture (the backbone)
6. [`05-compliance.md`](05-compliance.md) — GDPR / ISO 27001 / EU Data Act / DELICATE mapping
7. [`06-data-model.md`](06-data-model.md) — database schema / data model
8. [`07-roadmap.md`](07-roadmap.md) — phased build plan
9. [`08-dataset-analysis.md`](08-dataset-analysis.md) — per-dataset analysis (shape, messiness, curation outcomes)
10. [`09-database-comparison.md`](09-database-comparison.md) — storage-engine comparison + rationale for PostgreSQL + TimescaleDB
11. [`10-test-report.md`](10-test-report.md) — test suite results + coverage report
12. [`security-policy.md`](security-policy.md) — **deliverable**: DELICATE-structured data security policy (GDPR + ISO 27001)
13. [`bias-mitigation.md`](bias-mitigation.md) — **deliverable**: documented data-engineering bias decisions
14. [`audit-findings.md`](audit-findings.md) — internal audit (2026-06-15) + remediation status
15. [`frontend-master-prompt.md`](frontend-master-prompt.md) — design brief to paste into Claude design (frontend, deferred)

### Decision records
[`adr/`](adr/) — numbered Architecture Decision Records (0001–0010). Start at
[`adr/0001`](adr/0001-record-architecture-decisions.md). Add one for any significant decision
using [`adr/0000-template.md`](adr/0000-template.md). Recent: 0008 (key custody), 0009 (analytical
domains & honest linkage), 0010 (run model / idempotency / dead-letter).

### Grounding
Everything here traces to: the PR10 course slides (esp. Week 5 security), the four datasets in
`datasets/`, the group pillar write-ups in `assignments/`, or an explicit decision recorded in an
ADR. No invented requirements.
