#!/usr/bin/env python3
"""测试 Web 应用功能"""
import sys

def test_imports():
    """测试所有模块导入"""
    try:
        from jobinsight.pipeline.build_dataset import load_jobs
        from jobinsight.webapp.app import app, build_charts
        from jobinsight.analytics.stats import city_top, tag_top
        from jobinsight.analytics.trends import trend_by_date
        print("[OK] 所有模块导入成功")
        return True
    except Exception as e:
        print(f"[ERROR] 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_load_data():
    """测试数据加载"""
    try:
        from jobinsight.pipeline.build_dataset import load_jobs
        df = load_jobs(30)
        print(f"[OK] 数据加载成功: {len(df)} 行")
        return True
    except Exception as e:
        print(f"[ERROR] 数据加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_build_charts():
    """测试图表生成"""
    try:
        from jobinsight.webapp.app import build_charts
        df = build_charts()
        print(f"[OK] 图表生成成功: {len(df)} 行数据")
        return True
    except Exception as e:
        print(f"[ERROR] 图表生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("测试 JobInsight Web 应用")
    print("=" * 50)
    
    results = []
    results.append(("模块导入", test_imports()))
    results.append(("数据加载", test_load_data()))
    results.append(("图表生成", test_build_charts()))
    
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {name}: {status}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n[SUCCESS] 所有测试通过！Web 应用可以正常启动。")
        sys.exit(0)
    else:
        print("\n[FAILED] 部分测试失败，请检查错误信息。")
        sys.exit(1)
