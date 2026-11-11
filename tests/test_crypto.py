"""App-layer crypto tests. Skipped where the crypto/settings deps aren't installed
(so `unittest` stays green in a bare env); runs fully in the container / CI."""

import base64
import os
import unittest

os.environ.setdefault("PIPER_MASTER_KEY", "")  # avoid .env dependency at import

try:
    from cryptography.exceptions import InvalidTag

    from pipeline.common.config import get_settings
    from pipeline.common.crypto import (
        Cipher,
        aad_for,
        content_hash,
        get_cipher,
        receipt_mac,
        sha256_hex,
    )
    from pipeline.common.errors import ConfigError
    _HAVE = True
except Exception:
    _HAVE = False


@unittest.skipUnless(_HAVE, "cryptography/pydantic not installed")
class TestCrypto(unittest.TestCase):
    def setUp(self) -> None:
        self.cipher = Cipher(os.urandom(32))

    def test_roundtrip(self) -> None:
        pt = b"p01"
        self.assertEqual(self.cipher.decrypt(self.cipher.encrypt(pt)), pt)

    def test_str_roundtrip(self) -> None:
        self.assertEqual(self.cipher.decrypt_str(self.cipher.encrypt_str("teammate-a")), "teammate-a")

    def test_nonce_makes_ciphertext_unique(self) -> None:
        a = self.cipher.encrypt(b"same")
        b = self.cipher.encrypt(b"same")
        self.assertNotEqual(a, b)  # random nonce per call

    def test_wrong_key_fails(self) -> None:
        token = self.cipher.encrypt(b"secret")
        with self.assertRaises(InvalidTag):
            Cipher(os.urandom(32)).decrypt(token)

    def test_bad_key_length_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            Cipher(b"too-short")

    def test_content_hash_stable_and_order_independent(self) -> None:
        self.assertEqual(content_hash({"a": 1, "b": 2}), content_hash({"b": 2, "a": 1}))
        self.assertNotEqual(content_hash({"a": 1}), content_hash({"a": 2}))

    def test_sha256_hex(self) -> None:
        self.assertEqual(len(sha256_hex(b"x")), 64)

    def test_content_hash_decimal_canonical(self) -> None:
        from decimal import Decimal
        self.assertEqual(content_hash({"a": Decimal("1.50")}), content_hash({"a": Decimal("1.5")}))


class _MasterKeyCase(unittest.TestCase):
    """Sets PIPER_MASTER_KEY for one test and puts the old value back afterwards.

    The settings and the per-purpose ciphers are cached, so both caches are cleared
    around every test: a key from one test must never reach the next one.
    """

    master_key: str | None = None  # None = a fresh random 32-byte key per test

    def setUp(self) -> None:
        self._old = os.environ.get("PIPER_MASTER_KEY")
        key = self.master_key
        if key is None:
            key = base64.b64encode(os.urandom(32)).decode()
        os.environ["PIPER_MASTER_KEY"] = key
        self._clear()

    def tearDown(self) -> None:
        if self._old is None:
            os.environ.pop("PIPER_MASTER_KEY", None)
        else:
            os.environ["PIPER_MASTER_KEY"] = self._old
        self._clear()

    @staticmethod
    def _clear() -> None:
        get_settings.cache_clear()
        get_cipher.cache_clear()


@unittest.skipUnless(_HAVE, "crypto/settings deps not installed")
class TestKeySeparation(_MasterKeyCase):
    """Purpose-separated keys (ADR-0008 hardening): one purpose can't decrypt another's."""

    def test_same_purpose_roundtrip(self) -> None:
        token = get_cipher("identity").encrypt(b"p01", aad_for("identity"))
        self.assertEqual(get_cipher("identity").decrypt(token, aad_for("identity")), b"p01")

    def test_purposes_have_distinct_keys(self) -> None:
        token = get_cipher("identity").encrypt(b"p01", aad_for("identity"))
        with self.assertRaises(InvalidTag):
            get_cipher("device").decrypt(token, aad_for("device"))

    def test_aad_mismatch_fails(self) -> None:
        token = get_cipher("identity").encrypt(b"p01", aad_for("identity"))
        with self.assertRaises(InvalidTag):
            get_cipher("identity").decrypt(token, aad_for("device"))

    def test_receipt_mac_is_keyed_and_deterministic(self) -> None:
        payload = {"subject_pid": "x", "counts": {"a": 1}}
        self.assertEqual(receipt_mac(payload), receipt_mac(payload))
        # keyed HMAC != a bare content hash
        self.assertNotEqual(receipt_mac(payload), content_hash(payload))


@unittest.skipUnless(_HAVE, "crypto/settings deps not installed")
class TestMasterKeyMissing(_MasterKeyCase):
    """Without a usable master key nothing is encrypted: it stops with a clear error."""

    master_key = ""

    def test_empty_key_is_refused(self) -> None:
        with self.assertRaises(ConfigError):
            get_cipher("identity")

    def test_receipt_mac_needs_the_key(self) -> None:
        with self.assertRaises(ConfigError):
            receipt_mac({"a": 1})


@unittest.skipUnless(_HAVE, "crypto/settings deps not installed")
class TestMasterKeyWrongLength(_MasterKeyCase):
    master_key = base64.b64encode(b"sixteen-byte-key").decode()

    def test_short_key_is_refused(self) -> None:
        with self.assertRaises(ConfigError):
            get_cipher("identity")


if __name__ == "__main__":
    unittest.main()
