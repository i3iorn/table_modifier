from PyQt6.QtWidgets import QWidget, QComboBox, QHBoxLayout

from table_modifier.config import controls
from table_modifier.config.state import state


class ControlsWidget(QWidget):
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
        self.setLayout(QHBoxLayout())
        self.state = state

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
        self.widgets = {}
        for name_id, control in controls.items():
            widget = control["class"](self)
            widget.setObjectName(name_id)
            self.layout().addWidget(widget)

            if isinstance(widget, QComboBox):
                widget.addItems(control["items"])
                widget.activated.connect(self.connect_conbox_signal)
        # self.add_buttons()

    def connect_conbox_signal(self, index: int):
        """
        Handle the signal emitted by a combo box when an item is selected.

        This method updates the state with the selected value from the combo box.
        :param index: The index of the selected item in the combo box.
        """
        sender = self.sender()
        if isinstance(sender, QComboBox):
            self.state.update_control(sender.objectName(), sender.itemText(index))
