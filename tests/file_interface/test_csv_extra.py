import pytest

from pathlib import Path
from src.table_modifier.file_interface.csv import CSVFileInterface


def test_get_headers_file_not_found(tmp_path: Path, caplog):
    missing = tmp_path / "missing.csv"
    iface = CSVFileInterface(missing.as_posix())
    headers = iface.get_headers()
    assert headers is None


def test_context_manager_opens_and_closes(tmp_path: Path):
    p = tmp_path / "a.csv"
    p.write_text("h1\n1\n", encoding="utf-8")
    iface = CSVFileInterface(p.as_posix())
    assert getattr(iface, "_file", None) is None
    with iface as ctx:
        assert ctx is iface
        assert iface._file is not None
    # after context, file handle cleared
    assert iface._file is None

