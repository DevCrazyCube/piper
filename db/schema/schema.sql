-- Aegis pipeline — Phase 1 schema reference (human-readable mirror of migration 0001).
-- The migration in db/migrations/versions/ is the source of truth; this file is for review.
-- Phase 1 = RAW zone + provenance + quarantine. Curated zone, pseudonymisation map,
-- consent, and RLS arrive in Phase 2/3 (see docs/06-data-model.md, docs/07-roadmap.md).

CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE SCHEMA IF NOT EXISTS meta;
CREATE SCHEMA IF NOT EXISTS raw;

-- Source registry ----------------------------------------------------------
CREATE TABLE meta.source (
    name        TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,
    description TEXT,
    license     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Run provenance (ADR-0010) -------------------------------------------------
CREATE TABLE meta.pipeline_run (
    id               BIGSERIAL PRIMARY KEY,
    source           TEXT NOT NULL REFERENCES meta.source(name),
    kind             TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'running',
    started_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at      TIMESTAMPTZ,
    rows_in          BIGINT NOT NULL DEFAULT 0,
    rows_out         BIGINT NOT NULL DEFAULT 0,
    rows_quarantined BIGINT NOT NULL DEFAULT 0,
    detail           JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- Dead-letter / quarantine (ADR-0010) --------------------------------------
CREATE TABLE meta.quarantine (
    id         BIGSERIAL PRIMARY KEY,
    run_id     BIGINT REFERENCES meta.pipeline_run(id),
    source     TEXT NOT NULL,
    record_ref TEXT,
    field      TEXT,
    reason     TEXT NOT NULL,
    raw_value  TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Raw zone: structured records (JSONB, idempotent by content hash) ----------
CREATE TABLE raw.record (
    id           BIGSERIAL PRIMARY KEY,
    source       TEXT NOT NULL REFERENCES meta.source(name),
    record_type  TEXT NOT NULL,
    natural_key  TEXT,
    content_hash TEXT NOT NULL,
    payload      JSONB NOT NULL,
    run_id       BIGINT REFERENCES meta.pipeline_run(id),
    ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX raw_record_hash_uq ON raw.record(content_hash);
CREATE INDEX raw_record_source_type_idx ON raw.record(source, record_type);

-- Raw zone: time-series -> TimescaleDB hypertable (ADR-0003) ----------------
CREATE TABLE raw.timeseries (
    source      TEXT NOT NULL,
    participant TEXT NOT NULL,
    metric      TEXT NOT NULL,
    ts          TIMESTAMPTZ NOT NULL,
    value       DOUBLE PRECISION,
    run_id      BIGINT
);
SELECT create_hypertable('raw.timeseries', 'ts', chunk_time_interval => INTERVAL '7 days');
CREATE UNIQUE INDEX raw_timeseries_grain_uq ON raw.timeseries(source, participant, metric, ts);
