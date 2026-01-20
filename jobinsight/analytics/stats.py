from __future__ import annotations
import pandas as pd

def city_top(df: pd.DataFrame, n: int = 20) -> pd.Series:
    if len(df) == 0 or "city" not in df.columns:
        return pd.Series(dtype=int)
    return df["city"].fillna("Unknown").value_counts().head(n)

def salary_hist(df: pd.DataFrame) -> pd.Series:
    s = df["salary_avg"].dropna()
    if len(s) == 0:
        return pd.Series(dtype=int)
    bins = [0, 5000, 10000, 15000, 20000, 30000, 50000, 100000, 200000]
    return pd.cut(s, bins=bins).value_counts().sort_index()

def tag_top(df: pd.DataFrame, n: int = 30) -> pd.Series:
    if len(df) == 0 or "tags" not in df.columns:
        return pd.Series(dtype=int)
    # tags stored as JSON string
    import json
    from collections import Counter
    c = Counter()
    for x in df["tags"].fillna("[]"):
        try:
            arr = json.loads(x)
            for t in arr:
                c[str(t).lower()] += 1
        except Exception:
            continue
    items = c.most_common(n)
    return pd.Series({k: v for k, v in items})
