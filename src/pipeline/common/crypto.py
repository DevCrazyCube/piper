"""Application-layer encryption + hashing (ADR-0008).

AES-256-GCM, with the key supplied at runtime from the environment and held only in
memory — it never transits SQL and never touches the database (unlike pgcrypto). Used
to encrypt the pseudonymisation map and other most-sensitive fields *before* INSERT.
Content hashing (SHA-256) is keyless and drives idempotent ingest + raw-payload integrity.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from pipeline.common.config import get_settings
from pipeline.common.errors import ConfigError

_NONCE_BYTES = 12  # GCM standard


class Cipher:
    """AES-256-GCM authenticated encryption. Token layout: nonce(12) || ciphertext+tag."""

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


def get_cipher() -> Cipher:
    """Build the cipher from the runtime master key (base64 of 32 bytes)."""
    raw = get_settings().master_key.get_secret_value()
    if not raw:
        raise ConfigError("AEGIS_MASTER_KEY is not set (see .env.example to generate one)")
    try:
        key = base64.b64decode(raw)
    except (ValueError, base64.binascii.Error) as exc:  # type: ignore[attr-defined]
        raise ConfigError("AEGIS_MASTER_KEY is not valid base64") from exc
    return Cipher(key)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_hash(payload: object) -> str:
    """Stable hash of a JSON-serializable payload — the idempotency key for raw records."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256_hex(canonical.encode())
