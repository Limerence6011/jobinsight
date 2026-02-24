from __future__ import annotations
import json
import datetime as dt
from typing import Set, Tuple
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from ..settings import get_db_url
from .models import Base, Job
from ..crawler.base import JobPost
from ..utils.salary import parse_salary
from ..utils.normalize import normalize_city, normalize_edu, normalize_exp

# 创建 MySQL 引擎
ENGINE = create_engine(get_db_url(), echo=False, pool_pre_ping=True, pool_recycle=3600)

# 创建表（如果不存在）
Base.metadata.create_all(ENGINE)

def ensure_schema_compatibility() -> None:
    """
    Apply lightweight schema compatibility fixes for existing deployments.
    """
    with ENGINE.begin() as conn:
        inspector = inspect(conn)
        table_names = set(inspector.get_table_names())
        if "users" in table_names:
            user_columns = {col["name"] for col in inspector.get_columns("users")}
            if "is_admin" not in user_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"))

ensure_schema_compatibility()

def get_existing_job_keys(platform: str = None, keyword: str = None, city: str = None, limit: int = 1000) -> Set[Tuple[str, str]]:
    """
    查询数据库中现有的job数据，返回 (platform, job_id) 的集合
    
    Args:
        platform: 平台名称（可选，如果为None则查询所有平台）
        keyword: 关键词（可选，用于过滤title）
        city: 城市（可选，用于过滤）
        limit: 最多返回的记录数（如果为None则不限制）
    
    Returns:
        Set[Tuple[str, str]]: (platform, job_id) 的集合
    """
    with Session(ENGINE) as sess:
        query = sess.query(Job)
        
        # 如果提供了平台，过滤平台
        if platform:
            query = query.filter(Job.platform == platform)
        
        # 如果提供了关键词，在title中搜索
        if keyword:
            keyword_lower = keyword.lower()
            query = query.filter(Job.title.ilike(f"%{keyword_lower}%"))
        
        # 如果提供了城市，过滤城市
        if city:
            city_normalized = normalize_city(city)
            query = query.filter(Job.city == city_normalized)
        
        # 如果提供了limit，限制返回数量
        if limit:
            jobs = query.limit(limit).all()
        else:
            jobs = query.all()
        
        # 返回 (platform, job_id) 的集合
        return {(job.platform, job.job_id) for job in jobs}

def get_all_existing_job_keys() -> Set[Tuple[str, str]]:
    """
    查询数据库中所有现有的job数据，返回 (platform, job_id) 的集合
    
    Returns:
        Set[Tuple[str, str]]: (platform, job_id) 的集合
    """
    return get_existing_job_keys(platform=None, keyword=None, city=None, limit=None)

def upsert_jobs(posts: list[JobPost]) -> None:
    today = dt.date.today().isoformat()
    with Session(ENGINE) as sess:
        for p in posts:
            smin, smax, savg, unit_note = parse_salary(p.salary_raw)
            obj = Job(
                platform=p.platform,
                job_id=p.job_id,
                title=p.title[:256],
                company=p.company[:256],
                city=normalize_city(p.city)[:128],
                salary_raw=(p.salary_raw or "")[:128],
                salary_min=smin,
                salary_max=smax,
                salary_avg=savg,
                salary_unit_note=unit_note,
                education=normalize_edu(p.education_raw),
                exp=normalize_exp(p.exp_raw),
                tags=json.dumps(p.tags, ensure_ascii=False),
                detail_url=p.detail_url,
                description=p.description,
                crawl_date=today,
            )
            sess.merge(obj)
        sess.commit()
