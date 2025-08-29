import pytest
import pandas as pd

from src.table_modifier.processing.transform import apply_mapping, is_contiguous_prefix_zero_based


def test_is_contiguous_prefix_zero_based():
    assert is_contiguous_prefix_zero_based([])
    assert is_contiguous_prefix_zero_based([0])
    assert is_contiguous_prefix_zero_based([0, 1, 2])
    assert is_contiguous_prefix_zero_based([2, 0, 1])
    assert not is_contiguous_prefix_zero_based([0, 2])
    assert not is_contiguous_prefix_zero_based([1, 2, 3])


def test_apply_mapping_single_and_multi_sources():
    df = pd.DataFrame({
        "A": ["x", "y", None],
        "B": [1, 2, 3],
        "C": ["u", "v", "w"],
    })
    mapping = [
        {"sources": ["A"], "separator": "|"},
        {"sources": ["B", "C"], "separator": "-"},
    ]
    out = apply_mapping(df, mapping)
    # Single-source keeps column name
    assert list(out.columns) == ["A", "Combined_2"]
    assert out.loc[0, "A"] == "x"
    # Multi-source combines with separator, None treated as empty string
    assert out.loc[0, "Combined_2"] == "1-u"
    assert out.loc[1, "Combined_2"] == "2-v"
    assert out.loc[2, "Combined_2"] == "3-w"
