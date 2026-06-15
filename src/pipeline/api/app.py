"""FastAPI webhook ingest. Teammates' auto-export app POSTs signed health JSON here;
samples land in the raw zone (source 'wearable-live'), pseudonymous like every source.

Auth headers (see api/auth.py):
  X-Piper-Device, X-Piper-Timestamp, X-Piper-Nonce, X-Piper-Signature
"""

from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, Request

from pipeline.api.auth import verify
from pipeline.api.models import IngestRequest
from pipeline.common.crypto import aad_for, get_cipher
from pipeline.common.db import pg_connection
from pipeline.common.logging import get_logger
from pipeline.process.pseudonymise import get_or_create_subject

log = get_logger("api")
app = FastAPI(title="Piper Ingest API", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/ingest")
async def ingest(
    request: Request,
    x_piper_device: str = Header(...),
    x_piper_timestamp: str = Header(...),
    x_piper_nonce: str = Header(...),
    x_piper_signature: str = Header(...),
) -> dict[str, int | str]:
    body = await request.body()
    # Generic 401 for the client; precise reason only in server logs (no auth oracle).
    unauthorized = HTTPException(status_code=401, detail="unauthorized")

    with pg_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT enc_secret, source, source_local_id FROM meta.device WHERE device_id = %s",
            (x_piper_device,),
        )
        row = cur.fetchone()
        if row is None:
            log.warning("api.unknown_device", device=x_piper_device)
            raise unauthorized
        enc_secret, source, source_local_id = row
        secret = get_cipher("device").decrypt(bytes(enc_secret), aad_for("device"))

        ok, reason = verify(secret, x_piper_timestamp, x_piper_nonce, body, x_piper_signature)
        if not ok:
            log.warning("api.auth_failed", device=x_piper_device, reason=reason)
            raise unauthorized

        # Replay protection, authoritative + cross-worker: unique-insert the nonce.
        cur.execute(
            "INSERT INTO meta.webhook_nonce (nonce) VALUES (%s) ON CONFLICT DO NOTHING "
            "RETURNING nonce",
            (x_piper_nonce,),
        )
        if cur.fetchone() is None:
            log.warning("api.replay", device=x_piper_device)
            raise unauthorized

        # Validate payload (pydantic) -> 422 on malformed.
        try:
            payload = IngestRequest.model_validate_json(body)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="invalid payload") from exc
        if payload.device_id != x_piper_device:
            raise unauthorized

        pid = get_or_create_subject(cur, get_cipher("identity"), source, source_local_id)
        rows = [
            (source, source_local_id, s.metric, s.ts, s.value, None) for s in payload.samples
        ]
        cur.executemany(
            "INSERT INTO raw.timeseries (source, participant, metric, ts, value, run_id) "
            "VALUES (%s,%s,%s,%s,%s,%s) "
            "ON CONFLICT (source, participant, metric, ts) DO NOTHING",
            rows,
        )

    log.info("api.ingest", device=x_piper_device, subject=str(pid), accepted=len(payload.samples))
    return {"accepted": len(payload.samples), "subject_pid": str(pid)}
