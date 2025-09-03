from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import pytest

from src.table_modifier.config.state import state
from src.table_modifier.processing import engine
from src.table_modifier.signals import ON


class FakeInput:
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


class FakeOutputAppendFails:
    def __init__(self):
        self._df = None
        self.saved_path: str | None = None
        self._delimiter = ","

    def append_df(self, df: pd.DataFrame) -> None:
        raise RuntimeError("append failed")

    def save_as(self, file_path: str) -> None:
        # should be called even after fallback
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


def test_engine_strict_per_slot_errors(monkeypatch, tmp_path):
    fin = FakeInput((tmp_path / "in.csv").as_posix(), rows=[{"A": 1}], headers=["A"])
    fout = FakeOutputAppendFails()

    monkeypatch.setattr(engine, "_estimate_total_rows", lambda iface: 1)
    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    events, _ka = _subscribe_events()

    state.update_control("processing.strict", False)
    state.update_control("processing.strict_per_slot", True)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["A"], "separator": " "},
            {"sources": ["B"], "separator": " "},  # missing in headers
        ],
        "skip_rows": [],
    }
    engine._run_processing(current)
    assert events["error"], "Should error in strict per-slot mode"


def test_engine_append_df_failure_fallback(monkeypatch, tmp_path):
    rows = [{"A": "x"}, {"A": "y"}]
    fin = FakeInput((tmp_path / "in.csv").as_posix(), rows=rows)
    fout = FakeOutputAppendFails()

    monkeypatch.setattr(engine, "_estimate_total_rows", lambda iface: len(rows))
    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    state.update_control("processing.strict", False)

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["A"], "separator": " "},
        ],
        "skip_rows": [],
    }
    engine._run_processing(current)

    # Should still save even though append_df failed (fallback path used)
    assert fout.saved_path is not None


def test_engine_dedupe_concat_cancel(monkeypatch, tmp_path):
    class CancelInput(FakeInput):
        def iter_load(self, chunksize: int = 1000):  # noqa: ARG002
            df = pd.DataFrame([
                {"K": 1, "V": "a"},
                {"K": 1, "V": "b"},
            ])
            yield df
            engine.request_cancel()
            yield df

    fin = CancelInput((tmp_path / "in.csv").as_posix(), rows=[], headers=["K", "V"])
    class Fout:
        def __init__(self):
            self._dfs: List[pd.DataFrame] = []
            self.saved_path: str | None = None
        def append_df(self, df: pd.DataFrame) -> None:
            self._dfs.append(df.copy())
        def save_as(self, path: str) -> None:
            self.saved_path = path

    fout = Fout()

    monkeypatch.setattr(engine, "_estimate_total_rows", lambda iface: 4)
    monkeypatch.setattr(engine, "_create_output_interface_like", lambda iface: fout)
    monkeypatch.setattr("src.table_modifier.file_interface.factory.FileInterfaceFactory.create", lambda path: fin)

    events, _ka = _subscribe_events()

    current = {
        "source": fin.path.as_posix(),
        "mapping": [
            {"sources": ["K"], "separator": " "},
            {"sources": ["V"], "separator": ","},
        ],
        "skip_rows": [],
        "dedupe": {"enabled": True, "key": "K", "strategy": "concat", "concat_sep": ","},
    }
    engine._run_processing(current)

    # Cancel path should be emitted
    assert events["canceled"], "Expected processing.canceled in dedupe concat cancel test"

