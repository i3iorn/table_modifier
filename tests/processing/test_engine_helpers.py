import pytest
from typing import Any, Dict, Iterator, List

import pandas as pd

from src.table_modifier.processing import engine


def test_parse_source_id():
    assert engine._parse_source_id("/a/b.csv") == ("/a/b.csv", None)
    assert engine._parse_source_id("/a/b.xlsx::Sheet1") == ("/a/b.xlsx", "Sheet1")


def test_build_output_path(tmp_path):
    p = tmp_path / "file.csv"
    res = engine._build_output_path(p.as_posix())
    assert res.name == "file_processed.csv"


def test_collect_all_sources_and_compute_output_columns():
    mapping: List[Dict[str, Any]] = [
        {"sources": ["A"], "separator": " ",},
        {"sources": ["B", "C"], "separator": "-",},
    ]
    collected = engine._collect_all_sources(mapping)
    assert collected == {"A", "B", "C"}
    cols = engine._compute_output_columns(mapping)
    assert cols == ["A", "Combined_2"]


class DummyIface:
    def __init__(self):
        self.header_skip = None
        self.rows_skip = None

    def set_rows_to_skip(self, rows: List[int]) -> None:
        self.rows_skip = list(rows)

    def set_header_rows_to_skip(self, n: int) -> None:
        self.header_skip = n


class DummyIfaceNoList(DummyIface):
    def set_rows_to_skip(self, rows: List[int]) -> None:  # type: ignore[override]
        raise RuntimeError("no list skip")


def test_apply_skip_rows_prefers_list():
    iface = DummyIface()
    engine._apply_skip_rows(iface, [1, 3, 5])
    assert iface.rows_skip == [1, 3, 5]
    assert iface.header_skip is None


def test_apply_skip_rows_fallback_contiguous_header():
    iface = DummyIfaceNoList()
    engine._apply_skip_rows(iface, [0, 1, 2])
    assert iface.header_skip == 3


class CountIface:
    def __init__(self, counts: List[int]):
        self._counts = counts

    def iter_load(self, chunksize: int = 1000) -> Iterator[pd.DataFrame]:  # noqa: ARG002
        for n in self._counts:
            yield pd.DataFrame({"x": list(range(n))})


def test_estimate_total_rows():
    iface = CountIface([0, 10, 5])
    assert engine._estimate_total_rows(iface) == 15

