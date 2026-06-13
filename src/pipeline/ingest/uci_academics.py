"""UCI Student Academics connector — ARFF (Weka) format.

student+academics+performance.zip holds Sapfile1.arff: all-categorical attributes with
exam-performance bands (Best/Vg/Good/Pass/Fail), attendance (Good/Average/Poor), etc. —
a completely different schema/scale from the UCI Performance set, which is why harmonising
the two is a real Phase-2 task (ADR-0009, academic domain). Here we just land each row raw.
"""

from __future__ import annotations

import io
import zipfile

from pipeline.common.arff import read_rows
from pipeline.common.config import get_settings
from pipeline.ingest.base import Connector, RawRecord, RunContext

_ARFF_NAME = "Sapfile1.arff"


class UCIAcademicsConnector(Connector):
    source = "uci-academics"

    def run(self, ctx: RunContext) -> None:
        path = get_settings().datasets_dir / "student+academics+performance.zip"
        with zipfile.ZipFile(path) as zf:
            with zf.open(_ARFF_NAME) as fh:
                text = io.TextIOWrapper(fh, encoding="utf-8", errors="replace")
                for line_no, row in enumerate(read_rows(text), start=1):
                    ctx.record(
                        RawRecord(
                            record_type="academic",
                            payload=row,
                            natural_key=f"sap:{line_no}",
                        )
                    )
