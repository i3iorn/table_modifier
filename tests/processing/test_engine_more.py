import pytest
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from src.table_modifier.config.state import state
from src.table_modifier.processing import engine
from src.table_modifier.signals import ON


class FakeInputSheet:
    def __init__(self, path: str):
        self.path = Path(path)
        self.sheet_name: str | None = None
        self._headers = ["A"]
        self._rows = [{"A": 1}, {"A": 2}]
        self._set_rows_calls: list[list[int]] = []
        self._set_header_calls: list[int] = []

    def get_headers(self, sheet_name: str | None = None):  # noqa: ARG002
        return self._headers

    def set_rows_to_skip(self, rows: List[int]) -> None:
        self._set_rows_calls.append(list(rows))

    def set_header_rows_to_skip(self, header_rows: int) -> None:
        self._set_header_calls.append(int(header_rows))

    def iter_load(self, chunksize: int = 1000):  # noqa: ARG002
        df = pd.DataFrame(self._rows)
        yield df


class FakeOutput:
    def __init__(self):
        self.saved_path: str | None = None
        self._df_list: list[pd.DataFrame] = []

    def append_df(self, df: pd.DataFrame) -> None:
        self._df_list.append(df.copy())

    def save_as(self, path: str) -> None:
        self.saved_path = path


def _subscribe_status() -> Tuple[list[str], list[Any]]:
    logs: list[str] = []

    def on_status(s, msg, **k):  # noqa: ANN001
        logs.append(str(msg))

    ka = [on_status]
    ON("status.update", on_status)
    return logs, ka


def _subscribe_progress() -> Tuple[list[int], list[Any]]:
    vals: list[int] = []

    def on_prog(s, value, **k):  # noqa: ANN001
        vals.append(int(value))

    ka = [on_prog]
    ON("progress.update", on_prog)
    return vals, ka


def test_engine_uses_output_override_and_parses_sheet(monkeypatch, tmp_path):
    fin = FakeInputSheet((tmp_path / "in.xlsx").as_posix())
    fout = FakeOutput()

    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    override = (tmp_path / "custom.csv").as_posix()
    state.update_control("processing.output_path", override)

    current = {
        "source": fin.path.as_posix() + "::Sheet2",
        "mapping": [{"sources": ["A"], "separator": " ",}],
        "skip_rows": [],
    }
    engine._run_processing(current)

    assert fin.sheet_name == "Sheet2"  # ensure sheet parsed
    assert fout.saved_path == override  # ensure override used


def test_engine_header_probe_failure_warns(monkeypatch, tmp_path):
    class Fin(FakeInputSheet):
        def get_headers(self, sheet_name: str | None = None):  # noqa: ARG002
            raise RuntimeError("boom")

    fin = Fin((tmp_path / "in.csv").as_posix())
    fout = FakeOutput()
    logs, _ka = _subscribe_status()

    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [{"sources": ["A"], "separator": ","}],
        "skip_rows": [],
    }
    engine._run_processing(current)

    assert any("Could not read headers" in m for m in logs)
    assert fout.saved_path is not None


def test_engine_unknown_total_progress(monkeypatch, tmp_path):
    fin = FakeInputSheet((tmp_path / "in.csv").as_posix())
    fout = FakeOutput()
    progress, _ka = _subscribe_progress()

    monkeypatch.setattr(engine, "_estimate_total_rows", lambda iface: 0)
    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [{"sources": ["A"], "separator": " ",}],
        "skip_rows": [],
    }
    engine._run_processing(current)

    assert progress, "no progress updates"
    assert progress[-1] == 100


def test_engine_skip_rows_fallback_header(monkeypatch, tmp_path):
    class Fin(FakeInputSheet):
        def set_rows_to_skip(self, rows: List[int]) -> None:
            raise RuntimeError("no list")

    fin = Fin((tmp_path / "in.csv").as_posix())
    fout = FakeOutput()

    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [{"sources": ["A"], "separator": " ",}],
        "skip_rows": [0, 1, 2],  # contiguous -> header skip
    }
    engine._run_processing(current)

    # Should have used header skip fallback
    assert fin._set_header_calls and fin._set_header_calls[-1] == 3


def test_engine_save_failure_emits_error(monkeypatch, tmp_path):
    fin = FakeInputSheet((tmp_path / "in.csv").as_posix())

    class Fout(FakeOutput):
        def save_as(self, path: str) -> None:  # noqa: D401
            raise RuntimeError("disk full")

    fout = Fout()
    errors: list[str] = []

    def on_err(s, msg="", **k):  # noqa: ANN001
        errors.append(str(msg))

    _ka = [on_err]
    ON("processing.error", on_err)

    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [{"sources": ["A"], "separator": " ",}],
        "skip_rows": [],
    }
    engine._run_processing(current)
    assert errors, "processing.error should be emitted when save fails"


def test_engine_noop_when_missing_source_or_mapping(monkeypatch, tmp_path):
    logs, _ka = _subscribe_status()
    engine._run_processing({"source": "", "mapping": [], "skip_rows": []})
    assert any("Nothing to process" in m for m in logs)
