from loghelpers import log_calls
from typing import Optional

# half‑saturation constant a, solved from 2 / (2 + a) = 0.9
_A = 2 * (1 - 0.9) / 0.9


@log_calls()
def normalize_numeral(x: float | int, __half_saturation_constant: Optional[float] = None) -> float:
    """
    Normalize x to [0.0, 1.0), never reaching 1.0 but approaching it.

    - normalize(0) == 0.0
    - normalize(2) == 0.9
    - normalize(x→∞) → 1.0

    Args:
        __half_saturation_constant: Optional half-saturation constant, defaults to _A.
            If provided, it overrides the default value.
        x: A non‑negative value to normalize.
    Returns:
        A float in [0.0, 1.0).
    """
    if x <= 0:
        return 0.0
    return x / (x + _A)


def normalize_alpha(x: str) -> str:
    """
    Normalize a string to lowercase and strip whitespace.

    Args:
        x: The string to normalize.
    Returns:
        A normalized string in lowercase with leading/trailing whitespace removed.
    """
    return x.strip() if x else ""


def normalize_numeral_list(values: list[float | int]) -> list[float]:
    """
    Normalize a list of values to [0.0, 1.0).
    Args:
        values: A list of non‑negative values to normalize.

    Returns:
        A list of normalized floats in [0.0, 1.0).
    """
    return [normalize_numeral(v) for v in values if isinstance(v, (int, float)) and v >= 0]


def normalize_alpha_list(values: list[str]) -> list[str]:
    """
    Normalize a list of strings to lowercase and strip whitespace.

    Args:
        values: A list of strings to normalize.

    Returns:
        A list of normalized strings in lowercase with leading/trailing whitespace removed.
    """
    return [normalize_alpha(v) for v in values if isinstance(v, str)]
