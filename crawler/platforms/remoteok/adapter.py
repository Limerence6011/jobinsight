from __future__ import annotations
import json
from typing import Iterable, Optional, List
from ...base import JobPost, now_iso
from ....utils.http import HttpClient
from ....utils.log import get_logger

logger = get_logger(__name__)

class RemoteOKApiAdapter:
    """
    RemoteOK JSON API adapter.
    Data source: https://remoteok.com/api (public feed).
    NOTE: RemoteOK requests attribution and a direct link back to the listing URL.
    """
    platform = "remoteok"

    def __init__(self, client: Optional[HttpClient] = None):
        self.client = client or HttpClient()

    def fetch(self, keyword: str, city: Optional[str], page: int) -> str:
        # RemoteOK feed returns all recent jobs; we filter in parse().
        url = "https://remoteok.com/api"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        }
        return self.client.get(url, headers=headers).text

    def parse(self, payload: str) -> Iterable[JobPost]:
        data = json.loads(payload)
        if not isinstance(data, list):
            return []
        # first record may be metadata
        for obj in data:
            if not isinstance(obj, dict):
                continue
            if "id" not in obj or "position" not in obj:
                continue

            job_id = str(obj.get("id"))
            title = str(obj.get("position", "")).strip()
            company = str(obj.get("company", "")).strip()
            location = str(obj.get("location", "")).strip() or "Remote"
            tags = obj.get("tags") or []
            if not isinstance(tags, list):
                tags = []
            tags = [str(t) for t in tags][:20]

            # Salary fields vary; we store raw text if present
            salary_raw = str(obj.get("salary") or obj.get("salary_min") or "")
            url = str(obj.get("url") or obj.get("apply_url") or "")
            desc = str(obj.get("description") or "")

            yield JobPost(
                platform=self.platform,
                job_id=job_id,
                title=title,
                company=company,
                city=location,
                salary_raw=salary_raw,
                education_raw="",
                exp_raw="",
                tags=tags,
                detail_url=url,
                description=desc,
                crawl_time=now_iso(),
            )
