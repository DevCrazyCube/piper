"""Ingest engine: run provenance, batched idempotent raw writes, and quarantine.

A connector reads a source and emits two kinds of output via the RunContext:
  * structured records  -> raw.record  (JSONB, idempotent by content hash)
  * time-series points  -> raw.timeseries (TimescaleDB hypertable)
Rows that fail validation are sent to ctx.quarantine(...) — never silently dropped
(ADR-0010). The runner opens/closes a meta.pipeline_run row with final counts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

import psycopg
from psycopg.types.json import Json

from pipeline.common.crypto import content_hash
from pipeline.common.db import pg_connection
from pipeline.common.logging import get_logger

_BATCH = 5_000

log = get_logger("ingest")


@dataclass(slots=True)
class RawRecord:
    record_type: str
    payload: dict[str, object]
    natural_key: str | None = None


@dataclass(slots=True)
class TimeSeriesPoint:
    participant: str
    metric: str
    ts: datetime
    value: float | None


@dataclass
class RunContext:
    """Per-run state handed to a connector. Buffers writes and flushes in batches."""

    source: str
    run_id: int
    conn: psycopg.Connection
    rows_in: int = 0
    rows_out: int = 0
    rows_quarantined: int = 0
    _records: list[tuple] = field(default_factory=list)
    _points: list[tuple] = field(default_factory=list)
    _stage_ready: bool = False

    # -- emit API used by connectors --------------------------------------
    def record(self, rec: RawRecord) -> None:
        self.rows_in += 1
        self._records.append(
            (
                self.source,
                rec.record_type,
                rec.natural_key,
                content_hash(rec.payload),
                Json(rec.payload),
                self.run_id,
            )
        )
        if len(self._records) >= _BATCH:
            self._flush_records()

    def point(self, p: TimeSeriesPoint) -> None:
        self.rows_in += 1
        self._points.append((self.source, p.participant, p.metric, p.ts, p.value, self.run_id))
        if len(self._points) >= _BATCH:
            self._flush_points()

    def quarantine(
        self,
        reason: str,
        *,
        field: str | None = None,
        raw_value: object = None,
        record_ref: str | None = None,
    ) -> None:
        self.rows_quarantined += 1
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO meta.quarantine "
                "(run_id, source, record_ref, field, reason, raw_value) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (self.run_id, self.source, record_ref, field, reason,
                 None if raw_value is None else str(raw_value)[:2000]),
            )

    # -- batching ----------------------------------------------------------
    def flush(self) -> None:
        self._flush_records()
        self._flush_points()

    def _flush_records(self) -> None:
        if not self._records:
            return
        with self.conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO raw.record "
                "(source, record_type, natural_key, content_hash, payload, run_id) "
                "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (content_hash) DO NOTHING",
                self._records,
            )
        self.rows_out += len(self._records)
        self._records.clear()

    def _flush_points(self) -> None:
        # High-throughput path: COPY into an unlogged TEMP staging table; the final
        # upsert into the hypertable (commit_timeseries) handles idempotency. COPY is
        # ~100x faster than executemany for the ~20M PMData points.
        if not self._points:
            return
        if not self._stage_ready:
            with self.conn.cursor() as cur:
                cur.execute(
                    "CREATE TEMP TABLE IF NOT EXISTS _ts_stage ("
                    "source text, participant text, metric text, ts timestamptz, "
                    "value double precision, run_id bigint) ON COMMIT DROP"
                )
            self._stage_ready = True
        with self.conn.cursor() as cur:
            with cur.copy(
                "COPY _ts_stage (source, participant, metric, ts, value, run_id) FROM STDIN"
            ) as cp:
                for row in self._points:
                    cp.write_row(row)
        self.rows_out += len(self._points)
        self._points.clear()

    def commit_timeseries(self) -> None:
        """Move staged points into the hypertable, idempotently. Call once at run end."""
        if not self._stage_ready:
            return
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO raw.timeseries (source, participant, metric, ts, value, run_id) "
                "SELECT source, participant, metric, ts, value, run_id FROM _ts_stage "
                "ON CONFLICT (source, participant, metric, ts) DO NOTHING"
            )


class Connector(ABC):
    """A batch source connector. Subclasses set `source` and implement `run`."""

    source: str

    @abstractmethod
    def run(self, ctx: RunContext) -> None: ...


def run_ingest(connector: Connector) -> RunContext:
    """Open a run, drive the connector, finalize provenance. Raises on hard failure."""
    with pg_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO meta.pipeline_run (source, kind) VALUES (%s, 'ingest') RETURNING id",
                (connector.source,),
            )
            run_id = cur.fetchone()[0]  # type: ignore[index]
        conn.commit()

        ctx = RunContext(source=connector.source, run_id=run_id, conn=conn)
        log.info("ingest.start", source=connector.source, run_id=run_id)
        try:
            connector.run(ctx)
            ctx.flush()
            ctx.commit_timeseries()
        except Exception as exc:
            ctx.flush()
            _finalize(conn, ctx, "failed", detail={"error": str(exc)})
            conn.commit()
            log.error("ingest.failed", source=connector.source, run_id=run_id, error=str(exc))
            raise
        _finalize(conn, ctx, "success")
        log.info(
            "ingest.done",
            source=connector.source,
            run_id=run_id,
            rows_in=ctx.rows_in,
            rows_out=ctx.rows_out,
            rows_quarantined=ctx.rows_quarantined,
        )
        return ctx


def _finalize(
    conn: psycopg.Connection, ctx: RunContext, status: str, detail: dict | None = None
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE meta.pipeline_run SET status=%s, finished_at=now(), "
            "rows_in=%s, rows_out=%s, rows_quarantined=%s, detail=%s WHERE id=%s",
            (status, ctx.rows_in, ctx.rows_out, ctx.rows_quarantined,
             Json(detail or {}), ctx.run_id),
        )
