import pytest
from src.table_modifier.classifier import BooleanDetector


def test_detects_boolean_values_probability():
    detector = BooleanDetector()
    values = ["True", "False", "1", "0", "yes", "no"]
    result = detector.detect(values)
    assert isinstance(result, float)
    assert 0.6 <= result <= 0.8
    # Expect high probability for clear boolean values,
    # tempered by the fact that the detector is very generic.

def test_detects_non_boolean_values_probability():
    detector = BooleanDetector()
    values = ["hello", "world", 123, None]
    result = detector.detect(values)
    assert isinstance(result, float)
    assert 0.0 <= result <= 0.3  # Expect low probability for non-boolean values

def test_handles_empty_input_probability():
    detector = BooleanDetector()
    values = []
    result = detector.detect(values)
    assert isinstance(result, float)
    assert result == 0.0  # No data should yield zero probability

def test_handles_mixed_values_probability():
    detector = BooleanDetector()
    values = ["True", "False", "hello", 123]
    result = detector.detect(values)
    assert isinstance(result, float)
    assert 0.2 < result < 0.5  # Mixed values should yield low probability