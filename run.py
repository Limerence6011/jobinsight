#!/usr/bin/env python3
"""
JobInsight 项目一键启动脚本

功能：
- 检查项目环境和依赖
- 初始化数据库（如果需要）
- 可选：执行初始数据采集
- 启动 Web 应用和定时任务调度器

用法:
    python run.py [选项]

选项:
    --crawl-first        启动前先执行一次数据采集
    --no-scheduler       不启动定时任务调度器
    --host HOST          Web 服务器主机地址（默认: 127.0.0.1）
    --port PORT          Web 服务器端口（默认: 5000）
    --debug              启用调试模式
    --help               显示帮助信息
"""
import argparse
import sys
import os
from pathlib import Path

def check_environment():
    """检查项目环境"""
    print("=" * 50)
    print("检查项目环境...")
    print("=" * 50)
    
    issues = []
    
    # 检查 Python 版本
    if sys.version_info < (3, 7):
        issues.append(f"Python 版本过低: {sys.version_info.major}.{sys.version_info.minor} (需要 3.7+)")
    else:
        print(f"[OK] Python 版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # 检查必要的模块
    required_modules = [
        'flask', 'pandas', 'sqlalchemy', 'pymysql', 'requests', 
        'pyecharts', 'sklearn', 'yaml'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"[OK] 模块 {module} 已安装")
        except ImportError:
            missing_modules.append(module)
            issues.append(f"缺少模块: {module}")
    
    # 检查配置文件
    config_path = Path("config.yaml")
    if config_path.exists():
        print(f"[OK] 配置文件存在: {config_path}")
    else:
        issues.append(f"配置文件不存在: {config_path}")
    
    # 检查数据目录（用于存储处理后的 CSV 文件等）
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] 创建数据目录: {data_dir}")
    else:
        print(f"[OK] 数据目录存在: {data_dir}")
    
    # 检查数据库配置
    from jobinsight.settings import load_config
    cfg = load_config()
    db_cfg = cfg.get("database", {})
    if not db_cfg:
        issues.append("请在 config.yaml 中配置 database 信息")
    else:
        print(f"[OK] 数据库配置已设置: {db_cfg.get('database', 'N/A')}")
    
    if issues:
        print("\n[ERROR] 发现以下问题:")
        for issue in issues:
            print(f"  - {issue}")
        print("\n请先解决这些问题再启动项目。")
        return False
    
    print("\n[SUCCESS] 环境检查通过！")
    return True

def initialize_database():
    """初始化数据库（如果需要）"""
    print("\n" + "=" * 50)
    print("检查数据库...")
    print("=" * 50)
    
    try:
        from jobinsight.settings import load_config
        from jobinsight.storage.db import ENGINE, Base
        from jobinsight.storage.models import Job
        
        # 检查数据库配置
        cfg = load_config()
        db_cfg = cfg.get("database", {})
        if not db_cfg:
            print("[ERROR] 请在 config.yaml 中配置 database 信息")
            return False
        
        # 测试数据库连接
        try:
            with ENGINE.connect() as conn:
                print("[OK] MySQL 数据库连接成功")
        except Exception as e:
            print(f"[ERROR] 无法连接到 MySQL 数据库: {e}")
            print("请检查:")
            print("  1. MySQL 服务是否启动")
            print("  2. config.yaml 中的数据库配置是否正确")
            print("  3. 数据库是否存在（不存在请先创建）")
            return False
        
        # 创建表（如果不存在）
        Base.metadata.create_all(ENGINE)
        print("[OK] 数据库表已就绪")
        
        # 检查是否有数据
        with ENGINE.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT COUNT(*) FROM jobs"))
            count = result.scalar()
            print(f"[INFO] 数据库中有 {count} 条岗位数据")
            
        return True
    except Exception as e:
        print(f"[ERROR] 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def crawl_initial_data():
    """执行初始数据采集"""
    print("\n" + "=" * 50)
    print("执行初始数据采集...")
    print("=" * 50)
    
    try:
        from jobinsight.settings import load_config
        from jobinsight.crawler.run_crawl import crawl_once
        
        cfg = load_config()
        default_keyword = cfg.get("crawler", {}).get("default_keyword", "python")
        
        print(f"正在采集关键词: {default_keyword}")
        from jobinsight.crawler.run_crawl import print_crawl_summary
        result = crawl_once(keyword=default_keyword, city=None, pages=1)
        if result.get("success"):
            print_crawl_summary(result)
        return result.get("success", False)
    except Exception as e:
        print(f"[WARNING] 数据采集失败: {e}")
        print("您可以稍后通过 Web 界面或 run_crawl.py 手动采集数据")
        return False

def start_web_app(host="127.0.0.1", port=5000, debug=False, with_scheduler=True):
    """启动 Web 应用"""
    print("\n" + "=" * 50)
    print("启动 Web 应用...")
    print("=" * 50)
    
    try:
        from jobinsight.webapp.app import app
        
        if with_scheduler:
            from jobinsight.webapp.app import start_scheduler
            print("[INFO] 启动定时任务调度器...")
            start_scheduler()
            print("[OK] 定时任务调度器已启动（每天 09:00 自动采集）")
        
        print(f"\n{'=' * 50}")
        print("Web 应用已启动！")
        print(f"{'=' * 50}")
        print(f"访问地址: http://{host}:{port}")
        print(f"调试模式: {'开启' if debug else '关闭'}")
        print(f"定时任务: {'已启动' if with_scheduler else '未启动'}")
        print(f"\n按 Ctrl+C 停止服务器")
        print(f"{'=' * 50}\n")
        
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n\n[INFO] 服务器已停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] 启动 Web 应用失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="JobInsight 项目一键启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--crawl-first",
        action="store_true",
        help="启动前先执行一次数据采集"
    )
    
    parser.add_argument(
        "--no-scheduler",
        action="store_true",
        help="不启动定时任务调度器"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Web 服务器主机地址（默认: 127.0.0.1）"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Web 服务器端口（默认: 5000）"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )
    
    args = parser.parse_args()
    
    # 1. 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 2. 初始化数据库
    if not initialize_database():
        sys.exit(1)
    
    # 3. 可选：执行初始数据采集
    if args.crawl_first:
        crawl_initial_data()
    
    # 4. 启动 Web 应用
    start_web_app(
        host=args.host,
        port=args.port,
        debug=args.debug,
        with_scheduler=not args.no_scheduler
    )

if __name__ == "__main__":
    main()
