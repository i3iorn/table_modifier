import logging
from typing import Dict, Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox,
    QHBoxLayout, QSpacerItem, QSizePolicy,
    QGroupBox, QFormLayout, QCheckBox, QPushButton
)

from src.table_modifier.config import controls
from src.table_modifier.config.state import state
from src.table_modifier.localization import String


class ConfigScreen(QWidget):
    """
    A widget that contains controls for the main window.
    This widget is used to add buttons and other controls to the main window.
    """
    def __init__(self, parent=None):
        """
        Initialize the ControlsWidget.
        :param parent: The parent widget.
        """
        super().__init__(parent)
        self.widgets: Dict[str, QWidget] = {}
        self.setLayout(QVBoxLayout())

        self.init_ui()

    def init_ui(self):
        """
        Dynamically create controls based on the configuration.

        This method reads the configuration from `controls` and creates
        the appropriate widgets (e.g., buttons, combo boxes) for the main window.
        It stores the created widgets in the `self.widgets` dictionary for easy access.
        Values are stored in the `self.state` for later use. Signals are connected that
        update the state when the controls are changed.
        """
        if not isinstance(controls, dict):
            raise RuntimeError("Invalid controls config: expected dict")
        title_label = QLabel(String["CONFIG_SCREEN_TITLE"], self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.layout().addWidget(title_label)

        for group_key, group_cfg in controls.items():
            if not isinstance(group_cfg, list):
                logging.error(f"Skipping group '{group_key}': expected a list of control configs.")
                continue
            group_box = QGroupBox(String[group_key], self)
            form = QFormLayout()
            for cfg in group_cfg:
                label = QLabel(String[cfg.get("label")], self)
                widget = self._create_control(cfg)
                self.widgets[cfg["name"]] = widget
                state.add_control(cfg["name"], cfg.get("default", None))
                form.addRow(label, widget)
            group_box.setLayout(form)
            self.layout().addWidget(group_box)

        # Add a spacer to push the controls to the top
        spacer = QSpacerItem(1, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.layout().addItem(spacer)

    def _create_control(self, cfg: dict) -> QWidget:
        t = cfg.get("type")
        name = cfg.get("name")
        if t == "combo":
            combo = QComboBox(self)
            combo.addItems(cfg.get("items", []))
            combo.setCurrentText(str(cfg.get("default", "")))
            combo.currentTextChanged.connect(lambda v, key=name: self._on_value_changed(key, v))
            return combo
        if t == "checkbox":
            cb = QCheckBox(self)
            cb.setChecked(bool(cfg.get("default", False)))
            cb.stateChanged.connect(lambda s, key=name: self._on_value_changed(key, bool(s)))
            return cb
        if t == "button":
            btn = QPushButton(String[cfg.get("label")], self)
            btn.clicked.connect(cfg.get("callback"))
            return btn
        logging.warning(f"Unknown control type '{t}' for '{name}'")
        return QLabel(f"Unsupported: {t}", self)

    def _on_value_changed(self, key: str, value: Any) -> None:
        """Update internal state when a control’s value changes."""
        state[key] = value
