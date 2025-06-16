import re
from typing import List

from table_modifier.classifier.check import MustCheck, MightCheck
from table_modifier.classifier.detector import CheckBasedDetector


class DunsDetector(CheckBasedDetector):
    type_name = "duns"
    keywords = ["duns", "d-u-n-s", "dunsnumber"]

    def __init__(self):
        super().__init__()
        self.must_checks = [
            MustCheck(lambda vs: all(isinstance(v, str) for v in vs)),
            MustCheck(lambda vs: len(vs) > 0)
        ]

        self.might_checks = [
            MightCheck(self._format_match_score, weight=0.7),
            MightCheck(self._length_match_score, weight=0.3),
        ]

    def _format_match_score(self, values: List[str]) -> float:
        pattern1 = re.compile(r"^\d{2}-\d{3}-\d{4}$")
        pattern2 = re.compile(r"^\d{9}$")
        matched = sum(bool(pattern1.match(v) or pattern2.match(v)) for v in values)
        return matched / len(values) if values else 0.0

    def _length_match_score(self, values: List[str]) -> float:
        return sum(1 for v in values if len(v.strip()) in (9, 11)) / len(values)
