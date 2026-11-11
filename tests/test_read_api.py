"""The dashboard's encryption figure comes from the identity table, not from a constant.

No database here: `_scalar` is replaced, so these check what the API says for a given
count, not that the count is right.
"""

from __future__ import annotations

import pytest

from pipeline.api import read


def _counts(monkeypatch: pytest.MonkeyPatch, total: int, enveloped: int) -> None:
    def fake(sql: str, default: float = 0) -> float:
        return float(enveloped if "octet_length" in sql else total)

    monkeypatch.setattr(read, "_scalar", fake)


def test_all_identities_enveloped_is_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    _counts(monkeypatch, total=1175, enveloped=1175)
    v = read._identity_vital()
    assert v["value"] == "1175"
    assert v["sub"].startswith("of 1175")
    assert v["tone"] == "ok"


def test_a_short_value_turns_the_figure_bad(monkeypatch: pytest.MonkeyPatch) -> None:
    _counts(monkeypatch, total=10, enveloped=9)
    v = read._identity_vital()
    assert v["value"] == "9"
    assert v["tone"] == "bad"


def test_empty_table_claims_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    _counts(monkeypatch, total=0, enveloped=0)
    v = read._identity_vital()
    assert v["value"] == "0"
    assert "tone" not in v
    assert v["sub"] == "none stored yet"


def test_transport_is_not_shown_as_done() -> None:
    transport = next(s for s in read.STAGES if s["name"] == "Transport")
    assert transport["status"] == "idle"
    assert "planned" in transport["note"]


def test_token_floor_matches_the_cipher() -> None:
    from pipeline.common import crypto

    assert read._MIN_TOKEN_BYTES == crypto._NONCE_BYTES + 16
