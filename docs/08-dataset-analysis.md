# 08 — Dataset Analysis

> _Draft — AI-assisted scaffold for the Piper project. Every figure here was measured/derived from the repo, but verify against the code and data and put it in your own words before submission._

> Profiling pass over the four real batch datasets in `datasets/` — provenance, grain, schema,
> measured quality, and fitness for responsible learning-analytics. Companion to `03-data-sources.md`
> (the design-time view) and to ADR-0009 (honest linkage). Numbers below are **measured**, not the
> design-doc estimates — where they disagree, this file flags the discrepancy.

---

## 0. How these numbers were obtained

Big files were **never fully loaded** — no OOM risk taken. Tooling: `uv` (Python 3.11 for the
wheel-dependent libraries — pandas / pyarrow / polars / openpyxl / scipy / ijson; system Python 3.14
avoided for those). Secrets (`.env`) were never read; `pgdata` and the live TimescaleDB container
were not touched (these are pre-ingest raw source files — only the matching `src/pipeline/ingest/*`
connector code was cross-read).

| Dataset | Profile method | What was actually read |
|---|---|---|
| Open Food Facts | **SAMPLE + MANIFEST** | Parquet footer metadata (exact row/col/row-group counts) + **only `row_group(0)`** (1 021 rows) for missingness/ranges |
| PMData | **MANIFEST + SAMPLE** | `zipfile.infolist()` (all 912 entries + sizes); streamed first 3 records of one `heart_rate.json` via `ijson`; small CSV/XLSX/sleep files read whole |
| UCI Student Performance | **FULL load** (tiny) | both CSVs via `pandas.read_csv(sep=';')`; full cross-file merge for dedup |
| UCI Student Academics | **FULL load** (tiny) | `scipy.io.arff.loadarff` → pandas; ARFF header parsed directly |

Read sample sizes are stated inline so every distribution can be judged for representativeness — a
single Parquet row-group (1 021 of 4.5 M rows) is a convenience sample, not a stratified one, so its
distributions are **indicative only**.

---

## 1. PMData — Fitbit + wellness + meals (personal-health domain)

- **Source:** `datasets/pmdata.zip` — Simula PMData lifelogging (Fitbit Versa 2 + PMSys + Google
  Forms). **License: CC BY-NC 4.0** (education OK; **non-commercial** — flag for any productisation).
- **Provenance / grain:** per-participant tree `pNN/{fitbit,pmsys,googledocs}/...`. There is **no
  single grain** — it is a bundle of heterogeneous files, which is the whole engineering point:
  - Fitbit intraday JSON (`heart_rate`, `steps`, `calories`, `distance`, …) — grain = one
    timestamped sample; `dateTime` + `value`, where HR `value` is nested `{bpm, confidence}` (the
    connector pulls `bpm`).
  - `sleep.json` — grain = one sleep session; natural key `logId`; fields `dateOfSleep`,
    `minutesAsleep`, `efficiency`, `levels`.
  - `wellness.csv` / `srpe.csv` / `injury.csv` — grain = one self-report; 1–5 ordinal scales
    (fatigue / mood / readiness / stress).
  - `googledocs/reporting.csv` — grain = one daily meal/weight log; free-text `meals`, `weight`,
    `glasses_of_fluid`.
  - `participant id pNN` (p01–p16) is the **source-local** key; pseudonymised in Phase 2
    (`pmdata.py` notes this).

- **Schema / size (measured):** **1.3 GB compressed** (≈1.4 GB per docs), ~2.1 GB+ uncompressed;
  **912 zip entries**; **16 participants p01–p16**. Format = ZIP of mixed JSON + CSV + XLSX + meal
  photos (jpg/png).
  - This is the **volume/velocity** story: `heart_rate.json` totals **≈1 597 MB across 16 files**
    (106–123 MB each; biggest single file = **122.9 MB** `p08/fitbit/heart_rate.json`),
    5-second-cadence intraday → ~20 M+ rows per docs. Must be **streamed** (connector uses
    `ijson('item')`; never `json.load` the big arrays). `calories.json` 182 MB ×16, `distance.json`
    79.9 MB ×16, `steps.json` 78.8 MB ×16, `sleep.json` 8.2 MB ×16.
  - Small-file row counts (p01): `sleep` 155 sessions (15 keys incl. `logId`, `efficiency`,
    `levels`, `mainSleep`); `wellness` 137 rows; `srpe` 33; `sleep_score` 149; meal `reporting` 108.
  - `participant-overview.xlsx` = 30×21 including header rows; e.g. p01 age 48, max HR 182.

