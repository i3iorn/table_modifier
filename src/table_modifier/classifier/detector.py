import logging
from abc import ABC
from typing import List, Any

from src.table_modifier.classifier import normalize_numeral
from src.table_modifier.classifier.check import AbstractCheck
from src.table_modifier.classifier.registry import DetectorRegistry


class Detector(ABC):
    """Abstract base class for all column-type detectors."""
    def __init__(self, checks: List[AbstractCheck[Any]] = None):
        """
        Initialize the detector with a type name and an optional parent type.
        """
        DetectorRegistry.register(self)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._checks = checks or []

    def add_check(self, check: AbstractCheck[Any]) -> None:
        """
        Add a check to this detector.
        This allows dynamic addition of checks after initialization.
        """
        if not isinstance(check, AbstractCheck):
            raise TypeError("check must be an instance of AbstractCheck")
        self._checks.append(check)
        self.logger.debug(f"Added check {check.name()} to detector {self.type_name()}")

    def depth(self) -> int:
        """
        Return the depth of this detector in the type hierarchy.
        The depth is defined as the number of parent types in the hierarchy.
        """
        depth = 0
        current = self.parent_type()
        while current:
            depth += 1
            current = DetectorRegistry._registry[current].parent_type()
        return depth

    def checks(self) -> List[AbstractCheck[Any]]:
        """
        Return the list of checks associated with this detector.
        This allows dynamic addition of checks after initialization.
        """
        return self._checks

    def detect(self, values: List[str]) -> float:
        """
        Assess how well the column values match this type.
        Returns a score in [0.0, 1.0], with 1.0 for a perfect match.
        """
        score = 0.0
        check_done = set()

        for check in self.checks():
            if check.is_applicable(values):
                score += check.run(values)
                check_done.add(check.name)

        if not check_done:
            self.logger.debug(f"No applicable checks for detector {self.type_name()}")

        # Normalize the score based on the number of checks run
        if check_done:
            score /= len(check_done)

        return normalize_numeral((score * self.depth()) ** (1 + len(check_done)/10))

    def example_values(self) -> List[str]:
        """
        Return a list of example values that represent this type.
        This is used for debugging and documentation purposes.
        """
        return []

    def is_applicable(self, values: List[str]) -> bool:
        """
        Quick check: return False to skip this detector if values violate basic format.
        Detectors can override this (e.g., numeric detectors skip if any value has letters).
        """
        return True

    def keywords(self) -> List[str]:
        """
        Return a list of keywords that this detector matches against column names.
        This helps boost scores when the column name matches these keywords.
        """
        return []

    @classmethod
    def parent_type(cls) -> str:
        """
        Return the name of the parent type, if this detector is a specialization.
        """
        return cls.__bases__[0].__name__.replace("Detector", "").lower() if cls.__bases__ else None

    @classmethod
    def type_name(cls) -> str:
        """
        Return the name of the type this detector classifies.
        This should be unique across all detectors.
        """
        return cls.__name__.replace("Detector", "").lower()
