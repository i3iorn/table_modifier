

import re
from typing import List

from table_modifier.classifier.check import MustCheck, MightCheck
from table_modifier.classifier.detector import CheckBasedDetector


class NameDetector(CheckBasedDetector):
    """
    Detects if a column contains names (e.g. first names, last names, full names).
    Uses character heuristics and formatting patterns.
    """

    type_name = "name"
    parent_type = "string"
    keywords = ["first name", "last name", "full name", "person name", "name"]

    def __init__(self) -> None:
        super().__init__()
        self.must_checks = [
            MustCheck(lambda values: all(isinstance(v, str) and v.strip() for v in values)),
            MustCheck(lambda values: not any(re.search(r"\\d", v) for v in values))
        ]
        self.might_checks = [
            MightCheck(lambda values: sum(
                    v[0].isupper() and v[1:].islower()
                    for v in values if isinstance(v, str) and len(v) > 1
                ) / len(values),
                weight=0.4
            ),
            MightCheck(lambda values: sum(
                    len(v.split()) > 1
                    for v in values if isinstance(v, str)
                ) / len(values),
                weight=0.4
            ),
            MightCheck(lambda values: sum(
                    v.isalpha()
                    for v in values if isinstance(v, str)
                ) / len(values),
                weight=0.2
            )
        ]

    def is_applicable(self, values: List[str]) -> bool:
        """
        Check if the detector is applicable to the given values.

        Args:
            values (List[str]): The list of values to check.

        Returns:
            bool: True if applicable.
        """
        return all(isinstance(v, str) for v in values)
