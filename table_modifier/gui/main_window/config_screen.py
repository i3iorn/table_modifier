from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout, \
    QSpacerItem, QSizePolicy

from table_modifier.config import controls
from table_modifier.localizer import String


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
        self.widgets = None
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
        title_label = QLabel(String["CONFIG_SCREEN_TITLE"], self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.layout().addWidget(title_label)

        for group_name, group in controls.items():
            group_widget = QWidget(self)
            group_name_title = group_name.title().replace("_", " ")
            group_label = QLabel(group_name_title, group_widget)
            group_layout = QVBoxLayout(group_widget)

            group_layout.addWidget(group_label)
            group_layout.setContentsMargins(0, 0, 0, 0)

            group_widget.setLayout(group_layout)
            self.layout().addWidget(group_widget)

            controls_layout = QVBoxLayout()
            group_layout.addLayout(controls_layout)

            for control_name, control in group.items():
                control_layout = QHBoxLayout(self)
                controls_layout.addLayout(control_layout)
                control_layout.addWidget(QLabel(control["label"], group_widget))
                if control["class"] == QComboBox:
                    combo = QComboBox(group_widget)
                    combo.addItems(control["items"])
                    combo.setCurrentText(control.get("default", control["items"][0]))
                    control_layout.addWidget(combo)
                else:
                    raise ValueError(f"Unsupported control type: {control['class']}")

        # Add a spacer to push the controls to the top
        spacer = QSpacerItem(1, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.layout().addItem(spacer)
