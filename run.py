#!/usr/bin/env python3
"""JobInsight 一键启动脚本。"""
import argparse
import sys
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, make_server

# 确保可以导入 `jobinsight.*`
project_root = Path(__file__).resolve().parent
parent_dir = project_root.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def check_environment() -> bool:
    print("=" * 50)
    print("检查运行环境...")
    print("=" * 50)

    issues = []
    if sys.version_info < (3, 7):
        issues.append("需要 Python 3.7 及以上版本。")
    else:
        print(f"[成功] Python 版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    required_modules = ["flask", "pandas", "sqlalchemy", "pymysql", "requests", "pyecharts", "sklearn", "yaml"]
    for module in required_modules:
        try:
            __import__(module)
            print(f"[成功] 已安装模块: {module}")
        except ImportError:
            issues.append(f"缺少依赖模块: {module}")

    config_path = Path("config.yaml")
    if config_path.exists():
        print(f"[成功] 找到配置文件: {config_path}")
    else:
        issues.append("缺少配置文件 config.yaml")

    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"[成功] 数据目录: {data_dir}")

    if issues:
        print("\n[错误] 运行环境检查失败：")
        for item in issues:
            print(f"  - {item}")
        return False

    print("\n[成功] 运行环境检查通过。")
    return True


def initialize_database() -> bool:
    print("\n" + "=" * 50)
    print("检查数据库连接...")
    print("=" * 50)
    try:
        from sqlalchemy import text
        from jobinsight.storage.db import ENGINE
        from jobinsight.storage.models import Base

        with ENGINE.connect():
            print("[成功] 数据库连接正常")

        Base.metadata.create_all(ENGINE)
        print("[成功] 数据表检查完成")

        with ENGINE.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM jobs")).scalar()
            print(f"[信息] 当前岗位数据量: {count}")
        return True
    except Exception as e:
        print(f"[错误] 数据库初始化失败: {e}")
        return False


def crawl_initial_data() -> bool:
    print("\n" + "=" * 50)
    print("执行初始化采集...")
    print("=" * 50)
    try:
        from jobinsight.settings import load_config
        from jobinsight.crawler.run_crawl import crawl_once, print_crawl_summary

        cfg = load_config()
        default_keyword = cfg.get("crawler", {}).get("default_keyword", "python")
        result = crawl_once(keyword=default_keyword, city=None, pages=1)
        print_crawl_summary(result)
        return bool(result.get("success", False))
    except Exception as e:
        print(f"[警告] 初始化采集失败: {e}")
        return False


def start_web_app(host: str = "127.0.0.1", port: int = 5000, debug: bool = False, with_scheduler: bool = True) -> None:
    print("\n" + "=" * 50)
    print("启动 Web 应用...")
    print("=" * 50)

    from jobinsight.webapp.app import app

    if with_scheduler:
        from jobinsight.webapp.app import start_scheduler

        print("[信息] 启动定时采集任务...")
        start_scheduler()
        print("[成功] 定时采集已启动（每天 09:00）")

    print("=" * 50)
    print(f"访问地址: http://{host}:{port}")
    print(f"调试模式: {'开启' if debug else '关闭'}")
    print(f"定时采集: {'开启' if with_scheduler else '关闭'}")
    print("按 Ctrl+C 停止运行")
    print("=" * 50)

    if debug:
        print("[信息] 调试模式使用 Flask 开发服务器")
        app.run(host=host, port=port, debug=True, use_reloader=True)
        return

    class ChineseRequestHandler(WSGIRequestHandler):
        def log_message(self, format, *args):
            message = format % args
            print(f"[访问] {self.address_string()} - {message}")

    server = make_server(host, port, app, handler_class=ChineseRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[信息] 服务已停止")
    finally:
        server.server_close()


def main() -> None:
    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        print("用法: python run.py [选项]")
        print("")
        print("选项:")
        print("  --crawl-first   启动 Web 前先执行一次采集")
        print("  --no-scheduler  启动时不启用定时采集")
        print("  --host HOST     Web 服务监听地址（默认: 127.0.0.1）")
        print("  --port PORT     Web 服务监听端口（默认: 5000）")
        print("  --debug         启用 Flask 调试模式")
        print("  -h, --help      显示帮助信息并退出")
        return

    parser = argparse.ArgumentParser(description="JobInsight 一键启动", add_help=False)
    parser.add_argument("--crawl-first", action="store_true", help="启动 Web 前先执行一次采集")
    parser.add_argument("--no-scheduler", action="store_true", help="启动时不启用定时采集")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Web 服务监听地址")
    parser.add_argument("--port", type=int, default=5000, help="Web 服务监听端口")
    parser.add_argument("--debug", action="store_true", help="启用 Flask 调试模式")
    args = parser.parse_args()

    if not check_environment():
        sys.exit(1)
    if not initialize_database():
        sys.exit(1)
    if args.crawl_first:
        crawl_initial_data()
    start_web_app(
        host=args.host,
        port=args.port,
        debug=args.debug,
        with_scheduler=not args.no_scheduler,
    )


if __name__ == "__main__":
    main()
