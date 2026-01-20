#!/usr/bin/env python3
"""
前程无忧51job平台爬虫执行脚本（仅作学习交流使用）

用法:
    # 方式1：作为模块运行（推荐）
    python -m jobinsight.crawler.platforms.job51.run --keyword python --city 上海
    
    # 方式2：直接运行（需要在项目根目录下）
    cd jobinsight_project
    python jobinsight/crawler/platforms/job51/run.py --keyword python --city 上海

参数:
    --keyword KEYWORD    搜索关键词（必需）
    --city CITY          城市过滤（可选）
    --region REGION      区县过滤（可选，仅在指定单个城市时有效）
    --pages PAGES        页数（可选，默认1）
"""

import argparse
import sys
import os
import time
import random
from pathlib import Path
from typing import Optional, Dict, Any

# 处理直接运行时的导入问题
# 添加项目根目录到 Python 路径
current_file = Path(__file__).resolve()
# 项目根目录本身就是 jobinsight 包（因为有 __init__.py）
project_root = current_file.parents[3]  # 从 job51/run.py 向上4级到项目根目录
parent_dir = project_root.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    from jobinsight.settings import load_config
    from jobinsight.utils.http import HttpClient
    from jobinsight.utils.log import get_logger
    from jobinsight.crawler.platforms.job51.adapter import Job51Adapter
    from jobinsight.storage.db import upsert_jobs
except ImportError:
    # 如果绝对导入失败，尝试相对导入（作为模块运行时）
    from ....settings import load_config
    from ....utils.http import HttpClient
    from ....utils.log import get_logger
    from .adapter import Job51Adapter
    from ....storage.db import upsert_jobs

logger = get_logger(__name__)

def crawl_once(keyword: str, city: Optional[str] = None, region: Optional[str] = None, 
               pages: int = 1) -> Dict[str, Any]:
    """
    执行一次51job数据采集
    
    Args:
        keyword: 搜索关键词
        city: 城市名称（可选）
        region: 区县名称（可选）
        pages: 爬取页数
    
    Returns:
        采集结果字典
    """
    cfg = load_config()
    job51_cfg = cfg.get("job51", {})
    crawler_cfg = cfg.get("crawler", {})
    
    # 从配置读取代理设置
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
    
    # 从job51配置读取延迟设置
    delay_min = float(job51_cfg.get("delay_min", 1.0))
    delay_max = float(job51_cfg.get("delay_max", 2.0))
    max_pages = int(job51_cfg.get("max_pages", 10))
    
    # 限制页数
    pages = min(pages, max_pages)
    
    if proxies:
        logger.info("使用代理: %s", proxies)
    else:
        logger.info("未配置代理，使用直连")
    
    client = HttpClient(
        min_sleep=delay_min,
        max_sleep=delay_max,
        proxies=proxies,
    )
    
    start_time = time.time()
    adapter = Job51Adapter(client)
    all_posts = []
    
    # 爬取多页数据
    for page in range(1, pages + 1):
        try:
            logger.info("正在爬取第 %d/%d 页...", page, pages)
            fetch_page_start = time.time()
            
            payload = adapter.fetch(keyword=keyword, city=city, region=region, page=page)
            fetch_page_time = time.time()
            
            page_posts = list(adapter.parse(payload))
            parse_page_time = time.time()
            
            if not page_posts:
                logger.warning("第 %d 页未获取到数据，可能已到最后一页", page)
                break
            
            all_posts.extend(page_posts)
            logger.info("第 %d 页获取到 %d 条数据 (获取: %.2fs, 解析: %.2fs)", 
                       page, len(page_posts), 
                       fetch_page_time - fetch_page_start,
                       parse_page_time - fetch_page_time)
            
            # 页面间延迟（避免请求过快）
            if page < pages:
                delay = random.uniform(delay_min, delay_max)
                time.sleep(delay)
                
        except Exception as e:
            logger.error(f"爬取第 {page} 页失败: {e}")
            # 继续爬取下一页
            continue
    
    parse_time = time.time()
    
    # 去重（基于platform + job_id）
    seen = set()
    unique_posts = []
    for post in all_posts:
        key = (post.platform, post.job_id)
        if key not in seen:
            seen.add(key)
            unique_posts.append(post)
    
    logger.info("去重前: %d 条，去重后: %d 条", len(all_posts), len(unique_posts))
    
    # 保存到数据库
    upsert_jobs(unique_posts)
    end_time = time.time()
    
    # 统计信息
    total_count = len(unique_posts)
    fetch_duration = parse_time - start_time
    save_duration = end_time - parse_time
    total_duration = end_time - start_time
    
    # 统计城市分布
    city_stats = {}
    for post in unique_posts:
        city_name = post.city or "Unknown"
        city_stats[city_name] = city_stats.get(city_name, 0) + 1
    
    result = {
        "success": True,
        "count": total_count,
        "keyword": keyword,
        "city": city or None,
        "region": region or None,
        "pages": pages,
        "duration": {
            "total": round(total_duration, 2),
            "fetch": round(fetch_duration, 2),
            "save": round(save_duration, 2)
        },
        "city_stats": dict(sorted(city_stats.items(), key=lambda x: x[1], reverse=True)[:10])
    }
    
    logger.info("采集完成: 共 %s 条岗位 (关键词=%s, 城市=%s, 页数=%d, 耗时=%.2fs)", 
                total_count, keyword, city or "全部", pages, total_duration)
    
    return result

