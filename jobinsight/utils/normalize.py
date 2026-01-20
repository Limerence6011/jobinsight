from __future__ import annotations
import re

def normalize_city(raw: str) -> str:
    r = (raw or "").strip()
    return r if r else "Unknown"

def normalize_edu(raw: str) -> str:
    r = (raw or "").strip()
    if any(k in r for k in ["博士"]): return "PhD"
    if any(k in r for k in ["硕士", "研究生"]): return "Master"
    if any(k in r for k in ["本科"]): return "Bachelor"
    if any(k in r for k in ["大专", "专科"]): return "College"
    if any(k in r for k in ["高中", "中专"]): return "HighSchool"
    return "Unknown"

def normalize_exp(raw: str) -> str:
    r = (raw or "").strip()
    if any(k in r for k in ["不限", "应届", "无经验"]): return "0"
    m = re.search(r"(\d+)\s*年", r)
    if m: return m.group(1)
    # English like '3+ years'
    m2 = re.search(r"(\d+)\s*\+?\s*years?", r.lower())
    if m2: return m2.group(1)
    return "Unknown"
