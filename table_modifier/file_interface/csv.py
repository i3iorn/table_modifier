import csv
import os
from pathlib import Path
from typing import Optional, Iterator, Dict, List

from pandas import DataFrame, read_csv

from .factory import FileInterfaceFactory
from .protocol import FileInterfaceProtocol


class CSVFileInterface(FileInterfaceProtocol):
    file_type = "csv"

    def __init__(self, file_path: str, **kwargs):
        self.path = Path(file_path)
        self._df: Optional[DataFrame] = None
        self._file = None
        self._delimiter = kwargs.get("delimiter", ",")

    def get_headers(self, sheet_name: str = None) -> List[str] | None:
        """
        Returns the header row of the CSV file if it exists.
        If no header is present, returns None.
        """
        with open(self.path, newline="") as f:
            sample = f.read(2048)
            f.seek(0)
            dialect = csv.Sniffer().sniff(sample, delimiters=self._delimiter)
            reader = csv.reader(f, dialect)
            headers = next(reader, None)
            return headers if headers and any(headers) else None

    @classmethod
    def can_handle(cls, file_path: str) -> bool:
        return os.path.splitext(file_path)[1].lower() == ".csv"

    def __enter__(self) -> "CSVFileInterface":
        self._file = open(self.path, mode="r", newline="")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._file:
            self._file.close()

    def load(self) -> DataFrame:
        self._df = read_csv(self.path)
        return self._df

    def iter_load(self, chunksize: int = 1_000) -> Iterator[DataFrame]:
        return read_csv(self.path, chunksize=chunksize)

    def iter_columns(self, value_count: Optional[int] = None, chunksize: int = 1_000) -> Iterator[DataFrame]:
        """
        Iterate over columns in the CSV file, yielding DataFrames with one column at a time.
        If value_count is specified, only yield that many values per column.
        """
        for chunk in read_csv(self.path, chunksize=chunksize):
            for col in chunk.columns:
                col_series = chunk[col]
                yield col_series.head(value_count) if value_count else col_series

    def stream_rows(self) -> Iterator[Dict[str, any]]:
        for chunk in self.iter_load(chunksize=1):
            yield chunk.iloc[0].to_dict()

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
            # peek at first row
            skip_rows = self._skip_rows if hasattr(self, '_skip_rows') else 0
            df = read_csv(self.path, skiprows=skip_rows, nrows=1)
        else:
            df = self._df
        return {str(col): str(dtype) for col, dtype in df.dtypes.items()}

    def load_metadata(self) -> Dict[str, any]:
        # CSV has no extra metadata beyond headers
        return {"columns": list(self.get_schema().keys())}

    def validate(self, df: DataFrame) -> None:
        if any(col is None or col == "" for col in df.columns):
            raise ValueError("Empty column name detected in CSV")


FileInterfaceFactory.register(CSVFileInterface)