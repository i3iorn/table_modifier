# table_modifier/checks/date_checks.py
from datetime import datetime
from typing import List, Union
from .base import BaseCheck

class DateCheck(BaseCheck[Union[str, datetime]]):
    FORMATS = [
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S",
        "%d %b %Y", "%B %d, %Y",
    ]
    def __init__(self, *, weight: float = 1.0):
        super().__init__(func=self._score, name="date_check", weight=weight)
    def _score(self, values: List[Union[str, datetime]]) -> float:
        valid = 0
        for v in values:
            if isinstance(v, datetime):
                valid += 1
            elif isinstance(v, str):
                for fmt in self.FORMATS:
                    try:
                        datetime.strptime(v, fmt)
                        valid += 1
                        break
                    except ValueError:
                        pass
        return valid / len(values) if values else 0.0
    def is_applicable(self, values: List[Union[str, datetime]]) -> bool:
        return any(isinstance(v, (str, datetime)) for v in values)
