import pytest

import re

from src.table_modifier.localization import String


def test_translate_with_formatting_and_missing_var():
    # With formatting arg
    s = String.translate("STATUS_PROGRESS", value=42)
    assert "42%" in s
    # Missing var yields helpful marker
    s2 = String.translate("STATUS_PROGRESS")
    assert "Missing var: value" in s2


def test_language_switch_and_fallback():
    # Default language is 'en' with known keys
    assert isinstance(String["MAP_SCREEN_TITLE"], str)
    # Switching to a non-existing language raises
    try:
        String.set_language("zz")
        raised = False
    except ValueError:
        raised = True
    assert raised, "Expected ValueError for unknown language"
    # Ensure still usable after failed switch
    assert isinstance(String["INPUT_SCREEN_TITLE"], str)

