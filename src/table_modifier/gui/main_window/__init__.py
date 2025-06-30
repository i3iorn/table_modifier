from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QTabWidget

from src.table_modifier.config.state import state
from src.table_modifier.gui.main_window.config_screen import ConfigScreen
from src.table_modifier.gui.main_window.file_selector import FileSelectorWidget
from src.table_modifier.gui.main_window.folder_selector import FolderSelectorWidget
from src.table_modifier.gui.main_window.input_screen import InputScreen
from src.table_modifier.gui.main_window.map_screen import MapScreen
from src.table_modifier.signals import ON


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        ON("status.update", self.update_status_bar)
        self.setWindowTitle("Table Modifier")
        self.setGeometry(100, 100, 800, 600)

        self.main_layout = QVBoxLayout()
        self.init_ui()

    def init_ui(self):
        # Create a central widget with tabs
        cw = QTabWidget(self)
        cw.setLayout(self.main_layout)
        self.setCentralWidget(cw)

        cw.addTab(InputScreen(self), "Input Screen")
        cw.addTab(ConfigScreen(self), "Configuration")
        cw.addTab(MapScreen(self), "Map Columns")
        cw.setTabEnabled(2, False)  # Disable Map Columns tab initially

        ON("state.file.tracked_files.file.count", self.map_screen_enabled)

        self.init_menu_bar()

    def map_screen_enabled(self, sender, count: int, **kwargs):
        """Enable the screen if there are tracked files."""
        if count > 0:
            self.centralWidget().setTabEnabled(2, True)
        else:
            self.centralWidget().setTabEnabled(2, False)

    def init_menu_bar(self):
        self.menuBar().setNativeMenuBar(False)
        self.menu_bar = self.menuBar()

    def update_status_bar(self, sender, msg, timeout=8000, **kwargs):
        sender_class = sender.split(":")[-1].split(".")[0]
        msg = f"{sender_class}: {msg}"
        self.statusBar().showMessage(msg,timeout)

    def show_about_dialog(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(self, "About Table Modifier", "Table Modifier v1.0\nA simple tool for modifying tabular data.")

    def closeEvent(self, event):
        """
        Handle the close event to clean up resources.
        """
        state.maybe_store()
        super().closeEvent(event)
