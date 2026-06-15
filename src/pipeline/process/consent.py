"""Consent enforcement (GDPR Art. 7). Granting/revoking a scope updates consent.consent
AND enforces it: revoking removes the curated data derived under that scope (scoped erasure),
so revocation has real effect rather than being a flag nobody reads.
"""

from __future__ import annotations

from uuid import UUID

import psycopg

from pipeline.common.logging import get_logger

log = get_logger("consent")

# scope -> SQL that removes the curated data covered by that scope.
_SCOPE_DELETE: dict[str, str] = {
    "sleep": "DELETE FROM curated.sleep WHERE subject_pid = %s",
    "meals": "DELETE FROM curated.meal WHERE subject_pid = %s",
    "heart_rate": "DELETE FROM curated.timeseries WHERE subject_pid = %s AND metric = 'heart_rate'",
    "activity": (
        "DELETE FROM curated.timeseries WHERE subject_pid = %s AND metric IN "
        "('steps','calories','distance','lightly_active_minutes',"
        "'moderately_active_minutes','very_active_minutes','sedentary_minutes')"
    ),
}
SCOPES = tuple(_SCOPE_DELETE) + ("grades", "attendance")


def set_consent(conn: psycopg.Connection, subject_pid: str, scope: str, status: str) -> int:
    pid = str(UUID(subject_pid))
    if scope not in SCOPES:
        raise ValueError(f"unknown scope '{scope}'. Choices: {', '.join(SCOPES)}")
    if status not in ("granted", "revoked"):
        raise ValueError("status must be 'granted' or 'revoked'")

    removed = 0
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO consent.consent (subject_pid, scope, status, updated_at) "
            "VALUES (%s, %s, %s, now()) "
            "ON CONFLICT (subject_pid, scope) DO UPDATE SET status = EXCLUDED.status, updated_at = now()",
            (pid, scope, status),
        )
        if status == "revoked" and scope in _SCOPE_DELETE:
            cur.execute(_SCOPE_DELETE[scope], (pid,))
            removed = cur.rowcount
    log.info("consent.set", subject_pid=pid, scope=scope, status=status, curated_removed=removed)
    return removed
