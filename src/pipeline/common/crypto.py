"""Application-layer encryption + hashing (ADR-0008, hardened per audit).

AES-256-GCM with **purpose-separated keys** derived from the master key via HKDF, so a
single ciphertext class (identity map / device secrets / receipt MACs) can't be swapped
or cross-decrypted, and so one leaked key doesn't compromise every purpose. The master
key is supplied at runtime from the environment and held only in memory — it never
transits SQL and never touches the database.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
from functools import lru_cache
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from pipeline.common.config import get_settings
from pipeline.common.errors import ConfigError

_NONCE_BYTES = 12  # GCM standard


class Cipher:
    """AES-256-GCM authenticated encryption. Token layout: nonce(12) || ciphertext+tag.

    Always pass `aad` (additional authenticated data) to bind a ciphertext to its
    context (e.g. b"identity") so blobs can't be moved between columns/tables.
    """

    def __init__(self, key: bytes) -> None:
        if len(key) != 32:
            raise ConfigError(f"AES-256 key must be 32 bytes, got {len(key)}")
        self._aead = AESGCM(key)

    def encrypt(self, plaintext: bytes, aad: bytes | None = None) -> bytes:
        nonce = os.urandom(_NONCE_BYTES)
        return nonce + self._aead.encrypt(nonce, plaintext, aad)

    def decrypt(self, token: bytes, aad: bytes | None = None) -> bytes:
        nonce, ct = token[:_NONCE_BYTES], token[_NONCE_BYTES:]
        return self._aead.decrypt(nonce, ct, aad)

    def encrypt_str(self, text: str, aad: bytes | None = None) -> str:
        return base64.b64encode(self.encrypt(text.encode(), aad)).decode()

    def decrypt_str(self, token_b64: str, aad: bytes | None = None) -> str:
        return self.decrypt(base64.b64decode(token_b64), aad).decode()


def _master_key() -> bytes:
    raw = get_settings().master_key.get_secret_value()
    if not raw:
        raise ConfigError("PIPER_MASTER_KEY is not set (see .env.example to generate one)")
    try:
        key = base64.b64decode(raw)
    except (ValueError, binascii.Error) as exc:
        raise ConfigError("PIPER_MASTER_KEY is not valid base64") from exc
    if len(key) != 32:
        raise ConfigError("PIPER_MASTER_KEY must decode to 32 bytes")
    return key


def _derive_key(purpose: str) -> bytes:
    """HKDF-SHA256 subkey for a purpose label — separates identity/device/receipt keys."""
    return HKDF(algorithm=SHA256(), length=32, salt=None, info=f"piper:{purpose}".encode()).derive(
        _master_key()
    )


@lru_cache
def get_cipher(purpose: str = "identity") -> Cipher:
    """Cipher bound to a purpose (its own derived key). Use the same purpose as AAD."""
    return Cipher(_derive_key(purpose))


def aad_for(purpose: str) -> bytes:
    return f"piper:{purpose}".encode()


def receipt_mac(payload: object) -> str:
    """Keyed HMAC-SHA256 over a receipt (tamper-evident, unlike a bare hash)."""
    key = _derive_key("receipt")
    canonical = _canonical_json(payload).encode()
    return hmac.new(key, canonical, hashlib.sha256).hexdigest()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_hash(payload: object) -> str:
    """Stable hash of a payload — the idempotency key for raw records.

    Canonicalises types first (Decimal/float/datetime/bytes) so the same logical record
    hashes identically across runs even if a library returns a different concrete type.
    """
    return sha256_hex(_canonical_json(payload).encode())


def _canonical_json(payload: object) -> str:
    return json.dumps(_canonical(payload), sort_keys=True, separators=(",", ":"))


def _canonical(value: Any) -> Any:
    # Normalise numbers/dates/bytes to stable string forms; recurse into containers.
    import datetime as _dt
    import decimal as _dec

    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return value
    if isinstance(value, float):
        return format(value, ".12g")  # 1.0 and 1 differ; but stable per value
    if isinstance(value, _dec.Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return base64.b64encode(bytes(value)).decode()
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    return str(value)
