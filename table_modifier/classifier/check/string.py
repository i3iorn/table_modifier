# table_modifier/checks/string_checks.py
import re
from typing import List, Optional
from .base import BaseCheck
from .mixin import MatchCountCheckMixin

class StringCheck(BaseCheck[str], MatchCountCheckMixin[str]):
    def __init__(self, *, weight: float = 0.5):
        super().__init__(func=self._score, name="string_check", weight=weight)
    def _score(self, values: List[str]) -> float:
        all_str = all(isinstance(v, str) for v in values if v is not None)
        any_str = any(isinstance(v, str) for v in values if v is not None)
        return 1.0 if all_str else (0.25 if any_str else 0.0)
    def is_applicable(self, values: List[str]) -> bool:
        return any(isinstance(v, str) for v in values if v is not None)


class PatternCheck(BaseCheck[str], MatchCountCheckMixin[str]):
    def __init__(self, pattern: str, *, weight: float = 1.0, name: Optional[str] = None):
        self._regex = re.compile(pattern)
        super().__init__(func=self._score, name=name or "pattern_check", weight=weight)
    def _score(self, values: List[str]) -> float:
        return self.by_predicate(values, lambda v: isinstance(v, str) and bool(self._regex.search(v)))


class LengthCheck(BaseCheck[str], MatchCountCheckMixin[str]):
    def __init__(
        self,
        min_len: int = 0,
        max_len: Optional[int] = None,
        *,
        weight: float = 1.0,
        name: Optional[str] = None,
    ):
        self._min, self._max = min_len, max_len
        super().__init__(func=self._score, name=name or "length_check", weight=weight)
    def _score(self, values: List[str]) -> float:
        return self.by_predicate(
            values,
            lambda v: isinstance(v, str)
                      and len(v) >= self._min
                      and (self._max is None or len(v) <= self._max),
        )

