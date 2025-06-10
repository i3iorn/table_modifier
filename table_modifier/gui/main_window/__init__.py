from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QSpacerItem, QSizePolicy, QWidget

from table_modifier.config.state import state, State
from table_modifier.gui.main_window.controls import ControlsWidget
from table_modifier.gui.main_window.file_selector import FileSelectorWidget
from table_modifier.gui.main_window.folder_selector import FolderSelectorWidget
from table_modifier.gui.main_window.log_viewer import LogViewerWidget


class MainWindow(QMainWindow):
    def __init__(self, parent=None, saved_state: State = None):
        super().__init__(parent)
        self.setWindowTitle("Table Modifier")
        self.setGeometry(100, 100, 800, 600)
        self.state = saved_state or state
        self.main_layout = QVBoxLayout()
        self.init_ui()

    def init_ui(self):
        cw = QWidget(self)
        cw.setLayout(self.main_layout)
        self.setCentralWidget(cw)

        self.init_folder_selector()
        self.init_file_selector()
        self.init_controls()
        self.init_log_viewer()
        self.init_status_bar()
        self.init_menu_bar()

        self.layout().addItem(QSpacerItem(
            0, 0, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum
        ))

    def init_folder_selector(self):
        self.folder_selector = FolderSelectorWidget(self.centralWidget())
        self.main_layout.addWidget(self.folder_selector)

    def init_file_selector(self):
        self.file_selector = FileSelectorWidget(self.centralWidget())
        self.main_layout.addWidget(self.file_selector)

    def init_controls(self):
        self.controls = ControlsWidget(self.centralWidget())
        self.main_layout.addWidget(self.controls)

    def init_log_viewer(self):
        self.log_viewer = LogViewerWidget(self.centralWidget())
        self.main_layout.addWidget(self.log_viewer)

    def init_status_bar(self):
        self.statusBar().showMessage("Ready")
        self.status_bar = self.statusBar()

    def init_menu_bar(self):
        self.menuBar().setNativeMenuBar(False)
        self.menu_bar = self.menuBar()
        """
        # Add file menu
        file_menu = self.menuBar().addMenu("File")
        open_action = file_menu.addAction("Open")
        open_action.triggered.connect(self.injection_container.file_selector.open_file_dialog)

        save_action = file_menu.addAction("Save")
        save_action.triggered.connect(self.injection_container.file_selector.save_file_dialog)

        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        # Add help menu
        help_menu = self.menuBar().addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about_dialog)
        """

    def show_about_dialog(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(self, "About Table Modifier", "Table Modifier v1.0\nA simple tool for modifying tabular data.")

    def closeEvent(self, event):
        """
        Handle the close event to clean up resources.
        """
        self.state.maybe_store()
        super().closeEvent(event)
