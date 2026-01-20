#!/usr/bin/env python3
"""测试推荐功能"""
import pandas as pd
from jobinsight.analytics.recommend import recommend, UserQuery

def test_recommend():
    """测试推荐功能"""
    # 创建测试数据
    df = pd.DataFrame({
        'title': ['Python Developer', 'Data Scientist', 'Backend Engineer'],
        'company': ['Company A', 'Company B', 'Company C'],
        'city': ['Beijing', 'Shanghai', 'Beijing'],
        'salary_raw': ['15000', '20000', '18000'],
        'salary_avg': [15000, 20000, 18000],
        'detail_url': ['http://test1.com', 'http://test2.com', 'http://test3.com'],
        'education': ['Bachelor', 'Master', 'Bachelor'],
        'exp': ['2', '3', '1'],
        'description': ['Python Django Flask', 'Python ML Data Science', 'Python FastAPI']
    })
    
    # 测试1: 正常推荐
    print("测试1: 正常推荐")
    q1 = UserQuery(
        city=None,
        min_salary=None,
        education=None,
        max_exp_years=None,
        skills_text='python',
        keyword=None
    )
    result1 = recommend(df, q1, topk=5)
    print(f"  结果数量: {len(result1)}")
    print(f"  列: {result1.columns.tolist()}")
    print(f"  包含 score: {'score' in result1.columns}")
    if len(result1) > 0:
        print(f"  第一个结果的 score: {result1.iloc[0].get('score', 'N/A')}")
    
    # 测试2: 筛选后为空
    print("\n测试2: 筛选后为空")
    q2 = UserQuery(
        city='NewYork',
        min_salary=None,
        education=None,
        max_exp_years=None,
        skills_text='python',
        keyword=None
    )
    result2 = recommend(df, q2, topk=5)
    print(f"  结果数量: {len(result2)}")
    print(f"  列: {result2.columns.tolist()}")
    print(f"  包含 score: {'score' in result2.columns}")
    
    # 测试3: 带筛选条件
    print("\n测试3: 带筛选条件")
    q3 = UserQuery(
        city='Beijing',
        min_salary=16000,
        education=None,
        max_exp_years=3,
        skills_text='python',
        keyword=None
    )
    result3 = recommend(df, q3, topk=5)
    print(f"  结果数量: {len(result3)}")
    print(f"  列: {result3.columns.tolist()}")
    print(f"  包含 score: {'score' in result3.columns}")
    
    print("\n[SUCCESS] 所有测试完成")

if __name__ == "__main__":
    test_recommend()
