"""Connector parsing tests against synthetic in-memory fixtures (no DB).

Uses a FakeContext that records emitted points/records/quarantines, so we can assert the
*parsing* behaviour of the connectors without a database. Skipped where ingest deps
(ijson/psycopg) aren't installed; runs in the container / CI.
"""

import io
import json
import unittest
import zipfile

try:
    from pipeline.ingest.pmdata import PMDataConnector
    from pipeline.ingest.uci_performance import UCIPerformanceConnector
    _HAVE = True
except Exception:
    _HAVE = False


class FakeCtx:
    def __init__(self) -> None:
        self.points: list = []
        self.records: list = []
        self.quarantined: list = []

    def point(self, p) -> None:
        self.points.append(p)

    def record(self, r) -> None:
        self.records.append(r)

    def quarantine(self, reason, **kw) -> None:
        self.quarantined.append((reason, kw))


def _zip(name: str, data: bytes) -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(name, data)
    buf.seek(0)
    return zipfile.ZipFile(buf)


@unittest.skipUnless(_HAVE, "ingest deps (ijson/psycopg) not installed")
class TestPMDataParsing(unittest.TestCase):
    def test_heart_rate_points_extracted(self) -> None:
        # mixes the messy date formats + a dict {bpm,...} value
        data = json.dumps([
            {"dateTime": "2019-11-01 00:00:08", "value": {"bpm": 70, "confidence": 2}},
            {"dateTime": "2019-11-01 00:00:13", "value": {"bpm": 69}},
        ]).encode()
        zf = _zip("p01/fitbit/heart_rate.json", data)
        ctx = FakeCtx()
        PMDataConnector()._ingest_timeseries(ctx, zf, "p01/fitbit/heart_rate.json", "p01", "heart_rate")
        self.assertEqual(len(ctx.points), 2)
        self.assertEqual(ctx.points[0].value, 70.0)
        self.assertEqual(ctx.points[0].metric, "heart_rate")
        self.assertEqual(ctx.points[0].participant, "p01")

    def test_bad_timestamp_is_quarantined_not_dropped(self) -> None:
        data = json.dumps([{"dateTime": "not-a-date", "value": {"bpm": 70}}]).encode()
        zf = _zip("p01/fitbit/heart_rate.json", data)
        ctx = FakeCtx()
        PMDataConnector()._ingest_timeseries(ctx, zf, "p01/fitbit/heart_rate.json", "p01", "heart_rate")
        self.assertEqual(len(ctx.points), 0)
        self.assertEqual(len(ctx.quarantined), 1)

    def test_csv_record_carries_participant(self) -> None:
        csv = b"timestamp,overall_score\n2019-11-01T10:15:00Z,82\n"
        zf = _zip("p01/fitbit/sleep_score.csv", csv)
        ctx = FakeCtx()
        PMDataConnector()._ingest_csv(ctx, zf, "p01/fitbit/sleep_score.csv", "p01", "sleep_score")
        self.assertEqual(len(ctx.records), 1)
        self.assertEqual(ctx.records[0].payload["participant"], "p01")
        self.assertEqual(ctx.records[0].record_type, "sleep_score")


@unittest.skipUnless(_HAVE, "ingest deps not installed")
class TestUCIPerformanceParsing(unittest.TestCase):
    def test_semicolon_csv_parsed_with_subject_tag(self) -> None:
        csv = b'school;sex;age;G3\n"GP";"F";18;"6"\n"MS";"M";17;9\n'
        zf = _zip("student-mat.csv", csv)
        ctx = FakeCtx()
        UCIPerformanceConnector()._ingest_file(ctx, zf, "student-mat.csv", "mat")
        self.assertEqual(len(ctx.records), 2)
        self.assertEqual(ctx.records[0].payload["subject"], "mat")
        self.assertEqual(ctx.records[0].payload["school"], "GP")


if __name__ == "__main__":
    unittest.main()
