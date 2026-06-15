"""Right to erasure (GDPR Art. 17). Removes a subject across curated + raw + the
pseudonymisation map, then writes a verifiable deletion receipt (sha256 digest).

Deleting the id.subject row destroys the only link back to the real identity, so the
remaining (already-pseudonymous) data cannot be re-identified. Encrypted DB backups fall
under the same obligation — see docs/04-security.md (handled at the backup-rotation layer).
"""

from __future__ import annotations

from uuid import UUID

import psycopg
from psycopg.types.json import Json

from pipeline.common.crypto import content_hash
from pipeline.common.logging import get_logger

log = get_logger("erase")

_CURATED = ("curated.timeseries", "curated.sleep", "curated.wellness", "curated.meal")


def erase_subject(conn: psycopg.Connection, subject_pid: str) -> dict[str, int]:
    pid = str(UUID(subject_pid))  # validate
    counts: dict[str, int] = {}
    with conn.cursor() as cur:
        cur.execute(
            "SELECT source, source_local_id FROM id.subject WHERE subject_pid = %s", (pid,)
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"no subject with pid {pid}")
        source, local_id = row

        for table in _CURATED:
            # Table name is from the trusted _CURATED constant (not user input); value is
            # parameterised. Safe from injection. nosec/noqa document the SAST review.
            cur.execute(f"DELETE FROM {table} WHERE subject_pid = %s", (pid,))  # noqa: S608  # nosec B608
            counts[table] = cur.rowcount

        # Raw zone is keyed by the source-local id (resolved while the map still exists).
        cur.execute(
            "DELETE FROM raw.timeseries WHERE source = %s AND participant = %s",
            (source, local_id),
        )
        counts["raw.timeseries"] = cur.rowcount
        cur.execute(
            "DELETE FROM raw.record WHERE source = %s AND payload->>'participant' = %s",
            (source, local_id),
        )
        counts["raw.record"] = cur.rowcount

        cur.execute("DELETE FROM consent.consent WHERE subject_pid = %s", (pid,))
        counts["consent.consent"] = cur.rowcount
        # Destroy the identity link last (audit trigger logs this DELETE).
        cur.execute("DELETE FROM id.subject WHERE subject_pid = %s", (pid,))
        counts["id.subject"] = cur.rowcount

        digest = content_hash({"subject_pid": pid, "counts": counts})
        cur.execute(
            "INSERT INTO meta.deletion_receipt (subject_pid, counts, digest) "
            "VALUES (%s, %s, %s)",
            (pid, Json(counts), digest),
        )
    log.info("erase.done", subject_pid=pid, **{k.replace(".", "_"): v for k, v in counts.items()})
    return counts
