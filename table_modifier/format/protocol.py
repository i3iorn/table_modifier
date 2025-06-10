from typing import Protocol, Any

from table_modifier.file_interface.protocol import FileInterfaceProtocol


class FormatConverterProtocol(Protocol):
    """
    Protocol for defining a format converter that can convert data from one format
    to another. The converter should handle the conversion logic and any necessary
    metadata adjustments.
    """

    @property
    def source(self) -> FileInterfaceProtocol:
        """The format of the source data to be converted."""
        ...

    @property
    def target_format(self) -> FileInterfaceProtocol:
        """The format to which the data should be converted."""
        ...

    def convert(self, **kwargs: Any) -> str:
        """
        Convert data from the source to the target format.

        Args:
            **kwargs: Additional parameters that may be required for conversion.

        Returns:
            str: file path of the converted data.
        """
        ...
        for key, value in kwargs.items():
            if not isinstance(value, str):
                raise TypeError(f"Expected str for {key}, got {type(value).__name__}")

        for row in self.source.stream_rows():
            if not isinstance(row, dict):
                raise TypeError(f"Expected dict for row, got {type(row).__name__}")

            self.target_format.append_list([row])
