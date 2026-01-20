from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class UserQuery:
    city: str | None
    min_salary: int | None
    education: str | None
    max_exp_years: int | None
    skills_text: str
    keyword: str | None

def recommend(df: pd.DataFrame, q: UserQuery, topk: int = 20,
              w_sim: float = 0.75, w_sal: float = 0.25) -> pd.DataFrame:
    cand = df.copy()
    # Hard filters
    if q.city:
        cand = cand[cand["city"].fillna("").str.contains(q.city, case=False, na=False)]
    if q.min_salary is not None:
        cand = cand[cand["salary_avg"].fillna(0) >= q.min_salary]
    if q.education and q.education != "Unknown":
        cand = cand[cand["education"] == q.education]
    if q.max_exp_years is not None:
        exp_num = pd.to_numeric(cand["exp"], errors="coerce").fillna(99)
        cand = cand[exp_num <= q.max_exp_years]
    if q.keyword:
        key = q.keyword.lower()
        cand = cand[
            cand["title"].fillna("").str.lower().str.contains(key)
            | cand["description"].fillna("").str.lower().str.contains(key)
        ]

    if len(cand) == 0:
        # 返回空的 DataFrame，但确保包含必要的列结构
        empty_df = pd.DataFrame(columns=df.columns.tolist() + ['score'])
        return empty_df

    # Soft ranking: TF-IDF similarity
    corpus = (cand["title"].fillna("") + " " + cand["description"].fillna("")).tolist()
    vec = TfidfVectorizer(max_features=5000, stop_words="english")
    X = vec.fit_transform(corpus)
    u = vec.transform([q.skills_text or ""])
    sim = cosine_similarity(u, X).flatten()

    # Salary normalization (fallback median)
    salary = cand["salary_avg"].fillna(cand["salary_avg"].median()).astype(float)
    salary_norm = (salary - salary.min()) / (salary.max() - salary.min() + 1e-9)

    cand = cand.assign(score=w_sim * sim + w_sal * salary_norm)
    return cand.sort_values("score", ascending=False).head(topk)
