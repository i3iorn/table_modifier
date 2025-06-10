import threading
from typing import Type

from table_modifier.file_interface.protocol import FileInterfaceProtocol


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
