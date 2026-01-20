from __future__ import annotations
import argparse
import time
from typing import Optional, List, Dict, Any

from ..settings import load_config
from ..utils.http import HttpClient
from ..utils.log import get_logger
from .platforms.remoteok import RemoteOKApiAdapter
from ..storage.db import upsert_jobs

logger = get_logger(__name__)

def crawl_once(keyword: str, city: Optional[str], pages: int = 1) -> Dict[str, Any]:
    cfg = load_config()
    c_cfg = cfg.get("crawler", {})
    
    # 从配置读取代理设置
    proxies = None
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
    if proxies:
        logger.info("使用代理: %s", proxies)
    else:
        logger.info("未配置代理，使用直连")
    
    client = HttpClient(
        min_sleep=float(c_cfg.get("polite_sleep_min", 0.6)),
        max_sleep=float(c_cfg.get("polite_sleep_max", 1.5)),
        proxies=proxies,
    )

    start_time = time.time()
    adapter = RemoteOKApiAdapter(client)
    all_posts = []
    
    # RemoteOK feed doesn't paginate; keep `pages` arg for interface compatibility
    payload = adapter.fetch(keyword=keyword, city=city, page=1)
    fetch_time = time.time()
    
    for post in adapter.parse(payload):
        # filter keyword/city here for this data source
        if keyword:
            k = keyword.lower()
            hay = (post.title + " " + post.description + " " + " ".join(post.tags)).lower()
            if k not in hay:
                continue
        if city:
            if city.lower() not in (post.city or "").lower():
                continue
        all_posts.append(post)

    parse_time = time.time()
    upsert_jobs(all_posts)
    end_time = time.time()
    
    # 统计信息
    total_count = len(all_posts)
    fetch_duration = fetch_time - start_time
    parse_duration = parse_time - fetch_time
    save_duration = end_time - parse_time
    total_duration = end_time - start_time
    
    # 统计城市分布
    city_stats = {}
    for post in all_posts:
        city_name = post.city or "Unknown"
        city_stats[city_name] = city_stats.get(city_name, 0) + 1
    
    result = {
        "success": True,
        "count": total_count,
        "keyword": keyword,
        "city": city or None,
        "duration": {
            "total": round(total_duration, 2),
            "fetch": round(fetch_duration, 2),
            "parse": round(parse_duration, 2),
            "save": round(save_duration, 2)
        },
        "city_stats": dict(sorted(city_stats.items(), key=lambda x: x[1], reverse=True)[:10])
    }
    
    logger.info("采集完成: 共 %s 条岗位 (关键词=%s, 城市=%s, 耗时=%.2fs)", 
                total_count, keyword, city or "全部", total_duration)
    
    return result

def print_crawl_summary(result: Dict[str, Any]):
    """打印美观的采集结果摘要"""
    print("\n" + "=" * 60)
    print(" " * 15 + "📊 数据采集完成")
    print("=" * 60)
    
    if result["success"]:
        print(f"\n✅ 采集成功！")
        print(f"\n📈 统计信息:")
        print(f"   • 采集数量: {result['count']} 条岗位")
        print(f"   • 关键词: {result['keyword']}")
        if result['city']:
            print(f"   • 城市过滤: {result['city']}")
        else:
            print(f"   • 城市过滤: 全部")
        
        print(f"\n⏱️  耗时统计:")
        dur = result['duration']
        print(f"   • 总耗时: {dur['total']} 秒")
        print(f"   • 数据获取: {dur['fetch']} 秒")
        print(f"   • 数据解析: {dur['parse']} 秒")
        print(f"   • 数据保存: {dur['save']} 秒")
        
        if result['city_stats']:
            print(f"\n🌍 城市分布 (Top {len(result['city_stats'])}):")
            for city, count in list(result['city_stats'].items())[:5]:
                bar = "█" * min(20, int(count * 20 / max(result['city_stats'].values())))
                print(f"   • {city:20s} {count:4d} 条 {bar}")
    else:
        print(f"\n❌ 采集失败: {result.get('error', '未知错误')}")
    
    print("\n" + "=" * 60 + "\n")

def main():
    cfg = load_config()
    default_keyword = cfg.get("crawler", {}).get("default_keyword", "python")
    default_pages = int(cfg.get("crawler", {}).get("pages", 1))

    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", default=default_keyword, help="search keyword")
    ap.add_argument("--city", default="", help="city/location filter (optional)")
    ap.add_argument("--pages", type=int, default=default_pages, help="kept for compatibility")
    args = ap.parse_args()

    try:
        result = crawl_once(keyword=args.keyword, city=args.city or None, pages=args.pages)
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
