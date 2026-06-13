# Source layout

`src/pipeline/` — the pipeline package. Modules map to the 8 lifecycle stages and the
cross-cutting concerns. Code arrives in roadmap Phase 1+ (`docs/07-roadmap.md`); these are the
agreed homes for it.

| Module | Responsibility | Stages |
|---|---|---|
| `ingest/` | Batch connectors (JSON/CSV/Parquet) + FastAPI webhook + export-zip fallback; raw zone | 01 Ingest, 02 Transport |
| `process/` | Clean, filter, normalize, dedup, schema-harmonise, data-quality checks | 04 Process |
| `privacy/` | Pseudonymisation, consent model, data minimisation | 03/04 (privacy controls) |
| `store/` | DB access (SQLAlchemy), models, migrations glue | 03 Store |
| `analyse/` | The 5 cross-source analytics queries over curated views | 05 Analyse |
| `common/` | Config, structured logging/audit, crypto helpers, errors | cross-cutting (06/07) |

Sibling top-level dirs:
- `db/migrations/` — Alembic migrations · `db/schema/` — reference schema SQL (tracked)
- `tests/` — pytest unit + integration
- `docker/` — Dockerfiles (compose lives at repo root)
