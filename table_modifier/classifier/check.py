from typing import Callable, Protocol, Generic, TypeVar, List, Optional

T = TypeVar("T")

class BaseCheck(Protocol, Generic[T]):
    def run(self, values: List[T]) -> float:
        ...

    @property
    def weight(self) -> float:
        ...

class MustCheck(BaseCheck):
    def __init__(self, func: Callable[[List[str]], bool]):
        self.func = func

    def run(self, values: List[str]) -> float:
        return 1.0 if self.func(values) else 0.0

    @property
    def weight(self) -> float:
        return 1.0


class MustNotCheck(BaseCheck):
    def __init__(self, func: Callable[[List[str]], bool]):
        self.func = func

    def run(self, values: List[str]) -> float:
        return 0.0 if self.func(values) else 1.0

    @property
    def weight(self) -> float:
        return 1.0


class MightCheck(BaseCheck):
    def __init__(self, func: Callable[[List[str]], float], weight: float = 1.0):
        self.func = func
        self._weight = weight

    def run(self, values: List[str]) -> float:
        return self.func(values)

    @property
    def weight(self) -> float:
        return self._weight


class MightNotCheck(BaseCheck):
    def __init__(self, func: Callable[[List[str]], float], weight: float = 1.0):
        self.func = func
        self._weight = weight

    def run(self, values: List[str]) -> float:
        return 1.0 - self.func(values)

    @property
    def weight(self) -> float:
        return self._weight
