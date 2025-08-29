import pytest
from src.table_modifier.constants import NO_MARGIN


def test_no_margin_tuple():
    assert isinstance(NO_MARGIN, tuple)
    assert NO_MARGIN == (0, 0, 0, 0)