- **Measured quality / anomalies:**
  - **At least four distinct timestamp conventions inside one dataset** — HR `dateTime`
    `YYYY-MM-DD HH:MM:SS` (space form); sleep `startTime` space-form but `endTime` ISO-`T` with
    `.000` ms; wellness / srpe / sleep_score use ISO-8601 `Z` (UTC); meal `reporting.csv` uses
    `DD/MM/YYYY` for `date` **and** `MM/DD/YYYY HH:MM:SS` for the timestamp (mixed day/month order →
    genuine parse-ambiguity risk). All timestamp normalisation must be source-aware.
  - **List-valued cells stored as Python-literal strings**: `soreness_area='[12921003]'`,
    `activity_names="['individual','running']"` — need `ast.literal_eval`-style parsing, not naive
    CSV splitting.
  - `participant-overview.xlsx` has **merged header cells** (multi-row header + a stray title row)
    and some null stride cells (p03) → careful header handling required.
  - HR `confidence` field carries quality metadata that should survive into curated data, not be
    dropped silently. Data window **starts 2019-11**.

- **Fitness for responsible learning-analytics:** strong for the **personal-health domain** (Q1
  active-minutes, sleep/wellness patterns) — high temporal density and real self-reports. But it is
  **real personal data under CC BY-NC**: consent, minimisation, and pseudonymisation apply from
  ingest (the connector defers pseudonymisation to Phase 2 — make sure that actually lands before any
  shareable output). It is **not** a source for academic outcomes: PMData subjects have no grades, so
  any "health → grades" link is fabricated (see §6 / ADR-0009).

---

## 2. UCI Student Performance — Portuguese secondary schools (academic domain)

- **Source:** `datasets/student+performance.zip` — UCI dataset 320 (Cortez & Silva 2008), two
  Portuguese secondary schools. **License: open / public domain.**
- **Provenance / grain:** **nested zip** — outer zip → `student.zip` (+ a `.student.zip_old`
  backup) → `student-mat.csv` + `student-por.csv` (inner zip also carries `student-merge.R` and
  `student.txt`). Grain = **one student-enrolment row per subject** (Maths vs Portuguese). Connector
  lands each row raw with a subject tag and `natural_key = subject:line`.

- **Schema / size (measured):** **40 KB** zip (mat 56 KB / por 91 KB uncompressed). **33 columns**,
  **1 044 rows combined** = **mat (395, 33)** + **por (649, 33)**. Format = **semicolon-delimited**
  CSV (33 fields/line) with quoted strings — a comma parse would silently break. Key fields:
  `school` (GP/MS), `sex`, `age`, `Mjob`/`Fjob`, `Pstatus` (T/A), `studytime`, `failures`,
  `absences`, and grades `G1`/`G2`/`G3` (0–20; **G3 = final, the target**).

- **Measured quality / anomalies:**
  - **Zero missing values** in either file (`isna().sum() == 0`).
  - **Cross-file duplicate students** (the dedup challenge): **382 students overlap** on the UCI
    13-attribute merge key (`school, sex, age, address, famsize, Pstatus, Medu, Fedu, Mjob, Fjob,
    reason, nursery, internet`) — the same person appears in both Maths and Portuguese with subtly
    different per-subject values. Also **within-file near-dups** on that 13-key: mat 4, por 12.
  - **`G3 == 0` sentinels**: **38/395 (mat)** and **15/649 (por)** — these almost certainly encode
    dropouts / no-shows, **not** a literal zero grade. Treating them as numeric zeros would bias any
    mean (mat G3 mean 10.42 over 0–20; por 11.91 over 0–19) and any pass/fail model. Decide
    explicitly: drop, flag, or model as a separate class.
  - `school` split: mat {GP 349, MS 46}; por {GP 423, MS 226}. `age` 15–22; `absences` 0–75.
  - **DOC DISCREPANCY (encoding):** `03-data-sources.md` and the `uci_performance.py` docstring
    claim `â€"` mojibake / inconsistent encoding. **Not reproduced** — `file(1)` reports both files
    as **plain ASCII** and a byte-grep finds **no mojibake**. The semicolon-delimiter and cross-file
    duplicate claims **are** real; the encoding claim should be corrected in the docs (and the
    connector docstring) so cleaning effort is not wasted on a non-problem.

