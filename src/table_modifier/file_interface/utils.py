from pathlib import Path

from src.table_modifier.file_interface.factory import FileInterfaceFactory
from src.table_modifier.file_interface.protocol import FileInterfaceProtocol

FilePath = str | Path | FileInterfaceProtocol | object


def _looks_like_interface(obj: object) -> bool:
    return hasattr(obj, "path") and hasattr(obj, "append_list") and hasattr(obj, "save")


def from_file_path(file_path: FilePath) -> FileInterfaceProtocol:
    """
    Convert a file path to a FileInterfaceProtocol instance.

    Args:
        file_path (FilePath): The file path to convert.

    Returns:
        FileInterfaceProtocol: The file interface instance.
    """
    if isinstance(file_path, FileInterfaceProtocol) or _looks_like_interface(file_path):  # type: ignore[arg-type]
        return file_path  # type: ignore[return-value]
    elif isinstance(file_path, str) or isinstance(file_path, Path):
        return FileInterfaceFactory.create(file_path)
    else:
        raise TypeError(
            f"Expected str, Path, or FileInterfaceProtocol, got {type(file_path).__name__}")
