"""UCI Student Performance connector.

student+performance.zip contains a *nested* student.zip, which holds the two
semicolon-delimited files student-mat.csv and student-por.csv (Mathematics + Portuguese).
Each row is landed raw, tagged with its subject; the cross-file student dedup/merge and
the encoding/type cleanup happen in Phase 2. Encoding is read with errors='replace' so the
known artifacts (e.g. â€") survive into the raw zone rather than crashing ingest.
"""

from __future__ import annotations

import csv
import io
import zipfile

from pipeline.common.config import get_settings
from pipeline.ingest.base import Connector, RawRecord, RunContext

_INNER_FILES = {"mat": "student-mat.csv", "por": "student-por.csv"}


class UCIPerformanceConnector(Connector):
    source = "uci-performance"
    dataset_file = "student+performance.zip"

    def run(self, ctx: RunContext) -> None:
        path = get_settings().datasets_dir / self.dataset_file
        with zipfile.ZipFile(path) as outer:
            inner_bytes = outer.read("student.zip")
        with zipfile.ZipFile(io.BytesIO(inner_bytes)) as inner:
            for subject, fname in _INNER_FILES.items():
                self._ingest_file(ctx, inner, fname, subject)

    def _ingest_file(
        self, ctx: RunContext, zf: zipfile.ZipFile, fname: str, subject: str
    ) -> None:
        with zf.open(fname) as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8", errors="replace")
            reader = csv.DictReader(text, delimiter=";")
            for line_no, row in enumerate(reader, start=2):
                if row is None or all(v is None for v in row.values()):
                    ctx.quarantine("empty/malformed row", record_ref=f"{fname}:{line_no}")
                    continue
                ctx.record(
                    RawRecord(
                        record_type="grade",
                        payload={"subject": subject, **row},
                        natural_key=f"{subject}:{line_no}",
                    )
                )
