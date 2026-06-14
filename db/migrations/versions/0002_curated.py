"""curated zone, pseudonymisation map, consent, decision log, RLS scaffold

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-14
"""
from __future__ import annotations

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS id")
    op.execute("CREATE SCHEMA IF NOT EXISTS consent")
    op.execute("CREATE SCHEMA IF NOT EXISTS curated")

    # --- Pseudonymisation map (ADR-0006/0008): real source id -> random pid -----------
    # enc_identity holds the source-local identity encrypted at the APPLICATION layer
    # (AES-256-GCM, key from env) so the DB only ever stores ciphertext.
    op.execute(
        """
        CREATE TABLE id.subject (
            subject_pid     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source          TEXT NOT NULL,
            source_local_id TEXT NOT NULL,
            enc_identity    BYTEA NOT NULL,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (source, source_local_id)
        )
        """
    )

    # --- Consent per subject + scope (drives RLS / lawful basis) -----------------------
    op.execute(
        """
        CREATE TABLE consent.consent (
            subject_pid  UUID NOT NULL REFERENCES id.subject(subject_pid),
            scope        TEXT NOT NULL,               -- sleep|heart_rate|activity|meals|grades|...
            lawful_basis TEXT NOT NULL DEFAULT 'consent',
            status       TEXT NOT NULL DEFAULT 'granted',  -- granted|revoked
            updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (subject_pid, scope)
        )
        """
    )

    # --- Cleaning / bias / dedup decision log (the "documented decisions" deliverable) -
    op.execute(
        """
        CREATE TABLE meta.decision (
            id         BIGSERIAL PRIMARY KEY,
            run_id     BIGINT,
            stage      TEXT NOT NULL,        -- curate|dedup|harmonise|impute|...
            source     TEXT,
            decision   TEXT NOT NULL,
            rationale  TEXT,
            detail     JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # --- Curated time-series -> hypertable, keyed by pseudonymous subject --------------
    op.execute(
        """
        CREATE TABLE curated.timeseries (
            subject_pid UUID NOT NULL,
            metric      TEXT NOT NULL,
            ts          TIMESTAMPTZ NOT NULL,
            value       DOUBLE PRECISION
        )
        """
    )
    op.execute("SELECT create_hypertable('curated.timeseries','ts',chunk_time_interval=>INTERVAL '7 days')")
    op.execute(
        "CREATE UNIQUE INDEX curated_ts_grain_uq ON curated.timeseries(subject_pid, metric, ts)"
    )

    # --- Curated structured health records --------------------------------------------
    op.execute(
        """
        CREATE TABLE curated.sleep (
            subject_pid    UUID NOT NULL,
            sleep_date     DATE,
            start_ts       TIMESTAMPTZ,
            end_ts         TIMESTAMPTZ,
            minutes_asleep INTEGER,
            efficiency     INTEGER,
            deep_min       INTEGER,
            light_min      INTEGER,
            rem_min        INTEGER,
            wake_min       INTEGER,
            PRIMARY KEY (subject_pid, sleep_date, start_ts)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE curated.wellness (
            subject_pid     UUID NOT NULL,
            ts              TIMESTAMPTZ NOT NULL,
            fatigue         SMALLINT,
            mood            SMALLINT,
            readiness       SMALLINT,
            sleep_duration_h REAL,
            sleep_quality   SMALLINT,
            soreness        SMALLINT,
            stress          SMALLINT,
            PRIMARY KEY (subject_pid, ts)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE curated.meal (
            subject_pid UUID NOT NULL,
            ts          TIMESTAMPTZ NOT NULL,
            meals       TEXT,
            weight_kg   REAL,
            fluids      SMALLINT,
            alcohol     BOOLEAN,
            PRIMARY KEY (subject_pid, ts)
        )
        """
    )

    # --- Curated academic (harmonised UCI performance + academics) --------------------
    # grade_final_norm: 0..1 from either G3/20 (performance) or esp band (academics).
    op.execute(
        """
        CREATE TABLE curated.student_academic (
            id               BIGSERIAL PRIMARY KEY,
            origin           TEXT NOT NULL,     -- uci-performance | uci-academics
            sex              TEXT,              -- M|F
            age              SMALLINT,
            study_time       SMALLINT,          -- ordinal 1..4 (perf only)
            failures         SMALLINT,
            absences         SMALLINT,
            attendance_band  TEXT,              -- Good|Average|Poor (academics only)
            grade_final_norm REAL,              -- 0..1 normalised final outcome
            detail           JSONB NOT NULL DEFAULT '{}'::jsonb
        )
        """
    )

    # --- Curated nutrition reference (flattened from OFF nested nutriments) ------------
    op.execute(
        """
        CREATE TABLE curated.food_reference (
            code             TEXT PRIMARY KEY,
            product_name     TEXT,
            brands           TEXT,
            nutriscore_grade TEXT,
            energy_kcal_100g REAL,
            fat_100g         REAL,
            sugars_100g      REAL,
            proteins_100g    REAL,
            salt_100g        REAL
        )
        """
    )

    # --- RLS + roles scaffold (Week 5 AAA; ADR-0006) ----------------------------------
    # Roles are NOLOGIN demonstrators; the app connects as owner (bypasses RLS to curate).
    op.execute("DO $$ BEGIN CREATE ROLE aegis_analyst NOLOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("DO $$ BEGIN CREATE ROLE aegis_subject NOLOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$")

    # data_subject can see ONLY their own rows (RLS by session-set pid).
    op.execute("ALTER TABLE curated.timeseries ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY subject_isolation ON curated.timeseries FOR SELECT TO aegis_subject "
        "USING (subject_pid::text = current_setting('aegis.subject_pid', true))"
    )
    op.execute("GRANT USAGE ON SCHEMA curated TO aegis_subject, aegis_analyst")
    op.execute("GRANT SELECT ON curated.timeseries TO aegis_subject")

    # analyst gets aggregate-only views, never the base table (no identifiers).
    op.execute(
        """
        CREATE VIEW curated.v_daily_active_minutes AS
        SELECT time_bucket('1 day', ts) AS day,
               metric,
               count(*)          AS samples,
               avg(value)        AS avg_value
        FROM curated.timeseries
        WHERE metric IN ('lightly_active_minutes','moderately_active_minutes','very_active_minutes')
        GROUP BY 1, 2
        """
    )
    op.execute("GRANT SELECT ON curated.v_daily_active_minutes TO aegis_analyst")


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS curated.v_daily_active_minutes")
    op.execute("DROP SCHEMA IF EXISTS curated CASCADE")
    op.execute("DROP SCHEMA IF EXISTS consent CASCADE")
    op.execute("DROP SCHEMA IF EXISTS id CASCADE")
    op.execute("DROP TABLE IF EXISTS meta.decision")
    op.execute("DROP ROLE IF EXISTS aegis_analyst")
    op.execute("DROP ROLE IF EXISTS aegis_subject")
