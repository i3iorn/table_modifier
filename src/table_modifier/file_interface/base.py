from src.table_modifier.file_interface.protocol import FileInterfaceProtocol


class BaseInterface(FileInterfaceProtocol):
    def __hash__(self) -> int:
        """Support hashing by using the file path."""
        return hash(self.path)