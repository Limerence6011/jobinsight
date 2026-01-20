from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Any, Iterator

@dataclass
class JobPost:
    """
    统一职位数据模型
    (原名 Job，为了兼容 storage/db.py 重命名为 JobPost)
    """
    platform: str          # 平台名称 (如: job51, zhilian)
    job_id: str           # 职位ID (去重用)
    title: str            # 职位名称
    company: str          # 公司名称
    city: str             # 城市
    salary_raw: str       # 原始薪资文本
    detail_url: str       # 详情页链接
    
    # 以下为可选字段，设置默认值以防报错
    district: Optional[str] = None        # 行政区
    salary_min: Optional[float] = None    # 最低薪资(清洗后)
    salary_max: Optional[float] = None    # 最高薪资(清洗后)
    experience: Optional[str] = None      # 经验要求
    education: Optional[str] = None       # 学历要求
    tags: List[str] = field(default_factory=list)  # 福利标签
    pub_date: Optional[str] = None        # 发布时间
    raw_data: Optional[str] = None        # 原始数据(调试用)

# 【关键】添加别名，让 import Job 和 import JobPost 都能正常工作
Job = JobPost

class BaseAdapter(ABC):
    """
    爬虫适配器抽象基类
    """
    
    def __init__(self, client=None):
        self.client = client

    @abstractmethod
    def fetch(self, keyword: str, city: str = None, page: int = 1, **kwargs) -> Any:
        """
        获取数据
        :return: 返回 HTML 源码或 JSON 数据
        """
        pass

    @abstractmethod
    def parse(self, content: Any) -> Iterator[JobPost]:
        """
        解析数据
        :return: 返回 JobPost 对象的生成器
        """
        pass
