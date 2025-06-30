# table_modifier/detectors/boolean.py
from ..detectors.base import Detector
from ..check.base import BaseCheck
from ..check.mixin import MatchCountCheckMixin

class BooleanDetector(Detector):
    def __init__(self):
        super().__init__([
            BaseCheck(
                func=lambda vals: MatchCountCheckMixin().by_predicate(
                    vals,
                    lambda v: str(v).lower() in {"true", "false", "1", "0", "yes", "no"}
                ),
                name="boolean_check"
            )
        ])
        self._example_values = ["True", "False", "1", "0", "yes", "no"]
