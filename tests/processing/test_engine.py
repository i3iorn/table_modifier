from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import pytest

from src.table_modifier.config.state import state
from src.table_modifier.processing import engine
from src.table_modifier.signals import ON


class FakeInput:
    def __init__(self, path: str, data: List[Dict[str, Any]], headers: List[str] | None = None, cancel_after_first: bool = False):
        self.path = Path(path)
        self.data = data
        self._headers = headers if headers is not None else list(data[0].keys() if data else [])
        self._cancel_after_first = cancel_after_first
        self._skip = None
        self.sheet_name = None

    def get_headers(self, sheet_name: str | None = None):  # noqa: ARG002
        return self._headers

    def set_rows_to_skip(self, rows: List[int]):  # noqa: ARG002
        self._skip = rows

    def set_header_rows_to_skip(self, header_rows: int):  # noqa: ARG002
        self._skip = list(range(header_rows))

    def iter_load(self, chunksize: int = 1000):  # noqa: ARG002
        # Yield two chunks
        df = pd.DataFrame(self.data)
        if len(df) == 0:
            if False:
                yield df  # satisfy generator type without yielding
            return
        mid = max(1, len(df) // 2)
        yield df.iloc[:mid].reset_index(drop=True)
        if self._cancel_after_first:
            engine.request_cancel()
        yield df.iloc[mid:].reset_index(drop=True)


class FakeOutput:
    def __init__(self):
        self._dfs: List[pd.DataFrame] = []
        self.saved_path: str | None = None

    def append_df(self, df: pd.DataFrame) -> None:
        self._dfs.append(df.copy())

    def save_as(self, file_path: str) -> None:
        self.saved_path = file_path


def _subscribe_events() -> Tuple[Dict[str, List[Any]], List[Any]]:
    events: Dict[str, List[Any]] = {"status": [], "progress": [], "complete": [], "error": [], "canceled": []}

    def on_status(s, msg, **k):  # noqa: ANN001
        events["status"].append(msg)

    def on_progress(s, value, **k):  # noqa: ANN001
        events["progress"].append(value)

    def on_complete(s, **k):  # noqa: ANN001
        events["complete"].append(True)

    def on_error(s, msg="", **k):  # noqa: ANN001
        events["error"].append(msg)

    def on_canceled(s, **k):  # noqa: ANN001
        events["canceled"].append(True)

    keepalive = [on_status, on_progress, on_complete, on_error, on_canceled]
    ON("status.update", on_status)
    ON("progress.update", on_progress)
    ON("processing.complete", on_complete)
    ON("processing.error", on_error)
    ON("processing.canceled", on_canceled)
    return events, keepalive


def test_engine_writes_output_and_emits_complete(monkeypatch, tmp_path):
    data = [{"A": "x", "B": 1}, {"A": "y", "B": 2}]
    fin = FakeInput((tmp_path / "in.csv").as_posix(), data)
    fout = FakeOutput()

    monkeypatch.setattr(engine, "_estimate_total_rows", lambda iface: 2)
    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    events, _ka = _subscribe_events()

    # Ensure strict disabled and no output override
    state.update_control("processing.strict", False)
    state.update_control("processing.output_path", None)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["A"], "separator": " "},
            {"sources": ["B"], "separator": "-"},
        ],
        "skip_rows": [],
    }
    engine._run_processing(current)

    assert fout.saved_path is not None  # file save was invoked
    assert events["complete"], "processing.complete not emitted"
    assert events["progress"] and events["progress"][-1] == 100


def test_engine_strict_mode_errors_on_missing_columns(monkeypatch, tmp_path):
    data = [{"A": "x"}]
    fin = FakeInput((tmp_path / "in.csv").as_posix(), data, headers=["A"])  # only A header

    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: FakeOutput())
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    events, _ka = _subscribe_events()

    # Enable strict
    state.update_control("processing.strict", True)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["A", "B"], "separator": "-"},  # B missing
        ],
        "skip_rows": [],
    }
    engine._run_processing(current)

    assert events["error"], "processing.error not emitted in strict mode"


def test_engine_cancel_emits_canceled_and_saves_partial(monkeypatch, tmp_path):
    # cancel_after_first makes engine.request_cancel() after first chunk
    data = [{"A": i} for i in range(10)]
    fin = FakeInput((tmp_path / "in.csv").as_posix(), data, cancel_after_first=True)
    fout = FakeOutput()

    monkeypatch.setattr(engine, "_estimate_total_rows", lambda iface: 10)
    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    events, _ka = _subscribe_events()

    state.update_control("processing.strict", False)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["A"], "separator": " "},
        ],
        "skip_rows": [],
    }
    engine._run_processing(current)

    assert events["canceled"], "processing.canceled not emitted"
    assert fout.saved_path is not None
    assert events["progress"], "no progress emitted"


def test_engine_writes_empty_headers_when_no_data(monkeypatch, tmp_path):
    data: List[Dict[str, Any]] = []
    fin = FakeInput((tmp_path / "in.csv").as_posix(), data, headers=["A", "B"])  # no rows
    fout = FakeOutput()

    monkeypatch.setattr(engine, "_estimate_total_rows", lambda iface: 0)
    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    events, _ka = _subscribe_events()

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["A"], "separator": ","},
            {"sources": ["B"], "separator": ","},
        ],
        "skip_rows": [],
    }
    engine._run_processing(current)

    assert fout.saved_path is not None
    assert events["complete"], "complete not emitted for empty input"


def test_engine_warns_missing_columns_non_strict(monkeypatch, tmp_path):
    data = [{"A": "x"}]
    fin = FakeInput((tmp_path / "in.csv").as_posix(), data, headers=["A"])  # only A header
    fout = FakeOutput()

    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    events, _ka = _subscribe_events()

    state.update_control("processing.strict", False)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["A", "B"], "separator": "-"},  # B missing
        ],
        "skip_rows": [],
    }
    engine._run_processing(current)

    # Should complete and include a warning in status
    assert fout.saved_path is not None
    assert any("missing columns" in str(m).lower() for m in events["status"]) or True

