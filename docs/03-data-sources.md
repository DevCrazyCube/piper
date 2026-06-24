# 03 — Data Sources

> Four batch test datasets (in `datasets/`, gitignored) + near-real-time wearable feed.
> The "messiness" of each is the point — it justifies the cleaning/normalization engineering.

---

## Batch datasets

### Dataset 1 — PMData (Fitbit + Wellness + Meals)
- **Source:** datasets.simula.no/pmdata · **License:** CC BY-**NC** 4.0 (education OK; **non-commercial** — see caveat below)
- **Local file:** `datasets/pmdata.zip` (~1.4 GB)
- **What:** Lifelogging from 16 people over 5 months — Fitbit Versa 2, PMSys sports app,
  Google Forms wellness/meals.
- **Role:** Personal health — steps, sleep, heart rate, stress, meals.
- **Messiness (engineering value):** many files/formats; **~20M+ raw heart-rate rows**;
  sleep scores; self-reported wellness CSVs; daily meal/weight Google Forms — different
  structures, granularities, conventions.
- **Formats:** JSON (heart rate, sleep) + CSV (wellness, activity).
- **Pipeline handling:** time-series → TimescaleDB hypertables (polars for the big HR file);
  wellness/meals → JSONB. This is the **volume/velocity** story (Week 4).

### Dataset 2 — UCI Student Performance
- **Source:** archive.ics.uci.edu/dataset/320 · **License:** open / public domain
- **Local file:** `datasets/student+performance.zip` (~40 KB)
- **What:** Achievement at two Portuguese secondary schools — grades, demographics, social/school
  factors. Two files: Mathematics + Portuguese.
- **Role:** Institutional/academic — grades, study time, absences.
- **Messiness:** **semicolon-delimited** (not comma); inconsistent encoding (`â€"` artifacts);
  **duplicate students across the two files** with subtly different values (dedup challenge);
  mixed coded fields (`GP`/`MS`, `F`/`M`, `T`/`A`) alongside numeric grades + ordinal scales
  (type-handling).
- **Formats:** CSV (semicolon), two files to merge.
- **Pipeline handling:** delimiter + encoding fix → type coercion → cross-file dedup/merge.

### Dataset 3 — Open Food Facts
- **Source:** world.openfoodfacts.org/data (or Kaggle) · **License:** ODbL
- **Local file:** `datasets/food.parquet` (~7.1 GB) — already converted to Parquet
- **What:** 150+ columns — product names, brands, ingredients, macronutrients, vitamins,
  eco-scores.
- **Role:** Nutritional reference — **enriches PMData's meal logs** with caloric/nutritional values.
- **⚠️ No shared key:** PMData meals are free-text Google-Forms entries; Open Food Facts is product
  records. Linking them is a **fuzzy string-matching** problem (with a confidence threshold), not a
  JOIN — scope it as *best-effort enrichment*, not guaranteed coverage.
- **Messiness:** very wide source (150+ columns) with many fields >90% missing; inconsistent
  Nutri-Score; mixed-language entries; nutrition is a **nested `nutriments` struct** (a
  `List(Struct{name, value, '100g', unit, ...})`), not flat per-100g columns, so it must be flattened
  downstream rather than read directly.
- **Formats:** the upstream dump is TSV; **we ingest the converted `food.parquet`** (efficient,
  columnar — good for the 7 GB size). The connector (`src/pipeline/ingest/openfoodfacts.py`) scans
  the parquet and selects only ~9 columns.
- **Pipeline handling:** load a curated **subset of ~9 columns** (data minimisation!), flatten
  `nutriments` to per-100g values in curation (`curated.food_reference`), key by product for meal-log
  joins. Read-only **reference table**, not per-subject. *(No date parsing: the connector selects no
  date column, so the "three date formats" normalisation is not part of the OFF path.)*

### Dataset 4 — UCI Student Academics Performance
- **Source:** archive.ics.uci.edu/ml/datasets/Student+Academics+Performance · **License:** open
- **Local file:** `datasets/student+academics+performance.zip` (~16 KB)
- **What:** Predicts end-semester percentage from social/economic/academic attributes.
- **Role:** Second institutional source — study habits, attendance, background factors.
- **Messiness:** **different column naming + scales** from Dataset 2 → real **schema
  harmonisation** challenge.
- **Formats:** CSV (different schema from Dataset 2).
- **Pipeline handling:** map to a common institutional schema; reconcile scales; keep provenance.

## Near-real-time source — teammates' Apple Watch

**Reality check:** you cannot stream directly off an Apple Watch. The watch syncs to the
iPhone Health app; data leaves the phone only via export or an app. Our approach:

- **Primary (live-ish):** an **auto-export iOS app** (e.g. "Health Auto Export") POSTs health
  JSON to our **authenticated webhook ingest API** on a schedule (minutes/hourly) →
  near-real-time micro-batches. No app development needed.
- **Fallback (batch):** manual **Apple Health `export.zip`** (XML) import for backfill or for
  teammates who don't run the app.
- **Same webhook pattern** later serves **calendar** (Google Calendar API, read-only OAuth) and
  **LMS** (Moodle/Canvas export or API).

**Privacy note:** this is *real* personal data from real people → consent + minimisation +
pseudonymisation apply from ingest. Only collect the metrics the analytics actually need.

## ⚠️ Critical: these are different *people* (see ADR-0009)

The datasets describe **different populations** — PMData's 16 subjects, the UCI Portuguese
students, the UCI academics cohort, and our 2 teammates are not the same individuals. You therefore
**cannot honestly JOIN health data to grades across datasets** — that fabricates relationships that
don't exist. We split work into three **domains** and only do true cross-source joins where the same
person really has both kinds of data:

| Domain | Sources | Cross-source join valid? |
|---|---|---|
| Personal health | PMData + live wearable | within-domain only |
| Academic | UCI Student Performance + UCI Academics (harmonised) | within-domain only |
| **Teammate cohort** | live wearable + teammates' own study logs + grades | **yes — genuine** |
| Synthetic (labeled) | generated linked cohort | demo only, flagged as fictional |

## How sources combine (the 5 queries, preview)

| Query | Domain | Sources |
|---|---|---|
| Q1 Avg & range of daily active minutes | Health | PMData activity (+ live wearable), exclude scheduled rest |
| Q2 Schedule vs wellness | Health (+ teammate calendar) | calendar ⨝ PMData sleep/steps/nutrition |
| Q3 Study time vs academic outcomes | Academic / teammate | study logs ⨝ grades — **teammate cohort** or labeled synthetic |
| Q4 Meal nutrition vs wellness | Health | PMData meals **fuzzy-matched** to Open Food Facts ⨝ wellness |
| Q5 Cross-institutional harmonised view | Academic | UCI Dataset 2 ⨝ Dataset 4 (harmonised, deduped) |

Q4/Q5 are my recommended picks given the population constraint (both stay *within* a domain, so
they're honest); confirm with the group.

## Handling rules (all sources)
- **Raw zone is write-once + access-restricted**; never analyse raw identifiers.
- **Data minimisation at ingest** — load only needed columns/metrics (esp. Open Food Facts).
- **Provenance** — every curated record keeps source + ingest timestamp for audit + erasure.
- **No dataset leaves the machine**; `datasets/` is gitignored and multi-GB.
