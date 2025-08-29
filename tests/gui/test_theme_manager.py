import pytest
from src.table_modifier.gui.theme_manager import ThemeManager


def test_load_qss_matches_files_dark():
    base = ThemeManager.themes_dir()
    expected = (base / "common.qss").read_text(encoding="utf-8") + "\n\n" + (
        base / "dark.qss"
    ).read_text(encoding="utf-8")
    qss = ThemeManager.load_qss("dark")
    assert isinstance(qss, str)
    assert qss.strip() != ""
    # Accept minor whitespace differences
    assert expected.replace("\r\n", "\n").strip() in qss.replace("\r\n", "\n").strip()


def test_load_qss_matches_files_light():
    base = ThemeManager.themes_dir()
    expected = (base / "common.qss").read_text(encoding="utf-8") + "\n\n" + (
        base / "light.qss"
    ).read_text(encoding="utf-8")
    qss = ThemeManager.load_qss("light")
    assert isinstance(qss, str)
    assert qss.strip() != ""
    assert expected.replace("\r\n", "\n").strip() in qss.replace("\r\n", "\n").strip()

