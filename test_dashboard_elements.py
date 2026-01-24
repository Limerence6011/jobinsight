#!/usr/bin/env python3
"""
Dashboard页面元素检测和修复脚本

功能：
1. 访问dashboard页面
2. 检查关键元素（Chart.js、API调用等）
3. 与预期元素对比
4. 如果不一致，尝试修复或报告问题

用法:
    python test_dashboard_elements.py [--url URL] [--fix]
    
选项:
    --url URL     Web应用地址（默认: http://127.0.0.1:5000）
    --fix         自动修复问题（如果可能）
"""

import sys
import io
import argparse
from pathlib import Path
from bs4 import BeautifulSoup
import requests

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent
parent_dir = project_root.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from jobinsight.webapp.app import app, template_dir

# 预期的关键元素
EXPECTED_ELEMENTS = {
    'chart_js': {
        'type': 'script',
        'src_pattern': 'chart.js',
        'required': True,
        'description': 'Chart.js库'
    },
    'chartjs_plugin': {
        'type': 'script',
        'src_pattern': 'chartjs-plugin-datalabels',
        'required': True,
        'description': 'Chart.js数据标签插件'
    },
    'api_call': {
        'type': 'script_content',
        'pattern': '/api/dashboard/data',
        'required': True,
        'description': 'Dashboard API调用'
    },
    'stats_grid': {
        'type': 'element',
        'id': 'statsGrid',
        'required': True,
        'description': '统计卡片容器'
    },
    'city_chart_container': {
        'type': 'element',
        'id': 'cityChartContainer',
        'required': True,
        'description': '城市图表容器'
    },
    'trend_chart_container': {
        'type': 'element',
        'id': 'trendChartContainer',
        'required': True,
        'description': '趋势图表容器'
    },
    'tags_chart_container': {
        'type': 'element',
        'id': 'tagsChartContainer',
        'required': True,
        'description': '标签图表容器'
    },
    'load_dashboard_data': {
        'type': 'script_content',
        'pattern': 'loadDashboardData',
        'required': True,
        'description': '数据加载函数'
    }
}

def check_element(soup, element_config):
    """检查单个元素"""
    element_type = element_config['type']
    required = element_config.get('required', False)
    description = element_config.get('description', '')
    
    found = False
    details = {}
    
    if element_type == 'script':
        # 检查script标签
        src_pattern = element_config.get('src_pattern', '')
        scripts = soup.find_all('script', src=True)
        for script in scripts:
            src = script.get('src', '')
            if src_pattern.lower() in src.lower():
                found = True
                details = {
                    'tag': 'script',
                    'src': src,
                    'found_in': 'script src attribute'
                }
                break
    
    elif element_type == 'element':
        # 检查特定ID的元素
        element_id = element_config.get('id', '')
        element = soup.find(id=element_id)
        if element:
            found = True
            details = {
                'tag': element.name,
                'id': element_id,
                'found_in': f'element with id="{element_id}"'
            }
    
    elif element_type == 'script_content':
        # 检查script标签内容
        pattern = element_config.get('pattern', '')
        scripts = soup.find_all('script')
        for script in scripts:
            content = script.string or ''
            if pattern in content:
                found = True
                details = {
                    'tag': 'script',
                    'pattern': pattern,
                    'found_in': 'script content'
                }
                break
    
    return {
        'found': found,
        'required': required,
        'description': description,
        'details': details
    }

