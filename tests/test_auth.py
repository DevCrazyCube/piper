"""Webhook HMAC auth tests (pure stdlib — runs anywhere)."""

import time
import unittest

from pipeline.api.auth import expected_signature, verify


class TestAuth(unittest.TestCase):
    def setUp(self) -> None:
        self.secret = b"super-secret-key"
        self.body = b'{"device_id":"d1","samples":[]}'
        self.ts = str(int(time.time()))

    def _sig(self, nonce: str) -> str:
        return expected_signature(self.secret, self.ts, nonce, self.body)

    def test_valid_signature_accepted(self) -> None:
        ok, reason = verify(self.secret, self.ts, "n-ok-1", self.body, self._sig("n-ok-1"))
        self.assertTrue(ok, reason)

    def test_tampered_body_rejected(self) -> None:
        sig = self._sig("n-tamper")
        ok, reason = verify(self.secret, self.ts, "n-tamper", b'{"tampered":true}', sig)
        self.assertFalse(ok)
        self.assertEqual(reason, "bad signature")

    def test_wrong_secret_rejected(self) -> None:
        sig = self._sig("n-wrong")
        ok, _ = verify(b"other-secret", self.ts, "n-wrong", self.body, sig)
        self.assertFalse(ok)

    def test_stale_timestamp_rejected(self) -> None:
        old = str(int(time.time()) - 99_999)
        sig = expected_signature(self.secret, old, "n-stale", self.body)
        ok, reason = verify(self.secret, old, "n-stale", self.body, sig)
        self.assertFalse(ok)
        self.assertEqual(reason, "stale timestamp")

    def test_replayed_nonce_rejected(self) -> None:
        nonce = "n-replay"
        sig = self._sig(nonce)
        ok1, _ = verify(self.secret, self.ts, nonce, self.body, sig)
        ok2, reason = verify(self.secret, self.ts, nonce, self.body, sig)
        self.assertTrue(ok1)
        self.assertFalse(ok2)
        self.assertEqual(reason, "replayed nonce")


if __name__ == "__main__":
    unittest.main()
