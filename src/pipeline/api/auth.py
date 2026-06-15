"""Webhook authentication: per-device HMAC-SHA256 over (timestamp.nonce.body) with a
freshness window + nonce replay cache. Matches docs/04-security.md (API key + HMAC + nonce).
"""

from __future__ import annotations

import hashlib
import hmac
import time
from collections import OrderedDict

WINDOW_SECONDS = 300  # reject stamps older/newer than 5 min
_NONCE_TTL = 600
_seen_nonces: "OrderedDict[str, float]" = OrderedDict()


def expected_signature(secret: bytes, timestamp: str, nonce: str, body: bytes) -> str:
    msg = timestamp.encode() + b"." + nonce.encode() + b"." + body
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()


def verify(secret: bytes, timestamp: str, nonce: str, body: bytes, signature: str) -> tuple[bool, str]:
    """Return (ok, reason). Constant-time signature compare; window + replay checks."""
    now = time.time()
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False, "bad timestamp"
    if abs(now - ts) > WINDOW_SECONDS:
        return False, "stale timestamp"
    if not nonce:
        return False, "missing nonce"
    _evict(now)
    if nonce in _seen_nonces:
        return False, "replayed nonce"
    if not hmac.compare_digest(expected_signature(secret, timestamp, nonce, body), signature or ""):
        return False, "bad signature"
    _seen_nonces[nonce] = now
    return True, "ok"


def _evict(now: float) -> None:
    while _seen_nonces:
        nonce, seen = next(iter(_seen_nonces.items()))
        if now - seen > _NONCE_TTL:
            _seen_nonces.popitem(last=False)
        else:
            break
