from __future__ import annotations
import pandas as pd

def trend_by_date(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) == 0 or "crawl_date" not in df.columns:
        return pd.DataFrame(columns=["crawl_date", "postings"])
    g = df.groupby("crawl_date").size().reset_index(name="postings")
    g["crawl_date"] = pd.to_datetime(g["crawl_date"])
    return g.sort_values("crawl_date")

def tag_trend(df: pd.DataFrame, tag: str) -> pd.DataFrame:
    import json
    tag_l = tag.lower()
    def has_tag(s: str) -> bool:
        try:
            arr = json.loads(s) if s else []
            return any(str(x).lower() == tag_l for x in arr)
        except Exception:
            return False

    hit = df["tags"].fillna("[]").apply(has_tag)
    g = df.assign(hit=hit).groupby("crawl_date")["hit"].mean().reset_index(name="ratio")
    g["crawl_date"] = pd.to_datetime(g["crawl_date"])
    return g.sort_values("crawl_date")
