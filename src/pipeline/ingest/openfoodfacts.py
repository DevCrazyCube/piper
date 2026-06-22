"""Open Food Facts connector — nutrition reference (minimised subset).

food.parquet is ~7GB and 150+ columns. Per GDPR data minimisation we load only a small
column subset, and because this is a *reference* table (not per-subject data) we cap the
number of products ingested for Phase 1 and LOG the cap (no silent truncation — ADR/quality
rule). Scanned lazily with polars so we never materialise the whole file.
"""

from __future__ import annotations

import polars as pl

from pipeline.common.config import get_settings
from pipeline.common.logging import get_logger
from pipeline.ingest.base import Connector, RawRecord, RunContext

log = get_logger("ingest.openfoodfacts")

# Minimised, relevant columns (data minimisation). Only those present are used.
# Nutrition lives in a nested `nutriments` List(Struct{name,value,'100g',unit,...}) — we keep
# the whole nested column raw; Phase 2 flattens energy-kcal/fat/sugar/etc. out of it.
_DESIRED = [
    "code",
    "product_name",
    "brands",
    "categories_tags",
    "nutriscore_grade",
    "nutriscore_score",
    "nutrition_data_per",
    "nutriments",
    "countries_tags",
]

_LIMIT = 50_000  # reference-table seed size for Phase 1


class OpenFoodFactsConnector(Connector):
    source = "openfoodfacts"
    dataset_file = "food.parquet"

    def run(self, ctx: RunContext) -> None:
        path = get_settings().datasets_dir / self.dataset_file
        lf = pl.scan_parquet(path)
        available = set(lf.collect_schema().names())
        cols = [c for c in _DESIRED if c in available]
        missing = [c for c in _DESIRED if c not in available]
        if missing:
            log.warning("openfoodfacts.columns_missing", missing=missing)

        lf = lf.select(cols)
        if "product_name" in cols:
            lf = lf.filter(pl.col("product_name").is_not_null())

        log.info("openfoodfacts.cap", limit=_LIMIT, note="reference subset; not the full file")
        frame = lf.head(_LIMIT).collect()

        for row in frame.iter_rows(named=True):
            ctx.record(
                RawRecord(
                    record_type="food",
                    payload=row,
                    natural_key=str(row.get("code")) if row.get("code") is not None else None,
                )
            )
