"""audit log + triggers, engineer role/grants, erasure receipts, retention

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-14
"""
from __future__ import annotations

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Audit log (Week 5 'Accounting') ----------------------------------------------
    op.execute(
        """
        CREATE TABLE meta.audit_log (
            id      BIGSERIAL PRIMARY KEY,
            ts      TIMESTAMPTZ NOT NULL DEFAULT now(),
            actor   TEXT NOT NULL DEFAULT current_user,
            action  TEXT NOT NULL,            -- INSERT|UPDATE|DELETE|ERASE|...
            object  TEXT NOT NULL,            -- schema.table
            key     TEXT,                     -- affected key (pid/scope), best-effort
            detail  JSONB NOT NULL DEFAULT '{}'::jsonb
        )
        """
    )

    # Row-level audit on the high-value, low-volume tables: identity map + consent.
    # (Bulk curated inserts are intentionally NOT audited per-row — too noisy.)
    op.execute(
        """
        CREATE FUNCTION meta.audit_event() RETURNS trigger AS $$
        DECLARE k TEXT;
        BEGIN
          k := COALESCE(NEW.subject_pid::text, OLD.subject_pid::text, NULL);
          INSERT INTO meta.audit_log(actor, action, object, key, detail)
          VALUES (current_user, TG_OP, TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME, k,
                  jsonb_build_object('when', now()));
          RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        "CREATE TRIGGER audit_consent AFTER INSERT OR UPDATE OR DELETE ON consent.consent "
        "FOR EACH ROW EXECUTE FUNCTION meta.audit_event()"
    )
    op.execute(
        "CREATE TRIGGER audit_subject AFTER INSERT OR UPDATE OR DELETE ON id.subject "
        "FOR EACH ROW EXECUTE FUNCTION meta.audit_event()"
    )

    # --- Right to erasure (GDPR Art.17): verifiable deletion receipt -------------------
    op.execute(
        """
        CREATE TABLE meta.deletion_receipt (
            id          BIGSERIAL PRIMARY KEY,
            subject_pid UUID NOT NULL,
            erased_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
            actor       TEXT NOT NULL DEFAULT current_user,
            counts      JSONB NOT NULL,       -- rows removed per table
            digest      TEXT NOT NULL         -- sha256 over the receipt (integrity)
        )
        """
    )

    # --- RBAC: pipeline engineer role (least privilege; NO access to the identity map) -
    op.execute("DO $$ BEGIN CREATE ROLE piper_engineer NOLOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$")
    op.execute("GRANT USAGE ON SCHEMA raw, curated, meta TO piper_engineer")
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA raw TO piper_engineer")
    op.execute("GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA curated TO piper_engineer")
    op.execute("GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA meta TO piper_engineer")
    # Note: NO grant on schema `id` — engineers cannot read the pseudonymisation map.
    op.execute("REVOKE ALL ON SCHEMA id FROM piper_engineer")

    # --- Anomaly detection (illustrative): bursty actors in the audit log --------------
    op.execute(
        """
        CREATE VIEW meta.v_anomaly AS
        SELECT actor,
               date_trunc('hour', ts) AS hour,
               count(*) AS events,
               CASE WHEN count(*) > 100 THEN 'high'
                    WHEN count(*) > 25  THEN 'medium' ELSE 'low' END AS severity
        FROM meta.audit_log
        GROUP BY actor, date_trunc('hour', ts)
        HAVING count(*) > 25
        """
    )

    # --- Retention (TimescaleDB): demonstrate raw time-series retention policy ----------
    # Long window so nothing is dropped now; proves the deletion-obligation mechanism.
    op.execute("SELECT add_retention_policy('raw.timeseries', INTERVAL '3650 days')")


def downgrade() -> None:
    op.execute("SELECT remove_retention_policy('raw.timeseries', if_exists => true)")
    op.execute("DROP VIEW IF EXISTS meta.v_anomaly")
    op.execute("DROP TABLE IF EXISTS meta.deletion_receipt")
    op.execute("DROP TRIGGER IF EXISTS audit_subject ON id.subject")
    op.execute("DROP TRIGGER IF EXISTS audit_consent ON consent.consent")
    op.execute("DROP FUNCTION IF EXISTS meta.audit_event")
    op.execute("DROP TABLE IF EXISTS meta.audit_log")
    op.execute("DROP ROLE IF EXISTS piper_engineer")
