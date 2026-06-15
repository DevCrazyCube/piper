"""Database access. SQLAlchemy engine for migrations/queries; raw psycopg for fast batch writes."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

import psycopg
from sqlalchemy import Engine, create_engine

from pipeline.common.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().sqlalchemy_dsn, pool_pre_ping=True, future=True)


@contextmanager
def pg_connection() -> Iterator[psycopg.Connection]:
    """Runtime connection as the non-superuser app role (committed on clean exit)."""
    conn = psycopg.connect(get_settings().psycopg_conninfo)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def pg_admin_connection() -> Iterator[psycopg.Connection]:
    """Admin (superuser) connection — only for role bootstrap / privileged ops."""
    conn = psycopg.connect(get_settings().admin_conninfo)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
