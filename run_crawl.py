import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
# 项目根目录本身就是 jobinsight 包（因为有 __init__.py）
project_root = Path(__file__).resolve().parent
# 将父目录添加到路径，这样 from jobinsight.xxx 才能工作
parent_dir = project_root.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from jobinsight.crawler.run_crawl import main

if __name__ == "__main__":
    main()
