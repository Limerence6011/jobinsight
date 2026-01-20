# Placeholder adapter for BOSS直聘 (implement with authorization / allowed endpoints)

from __future__ import annotations
from typing import Iterable, Optional
from ...base import JobPost
from ....utils.http import HttpClient
from ....utils.log import get_logger

logger = get_logger(__name__)

class BossAdapter:
    """
    BOSS直聘平台适配器
    
    NOTE: 需要授权和合规处理
    """
    platform = "boss"
    
    def __init__(self, client: Optional[HttpClient] = None):
        self.client = client or HttpClient()
    
    def fetch(self, keyword: str, city: Optional[str], page: int) -> str:
        # TODO: 实现 BOSS直聘数据获取逻辑
        raise NotImplementedError("BOSS直聘适配器待实现")
    
    def parse(self, payload: str) -> Iterable[JobPost]:
        # TODO: 实现 BOSS直聘数据解析逻辑
        raise NotImplementedError("BOSS直聘适配器待实现")
