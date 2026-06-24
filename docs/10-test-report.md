> _Draft — AI-assisted scaffold for the Piper project. Every figure here was measured/derived from the repo, but verify against the code and data and put it in your own words before submission._

# Test Report — Piper

This report records the result of one concrete test run of Piper's automated suite, what each
test area actually validates, where coverage is thin, and what could not be exercised in this
environment. It complements [`TESTING.md`](TESTING.md) (the how-to-run-and-demo guide) rather than
repeating it: `TESTING.md` tells a teammate how to stand the system up and prove the features by
hand; this document is the evidence from running `pytest`.

A note on language throughout: "passed in this run" means the assertion held once, on this machine,
on this commit. It is **not** the same as "proven correct". A green suite is a floor, not a
guarantee — see [Coverage gaps](#coverage-gaps-honest) and [What "passed" does and does not
prove](#what-passed-does-and-does-not-prove).

## How the tests were run

| Item | Value |
|---|---|
| Command | `python -m pytest tests -q --tb=short --cov=pipeline --cov-report=term-missing` |
| Test runner | `pytest` (project `[dev]` extra) + `pytest-cov` (see note) |
| Python | CPython **3.12.12** (uv-managed) |
| Install | clean venv **outside** the repo, `pip install -e ".[dev]"` |
| Database | **not used** — no test touches Postgres |
| Source/tests modified | none |

The exact sequence:

```bash
uv venv --python 3.12 /tmp/piper-venv
uv pip install --python /tmp/piper-venv -e "/home/anont/DataPipeline[dev]"
uv pip install --python /tmp/piper-venv pytest-cov   # NOT a project dep — see note
/tmp/piper-venv/bin/python -m pytest /home/anont/DataPipeline/tests \
    -q --tb=short --cov=pipeline --cov-report=term-missing
```

**Why not `make test`?** The canonical target in the Makefile is `docker compose exec app pytest -q`,
i.e. it runs the suite *inside the `app` container*. In this environment only the `db` container
(`datapipeline-db-1`) is up; the `app`/`api` containers are not running, so the in-container path
could not be exercised. The suite was therefore run locally in a throwaway 3.12 venv instead. This
matters: the numbers below come from the *local* path, not the canonical Docker path, so they should
be reproduced with `make test` before being quoted as the official result.

**Why Python 3.12 and not the suggested 3.11?** `pyproject.toml` declares `requires-python >= 3.12`,
so the resolver refused to install the project on 3.11. (The host's system `python3` is 3.14.5, too
new for some binary wheels.) The uv-managed CPython 3.12.12 satisfied the constraint and every
binary wheel — polars 1.41.2, pandas 2.x, pyarrow 24.0.0, psycopg-binary 3.3.4, cryptography —
installed cleanly.

**Why `pytest-cov` was added separately.** `pytest-cov` is **not** in the project's `[dev]` extras.
It was installed only into the throwaway venv to *measure* coverage; nothing in the repo was changed.
If you want coverage in CI, add it to the `[dev]` extra deliberately rather than relying on this
ad-hoc install.

## Summary

| Metric | Result |
|---|---|
| Total tests | **37** |
| Passed | **37** |
| Failed | 0 |
| Skipped | 0 |
| Errors | 0 |
| Line coverage (`pipeline`) | **~29%** (1196 stmts, 849 missed) |
| Wall time | ~4 s |

Raw tail of the run:

```
.....................................                                    [100%]
================================ tests coverage ================================
TOTAL                                      1196    849    29%
37 passed in 3.95s
```

All 37 tests passed and nothing was skipped. The "0 skipped" is itself a small result worth noting:
`test_crypto.py` and `test_connectors.py` are written to *skip* themselves when their heavy
dependencies (`cryptography`, `ijson`/`psycopg`) are missing, so a green-but-empty run can look the
same as a real one. Because the `[dev]` install brought those deps in, the skip-guards did **not**
trigger and the crypto/connector tests genuinely ran. (The crypto key-separation tests additionally
need `PIPER_MASTER_KEY` to be set at import time — when it is unset, those three tests fail with a
`ConfigError` rather than skipping. In this run the project's environment supplied the key, so they
ran and passed. Treat that as a precondition, not a given.)

## Per-area breakdown

| Test file | Area | Passed | Failed | Skipped | Module(s) under test |
|---|---|---:|---:|---:|---|
| `test_crypto.py` | App-layer crypto | 11 | 0 | 0 | `pipeline.common.crypto` |
| `test_dates.py` | Timestamp normalisation | 10 | 0 | 0 | `pipeline.common.dates` |
| `test_arff.py` | ARFF reader | 7 | 0 | 0 | `pipeline.common.arff` |
| `test_auth.py` | Webhook HMAC auth | 5 | 0 | 0 | `pipeline.api.auth` |
| `test_connectors.py` | Connector parsing | 4 | 0 | 0 | `pipeline.ingest.pmdata`, `pipeline.ingest.uci_performance` |
| **Total** | | **37** | **0** | **0** | |

### Crypto — `test_crypto.py` (11)
Exercises the encryption primitives the privacy story rests on:
- **AES-256-GCM roundtrip** for both bytes and strings (encrypt→decrypt yields the original).
- **Nonce freshness** — encrypting the same plaintext twice yields different ciphertext (random
  nonce per call), so identical pseudonyms don't leak by ciphertext equality.
- **Authentication / tamper resistance** — decrypting with the wrong key raises `InvalidTag`; a key
  of the wrong length is rejected up-front with `ConfigError`.
- **Key separation (ADR-0008)** — a cipher derived for the `identity` purpose cannot decrypt a
  `device`-purpose token, and an AAD mismatch fails. This is what stops one subsystem's key from
  unlocking another's data.
- **`content_hash`** — stable and key-order-independent (`{a,b}` == `{b,a}`), value-sensitive
  (`{a:1}` != `{a:2}`), and decimal-canonical (`1.50` == `1.5`).
- **`receipt_mac`** — keyed and deterministic, and provably *not* equal to a bare content hash
  (i.e. erasure receipts are HMACs, not just hashes an attacker could recompute).

### Dates — `test_dates.py` (10)
`normalize_timestamp` is the single choke-point that makes every source's timestamps UTC-aware. The
tests cover the real formats seen across sources: Fitbit space-separated naive (`2019-11-01 00:00:08`,
treated as UTC), ISO with/without millis, Zulu (`Z`) suffix, meal-log `dd/mm/yyyy` (date-only and
with time), and Unix epoch seconds. Two negative cases matter for data quality: an unparseable or
empty string **raises** (so bad rows are caught, not silently zeroed), and an id-like large integer
(`24475133162`, a sleep-log id) is **rejected** because it falls outside the plausible epoch window —
guarding against mistaking an identifier for a timestamp.

### ARFF — `test_arff.py` (7)
`read_rows` parses the UCI academic-performance ARFF format. Tests confirm: all data rows are yielded,
row keys match the `@ATTRIBUTE` names, nominal values are preserved verbatim, `numeric` columns are
coerced to `float`, the ARFF missing marker `?` becomes `None`, `%` comment lines are skipped, and a
row with the wrong column count **raises `ValueError`** rather than producing a misaligned record.

### Auth — `test_auth.py` (5)
Validates the webhook HMAC scheme in `pipeline.api.auth` (`expected_signature` / `verify`), the gate
for the live-ingest endpoint. A correctly signed request is accepted; a tampered body is rejected
with reason `"bad signature"`; a signature made with the wrong secret is rejected; a stale timestamp
(~99,999 s old) is rejected with `"stale timestamp"`; and a replayed nonce is accepted once then
rejected with `"replayed nonce"`. Together these cover the four standard webhook attacks: forgery,
tampering, replay, and clock-skew abuse. (Note: the nonce store is exercised in-process here — the
production replay defence depends on whatever backing store `verify` uses at runtime, which this unit
test does not stand up.)

### Connectors — `test_connectors.py` (4)
Parsing-only tests (3 PMData + 1 UCI-performance) using a `FakeCtx` that records emitted
points/records/quarantines, plus in-memory zip/csv/JSON fixtures — **no database**. They prove:
- PMData heart-rate JSON with `{"bpm":...}` dict values and messy date formats produces the right
  `Point`s (value, `metric`, `participant` all tagged correctly).
- A bad timestamp is **quarantined, not dropped** — 0 points emitted, 1 quarantine recorded. This is
  the data-quality contract: bad input is retained for inspection, not lost.
- A PMData CSV record carries the `participant` tag and correct `record_type`.
- A semicolon-delimited, quoted UCI `student-mat.csv` is parsed into records tagged with the
  `subject` (`mat`) and the right column values.

## Coverage — what the 29% actually covers

Coverage is **~29% of lines in `pipeline`** (1196 statements, 849 missed). That headline number is
low *by design of this run*: the suite is entirely **unit tests of pure functions**, so only the
modules those functions live in light up. Per-module figures from this run:

| Module | Cover | Read this as |
|---|---:|---|
| `common/logging.py` | 100% | fully exercised |
| `common/arff.py` | 96% | well covered (2 lines missed) |
| `common/dates.py` | 94% | well covered |
| `api/auth.py` | 88% | well covered |
| `common/crypto.py` | 79% | core paths covered; some branches missed |
| `common/config.py` | 78% | partial |
| `ingest/uci_performance.py` | 69% | parsing path only |
| `ingest/pmdata.py` | 53% | parsing path only |
| `common/db.py` | 43% | mostly DB plumbing, untested |
| `ingest/base.py` | 43% | connector framework partly hit via parsing tests |
| `cli.py` | **0%** | entrypoint, untested |
| `api/app.py`, `api/read.py`, `api/models.py` | **0%** | HTTP layer, untested |
| `analyse/queries.py` | **0%** | the 5 aggregate queries, untested |
| `process/curate_*.py`, `consent.py`, `erase.py`, `export.py`, `pseudonymise.py`, `util.py` | **0%** | the entire curation + GDPR-action layer, untested |
| `ingest/openfoodfacts.py`, `ingest/uci_academics.py` | **0%** | two connectors with no parsing test |

(Exact missed-line ranges are in the `term-missing` output; the table above is the shape, not every line.)

## Coverage gaps (honest)

The unit suite is solid for the **pure, deterministic** layer — crypto, date parsing, ARFF, HMAC,
and connector parsing. The gaps are everything that needs a database, a process, or an HTTP request:

1. **The entire curation + GDPR layer is at 0%.** `curate_academic/food/health`, `pseudonymise`,
   `consent`, `export`, `erase` — i.e. dedup, schema harmonisation, pseudonymisation, and the
   Art. 15/17/20 actions — have **no automated test**. These are the features the project leans on
   most heavily for its compliance claims, and they are currently validated only by the manual SQL
   walk-through in `TESTING.md`. That is the single biggest gap.
2. **No DB-backed tests exist at all.** Every one of the 37 tests is in-memory. Row-level security,
   the non-superuser app role, the pseudonymisation-map access denial, k-anonymity in the analytics —
   none of these are asserted in code. They are demonstrated by hand (`make analyse`, the RLS/role
   `psql` snippets in `TESTING.md`) but a regression in any of them would not fail the suite.
3. **The HTTP/API layer is at 0%.** `api/app.py` and `api/read.py` are untested end-to-end. Only the
   signature *helper* (`auth.py`) is unit-tested; the actual endpoint that calls it, parses the
   request, and writes to the raw zone is not.
4. **The CLI is at 0%.** `cli.py` and `__main__.py` (the `python -m pipeline ...` surface that
   `TESTING.md` drives the whole demo through) have no tests.
5. **Two connectors have no parsing test.** `openfoodfacts.py` and `uci_academics.py` are at 0% —
   the connector parsing tests only cover PMData and UCI-performance.
6. **Coverage tooling is not wired in.** `pytest-cov` had to be added by hand; the project can't
   currently produce this number from `make test`.

## Tests that could not run in this environment (and why)

- **`make test` (the canonical Docker path) — not runnable.** Only `datapipeline-db-1` is up; the
  `app`/`api` containers are down, so `docker compose exec app pytest` had no container to exec into.
  Worked around by running the suite in a local 3.12 venv. The official result should still be taken
  from `make test` once the app container is running.
- **Python 3.11 (suggested) — unusable.** `requires-python >= 3.12` in `pyproject.toml`; the resolver
  refused. Used uv-managed CPython 3.12.12 instead.
- **DB-backed tests — none to run.** There simply are no tests that need Postgres, so "DB not used"
  reflects the suite, not a skipped subset. Separately, the live TimescaleDB container is up and
  answering on `localhost:5432`, but password auth for role `piper` **failed** with the `.env`
  credentials — most likely `pgdata` was initialised with a different password than the current
  `.env`, or the app role was never bootstrapped. This did **not** affect the run (no test needs the
  DB) and **no secrets were read or printed**, but it is a real setup issue: any future DB-backed
  test, and the `make` demo flow, will hit the same auth wall until the password mismatch is fixed
  (e.g. re-bootstrap the role or recreate `pgdata` to match `.env`).

## What "passed" does and does not prove

- **Proven here:** the crypto roundtrips/tamper-rejection/key-separation, timestamp normalisation
  across the real formats, ARFF parsing, the four webhook attack defences, and connector
  parse-and-quarantine behaviour all held — on commit `4a5fdfc`, on Python 3.12.12, once.
- **Not proven here:** that curation/pseudonymisation/erasure produce correct rows; that RLS and the
  non-superuser role actually deny access; that k-anonymity holds in the analytics output; that the
  live webhook endpoint behaves like its helper; that the CLI commands do what they claim. These are
  asserted only by the manual procedures in `TESTING.md`, not by the suite.

## Advice for improvement (concrete)

1. **Add DB-backed tests for curation and GDPR actions** — the highest-value gap. Spin up a throwaway
   Postgres (the `db` container, or `testcontainers`/an ephemeral schema), load a tiny fixture, run
   `curate_*` and `erase`/`export`/`consent revoke`, and assert on the resulting rows and on the
   erasure receipt MAC. This converts the manual `TESTING.md` walk-through into regression tests.
2. **Encode the access-control claims as tests.** Turn the RLS / role-denial `psql` snippets in
   `TESTING.md` into automated tests: connect as `piper_subject` and assert exactly one subject is
   visible; connect as `piper_engineer` and assert `id.subject` is denied. Right now these
   security guarantees have zero automated protection.
3. **Add an API integration test** (FastAPI `TestClient` or a request against the running `api`
   container) that signs a real payload and asserts 200, then asserts 401 for tampered/replayed/stale
   — closing the gap between the auth *helper* (tested) and the *endpoint* (untested).
4. **Cover the two missing connectors** (`openfoodfacts`, `uci_academics`) with the same FakeCtx
   parsing pattern already used for PMData/UCI-performance.
5. **Wire coverage into the project**: add `pytest-cov` to the `[dev]` extra and a `--cov=pipeline`
   flag (or a `make coverage` target) so the number is reproducible, and set a floor in CI that
   rises as DB tests are added.
6. **Make the suite's preconditions explicit.** The crypto key-separation tests need
   `PIPER_MASTER_KEY` set or they fail at import; the skip-guards in `test_crypto.py`/
   `test_connectors.py` can hide a half-installed environment as "all green". Consider failing loudly
   (or a one-line precondition check) when deps/keys are absent, so a misconfigured run can't be
   mistaken for a passing one.
7. **Fix the DB password mismatch** so `make setup`/`make test` work against the live container, then
   make `make test` (the canonical Docker path) the source of truth for these numbers.
