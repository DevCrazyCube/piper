"""The five cross-source analytics queries (aggregate-only, domain-scoped)."""

from __future__ import annotations

from dataclasses import dataclass

import psycopg

K_ANON = 3  # minimum group size for any per-group result


@dataclass(frozen=True)
class Query:
    key: str
    title: str
    domain: str
    sql: str


QUERIES: list[Query] = [
    Query(
        "q1", "Average & range of daily active minutes", "health",
        """
        WITH daily AS (
            SELECT subject_pid, time_bucket('1 day', ts) AS d, sum(value) AS active_min
            FROM curated.timeseries
            WHERE metric IN ('lightly_active_minutes','moderately_active_minutes','very_active_minutes')
            GROUP BY subject_pid, d
        )
        SELECT round(avg(active_min)::numeric, 1) AS avg_daily_active_min,
               round(min(active_min)::numeric, 1) AS min_day,
               round(max(active_min)::numeric, 1) AS max_day,
               count(DISTINCT subject_pid)        AS n_subjects
        FROM daily
        HAVING count(DISTINCT subject_pid) >= %(k)s
        """,
    ),
    Query(
        "q2", "Weekly activity-minutes cohort trend", "health",
        """
        WITH daily AS (
            SELECT subject_pid, time_bucket('1 day', ts) AS d, sum(value) AS active_min
            FROM curated.timeseries
            WHERE metric IN ('lightly_active_minutes','moderately_active_minutes','very_active_minutes')
            GROUP BY subject_pid, d
        )
        SELECT time_bucket('7 days', d, TIMESTAMPTZ '2000-01-03')::date AS week,
               round(avg(active_min)::numeric, 1)                       AS avg_active_min,
               count(DISTINCT subject_pid)                              AS n_subjects
        FROM daily
        GROUP BY week
        HAVING count(DISTINCT subject_pid) >= %(k)s
        ORDER BY week
        LIMIT 12
        """,
    ),
    Query(
        "q3", "Study time vs academic outcome", "academic",
        """
        SELECT study_time,
               round(avg(grade_final_norm)::numeric, 3) AS avg_grade_norm,
               count(*)                                 AS n_students
        FROM curated.student_academic
        WHERE origin = 'uci-performance' AND study_time IS NOT NULL AND grade_final_norm IS NOT NULL
        GROUP BY study_time
        HAVING count(*) >= %(k)s
        ORDER BY study_time
        """,
    ),
    Query(
        "q4", "Sleep vs activity correlation (cohort)", "health",
        """
        WITH daily_steps AS (
            SELECT subject_pid, time_bucket('1 day', ts) AS d, sum(value) AS steps
            FROM curated.timeseries
            WHERE metric = 'steps'
            GROUP BY subject_pid, d
        ),
        per_subject AS (
            SELECT s.subject_pid,
                   avg(s.minutes_asleep) AS avg_sleep_min,
                   (SELECT avg(steps) FROM daily_steps ds
                     WHERE ds.subject_pid = s.subject_pid) AS avg_steps
            FROM curated.sleep s
            GROUP BY s.subject_pid
        )
        SELECT round(corr(avg_sleep_min, avg_steps)::numeric, 3) AS corr_sleep_steps,
               count(*) AS n_subjects
        FROM per_subject
        WHERE avg_steps IS NOT NULL AND avg_sleep_min IS NOT NULL
        HAVING count(*) >= %(k)s
        """,
    ),
    Query(
        "q5", "Cross-institutional grade distribution", "academic",
        """
        SELECT origin,
               round(avg(grade_final_norm)::numeric, 3)         AS avg_grade_norm,
               round(stddev_pop(grade_final_norm)::numeric, 3)  AS sd,
               count(*)                                         AS n_students
        FROM curated.student_academic
        WHERE grade_final_norm IS NOT NULL
        GROUP BY origin
        HAVING count(*) >= %(k)s
        ORDER BY origin
        """,
    ),
]


def run_query(conn: psycopg.Connection, q: Query) -> tuple[list[str], list[tuple]]:
    with conn.cursor() as cur:
        cur.execute(q.sql, {"k": K_ANON})
        cols = [d.name for d in cur.description]  # type: ignore[union-attr]
        return cols, cur.fetchall()
