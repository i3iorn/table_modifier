# table_modifier/detectors/numeric.py
from typing import Any, List
from ..detectors.base import Detector
from ..check.numeric import NumericCheck
from ..check.string import PatternCheck  # if you have any
from ..check.special import LengthVarianceCheck, UniquenessCheck
from ..check.numeric import VarianceCheck

class NumericDetector(Detector):
    def __init__(self):
        super().__init__()
        self.add_check(NumericCheck())

    def is_applicable(self, values: List[Any]) -> bool:
        # apply if any purely‐digit strings or numbers appear
        return any(isinstance(v, (int, float)) or (isinstance(v, str) and v.strip().isdigit())
                   for v in values)


class DunsDetector(NumericDetector):
    def __init__(self):
        super().__init__()
        self.add_check(PatternCheck(r"^\d{9}$", name="duns_check"))
        self.add_check(PatternCheck(r"^\d{2}-\d{3}-\d{4}$", weight=1.6, name="duns_hyphen_check"))
        self.add_check(LengthVarianceCheck(max_variance=0.1, weight=1.1))
        self.add_check(UniquenessCheck(min_uniqueness=0.8))


class NumericalCategoryDetector(NumericDetector):
    def __init__(self):
        super().__init__()
        self.add_check(VarianceCheck(max_variance=0.2))
        self.add_check(UniquenessCheck(max_uniqueness=0.1))


class ZipCodeDetector(NumericDetector):
    def __init__(self):
        super().__init__()
        self.add_check(PatternCheck(r"^\d{5}(-\d{4})?$", name="zip_code_check"))
        self.add_check(PatternCheck(r"^\d{5}$", weight=1.2, name="zip_code_5_digit_check"))
        self.add_check(LengthVarianceCheck(max_variance=0.1, weight=1.1))
        self.add_check(UniquenessCheck(min_uniqueness=0.8))


class PhoneNumberDetector(NumericDetector):
    def __init__(self):
        super().__init__()
        self.add_check(PatternCheck(
            r"^(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}$",
            name="phone_number_check", weight=0.75))
        self.add_check(LengthVarianceCheck(max_variance=0.1, weight=1.1))
        self.add_check(UniquenessCheck(min_uniqueness=0.8))


class NordicRegistrationNumberDetector(NumericDetector):
    def __init__(self):
        super().__init__()
        self.add_check(PatternCheck(
            r"^(?:\d{7}-\d|\d{8}|\d{9}|\d{10}|(16|[2-9]\d)\d{6}-?\d{4})$",
            name="nordic_registration_number_check", weight=0.5)
        )
        self.add_check(LengthVarianceCheck(max_variance=0.1, weight=1.1))
        self.add_check(UniquenessCheck(min_uniqueness=0.8))


class SwedishRegistrationNumberDetector(NumericDetector):
    def __init__(self):
        super().__init__()
        self.add_check(PatternCheck(
            r"^(16)?\d{6}(-)?\d{4}$", name="swedish_registration_number_check"))
        self.add_check(LengthVarianceCheck(max_variance=0.1, weight=1.1))
        self.add_check(UniquenessCheck(min_uniqueness=0.8))


class NorwegianRegistrationNumberDetector(NumericDetector):
    def __init__(self):
        super().__init__()
        self.add_check(PatternCheck(
            r"^\d{9}$", name="norwegian_registration_number_check", weight=0.75))
        self.add_check(LengthVarianceCheck(max_variance=0.1, weight=1.1))
        self.add_check(UniquenessCheck(min_uniqueness=0.8))


class FinnishRegistrationNumberDetector(NumericDetector):
    def __init__(self):
        super().__init__()
        self.add_check(PatternCheck(
            r"^\d{7}-\d$", name="finnish_registration_number_check"))
        self.add_check(LengthVarianceCheck(max_variance=0.01, weight=1.1))
        self.add_check(UniquenessCheck(min_uniqueness=0.8))


class DanishRegistrationNumberDetector(NumericDetector):
    def __init__(self):
        super().__init__()
        self.add_check(PatternCheck(
            r"^\d{8}$", name="danish_registration_number_check", weight=0.75))
        self.add_check(LengthVarianceCheck(max_variance=0.01, weight=1.1))
        self.add_check(UniquenessCheck(min_uniqueness=0.8))


