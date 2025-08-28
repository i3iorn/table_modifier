import re
from typing import Iterable, List, Set

_RANGE_RE = re.compile(r"^\s*(\d+)\s*[-\.]{1,2}\s*(\d+)\s*$")
_INT_RE = re.compile(r"^\s*\d+\s*$")


def parse_skip_rows(expr: str | None) -> List[int]:
    """Parse a skip-rows expression like "0,1,2", "2-5", or "1, 4-6, 10".

    Rules:
    - Accept comma-separated items; each item is either an integer N or a range A-B / A..B
    - Ignore empty items and surrounding whitespace
    - Only non-negative integers are allowed
    - Ranges are inclusive; order of endpoints doesn't matter (2-5 == 5-2)

    Returns a sorted list of unique integers.

    Raises ValueError on invalid tokens.
    """
    if not expr:
        return []
    values: Set[int] = set()
    for token in expr.split(','):
        token = token.strip()
        if not token:
            continue
        if _INT_RE.match(token):
            n = int(token)
            values.add(n)
            continue
        m = _RANGE_RE.match(token)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a <= b:
                rng = range(a, b + 1)
            else:
                rng = range(b, a + 1)
            values.update(rng)
            continue
        raise ValueError(f"Invalid skip-rows token: '{token}'")
    return sorted(values)


def is_valid_skip_rows(expr: str | None) -> bool:
    try:
        parse_skip_rows(expr)
        return True
    except Exception:
        return False

