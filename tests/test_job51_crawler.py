#!/usr/bin/env python3
"""
51job爬虫测试脚本（带详细日志）

用法:
    python test_crawler.py --keyword C --city 南京 --pages 1
    python test_crawler.py --keyword python --pages 2
"""

import argparse
import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from jobinsight.settings import load_config
from jobinsight.utils.http import HttpClient
from jobinsight.utils.log import get_logger
from jobinsight.crawler.platforms.job51.adapter import Job51Adapter
from jobinsight.storage.db import upsert_jobs

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tests/test_crawler.log', encoding='utf-8')
    ]
)

logger = get_logger(__name__)

def test_crawler(keyword: str, city: str = None, pages: int = 1):
    """测试爬虫功能"""
    logger.info("=" * 80)
    logger.info("开始测试51job爬虫")
    logger.info("=" * 80)
    logger.info(f"参数: keyword={keyword}, city={city}, pages={pages}")
    
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
        logger.info(f"使用代理: {proxies}")
    else:
        logger.info("未配置代理，使用直连")
    
    # 创建HttpClient
    client = HttpClient(
        min_sleep=float(job51_cfg.get("delay_min", 1.0)),
        max_sleep=float(job51_cfg.get("delay_max", 2.0)),
        proxies=proxies,
    )
    
    # 创建适配器
    adapter = Job51Adapter(client)
    
    all_posts = []
    
    # 遍历页面
    for page_num in range(1, pages + 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"正在爬取第 {page_num}/{pages} 页")
        logger.info(f"{'='*80}")
        
        try:
            # 获取数据
            logger.info(f"调用 fetch() 方法...")
            payload = adapter.fetch(keyword=keyword, city=city, region=None, page=page_num)
            logger.info(f"获取到数据，长度: {len(payload)} 字符")
            logger.debug(f"数据预览: {payload[:200]}...")
            
            # 解析数据
            logger.info(f"调用 parse() 方法...")
            posts = list(adapter.parse(payload))
            logger.info(f"解析到 {len(posts)} 个职位")
            
            if posts:
                all_posts.extend(posts)
                # 打印前3个职位信息
                for i, post in enumerate(posts[:3], 1):
                    logger.info(f"\n职位 #{i}:")
                    logger.info(f"  ID: {post.job_id}")
                    logger.info(f"  标题: {post.title}")
                    logger.info(f"  公司: {post.company}")
                    logger.info(f"  城市: {post.city}")
                    logger.info(f"  薪资: {post.salary_raw}")
                    logger.info(f"  链接: {post.detail_url}")
            else:
                logger.warning("未解析到任何职位")
                
        except Exception as e:
            logger.error(f"爬取第 {page_num} 页失败: {e}", exc_info=True)
            break
    
    # 去重
    logger.info(f"\n{'='*80}")
    logger.info("数据去重")
    logger.info(f"{'='*80}")
    logger.info(f"去重前: {len(all_posts)} 条")
    unique_posts = {}
    for post in all_posts:
        key = f"{post.platform}_{post.job_id}"
        unique_posts[key] = post
    final_posts = list(unique_posts.values())
    logger.info(f"去重后: {len(final_posts)} 条")
    
    # 保存到数据库
    if final_posts:
        logger.info(f"\n{'='*80}")
        logger.info("保存数据到数据库")
        logger.info(f"{'='*80}")
        try:
            upsert_jobs(final_posts)
            logger.info(f"成功保存 {len(final_posts)} 条职位到数据库")
        except Exception as e:
            logger.error(f"保存数据失败: {e}", exc_info=True)
    
    # 统计信息
    logger.info(f"\n{'='*80}")
    logger.info("测试完成 - 统计信息")
    logger.info(f"{'='*80}")
    logger.info(f"关键词: {keyword}")
    logger.info(f"城市: {city or '全部'}")
    logger.info(f"爬取页数: {pages}")
    logger.info(f"成功采集: {len(final_posts)} 条职位")
    
    # 城市分布
    from collections import Counter
    city_stats = Counter(post.city for post in final_posts)
    if city_stats:
        logger.info(f"\n城市分布 (Top 5):")
        for city_name, count in city_stats.most_common(5):
            logger.info(f"  {city_name}: {count} 条")
    
    return len(final_posts)

def main():
    parser = argparse.ArgumentParser(description='51job爬虫测试脚本（带详细日志）')
    parser.add_argument('--keyword', type=str, required=True, help='搜索关键词')
    parser.add_argument('--city', type=str, default=None, help='城市过滤（可选）')
    parser.add_argument('--pages', type=int, default=1, help='页数（默认1）')
    
    args = parser.parse_args()
    
    try:
        count = test_crawler(args.keyword, args.city, args.pages)
        print(f"\n测试完成！成功采集 {count} 条职位")
        print(f"详细日志已保存到: tests/test_crawler.log")
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
