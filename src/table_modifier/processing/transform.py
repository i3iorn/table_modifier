from typing import Any, Dict, List

import pandas as pd


def is_contiguous_prefix_zero_based(rows: List[int]) -> bool:
    if not rows:
        return True
    rows_sorted = sorted(set(int(r) for r in rows if int(r) >= 0))
    return rows_sorted == list(range(len(rows_sorted)))


def combine_sources(df: pd.DataFrame, sources: List[str], sep: str) -> pd.Series:
    """
    Combine multiple source columns into a single Series using the provided separator.

    - Missing columns produce empty strings and a best-effort warning by caller.
    - NaN values are treated as empty strings.
    - All values coerced to string for safe concatenation.
    """
    if not sources:
        return pd.Series(["" for _ in range(len(df))], index=df.index)
    parts: List[pd.Series] = []
    for col in sources:
        if col in df.columns:
            s = df[col]
            # Convert to str but keep NaN as empty
            s = s.astype(str)
            s = s.where(~s.isna(), "")
            parts.append(s)
        else:
            parts.append(pd.Series([""] * len(df), index=df.index))
    if not parts:
        return pd.Series([""] * len(df), index=df.index)
    # Efficient concatenation using vectorized join across columns
    out = parts[0]
    for s in parts[1:]:
        out = out.str.cat(s, sep=sep)
    return out


def apply_mapping(df: pd.DataFrame, mapping: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Given a DataFrame and a structured mapping:
    [
      {"sources": ["A", "B"], "separator": " "},
      {"sources": ["C"], "separator": ","}
    ]
    produce an output DataFrame with one column per mapping entry.

    Column naming strategy:
    - Single source -> use that source name
    - Multi-source -> "Combined_{i+1}"
    """
    outputs: Dict[str, pd.Series] = {}
    for i, entry in enumerate(mapping):
        sources = list(entry.get("sources", []))
        sep = entry.get("separator") or " "
        col_name = sources[0] if len(sources) == 1 else f"Combined_{i+1}"
        outputs[col_name] = combine_sources(df, sources, sep)
    if not outputs:
        return pd.DataFrame(index=df.index)
    return pd.DataFrame(outputs, index=df.index)

