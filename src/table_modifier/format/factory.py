import json
from os import PathLike
from pathlib import Path

from src.table_modifier.format.base import BaseFormat
from src.table_modifier.format.protocol import FormatProtocol


class FormatFactory:
    """
    Factory class to create format objects from json configuration.
    """
    def create_format(self, file_path: str | Path | PathLike) -> FormatProtocol:
        """
        Create a format object from a json file.

        Args:
            file_path (FilePath): The path to the json file containing the format configuration.

        Returns:
            FormatProtocol: An instance of a class that implements FormatProtocol.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
            return BaseFormat(config)
