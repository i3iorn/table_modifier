# table_modifier/checks/mixins.py
from typing import List, TypeVar, Callable, Generic

import pandas as pd

T = TypeVar("T")

class MatchCountCheckMixin(Generic[T]):
    def by_predicate(self, values: List[T], pred: Callable[[T], bool]) -> float:
        if not values:
            return 0.0
        matches = sum(1 for v in values if pred(v))
        return matches / len(values)


class PandasMatchMixin:
    def by_predicate_series(
        self, series: pd.Series, pred: Callable[[pd.Series], pd.Series]
    ) -> float:
        if series.empty:
            return 0.0
        mask = pred(series)
        return mask.sum() / len(series)
