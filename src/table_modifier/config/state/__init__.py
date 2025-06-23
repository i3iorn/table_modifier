import logging
from threading import Lock
from typing import Dict, Any, List

from src.table_modifier.file_interface.protocol import FileInterfaceProtocol
from src.table_modifier.file_interface.utils import from_file_path, FilePath
from src.table_modifier.file_status import FileStatus
from src.table_modifier.signals import EMIT


class FileList:
    """
    A dictionary-like class that holds file paths as keys and their statuses as values.
    It provides a convenient way to manage files and their statuses in the application state.

    It integrates with the application's signal emitter to notify when files are added or removed.
    """
    def __init__(self, name: str):
        super().__init__()
        self._name = name
        self._lock: Lock = Lock()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._files: Dict[FileInterfaceProtocol, FileStatus] = {}

    def all(self) -> List[FileInterfaceProtocol]:
        """
        Get all file paths in the list.

        Returns:
            List[FileInterfaceProtocol]: A list of all file paths.
        """
        with self._lock:
            return list(self._files.keys())

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
                action = "updated"
            else:
                action = "added"
            self._files[file_interface] = status

        self._logger.debug(f"{action.title()}{' existing' if action == 'updated' else ''} file {file_interface} status to {status}")
        EMIT(f"state.file.{self._name}.{action}", file=file_interface, status=status)

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
        EMIT(f"state.file.{self._name}.deleted", file=file_interface)

    def clear(self) -> None:
        """
        Clear the file list and emit a signal that the list has been cleared.
        """
        with self._lock:
            self._files.clear()
        EMIT(f"file.{self._name}.cleared")
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
            files = list(self._files.keys()).copy()
        return iter(files)


class Container:
    pass


class State:
    _controls_lock: Lock = Lock()

    def __init__(self):
        self.container: Container = Container()
        self.tracked_files: FileList = FileList("tracked_files")
        self._controls: Dict[str, any] = {}
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

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
            EMIT(f"control.{name_id}.updated", control=name_id, new_value=new_value)
        self._logger.debug(f"Control '{name_id}' updated to: {new_value}")


state = State()