"""List models for the FileSelector widget."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Any

from PyQt6.QtCore import QAbstractListModel, Qt, QModelIndex

from src.table_modifier.config.state import state
from src.table_modifier.file_interface.factory import FileInterfaceFactory


class FileModel(QAbstractListModel):
    """Model representing either available files in a directory or tracked files.

    - When state_name is None: lists files in the currently selected directory
      that can be handled by any registered file handler.
    - When state_name == "tracked_files": lists files added to state.tracked_files.
    """

    def __init__(self, parent: Optional[Any] = None, state_name: Optional[str] = None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.state_name = state_name
        self.files: List[Path] = []

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        """Return the data for the given index and role."""
        if not index.isValid() or index.row() < 0 or index.row() >= len(self.files):
            return None
        path = self.files[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return path.name
        if role == Qt.ItemDataRole.UserRole:
            return path
        return None

    def update(self, sender: str, **kwargs):
        """Refresh the model from state.tracked_files."""
        self.logger.debug("Updating file model with current tracked files")
        self.beginResetModel()
        self.files = [f.path for f in state.tracked_files.all()]
        self.endResetModel()
        self.logger.info("File model updated with %d files", len(self.files))

    def update_files_from_folder_path(self, sender: str, **kwargs) -> None:
        """Load files from provided directory that handlers can process."""
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
        finally:
            self.endResetModel()
        self.logger.info("Loaded %d files from %s", len(self.files), directory)

    def rowCount(self, parent: Optional[QModelIndex] = None) -> int:  # type: ignore[override]
        """Return the number of rows in the model."""
        return len(self.files)