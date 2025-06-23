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
                    lambda v: isinstance(v, bool)
                              or (isinstance(v, str) and v.lower() in {"true","false","yes","no"})
                              or (isinstance(v, (int)) and v in {0,1})
                ),
                name="boolean_check",
                weight=1.0
            )
        ])
        self._example_values = ["True", "False", "1", "0", "yes", "no"]
