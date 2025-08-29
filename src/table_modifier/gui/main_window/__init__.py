"""Main application window for the Table Modifier GUI.

Defines the top-level QMainWindow and orchestrates the main screens as tabs.
"""

from typing import Any, Optional

from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget

from src.table_modifier.config.state import state
from src.table_modifier.gui.main_window.config_screen import ConfigScreen
from src.table_modifier.gui.main_window.input_screen import InputScreen
from src.table_modifier.gui.main_window.map_screen import MapScreen
from src.table_modifier.gui.main_window.status_screen import StatusScreen
from src.table_modifier.gui.theme_manager import ThemeManager
from src.table_modifier.localization import String
from src.table_modifier.signals import ON


class MainWindow(QMainWindow):
    """Top-level window embedding the main application tabs.

    Tabs:
    - InputScreen: initial inputs and selections
    - ConfigScreen: configuration options
    - MapScreen: column mapping (enabled once files are tracked)
    - StatusScreen: processing status
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        ON("status.update", self.update_status_bar)
        ON("processing.current.updated", self._open_status_tab)
        self.setWindowTitle("Table Modifier")
        self.setGeometry(100, 100, 800, 600)

        # Keep a reference to the tab widget for clearer access later.
        self._tabs: QTabWidget
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the central tab widget and menu bar."""
        # Apply theme (default to dark). This applies to the whole application.
        ThemeManager.apply("light")
        # Create a central widget with tabs
        tabs = QTabWidget(self)
        self.setCentralWidget(tabs)
        self._tabs = tabs

        tabs.addTab(InputScreen(self), String["INPUT_SCREEN_TITLE"])  # 0
        tabs.addTab(ConfigScreen(self), String["CONFIG_SCREEN_TITLE"])  # 1
        tabs.addTab(MapScreen(self), String["MAP_SCREEN_TITLE"])  # 2
        tabs.addTab(StatusScreen(self), String["STATUS_TAB_TITLE"])  # 3
        tabs.setTabEnabled(2, False)  # Disable Map Columns tab initially
        tabs.setTabEnabled(3, False)  # Disable Status tab initially

        ON("state.file.tracked_files.file.count", self.map_screen_enabled)

        self.init_menu_bar()


    def map_screen_enabled(self, sender: str, count: int, **kwargs: Any) -> None:
        """Enable the Map Columns tab when there are tracked files."""
        self._tabs.setTabEnabled(2, count > 0)

    def _open_status_tab(self, sender: Any, **kwargs: Any) -> None:
        """Enable and switch to the Status tab when processing starts."""
        self._tabs.setTabEnabled(3, True)
        self._tabs.setCurrentIndex(3)

    def init_menu_bar(self) -> None:
        """Initialize a non-native (cross-platform) menu bar."""
        self.menuBar().setNativeMenuBar(False)
        self.menu_bar = self.menuBar()

    def update_status_bar(self, sender: Any, msg: str, timeout: int = 8000, **kwargs: Any) -> None:
        """Update the status bar with a formatted message.

        Args:
            sender: Origin identifier of the message (string-like).
            msg: Message content.
            timeout: Display duration in milliseconds.
        """
        sender_str = str(sender)
        sender_class = sender_str.split(":")[-1].split(".")[0]
        formatted = f"{sender_class}: {msg}"
        self.statusBar().showMessage(formatted, timeout)

    def show_about_dialog(self) -> None:
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.about(
            self,
            "About Table Modifier",
            "Table Modifier v1.0\nA simple tool for modifying tabular data.",
        )

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Handle the close event to persist state and clean up."""
        state.maybe_store()
        super().closeEvent(event)
