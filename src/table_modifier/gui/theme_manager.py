from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from PyQt6.QtWidgets import QApplication, QWidget

from src.table_modifier.config.state import state

try:
    # Python 3.9+
    from importlib.resources import files as ir_files
except Exception:  # pragma: no cover
    ir_files = None  # type: ignore

ThemeName = Literal["dark", "light"]


class ThemeManager:
    """Loads and applies QSS themes (common + light/dark) application-wide or to a root widget.

    Usage:
      ThemeManager.apply("dark")  # applies to QApplication.instance()
      ThemeManager.apply("light", root=some_widget)
    """

    @staticmethod
    def themes_dir() -> Path:
        # themes directory relative to this file (dev fallback)
        return Path(__file__).parent / "themes"

    @staticmethod
    def _load_file(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""

    @classmethod
    def load_qss(cls, theme: ThemeName) -> str:
        # Prefer package resources when available
        qss_common = ""
        qss_theme = ""
        if ir_files is not None:
            # Try normal package layout first, then current "src." layout
            for pkg_name in ("table_modifier.gui.themes", "src.table_modifier.gui.themes"):
                try:
                    pkg = ir_files(pkg_name)
                    qss_common = (pkg / "common.qss").read_text(encoding="utf-8")
                    qss_theme = (pkg / f"{theme}.qss").read_text(encoding="utf-8")
                    if qss_common and qss_theme:
                        break
                except Exception:
                    # try next strategy
                    qss_common = ""
                    qss_theme = ""
                    continue
        if not (qss_common and qss_theme):
            base = cls.themes_dir()
            qss_common = cls._load_file(base / "common.qss")
            qss_theme = cls._load_file(base / f"{theme}.qss")
        return (qss_common or "") + "\n\n" + (qss_theme or "")

    @classmethod
    def apply(cls, theme: ThemeName = "dark", root: Optional[QWidget] = None) -> None:
        qss = cls.load_qss(theme)
        state.update_control(f"theme.name", theme)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(qss)
        elif root is not None:
            root.setStyleSheet(qss)
        # else: nothing to apply yet
