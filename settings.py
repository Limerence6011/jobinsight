from __future__ import annotations
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CONFIG_PATH = BASE_DIR / "config.yaml"

def load_config() -> dict:
    if CONFIG_PATH.exists():
        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}

def get_db_url() -> str:
    """获取数据库连接 URL"""
    cfg = load_config()
    db_cfg = cfg.get("database", {})
    
    host = db_cfg.get("host", "localhost")
    port = db_cfg.get("port", 3306)
    user = db_cfg.get("user", "root")
    password = db_cfg.get("password", "")
    database = db_cfg.get("database", "jobinsight")
    charset = db_cfg.get("charset", "utf8mb4")
    
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset={charset}"
