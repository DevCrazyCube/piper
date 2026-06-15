"""device registry for the real-time webhook ingest

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-15
"""
from __future__ import annotations

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Per-device HMAC secret, encrypted at the application layer (never plaintext at rest).
    # Each device maps to a subject (its source_local_id -> id.subject), keeping the live
    # feed pseudonymous like every other source.
    op.execute(
        """
        CREATE TABLE meta.device (
            device_id       TEXT PRIMARY KEY,
            enc_secret      BYTEA NOT NULL,
            source          TEXT NOT NULL DEFAULT 'wearable-live',
            source_local_id TEXT NOT NULL,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "INSERT INTO meta.source(name, kind, description, license) VALUES "
        "('wearable-live','stream','Near-real-time wearable feed via authenticated webhook','n/a') "
        "ON CONFLICT (name) DO NOTHING"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS meta.device")
