from src.table_modifier.file_interface.protocol import FileInterfaceProtocol


class BaseInterface(FileInterfaceProtocol):
    def __hash__(self) -> int:
        """Support hashing by using the file path."""
        return hash(self.path)

    def __eq__(self, other) -> bool:  # pragma: no cover - exercised via higher-level tests
        try:
            return getattr(self, "path", None) == getattr(other, "path", None)
        except Exception:
            return False
