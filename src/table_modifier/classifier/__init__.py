import difflib
from pandas import isna
from typing import List, Optional, Type, Any, Dict

from src.table_modifier.classifier.detectors import *
from .registry import DetectorRegistry
from .result import ClassificationResult
from .utils import normalize_numeral


class ColumnTypeClassifier:
    """Main engine that classifies column type using detectors and heuristics."""

    def __init__(self, registry: Type[DetectorRegistry]):
        self.registry = registry

    def classify(
        self,
        values: List[Any],
        column_name: Optional[str] = None
    ) -> ClassificationResult:
        """Classifies a column using all applicable detectors.

        Args:
            values: List of stringified values in the column.
            column_name: Optional column label to aid classification.

        Returns:
            ClassificationResult containing scored types.
        """
        values = [None if isna(x) else x for x in values]
        name = column_name.lower() if column_name else ""
        candidates: Dict[str, float] = {}

        #print(f"\n=====================================================================\nClassifying column '{column_name}' with values: {values[:5]}...")
        for detector in self.registry.get_detectors():
            if not detector.is_applicable(values):
                continue

            score = detector.detect(values)
            if score == 0.0:
                continue
            #print(f"Detector: {detector.type_name()}, Score: {score:.2f}")

            # Name-based boost
            if any(kw in name for kw in detector.keywords()):
                score += 0.1
                #print(f"Boosted {detector.type_name()} for keywords in name: {detector.keywords()} to {score:.2f}")
            else:
                sim = difflib.SequenceMatcher(None, name, detector.type_name()).ratio()
                score += max(sim, 0.0) * 0.05
                #print(f"Similarity boost for {detector.type_name()}: {sim:.2f} to {score:.2f}")

            score = normalize_numeral(score)

            if score > 0.0:
                candidates[detector.type_name()] = score

        # Loop through candidates and adjust scores based on parent-child relationships
        for candidate in list(candidates.keys()):
            detector = self.registry._registry[candidate]
            parent = detector.parent_type()
            if parent and parent in candidates:
                # If this candidate has a parent, adjust its score based on the parents score
                parent_score = candidates[parent]
                candidates[candidate] = candidates[candidate] + parent_score / 5

        return ClassificationResult(
            column_name=column_name,
            candidates=candidates,
            example_values=[v for v in values if str(v).strip()][:3]
        )

TextDetector()
BooleanDetector()
NumericDetector()
NameDetector()
CompanyNameDetector()
DunsDetector()
CountryCodeDetector()
NumericalCategoryDetector()
TextCategoryDetector()
CountryNameDetector()
CurrencyCodeDetector()
PhoneNumberDetector()
NordicRegistrationNumberDetector()
SwedishRegistrationNumberDetector()
NorwegianRegistrationNumberDetector()
DanishRegistrationNumberDetector()
FinnishRegistrationNumberDetector()