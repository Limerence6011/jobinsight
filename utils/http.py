from __future__ import annotations
import os
import time
import random
import requests
from requests import Response
from typing import Optional, Dict
import urllib3

# 禁用 SSL 警告（某些代理环境需要）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HttpClient:
    """Simple HTTP client with polite sleep and retries."""
    def __init__(self, timeout: int = 20, min_sleep: float = 0.6, max_sleep: float = 1.5, 
                 retries: int = 2, proxies: Optional[Dict[str, str]] = None):
        self.sess = requests.Session()
        self.timeout = timeout
        self.min_sleep = min_sleep
        self.max_sleep = max_sleep
        self.retries = retries
        
        # 设置代理：优先使用传入的代理，其次从环境变量读取，最后从配置文件读取
        if proxies:
            self.proxies = proxies
        else:
            # 从环境变量读取代理
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
            https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
            
            if http_proxy or https_proxy:
                self.proxies = {
                    'http': http_proxy or https_proxy,
                    'https': https_proxy or http_proxy,
                }
            else:
                self.proxies = None
        
        # 如果设置了代理，应用到 session
        if self.proxies:
            # 直接设置 proxies 属性，而不是 update
            self.sess.proxies = self.proxies.copy()

    def _sleep(self) -> None:
        time.sleep(random.uniform(self.min_sleep, self.max_sleep))

    def get(self, url: str, *, headers: dict | None = None, params: dict | None = None) -> Response:
        last_err: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                self._sleep()
                # 在每次请求时显式传递代理，确保代理设置生效
                # 使用 verify=False 以兼容某些代理环境
                resp = self.sess.get(
                    url, 
                    headers=headers, 
                    params=params, 
                    timeout=self.timeout, 
                    verify=False,
                    proxies=self.proxies  # 显式传递代理
                )
                resp.raise_for_status()
                return resp
            except Exception as e:
                last_err = e
                # 如果是最后一次尝试且是代理错误，记录日志
                if attempt == self.retries:
                    from .log import get_logger
                    logger = get_logger(__name__)
                    logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.retries + 1}): {e}")
        raise last_err  # type: ignore[misc]
