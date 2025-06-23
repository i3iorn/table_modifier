import logging

from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListView, QHBoxLayout

from src.table_modifier.config.state import state
from src.table_modifier.gui.main_window.file_selector.models import FileModel
from src.table_modifier.signals import ON


class FileSelectorWidget(QWidget):
    """
    A widget for selecting a file from a list of files.

    The widget displays a list view of files available in the current directory that
    can be handled by one of the file interface handlers. It allows the user to select
    a file, which can then be processed by the application.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_files_view = None
        self.selected_files_model = None
        self.file_view: QListView = None
        self.file_model: FileModel = None
        self.setLayout(QVBoxLayout(self))
        self.state = state
        self.logger = logging.getLogger(self.__class__.__name__)

        self.init_ui()
        self.connect_signals()

    def init_ui(self) -> None:
        """
        Initialize the user interface components of the file selector widget.
        This method sets up the layout and any necessary widgets for file selection.
        """
        label = QLabel("Select a file from the list below:")
        self.layout().addWidget(label)

        box_layout = QHBoxLayout(self)

        self.file_model = FileModel(self)
        ON("directory.updated", self.file_model.update_files_from_folder_path)

        self.file_view = QListView(self)
        self.file_view.setModel(self.file_model)
        self.file_view.setSelectionMode(
            QListView.SelectionMode.SingleSelection
        )

        self.selected_files_model = FileModel(self, "tracked_files")
        self.selected_files_view = QListView(self)
        self.selected_files_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.selected_files_view.setModel(self.selected_files_model)
        self.selected_files_view.setSelectionMode(
            QListView.SelectionMode.SingleSelection
        )
        ON("state.file.tracked_files.*", self.selected_files_model.update)

        box_layout.addWidget(self.file_view, 2)
        box_layout.addWidget(self.selected_files_view, 1)
        state.container.selected_files_model = self.selected_files_model
        self.layout().addLayout(box_layout)

    def connect_signals(self) -> None:
        """
        Connect signals to handle user interactions with the file selector widget.
        """
        self.file_view.doubleClicked.connect(self.on_file_double_clicked)
        self.selected_files_view.doubleClicked.connect(self.on_selected_files_double_clicked)

    def on_file_double_clicked(self, index: QModelIndex) -> None:
        """
        Handle the double-click event on a file in the list view.

        This method retrieves the file path from the clicked index and emits a signal
        to update the selected files in the application state.
        """
        if not index.isValid():
            return

        file_path = self.file_model.data(index, role=Qt.ItemDataRole.UserRole)
        if not file_path:
            return

        self.logger.debug(f"File selected: {file_path}")
        if file_path not in self.state.tracked_files:
            state.tracked_files.append(file_path)
        else:
            self.logger.info(f"File {file_path} is already selected.")

    def on_selected_files_double_clicked(self, index: QModelIndex) -> None:
        """
        Handle the double-click event on a selected file in the list view.

        This method retrieves the file path from the clicked index and emits a signal
        to remove the file from the selected files in the application state.
        """
        if not index.isValid():
            return

        file_path = self.selected_files_model.data(index, role=Qt.ItemDataRole.UserRole)
        if not file_path:
            return

        self.logger.debug(f"Removing selected file: {file_path}")
        if file_path in self.state.tracked_files:
            del self.state.tracked_files[file_path]
        else:
            self.logger.warning(f"File {file_path} is not in the tracked files.")