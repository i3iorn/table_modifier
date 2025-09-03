"""List models for the FileSelector widget."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Optional, Any

from PyQt6.QtCore import QAbstractListModel, Qt, QModelIndex

from src.table_modifier.config.state import state
from src.table_modifier.file_interface.factory import FileInterfaceFactory
from src.table_modifier.signals import EMIT


class FileModel(QAbstractListModel):
    """Model representing either available files in a directory or tracked files.

    - When state_name is None: lists files in the currently selected directory
      that can be handled by any registered file handler.
    - When state_name == "tracked_files": lists files added to state.tracked_files.
    """

    def __init__(self, parent: Optional[Any] = None, state_name: Optional[str] = None):
        super().__init__(parent)
        self._filter_applied = None
        self.filtered_files = []
        self.logger = logging.getLogger(self.__class__.__name__)
        self.state_name = state_name
        self.files: List[Path] = []

    def apply_filter(self, pattern: str) -> None:
        """Filter files using a regex pattern on file names."""
        if not pattern:
            self.filtered_files = self.files.copy()
        else:
            try:
                regex = re.compile(pattern)
                self.filtered_files = [f for f in self.files if regex.search(f.name)]
                EMIT("file_selector.filter.regex.applied")
            except re.error as e:
                self.filtered_files = self.files.copy()
                EMIT("file_selector.filter.regex.error", error=str(e))
        self.layoutChanged.emit()

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not hasattr(self, "filtered_files"):
            self.filtered_files = self.files
        if not index.isValid() or index.row() < 0 or index.row() >= len(
                self.filtered_files):
            return None
        path = self.filtered_files[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return path.name
        if role == Qt.ItemDataRole.UserRole:
            return path
        return None

    def update(self, sender: str, **kwargs):
        self.logger.debug("Updating file model with current tracked files")
        self.beginResetModel()
        self.files = [f.path for f in state.tracked_files.all()]
        self.filtered_files = self.files.copy()
        self.endResetModel()
        self.logger.info("File model updated with %d files", len(self.files))

    def update_files_from_folder_path(self, sender: str, **kwargs) -> None:
        directory = kwargs.get("directory")
        if not directory:
            return
        self.logger.debug("Updating files from folder: %s", directory)
        root = Path(directory)
        self.beginResetModel()
        try:
            self.files = [
                file
                for file in root.glob("*")
                if file.is_file() and FileInterfaceFactory.can_handle(file.as_posix())
            ]
            self.filtered_files = self.files.copy()
        finally:
            self.endResetModel()
        self.logger.info("Loaded %d files from %s", len(self.files), directory)

    def rowCount(self,
                 parent: Optional[QModelIndex] = None) -> int:  # type: ignore[override]
        if not hasattr(self, "filtered_files"):
            self.filtered_files = self.files
        return len(self.filtered_files)