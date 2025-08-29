import pytest

from pathlib import Path

import pandas as pd
import pytest

from src.table_modifier.file_interface.csv import CSVFileInterface


def make_csv(tmp_path: Path, name: str = "data.csv", with_header: bool = True) -> Path:
    p = tmp_path / name
    if with_header:
        p.write_text("a,b,c\n1,2,3\n4,5,6\n", encoding="utf-8")
    else:
        p.write_text("1,2,3\n4,5,6\n", encoding="utf-8")
    return p


def test_get_headers_and_can_handle(tmp_path: Path):
    p = make_csv(tmp_path)
    iface = CSVFileInterface(str(p))
    assert CSVFileInterface.can_handle(str(p))
    headers = iface.get_headers()
    assert headers == ["a", "b", "c"]


def test_load_and_skip_rows(tmp_path: Path):
    p = make_csv(tmp_path)
    iface = CSVFileInterface(str(p))
    df = iface.load()
    assert list(df.columns) == ["a", "b", "c"]
    assert df.shape == (2, 3)

    iface2 = CSVFileInterface(str(p))
    iface2.set_header_rows_to_skip(1)
    df2 = iface2.load()
    # Skipping the header will cause pandas to treat first data row as header
    assert list(df2.columns) == ["1", "2", "3"]


def test_iter_load_and_stream_rows(tmp_path: Path):
    p = make_csv(tmp_path)
    iface = CSVFileInterface(str(p))
    chunks = list(iface.iter_load(chunksize=1))
    assert len(chunks) == 2
    assert list(chunks[0].iloc[0].values) == [1, 2, 3]

    rows = list(iface.stream_rows())
    assert rows == [{"a": 1, "b": 2, "c": 3}, {"a": 4, "b": 5, "c": 6}]


def test_iter_columns_value_count(tmp_path: Path):
    p = make_csv(tmp_path)
    iface = CSVFileInterface(str(p))
    cols = list(iface.iter_columns(value_count=1, chunksize=1))
    # Expect 2 rows * 3 columns -> 6 one-column frames, each with 1 value
    assert len(cols) == 6
    for df in cols:
        assert df.shape[1] == 1
        assert df.shape[0] == 1


def test_append_df_and_list_and_save(tmp_path: Path):
    p = make_csv(tmp_path)
    iface = CSVFileInterface(str(p))
    iface.load()  # initialize _df

    # append list
    iface.append_list([{"a": 7, "b": 8, "c": 9}])
    # append df
    iface.append_df(pd.DataFrame([{"a": 10, "b": 11, "c": 12}]))

    out = tmp_path / "out.csv"
    iface.save_as(out.as_posix())
    txt = out.read_text(encoding="utf-8").strip().splitlines()
    # original 2 rows + 2 appended rows = 4 rows
    assert txt[0] == "a,b,c"
    assert len(txt) == 5  # header + 4 rows


def test_get_schema_and_metadata_and_validate(tmp_path: Path):
    p = make_csv(tmp_path)
    iface = CSVFileInterface(str(p))
    df = iface.load()
    schema = iface.get_schema()
    assert set(schema.keys()) == {"a", "b", "c"}
    meta = iface.load_metadata()
    assert meta["columns"] == ["a", "b", "c"]

    # Validate should reject empty column names
    bad = df.copy()
    bad.columns = ["a", "", "c"]
    with pytest.raises(ValueError):
        iface.validate(bad)

