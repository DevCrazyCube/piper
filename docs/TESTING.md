# Testing Piper — a guide for teammates

How to get Piper running and test it on a normal laptop. The whole thing runs in Docker, so you
don't install Python/Postgres yourself.

> ⚠️ **The full PMData ingest is heavy** (~27M points, ~40 min, lots of RAM — it can freeze a
> laptop). For testing, use the **light path** below: skip or cap PMData. You still exercise the
> entire pipeline.

## 0. What you need
1. **Repo access** — Piper is a *private* repo (`DevCrazyCube/piper`). Ask Joyren to add your GitHub
   username as a collaborator, then `git clone`.
2. **Docker + Docker Compose** installed and running.
3. **The datasets** in `datasets/` (they're gitignored, not in the repo):
   - `student+performance.zip`, `student+academics+performance.zip` — tiny, public (UCI). Enough for
     a full academic-domain test.
   - `food.parquet` (~7 GB) and `pmdata.zip` (~1.4 GB) — large; get them from Joyren. Optional for a
     light test.

## 1. First-run (2 minutes)
```bash
cp .env.example .env
# In .env set: PIPER_DB_PASSWORD, PIPER_APP_PASSWORD (any strong values), and
# PIPER_MASTER_KEY — generate with:
python -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"

# For a light test, also set:  PIPER_PMDATA_MAX_PARTICIPANTS=2

make setup       # start containers + create schema + create the app role
```

## 2. Light test path (seconds → a couple minutes, no freeze)
```bash
# fast sources only (UCI is tiny; food needs the 7GB parquet — skip if you don't have it)
make ingest-uci-perf
make ingest-uci-academics
make ingest-food          # only if you have food.parquet

# only 2 PMData participants (set PIPER_PMDATA_MAX_PARTICIPANTS=2 in .env first)
make ingest-pmdata        # only if you have pmdata.zip

make curate               # build the curated zone from whatever you ingested
make analyse              # run the 5 aggregate queries
```

## 3. Verify your environment with ZERO data
```bash
make check     # builds, lints, type-checks, runs the test suite + security scan
```
If `make check` is green, your setup is correct even before loading any data.

## 4. Test the features (what to actually look at)
```bash
# Analytics — aggregate only, never individual rows
make analyse                      # all 5; or:  make analyse Q=q3

# Pipeline provenance / what ran
docker compose exec db psql -U piper -d piper -c "SELECT id, source, status, rows_in, rows_quarantined FROM meta.pipeline_run ORDER BY id;"

# Privacy & data-subject rights (need a health subject — from PMData)
docker compose exec db psql -U piper -d piper -c "SELECT subject_pid, source FROM id.subject LIMIT 5;"
docker compose exec app python -m pipeline export <subject_pid>          # GDPR Art.15/20
docker compose exec app python -m pipeline consent revoke <pid> sleep    # deletes that scope's data
make erase PID=<subject_pid>                                             # GDPR Art.17 + receipt

# Row-level security — a subject can only see their own rows
docker compose exec db psql -U piper -d piper <<'SQL'
SELECT set_config('piper.subject_pid',(SELECT subject_pid::text FROM id.subject LIMIT 1),false);
SET ROLE piper_subject;
SELECT count(DISTINCT subject_pid) AS subjects_visible FROM curated.timeseries;  -- expect 1
RESET ROLE;
SQL

# The pseudonymisation map is NOT readable by analyst/engineer/subject roles (try it → denied)
docker compose exec db psql -U piper -d piper -c "SET ROLE piper_engineer; SELECT * FROM id.subject LIMIT 1;"
```

## 5. Live webhook (optional)
```bash
docker compose exec app python -m pipeline register-device watch-01 teammate-a   # prints a secret
```
Then POST signed JSON to `http://localhost:8000/v1/ingest` (headers `X-Piper-Device/-Timestamp/
-Nonce/-Signature`, HMAC-SHA256 over `timestamp.nonce.body`). Tampered/replayed/stale → `401`.

## What each command proves (for the write-up / demo)
| Command | Demonstrates |
|---|---|
| `make ingest` | raw-zone landing, format handling, quarantine, idempotency |
| `make curate` | cleaning, **dedup** (UCI mat+por), **schema harmonisation**, **pseudonymisation** |
| `make analyse` | aggregate-only analytics with k-anonymity |
| `export` / `consent revoke` / `erase` | GDPR Art. 15/20, Art. 7, Art. 17 |
| the RLS / role checks | access control actually enforced (non-superuser app role) |
| `make check` | tests + lint + SAST all pass |

Stuck? `make logs` (tail), `make shell` (shell in the app container), `make down` (stop).
Full design + the security/compliance/bias deliverables are in [`docs/`](.).
