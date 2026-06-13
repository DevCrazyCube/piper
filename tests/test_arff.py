"""Tests for the ARFF reader (runnable with stdlib unittest)."""

import unittest

from pipeline.common.arff import read_rows

SAMPLE = """\
@RELATION Sapfile1

@ATTRIBUTE ge  {M,F}
@ATTRIBUTE esp {Best,Vg,Good,Pass,Fail}
@ATTRIBUTE arr {Y,N}
@ATTRIBUTE score numeric
@ATTRIBUTE atd {Good,Average,Poor}

@DATA
F,Good,Y,12.5,Good
M,Vg,N,?,Average
% a comment line
F,Fail,N,8,Poor
"""


class TestArff(unittest.TestCase):
    def test_parses_all_rows(self) -> None:
        rows = list(read_rows(SAMPLE.splitlines()))
        self.assertEqual(len(rows), 3)

    def test_keys_match_attributes(self) -> None:
        row = next(read_rows(SAMPLE.splitlines()))
        self.assertEqual(set(row), {"ge", "esp", "arr", "score", "atd"})

    def test_nominal_values_preserved(self) -> None:
        row = next(read_rows(SAMPLE.splitlines()))
        self.assertEqual(row["ge"], "F")
        self.assertEqual(row["esp"], "Good")

    def test_numeric_coerced_to_float(self) -> None:
        row = next(read_rows(SAMPLE.splitlines()))
        self.assertEqual(row["score"], 12.5)
        self.assertIsInstance(row["score"], float)

    def test_missing_value_becomes_none(self) -> None:
        rows = list(read_rows(SAMPLE.splitlines()))
        self.assertIsNone(rows[1]["score"])

    def test_comment_lines_skipped(self) -> None:
        rows = list(read_rows(SAMPLE.splitlines()))
        self.assertEqual(rows[2]["atd"], "Poor")

    def test_wrong_column_count_raises(self) -> None:
        bad = SAMPLE + "M,Vg,N\n"  # too few columns
        with self.assertRaises(ValueError):
            list(read_rows(bad.splitlines()))


if __name__ == "__main__":
    unittest.main()
