from __future__ import annotations
import pandas as pd
from sqlalchemy import text
from ..storage.db import ENGINE

def load_jobs(days: int = 30) -> pd.DataFrame:
    # 使用 MySQL 日期函数（DATE_SUB）
    sql = text(f"""
      SELECT * FROM jobs
      WHERE DATE(crawl_date) >= DATE_SUB(CURDATE(), INTERVAL {days} DAY)
    """)
    try:
        with ENGINE.connect() as conn:
            result = conn.execute(sql)
            rows = result.fetchall()
            columns = result.keys()
            return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        from ..utils.log import get_logger
        logger = get_logger(__name__)
        logger.error(f"加载数据失败: {e}")
        # 返回空的 DataFrame，避免应用崩溃
        return pd.DataFrame()

def to_processed_csv(days: int = 30, out_path: str = "data/processed/jobs_last30d.csv") -> str:
    df = load_jobs(days=days)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    return out_path
