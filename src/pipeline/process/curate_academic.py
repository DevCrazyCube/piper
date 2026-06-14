"""Curate the academic domain (ADR-0009): dedup the two UCI Performance files and
harmonise them with the UCI Academics (ARFF) set into one schema with a normalised
final-grade. These are different populations from PMData — no cross-join to health.
"""

from __future__ import annotations

import psycopg
from psycopg.types.json import Json

from pipeline.common.logging import get_logger
from pipeline.process.util import log_decision, to_int

log = get_logger("curate.academic")

# Identifying attributes used to detect the same student across mat/por (per student-merge.R).
_DEDUP_KEYS = (
    "school", "sex", "age", "address", "famsize", "Pstatus",
    "Medu", "Fedu", "Mjob", "Fjob", "reason", "nursery", "internet",
)

# Academics exam-band -> 0..1 normalised grade (scale reconciliation with G3/20).
_BAND_NORM = {"Best": 1.0, "Vg": 0.8, "Good": 0.6, "Pass": 0.4, "Fail": 0.2}


def curate_academic(conn: psycopg.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    with conn.cursor() as cur:
        counts["performance"] = _curate_performance(cur)
        counts["academics"] = _curate_academics(cur)
    log.info("curate.academic.done", **counts)
    return counts


def _curate_performance(cur: psycopg.Cursor) -> int:
    cur.execute("SELECT payload FROM raw.record WHERE source='uci-performance' AND record_type='grade'")
    records = [r[0] for r in cur.fetchall()]

    groups: dict[tuple, list[dict]] = {}
    for rec in records:
        key = tuple(rec.get(k) for k in _DEDUP_KEYS)
        groups.setdefault(key, []).append(rec)

    merged = sum(1 for g in groups.values() if len({r.get("subject") for r in g}) > 1)

    rows = []
    for recs in groups.values():
        g3s = [v / 20.0 for r in recs if (v := _num(r.get("G3"))) is not None]
        grade_norm = sum(g3s) / len(g3s) if g3s else None
        rep = recs[0]
        rows.append(
            ("uci-performance", rep.get("sex"), to_int(rep.get("age")),
             to_int(rep.get("studytime")), to_int(rep.get("failures")),
             to_int(rep.get("absences")), None, grade_norm,
             Json({"subjects": sorted({r.get("subject") for r in recs})}))
        )
    _insert(cur, rows)

    log_decision(
        cur, stage="dedup", source="uci-performance",
        decision=f"deduped {len(records)} rows -> {len(groups)} students ({merged} in both mat+por)",
        rationale="same student appears in both files; matched on 13 identifying attrs (student-merge.R)",
        detail={"raw_rows": len(records), "unique_students": len(groups), "in_both": merged},
    )
    return len(rows)


def _curate_academics(cur: psycopg.Cursor) -> int:
    cur.execute("SELECT payload FROM raw.record WHERE source='uci-academics' AND record_type='academic'")
    rows = []
    unmapped = 0
    for (p,) in cur.fetchall():
        norm = _BAND_NORM.get(p.get("esp"))
        if norm is None:
            unmapped += 1
        rows.append(
            ("uci-academics", p.get("ge"), None, None, None, None,
             p.get("atd"), norm, Json({"caste": p.get("cst"), "esp_band": p.get("esp")}))
        )
    _insert(cur, rows)

    log_decision(
        cur, stage="harmonise", source="uci-academics",
        decision="mapped exam bands (Best..Fail) to 0..1 grade_final_norm",
        rationale="reconcile categorical bands with UCI-performance numeric G3/20 onto one scale",
        detail={"band_map": _BAND_NORM, "rows": len(rows), "unmapped_band": unmapped},
    )
    return len(rows)


def _num(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return None


def _insert(cur: psycopg.Cursor, rows: list[tuple]) -> None:
    cur.executemany(
        "INSERT INTO curated.student_academic "
        "(origin, sex, age, study_time, failures, absences, attendance_band, "
        "grade_final_norm, detail) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        rows,
    )
