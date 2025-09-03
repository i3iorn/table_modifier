"""File selection widget showing available and tracked files side by side."""

import logging
from typing import Optional

from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListView, QHBoxLayout, \
    QLineEdit, QPushButton

from src.table_modifier.config.state import state
from src.table_modifier.constants import NO_MARGIN
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

        # Top-level layout
        main_layout = self.layout()

        # Label
        label = QLabel(
            String.get("FILE_SELECTOR_HINT", "Select a file from the list below:"))
        main_layout.addWidget(label)

        # File model
        self.file_model = FileModel(self)

        # Filters (horizontal)
        filter_layout = QHBoxLayout()

        self.file_filter = QLineEdit(self)
        self.file_filter.setPlaceholderText(
            String.get("FILE_FILTER_PLACEHOLDER", "Filter files..."))
        self.file_filter.textChanged.connect(self.file_model.apply_filter)
        filter_layout.addWidget(self.file_filter)

        kundkod_regex_btn = QPushButton(
            String.get("FILE_FILTER_KUNDKOD_REGEX_BTN", "Kundkoder"))
        kundkod_regex_btn.clicked.connect(
            lambda: self.file_filter.setText(r"^.*[A-Z]{3}[0-9]{1,4}.*$"))
        filter_layout.addWidget(kundkod_regex_btn)

        main_layout.addLayout(filter_layout)  # ✅ Add the horizontal filter layout

        # Views (horizontal)
        view_layout = QHBoxLayout()

        self.file_view = QListView(self)
        self.file_view.setModel(self.file_model)
        self.file_view.setSelectionMode(QListView.SelectionMode.SingleSelection)
        view_layout.addWidget(self.file_view, 2)

        self.selected_files_model = FileModel(self, "tracked_files")
        self.selected_files_view = QListView(self)
        self.selected_files_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.selected_files_view.setModel(self.selected_files_model)
        self.selected_files_view.setSelectionMode(
            QListView.SelectionMode.SingleSelection)
        view_layout.addWidget(self.selected_files_view, 1)

        main_layout.addLayout(view_layout)  # ✅ Add the horizontal view layout

        # Signal connections
        from src.table_modifier.signals import \
            ON  # local import to avoid cycles at import time
        ON("directory.updated", self.file_model.update_files_from_folder_path)
        ON("state.file.tracked_files.*", self.selected_files_model.update)
        ON("file_selector.filter.regex.error", self.on_filter_error)
        ON("file_selector.filter.regex.applied", self.on_filter_applied)

        # Store selected model in state
        state.container.selected_files_model = self.selected_files_model

    def connect_signals(self) -> None:
        """Connect interactions for both lists."""
        self.file_view.doubleClicked.connect(self.on_file_double_clicked)
        self.selected_files_view.doubleClicked.connect(self.on_selected_files_double_clicked)

    def on_filter_error(self, sender, error: str, **kwargs) -> None:
        """Show an error message when the filter is invalid."""
        self.logger.error("Invalid filter: %s", error)
        self.file_filter.setProperty("input_error", True)
        self.file_filter.style().unpolish(self.file_filter)
        self.file_filter.style().polish(self.file_filter)

    def on_filter_applied(self, sender, **kwargs) -> None:
        """Clear the input error state when the filter is applied."""
        self.file_filter.setProperty("input_error", False)
        self.file_filter.style().unpolish(self.file_filter)
        self.file_filter.style().polish(self.file_filter)

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
