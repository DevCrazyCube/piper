"""PMData connector: Fitbit time-series (JSON), sleep, wellness/srpe/injury, meal logs.

Per-participant layout inside pmdata.zip:
  pNN/fitbit/{heart_rate,steps,calories,distance,*_active_minutes,sedentary_minutes}.json
  pNN/fitbit/sleep.json, sleep_score.csv
  pNN/pmsys/{wellness,srpe,injury}.csv
  pNN/googledocs/reporting.csv   (meal log)
The big intraday JSON arrays (heart_rate ~100MB/participant) are streamed with ijson.
`participant` is the source-local id (pNN); it gets pseudonymised in Phase 2.
"""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from typing import Any

import ijson

from pipeline.common.config import get_settings
from pipeline.common.dates import normalize_timestamp
from pipeline.common.logging import get_logger
from pipeline.ingest.base import Connector, RawRecord, RunContext, TimeSeriesPoint

log = get_logger("ingest.pmdata")

# Intraday time-series files -> raw.timeseries (metric = file stem).
_TS_METRICS = (
    "heart_rate",
    "steps",
    "calories",
    "distance",
    "lightly_active_minutes",
    "moderately_active_minutes",
    "very_active_minutes",
    "sedentary_minutes",
)

# CSV files -> raw.record (record_type, relative path).
_CSV_RECORDS = {
    "sleep_score": "fitbit/sleep_score.csv",
    "wellness": "pmsys/wellness.csv",
    "srpe": "pmsys/srpe.csv",
    "injury": "pmsys/injury.csv",
    "meal_report": "googledocs/reporting.csv",
}

_PARTICIPANT_RE = re.compile(r"^(p\d+)/")


def _numeric(value: Any) -> float | None:
    if isinstance(value, dict):
        if "bpm" in value:
            return float(value["bpm"])
        if "value" in value:
            return _numeric(value["value"])
        return None
    if value is None or value == "":
        return None
    return float(value)  # may raise ValueError -> caller quarantines


class PMDataConnector(Connector):
    source = "pmdata"
    dataset_file = "pmdata.zip"

    def run(self, ctx: RunContext) -> None:
        path = get_settings().datasets_dir / self.dataset_file
        with zipfile.ZipFile(path) as zf:
            names = set(zf.namelist())
            participants = sorted(
                {m.group(1) for n in names if (m := _PARTICIPANT_RE.match(n))}
            )
            limit = get_settings().pmdata_max_participants
            if limit and limit > 0:
                participants = participants[:limit]
                log.info("pmdata.limited", participants=len(participants), note="testing subset")
            for pid in participants:
                self._ingest_participant(ctx, zf, names, pid)

    def _ingest_participant(
        self, ctx: RunContext, zf: zipfile.ZipFile, names: set[str], pid: str
    ) -> None:
        for metric in _TS_METRICS:
            name = f"{pid}/fitbit/{metric}.json"
            if name in names:
                self._ingest_timeseries(ctx, zf, name, pid, metric)

        sleep_name = f"{pid}/fitbit/sleep.json"
        if sleep_name in names:
            self._ingest_sleep(ctx, zf, sleep_name, pid)

        for record_type, rel in _CSV_RECORDS.items():
            name = f"{pid}/{rel}"
            if name in names:
                self._ingest_csv(ctx, zf, name, pid, record_type)

    def _ingest_timeseries(
        self, ctx: RunContext, zf: zipfile.ZipFile, name: str, pid: str, metric: str
    ) -> None:
        with zf.open(name) as fh:
            for item in ijson.items(fh, "item"):
                try:
                    ts = normalize_timestamp(item["dateTime"])
                    value = _numeric(item.get("value"))
                except (KeyError, ValueError, TypeError) as exc:
                    ctx.quarantine(
                        f"{metric}: {exc}", field="dateTime/value",
                        raw_value=item, record_ref=f"{pid}/{metric}",
                    )
                    continue
                ctx.point(TimeSeriesPoint(participant=pid, metric=metric, ts=ts, value=value))

    def _ingest_sleep(self, ctx: RunContext, zf: zipfile.ZipFile, name: str, pid: str) -> None:
        with zf.open(name) as fh:
            try:
                entries = json.load(fh)
            except json.JSONDecodeError as exc:
                ctx.quarantine(f"sleep json parse: {exc}", record_ref=name)
                return
        for entry in entries:
            payload = {"participant": pid, **entry}
            ctx.record(
                RawRecord(
                    record_type="sleep",
                    payload=payload,
                    natural_key=str(entry.get("logId")) if isinstance(entry, dict) else None,
                )
            )

    def _ingest_csv(
        self, ctx: RunContext, zf: zipfile.ZipFile, name: str, pid: str, record_type: str
    ) -> None:
        with zf.open(name) as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8", errors="replace")
            for row in csv.DictReader(text):
                ctx.record(RawRecord(record_type=record_type, payload={"participant": pid, **row}))
