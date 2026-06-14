"""Curate the PMData health domain: pseudonymise participants, build curated time-series
(in-DB join), and clean sleep / wellness / meal records out of the raw zone.
"""

from __future__ import annotations

import psycopg

from pipeline.common.crypto import get_cipher
from pipeline.common.dates import normalize_timestamp
from pipeline.common.logging import get_logger
from pipeline.process.pseudonymise import get_or_create_subject
from pipeline.process.util import log_decision, to_bool, to_float, to_int

log = get_logger("curate.health")
_SCOPES = ("sleep", "heart_rate", "activity", "meals")


def curate_pmdata(conn: psycopg.Connection) -> dict[str, int]:
    cipher = get_cipher()
    counts: dict[str, int] = {}
    with conn.cursor() as cur:
        # 1) pseudonymise every participant + seed consent (default granted) ------------
        cur.execute("SELECT DISTINCT participant FROM raw.timeseries WHERE source='pmdata'")
        participants = sorted(r[0] for r in cur.fetchall())
        pids: dict[str, object] = {}
        for p in participants:
            pid = get_or_create_subject(cur, cipher, "pmdata", p)
            pids[p] = pid
            for scope in _SCOPES:
                cur.execute(
                    "INSERT INTO consent.consent (subject_pid, scope) VALUES (%s, %s) "
                    "ON CONFLICT DO NOTHING",
                    (pid, scope),
                )
        counts["subjects"] = len(participants)

        # 2) curated time-series = HOURLY rollups keyed by pseudonymous subject.
        # We deliberately do NOT copy the ~21M per-second heart-rate points verbatim:
        # curated data is analytics-ready and aggregate-by-design (smaller, privacy-friendly).
        # heart_rate -> hourly mean; cumulative metrics (steps/calories/distance/active) -> hourly sum.
        cur.execute(
            """
            INSERT INTO curated.timeseries (subject_pid, metric, ts, value)
            SELECT s.subject_pid,
                   r.metric,
                   time_bucket('1 hour', r.ts) AS ts,
                   CASE WHEN r.metric = 'heart_rate' THEN avg(r.value) ELSE sum(r.value) END
            FROM raw.timeseries r
            JOIN id.subject s ON s.source='pmdata' AND s.source_local_id = r.participant
            GROUP BY s.subject_pid, r.metric, time_bucket('1 hour', r.ts)
            ON CONFLICT (subject_pid, metric, ts) DO NOTHING
            """
        )
        counts["timeseries"] = cur.rowcount
        log_decision(
            cur, stage="curate", source="pmdata",
            decision="curated time-series as HOURLY rollups, not verbatim per-second copy",
            rationale="21M raw HR points -> hourly aggregates: analytics-ready, far smaller, "
                      "and aggregate-by-design supports privacy. HR=mean, cumulative=sum.",
            detail={"hr_agg": "mean", "cumulative_agg": "sum", "bucket": "1 hour"},
        )

        # 3) structured records from the raw zone --------------------------------------
        counts["sleep"] = _curate_sleep(cur, pids)
        counts["wellness"] = _curate_wellness(cur, pids)
        counts["meals"] = _curate_meals(cur, pids)

        log_decision(
            cur,
            stage="curate",
            source="pmdata",
            decision="pseudonymised participants; consent seeded granted-by-default",
            rationale="ADR-0006/0008: pid via app-layer encrypted map; consent drives RLS",
            detail={"subjects": counts["subjects"], "scopes": list(_SCOPES)},
        )
    log.info("curate.pmdata.done", **counts)
    return counts


def _curate_sleep(cur: psycopg.Cursor, pids: dict[str, object]) -> int:
    rows = []
    cur.execute("SELECT payload FROM raw.record WHERE source='pmdata' AND record_type='sleep'")
    for (payload,) in cur.fetchall():
        pid = pids.get(payload.get("participant"))
        if pid is None:
            continue
        summary = (payload.get("levels") or {}).get("summary") or {}

        def _min(stage: str) -> int | None:
            return to_int((summary.get(stage) or {}).get("minutes"))

        try:
            start_ts = normalize_timestamp(payload["startTime"])
            end_ts = normalize_timestamp(payload["endTime"])
            sleep_date = normalize_timestamp(payload["dateOfSleep"]).date()
        except (KeyError, ValueError, TypeError):
            continue
        rows.append(
            (pid, sleep_date, start_ts, end_ts, to_int(payload.get("minutesAsleep")),
             to_int(payload.get("efficiency")), _min("deep"), _min("light"),
             _min("rem"), _min("wake"))
        )
    with cur.connection.cursor() as c2:
        c2.executemany(
            "INSERT INTO curated.sleep (subject_pid, sleep_date, start_ts, end_ts, "
            "minutes_asleep, efficiency, deep_min, light_min, rem_min, wake_min) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            rows,
        )
    return len(rows)


def _curate_wellness(cur: psycopg.Cursor, pids: dict[str, object]) -> int:
    rows = []
    cur.execute("SELECT payload FROM raw.record WHERE source='pmdata' AND record_type='wellness'")
    for (payload,) in cur.fetchall():
        pid = pids.get(payload.get("participant"))
        if pid is None:
            continue
        try:
            ts = normalize_timestamp(payload["effective_time_frame"])
        except (KeyError, ValueError, TypeError):
            continue
        rows.append(
            (pid, ts, to_int(payload.get("fatigue")), to_int(payload.get("mood")),
             to_int(payload.get("readiness")), to_float(payload.get("sleep_duration_h")),
             to_int(payload.get("sleep_quality")), to_int(payload.get("soreness")),
             to_int(payload.get("stress")))
        )
    with cur.connection.cursor() as c2:
        c2.executemany(
            "INSERT INTO curated.wellness (subject_pid, ts, fatigue, mood, readiness, "
            "sleep_duration_h, sleep_quality, soreness, stress) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            rows,
        )
    return len(rows)


def _curate_meals(cur: psycopg.Cursor, pids: dict[str, object]) -> int:
    rows = []
    cur.execute("SELECT payload FROM raw.record WHERE source='pmdata' AND record_type='meal_report'")
    for (payload,) in cur.fetchall():
        pid = pids.get(payload.get("participant"))
        if pid is None:
            continue
        try:
            ts = normalize_timestamp(payload["timestamp"])
        except (KeyError, ValueError, TypeError):
            continue
        rows.append(
            (pid, ts, payload.get("meals"), to_float(payload.get("weight")),
             to_int(payload.get("glasses_of_fluid")), to_bool(payload.get("alcohol_consumed")))
        )
    with cur.connection.cursor() as c2:
        c2.executemany(
            "INSERT INTO curated.meal (subject_pid, ts, meals, weight_kg, fluids, alcohol) "
            "VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            rows,
        )
    return len(rows)
