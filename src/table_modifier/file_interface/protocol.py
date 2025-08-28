from pathlib import Path
from typing import (
    Protocol,
    ClassVar,
    Iterator,
    Dict,
    Optional,
    runtime_checkable,
    Any,
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
    def name(self) -> str:  # pragma: no cover - protocol signature only
        """Basename of the backing file path."""
        ...

    def get_headers(self, sheet_name: Optional[str] = None) -> Optional[list[str]]:
        """
        Return the header row of the file if it exists.
        If no header is present, return None.

        For Excel files, sheet_name can be specified to get headers from a specific sheet.
        """
        ...

    @classmethod
    def can_handle(cls, file_path: str) -> bool:
        """Return True if this handler supports the given file_path (usually via extension)."""
        ...

    def __enter__(self) -> "FileInterfaceProtocol":  # pragma: no cover - protocol signature only
        """Optional: open any heavy resources (e.g. file handles)."""
        ...

    def __exit__(self, exc_type, exc, tb) -> bool:  # pragma: no cover - protocol signature only
        """Optional: clean up resources on context exit."""
        ...

    def append_df(self, df: pd.DataFrame) -> None:
        """
        Append a DataFrame to the existing data.
        Raises ValueError if the file format does not support appending.
        """
        ...

    def append_list(self, data: list[Dict[str, Any]]) -> None:
        """
        Append a list of dicts to the existing data.
        Raises ValueError if the file format does not support appending.
        """
        ...

    @property
    def encoding(self) -> str:
        """Return the encoding used for the file, if applicable (e.g., 'utf-8')."""
        ...

    def load(self) -> pd.DataFrame:
        """Eagerly read the entire dataset into memory."""
        ...

    def iter_load(self, chunksize: int = 1_000) -> Iterator[pd.DataFrame]:
        """
        Lazily read the file in “chunksize”-row DataFrames.
        Default chunksize=1000; adjust based on memory/throughput tradeoffs.
        """
        ...

    def iter_columns(
        self, value_count: Optional[int] = None, chunksize: int = 1_000
    ) -> Iterator[pd.DataFrame]:
        """
        Lazily read the file in “chunksize”-column DataFrames.
        Useful for column‑wise processing.
        Default chunksize=1000; adjust based on memory/throughput tradeoffs.
        """
        ...

    def stream_rows(self) -> Iterator[Dict[str, Any]]:
        """
        Stream single rows as a dict mapping column→value.
        Useful for record‑by‑record processing.
        """
        ...

    def set_header_rows_to_skip(self, header_rows: int) -> None:
        """
        Set the number of header rows to skip when loading data.
        This is useful for formats like CSV where the header may not be on the first row.
        """
        ...

    def save(self) -> None:
        """Write current DataFrame back to self.file_path."""
        ...

    def save_as(self, file_path: str) -> None:
        """Write current DataFrame to a new path."""
        ...

    def get_schema(self) -> Dict[str, str]:
        """Return column‑to‑dtype mapping without loading all data, if possible."""
        ...

    def load_metadata(self) -> Dict[str, Any]:
        """
        Read any file‑level metadata (e.g. Excel sheet names, Parquet metadata).
        Should not load the entire dataset.
        """
        ...

    def validate(self, df: pd.DataFrame) -> None:
        """Enforce schema/content invariants; raise on failure."""
        ...

    def __reduce__(self):  # pragma: no cover - protocol signature only
        """Support pickling by returning the class and file_path."""
        ...

    def __hash__(self):  # pragma: no cover - protocol signature only
        """Hash based on the file path to allow use in sets or as dictionary keys."""
        ...

    def __eq__(self, other):  # pragma: no cover - protocol signature only
        """Equality based on file path."""
        ...
