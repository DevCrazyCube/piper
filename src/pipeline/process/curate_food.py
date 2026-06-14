"""Flatten Open Food Facts: pull energy/fat/sugar/protein/salt per-100g out of the nested
`nutriments` list into curated.food_reference (the meal-enrichment lookup for Phase-2 Q4).
"""

from __future__ import annotations

import psycopg

from pipeline.common.logging import get_logger
from pipeline.process.util import log_decision

log = get_logger("curate.food")

# OFF nutrient name -> our column.
_WANTED = {
    "energy-kcal": "energy_kcal_100g",
    "fat": "fat_100g",
    "sugars": "sugars_100g",
    "proteins": "proteins_100g",
    "salt": "salt_100g",
}
_BATCH = 5_000


def _text(value: object) -> str | None:
    """OFF product_name is a List(Struct{lang,text}); pick en/main, else first non-empty."""
    if value is None or isinstance(value, str):
        return value or None
    if isinstance(value, dict):
        return value.get("text") or None
    if isinstance(value, list):
        chosen = None
        for item in value:
            if isinstance(item, dict) and item.get("text"):
                if item.get("lang") in ("en", "main"):
                    return item["text"]
                chosen = chosen or item["text"]
        return chosen
    return str(value)


def curate_food(conn: psycopg.Connection) -> dict[str, int]:
    inserted = 0
    with_nutrition = 0
    batch: list[tuple] = []

    write = conn.cursor()
    read = conn.cursor(name="off_scan")  # server-side cursor: stream 50k without loading all
    read.itersize = _BATCH
    read.execute("SELECT payload FROM raw.record WHERE source='openfoodfacts' AND record_type='food'")

    for (p,) in read:
        code = p.get("code")
        if not code:
            continue
        nutr = {n.get("name"): n.get("100g") for n in (p.get("nutriments") or []) if isinstance(n, dict)}
        vals = {col: nutr.get(name) for name, col in _WANTED.items()}
        if any(v is not None for v in vals.values()):
            with_nutrition += 1
        batch.append(
            (str(code), _text(p.get("product_name")), p.get("brands"), p.get("nutriscore_grade"),
             vals["energy_kcal_100g"], vals["fat_100g"], vals["sugars_100g"],
             vals["proteins_100g"], vals["salt_100g"])
        )
        if len(batch) >= _BATCH:
            inserted += _flush(write, batch)
            batch.clear()
    if batch:
        inserted += _flush(write, batch)
    read.close()

    log_decision(
        write, stage="curate", source="openfoodfacts",
        decision=f"flattened nested nutriments; {inserted} products, {with_nutrition} with nutrition",
        rationale="OFF stores nutriments as List(Struct); extract per-100g for meal enrichment",
        detail={"products": inserted, "with_nutrition": with_nutrition, "nutrients": list(_WANTED)},
    )
    log.info("curate.food.done", products=inserted, with_nutrition=with_nutrition)
    return {"products": inserted, "with_nutrition": with_nutrition}


def _flush(cur: psycopg.Cursor, batch: list[tuple]) -> int:
    cur.executemany(
        "INSERT INTO curated.food_reference "
        "(code, product_name, brands, nutriscore_grade, energy_kcal_100g, fat_100g, "
        "sugars_100g, proteins_100g, salt_100g) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) "
        "ON CONFLICT (code) DO NOTHING",
        batch,
    )
    return len(batch)
