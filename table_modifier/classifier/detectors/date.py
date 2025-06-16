import re
from typing import List
from table_modifier.classifier.detector import CheckBasedDetector, MustNotCheck, MightCheck


class DateDetector(CheckBasedDetector):
    type_name = "date"
    parent_type = "hyphenated_integer"
    keywords = ["date"]

    def __init__(self):
        super().__init__()

        # Disqualify if any values contain alphabetic strings of length >= 2
        self.must_not_checks = [
            MustNotCheck(lambda vs: any(re.search(r"[a-zA-Z]{2,}", v) for v in vs))
        ]

        self.might_checks = [
            MightCheck(self._date_format_score, weight=1.0)
        ]

    def _date_format_score(self, values: List[str]) -> float:
        """
        Compute a score based on how many values match known date formats.

        Supported formats:
        - YYYY-MM-DD
        - DD/MM/YYYY
        - DD-MM-YYYY
        - D Month YYYY
        - YYYY Month D
        - YYYY Month DD
        - MM.DD.YYYY
        - MM/DD/YYYY

        Args:
            values (List[str]): The list of values to evaluate.

        Returns:
            float: Normalized confidence score in range [0.0, 1.0].
        """
        match_count = 0
        for value in values:
            if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
                year, month, day = map(int, value.split("-"))
                if 1 <= month <= 12 and 1 <= day <= 31:
                    match_count += 1

            elif re.match(r"^\d{2}/\d{2}/\d{4}$", value):
                day, month, year = map(int, value.split("/"))
                if 1 <= month <= 12 and 1 <= day <= 31:
                    match_count += 1

            elif re.match(r"^\d{2}-\d{2}-\d{4}$", value):
                day, month, year = map(int, value.split("-"))
                if 1 <= month <= 12 and 1 <= day <= 31:
                    match_count += 1

            elif re.match(r"^\d{1,2} [A-Za-z]+ \d{4}$", value):
                parts = value.split()
                if len(parts) == 3:
                    day = int(parts[0])
                    month = self._month_name_to_number(parts[1])
                    year = int(parts[2])
                    if month and 1 <= day <= 31:
                        match_count += 1

            elif re.match(r"^\d{4} [A-Za-z]+ \d{1,2}$", value):
                parts = value.split()
                if len(parts) == 3:
                    year = int(parts[0])
                    month = self._month_name_to_number(parts[1])
                    day = int(parts[2])
                    if month and 1 <= day <= 31:
                        match_count += 1

            elif re.match(r"^\d{4} [A-Za-z]+ \d{2}$", value):
                parts = value.split()
                if len(parts) == 3:
                    year = int(parts[0])
                    month = self._month_name_to_number(parts[1])
                    day = int(parts[2])
                    if month and 1 <= day <= 31:
                        match_count += 1

            elif re.match(r"^\d{2}\.\d{2}\.\d{4}$", value):
                month, day, year = map(int, value.split("."))
                if 1 <= month <= 12 and 1 <= day <= 31:
                    match_count += 1

            elif re.match(r"^\d{2}/\d{2}/\d{4}$", value):
                month, day, year = map(int, value.split("/"))
                if 1 <= month <= 12 and 1 <= day <= 31:
                    match_count += 1

        return match_count / len(values) if values else 0.0

    def _month_name_to_number(self, name: str) -> int:
        """Convert month name to corresponding number."""
        months = {
            "January": 1, "February": 2, "March": 3,
            "April": 4, "May": 5, "June": 6,
            "July": 7, "August": 8, "September": 9,
            "October": 10, "November": 11, "December": 12
        }
        return months.get(name.capitalize(), 0)
