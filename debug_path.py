import sys
import os
from pathlib import Path

# 1. 模拟 run.py 的路径插入逻辑
project_root = Path(__file__).resolve().parent
parent_dir = project_root.parent

if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def inspect_environment():
    print(f"{'='*20} ENVIRONMENT DIAGNOSIS {'='*20}")
    print(f"Project Root: {project_root}")
    
    try:
        # 尝试导入 settings 以获取 BASE_DIR
        # 注意：这里假设 jobinsight 是包名
        from jobinsight.settings import BASE_DIR
        print(f"Imported BASE_DIR: {BASE_DIR}")
        
        # 2. 验证 Flask 将使用的模板路径
        expected_template_dir = BASE_DIR / "webapp" / "templates"
        target_html = expected_template_dir / "dashboard.html"
        
        print(f"Flask Template Dir: {expected_template_dir}")
        print(f"Target HTML Path:   {target_html}")
        
        # 3. 检查文件是否存在及内容预览
        if target_html.exists():
            print(f"[OK] File exists.")
            content = target_html.read_text(encoding='utf-8')
            print(f"{'-'*20} FILE CONTENT PREVIEW (First 200 chars) {'-'*20}")
            print(content[:2000])
            print(f"{'-'*20}")
            
            # 检查是否有你特有的修改标记
            print("Check above: Is this your modified content?")
        else:
            print(f"[ERROR] File NOT found at: {target_html}")
            print("Please check if 'config.yaml' or settings.py overrides BASE_DIR.")

    except ImportError as e:
        print(f"[CRITICAL] Import failed: {e}")
        print("Structure seems incorrect. Ensure 'jobinsight' package exists in root.")
        print(f"Current sys.path: {sys.path}")

if __name__ == "__main__":
    inspect_environment()