from typing import Optional, Tuple, List, Dict

from table_modifier.classifier.registry import DetectorRegistry


class ClassificationResult:
    def __init__(self, candidates: Dict[str, float], column_name: Optional[str] = None):
        print(candidates)
        self.candidates = candidates
        self.column_name = column_name

    def best_match(self):
        if not self.candidates:
            return None
        top_score = self.candidates[0][1]
        top_candidates = [t for (t,s) in self.candidates if s == top_score]
        if len(top_candidates) == 1:
            return top_candidates[0]
        # Tie-break: choose the type with greatest depth in hierarchy
        def depth(type_name):
            d = 0
            current = type_name
            while current and DetectorRegistry._registry[current].parent_type:
                d += 1
                current = DetectorRegistry._registry[current].parent_type
            return d
        return max(top_candidates, key=depth)

    def most_generic(self):
        top = self.best_match()
        if top is None:
            return None
        current = top
        while DetectorRegistry._registry[current].parent_type:
            current = DetectorRegistry._registry[current].parent_type
        return current
