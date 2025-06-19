from typing import Optional, List

from table_modifier.classifier import BaseCheck, MatchCountCheckMixin


class LengthVarianceCheck(BaseCheck[str], MatchCountCheckMixin[str]):
    def __init__(
            self,
            min_variance: float = 0.0,
            *,
            max_variance: Optional[float] = None,
            weight: float = 1.0,
            name: Optional[str] = None,
    ):
        self._min_variance = min_variance
        self._max_variance = max_variance
        super().__init__(func=self._score, name=name or "length_variance_check", weight=weight)

    def _score(self, values: List[str]) -> float:
        if not values:
            return 0.0

        lengths = [len(v) for v in values if isinstance(v, str)]
        if not lengths:
            return 0.0

        mean_length = sum(lengths) / len(lengths)
        variance = sum((l - mean_length) ** 2 for l in lengths) / len(lengths)

        if self._max_variance is not None and variance > self._max_variance:
            return 0.0

        return 1.0 if variance >= self._min_variance else 0.25


class UniquenessCheck(BaseCheck[str], MatchCountCheckMixin[str]):
    def __init__(
        self,
        min_uniqueness: float = 0.0,
        *,
        max_uniqueness: Optional[float] = None,
        weight: float = 1.0,
        name: Optional[str] = None,
    ):
        self._min_uniqueness = min_uniqueness
        self._max_uniqueness = max_uniqueness
        super().__init__(func=self._score, name=name or "uniqueness_check", weight=weight)

    def _score(self, values: List[str]) -> float:
        if not values:
            return 0.0

        unique_count = len(set(values))
        total_count = len(values)

        if total_count == 0:
            return 0.0

        uniqueness_ratio = unique_count / total_count

        if self._max_uniqueness is not None and uniqueness_ratio > self._max_uniqueness:
            return 0.0

        return 1.0 if uniqueness_ratio >= self._min_uniqueness else 0.25


