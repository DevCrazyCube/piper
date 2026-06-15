"""Right to erasure (GDPR Art. 17). Removes a subject across curated + raw + the
pseudonymisation map + quarantine + device registry, then writes a deletion receipt
authenticated with a keyed HMAC (tamper-evident, not just a bare hash).

Deleting the id.subject row destroys the link back to the real identity, so the remaining
(already-pseudonymous) data cannot be re-identified. Existing encrypted backups are NOT
retroactively purged — they age out under the retention/rotation policy (documented honestly
in docs/05-compliance.md), since per-row backup editing is impractical.
"""

from __future__ import annotations

from uuid import UUID

import psycopg
from psycopg import sql
from psycopg.types.json import Json

from pipeline.common.crypto import receipt_mac
from pipeline.common.logging import get_logger

log = get_logger("erase")

# (schema, table) deleted by subject_pid. Identifiers are composed via sql.Identifier.
_CURATED = (("curated", "timeseries"), ("curated", "sleep"),
            ("curated", "wellness"), ("curated", "meal"))


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

        for schema, table in _CURATED:
            cur.execute(
                sql.SQL("DELETE FROM {}.{} WHERE subject_pid = %s").format(
                    sql.Identifier(schema), sql.Identifier(table)),
                (pid,),
            )
            counts[f"{schema}.{table}"] = cur.rowcount

        # Raw zone + quarantine + device registry are keyed by the source-local id.
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
        cur.execute(
            "DELETE FROM meta.quarantine WHERE source = %s AND raw_value LIKE %s",
            (source, f"%{local_id}%"),
        )
        counts["meta.quarantine"] = cur.rowcount
        cur.execute(
            "DELETE FROM meta.device WHERE source = %s AND source_local_id = %s",
            (source, local_id),
        )
        counts["meta.device"] = cur.rowcount

        cur.execute("DELETE FROM consent.consent WHERE subject_pid = %s", (pid,))
        counts["consent.consent"] = cur.rowcount
        # Destroy the identity link last (audit trigger logs this DELETE).
        cur.execute("DELETE FROM id.subject WHERE subject_pid = %s", (pid,))
        counts["id.subject"] = cur.rowcount

        digest = receipt_mac({"subject_pid": pid, "counts": counts})
        cur.execute(
            "INSERT INTO meta.deletion_receipt (subject_pid, counts, digest) "
            "VALUES (%s, %s, %s)",
            (pid, Json(counts), digest),
        )
    log.info("erase.done", subject_pid=pid, **{k.replace(".", "_"): v for k, v in counts.items()})
    return counts
