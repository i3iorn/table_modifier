import threading
from typing import Type, List, Dict, Any

from src.table_modifier.file_interface.protocol import FileInterfaceProtocol


class FileInterfaceFactory:
    """
    Holds a registry of handlers; new formats can register themselves
    by subclassing FileInterfaceProtocol and appending to ._handlers.
    """

    _handlers: list[Type[FileInterfaceProtocol]] = []
    _handler_lock: threading.Lock = threading.Lock()

    @classmethod
    def register(cls, handler: type) -> None:
        cls._handlers.append(handler)  # type: ignore[list-item]

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


def _looks_like_interface(obj: object) -> bool:
    return hasattr(obj, "path") and hasattr(obj, "append_list") and hasattr(obj, "save")


def load(file_path: "FilePath") -> FileInterfaceProtocol:
    """
    Load or return a file interface for the given file path or interface.
    """
    if isinstance(file_path, FileInterfaceProtocol) or _looks_like_interface(file_path):  # type: ignore[arg-type]
        return file_path  # type: ignore[return-value]
    return FileInterfaceFactory.create(str(file_path))


def save(file_path: "FilePath", data: List[Dict[str, Any]]) -> None:
    """
    Save data (list of dicts) to a file using the appropriate file interface.

    - If file_path is an interface, it will be used directly.
    - Otherwise, a handler will be selected based on the path extension.
    """
    file_interface = load(file_path)
    file_interface.append_list(data)
    file_interface.save()
