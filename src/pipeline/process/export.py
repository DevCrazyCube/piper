"""Data-subject export (GDPR Art. 15 access / Art. 20 portability).

Returns a subject's curated data as a structured dict (JSON-serialisable). Uses the
pseudonymous subject_pid only — no real identity is included.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any
from uuid import UUID

import psycopg

_QUERIES: dict[str, str] = {
    "timeseries": "SELECT metric, ts, value FROM curated.timeseries WHERE subject_pid = %s ORDER BY ts",
    "sleep": "SELECT sleep_date, minutes_asleep, efficiency, deep_min, light_min, rem_min, wake_min "
             "FROM curated.sleep WHERE subject_pid = %s ORDER BY sleep_date",
    "wellness": "SELECT ts, fatigue, mood, readiness, sleep_duration_h, sleep_quality, soreness, stress "
                "FROM curated.wellness WHERE subject_pid = %s ORDER BY ts",
    "meal": "SELECT ts, meals, weight_kg, fluids, alcohol FROM curated.meal WHERE subject_pid = %s ORDER BY ts",
    "consent": "SELECT scope, lawful_basis, status, updated_at FROM consent.consent WHERE subject_pid = %s",
}


def export_subject(conn: psycopg.Connection, subject_pid: str) -> dict[str, Any]:
    pid = str(UUID(subject_pid))
    out: dict[str, Any] = {"subject_pid": pid, "data": {}}
    with conn.cursor() as cur:
        for name, sql in _QUERIES.items():
            cur.execute(sql, (pid,))
            cols = [d.name for d in cur.description]  # type: ignore[union-attr]
            out["data"][name] = [
                {c: _json_safe(v) for c, v in zip(cols, r, strict=True)} for r in cur.fetchall()
            ]
    return out


def _json_safe(value: Any) -> Any:
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()
    return value
