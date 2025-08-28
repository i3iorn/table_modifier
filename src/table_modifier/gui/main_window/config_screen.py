"""Configuration screen for the main window.

Dynamically builds controls based on a configuration mapping.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, TypedDict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QSpacerItem,
    QSizePolicy,
    QGroupBox,
    QFormLayout,
    QCheckBox,
    QPushButton,
)

from src.table_modifier.config import controls
from src.table_modifier.config.state import state
from src.table_modifier.localization import String


logger = logging.getLogger(__name__)


class ControlConfig(TypedDict, total=False):
    """Typed representation of a single control config entry."""

    type: str  # "combo" | "checkbox" | "button"
    name: str
    label: str
    items: List[str]
    default: Any
    callback: Callable[[], None]


class ConfigScreen(QWidget):
    """A widget that contains dynamically created configuration controls."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.widgets: Dict[str, QWidget] = {}

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.init_ui()

    def init_ui(self) -> None:
        """Create controls based on the configuration map."""
        if not isinstance(controls, dict):
            raise RuntimeError("Invalid controls config: expected dict")

        title_label = QLabel(String["CONFIG_SCREEN_TITLE"], self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        assert self.layout() is not None
        self.layout().addWidget(title_label)

        for group_key, group_cfg in controls.items():
            if not isinstance(group_cfg, list):
                logger.error(
                    "Skipping group '%s': expected a list of control configs.", group_key
                )
                continue

            group_box = QGroupBox(String[group_key], self)
            form = QFormLayout()

            for cfg in group_cfg:
                # Defensive checks for required fields
                name = cfg.get("name") if isinstance(cfg, dict) else None
                label_key = cfg.get("label") if isinstance(cfg, dict) else None
                if not name or not label_key:
                    logger.error(
                        "Skipping control in group '%s': missing 'name' or 'label' in config %r",
                        group_key,
                        cfg,
                    )
                    continue

                label = QLabel(String[label_key], self)
                widget = self._create_control(cfg)  # type: ignore[arg-type]
                self.widgets[name] = widget
                state.add_control(name, cfg.get("default", None))
                form.addRow(label, widget)

            group_box.setLayout(form)
            assert self.layout() is not None
            self.layout().addWidget(group_box)

        # Add a spacer to push the controls to the top
        spacer = QSpacerItem(1, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        assert self.layout() is not None
        self.layout().addItem(spacer)

    def _create_control(self, cfg: ControlConfig) -> QWidget:
        t = cfg.get("type")
        name = cfg.get("name")

        if t == "combo":
            combo = QComboBox(self)
            items = list(cfg.get("items", []) or [])
            combo.addItems(items)

            default = cfg.get("default")
            if isinstance(default, str) and default in items:
                combo.setCurrentText(default)
            elif items:
                combo.setCurrentIndex(0)

            combo.currentTextChanged.connect(lambda v, key=name: self._on_value_changed(key or "", v))
            return combo

        if t == "checkbox":
            cb = QCheckBox(self)
            cb.setChecked(bool(cfg.get("default", False)))
            cb.stateChanged.connect(
                lambda s, key=name: self._on_value_changed(key or "", Qt.CheckState(s) == Qt.CheckState.Checked)
            )
            return cb

        if t == "button":
            label_key = cfg.get("label", "")
            btn = QPushButton(String(label_key, default=label_key), self)
            callback = cfg.get("callback")
            if callable(callback):
                btn.clicked.connect(callback)  # type: ignore[arg-type]
            else:
                logger.warning("Button '%s' has no callable callback.", name)
                btn.setEnabled(False)
            return btn

        logger.warning("Unknown control type '%s' for '%s'", t, name)
        return QLabel(f"Unsupported: {t}", self)

    def _on_value_changed(self, key: str, value: Any) -> None:
        """Update internal state when a control's value changes."""
        if not key:
            return
        state[key] = value
