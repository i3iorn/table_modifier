import pytest

from src.table_modifier.classifier import ColumnTypeClassifier, DetectorRegistry


def test_classifier_boolean_column():
    clf = ColumnTypeClassifier(DetectorRegistry)
    values = ["True", "False", "yes", "no", "0", "1"]
    res = clf.classify(values, column_name="is_active")
    assert isinstance(res.candidates, dict)
    # should include boolean candidate with a non-zero score
    assert any(k == "boolean" and v > 0 for k, v in res.candidates.items())
    # example_values not empty
    assert len(res.example_values) > 0
