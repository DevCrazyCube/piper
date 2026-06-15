"""non-superuser app role, FORCE RLS on all subject tables, nonce store, audit lockdown

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-15

Audit remediation:
- The app previously connected as the superuser `aegis`, which BYPASSES RLS — making the
  whole access-control layer decorative. Introduce a NOSUPERUSER/NOBYPASSRLS `aegis_app`
  login role for runtime; migrations still run as `aegis`.
- FORCE ROW LEVEL SECURITY + policies on every curated subject table (was 1 of 4).
- Replay nonce store moved to the DB (was in-process only).
- Engineers can no longer write the audit log / deletion receipts (audit integrity).
"""
from __future__ import annotations

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

_SUBJECT_TABLES = ("timeseries", "sleep", "wellness", "meal")


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN CREATE ROLE aegis_app LOGIN NOSUPERUSER NOBYPASSRLS; "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    )

    # Replay-nonce store (shared across workers/restarts; unique-insert = replay check).
    op.execute(
        "CREATE TABLE IF NOT EXISTS meta.webhook_nonce ("
        "nonce TEXT PRIMARY KEY, seen_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    )

    # Grants to the runtime role (least privilege: no DDL, no superuser).
    for schema in ("raw", "curated", "meta", "id", "consent"):
        op.execute(f"GRANT USAGE ON SCHEMA {schema} TO aegis_app")
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema} TO aegis_app")
        op.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema} TO aegis_app")
        # Future tables created by aegis in these schemas.
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE aegis IN SCHEMA {schema} "
            "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO aegis_app"
        )
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE aegis IN SCHEMA {schema} "
            "GRANT USAGE, SELECT ON SEQUENCES TO aegis_app"
        )
    # The app role must NOT read the pseudonymisation map? It must, to join/pseudonymise.
    # Engineers/analysts/subjects still cannot (no grants on schema id for them).

    # RLS on every curated subject table: app sees all (it's the processor), subject sees own.
    for tbl in _SUBJECT_TABLES:
        op.execute(f"ALTER TABLE curated.{tbl} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE curated.{tbl} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"DO $$ BEGIN CREATE POLICY app_all ON curated.{tbl} TO aegis_app "
            "USING (true) WITH CHECK (true); EXCEPTION WHEN duplicate_object THEN NULL; END $$"
        )
        op.execute(
            f"DO $$ BEGIN CREATE POLICY subject_isolation ON curated.{tbl} FOR SELECT "
            "TO aegis_subject USING (subject_pid::text = current_setting('aegis.subject_pid', true)); "
            "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
        )
        op.execute(f"GRANT SELECT ON curated.{tbl} TO aegis_subject")

    # Audit integrity: the audited party (engineer) must not write audit/receipt rows.
    op.execute("REVOKE INSERT ON meta.audit_log FROM aegis_engineer")
    op.execute("REVOKE INSERT, SELECT ON meta.deletion_receipt FROM aegis_engineer")


def downgrade() -> None:
    for tbl in _SUBJECT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS app_all ON curated.{tbl}")
        if tbl != "timeseries":
            op.execute(f"DROP POLICY IF EXISTS subject_isolation ON curated.{tbl}")
            op.execute(f"ALTER TABLE curated.{tbl} DISABLE ROW LEVEL SECURITY")
        else:
            op.execute("ALTER TABLE curated.timeseries NO FORCE ROW LEVEL SECURITY")
    op.execute("DROP TABLE IF EXISTS meta.webhook_nonce")
    # role + grants intentionally left (other objects may depend); drop manually if needed.