- **Fitness for responsible learning-analytics:** clean, well-understood, ideal for the **academic
  domain** (Q3 study-time vs outcomes, Q5 harmonisation). The cross-file overlap makes it a good
  **honest dedup** teaching case. Caveat: it is a different population from PMData — academic-domain
  only.

---

## 3. UCI Student Academics Performance — Indian college cohort (academic domain)

- **Source:** `datasets/student+academics+performance.zip` — UCI Student Academics Performance
  (Indian college cohort). **License: open.** Single `Sapfile1.arff`, read via a custom ARFF reader
  (`src/pipeline/common/arff.py`); connector lands each row raw with `natural_key = sap:line_no`.
- **Provenance / grain:** grain = **one student row**, **all-categorical**. `@DATA` starts at
  line 27; **131 data rows**.

- **Schema / size (measured):** **16 KB** zip (15.8 KB ARFF). **shape (131, 22)** — 22 nominal
  `@ATTRIBUTE` declarations, **no numeric/continuous fields at all**. Format = **ARFF (Weka)**,
  comma-separated. Key fields: `esp` (end-semester performance Best/Vg/Good/Pass/Fail — **target**),
  `ge` (gender), `cst` (caste), `tnp`/`twp`/`iap` (prior-performance bands), `atd` (attendance
  Good/Average/Poor), `arr` (arrears Y/N), `fmi` (family income), `fq`/`mq`, `fo`/`mo`.

- **Measured quality / anomalies:**
  - **No nulls; no full-duplicate rows.**
  - **Target class imbalance + a phantom class:** `esp` = Good 54, Vg 42, Pass 27, **Best 8** — and
    the declared **`Fail` class never appears** in the 131 rows. Any classifier must handle the rare
    `Best` class and not assume `Fail` exists.
  - Other distributions: `ge` M 72 / F 59; `atd` Good 56 / Average 47 / Poor 28; `arr` N 78 / Y 53.
  - **Terse, coded attribute names** (`ge`, `cst`, `tnp`, `esp`, `atd`…) need a code→meaning
    mapping. `fq`/`mq` enumerations **mix tokens** `'10'`/`'12'` (schooling years) with
    `Il`/`Um`/`Degree`/`Pg` — a **non-obvious ordinal scale** that must be encoded deliberately.

- **Fitness for responsible learning-analytics:** usable as a **second academic source**, but note
  it is **completely schema- and scale-incompatible** with Dataset 2 (band labels
  Best/Vg/Good/Pass/Fail and Good/Average/Poor, **not** 0–20 numeric grades). That mismatch is the
  point — it makes Q5 a **real schema-harmonisation** task (ADR-0009). Two responsible-analytics
  cautions: (a) `cst` (caste) is a sensitive attribute — only use it for **bias auditing**, never as
  a predictive feature (see `bias-mitigation.md`); (b) n=131 with an 8-row `Best` class is too small
  for confident per-subgroup claims.

---

## 4. Open Food Facts — nutrition reference (reference zone)

- **Source:** `datasets/food.parquet` — Open Food Facts world export. **License: ODbL.** Reference
  table, **not** per-subject data.
- **Provenance / grain:** grain = **one row per food product**; natural key `code` (barcode) — the
  connector sets `natural_key = code`.

