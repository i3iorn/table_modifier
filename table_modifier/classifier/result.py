from typing import Optional, Tuple, List, Dict

from table_modifier.classifier.registry import DetectorRegistry


class ClassificationResult:
    def __init__(self, candidates: Dict[str, float], column_name: Optional[str] = None, example_values: Optional[List[str]] = None):
        # Sort candidates by score in descending order
        self._candidates = {k: v for k, v in sorted(candidates.items(), key=lambda item: item[1], reverse=True)}
        self.column_name = column_name
        self.example_values = example_values if example_values is not None else []

    @property
    def candidates(self) -> Dict[str, float]:
        """Return the dictionary of candidate types and their scores."""
        return self._candidates

    def best_match(self, threshold: float = 0.1) -> Tuple[Optional[str], Optional[float]]:
        if not self.candidates:
            # No candidates found
            return None, None

        top_score = max(self.candidates.values())
        if top_score < threshold:
            # No strong candidates
            return None, None

        top_candidates = [t for (t,s) in self.candidates.items() if s == top_score]
        if len(top_candidates) == 1:
            # Only one candidate with the highest score
            return top_candidates[0], top_score

        # Tie-break: choose the type with greatest depth in hierarchy
        best_type = None
        best_depth = -1
        for candidate in top_candidates:
            depth = 0
            current = candidate
            while DetectorRegistry._registry[current].parent_type():
                current = DetectorRegistry._registry[current].parent_type()
                depth += 1

            if depth > best_depth:
                best_depth = depth
                best_type = candidate

        return best_type, top_score

    def most_generic(self):
        top = self.best_match()
        if top is None:
            return None
        current = top
        while DetectorRegistry._registry[current].parent_type:
            current = DetectorRegistry._registry[current].parent_type
        return current

    def __repr__(self):
        return f"ClassificationResult(column_name={self.column_name}, candidates={self.candidates})"
