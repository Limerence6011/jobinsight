#!/usr/bin/env python3
"""
MySQL 数据库初始化脚本

功能：创建数据库和表结构

用法:
    python init_database.py
"""
import sys
from jobinsight.settings import load_config, get_db_url
from sqlalchemy import create_engine, text

def create_database_if_not_exists():
    """创建数据库（如果不存在）"""
    cfg = load_config()
    db_cfg = cfg.get("database", {})
    
    if not db_cfg:
        print("[ERROR] 请在 config.yaml 中配置 database 信息")
        sys.exit(1)
    
    host = db_cfg.get("host", "localhost")
    port = db_cfg.get("port", 3306)
    user = db_cfg.get("user", "root")
    password = db_cfg.get("password", "")
    database = db_cfg.get("database", "jobinsight")
    
    # 连接到 MySQL 服务器（不指定数据库）
    server_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/"
    
    try:
        print(f"正在连接到 MySQL 服务器 {host}:{port}...")
        engine = create_engine(server_url, echo=False)
        
        with engine.connect() as conn:
            # 检查数据库是否存在
            result = conn.execute(text(f"SHOW DATABASES LIKE '{database}'"))
            exists = result.fetchone() is not None
            
            if exists:
                print(f"[INFO] 数据库 '{database}' 已存在")
            else:
                # 创建数据库（需要使用 begin() 事务上下文）
                print(f"正在创建数据库 '{database}'...")
                with conn.begin():
                    conn.execute(text(f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                print(f"[OK] 数据库 '{database}' 创建成功")
        
        return True
    except Exception as e:
        print(f"[ERROR] 创建数据库失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_tables():
    """创建表结构"""
    try:
        from jobinsight.storage.db import ENGINE, Base
        
        print("正在创建表结构...")
        Base.metadata.create_all(ENGINE)
        print("[OK] 表结构创建成功")
        return True
    except Exception as e:
        print(f"[ERROR] 创建表结构失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 50)
    print("MySQL 数据库初始化")
    print("=" * 50)
    
    # 1. 创建数据库
    if not create_database_if_not_exists():
        sys.exit(1)
    
    # 2. 创建表结构
    if not create_tables():
        sys.exit(1)
    
    print("\n[SUCCESS] 数据库初始化完成！")
    print("\n下一步:")
    print("  1. 确认 config.yaml 中的数据库配置正确")
    print("  2. 运行 python run.py 启动项目")

if __name__ == "__main__":
    main()