- **Schema / size (measured):** **7.0 GB on disk** (7.1 GB per docs). **rows = 4 531 058**
  (Parquet-metadata-exact), **columns = 111** (54 of them nested `list`/`struct`). Format = Apache
  **Parquet** (columnar), `format_version` 2.6, `created_by parquet-cpp-arrow 18.0.0`,
  **4 434 row groups**. Key fields: `code`, `product_name` (nested `list<struct<lang,text>>` —
  multilingual), `brands`, `categories_tags`, `nutriscore_grade`, `nutriscore_score`,
  `nutrition_data_per`, `nutriments` (nested `list<struct<name,value,'100g',serving,unit,
  prepared_*>>`), `countries_tags`, `created_t` / `last_modified_t` (UNIX epoch).
  - **DOC DISCREPANCY (column count):** docs and the `openfoodfacts.py` comment say **150+
    columns**; the file actually has **111**. Correct the docs.
  - The connector ingests only a **minimised 9-column subset** capped at **50 000 products** (data
    minimisation; the cap is **logged**, no silent truncation).

- **Measured quality / anomalies** (sample = `row_group(0)`, **n = 1 021** — indicative only):
  - **Heavy sparsity** on provenance fields: `generic_name` **~95% empty** (docs' ">90% missing"
    claim — **confirmed**); `origins_tags` **~82% null** in sample; `brands` 6.4% null;
    `product_name` only 1.4% empty.
  - **Inconsistent Nutri-Score:** `nutriscore_grade` carries **non-grade sentinels** `'unknown'`
    (~24% of sample) and `'not-applicable'` alongside `a`–`e`. Sample dist: e 493, unknown 245,
    d 104, c 99, a 44, not-applicable 20, b 16. Must filter/recode sentinels before any grade math.
  - `nutriscore_score` **26% null**, range **−10..52** — **negative by design** (do not clip).
  - **Unit-basis ambiguity:** `nutrition_data_per` mixes `'100g'` (445), `'serving'` (419), and
    `null` (157 = **15.4%**) — nutrient math is wrong unless normalised to a common basis;
    15% have **no stated basis at all**.
  - **Mixed-language entries:** `product_name`/`generic_name` are language-tagged structs
    (`lang='main'/'fr'/'de'…`) → flattening + language selection needed before matching.
  - **Multiple date conventions** present: `created_t`/`last_modified_t` are **UNIX-epoch ints**
    here (sample spans 1340913181..1643133122 = **years 2012–2022**); docs note ISO strings appear
    elsewhere in the wider OFF data.

- **Fitness for responsible learning-analytics:** good as a **read-only nutrition reference** to
  enrich PMData meal logs — but **best-effort, not guaranteed**: there is **no shared key** with the
  free-text PMData `meals`, so enrichment is **fuzzy string matching with a confidence threshold,
  not a JOIN** (ADR-0009; §6). Data-minimisation and the 50 k cap keep the 7 GB file tractable and
  privacy-clean (no personal data here, so the responsibility concern is **provenance/accuracy of
  the enrichment**, not consent).

---

## 5. Schema & quality summary

| Dataset | Format | Rows (measured) | Cols | Nulls | Standout quality risk |
|---|---|---:|---:|---|---|
| PMData | ZIP of JSON/CSV/XLSX | 16 participants / 912 entries / ~20 M+ HR rows | n/a (heterogeneous) | varies per file | ≥4 timestamp conventions; list-as-string cells; 1.6 GB streamed HR |
| UCI Performance | CSV (semicolon), nested zip | 1 044 (395 + 649) | 33 | **0** | cross-file dup (382); `G3==0` sentinels (38/15) |
| UCI Academics | ARFF (Weka) | 131 | 22 | **0** | all-categorical; `Best`=8; phantom `Fail` class |
| Open Food Facts | Parquet (columnar) | **4 531 058** | **111** (54 nested) | high on ref fields | Nutri-Score sentinels; 100g-vs-serving basis; mixed language |

**Doc-vs-reality discrepancies to fix in `03-data-sources.md` (and connector docstrings):**
1. `food.parquet` is **111 columns, not "150+"**.
2. UCI Performance CSVs are **plain ASCII — no `â€"` mojibake** (semicolon + cross-file-dup claims
   are correct).
