import csv
import logging
import os
from pathlib import Path
from typing import Optional, Iterator, Dict, List, Any

import pandas as pd
from pandas import DataFrame, read_csv

from .base import BaseInterface
from .factory import FileInterfaceFactory
from .utils import FilePath

logger = logging.getLogger(__name__)


class CSVFileInterface(BaseInterface):
    file_type = "csv"

    def __init__(self, file_path: FilePath, **kwargs):
        self._cached_headers: Optional[List[str]] = None
        self.path = Path(file_path)
        self._df: Optional[DataFrame] = None
        self._file = None
        self._delimiter = kwargs.get("delimiter", ",")
        self._skip_rows: int = 0
        self._skip_rows_list: Optional[List[int]] = None

    def get_headers(self, sheet_name: str = None) -> List[str] | None:
        """
        Returns the header row of the CSV file if it exists.
        If no header is present, returns None.
        """
        if self._cached_headers is None:
            try:
                with open(self.path, newline="", encoding="utf-8") as f:
                    sample = f.read(2048)
                    f.seek(0)
                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters=self._delimiter)
                    except csv.Error:
                        dialect = csv.get_dialect("excel")
                        dialect.delimiter = self._delimiter
                    reader = csv.reader(f, dialect)
                    headers = next(reader, None)
                    self._cached_headers = headers
            except FileNotFoundError:
                logger.error("CSV file not found: %s", self.path)
                self._cached_headers = None
        return self._cached_headers

    @classmethod
    def can_handle(cls, file_path: str) -> bool:
        return os.path.splitext(str(file_path))[1].lower() == ".csv"

    def __enter__(self) -> "CSVFileInterface":
        self._file = open(self.path, mode="r", newline="", encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if self._file:
            self._file.close()
            self._file = None
        return False  # Do not suppress exceptions

    def _pandas_skiprows(self):
        # Prefer explicit list of rows if provided
        if self._skip_rows_list is not None:
            return self._skip_rows_list
        return self._skip_rows

    def load(self) -> DataFrame:
        logger.debug("Loading CSV from %s", self.path)
        try:
            df = read_csv(self.path, skiprows=self._pandas_skiprows())
        except Exception as e:
            logger.error("Failed to load CSV: %s", e)
            raise
        self._df = df
        return df

    def iter_load(self, chunksize: int = 1_000) -> Iterator[DataFrame]:
        return read_csv(self.path, skiprows=self._pandas_skiprows(), chunksize=chunksize)

    def iter_columns(
        self, value_count: Optional[int] = None, chunksize: int = 1_000
    ) -> Iterator[DataFrame]:
        """
        Iterate over columns in the CSV file, yielding DataFrames with one column at a time.
        If value_count is specified, only yield that many values per column.
        """
        for chunk in read_csv(self.path, skiprows=self._pandas_skiprows(), chunksize=chunksize):
            for col in chunk.columns:
                col_series = chunk[col]
                if value_count:
                    col_series = col_series.head(value_count)
                yield col_series.to_frame()

    def stream_rows(self) -> Iterator[Dict[str, Any]]:
        for chunk in self.iter_load(chunksize=1):
            # chunksize=1 ensures one row per chunk
            yield chunk.iloc[0].to_dict()

    def append_df(self, df: DataFrame) -> None:
        if self._df is None:
            # Initialize with provided df
            self._df = df.copy()
        else:
            self._df = pd.concat([self._df, df], ignore_index=True)

    def append_list(self, data: List[Dict[str, Any]]) -> None:
        # Convert list of dicts to DataFrame and append
        import pandas as pd

        new_df = pd.DataFrame(data)
        self.append_df(new_df)

    def set_header_rows_to_skip(self, header_rows: int) -> None:
        self._skip_rows = max(0, int(header_rows))
        self._skip_rows_list = None

    def set_rows_to_skip(self, rows: List[int]) -> None:
        self._skip_rows_list = sorted(set(int(r) for r in rows if int(r) >= 0))

    @property
    def encoding(self) -> str:
        # We default to utf-8 for reading/writing unless overridden
        return "utf-8"

    def save(self) -> None:
        """
        Save the current DataFrame to the original file path.
        """
        self.save_as(self.path.as_posix())

    def save_as(self, file_path: str) -> None:
        if self._df is None:
            raise RuntimeError("No DataFrame loaded to save")
        self._df.to_csv(file_path, index=False)

    def get_schema(self) -> Dict[str, str]:
        if self._df is None:
            # Peek at first row
            df = read_csv(self.path, skiprows=self._pandas_skiprows(), nrows=1)
        else:
            df = self._df
        return {str(col): str(dtype) for col, dtype in df.dtypes.items()}

    def load_metadata(self) -> Dict[str, Any]:
        # CSV has no extra metadata beyond headers
        return {"columns": list(self.get_schema().keys())}

    def validate(self, df: DataFrame) -> None:
        if any(col is None or col == "" for col in df.columns):
            raise ValueError("Empty column name detected in CSV")


FileInterfaceFactory.register(CSVFileInterface)