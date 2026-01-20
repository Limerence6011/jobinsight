from __future__ import annotations

SKILL_DICT = [
    "python","java","c++","golang","rust","sql","linux","docker","kubernetes",
    "spark","hadoop","pandas","numpy","matplotlib","pyecharts","flask","django",
    "fastapi","mysql","postgresql","redis","git","etl","nlp","machine learning",
    "deep learning","机器学习","深度学习"
]

def extract_skills(text: str) -> list[str]:
    t = (text or "").lower()
    hits: set[str] = set()
    for s in SKILL_DICT:
        if s.lower() in t:
            hits.add(s)
    return sorted(hits)
