# table_modifier/detectors/text.py
from typing import Any, List
from ..detectors.base import Detector
from ..check.string import StringCheck, PatternCheck, LengthCheck
from ..check.base import BaseCheck
from ..check.mixin import MatchCountCheckMixin

class TextDetector(Detector):
    def __init__(self):
        super().__init__([StringCheck()])
    def is_applicable(self, values: List[Any]) -> bool:
        return sum(1 for v in values if isinstance(v, str)) / max(1, len(values)) > 0.1
    def example_values(self):
        return ["Hello", "World"]

class CountryCodeDetector(TextDetector):
    def __init__(self):
        super().__init__()
        self.add_check(PatternCheck(r"^[A-Z]{2}$", weight=2.0, name="country_code"))
        self.add_check(LengthCheck(2, 2, weight=1.5, name="country_code_length"))
    def keywords(self):
        return ["country", "iso"]

class NameDetector(Detector):
    def __init__(self):
        super().__init__([
            BaseCheck(
                func=lambda vals: MatchCountCheckMixin().by_predicate(
                    vals, lambda v: isinstance(v, str) and all(p.isalpha() for p in v.split())
                ),
                name="name_alpha_check",
                weight=1.0
            ),
            LengthCheck(3, 50, name="name_length", weight=1.0)
        ])
    def keywords(self):
        return ["name"]

class CompanyNameDetector(TextDetector):
    def __init__(self):
        super().__init__()
        self.add_check(PatternCheck(r"^[A-Za-z0-9\s&.,-]+$", weight=1.5, name="company_name_pattern"))
        self.add_check(LengthCheck(3, 100, weight=1.0, name="company_name_length"))
    def keywords(self):
        return ["company", "business", "organization"]


class CountryNameDetector(TextDetector):
    def __init__(self):
        super().__init__()
        self.add_check(PatternCheck(r"^[A-Za-z\s-]+$", weight=1.5, name="country_name_pattern"))
        self.add_check(LengthCheck(3, 50, weight=1.0, name="country_name_length"))
    def keywords(self):
        return ["country", "nation", "state"]


class TextCategoryDetector(TextDetector):
    def __init__(self):
        super().__init__()
        self.add_check(PatternCheck(r"^[A-Za-z\s]+$", weight=1.5, name="text_category_pattern"))
        self.add_check(LengthCheck(3, 50, weight=1.0, name="text_category_length"))
    def keywords(self):
        return ["category", "type", "classification"]


class CurrencyCodeDetector(TextDetector):
    def __init__(self):
        super().__init__()
        self.add_check(PatternCheck(r"^[A-Z]{3}$", weight=2.0, name="currency_code"))
        self.add_check(LengthCheck(3, 3, weight=1.5, name="currency_code_length"))
    def keywords(self):
        return ["currency", "iso4217"]