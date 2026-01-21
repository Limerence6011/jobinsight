from __future__ import annotations
import argparse
import time
import random
from typing import Optional, List, Dict, Any, Set, Tuple

from ..settings import load_config
from ..utils.http import HttpClient
from ..utils.log import get_logger
from .platforms.remoteok import RemoteOKApiAdapter
from .platforms.job51.adapter import Job51Adapter
from ..storage.db import upsert_jobs, get_existing_job_keys, get_all_existing_job_keys

logger = get_logger(__name__)

def calculate_similarity_rate(new_posts: List, existing_keys: Set[Tuple[str, str]]) -> float:
    """
    计算数据库现有数据在当前单次爬取数据中的覆盖率
    
    新逻辑：计算数据库中有多少数据在当前单次爬取的数据中存在
    
    Args:
        new_posts: 当前单次爬取的岗位列表
        existing_keys: 数据库中所有现有的 (platform, job_id) 集合
    
    Returns:
        float: 覆盖率（0.0-1.0），表示数据库中有多少数据在当前爬取数据中存在
    """
    if not new_posts or not existing_keys:
        return 0.0
    
    # 构建当前爬取数据的key集合
    new_keys = {(post.platform, post.job_id) for post in new_posts}
    
    # 计算数据库中有多少数据在当前爬取数据中存在
    matched_count = len(existing_keys & new_keys)
    
    # 覆盖率 = 匹配数 / 当前爬取数据总数
    similarity_rate = matched_count / len(new_posts) if new_posts else 0.0
    return similarity_rate

