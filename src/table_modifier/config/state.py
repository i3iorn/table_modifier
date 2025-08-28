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
        self._logger = logging.getLogger(self.__class__.__name__)
        self._files: Dict[FileInterfaceProtocol, FileStatus] = {}

    def all(self) -> List[FileInterfaceProtocol]:
        """Return all file interfaces in the list."""
        with self._lock:
            return list(self._files.keys())

    def append(self, file_path: FilePath, status: FileStatus = FileStatus()) -> None:
        """Append or update a file with status and emit signals accordingly."""
        file_interface = from_file_path(file_path)
        with self._lock:
            if file_interface in self._files:
                action = "updated"
            else:
                action = "added"
            self._files[file_interface] = status

        self._logger.debug(
            f"{action.title()}{' existing' if action == 'updated' else ''} file {file_interface} status to {status}"
        )
        EMIT(f"state.file.{self._name}.{action}", file=file_interface, status=status)
        self.emit_file_count()

    def emit_file_count(self) -> None:
        """Emit the current count of files in the list."""
        EMIT(f"state.file.{self._name}.file.count", count=len(self._files))

    def __setitem__(self, file_path: FilePath, status: FileStatus) -> None:
        """Set or update a file's status."""
        self.append(file_path, status)

    def __getitem__(self, file_path: FilePath) -> FileStatus:
        """Get the status of a specific file."""
        file_interface = from_file_path(file_path)
        with self._lock:
            if file_interface not in self._files:
                raise KeyError(f"File {file_interface} not found in FileList")
            return self._files[file_interface]

    def __delitem__(self, file_path: FilePath) -> None:
        """Remove a file from the list and emit signals."""
        file_interface = from_file_path(file_path)
        with self._lock:
            if file_interface not in self._files:
                raise KeyError(f"File {file_interface} not found in FileList")
            del self._files[file_interface]
        EMIT(f"state.file.{self._name}.deleted", file=file_interface)
        self.emit_file_count()

    def clear(self) -> None:
        """Clear the file list and emit a signal that the list has been cleared."""
        with self._lock:
            self._files.clear()
        EMIT(f"state.file.{self._name}.cleared")
        self.emit_file_count()

    def __contains__(self, file_path: FilePath) -> bool:
        """Return True if a file is in the list."""
        file_interface = from_file_path(file_path)
        with self._lock:
            return file_interface in self._files

    def __set__(self, instance, value):
        raise AttributeError("FileList is read-only; use __setitem__ to add files.")

    def __len__(self):
        with self._lock:
            return len(self._files)

    def __iter__(self):
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
        self._controls: Dict[str, Any] = {}
        self._logger = logging.getLogger(self.__class__.__name__)

    def add_control(self, name_id: str, value: Any = None):
        """Add a control with an initial value; emits a 'control.added' event."""
        with self._controls_lock:
            if name_id in self._controls:
                self._logger.warning(
                    f"Control '{name_id}' already exists; updating its value."
                )
                self.update_control(name_id, value)
            else:
                self._controls[name_id] = value
                EMIT(f"control.{name_id}.added", control=name_id, value=value)
        self._logger.debug(f"Control '{name_id}' added with value: {value}")

    @property
    def controls(self) -> Dict[str, Any]:
        """Return a copy of current controls state."""
        with self._controls_lock:
            return self._controls.copy()

    def maybe_store(self):
        """Placeholder for persisting state to disk or config."""
        self._logger.warning("State is not stored; implement storage logic if needed.")

    def update_control(self, name_id: str, new_value: Any = None):
        """Update a control value and emit an 'updated' event."""
        with self._controls_lock:
            self._controls[name_id] = new_value
            EMIT(f"control.{name_id}.updated", control=name_id, new_value=new_value)
        self._logger.debug(f"Control '{name_id}' updated to: {new_value}")

    def __setitem__(self, name_id: str, value: Any) -> None:
        """Dict-like assignment for controls, delegates to update_control."""
        self.update_control(name_id, value)


state = State()