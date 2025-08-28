import pytest

from src.table_modifier.gui.main_window.map_screen.utils import parse_skip_rows, is_valid_skip_rows


def test_parse_skip_rows_empty():
    assert parse_skip_rows("") == []
    assert parse_skip_rows(None) == []


def test_parse_skip_rows_list_and_ranges():
    assert parse_skip_rows("0, 2, 4") == [0, 2, 4]
    assert parse_skip_rows("2-5") == [2, 3, 4, 5]
    assert parse_skip_rows("5-2") == [2, 3, 4, 5]
    assert parse_skip_rows("1..3, 7, 10-11") == [1, 2, 3, 7, 10, 11]


def test_parse_skip_rows_dedup_and_sort():
    assert parse_skip_rows("3,1,2,3,2") == [1, 2, 3]


def test_parse_skip_rows_invalid():
    with pytest.raises(ValueError):
        parse_skip_rows("a,b")
    with pytest.raises(ValueError):
        parse_skip_rows("1-2-3")


def test_is_valid_skip_rows():
    assert is_valid_skip_rows("1,2,3")
    assert is_valid_skip_rows("1-3, 7")
    assert not is_valid_skip_rows("oops")

