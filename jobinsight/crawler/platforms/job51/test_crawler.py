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
project_root = Path(__file__).resolve().parents[4]
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
        logging.FileHandler('test_crawler.log', encoding='utf-8')
    ]
)

logger = get_logger(__name__)

def test_crawler(keyword: str, city: str = None, pages: int = 1, 
                 max_attempts: int = 8, min_success_count: int = 1, 
                 max_failures: int = 3):
    """
    测试爬虫功能（带循环重试机制）
    
    Args:
        keyword: 搜索关键词
        city: 城市过滤
        pages: 每轮爬取的页数
        max_attempts: 最大尝试次数（默认8次）
        min_success_count: 成功条件：至少采集到的职位数量（默认1条）
        max_failures: 失败条件：连续失败次数达到此值则停止（默认3次）
    
    Returns:
        (总采集数量, 是否达到目标, 停止原因)
    """
    logger.info("=" * 80)
    logger.info("开始测试51job爬虫（循环重试模式）")
    logger.info("=" * 80)
    logger.info(f"参数: keyword={keyword}, city={city}, pages={pages}")
    logger.info(f"重试策略: 最多尝试{max_attempts}次, 成功条件≥{min_success_count}条, 连续失败{max_failures}次停止")
    
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
    
    # 循环重试统计
    all_attempts_posts = []  # 所有尝试采集到的职位
    consecutive_failures = 0  # 连续失败次数
    success_attempts = 0  # 成功次数
    stop_reason = None  # 停止原因
    
    # 循环执行最多max_attempts次
    for attempt in range(1, max_attempts + 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"第 {attempt}/{max_attempts} 次尝试")
        logger.info(f"{'='*80}")
        logger.info(f"连续失败次数: {consecutive_failures}/{max_failures}")
        logger.info(f"累计成功次数: {success_attempts}")
        logger.info(f"累计采集职位: {len(all_attempts_posts)} 条")
        
        attempt_posts = []  # 本次尝试采集到的职位
        
        try:
            # 遍历页面
            for page_num in range(1, pages + 1):
                logger.info(f"\n  --- 第 {page_num}/{pages} 页 ---")
                
                try:
                    # 获取数据
                    logger.info(f"  调用 fetch() 方法...")
                    payload = adapter.fetch(keyword=keyword, city=city, region=None, page=page_num)
                    logger.info(f"  获取到数据，长度: {len(payload)} 字符")
                    logger.debug(f"  数据预览: {payload[:200]}...")
                    
                    # 解析数据
                    logger.info(f"  调用 parse() 方法...")
                    posts = list(adapter.parse(payload))
                    logger.info(f"  解析到 {len(posts)} 个职位")
                    
                    if posts:
                        attempt_posts.extend(posts)
                        # 打印前2个职位信息
                        for i, post in enumerate(posts[:2], 1):
                            logger.info(f"  职位 #{i}: {post.title} @ {post.company} ({post.city})")
                    else:
                        logger.warning("  未解析到任何职位")
                        
                except Exception as e:
                    logger.error(f"  爬取第 {page_num} 页失败: {e}", exc_info=True)
                    # 单页失败不中断整个尝试，继续下一页
                    continue
            
            # 判断本次尝试是否成功
            if len(attempt_posts) > 0:
                # 本次尝试成功
                consecutive_failures = 0
                success_attempts += 1
                all_attempts_posts.extend(attempt_posts)
                logger.info(f"\n[成功] 第 {attempt} 次尝试成功采集 {len(attempt_posts)} 条职位")
                
                # 检查是否达到目标
                unique_posts = {}
                for post in all_attempts_posts:
                    key = f"{post.platform}_{post.job_id}"
                    unique_posts[key] = post
                total_unique = len(unique_posts)
                
                if total_unique >= min_success_count:
                    logger.info(f"[达到目标] 累计采集 {total_unique} 条职位，已达到目标（≥{min_success_count}条）")
                    stop_reason = f"达到目标（采集到{total_unique}条职位）"
                    break
            else:
                # 本次尝试失败
                consecutive_failures += 1
                logger.warning(f"\n[失败] 第 {attempt} 次尝试未采集到任何职位")
                
                # 检查是否连续失败次数过多
                if consecutive_failures >= max_failures:
                    logger.error(f"[无法达到目的] 连续失败 {consecutive_failures} 次，停止重试")
                    stop_reason = f"连续失败{consecutive_failures}次，无法达到目的"
                    break
                    
        except Exception as e:
            # 本次尝试出现异常
            consecutive_failures += 1
            logger.error(f"\n[异常] 第 {attempt} 次尝试出现异常: {e}", exc_info=True)
            
            if consecutive_failures >= max_failures:
                logger.error(f"[无法达到目的] 连续失败 {consecutive_failures} 次，停止重试")
                stop_reason = f"连续失败{consecutive_failures}次（异常），无法达到目的"
                break
        
        # 如果还没达到目标且还有剩余尝试次数，继续
        if attempt < max_attempts and stop_reason is None:
            logger.info(f"\n等待下一次尝试...")
            import time
            time.sleep(2)  # 每次尝试之间稍作等待
        elif stop_reason:
            # 已确定停止原因，跳出循环
            break
    
    # 最终统计
    logger.info(f"\n{'='*80}")
    logger.info("循环测试完成")
    logger.info(f"{'='*80}")
    
    # 去重
    logger.info(f"去重前: {len(all_attempts_posts)} 条")
    unique_posts = {}
    for post in all_attempts_posts:
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
    logger.info("最终统计信息")
    logger.info(f"{'='*80}")
    logger.info(f"关键词: {keyword}")
    logger.info(f"城市: {city or '全部'}")
    logger.info(f"每轮页数: {pages}")
    logger.info(f"总尝试次数: {attempt}/{max_attempts}")
    logger.info(f"成功次数: {success_attempts}")
    logger.info(f"失败次数: {attempt - success_attempts}")
    logger.info(f"成功采集: {len(final_posts)} 条职位")
    logger.info(f"停止原因: {stop_reason or '达到最大尝试次数'}")
    
    # 判断是否达到目标
    reached_goal = len(final_posts) >= min_success_count
    
    # 城市分布
    from collections import Counter
    city_stats = Counter(post.city for post in final_posts)
    if city_stats:
        logger.info(f"\n城市分布 (Top 5):")
        for city_name, count in city_stats.most_common(5):
            logger.info(f"  {city_name}: {count} 条")
    
    return len(final_posts), reached_goal, stop_reason

def main():
    parser = argparse.ArgumentParser(description='51job爬虫测试脚本（带详细日志）')
    parser.add_argument('--keyword', type=str, required=True, help='搜索关键词')
    parser.add_argument('--city', type=str, default=None, help='城市过滤（可选）')
    parser.add_argument('--pages', type=int, default=1, help='页数（默认1）')
    
    args = parser.parse_args()
    
    try:
        count = test_crawler(args.keyword, args.city, args.pages)
        print(f"\n测试完成！成功采集 {count} 条职位")
        print(f"详细日志已保存到: test_crawler.log")
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
