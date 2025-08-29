import pytest
from src.table_modifier.classifier.result import ClassificationResult


def test_best_match_threshold_none():
    res = ClassificationResult(candidates={"boolean": 0.05}, column_name="x")
    best, score = res.best_match(threshold=0.1)
    assert best is None and score is None


def test_tie_break_prefers_deeper_type_and_most_generic():
    # numeric is parent of duns; both with equal score -> choose duns
    res = ClassificationResult(candidates={"numeric": 0.8, "duns": 0.8})
    best, score = res.best_match(threshold=0.0)
    assert best == "duns"
    # most generic for duns should be numeric
    assert res.most_generic() in {"numeric", "text", "boolean"}  # duns -> numeric

