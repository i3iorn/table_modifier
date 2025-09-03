from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from src.table_modifier.config.state import state
from src.table_modifier.processing import engine


class FakeInput:
    def __init__(self, path: str, data: List[Dict[str, Any]]):
        self.path = Path(path)
        self._data = data

    def get_headers(self, sheet_name: str | None = None):  # noqa: ARG002
        # derive from first row
        return list(self._data[0].keys() if self._data else [])

    def set_rows_to_skip(self, rows: List[int]):  # noqa: ARG002
        # no-op for tests
        return None

    def set_header_rows_to_skip(self, header_rows: int):  # noqa: ARG002
        # no-op for tests
        return None

    def iter_load(self, chunksize: int = 1000):  # noqa: ARG002
        df = pd.DataFrame(self._data)
        if len(df) == 0:
            if False:
                yield df
            return
        mid = max(1, len(df) // 2)
        yield df.iloc[:mid].reset_index(drop=True)
        yield df.iloc[mid:].reset_index(drop=True)


class FakeOutput:
    def __init__(self):
        self._dfs: List[pd.DataFrame] = []
        self.saved_path: str | None = None

    def append_df(self, df: pd.DataFrame) -> None:
        self._dfs.append(df.copy())

    def save_as(self, file_path: str) -> None:
        self.saved_path = file_path


def _collect_output_df(fout: FakeOutput) -> pd.DataFrame:
    if not fout._dfs:
        return pd.DataFrame()
    return pd.concat(fout._dfs, ignore_index=True)


def test_dedupe_drop_keeps_first_by_key(monkeypatch, tmp_path):
    data = [
        {"A": "k1", "B": "b1", "C": 1},
        {"A": "k2", "B": "b2", "C": 2},
        {"A": "k1", "B": "b1_dup", "C": 3},
        {"A": "k3", "B": "b3", "C": 4},
    ]
    fin = FakeInput((tmp_path / "in.csv").as_posix(), data)
    fout = FakeOutput()

    monkeypatch.setattr(engine, "_estimate_total_rows", lambda iface, chunksize=100000: len(data))
    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    state.update_control("processing.strict", False)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["A"], "separator": " "},
            {"sources": ["B"], "separator": " "},
        ],
        "skip_rows": [],
        "dedupe": {"enabled": True, "key": "A", "strategy": "drop"},
    }
    engine._run_processing(current)

    out = _collect_output_df(fout)
    # Expect first occurrence per A: k1->b1, k2->b2, k3->b3
    assert sorted(out["A"].tolist()) == ["k1", "k2", "k3"]
    assert out.loc[out["A"] == "k1", "B"].iloc[0] == "b1"


def test_dedupe_concat_combines_unique_values(monkeypatch, tmp_path):
    data = [
        {"A": "k1", "B": "x", "C": "p"},
        {"A": "k1", "B": "y", "C": "p"},
        {"A": "k2", "B": "y", "C": "q"},
        {"A": "k1", "B": "x", "C": None},  # duplicate B value and NaN in C
    ]
    fin = FakeInput((tmp_path / "in.csv").as_posix(), data)
    fout = FakeOutput()

    monkeypatch.setattr(engine, "_estimate_total_rows", lambda iface, chunksize=100000: len(data))
    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    state.update_control("processing.strict", False)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["A"], "separator": " "},
            {"sources": ["B"], "separator": " "},
            {"sources": ["C"], "separator": " "},
        ],
        "skip_rows": [],
        "dedupe": {"enabled": True, "key": "A", "strategy": "concat", "concat_sep": ","},
    }
    engine._run_processing(current)

    out = _collect_output_df(fout)
    # k1 should have B = 'x,y' (order preserved, unique), C = 'p'
    row_k1 = out[out["A"] == "k1"].iloc[0]
    assert row_k1["B"] in ("x,y", "x, y", "x, y")  # tolerate space variations
    assert row_k1["C"] == "p"
    # k2 should be single
    row_k2 = out[out["A"] == "k2"].iloc[0]
    assert row_k2["B"] == "y"
    assert row_k2["C"] == "q"


def test_dedupe_enabled_without_key_runs_normally(monkeypatch, tmp_path):
    data = [
        {"A": "x", "B": 1},
        {"A": "y", "B": 2},
    ]
    fin = FakeInput((tmp_path / "in.csv").as_posix(), data)
    fout = FakeOutput()

    monkeypatch.setattr(engine, "_estimate_total_rows", lambda iface: len(data))
    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["A"], "separator": " "},
        ],
        "skip_rows": [],
        "dedupe": {"enabled": True},  # no key
    }
    engine._run_processing(current)

    out = _collect_output_df(fout)
    assert out.shape[0] == 2
    assert out["A"].tolist() == ["x", "y"]


def test_dedupe_key_not_in_headers_disables(monkeypatch, tmp_path):
    data = [
        {"A": "x", "B": 1},
        {"A": "x", "B": 2},
    ]
    fin = FakeInput((tmp_path / "in.csv").as_posix(), data)
    fout = FakeOutput()

    monkeypatch.setattr(engine, "_estimate_total_rows", lambda iface: len(data))
    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["A"], "separator": " "},
        ],
        "skip_rows": [],
        "dedupe": {"enabled": True, "key": "Z", "strategy": "drop"},  # Z not in headers
    }
    engine._run_processing(current)

    out = _collect_output_df(fout)
    # Without dedupe, we keep both rows
    assert out.shape[0] == 2


def test_dedupe_drop_fallback_when_chunk_missing_key(monkeypatch, tmp_path):
    class WeirdInput(FakeInput):
        def get_headers(self, sheet_name: str | None = None):  # noqa: ARG002
            return ["A", "B"]
        def iter_load(self, chunksize: int = 1000):  # noqa: ARG002
            # Intentionally drop the key column from chunks
            df = pd.DataFrame([{"B": "b1"}, {"B": "b2"}])
            yield df

    fin = WeirdInput((tmp_path / "in.csv").as_posix(), [])
    fout = FakeOutput()

    monkeypatch.setattr(engine, "_estimate_total_rows", lambda iface: 2)
    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["B"], "separator": " "},
        ],
        "skip_rows": [],
        "dedupe": {"enabled": True, "key": "A", "strategy": "drop"},  # key A present in headers but missing in chunk
    }
    engine._run_processing(current)

    out = _collect_output_df(fout)
    assert out.shape[0] == 2
    assert out["B"].tolist() == ["b1", "b2"]
