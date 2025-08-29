import pytest
from datetime import datetime

from src.table_modifier.classifier.check.date import DateCheck


def test_date_check_score_and_applicability():
    dc = DateCheck()
    values = [
        "2024-01-31",
        "31/01/2024",
        "01/31/2024",
        "2024-01-31T12:34:56",
        "31 Jan 2024",
        "January 31, 2024",
        datetime(2023, 5, 1),
        "invalid",
    ]
    score = dc._score(values)
    assert score == 7 / 8
    assert dc.is_applicable(values) is True
    assert dc.is_applicable([1, 2, 3]) is False


def test_date_check_empty():
    dc = DateCheck()
    assert dc._score([]) == 0.0
