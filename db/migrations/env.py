"""Alembic environment — uses the app's SQLAlchemy engine (DB URL from settings/env)."""

from __future__ import annotations

from alembic import context

from pipeline.common.db import get_engine

target_metadata = None  # migrations are hand-written SQL (TimescaleDB hypertables, RLS)


def run_migrations_online() -> None:
    connectable = get_engine()
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise SystemExit("Offline mode is not supported; run with a live database.")
run_migrations_online()
