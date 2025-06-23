import threading
from typing import Type, List, Dict, Any, TYPE_CHECKING

from src.table_modifier.file_interface.protocol import FileInterfaceProtocol

if TYPE_CHECKING:
    from src.table_modifier.file_interface.utils import FilePath


class FileInterfaceFactory:
    """
    Holds a registry of handlers; new formats can register themselves
    by subclassing FileInterfaceProtocol and appending to ._handlers.
    """
    _handlers: list[Type[FileInterfaceProtocol]] = []
    _handler_lock: threading.Lock = threading.Lock()

    @classmethod
    def register(cls, handler: Type[FileInterfaceProtocol]) -> None:
        cls._handlers.append(handler)

    @classmethod
    def can_handle(cls, file_path: str) -> bool:
        with cls._handler_lock:
            if not cls._handlers:
                raise RuntimeError("No file handlers registered")
            return any(handler.can_handle(file_path) for handler in cls._handlers)

    @classmethod
    def create(cls, file_path: str) -> FileInterfaceProtocol:
        with cls._handler_lock:
            if not cls._handlers:
                raise RuntimeError("No file handlers registered")
            for handler in cls._handlers:
                if handler.can_handle(file_path):
                    return handler(file_path)
        raise ValueError(f"No handler for {file_path!r}")


def load(file_path: str) -> FileInterfaceProtocol:
    """
    Load a file interface for the given file path.

    Args:
        file_path (str): The path to the file.

    Returns:
        FileInterfaceProtocol: An instance of a file interface that can handle the file.

    Raises:
        ValueError: If no handler can handle the given file path.
    """
    return FileInterfaceFactory.create(file_path)


def save(file_path: "FilePath", data: List[Dict[str, Any]]) -> None:
    """
    Save data to a file using the appropriate file interface.

    Args:
        file_path (FilePath): The path to the file or FileInterface.
        data (List[Dict[str, Any]]): The data to save.

    Raises:
        ValueError: If no handler can handle the given file path.
    """
    file_interface = load(file_path)
    file_interface.append_list(data)
    file_interface.save()
