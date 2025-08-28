import logging
from abc import ABC
from typing import List, Any, Optional

from src.table_modifier.classifier.utils import normalize_numeral
from src.table_modifier.classifier.check import AbstractCheck
from src.table_modifier.classifier.registry import DetectorRegistry


class Detector(ABC):
    """Abstract base class for all column-type detectors."""

    def __init__(self, checks: List[AbstractCheck[Any]] = None):
        """
        Initialize the detector with optional checks and register it.
        """
        DetectorRegistry.register(self)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._checks = checks or []

    def add_check(self, check: AbstractCheck[Any]) -> None:
        """Add a check to this detector at runtime."""
        if not isinstance(check, AbstractCheck):
            raise TypeError("check must be an instance of AbstractCheck")
        else:
            self._checks.append(check)
            self.logger.debug(f"Added check {check.name()} to detector {self.type_name()}")

    def depth(self) -> int:
        """
        Return the depth of this detector in the type hierarchy.
        Depth is the number of detector ancestors excluding the base Detector.
        """
        depth = 0
        parent = self.parent_type()
        while parent:
            depth += 1
            parent = DetectorRegistry._registry[parent].parent_type()  # type: ignore[attr-defined]
        return depth

    def checks(self) -> List[AbstractCheck[Any]]:
        """Return the list of checks associated with this detector."""
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
                check_done.add(check.name())

        self.logger.debug(f"Detector {self.type_name()} checks done: {check_done}, score: {score:.2f}")

        if not check_done:
            self.logger.debug(f"No applicable checks for detector {self.type_name()}")

        # Normalize the score based on the number of checks run
        if check_done:
            score /= len(check_done)

        if score <= 0.3:
            self.logger.debug(f"Low score {score:.2f} for detector {self.type_name()}")
            return score

        self.logger.debug(f"Detector {self.type_name()} score before depth normalization: {score:.2f}")

        # Favor more specific (deeper) detectors; base depth treated as 1
        effective_depth = max(1, self.depth())
        return normalize_numeral((score * effective_depth) ** (1 + len(check_done) / 10))

    def example_values(self) -> List[str]:
        """Return a list of example values that represent this type."""
        return []

    def is_applicable(self, values: List[str]) -> bool:
        """
        Quick check: return False to skip this detector if values violate basic format.
        Detectors can override this (e.g., numeric detectors skip if any value has letters).
        """
        return True

    def keywords(self) -> List[str]:
        """Column-name keywords that boost this detector's score when present."""
        return []

    @classmethod
    def parent_type(cls) -> Optional[str]:
        """
        Return the name of the parent type if this detector specializes another detector.
        Detects the immediate base class that ends with 'Detector' and isn't the root Detector.
        """
        for base in cls.__bases__:
            name = getattr(base, "__name__", "")
            if name.endswith("Detector") and name != "Detector":
                return name.replace("Detector", "").lower()
        return None

    @classmethod
    def type_name(cls) -> str:
        """Unique detector type name derived from class name."""
        return cls.__name__.replace("Detector", "").lower()
