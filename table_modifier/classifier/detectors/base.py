# table_modifier/detectors/base.py
import logging
from abc import ABC
from typing import Any, List

from ..utils import normalize_numeral
from ..registry import DetectorRegistry
from ..check.base import AbstractCheck

class Detector(ABC):
    def __init__(self, checks: List[AbstractCheck[Any]] = None):
        DetectorRegistry.register(self)
        self.logger = logging.getLogger(type(self).__name__)
        self._checks = checks or []
    def add_check(self, check: AbstractCheck[Any]) -> None:
        self._checks.append(check)
        self.logger.debug("Added %s to %s", check.name(), self.type_name())
    def detect(self, values: List[Any]) -> float:
        applicable = [c for c in self._checks if c.is_applicable(values)]
        if not applicable:
            self.logger.debug("No applicable checks in %s", self.type_name())
            return 0.0
        raw = sum(c.run(values) for c in applicable) / len(applicable)

        return normalize_numeral(raw + len(applicable) / 10)

    @classmethod
    def type_name(cls) -> str:
        return cls.__name__.replace("Detector", "").lower()

    def is_applicable(self, values: List[Any]) -> bool:
        """
        Check if this detector is applicable to the given values.
        This is a simple heuristic based on the checks defined for this detector.
        """
        return any(check.is_applicable(values) for check in self._checks)

    def keywords(self) -> List[str]:
        """
        Return a list of keywords that this detector is associated with.
        This can be used for name-based boosting during classification.
        """
        return [self.type_name()]

    @classmethod
    def parent_type(cls) -> str:
        """
        Return the parent type of this detector.
        This is used to establish a hierarchy of detectors.
        By default, detectors have no parent.
        """
        return cls.__name__.replace("Detector", "").lower() if cls.__name__ != "Detector" else None
