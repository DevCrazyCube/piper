"""Minimal ARFF (Weka) reader — stdlib only.

Dataset 4 (UCI Student Academics) ships as ARFF, not CSV: a header of
``@ATTRIBUTE name {nominal,values}`` (or ``numeric``/``real``) lines, then ``@DATA``
followed by CSV rows. We parse it ourselves rather than pull in a dependency.
Missing values ('?') become None. Numeric attributes are coerced to float.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Iterable, Iterator

_NUMERIC = {"numeric", "real", "integer"}


@dataclass(frozen=True)
class Attribute:
    name: str
    numeric: bool


def parse_attributes(lines: Iterable[str]) -> tuple[list[Attribute], Iterator[str]]:
    """Consume the header and return (attributes, iterator positioned at data rows)."""
    attributes: list[Attribute] = []
    it = iter(lines)
    for raw in it:
        line = raw.strip()
        if not line or line.startswith("%"):
            continue
        low = line.lower()
        if low.startswith("@attribute"):
            attributes.append(_parse_attribute(line))
        elif low.startswith("@data"):
            return attributes, it
        # @relation and anything else in the header is ignored.
    raise ValueError("ARFF: no @DATA section found")


def _parse_attribute(line: str) -> Attribute:
    # @ATTRIBUTE <name> {a,b,c}   |   @ATTRIBUTE <name> numeric
    body = line[len("@attribute"):].strip()
    if "{" in body:
        name = body[: body.index("{")].strip()
        numeric = False
    else:
        parts = body.split(None, 1)
        name = parts[0].strip()
        kind = parts[1].strip().lower() if len(parts) > 1 else ""
        numeric = kind in _NUMERIC
    return Attribute(name=name.strip("'\""), numeric=numeric)


def read_rows(lines: Iterable[str]) -> Iterator[dict[str, object]]:
    """Yield one dict per data row, keyed by attribute name. '?' -> None."""
    attributes, data_lines = parse_attributes(lines)
    names = [a.name for a in attributes]
    for values in csv.reader(_data_only(data_lines)):
        if not values:
            continue
        if len(values) != len(names):
            raise ValueError(
                f"ARFF row has {len(values)} values, expected {len(names)}: {values!r}"
            )
        record: dict[str, object] = {}
        for attr, value in zip(attributes, values, strict=False):
            v = value.strip()
            if v in ("?", ""):
                record[attr.name] = None
            elif attr.numeric:
                record[attr.name] = float(v)
            else:
                record[attr.name] = v
        yield record


def _data_only(lines: Iterator[str]) -> Iterator[str]:
    for raw in lines:
        line = raw.strip()
        if line and not line.startswith("%"):
            yield line
