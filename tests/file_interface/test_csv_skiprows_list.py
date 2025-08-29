import pytest
from pathlib import Path

import pandas as pd

from src.table_modifier.file_interface.csv import CSVFileInterface


def test_csv_set_rows_to_skip_list(tmp_path: Path):
    p = tmp_path / "data.csv"
    p.write_text("a,b\nx,y\nm,n\n", encoding="utf-8")
    iface = CSVFileInterface(p.as_posix())
    iface.set_rows_to_skip([1])  # skip first data row only
    df = iface.load()
    # Header remains; only second line skipped
    assert list(df.columns) == ["a", "b"]
    assert df.shape == (1, 2)
    assert list(df.iloc[0].values) == ["m", "n"]

