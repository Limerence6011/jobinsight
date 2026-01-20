from __future__ import annotations
import json
import datetime as dt
from sqlalchemy import create_engine
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
