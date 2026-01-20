from __future__ import annotations
import re
from typing import Optional, Tuple

def parse_salary(text: str) -> tuple[Optional[int], Optional[int], Optional[int], str]:
    """
    Parse salary text into monthly RMB (demo-friendly).
    Returns (min, max, avg, unit_note).
    unit_note is for audit/debug (e.g., 'monthly_rmb', 'annual_usd', 'unknown').
    """
    if not text:
        return None, None, None, "unknown"

    t = text.replace(" ", "").lower()

    # Generic patterns: 15-25k, 1.5-2万
    m = re.search(r"(\d+(?:\.\d+)?)[-~](\d+(?:\.\d+)?)(k|万)", t)
    if m:
        a, b, unit = float(m.group(1)), float(m.group(2)), m.group(3)
        mul = 1000 if unit == "k" else 10000
        smin, smax = int(a * mul), int(b * mul)
        return smin, smax, int((smin + smax) / 2), "monthly_rmb"

    m2 = re.search(r"(\d+(?:\.\d+)?)(k|万)", t)
    if m2:
        v, unit = float(m2.group(1)), m2.group(2)
        mul = 1000 if unit == "k" else 10000
        avg = int(v * mul)
        return avg, avg, avg, "monthly_rmb"

    # USD/year like $60000/year - use rough conversion to RMB/month for visualization (configurable in future)
    m3 = re.search(r"\$\s*(\d{2,6})(?:[-~](\d{2,6}))?/year", t)
    if m3:
        a = int(m3.group(1))
        b = int(m3.group(2)) if m3.group(2) else a
        # rough: 1 USD ≈ 7.0 RMB, annual -> monthly
        smin = int(a * 7.0 / 12)
        smax = int(b * 7.0 / 12)
        return smin, smax, int((smin + smax) / 2), "annual_usd_to_rmb_month"

    return None, None, None, "unknown"
