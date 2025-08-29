import types
import pytest

from src.table_modifier.file_interface.factory import FileInterfaceFactory
from src.table_modifier.file_interface.utils import from_file_path


def test_factory_errors_when_no_handlers(monkeypatch):
    # Backup and clear handlers
    orig = FileInterfaceFactory._handlers.copy()
    try:
        FileInterfaceFactory._handlers = []  # type: ignore[attr-defined]
        with pytest.raises(RuntimeError):
            FileInterfaceFactory.can_handle("x.csv")
        with pytest.raises(RuntimeError):
            FileInterfaceFactory.create("x.csv")
    finally:
        FileInterfaceFactory._handlers = orig  # type: ignore[attr-defined]


def test_factory_create_raises_when_no_matching_handler(monkeypatch):
    # Ensure some handlers exist but none match '.zzz'
    assert FileInterfaceFactory._handlers  # type: ignore[attr-defined]
    with pytest.raises(ValueError):
        FileInterfaceFactory.create("no_match.zzz")


def test_from_file_path_invalid_type_raises():
    class Bad:
        pass
    with pytest.raises(TypeError):
        from_file_path(Bad())

