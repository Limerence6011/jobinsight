#!/usr/bin/env python3
"""
检查Dashboard可视化面板配置

快速验证：
1. 模板文件是否正确
2. Flask配置是否正确
3. API端点是否可用
"""

import sys
import io
from pathlib import Path

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent
parent_dir = project_root.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from jobinsight.settings import BASE_DIR
from jobinsight.webapp.app import app, template_dir

def check_dashboard_template():
    """检查dashboard模板"""
    print("=" * 60)
    print("检查Dashboard模板")
    print("=" * 60)
    
    template_path = template_dir / "dashboard.html"
    
    if not template_path.exists():
        print(f"[X] 模板文件不存在: {template_path}")
        return False
    
    print(f"[OK] 模板文件存在: {template_path}")
    
    # 读取文件内容检查
    content = template_path.read_text(encoding='utf-8')
    
    # 检查是否使用Chart.js
    has_chartjs = 'chart.js' in content.lower() or 'chart.umd' in content.lower()
    has_api_call = '/api/dashboard/data' in content
    
    print(f"  文件大小: {template_path.stat().st_size:,} 字节")
    print(f"  使用Chart.js: {'[OK]' if has_chartjs else '[X]'}")
    print(f"  调用API: {'[OK]' if has_api_call else '[X]'}")
    
    # 检查是否还有旧的iframe代码
    has_iframe = '<iframe' in content.lower()
    if has_iframe:
        print(f"  [WARNING] 模板中仍包含iframe标签（可能是旧代码）")
    
    return has_chartjs and has_api_call

def check_flask_config():
    """检查Flask配置"""
    print("\n" + "=" * 60)
    print("检查Flask配置")
    print("=" * 60)
    
    print(f"模板目录: {app.template_folder}")
    print(f"静态文件目录: {app.static_folder}")
    print(f"模板自动重载: {app.config.get('TEMPLATES_AUTO_RELOAD', '未设置')}")
    print(f"静态文件缓存: {app.config.get('SEND_FILE_MAX_AGE_DEFAULT', '未设置')}")
    
    # 检查路由
    dashboard_routes = [rule for rule in app.url_map.iter_rules() if 'dashboard' in rule.rule]
    print(f"\nDashboard相关路由:")
    for rule in dashboard_routes:
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"  {rule.rule} [{methods}]")
    
    return True

def test_api():
    """测试API端点"""
    print("\n" + "=" * 60)
    print("测试API端点")
    print("=" * 60)
    
    with app.test_client() as client:
        # 测试dashboard页面
        print("\n1. 测试Dashboard页面:")
        response = client.get('/dashboard')
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            content = response.data.decode('utf-8')
            has_chartjs = 'chart.js' in content.lower() or 'chart.umd' in content.lower()
            has_api = '/api/dashboard/data' in content
            print(f"   [OK] 页面加载成功")
            print(f"   包含Chart.js: {'[OK]' if has_chartjs else '[X]'}")
            print(f"   包含API调用: {'[OK]' if has_api else '[X]'}")
        else:
            print(f"   [X] 页面加载失败")
        
        # 测试API
        print("\n2. 测试Dashboard API:")
        response = client.get('/api/dashboard/data')
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            import json
            data = json.loads(response.data)
            print(f"   [OK] API响应成功")
            print(f"   有数据: {data.get('has_data', False)}")
            if data.get('has_data'):
                stats = data.get('stats', {})
                print(f"   总岗位数: {stats.get('total_jobs', 0)}")
        else:
            print(f"   [X] API响应失败")

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Dashboard可视化面板配置检查")
    print("=" * 60)
    print(f"项目根目录: {project_root}")
    print(f"BASE_DIR: {BASE_DIR}")
    print()
    
    # 检查模板
    template_ok = check_dashboard_template()
    
    # 检查Flask配置
    config_ok = check_flask_config()
    
    # 测试API
    test_api()
    
    # 总结
    print("\n" + "=" * 60)
    print("检查总结")
    print("=" * 60)
    
    if template_ok:
        print("[OK] Dashboard模板配置正确（使用Chart.js）")
    else:
        print("[X] Dashboard模板配置有问题")
    
    if config_ok:
        print("[OK] Flask配置正确")
    else:
        print("[X] Flask配置有问题")
    
    print("\n提示:")
    print("  1. 如果模板不是最新的，请重启Flask应用")
    print("  2. 确保浏览器没有缓存（Ctrl+F5强制刷新）")
    print("  3. 检查浏览器控制台是否有JavaScript错误")
    print("=" * 60)

if __name__ == "__main__":
    main()
