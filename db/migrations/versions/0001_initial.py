"""initial: raw zone, provenance, quarantine, timescaledb hypertable

Revision ID: 0001
Revises:
Create Date: 2026-06-13
"""
from __future__ import annotations

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
    op.execute("CREATE SCHEMA IF NOT EXISTS meta")
    op.execute("CREATE SCHEMA IF NOT EXISTS raw")

    # --- Source registry (seeded below) ---
    op.execute(
        """
        CREATE TABLE meta.source (
            name        TEXT PRIMARY KEY,
            kind        TEXT NOT NULL,
            description TEXT,
            license     TEXT,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # --- Provenance: one row per pipeline run (ADR-0010) ---
    op.execute(
        """
        CREATE TABLE meta.pipeline_run (
            id               BIGSERIAL PRIMARY KEY,
            source           TEXT NOT NULL REFERENCES meta.source(name),
            kind             TEXT NOT NULL,            -- e.g. 'ingest'
            status           TEXT NOT NULL DEFAULT 'running',  -- running|success|failed
            started_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
            finished_at      TIMESTAMPTZ,
            rows_in          BIGINT NOT NULL DEFAULT 0,
            rows_out         BIGINT NOT NULL DEFAULT 0,
            rows_quarantined BIGINT NOT NULL DEFAULT 0,
            detail           JSONB NOT NULL DEFAULT '{}'::jsonb
        )
        """
    )

    # --- Dead-letter / quarantine: failed rows, never silently dropped (ADR-0010) ---
    op.execute(
        """
        CREATE TABLE meta.quarantine (
            id         BIGSERIAL PRIMARY KEY,
            run_id     BIGINT REFERENCES meta.pipeline_run(id),
            source     TEXT NOT NULL,
            record_ref TEXT,            -- best-effort id/locator of the offending record
            field      TEXT,            -- offending field, if known
            reason     TEXT NOT NULL,
            raw_value  TEXT,            -- the raw value that failed
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # --- Raw zone: low-volume structured records as JSONB (write-once, checksummed) ---
    op.execute(
        """
        CREATE TABLE raw.record (
            id           BIGSERIAL PRIMARY KEY,
            source       TEXT NOT NULL REFERENCES meta.source(name),
            record_type  TEXT NOT NULL,         -- e.g. 'sleep', 'wellness', 'meal', 'grade'
            natural_key  TEXT,                   -- source-natural identifier, if any
            content_hash TEXT NOT NULL,          -- sha256 of canonical payload -> idempotency
            payload      JSONB NOT NULL,
            run_id       BIGINT REFERENCES meta.pipeline_run(id),
            ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    # Idempotent re-ingest: same payload hash never duplicates.
    op.execute("CREATE UNIQUE INDEX raw_record_hash_uq ON raw.record(content_hash)")
    op.execute("CREATE INDEX raw_record_source_type_idx ON raw.record(source, record_type)")

    # --- Raw zone: high-volume time-series -> TimescaleDB hypertable (ADR-0003) ---
    op.execute(
        """
        CREATE TABLE raw.timeseries (
            source      TEXT NOT NULL,
            participant TEXT NOT NULL,           -- source-local subject id (pseudonymised in Phase 2)
            metric      TEXT NOT NULL,           -- heart_rate | steps | calories | distance | ...
            ts          TIMESTAMPTZ NOT NULL,
            value       DOUBLE PRECISION,
            run_id      BIGINT
        )
        """
    )
    op.execute("SELECT create_hypertable('raw.timeseries', 'ts', chunk_time_interval => INTERVAL '7 days')")
    # Idempotency: unique on the natural grain. Must include the partition column (ts).
    op.execute(
        "CREATE UNIQUE INDEX raw_timeseries_grain_uq "
        "ON raw.timeseries(source, participant, metric, ts)"
    )

    # --- Seed the source registry ---
    op.execute(
        """
        INSERT INTO meta.source(name, kind, description, license) VALUES
          ('pmdata',          'batch', 'PMData: Fitbit + PMSys wellness + meal logs (16 participants)', 'CC BY-NC 4.0'),
          ('uci-performance', 'batch', 'UCI Student Performance (mat + por, semicolon CSV)',            'Open / public domain'),
          ('uci-academics',   'batch', 'UCI Student Academics (ARFF, categorical bands)',               'Open'),
          ('openfoodfacts',   'batch', 'Open Food Facts nutrition reference (minimised subset)',        'ODbL')
        ON CONFLICT (name) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS raw CASCADE")
    op.execute("DROP SCHEMA IF EXISTS meta CASCADE")
