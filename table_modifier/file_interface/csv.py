import os
from pathlib import Path
from typing import Optional, Iterator, Dict

import pandas as pd

from .factory import FileInterfaceFactory
from .protocol import FileInterfaceProtocol


class CSVFileInterface(FileInterfaceProtocol):
    file_type = "csv"

    def __init__(self, file_path: str):
        self.path = Path(file_path)
        self._df: Optional[pd.DataFrame] = None
        self._file = None

    @classmethod
    def can_handle(cls, file_path: str) -> bool:
        return os.path.splitext(file_path)[1].lower() == ".csv"

    def __enter__(self) -> "CSVFileInterface":
        self._file = open(self.path, mode="r", newline="")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._file:
            self._file.close()

    def load(self) -> pd.DataFrame:
        self._df = pd.read_csv(self.path)
        return self._df

    def iter_load(self, chunksize: int = 1_000) -> Iterator[pd.DataFrame]:
        return pd.read_csv(self.path, chunksize=chunksize)

    def stream_rows(self) -> Iterator[Dict[str, any]]:
        for chunk in self.iter_load(chunksize=1):
            yield chunk.iloc[0].to_dict()

    def save(self) -> None:
        self.save_as(self.path.as_posix())

    def save_as(self, file_path: str) -> None:
        if self._df is None:
            raise RuntimeError("No DataFrame loaded to save")
        self._df.to_csv(file_path, index=False)

    def get_schema(self) -> Dict[str, str]:
        if self._df is None:
            # peek at first row
            df = pd.read_csv(self.path, nrows=1)
        else:
            df = self._df
        return {col: str(dtype) for col, dtype in df.dtypes.items()}

    def load_metadata(self) -> Dict[str, any]:
        # CSV has no extra metadata beyond headers
        return {"columns": list(self.get_schema().keys())}

    def validate(self, df: pd.DataFrame) -> None:
        if any(col is None or col == "" for col in df.columns):
            raise ValueError("Empty column name detected in CSV")


FileInterfaceFactory.register(CSVFileInterface)