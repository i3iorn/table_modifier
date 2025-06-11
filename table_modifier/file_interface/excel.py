import os
from typing import Iterator, Dict, Any, Optional
import pandas as pd

from .utils import FilePath
from .factory import FileInterfaceFactory
from .protocol import FileInterfaceProtocol


class ExcelFileInterface(FileInterfaceProtocol):
    file_type = "excel"

    def __init__(self, file_path: Optional[FilePath] = None, sheet_name: Optional[str] = None):
        """
        :param file_path: path to the .xls/.xlsx file
        :param sheet_name: name or index of sheet to operate on; defaults to first sheet
        """
        self.path = file_path
        self.sheet_name = sheet_name
        self._df: Optional[pd.DataFrame] = None

    def get_headers(self, sheet_name: str = None) -> Optional[list[str]]:
        """
        Returns the header row of the specified sheet if it exists.
        If no header is present, returns None.
        """
        self._ensure_sheet()
        if sheet_name is None:
            sheet_name = self.sheet_name or pd.ExcelFile(self.path).sheet_names[0]
        skip_rows = self._skip_rows if hasattr(self, '_skip_rows') else 0
        df = pd.read_excel(self.path, sheet_name=sheet_name, nrows=0, skiprows=skip_rows)
        return list(df.columns)

    @classmethod
    def can_handle(cls, file_path: str) -> bool:
        ext = os.path.splitext(file_path)[1].lower()
        return ext in (".xls", ".xlsx")

    def _ensure_sheet(self) -> None:
        # Lazily load ExcelFile to pick a default sheet
        if self.sheet_name is None:
            xls = pd.ExcelFile(self.path)
            self.sheet_name = xls.sheet_names[0]

    def append_df(self, df: pd.DataFrame) -> None:
        if self._df is None:
            self.load()
        if self.sheet_name not in self._df.columns:
            raise ValueError(f"Sheet '{self.sheet_name}' does not exist in the loaded DataFrame")
        # Append to existing DataFrame
        self._df = pd.concat([self._df, df], ignore_index=True)

    def append_list(self, data: list[Dict[str, Any]]) -> None:
        if self._df is None:
            self.load()
        if self.sheet_name not in self._df.columns:
            raise ValueError(f"Sheet '{self.sheet_name}' does not exist in the loaded DataFrame")
        # Convert list of dicts to DataFrame and append
        new_df = pd.DataFrame(data)
        self._df = pd.concat([self._df, new_df], ignore_index=True)

    def encoding(self) -> str:
        # Excel files don't have a text encoding like CSV
        return "utf-8"

    def load(self) -> pd.DataFrame:
        # Eager read entire sheet
        self._ensure_sheet()
        self._df = pd.read_excel(self.path, sheet_name=self.sheet_name)
        return self._df

    def iter_load(self, chunksize: int = 1_000) -> Iterator[pd.DataFrame]:
        # Ensure we have a DataFrame
        df = self._df if self._df is not None else self.load()
        for start in range(0, len(df), chunksize):
            yield df.iloc[start : start + chunksize]

    def stream_rows(self) -> Iterator[Dict[str, Any]]:
        for chunk in self.iter_load(chunksize=1):
            yield chunk.iloc[0].to_dict()

    def save(self) -> None:
        self.save_as(self.path.as_posix())

    def save_as(self, file_path: str) -> None:
        if self._df is None:
            raise RuntimeError("No DataFrame loaded to save")
        # Use ExcelWriter to preserve sheet_name
        if self.path is None:
            raise ValueError("File path must be set before saving")
        else:
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                # sheet_name is guaranteed by _ensure_sheet/load
                self._df.to_excel(writer, sheet_name=self.sheet_name, index=False)

    def get_schema(self) -> Dict[str, str]:
        # Peek at first row if not already loaded
        if self._df is None:
            self._ensure_sheet()
            skip_rows = self._skip_rows if hasattr(self, '_skip_rows') else 0
            df = pd.read_excel(self.path, sheet_name=self.sheet_name, skiprows=skip_rows, nrows=1)
        else:
            df = self._df
        return {str(col): str(dtype) for col, dtype in df.dtypes.items()}

    def load_metadata(self) -> Dict[str, Any]:
        # Must inspect sheet names & engine
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
        self._ensure_sheet()
        xls = pd.ExcelFile(self.path)
        return xls.sheet_names


FileInterfaceFactory.register(ExcelFileInterface)