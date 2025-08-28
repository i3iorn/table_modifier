"""File selection widget showing available and tracked files side by side."""

import logging
from typing import Optional

from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListView, QHBoxLayout

from src.table_modifier.config.state import state
from src.table_modifier.gui.main_window.file_selector.models import FileModel
from src.table_modifier.localization import String


class FileSelectorWidget(QWidget):
    """Widget for selecting files from a directory and managing tracked files."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.selected_files_view: QListView
        self.selected_files_model: FileModel
        self.file_view: QListView
        self.file_model: FileModel
        self.setLayout(QVBoxLayout(self))
        self.state = state
        self.logger = logging.getLogger(self.__class__.__name__)

        self.init_ui()
        self.connect_signals()

    def init_ui(self) -> None:
        """Initialize the UI and models/views."""
        label = QLabel(String.get("FILE_SELECTOR_HINT", "Select a file from the list below:"))
        self.layout().addWidget(label)

        box_layout = QHBoxLayout(self)

        self.file_model = FileModel(self)
        # Refresh available files when directory changes
        from src.table_modifier.signals import ON  # local import to avoid cycles at import time
        ON("directory.updated", self.file_model.update_files_from_folder_path)

        self.file_view = QListView(self)
        self.file_view.setModel(self.file_model)
        self.file_view.setSelectionMode(QListView.SelectionMode.SingleSelection)

        self.selected_files_model = FileModel(self, "tracked_files")
        self.selected_files_view = QListView(self)
        self.selected_files_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.selected_files_view.setModel(self.selected_files_model)
        self.selected_files_view.setSelectionMode(QListView.SelectionMode.SingleSelection)

        ON("state.file.tracked_files.*", self.selected_files_model.update)

        box_layout.addWidget(self.file_view, 2)
        box_layout.addWidget(self.selected_files_view, 1)
        state.container.selected_files_model = self.selected_files_model
        self.layout().addLayout(box_layout)

    def connect_signals(self) -> None:
        """Connect interactions for both lists."""
        self.file_view.doubleClicked.connect(self.on_file_double_clicked)
        self.selected_files_view.doubleClicked.connect(self.on_selected_files_double_clicked)

    def on_file_double_clicked(self, index: QModelIndex) -> None:
        """Add a file to tracked files when double-clicked on the available list."""
        if not index.isValid():
            return

        file_path = self.file_model.data(index, role=Qt.ItemDataRole.UserRole)
        if not file_path:
            return

        self.logger.debug(f"File selected: {file_path}")
        if file_path not in self.state.tracked_files:
            state.tracked_files.append(file_path)
        else:
            self.logger.info("File %s is already selected.", file_path)

    def on_selected_files_double_clicked(self, index: QModelIndex) -> None:
        """Remove a tracked file when double-clicked in the tracked list."""
        if not index.isValid():
            return

        file_path = self.selected_files_model.data(index, role=Qt.ItemDataRole.UserRole)
        if not file_path:
            return

        self.logger.debug(f"Removing selected file: {file_path}")
        if file_path in self.state.tracked_files:
            del self.state.tracked_files[file_path]
        else:
            self.logger.warning("File %s is not in the tracked files.", file_path)
