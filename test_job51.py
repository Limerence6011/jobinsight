#!/usr/bin/env python3
"""
51job爬虫独立测试脚本

用法:
    python test_job51.py --keyword Python --city 上海 --pages 1
    python test_job51.py --keyword Python --pages 2
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent
parent_dir = project_root.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from jobinsight.settings import load_config
from jobinsight.utils.http import HttpClient
from jobinsight.utils.log import get_logger
from jobinsight.crawler.platforms.job51.adapter import Job51Adapter
from jobinsight.storage.db import upsert_jobs

logger = get_logger(__name__)

def test_job51_crawler(keyword: str, city: str = None, pages: int = 1):
    """测试51job爬虫功能"""
    print("=" * 70)
    print("51job爬虫测试")
    print("=" * 70)
    print(f"关键词: {keyword}")
    print(f"城市: {city or '全部'}")
    print(f"页数: {pages}")
    print("=" * 70)
    
    # 加载配置
    cfg = load_config()
    crawler_cfg = cfg.get("crawler", {})
    job51_cfg = cfg.get("job51", {})
    
    # 配置代理
    proxies = None
    proxy_http = crawler_cfg.get("proxy_http")
    proxy_https = crawler_cfg.get("proxy_https")
    if proxy_http or proxy_https:
        proxies = {}
        if proxy_http:
            proxies['http'] = proxy_http
        if proxy_https:
            proxies['https'] = proxy_https
        if 'http' in proxies and 'https' not in proxies:
            proxies['https'] = proxies['http']
        elif 'https' in proxies and 'http' not in proxies:
            proxies['http'] = proxies['https']
        print(f"[INFO] 使用代理: {proxies}")
    else:
        print("[INFO] 未配置代理，使用直连")
    
    # 创建HttpClient
    delay_min = float(job51_cfg.get("delay_min", 1.0))
    delay_max = float(job51_cfg.get("delay_max", 2.0))
    
    client = HttpClient(
        min_sleep=delay_min,
        max_sleep=delay_max,
        proxies=proxies,
    )
    
    # 创建适配器
    adapter = Job51Adapter(client)
    
    all_posts = []
    
    # 遍历页面
    for page_num in range(1, pages + 1):
        print(f"\n[INFO] 正在爬取第 {page_num}/{pages} 页...")
        
        try:
            # 获取数据
            print(f"[INFO] 调用 fetch() 方法...")
            payload = adapter.fetch(keyword=keyword, city=city, region=None, page=page_num)
            print(f"[OK] 获取到数据，长度: {len(payload)} 字符")
            
            # 解析数据
            print(f"[INFO] 调用 parse() 方法...")
            posts = list(adapter.parse(payload))
            print(f"[OK] 解析到 {len(posts)} 个职位")
            
            if posts:
                all_posts.extend(posts)
                # 打印前3个职位信息
                print(f"\n[INFO] 前3个职位预览:")
                for i, post in enumerate(posts[:3], 1):
                    print(f"  职位 #{i}:")
                    print(f"    ID: {post.job_id}")
                    print(f"    标题: {post.title}")
                    print(f"    公司: {post.company}")
                    print(f"    城市: {post.city}")
                    print(f"    薪资: {post.salary_raw}")
                    print(f"    链接: {post.detail_url[:80]}...")
            else:
                print("[WARNING] 未解析到任何职位")
                if page_num == 1:
                    print("[WARNING] 第一页就没有数据，可能页面结构已变化或需要登录")
                    print(f"[DEBUG] 页面内容预览（前500字符）:")
                    print(payload[:500])
                break
                
        except Exception as e:
            print(f"[ERROR] 爬取第 {page_num} 页失败: {e}")
            import traceback
            traceback.print_exc()
            break
    
    # 去重
    print(f"\n[INFO] 数据去重...")
    print(f"  去重前: {len(all_posts)} 条")
    unique_posts = {}
    for post in all_posts:
        key = f"{post.platform}_{post.job_id}"
        unique_posts[key] = post
    final_posts = list(unique_posts.values())
    print(f"  去重后: {len(final_posts)} 条")
    
    # 保存到数据库
    if final_posts:
        print(f"\n[INFO] 保存数据到数据库...")
        try:
            upsert_jobs(final_posts)
            print(f"[OK] 成功保存 {len(final_posts)} 条职位到数据库")
        except Exception as e:
            print(f"[ERROR] 保存数据失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 统计信息
    print(f"\n" + "=" * 70)
    print("测试完成 - 统计信息")
    print("=" * 70)
    print(f"关键词: {keyword}")
    print(f"城市: {city or '全部'}")
    print(f"爬取页数: {pages}")
    print(f"成功采集: {len(final_posts)} 条职位")
    
    # 城市分布
    from collections import Counter
    city_stats = Counter(post.city for post in final_posts)
    if city_stats:
        print(f"\n城市分布 (Top 5):")
        for city_name, count in city_stats.most_common(5):
            print(f"  {city_name}: {count} 条")
    
    print("=" * 70)
    
    return len(final_posts)

def main():
    parser = argparse.ArgumentParser(description='51job爬虫独立测试脚本')
    parser.add_argument('--keyword', type=str, required=True, help='搜索关键词')
    parser.add_argument('--city', type=str, default=None, help='城市过滤（可选）')
    parser.add_argument('--pages', type=int, default=1, help='页数（默认1）')
    
    args = parser.parse_args()
    
    try:
        count = test_job51_crawler(args.keyword, args.city, args.pages)
        if count > 0:
            print(f"\n[SUCCESS] 测试完成！成功采集 {count} 条职位")
            return 0
        else:
            print(f"\n[WARNING] 测试完成，但未采集到数据")
            return 1
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
