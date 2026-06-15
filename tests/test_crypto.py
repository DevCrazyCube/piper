"""App-layer crypto tests. Skipped where the crypto/settings deps aren't installed
(so `unittest` stays green in a bare env); runs fully in the container / CI."""

import os
import unittest

os.environ.setdefault("PIPER_MASTER_KEY", "")  # avoid .env dependency at import

try:
    from cryptography.exceptions import InvalidTag

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


@unittest.skipUnless(_HAVE, "crypto/settings deps not installed")
class TestKeySeparation(unittest.TestCase):
    """Purpose-separated keys (ADR-0008 hardening): one purpose can't decrypt another's."""

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


if __name__ == "__main__":
    unittest.main()
