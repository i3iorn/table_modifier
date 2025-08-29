import types
from typing import Any

import pandas as pd
import pytest

from src.table_modifier.file_interface.excel import ExcelFileInterface


class DummyExcelFile:
    def __init__(self, path):
        self.path = path
        self.sheet_names = ["Sheet1", "Sheet2"]
        self.engine = "openpyxl"


class DummyExcelWriter:
    def __init__(self, file_path: str, engine: str):  # noqa: ARG002
        self.file_path = file_path
        self.engine = engine
        self.written = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: D401
        return False


def test_excel_interface_core(monkeypatch, tmp_path):
    sample_df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    headers_df = pd.DataFrame(columns=["A", "B"])  # for nrows=0

    calls: dict[str, Any] = {"writer_called": False, "to_excel_called": False}

    def fake_read_excel(path, sheet_name=0, nrows=None, skiprows=0):  # noqa: ANN001
        if nrows == 0:
            return headers_df
        return sample_df

    def fake_excel_writer(file_path, engine):  # noqa: ANN001
        calls["writer_called"] = True
        return DummyExcelWriter(file_path, engine)

    def fake_to_excel(self, writer, sheet_name=None, index=False):  # noqa: ANN001
        calls["to_excel_called"] = True
        return None

    # Patch pandas I/O
    monkeypatch.setattr(pd, "read_excel", fake_read_excel)
    monkeypatch.setattr(pd, "ExcelFile", lambda p: DummyExcelFile(p))
    monkeypatch.setattr(pd, "ExcelWriter", fake_excel_writer)
    monkeypatch.setattr(pd.DataFrame, "to_excel", fake_to_excel, raising=True)

    path = tmp_path / "test.xlsx"
    path.write_bytes(b"")  # ensure file exists, although reads are mocked

    iface = ExcelFileInterface(path)

    # can_handle
    assert ExcelFileInterface.can_handle(str(path)) is True
    assert ExcelFileInterface.can_handle("/tmp/file.csv") is False

    # headers
    headers = iface.get_headers()
    assert headers == ["A", "B"]

    # load and schema
    df_loaded = iface.load()
    assert list(df_loaded.columns) == ["A", "B"]
    schema = iface.get_schema()
    assert set(schema.keys()) == {"A", "B"}

    # append & iter
    iface.append_list([{"A": 7, "B": 8}])
    iface.append_df(pd.DataFrame({"A": [9], "B": [10]}))
    assert len(iface._df) == 5  # type: ignore[operator]

    chunks = list(iface.iter_load(chunksize=2))
    assert [len(c) for c in chunks] == [2, 2, 1]

    cols = list(iface.iter_columns(value_count=3, chunksize=2))
    # Expect 2 columns each yielding 2 then 1 rows (3 values limited)
    assert [list(c.columns)[0] for c in cols] == ["A", "A", "B", "B"]

    # stream rows
    first_row = next(iface.stream_rows())
    assert set(first_row.keys()) == {"A", "B"}

    # validate
    with pytest.raises(ValueError):
        iface.validate(pd.DataFrame([[1, 2]], columns=["A", "A"]))

    # metadata and sheets
    meta = iface.load_metadata()
    assert meta["sheet_names"] == ["Sheet1", "Sheet2"]
    assert meta["engine"] == "openpyxl"
    assert iface.get_sheets() == ["Sheet1", "Sheet2"]

    # save
    iface.save()
    iface.save_as((tmp_path / "out.xlsx").as_posix())
    assert calls["writer_called"] is True
    assert calls["to_excel_called"] is True

    # encoding constant
    assert iface.encoding == "utf-8"
