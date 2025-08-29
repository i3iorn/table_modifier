import pytest
import pandas as pd

from src.table_modifier.classifier.check.mixin import MatchCountCheckMixin, PandasMatchMixin


def test_match_count_check_mixin():
    mixin = MatchCountCheckMixin[int]()
    values = [1, 2, 3, 4, 5]
    res = mixin.by_predicate(values, lambda v: v % 2 == 0)
    assert res == 2 / 5
    assert mixin.by_predicate([], lambda v: True) == 0.0


def test_pandas_match_mixin():
    mixin = PandasMatchMixin()
    s = pd.Series(["a", "bb", "ccc", "", None])
    res = mixin.by_predicate_series(s, lambda ser: ser.fillna("").str.len() > 1)
    # 'bb' and 'ccc' only
    assert res == 2 / 5
    assert mixin.by_predicate_series(pd.Series(dtype=object), lambda ser: ser == "x") == 0.0

