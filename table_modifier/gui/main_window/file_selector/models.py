import logging
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import QAbstractListModel, Qt

from table_modifier.config.state import state
from table_modifier.file_interface.factory import FileInterfaceFactory


class FileModel(QAbstractListModel):
    """
    A model for managing a list of files in a QListView.

    This model is used to display a list of files that can be selected by the user.
    It inherits from QAbstractListModel and provides methods to manage the file list.
    """
    def __init__(self, parent=None, state_name: Optional[str] = None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.state_name = state_name
        self.files = []

    def data(self, index, role: int = Qt.ItemDataRole.DisplayRole):
        """
        Return the data for the given index and role.

        :param index: The index of the item to retrieve.
        :param role: The role of the data to retrieve.
        :return: The file name if the role is DisplayRole, otherwise None.
        """
        if not index.isValid() or index.row() >= len(self.files):
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self.files[index.row()].name
        elif role == Qt.ItemDataRole.UserRole:
            return self.files[index.row()]
        return None

    def update(self, sender, **kwargs):
        """
        Update the model with the current list of files.

        This method is called to refresh the model's data.
        It emits dataChanged signal to notify views about the update.
        """
        if self.state_name is None:
            self.logger.warning("State name is not set, cannot update file model without arguments.")
            return
        self.logger.debug("Updating file model")
        self.beginResetModel()
        self.files = list(getattr(state, self.state_name, []))
        self.endResetModel()
        self.logger.info(f"File model updated with {len(self.files)} files")

    def update_files_from_folder_path(self, sender, **kwargs):
        """
        Update the model with files from the specified folder path.

        :param directory: The path to the folder from which to load files.
        """
        directory = kwargs.get("directory")
        self.logger.debug(f"Updating files from folder: {directory}")
        self.beginResetModel()
        self.files = [
            file
            for file
            in Path(directory).glob("*")
            if file.is_file()
               and FileInterfaceFactory.can_handle(file.as_posix())
        ]
        self.endResetModel()
        self.logger.info(f"Loaded {len(self.files)} files from {directory}")

    def rowCount(self, parent=None):
        """
        Return the number of rows in the model.

        :param parent: Not used, required by QAbstractListModel.
        :return: The number of files in the model.
        """
        return len(self.files)