def print_crawl_summary(result: Dict[str, Any]):
    """打印美观的采集结果摘要"""
    print("\n" + "=" * 60)
    print(" " * 15 + "[OK] 51job数据采集完成")
    print("=" * 60)
    
    if result["success"]:
        print(f"\n[OK] 采集成功！")
        print(f"\n统计信息:")
        print(f"   • 采集数量: {result['count']} 条岗位")
        print(f"   • 关键词: {result['keyword']}")
        if result['city']:
            print(f"   • 城市: {result['city']}")
        if result.get('region'):
            print(f"   • 区县: {result['region']}")
        print(f"   • 爬取页数: {result.get('pages', 1)}")
        
        print(f"\n耗时统计:")
        dur = result['duration']
        print(f"   • 总耗时: {dur['total']} 秒")
        print(f"   • 数据获取与解析: {dur['fetch']} 秒")
        print(f"   • 数据保存: {dur['save']} 秒")
        
        if result['city_stats']:
            print(f"\n城市分布 (Top {len(result['city_stats'])}):")
            for city, count in list(result['city_stats'].items())[:5]:
                max_count = max(result['city_stats'].values()) if result['city_stats'] else 1
                bar = "█" * min(20, int(count * 20 / max_count))
                print(f"   • {city:20s} {count:4d} 条 {bar}")
    else:
        print(f"\n[ERROR] 采集失败: {result.get('error', '未知错误')}")
    
    print("\n" + "=" * 60 + "\n")

def main():
    parser = argparse.ArgumentParser(description='前程无忧51job平台数据采集（仅作学习交流使用）')
    parser.add_argument('--keyword', type=str, required=True, help='搜索关键词')
    parser.add_argument('--city', type=str, default=None, help='城市过滤（可选）')
    parser.add_argument('--region', type=str, default=None, help='区县过滤（可选，仅在指定单个城市时有效）')
    parser.add_argument('--pages', type=int, default=1, help='页数（默认1）')
    
    args = parser.parse_args()
    
    try:
        result = crawl_once(
            keyword=args.keyword, 
            city=args.city, 
            region=args.region,
            pages=args.pages
        )
        print_crawl_summary(result)
    except Exception as e:
        logger.error(f"采集失败: {e}", exc_info=True)
        result = {
            "success": False,
            "error": str(e),
            "count": 0
        }
        print_crawl_summary(result)
        raise

if __name__ == "__main__":
    main()
