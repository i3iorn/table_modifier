import os
from pathlib import Path
from typing import Iterator, Dict, Any, Optional, List
import pandas as pd

from .base import BaseInterface
from .utils import FilePath
from .factory import FileInterfaceFactory


class ExcelFileInterface(BaseInterface):
    file_type = "excel"

    def __init__(self, file_path: FilePath, sheet_name: Optional[str] = None):
        """
        :param file_path: path to the .xls/.xlsx file
        :param sheet_name: name or index of sheet to operate on; defaults to first sheet
        """
        self.path = Path(file_path)
        self.sheet_name: Optional[str] = sheet_name
        self._df: Optional[pd.DataFrame] = None
        self._skip_rows: int = 0
        self._skip_rows_list: Optional[List[int]] = None

    def get_headers(self, sheet_name: str = None) -> Optional[list[str]]:
        """
        Returns the header row of the specified sheet if it exists.
        If no header is present, returns None.
        """
        self._ensure_sheet()
        sheet: int | str = sheet_name or self.sheet_name or 0
        df = pd.read_excel(self.path, sheet_name=sheet, nrows=0, skiprows=self._skip_for_pandas())
        return list(df.columns)

    @classmethod
    def can_handle(cls, file_path: str) -> bool:
        ext = os.path.splitext(str(file_path))[1].lower()
        return ext in (".xls", ".xlsx")

    def _ensure_sheet(self) -> None:
        # Lazily load ExcelFile to pick a default sheet
        if self.sheet_name is None:
            xls = pd.ExcelFile(self.path)
            self.sheet_name = xls.sheet_names[0]

    def _skip_for_pandas(self):
        return self._skip_rows_list if self._skip_rows_list is not None else self._skip_rows

    def append_df(self, df: pd.DataFrame) -> None:
        # Ensure loaded DataFrame for the active sheet
        base = self._df if self._df is not None else self.load()
        self._df = pd.concat([base, df], ignore_index=True)

    def append_list(self, data: List[Dict[str, Any]]) -> None:
        new_df = pd.DataFrame(data)
        self.append_df(new_df)

    @property
    def encoding(self) -> str:
        # Excel files don't have a text encoding like CSV
        return "utf-8"

    def load(self) -> pd.DataFrame:
        # Eager read entire sheet
        self._ensure_sheet()
        sheet: int | str = self.sheet_name or 0
        df = pd.read_excel(self.path, sheet_name=sheet, skiprows=self._skip_for_pandas())
        self._df = df
        return self._df

    def iter_load(self, chunksize: int = 1_000) -> Iterator[pd.DataFrame]:
        # Ensure we have a DataFrame
        df = self._df if self._df is not None else self.load()
        for start in range(0, len(df), chunksize):
            yield df.iloc[start : start + chunksize]

    def iter_columns(self, value_count: Optional[int] = None, chunksize: int = 1_000) -> Iterator[pd.DataFrame]:
        """
        Iterate over columns in chunks.
        If value_count is specified, yield only that many values per column.
        """
        df = self._df if self._df is not None else self.load()
        for col in df.columns:
            col_data = df[col]
            if value_count is not None:
                col_data = col_data.head(value_count)
            for start in range(0, len(col_data), chunksize):
                yield pd.DataFrame({col: col_data.iloc[start : start + chunksize]})

    def stream_rows(self) -> Iterator[Dict[str, Any]]:
        for chunk in self.iter_load(chunksize=1):
            yield chunk.iloc[0].to_dict()

    def save(self) -> None:
        self.save_as(self.path.as_posix())

    def save_as(self, file_path: str) -> None:
        if self._df is None:
            raise RuntimeError("No DataFrame loaded to save")
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            # sheet_name is guaranteed by _ensure_sheet/load
            self._df.to_excel(writer, sheet_name=self.sheet_name or "Sheet1", index=False)

    def get_schema(self) -> Dict[str, str]:
        # Peek at first row if not already loaded
        if self._df is None:
            sheet: int | str = self.sheet_name or 0
            df = pd.read_excel(self.path, sheet_name=sheet, skiprows=self._skip_for_pandas(), nrows=1)
        else:
            df = self._df
        return {str(col): str(dtype) for col, dtype in df.dtypes.items()}

    def load_metadata(self) -> Dict[str, Any]:
        xls = pd.ExcelFile(self.path)
        return {
            "sheet_names": xls.sheet_names,
            "engine": xls.engine,
        }

    def validate(self, df: pd.DataFrame) -> None:
        # Example rule: no duplicate columns
        cols = list(df.columns)
        dupes = {c for c in cols if cols.count(c) > 1}
        if dupes:
            raise ValueError(f"Duplicate column names in sheet: {dupes}")

    def get_sheets(self) -> list[str]:
        """
        Return a list of sheet names in the Excel file.
        """
        xls = pd.ExcelFile(self.path)
        return xls.sheet_names

    def set_header_rows_to_skip(self, header_rows: int) -> None:
        self._skip_rows = max(0, int(header_rows))
        self._skip_rows_list = None

    def set_rows_to_skip(self, rows: List[int]) -> None:
        self._skip_rows_list = sorted(set(int(r) for r in rows if int(r) >= 0))


FileInterfaceFactory.register(ExcelFileInterface)