from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Optional, List
try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol
import datetime as dt

@dataclass
class JobPost:
    platform: str
    job_id: str
    title: str
    company: str
    city: str
    salary_raw: str
    education_raw: str
    exp_raw: str
    tags: List[str]
    detail_url: str
    description: str
    crawl_time: str  # ISO8601

class JobAdapter(Protocol):
    platform: str
    def fetch(self, keyword: str, city: Optional[str], page: int) -> str: ...
    def parse(self, payload: str) -> Iterable[JobPost]: ...

def now_iso() -> str:
    return dt.datetime.now().replace(microsecond=0).isoformat()
