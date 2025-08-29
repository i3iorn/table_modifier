import pandas as pd
import pytest

from src.table_modifier.file_interface.excel import ExcelFileInterface


def test_excel_set_rows_to_skip_list(monkeypatch, tmp_path):
    calls = {"args": []}

    def fake_read_excel(path, sheet_name=0, nrows=None, skiprows=0):  # noqa: ANN001
        calls["args"].append({"sheet_name": sheet_name, "nrows": nrows, "skiprows": skiprows})
        # return headers or data accordingly
        if nrows == 0:
            return pd.DataFrame(columns=["A", "B"])  # header only
        return pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

    monkeypatch.setattr(pd, "read_excel", fake_read_excel)
    monkeypatch.setattr(pd, "ExcelFile", lambda p: type("X", (), {"sheet_names": ["S1"], "engine": "openpyxl"})())

    p = tmp_path / "test.xlsx"
    p.write_bytes(b"")
    iface = ExcelFileInterface(p.as_posix(), sheet_name="S1")
    iface.set_rows_to_skip([1, 3])

    # headers call should pass skiprows list
    _ = iface.get_headers()
    # data load should pass skiprows list too
    df = iface.load()

    assert list(df.columns) == ["A", "B"]
    assert any(isinstance(call["skiprows"], list) for call in calls["args"])  # at least once a list

