from __future__ import annotations
from pathlib import Path

def render_chart(chart, out_html: str) -> str:
    p = Path(out_html)
    p.parent.mkdir(parents=True, exist_ok=True)
    chart.render(str(p))
    return str(p)
