"""Tests for timestamp normalization (runnable with stdlib unittest)."""

import unittest
from datetime import datetime, timezone

from pipeline.common.dates import normalize_timestamp


class TestNormalizeTimestamp(unittest.TestCase):
    def test_fitbit_space_separated_naive_is_utc(self) -> None:
        dt = normalize_timestamp("2019-11-01 00:00:08")
        self.assertEqual(dt, datetime(2019, 11, 1, 0, 0, 8, tzinfo=timezone.utc))

    def test_iso_with_millis_no_tz(self) -> None:
        dt = normalize_timestamp("2019-11-01T10:15:00.000")
        self.assertEqual(dt, datetime(2019, 11, 1, 10, 15, 0, tzinfo=timezone.utc))

    def test_iso_zulu(self) -> None:
        dt = normalize_timestamp("2019-11-01T10:15:00Z")
        self.assertEqual(dt.tzinfo, timezone.utc)
        self.assertEqual(dt.hour, 10)

    def test_iso_millis_zulu(self) -> None:
        dt = normalize_timestamp("2019-11-15T09:10:38.176Z")
        self.assertEqual(dt.year, 2019)
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_meal_log_ddmmyyyy_with_time(self) -> None:
        dt = normalize_timestamp("14/11/2019 23:38:28")
        self.assertEqual(dt, datetime(2019, 11, 14, 23, 38, 28, tzinfo=timezone.utc))

    def test_meal_log_ddmmyyyy_date_only(self) -> None:
        dt = normalize_timestamp("15/11/2019")
        self.assertEqual(dt, datetime(2019, 11, 15, 0, 0, 0, tzinfo=timezone.utc))

    def test_unix_epoch_seconds(self) -> None:
        dt = normalize_timestamp(1572566408)  # 2019-11-01
        self.assertEqual(dt.year, 2019)

    def test_unparseable_raises(self) -> None:
        with self.assertRaises(ValueError):
            normalize_timestamp("not a date")

    def test_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            normalize_timestamp("   ")

    def test_id_like_number_not_treated_as_date(self) -> None:
        # A sleep-log id like 24475133162 is out of the epoch window -> rejected.
        with self.assertRaises(ValueError):
            normalize_timestamp(24475133162)


if __name__ == "__main__":
    unittest.main()
