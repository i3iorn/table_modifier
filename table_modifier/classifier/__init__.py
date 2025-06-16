import difflib
from typing import List, Optional, Dict, Type

from .detectors.date import DateDetector
from .detectors.duns import DunsDetector
from .detectors.email import EmailDetector
from .detectors.hyphenated_integer import HyphenatedIntegerDetector, IntegerDetector
from .detectors.name import NameDetector
from .registry import DetectorRegistry
from .result import ClassificationResult


class ColumnTypeClassifier:
    """Main engine that classifies column type using detectors and heuristics."""

    def __init__(self, registry: Type[DetectorRegistry]):
        self.registry = registry

    def classify(
        self,
        values: List[str],
        column_name: Optional[str] = None
    ) -> ClassificationResult:
        """Classifies a column using all applicable detectors.

        Args:
            values: List of stringified values in the column.
            column_name: Optional column label to aid classification.

        Returns:
            ClassificationResult containing scored types.
        """
        name = column_name.lower() if column_name else ""
        candidates: Dict[str, float] = {}

        for detector in self.registry.get_detectors():
            if not detector.is_applicable(values):
                continue

            score = detector.detect(values)

            # Name-based boost
            if any(kw in name for kw in detector.keywords):
                score += 0.1
            else:
                sim = difflib.SequenceMatcher(None, name, detector.type_name).ratio()
                score += sim * 0.05

            score = min(score, 1.0)
            if score > 0.0:
                candidates[detector.type_name] = score

        return ClassificationResult(column_name=column_name, candidates=candidates)


DunsDetector()
EmailDetector()
IntegerDetector()
HyphenatedIntegerDetector()
DateDetector()
NameDetector()