3. `Sapfile1.arff` declares an `esp` **`Fail` class that never appears** in the 131 rows.

---

## 6. Cross-source linkage (per ADR-0009)

These four datasets describe **different populations**, so most cross-dataset joins are **invalid**
— joining health to grades across them would fabricate relationships. ADR-0009 splits work into
domains; linkage is only honest **within** a domain (or on the teammate cohort / a clearly-labeled
synthetic cohort).

| Link | Mechanism | Honest? |
|---|---|---|
| UCI Performance ⨝ UCI Academics | **schema harmonisation** to a common academic schema (band scales ↔ 0–20 numeric reconciled, provenance kept) — Q5 | within academic domain ✓ |
| PMData meals ⨝ Open Food Facts | **fuzzy string match** on free-text meal name → product, with a confidence threshold (no shared key) — Q4, best-effort enrichment | reference enrichment ✓ |
| PMData ⨝ UCI (health ↔ grades) | — | **no** — different people; fabricates a relationship |
| Within UCI Performance (mat ↔ por) | **dedup/merge** on the UCI 13-key (382 overlapping students) | ✓ |

The only **genuine** cross-domain (health ↔ academic) join is on the **teammate cohort** who really
supply both wearable and study data; the alternative is an **explicitly-labeled synthetic** linkage
flagged everywhere as fictional. See ADR-0009 for the full rule.

---

## 7. Data-quality recommendations

- **Timestamp normalisation (PMData):** make it **source-aware** — handle the space-form, ISO-`Z`,
  ISO-`T`-with-ms, and the `DD/MM/YYYY` vs `MM/DD/YYYY` meal-log forms explicitly; assert a parsed
  timezone rather than guessing. Add fixtures for each form (cross-ref `10-test-report.md`).
- **Sentinels are not values:** treat OFF `nutriscore_grade` `unknown`/`not-applicable`, OFF
  `nutriscore_score` nulls, and UCI Performance **`G3 == 0`** as explicit missing/other — never feed
  them into means or models as real numbers. The 53 `G3==0` rows in particular need a documented
  decision (drop / flag / separate class).
- **Unit-basis before nutrient math (OFF):** normalise everything to a single basis using
  `nutrition_data_per`; quarantine the **15% with no stated basis** rather than assuming `100g`.
- **Dedup with provenance (UCI):** merge the **382** cross-file students on the UCI 13-key, keep
  both subject grades, and retain `source`/`natural_key` for audit (the connector already lands
  provenance — preserve it through curation).
- **Encode, don't drop, ordinals (UCI Academics):** build an explicit code→meaning map for the terse
  ARFF attributes and a deliberate ordinal for the mixed `fq`/`mq` tokens (`10`/`12`/`Il`/`Um`/
  `Degree`/`Pg`).
- **Sensitive attributes:** `cst` (caste) and the demographic fields are for **bias auditing only**,
  not prediction (see `bias-mitigation.md`); PMData stays pseudonymised from ingest.
- **Validate the cap & confidence threshold:** log/assert the OFF 50 k cap and the fuzzy-match
  confidence threshold so enrichment coverage is **measured, not assumed**.
- **Fix the docs:** apply the three discrepancies in §5 so the cleaning plan targets the **real**
  problems.

---

## Related docs

- `03-data-sources.md` — design-time source overview (the estimates this file measures against).
- `adr/0009-analytical-domains-and-linkage.md` — domains + honest linkage rules.
- `06-data-model.md` — zones (raw / curated / reference) these datasets land in.
- `bias-mitigation.md` — handling of sensitive attributes (caste, demographics).
- `09-database-comparison.md` — storage/engine choices for the time-series vs reference vs curated
  data profiled here (companion doc — pending).
- `10-test-report.md` — fixtures/tests that pin the quality issues above (timestamp forms,
  delimiter, sentinels, dedup) (companion doc — pending).
- Connectors: `src/pipeline/ingest/{pmdata,uci_performance,uci_academics,openfoodfacts}.py`,
  `src/pipeline/common/arff.py`.
</content>
</invoke>
