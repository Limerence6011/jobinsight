from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Any, Iterator
from datetime import datetime

# 【修复点 1】把丢失的工具函数加回来
def now_iso() -> str:
    """获取当前时间的 ISO 格式字符串"""
    return datetime.now().isoformat()

@dataclass
class JobPost:
    """
    统一职位数据模型
    """
    platform: str          # 平台名称
    job_id: str           # 职位ID
    title: str            # 职位名称
    company: str          # 公司名称
    city: str             # 城市
    salary_raw: str       # 原始薪资文本
    detail_url: str       # 详情页链接
    
    # 可选字段
    district: Optional[str] = None        # 行政区
    salary_min: Optional[float] = None    # 最低薪资
    salary_max: Optional[float] = None    # 最高薪资
    experience: Optional[str] = None      # 经验
    education: Optional[str] = None       # 学历
    tags: List[str] = field(default_factory=list)
    pub_date: Optional[str] = None
    raw_data: Optional[str] = None

    # 兼容性字段 (适配 db.py 和 51job 爬虫)
    education_raw: Optional[str] = None   
    exp_raw: Optional[str] = None         
    description: Optional[str] = None     

# 别名兼容
Job = JobPost

class BaseAdapter(ABC):
    def __init__(self, client=None):
        self.client = client

    @abstractmethod
    def fetch(self, keyword: str, city: str = None, page: int = 1, **kwargs) -> Any:
        pass

    @abstractmethod
    def parse(self, content: Any) -> Iterator[JobPost]:
        pass