from __future__ import annotations
import argparse

from .adapter import Wuba58Adapter
from ....utils.http import HttpClient
from ....utils.log import get_logger

logger = get_logger(__name__)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", required=True, help="search keyword")
    ap.add_argument("--city", default="", help="city/location filter (optional)")
    ap.add_argument("--pages", type=int, default=1, help="pages to crawl")
    args = ap.parse_args()

    adapter = Wuba58Adapter(HttpClient())
    try:
        payload = adapter.fetch(keyword=args.keyword, city=args.city or None, page=1)
        posts = list(adapter.parse(payload))
        logger.info("Fetched %d posts", len(posts))
    except NotImplementedError as e:
        logger.error(str(e))

if __name__ == "__main__":
    main()
