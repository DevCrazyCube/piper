"""Curation helpers: tolerant coercion + decision logging."""

from __future__ import annotations

import psycopg
from psycopg.types.json import Json

_TRUE = {"yes", "true", "1", "y"}
_FALSE = {"no", "false", "0", "n"}


def to_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))  # tolerate "5" and "5.0"
    except (ValueError, TypeError):
        return None


def to_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def to_bool(value: object) -> bool | None:
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in _TRUE:
        return True
    if s in _FALSE:
        return False
    return None


def log_decision(
    cur: psycopg.Cursor,
    *,
    stage: str,
    decision: str,
    source: str | None = None,
    rationale: str | None = None,
    detail: dict | None = None,
    run_id: int | None = None,
) -> None:
    """Record a cleaning/dedup/harmonisation/bias decision (deliverable: documented decisions)."""
    cur.execute(
        "INSERT INTO meta.decision (run_id, stage, source, decision, rationale, detail) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (run_id, stage, source, decision, rationale, Json(detail or {})),
    )
