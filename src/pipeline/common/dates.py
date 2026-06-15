"""Timestamp normalization — stdlib only (unit-testable without the stack).

PMData alone mixes: '2019-11-01 00:00:08' (naive, space), '...T10:15:00.000' (ISO, no tz),
'2019-11-01T10:15:00Z' / '2019-11-15T09:10:38.176Z' (ISO + Z), and the meal log uses
'14/11/2019' / '14/11/2019 23:38:28' (DD/MM/YYYY). Open Food Facts adds UNIX epochs.
Everything is normalized to a timezone-aware UTC datetime; values with no recognizable
format raise ValueError so the caller can quarantine them.

CAVEAT: slash dates are assumed **day-first** (DD/MM/YYYY — correct for the PMData meal
log, which is European). An ambiguous value like '02/03/2019' is therefore read as
2 March, not 2 February — it does NOT raise. Only use this on day-first sources; a
month-first source would need its own parser/flag.
"""

from __future__ import annotations

from datetime import datetime, timezone

# Non-ISO fallbacks, tried in order. (ISO 8601 is handled by fromisoformat first.)
_FALLBACK_FORMATS = (
    "%d/%m/%Y %H:%M:%S",  # 14/11/2019 23:38:28  (meal log timestamp)
    "%d/%m/%Y",           # 14/11/2019           (meal log date)
    "%Y-%m-%d %H:%M:%S",  # 2019-11-01 00:00:08  (Fitbit space-separated)
    "%Y-%m-%d",           # 2019-11-01
)

# Plausible epoch-seconds window (2001-09..2033) to avoid mis-reading IDs as dates.
_EPOCH_MIN = 1_000_000_000
_EPOCH_MAX = 2_000_000_000


def normalize_timestamp(value: object) -> datetime:
    """Return a timezone-aware UTC datetime for a messy timestamp value.

    Naive inputs are assumed to be UTC. Raises ValueError on anything unparseable.
    """
    if isinstance(value, datetime):
        return _as_utc(value)

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        secs = float(value)
        if _EPOCH_MIN <= secs <= _EPOCH_MAX:
            return datetime.fromtimestamp(secs, tz=timezone.utc)
        raise ValueError(f"numeric timestamp out of epoch range: {value!r}")

    if not isinstance(value, str):
        raise ValueError(f"unsupported timestamp type: {type(value).__name__}")

    text = value.strip()
    if not text:
        raise ValueError("empty timestamp")

    # Try ISO 8601 first (handles 'Z', offsets, and fractional seconds on 3.11+).
    try:
        return _as_utc(datetime.fromisoformat(text.replace("Z", "+00:00")))
    except ValueError:
        pass

    for fmt in _FALLBACK_FORMATS:
        try:
            return _as_utc(datetime.strptime(text, fmt))
        except ValueError:
            continue

    raise ValueError(f"unrecognized timestamp format: {value!r}")


def _as_utc(dt: datetime) -> datetime:
    """Attach UTC to naive datetimes; convert aware ones to UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
