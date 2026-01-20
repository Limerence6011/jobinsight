#!/usr/bin/env python3
"""
JobInsight Web 应用启动脚本

功能：仅启动 Web 应用和定时任务调度器
注意：此脚本不进行环境检查或数据初始化
      如需完整启动（包含环境检查、数据初始化等），请使用 run.py

用法:
    python run_web.py [选项]

选项:
    --host HOST          Web 服务器主机地址（默认: 127.0.0.1）
    --port PORT          Web 服务器端口（默认: 5000）
    --no-scheduler      不启动定时任务调度器
    --debug             启用调试模式
"""
import argparse
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
# 项目根目录本身就是 jobinsight 包（因为有 __init__.py）
project_root = Path(__file__).resolve().parent
# 将父目录添加到路径，这样 from jobinsight.xxx 才能工作
parent_dir = project_root.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

def main():
    parser = argparse.ArgumentParser(
        description="JobInsight Web 应用启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
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
        "--no-scheduler",
        action="store_true",
        help="不启动定时任务调度器"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        default=True,
        help="启用调试模式（默认: True）"
    )
    
    args = parser.parse_args()
    
    from jobinsight.webapp.app import app
    
    # 启动定时任务调度器（如果需要）
    if not args.no_scheduler:
        from jobinsight.webapp.app import start_scheduler
        try:
            start_scheduler()
            print("[INFO] 定时任务调度器已启动")
        except Exception as e:
            print(f"[WARNING] 定时任务调度器启动失败: {e}")
    
    # 启动 Web 应用
    print(f"[INFO] 启动 Web 应用: http://{args.host}:{args.port}")
    try:
        app.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n[INFO] Web 应用已停止")
        sys.exit(0)

if __name__ == "__main__":
    main()

