import os
from typing import Optional, Iterator, Dict

import pandas as pd

from .factory import FileInterfaceFactory
from .protocol import FileInterfaceProtocol


class ParquetFileInterface(FileInterfaceProtocol):
    file_type = "parquet"

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._df: Optional[pd.DataFrame] = None

    @classmethod
    def can_handle(cls, file_path: str) -> bool:
        return os.path.splitext(file_path)[1].lower() in (".parquet", ".pq")

    def load(self) -> pd.DataFrame:
        self._df = pd.read_parquet(self.file_path)
        return self._df

    def iter_load(self, chunksize: int = 1_000) -> Iterator[pd.DataFrame]:
        # no native chunks; load then yield slices
        df = self.load()
        for i in range(0, len(df), chunksize):
            yield df.iloc[i : i + chunksize]

    def stream_rows(self) -> Iterator[Dict[str, any]]:
        for chunk in self.iter_load(chunksize=1):
            yield chunk.iloc[0].to_dict()

    def save(self) -> None:
        self.save_as(self.file_path)

    def save_as(self, file_path: str) -> None:
        if self._df is None:
            raise RuntimeError("No DataFrame loaded to save")
        self._df.to_parquet(file_path)

    def get_schema(self) -> Dict[str, str]:
        # pandas can read metadata-only for schema
        mq = pd.read_parquet(self.file_path, engine="pyarrow", columns=[])
        return {meta.name: str(meta.type) for meta in mq.schema}

    def load_metadata(self) -> Dict[str, any]:
        import pyarrow.parquet as pq
        meta = pq.ParquetFile(self.file_path).metadata
        return {
            "num_row_groups": meta.num_row_groups,
            "num_rows": meta.num_rows,
            "created_by": meta.created_by,
        }

    def validate(self, df: pd.DataFrame) -> None:
        if any(col.lower() != col for col in df.columns):
            raise ValueError("Parquet column names must be lowercase")


FileInterfaceFactory.register(ParquetFileInterface)
