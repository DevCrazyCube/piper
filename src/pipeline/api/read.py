"""Read-only endpoints for the dashboard. Aggregate/operational data only — no raw
identifiers. Each is defensive: on any error it returns an empty list so the frontend
falls back to its mock seed rather than 500-ing.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter

from pipeline.common.db import pg_connection

router = APIRouter(prefix="/v1")


def _query(sql: str, mapper: Callable[[dict], Any]) -> list[Any]:
    try:
        with pg_connection() as conn, conn.cursor() as cur:
            cur.execute(sql)
            cols = [d.name for d in cur.description]  # type: ignore[union-attr]
            return [mapper(dict(zip(cols, row, strict=True))) for row in cur.fetchall()]
    except Exception:
        return []


@router.get("/runs")
def runs() -> list[dict]:
    def m(r: dict) -> dict:
        status = "failed" if r["status"] == "failed" else ("quarantine" if r["rows_quarantined"] else "success")
        dur = r["dur_s"] or 0
        return {
            "id": f"run_{r['id']}", "source": r["source"], "status": status,
            "rows_in": r["rows_in"], "rows_out": r["rows_out"],
            "transforms": 0, "duration": f"{int(dur)//60}m {int(dur)%60:02d}s",
            "quarantined": r["rows_quarantined"],
        }
    return _query(
        "SELECT id, source, status, rows_in, rows_out, rows_quarantined, "
        "EXTRACT(EPOCH FROM COALESCE(finished_at, now()) - started_at) AS dur_s "
        "FROM meta.pipeline_run ORDER BY id DESC LIMIT 50",
        m,
    )


@router.get("/security/audit")
def audit() -> list[dict]:
    def m(r: dict) -> dict:
        return {
            "t": str(r["t"]), "action": r["action"], "object": r["object"] or "",
            "actor": r["actor"], "result": "denied" if r["action"] == "DENY" else "ok",
        }
    return _query(
        "SELECT to_char(ts,'HH24:MI:SS') AS t, action, object, actor "
        "FROM meta.audit_log ORDER BY id DESC LIMIT 40",
        m,
    )


@router.get("/security/anomalies")
def anomalies() -> list[dict]:
    sev = {"high": "HIGH", "medium": "MED", "low": "LOW"}
    return _query(
        "SELECT actor, events, severity, hour FROM meta.v_anomaly ORDER BY events DESC LIMIT 10",
        lambda r: {"title": f"{r['actor']} — unusual activity",
                   "detail": f"{r['events']} events · {r['hour']}",
                   "severity": sev.get(r["severity"], "LOW")},
    )
