import pytest

from src.table_modifier.classifier.utils import (
    normalize_numeral,
    normalize_alpha,
    normalize_numeral_list,
    normalize_alpha_list,
)


def test_normalize_numeral_basic():
    assert normalize_numeral(0) == 0.0
    assert 0.85 < normalize_numeral(2) < 0.95
    assert 0.0 < normalize_numeral(1) < 1.0


def test_normalize_alpha_basic():
    assert normalize_alpha("  HeLLo  ") == "hello"
    assert normalize_alpha("") == ""
    assert normalize_alpha(None) == ""


def test_normalize_lists():
    nums = normalize_numeral_list([0, 1, -1, 10, "x"])  # type: ignore[list-item]
    assert nums[0] == 0.0
    assert 0 < nums[1] < 1
    assert 0 < nums[-1] < 1

    alphas = normalize_alpha_list([" A ", None, 42, "b"])  # type: ignore[list-item]
    assert alphas == ["a", "b"]