def crawl_once(keyword: str, city: Optional[str], pages: int = 1, platform: str = "remoteok") -> Dict[str, Any]:
    """
    执行数据采集，支持动态页数调整
    
    逻辑：
    1. 每次抓取一页后，与数据库所有数据进行对比
    2. 如果数据库的现有数据有当前单次爬取数据的60%，则爬取页数+6
    3. 最多抓取10页
    """
    cfg = load_config()
    c_cfg = cfg.get("crawler", {})
    job51_cfg = cfg.get("job51", {})
    
    # 最大页数限制
    MAX_PAGES = 10
    SIMILARITY_THRESHOLD = 0.6  # 60% 覆盖率阈值
    PAGE_INCREMENT = 6  # 当达到阈值时，页数增加量
    
    # job51 平台不使用代理，其他平台从配置读取代理设置
    proxies = None
    if platform != "job51":
        proxy_http = c_cfg.get("proxy_http")
        proxy_https = c_cfg.get("proxy_https")
        if proxy_http or proxy_https:
            proxies = {}
            if proxy_http:
                proxies['http'] = proxy_http
            if proxy_https:
                proxies['https'] = proxy_https
            # 如果只设置了一个，另一个使用相同的
            if 'http' in proxies and 'https' not in proxies:
                proxies['https'] = proxies['http']
            elif 'https' in proxies and 'http' not in proxies:
                proxies['http'] = proxies['https']
    
    # 记录代理配置
    if platform == "job51":
        logger.info("使用 job51 平台，无需代理")
    elif proxies:
        logger.info("使用代理: %s", proxies)
    else:
        logger.info("未配置代理，使用直连")
    
    # 获取数据库中所有现有的job数据（用于对比）
    logger.info("查询数据库中所有现有的job数据...")
    all_existing_keys = get_all_existing_job_keys()
    logger.info("数据库中现有 %d 条job记录（所有平台）", len(all_existing_keys))
    
    start_time = time.time()
    all_posts = []
    current_page = 1
    max_pages_to_crawl = min(pages, MAX_PAGES)  # 限制最大页数
    
    # 记录实际爬取的页数
    pages_crawled = 0
    
    if platform == "job51":
        # job51 平台：不使用 HttpClient，直接使用适配器（适配器内部使用 Playwright）
        adapter = Job51Adapter(client=None)
        
        # 动态页数爬取：每次抓取一页后判断是否继续
        while current_page <= max_pages_to_crawl:
            try:
                logger.info("正在爬取第 %d/%d 页...", current_page, max_pages_to_crawl)
                fetch_page_start = time.time()
                
                payload = adapter.fetch(keyword=keyword, city=city, page=current_page)
                fetch_page_time = time.time()
                
                page_posts = list(adapter.parse(payload))
                parse_page_time = time.time()
                
                if not page_posts:
                    logger.warning("第 %d 页未获取到数据，可能已到最后一页", current_page)
                    break
                
                # 计算数据库现有数据在当前单次爬取数据中的覆盖率
                similarity_rate = calculate_similarity_rate(page_posts, all_existing_keys)
                logger.info("第 %d 页获取到 %d 条数据，数据库覆盖率: %.2f%% (获取: %.2fs, 解析: %.2fs)", 
                           current_page, len(page_posts), similarity_rate * 100,
                           fetch_page_time - fetch_page_start,
                           parse_page_time - fetch_page_time)
                
                all_posts.extend(page_posts)
                pages_crawled = current_page  # 记录已爬取的页数
                
                # 更新all_existing_keys，包含本页新抓取的数据（用于后续页的对比）
                for post in page_posts:
                    all_existing_keys.add((post.platform, post.job_id))
                
                # 判断是否继续爬取下一页
                if similarity_rate >= SIMILARITY_THRESHOLD:
                    # 覆盖率≥60%，增加爬取页数
                    new_max_pages = min(max_pages_to_crawl + PAGE_INCREMENT, MAX_PAGES)
                    if new_max_pages > max_pages_to_crawl:
                        max_pages_to_crawl = new_max_pages
                        logger.info("覆盖率 %.2f%% ≥ 60%%，增加爬取页数至 %d 页", similarity_rate * 100, max_pages_to_crawl)
                    
                    # 继续爬取下一页
                    current_page += 1
                    if current_page > max_pages_to_crawl:
                        logger.info("已达到最大页数限制 (%d 页)，停止爬取", max_pages_to_crawl)
                        break
                    logger.info("继续爬取第 %d 页", current_page)
                else:
                    # 覆盖率<60%，停止爬取
                    logger.info("覆盖率 %.2f%% < 60%%，停止爬取", similarity_rate * 100)
                    break
                
                # 页面间延迟（避免请求过快）
                if current_page <= max_pages_to_crawl:
                    delay_min = float(job51_cfg.get("delay_min", 1.0))
                    delay_max = float(job51_cfg.get("delay_max", 2.0))
                    delay = random.uniform(delay_min, delay_max)
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"爬取第 {current_page} 页失败: {e}")
                # 如果出错，也停止爬取
                break
        
        fetch_time = time.time()
        parse_time = fetch_time
    else:
        # remoteok 平台：使用原有逻辑（不支持分页，只抓取一次）
        client = HttpClient(
            min_sleep=float(c_cfg.get("polite_sleep_min", 0.6)),
            max_sleep=float(c_cfg.get("polite_sleep_max", 1.5)),
            proxies=proxies,
        )
        
        adapter = RemoteOKApiAdapter(client)
        
        # RemoteOK feed doesn't paginate; keep `pages` arg for interface compatibility
        payload = adapter.fetch(keyword=keyword, city=city, page=1)
        fetch_time = time.time()
        
        for post in adapter.parse(payload):
            # filter keyword/city here for this data source
            if keyword:
                k = keyword.lower()
                hay = (post.title + " " + (post.description or "") + " " + " ".join(post.tags or [])).lower()
                if k not in hay:
                    continue
            if city:
                if city.lower() not in (post.city or "").lower():
                    continue
            all_posts.append(post)
        
        pages_crawled = 1  # remoteok 只抓取一次
        parse_time = time.time()

    # 去重（基于platform + job_id）
    seen = set()
    unique_posts = []
    for post in all_posts:
        key = (post.platform, post.job_id)
        if key not in seen:
            seen.add(key)
            unique_posts.append(post)
    
    if len(all_posts) != len(unique_posts):
        logger.info("去重前: %d 条，去重后: %d 条", len(all_posts), len(unique_posts))
    
    upsert_jobs(unique_posts)
    end_time = time.time()
    
    # 统计信息
    total_count = len(unique_posts)
    fetch_duration = fetch_time - start_time
    parse_duration = parse_time - fetch_time
    save_duration = end_time - parse_time
    total_duration = end_time - start_time
    
    # 统计城市分布
    city_stats = {}
    for post in unique_posts:
        city_name = post.city or "Unknown"
        city_stats[city_name] = city_stats.get(city_name, 0) + 1
    
    # 计算最终与数据库的覆盖率（用于统计）
    final_similarity_rate = 0.0
    if unique_posts:
        # 重新获取所有数据库数据（因为可能已经更新）
        final_existing_keys = get_all_existing_job_keys()
        final_similarity_rate = calculate_similarity_rate(unique_posts, final_existing_keys)
    
    result = {
        "success": True,
        "count": total_count,
        "keyword": keyword,
        "city": city or None,
        "platform": platform,
        "pages_crawled": pages_crawled,
        "similarity_rate": round(final_similarity_rate * 100, 2),
        "duration": {
            "total": round(total_duration, 2),
            "fetch": round(fetch_duration, 2),
            "parse": round(parse_duration, 2),
            "save": round(save_duration, 2)
        },
        "city_stats": dict(sorted(city_stats.items(), key=lambda x: x[1], reverse=True)[:10])
    }
    
    logger.info("采集完成: 共 %s 条岗位 (平台=%s, 关键词=%s, 城市=%s, 爬取页数=%d, 相同率=%.2f%%, 耗时=%.2fs)", 
                total_count, platform, keyword, city or "全部", 
                result["pages_crawled"], result["similarity_rate"], total_duration)
    
    return result

