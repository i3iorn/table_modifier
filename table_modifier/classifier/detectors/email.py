import re

from table_modifier.classifier.detector import Detector


class EmailDetector(Detector):
    type_name = "email"
    parent_type = "string"
    keywords = ["email", "e-mail"]

    def is_applicable(self, values):
        # All values must be strings containing "@"
        return all(isinstance(v, str) and "@" in v for v in values if v)

    def detect(self, values):
        # Apply a basic regex to each non-null value
        pattern = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
        matches = [bool(pattern.match(v)) for v in values if v]
        if not matches:
            return 0.0
        # Score = fraction of values matching the pattern
        return sum(matches) / len(matches)

