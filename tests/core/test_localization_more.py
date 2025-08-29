import pytest

from src.table_modifier.localization import String


def test_localizer_get_with_default_for_missing_key():
    assert String.get("__MISSING_KEY__", default="fallback") == "fallback"


def test_localizer_call_with_default_for_missing_key():
    assert String("__MISSING__", default="ok") == "ok"

