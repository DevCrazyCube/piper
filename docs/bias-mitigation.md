# Bias-Mitigation Decisions — Data Engineering

**Pillar:** Bias & fairness (Daniels) · **Scope:** the *data-engineering* decisions in the Aegis
pipeline that can introduce or reduce bias. We prepare ML-ready data; we don't train models here —
and the research is clear that **most bias originates in data collection and preparation, not the
algorithm** (Idowu et al. 2024; Biswas & Rajan 2021), and that individual preprocessing steps each
add small unfairness that **compounds** across the pipeline.

> Every decision below is also recorded at runtime in **`meta.decision`** (stage, decision,
> rationale, detail) so the choices are auditable, not just narrated. Query: `SELECT * FROM meta.decision`.

---

## Principle
- **No universal fix** — what reduces bias for one group can worsen it for another (Opoku et al. 2025);
  so we *document* each decision and its trade-off rather than apply a blanket "fix".
- **Make decisions explicit** — explainability is the common gap (Alvarez et al. 2024); logging every
  transformation decision is our mitigation for that gap.

## Decisions and their fairness impact

| Stage | Decision | Fairness consideration / trade-off |
|---|---|---|
| **Ingest** | Land everything raw, quarantine only unparseable rows | Avoids early silent dropping that could systematically exclude a subgroup (e.g. one device's odd format). Dropped rows are inspectable in `meta.quarantine`, not lost. |
| **Dedup (UCI mat+por)** | Merge students appearing in both files (1044→662) on 13 identifying attributes; average available G3 | A student in both subjects would otherwise be **double-counted**, over-weighting whoever takes both courses. Averaging avoids privileging one subject. |
| **Harmonise (academics→norm)** | Map exam bands Best/Vg/Good/Pass/Fail → 1.0/0.8/0.6/0.4/0.2 | The band→number mapping is a **value judgment** (equal spacing assumed). Documented explicitly; a different spacing would shift cross-institution comparisons. |
| **Missing values** | Tolerant coercion → NULL (not imputation) for bad/empty fields | We do **not** impute, because imputation can encode majority-group assumptions onto minority rows. NULLs are honest; downstream aggregates exclude them. |
| **Time-series aggregation** | Hourly rollups (HR=mean, cumulative=sum) | Aggregation loses individual granularity — good for privacy, but could mask within-hour variation. Chosen deliberately; raw remains available if finer analysis is justified. |
| **Analytics** | Aggregate-only + k-anonymity (k=3) | Prevents singling out small subgroups; but very small groups are **suppressed**, which can hide signal for minorities — a known fairness/privacy tension, surfaced here not buried. |
| **Cross-population** | No health↔academic joins across datasets (ADR-0009) | Fabricated linkages across unrelated populations would invent relationships and bias conclusions; only the teammate/synthetic cohort supports real cross-source analysis. |

## Known data-source bias (inherited, flagged not "fixed")
- **PMData**: 16 self-selected lifelogging participants — not representative; activity/sleep norms
  skew to that group. Cohort stats are descriptive of *them*, not a population.
- **UCI Student Performance**: two Portuguese secondary schools; **UCI Academics**: a different
  cohort with caste/attendance attributes. Demographics differ → cross-institution comparison
  (Q5) shows *distributional* difference, which must not be read as one group being "better".
- **Collection bias**: which attributes each institution recorded reflects their own priorities
  (attendance band vs numeric absences) — the harmonisation reconciles *format*, not the underlying
  collection differences.

## Three-stage framing (from the literature, mapped to our pipeline)
- **Pre-processing** (where we operate): minimise, document transformations, avoid imputation that
  encodes assumptions, keep raw for re-derivation.
- **In-processing** (model training): out of scope — flagged for whoever trains on `curated.*`.
- **Post-processing** (outputs): aggregate-only + k-anonymity; per-group thresholding would be a
  downstream concern, documented as future work.

## How to audit
`SELECT stage, source, decision, rationale FROM meta.decision ORDER BY id;` reproduces this table
from the live run — the decisions are data, not just prose.
