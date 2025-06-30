from typing import List, Dict, Any

from src.table_modifier.format.protocol import FormatProtocol


class BaseFormat(FormatProtocol):
    """
    Base class for all format implementations.

    This class provides a template for creating specific format classes.
    It implements the basic structure of a format, including components,
    header, footer, and file interface methods.
    """
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the BaseFormat with a configuration dictionary.

        Args:
            config (Dict[str, Any]): Configuration dictionary for the format.
        """
        self.config = config
        for key, value in config.items():
            setattr(self, key, value)
