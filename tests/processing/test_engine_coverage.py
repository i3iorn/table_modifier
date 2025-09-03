from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from src.table_modifier.config.state import state
from src.table_modifier.processing import engine


class Fin:
    def __init__(self, path: str, rows: List[Dict[str, Any]], headers: List[str] | None = None):
        self.path = Path(path)
        self._rows = rows
        self._headers = headers if headers is not None else list(rows[0].keys() if rows else [])

    def get_headers(self, sheet_name: str | None = None):  # noqa: ARG002
        return self._headers

    def set_rows_to_skip(self, rows: List[int]):  # noqa: ARG002
        return None

    def iter_load(self, chunksize: int = 1000):  # noqa: ARG002
        df = pd.DataFrame(self._rows)
        if len(df) == 0:
            if False:
                yield df
            return
        yield df


class FoutCapture:
    def __init__(self):
        self._dfs: List[pd.DataFrame] = []
        self.saved_path: str | None = None
        self._delimiter = ","

    def append_df(self, df: pd.DataFrame) -> None:
        self._dfs.append(df.copy())

    def save_as(self, path: str) -> None:
        self.saved_path = path


def _collect(fout: FoutCapture) -> pd.DataFrame:
    if not fout._dfs:
        return pd.DataFrame()
    return pd.concat(fout._dfs, ignore_index=True)


def test_dedupe_drop_all_nan_keys_writes_empty(monkeypatch, tmp_path):
    rows = [{"K": None, "V": "a"}, {"K": float('nan'), "V": "b"}]  # NaN/None keys
    fin = Fin((tmp_path / "in.csv").as_posix(), rows=rows, headers=["K", "V"])
    fout = FoutCapture()

    monkeypatch.setattr(engine, "_estimate_total_rows", lambda iface: len(rows))
    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["K"], "separator": " "},
        ],
        "skip_rows": [],
        "dedupe": {"enabled": True, "key": "K", "strategy": "drop"},
    }
    engine._run_processing(current)

    out = _collect(fout)
    # Should be empty but with header K
    assert list(out.columns) == ["K"]
    assert out.empty


def test_dedupe_concat_only_key_results_empty_headers(monkeypatch, tmp_path):
    rows = [{"K": 1, "V": "a"}, {"K": 1, "V": "b"}]
    fin = Fin((tmp_path / "in.csv").as_posix(), rows=rows, headers=["K", "V"])
    fout = FoutCapture()

    monkeypatch.setattr(engine, "_estimate_total_rows", lambda iface: len(rows))
    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["K"], "separator": " "},
        ],
        "skip_rows": [],
        "dedupe": {"enabled": True, "key": "K", "strategy": "concat", "concat_sep": ";"},
    }
    engine._run_processing(current)

    out = _collect(fout)
    assert list(out.columns) == ["K"]


def test_csv_delimiter_propagation(monkeypatch, tmp_path):
    rows = [{"A": "x"}, {"A": "y"}]
    fin = Fin((tmp_path / "in.csv").as_posix(), rows=rows)
    fout = FoutCapture()

    state.update_control("processing.csv_delimiter", ";")

    monkeypatch.setattr(engine, "_estimate_total_rows", lambda iface: len(rows))
    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["A"], "separator": " "},
        ],
        "skip_rows": [],
    }
    engine._run_processing(current)

    # Output interface should reflect delimiter preference
    assert getattr(fout, "_delimiter", None) == ";"

