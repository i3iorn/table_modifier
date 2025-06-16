from abc import ABC, abstractmethod
from typing import Optional, List

from table_modifier.classifier.check import MustCheck, MustNotCheck, MightCheck, \
    MightNotCheck
from table_modifier.classifier.registry import DetectorRegistry


class Detector(ABC):
    """Abstract base class for all column-type detectors."""
    type_name: str             # Unique type identifier
    parent_type: Optional[str] # Name of a more generic parent type
    keywords: Optional[List[str]] = None  # Optional keywords for this type

    def __init__(self):
        """
        Initialize the detector with a type name and an optional parent type.

        :param type_name: Unique identifier for this detector type.
        :param parent_type: Name of a more generic parent type, if applicable.
        """
        DetectorRegistry.register(self)

    @abstractmethod
    def detect(self, values: List[str]) -> float:
        """
        Assess how well the column values match this type.
        Returns a score in [0.0, 1.0], with 1.0 for a perfect match.
        """
        pass

    def is_applicable(self, values: List[str]) -> bool:
        """
        Quick check: return False to skip this detector if values violate basic format.
        Detectors can override this (e.g., numeric detectors skip if any value has letters).
        """
        return True


class CheckBasedDetector(Detector, ABC):
    def __init__(self):
        super().__init__()
        self.must_checks: List[MustCheck] = []
        self.must_not_checks: List[MustNotCheck] = []
        self.might_checks: List[MightCheck] = []
        self.might_not_checks: List[MightNotCheck] = []

    def detect(self, values: List[str]) -> float:
        for check in self.must_checks + self.must_not_checks:
            if check.run(values) < 1.0:
                return 0.0

        weighted_scores = []
        total_weight = 0.0

        for check in self.might_checks + self.might_not_checks:
            score = check.run(values)
            weight = check.weight
            weighted_scores.append(score * weight)
            total_weight += weight

        return sum(weighted_scores) / total_weight if total_weight else 1.0
