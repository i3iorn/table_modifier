# table_modifier/checks/base.py
from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar, Callable, Optional

T = TypeVar("T")

class AbstractCheck(ABC, Generic[T]):
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def is_applicable(self, values: List[T]) -> bool: ...
    @abstractmethod
    def run(self, values: List[T]) -> float: ...
    @abstractmethod
    def weight(self) -> float: ...


class BaseCheck(AbstractCheck[T]):
    def __init__(
        self,
        *,
        func: Callable[[List[T]], float],
        name: str,
        weight: float = 0.5,
        description: Optional[str] = None,
    ):
        self._func = func
        self._name = name
        self._weight = weight
        self._description = description or ""
    def name(self) -> str:
        return self._name
    def weight(self) -> float:
        return self._weight
    def is_applicable(self, values: List[T]) -> bool:
        return bool(values)
    def run(self, values: List[T]) -> float:
        return self._func(values) * self._weight
