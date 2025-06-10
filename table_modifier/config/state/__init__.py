import logging
from pathlib import Path
from threading import Lock
from typing import Dict, Any

from PyQt6.QtCore import QObject, pyqtSignal

from table_modifier.file_interface.factory import FileInterfaceFactory
from table_modifier.file_interface.protocol import FileInterfaceProtocol
from table_modifier.file_status import FileStatus
from table_modifier.gui.emitter import signal_emitter


FilePath = str | Path | FileInterfaceProtocol


def from_file_path(file_path: FilePath) -> FileInterfaceProtocol:
    """
    Convert a file path to a FileInterfaceProtocol instance.

    Args:
        file_path (FilePath): The file path to convert.

    Returns:
        FileInterfaceProtocol: The file interface instance.
    """
    if isinstance(file_path, FileInterfaceProtocol):
        return file_path
    elif isinstance(file_path, str) or isinstance(file_path, Path):
        return FileInterfaceFactory.create(file_path)
    else:
        raise TypeError(
            f"Expected str, Path, or FileInterfaceProtocol, got {type(file_path).__name__}")


class FileListSignals(QObject):
    """
    Signals for the FileList class to notify about file additions and removals.
    """
    fileAdded = pyqtSignal(FileInterfaceProtocol)
    fileRemoved = pyqtSignal(FileInterfaceProtocol)
    fileStatusUpdated = pyqtSignal(FileInterfaceProtocol, FileStatus)
    updated = pyqtSignal()
    listCleared = pyqtSignal()


class FileList:
    """
    A dictionary-like class that holds file paths as keys and their statuses as values.
    It provides a convenient way to manage files and their statuses in the application state.

    It integrates with the application's signal emitter to notify when files are added or removed.
    """
    def __init__(self):
        super().__init__()
        self._lock: Lock = Lock()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._files: Dict[FileInterfaceProtocol, FileStatus] = {}
        self.signals = FileListSignals()

    def append(self, file_path: FilePath, status: FileStatus = FileStatus()) -> None:
        """
        Append a file to the list with its status.

        Args:
            file_path (FilePath): The file path to add.
            status (FileStatus): The status of the file, default is PENDING.
        """
        file_interface = from_file_path(file_path)
        with self._lock:
            if file_interface in self._files:
                self._logger.debug(f"Updating existing file {file_interface} status to {status}")
                self._files[file_interface] = status
                self.signals.fileStatusUpdated.emit(file_interface, status)
            else:
                self._logger.debug(f"Adding new file {file_interface} with status {status}")
                self._files[file_interface] = status
                self.signals.fileAdded.emit(file_interface)
            self._files[file_interface] = status
        self.signals.updated.emit()

    def __setitem__(self, file_path: FilePath, status: FileStatus) -> None:
        """
        Set the status of a file in the list.

        Args:
            file_path (FilePath): The file path to set.
            status (FileStatus): The status to set for the file.
        """
        self.append(file_path, status)

    def __getitem__(self, file_path: FilePath) -> FileStatus:
        """
        Get the status of a file in the list.

        Args:
            file_path (FilePath): The file path to get the status for.

        Returns:
            FileStatus: The status of the file.
        """
        file_interface = from_file_path(file_path)
        with self._lock:
            if file_interface not in self._files:
                raise KeyError(f"File {file_interface} not found in FileList")
            return self._files[file_interface]

    def __delitem__(self, file_path: FilePath) -> None:
        """
        Remove a file from the list.

        Args:
            file_path (FilePath): The file path to remove.
        """
        file_interface = from_file_path(file_path)
        with self._lock:
            if file_interface not in self._files:
                raise KeyError(f"File {file_interface} not found in FileList")
            del self._files[file_interface]
        self.signals.fileRemoved.emit(file_interface)
        self.signals.updated.emit()

    def clear(self) -> None:
        """
        Clear the file list and emit a signal that the list has been cleared.
        """
        with self._lock:
            self._files.clear()
        self.signals.listCleared.emit()
        self._logger.debug("FileList cleared")

    def __contains__(self, file_path: FilePath) -> bool:
        """
        Check if a file is in the list.

        Args:
            file_path (FilePath): The file path to check.

        Returns:
            bool: True if the file is in the list, False otherwise.
        """
        file_interface = from_file_path(file_path)
        with self._lock:
            return file_interface in self._files

    def __set__(self, instance, value):
        """
        Set the value of the file list. This method is not used in this context,
        but it is defined to avoid AttributeError when accessing the property.
        """
        raise AttributeError("FileList is read-only; use __setitem__ to add files.")

    def __len__(self):
        """
        Get the number of files in the list.
        """
        with self._lock:
            return len(self._files)

    def __iter__(self):
        """
        Iterate over the file paths in the list.
        """
        with self._lock:
            return iter(self._files.keys())


class State:
    _controls_lock: Lock = Lock()

    def __init__(self):
        self.tracked_files: FileList = FileList()
        signal_emitter.tracked_files = self.tracked_files.signals

        self._controls: Dict[str, any] = {}

        self._logger = logging.getLogger("table_modifier.state")

    @property
    def controls(self) -> Dict[str, any]:
        """
        Get the current controls state.
        """
        with self._controls_lock:
            return self._controls.copy()

    def maybe_store(self):
        """
        Store the current state of the application if needed.
        This is a placeholder for any state persistence logic.
        """
        self._logger.warning("State is not stored; implement storage logic if needed.")
        pass

    def update_control(self, name_id, new_value: Any = None):
        """
        Update a control value in the state.

        Args:
            name_id (str): The identifier for the control.
            new_value (Any): The new value to set for the control.
        """
        with self._controls_lock:
            self._controls[name_id] = new_value
            signal_emitter.controlUpdated.emit(name_id, new_value)
        self._logger.debug(f"Control '{name_id}' updated to: {new_value}")


state = State()