def print_crawl_summary(result: Dict[str, Any]):
    """打印美观的采集结果摘要"""
    import sys
    import io
    # 设置输出编码为UTF-8，避免Windows控制台编码问题
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("\n" + "=" * 60)
    print(" " * 15 + "数据采集完成")
    print("=" * 60)
    
    if result["success"]:
        print(f"\n[OK] 采集成功！")
        print(f"\n统计信息:")
        print(f"   - 采集数量: {result['count']} 条岗位")
        print(f"   - 关键词: {result['keyword']}")
        if result['city']:
            print(f"   - 城市过滤: {result['city']}")
        else:
            print(f"   - 城市过滤: 全部")
        
        print(f"\n耗时统计:")
        dur = result['duration']
        print(f"   - 总耗时: {dur['total']} 秒")
        print(f"   - 数据获取: {dur['fetch']} 秒")
        print(f"   - 数据解析: {dur['parse']} 秒")
        print(f"   - 数据保存: {dur['save']} 秒")
        
        if result['city_stats']:
            print(f"\n城市分布 (Top {len(result['city_stats'])}):")
            for city, count in list(result['city_stats'].items())[:5]:
                bar = "#" * min(20, int(count * 20 / max(result['city_stats'].values())))
                print(f"   - {city:20s} {count:4d} 条 {bar}")
    else:
        print(f"\n[ERROR] 采集失败: {result.get('error', '未知错误')}")
    
    print("\n" + "=" * 60 + "\n")

def main():
    cfg = load_config()
    default_keyword = cfg.get("crawler", {}).get("default_keyword", "python")
    default_pages = int(cfg.get("crawler", {}).get("pages", 1))

    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", default=default_keyword, help="search keyword")
    ap.add_argument("--city", default="", help="city/location filter (optional)")
    ap.add_argument("--pages", type=int, default=default_pages, help="kept for compatibility")
    ap.add_argument("--platform", default="remoteok", choices=["remoteok", "job51"], help="platform to crawl")
    args = ap.parse_args()

    try:
        result = crawl_once(keyword=args.keyword, city=args.city or None, pages=args.pages, platform=args.platform)
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