def analyze_dashboard_page(url='http://127.0.0.1:5000/dashboard'):
    """分析dashboard页面"""
    print("=" * 80)
    print("Dashboard页面元素检测")
    print("=" * 80)
    print(f"访问URL: {url}")
    print()
    
    try:
        # 获取页面内容
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        print(f"[OK] 页面访问成功")
        print(f"状态码: {response.status_code}")
        print(f"内容长度: {len(response.text):,} 字符")
        print()
        
        # 保存实际返回的HTML内容用于分析
        debug_html_path = project_root / "dashboard_actual_response.html"
        debug_html_path.write_text(response.text, encoding='utf-8')
        print(f"[INFO] 实际返回的HTML已保存到: {debug_html_path}")
        print(f"[INFO] HTML内容预览（前500字符）:")
        print(response.text[:500])
        print()
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 检查所有预期元素
        results = {}
        all_passed = True
        
        print("=" * 80)
        print("元素检查结果")
        print("=" * 80)
        
        for element_name, element_config in EXPECTED_ELEMENTS.items():
            result = check_element(soup, element_config)
            results[element_name] = result
            
            status = "[OK]" if result['found'] else "[X]"
            if result['required'] and not result['found']:
                all_passed = False
                status = "[FAIL]"
            
            print(f"{status} {element_config['description']}: {element_name}")
            if result['found']:
                print(f"     找到位置: {result['details'].get('found_in', 'N/A')}")
            else:
                print(f"     未找到")
            print()
        
        # 额外检查：是否有旧的iframe元素
        iframes = soup.find_all('iframe')
        has_old_iframe = len(iframes) > 0
        
        if has_old_iframe:
            print(f"[WARNING] 发现 {len(iframes)} 个iframe元素（可能是旧版本）")
            for iframe in iframes:
                src = iframe.get('src', '')
                print(f"   iframe src: {src}")
            print()
            all_passed = False
        
        # 检查页面标题
        title = soup.find('title')
        if title:
            title_text = title.string or ''
            print(f"页面标题: {title_text}")
            if 'JobInsight' not in title_text:
                print(f"[WARNING] 页面标题可能不正确")
        
        print()
        print("=" * 80)
        print("检测总结")
        print("=" * 80)
        
        if all_passed and not has_old_iframe:
            print("[SUCCESS] 所有关键元素检查通过！")
            print("Dashboard页面使用的是新版本（Chart.js）")
        else:
            print("[FAIL] 检测到问题：")
            for element_name, result in results.items():
                if result['required'] and not result['found']:
                    print(f"  - 缺少必需元素: {EXPECTED_ELEMENTS[element_name]['description']}")
            if has_old_iframe:
                print(f"  - 页面包含旧的iframe元素（可能是旧版本）")
        
        print()
        return {
            'success': all_passed and not has_old_iframe,
            'results': results,
            'has_old_iframe': has_old_iframe,
            'html_content': response.text,
            'soup': soup
        }
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 无法访问页面: {e}")
        print("请确保Web应用正在运行")
        return None
    except Exception as e:
        print(f"[ERROR] 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_template_file():
    """检查模板文件"""
    print("=" * 80)
    print("模板文件检查")
    print("=" * 80)
    
    template_path = template_dir / "dashboard.html"
    
    if not template_path.exists():
        print(f"[FAIL] 模板文件不存在: {template_path}")
        return None
    
    print(f"[OK] 模板文件存在: {template_path}")
    
    # 读取文件内容
    content = template_path.read_text(encoding='utf-8')
    print(f"文件大小: {len(content):,} 字符")
    
    # 检查关键元素
    has_chartjs = 'chart.js' in content.lower() or 'chart.umd' in content.lower()
    has_api = '/api/dashboard/data' in content
    has_iframe = '<iframe' in content.lower()
    
    print(f"包含Chart.js: {'[OK]' if has_chartjs else '[X]'}")
    print(f"包含API调用: {'[OK]' if has_api else '[X]'}")
    print(f"包含iframe: {'[WARNING] 可能是旧版本' if has_iframe else '[OK]'}")
    
    return {
        'path': template_path,
        'content': content,
        'has_chartjs': has_chartjs,
        'has_api': has_api,
        'has_iframe': has_iframe
    }

def fix_dashboard_function():
    """修复dashboard()函数，确保它直接返回文件内容"""
    app_py_path = project_root / "webapp" / "app.py"
    
    if not app_py_path.exists():
        print(f"[ERROR] 找不到 app.py: {app_py_path}")
        return False
    
    content = app_py_path.read_text(encoding='utf-8')
    
    # 检查dashboard函数是否已经使用直接文件读取
    if 'make_response(template_content)' in content and 'force_path' in content:
        print("[INFO] dashboard()函数已经使用直接文件读取方式")
        return True
    
    print("[INFO] 需要修复dashboard()函数")
    return False

def compare_and_fix(template_info, page_info, auto_fix=False):
    """对比模板文件和实际页面，必要时修复"""
    print()
    print("=" * 80)
    print("对比分析")
    print("=" * 80)
    
    if not template_info or not page_info:
        print("[ERROR] 无法进行对比，缺少必要信息")
        return False
    
    issues = []
    fixes_applied = []
    
    # 检查模板文件是否包含Chart.js
    if not template_info['has_chartjs']:
        issues.append({
            'type': 'template_missing_chartjs',
            'message': "模板文件不包含Chart.js",
            'severity': 'high'
        })
    
    # 检查页面是否包含Chart.js
    page_has_chartjs = page_info['results'].get('chart_js', {}).get('found', False)
    if not page_has_chartjs:
        issues.append({
            'type': 'page_missing_chartjs',
            'message': "页面不包含Chart.js",
            'severity': 'high'
        })
    
    # 检查是否有iframe（旧版本）
    if page_info['has_old_iframe']:
        issues.append({
            'type': 'page_has_iframe',
            'message': "页面包含旧的iframe元素（可能是旧版本）",
            'severity': 'medium'
        })
    
    # 检查API调用
    page_has_api = page_info['results'].get('api_call', {}).get('found', False)
    if not page_has_api:
        issues.append({
            'type': 'page_missing_api',
            'message': "页面不包含API调用",
            'severity': 'high'
        })
    
    # 检查内容长度差异
    template_size = len(template_info['content'])
    page_size = len(page_info['html_content'])
    size_diff = abs(template_size - page_size)
    size_diff_percent = (size_diff / template_size * 100) if template_size > 0 else 0
    
    if size_diff_percent > 10:  # 如果差异超过10%
        issues.append({
            'type': 'size_mismatch',
            'message': f"页面内容长度不匹配（模板: {template_size:,} 字符，实际: {page_size:,} 字符，差异: {size_diff_percent:.1f}%）",
            'severity': 'high'
        })
    
    if not issues:
        print("[OK] 模板文件和页面内容一致，都使用新版本")
        return True
    
    print("[WARNING] 发现不一致：")
    for issue in issues:
        severity_icon = "!!!" if issue['severity'] == 'high' else "!"
        print(f"  [{severity_icon}] {issue['message']}")
    
    if auto_fix:
        print()
        print("=" * 80)
        print("尝试修复")
        print("=" * 80)
        
        # 如果模板文件是正确的，但页面不正确，说明Flask没有加载最新模板
        if template_info['has_chartjs'] and not page_has_chartjs:
            print("[INFO] 模板文件是正确的，但页面不正确")
            print("[INFO] 可能的原因：")
            print("  1. Flask模板缓存未清除")
            print("  2. 浏览器缓存")
            print("  3. Flask配置问题")
            print("  4. dashboard()函数可能没有正确执行")
            print()
            print("[诊断] 检查dashboard()函数...")
            fix_dashboard_function()
            print()
            print("[建议] 请执行以下操作：")
            print("  1. 完全重启Flask应用（停止后重新启动，不要使用reloader）")
            print("  2. 清除浏览器缓存（Ctrl+F5 或 Cmd+Shift+R）")
            print("  3. 检查Flask的模板配置")
            print("  4. 确认dashboard()函数使用直接文件读取方式")
            print("  5. 查看控制台输出，确认dashboard()函数是否被调用")
        
        # 如果模板文件也不正确，需要修复模板文件
        if not template_info['has_chartjs']:
            print("[WARNING] 模板文件本身不正确，需要修复")
            print("[INFO] 模板文件应该包含Chart.js，但当前不包含")
            print("[INFO] 请检查 webapp/templates/dashboard.html 文件")
    
    # 生成修复建议
    print()
    print("=" * 80)
    print("修复建议")
    print("=" * 80)
    
    high_severity_issues = [i for i in issues if i['severity'] == 'high']
    if high_severity_issues:
        print("[重要] 发现严重问题，需要立即修复：")
        for issue in high_severity_issues:
            print(f"  - {issue['message']}")
        print()
        print("修复步骤：")
        print("  1. 确认 webapp/templates/dashboard.html 包含Chart.js")
        print("  2. 确认 webapp/app.py 的dashboard()函数使用直接文件读取")
        print("  3. 完全重启Flask应用（停止进程后重新启动）")
        print("  4. 清除浏览器缓存")
        print("  5. 查看 dashboard_actual_response.html 文件分析实际返回的内容")
    
    return len(issues) == 0

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Dashboard页面元素检测和修复')
    parser.add_argument('--url', type=str, default='http://127.0.0.1:5000/dashboard',
                       help='Web应用地址（默认: http://127.0.0.1:5000/dashboard）')
    parser.add_argument('--fix', action='store_true',
                       help='自动修复问题（如果可能）')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 80)
    print("Dashboard页面元素检测和修复工具")
    print("=" * 80)
    print(f"项目根目录: {project_root}")
    print()
    
    # 1. 检查模板文件
    template_info = check_template_file()
    
    # 2. 分析实际页面
    page_info = analyze_dashboard_page(args.url)
    
    # 3. 对比和修复
    if template_info and page_info:
        compare_and_fix(template_info, page_info, auto_fix=args.fix)
    
    print()
    print("=" * 80)
    print("检测完成")
    print("=" * 80)
    
    if page_info and page_info['success']:
        print("[SUCCESS] Dashboard页面配置正确")
        return 0
    else:
        print("[FAIL] Dashboard页面存在问题，请查看上述详细信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())
