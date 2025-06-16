import re

from table_modifier.classifier.detector import Detector


class HyphenatedIntegerDetector(Detector):
    type_name = "hyphenated_integer"
    parent_type = "integer"
    keywords = ["hyphen", "hyphenated"]

    def is_applicable(self, values):
        # Allow only digits or hyphens, and require at least one hyphen.
        return all(re.fullmatch(r'[0-9\-]+', str(v)) and '-' in str(v)
                   for v in values if v)

    def detect(self, values):
        return 0.8  # e.g., 80% confidence for this broad match

class IntegerDetector(Detector):
    type_name = "integer"
    parent_type = "numeric"
    keywords = ["integer", "int"]

    def is_applicable(self, values):
        return all(str(v).isdigit() for v in values if v is not None)

    def detect(self, values):
        return 1.0  # exact match if all digits
