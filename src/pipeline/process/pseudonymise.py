"""Pseudonymisation: map a source-local identity to a random subject_pid.

The real identity is encrypted at the application layer (AES-256-GCM, key from env —
ADR-0008) before it ever reaches the DB, so id.subject stores only ciphertext + the pid.
"""

from __future__ import annotations

from uuid import UUID

import psycopg

from pipeline.common.crypto import Cipher


def get_or_create_subject(
    cur: psycopg.Cursor, cipher: Cipher, source: str, local_id: str
) -> UUID:
    cur.execute(
        "SELECT subject_pid FROM id.subject WHERE source = %s AND source_local_id = %s",
        (source, local_id),
    )
    row = cur.fetchone()
    if row is not None:
        return row[0]
    enc = cipher.encrypt(local_id.encode())
    cur.execute(
        "INSERT INTO id.subject (source, source_local_id, enc_identity) "
        "VALUES (%s, %s, %s) RETURNING subject_pid",
        (source, local_id, enc),
    )
    return cur.fetchone()[0]  # type: ignore[index]
