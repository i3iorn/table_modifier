from pathlib import Path
from typing import (
    Protocol, ClassVar, Iterator, Dict, Optional, runtime_checkable
)
import pandas as pd


@runtime_checkable
class FileInterfaceProtocol(Protocol):
    """
    Protocol for any tabular file handler (CSV, Excel, Parquet, …),
    with lazy/streaming support and metadata inspection.
    """

    # Path or file-like identifier
    path: Path

    # Short format name (e.g. "csv", "parquet", "xlsx")
    file_type: ClassVar[str]

    @property
    def name(self):
        return self.path.name

    def get_headers(self, sheet_name: str = None) -> Optional[list[str]]:
        """
        Return the header row of the file if it exists.
        If no header is present, return None.

        For Excel files, sheet_name can be specified to get headers from a specific sheet.
        """
        ...

    @classmethod
    def can_handle(cls, file_path: str) -> bool:
        """Return True if this handler supports the given file_path (usually via extension)."""

    def __enter__(self) -> "FileInterfaceProtocol":
        """Optional: open any heavy resources (e.g. file handles)."""
        ...

    def __exit__(self, exc_type, exc, tb) -> bool:
        """Optional: clean up resources on context exit."""
        ...

    def append_df(self, df: pd.DataFrame) -> None:
        """
        Append a DataFrame to the existing data.
        Raises ValueError if the file format does not support appending.
        """

    def append_list(self, data: list[Dict[str, any]]) -> None:
        """
        Append a list of dicts to the existing data.
        Raises ValueError if the file format does not support appending.
        """

    @property
    def encoding(self) -> str:
        """Return the encoding used for the file, if applicable (e.g., 'utf-8')."""

    def load(self) -> pd.DataFrame:
        """Eagerly read the entire dataset into memory."""

    def iter_load(self, chunksize: int = 1_000) -> Iterator[pd.DataFrame]:
        """
        Lazily read the file in “chunksize”‐row DataFrames.
        Default chunksize=1000; adjust based on memory/throughput tradeoffs.
        """

    def iter_columns(self, value_count: Optional[int] = None, chunksize: int = 1_000) -> Iterator[pd.DataFrame]:
        """
        Lazily read the file in “chunksize”‐column DataFrames.
        Useful for column‐wise processing.
        Default chunksize=1000; adjust based on memory/throughput tradeoffs.
        """

    def stream_rows(self) -> Iterator[Dict[str, any]]:
        """
        Stream single rows as a dict mapping column→value.
        Useful for record‐by‐record processing.
        """

    def set_header_rows_to_skip(self, header_rows: int) -> None:
        """
        Set the number of header rows to skip when loading data.
        This is useful for formats like CSV where the header may not be on the first row.
        """
        self._skip_rows = header_rows

    def save(self) -> None:
        """Write current DataFrame back to self.file_path."""

    def save_as(self, file_path: str) -> None:
        """Write current DataFrame to a new path."""

    def get_schema(self) -> Dict[str, str]:
        """Return column‐to‐dtype mapping without loading all data, if possible."""

    def load_metadata(self) -> Dict[str, any]:
        """
        Read any file‐level metadata (e.g. Excel sheet names, Parquet metadata).
        Should not load the entire dataset.
        """

    def validate(self, df: pd.DataFrame) -> None:
        """Enforce schema/content invariants; raise on failure."""

    def __reduce__(self):
        """
        Support pickling by returning the class and file_path.
        This allows re-instantiation without needing to pass the file handle.
        """
        return self.__class__, (self.path,)

    def __hash__(self):
        """
        Hash based on the file path to allow use in sets or as dictionary keys.
        """
        return hash(self.path)

    def __eq__(self, other):
        """
        Equality based on file path.
        This allows comparing different instances of the same file interface.
        """
        if not isinstance(other, FileInterfaceProtocol):
            return NotImplemented
        return self.path == other.path
