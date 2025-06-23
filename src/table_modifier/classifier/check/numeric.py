# table_modifier/checks/numeric_checks.py
from typing import List, Union
from .base import BaseCheck
from .mixin import MatchCountCheckMixin

Number = Union[int, float]

class NumericCheck(BaseCheck[Number], MatchCountCheckMixin[Number]):
    def __init__(self, *, weight: float = 0.5):
        super().__init__(func=self._score, name="numeric_check", weight=weight)
    def _score(self, values: List[Number]) -> float:
        return self.by_predicate(values, lambda v: isinstance(v, (int, float)))
    def is_applicable(self, values: List[Number]) -> bool:
        return self.by_predicate(values, lambda v: isinstance(v, (int, float))) > 0


class VarianceCheck(BaseCheck[Number]):
    def __init__(
        self,
        min_variance: float = 0.0,
        *,
        max_variance: float = float("inf"),
        weight: float = 1.0,
        name: str = "variance_check",
    ):
        self._min, self._max = min_variance, max_variance
        super().__init__(func=self._score, name=name, weight=weight)

    def _score(self, values: List[Number]) -> float:
        nums = [v for v in values if isinstance(v, (int, float))]
        if not nums:
            return 0.0
        mean = sum(nums) / len(nums)
        var = sum((x - mean) ** 2 for x in nums) / len(nums)
        return 1.0 if self._min <= var <= self._max else 0.0
