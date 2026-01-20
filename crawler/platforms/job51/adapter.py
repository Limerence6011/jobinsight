import json
import logging
import time
import random
import re
from typing import Iterator, Dict, Any, Optional
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# 确保这里的引用路径正确
from jobinsight.crawler.base import BaseAdapter, JobPost as Job 

logger = logging.getLogger(__name__)

class Job51Adapter(BaseAdapter):
    """
    前程无忧 (51job) 适配器 - Playwright 诊断版
    """

    def __init__(self, client=None):
        self.client = client
        self.base_url = "https://we.51job.com/pc/search"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

    def _build_url(self, keyword: str, city: str = None, page: int = 1) -> str:
        params = {
            "keyword": keyword,
            "searchType": 2,
            "sortType": 0,
            "metro": ""
        }
        query_string = urlencode(params)
        return f"{self.base_url}?{query_string}"

    def fetch(self, keyword: str, city: str = None, page: int = 1, **kwargs) -> str:
        """
        使用 Playwright 加载页面
        """
        url = self._build_url(keyword, city, page)
        logger.info(f"[Job51] 启动 Playwright 抓取: {url}")
        
        result_payload = ""

        try:
            with sync_playwright() as p:
                # 1. 启动浏览器
                browser = p.chromium.launch(headless=True) # 调试时可改为 False
                
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent=random.choice(self.user_agents)
                )
                
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)

                page_obj = context.new_page()
                page_obj.goto(url)
                
                # 2. 等待加载
                try:
                    page_obj.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    logger.warning("[Job51] 等待网络空闲超时，尝试继续...")

                # 3. 尝试直接从浏览器内存获取 JSON 数据 (修复了之前的语法错误)
                logger.info("[Job51] 尝试提取 window.__SEARCH_RESULT__ ...")
                json_data = page_obj.evaluate("""
                    window.__SEARCH_RESULT__ ? JSON.stringify(window.__SEARCH_RESULT__) : null
                """)
                
                if json_data and len(json_data) > 100:
                    logger.info("[Job51] 成功提取到内存 JSON 数据")
                    result_payload = "JSON_PREFIX:" + json_data
                else:
                    # 4. 如果提取不到 JSON，回退到 HTML
                    logger.warning("[Job51] 未找到内存 JSON，回退到 HTML 解析模式")
                    # 滚动到底部
                    page_obj.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2) 
                    result_payload = page_obj.content()

                browser.close()

        except Exception as e:
            logger.error(f"[Job51] Playwright 执行异常: {e}")
            return ""

        return result_payload

    def parse(self, content: str) -> Iterator[Job]:
        """
        解析数据
        """
        if not content:
            logger.warning("[Job51] 内容为空，跳过解析")
            return

        # 策略 A: JSON 解析
        if content.startswith("JSON_PREFIX:"):
            logger.info("[Job51] 使用 JSON 解析策略")
            json_str = content.replace("JSON_PREFIX:", "", 1)
            try:
                data = json.loads(json_str)
                job_list = data.get('engine_search_result', [])
                if not job_list:
                    # 有时候可能是 top_ads
                    job_list = data.get('job_search_result', [])
                
                logger.info(f"[Job51] JSON 中包含 {len(job_list)} 个职位")
                for item in job_list:
                    yield self._parse_json_item(item)
            except json.JSONDecodeError as e:
                logger.error(f"[Job51] JSON 解析错误: {e}")

        # 策略 B: HTML DOM 解析
        else:
            logger.info("[Job51] 使用 HTML DOM 解析策略")
            soup = BeautifulSoup(content, 'lxml')
            
            # --- 尝试多种选择器 ---
            # 1. 尝试找包含 list 的 div
            job_items = soup.select(".j_joblist > div") 
            
            # 2. 如果没找到，尝试找常见的 item 容器
            if not job_items:
                job_items = soup.select(".joblist-item")
            
            # 3. 实在不行，尝试找包含 jobid 属性的 div (非常宽泛的搜索)
            if not job_items:
                job_items = soup.find_all("div", attrs={"jobid": True})

            # --- 诊断逻辑 ---
            if not job_items:
                logger.warning("!!! 严重警告：未匹配到任何职位元素 !!!")
                logger.warning("正在将页面保存为 'debug_51job.html'，请查看该文件！")
                try:
                    with open("debug_51job.html", "w", encoding="utf-8") as f:
                        f.write(soup.prettify())
                    logger.info("[DEBUG] 文件已保存至项目根目录: debug_51job.html")
                except Exception as e:
                    logger.error(f"[DEBUG] 保存文件失败: {e}")
            else:
                logger.info(f"[Job51] DOM 中找到 {len(job_items)} 个职位元素")
            
            for item in job_items:
                job = self._parse_dom_item(item)
                if job:
                    yield job

    def _parse_json_item(self, item: Dict[str, Any]) -> Job:
        return Job(
            platform="51job",
            job_id=str(item.get('jobid', '')),
            title=item.get('job_name', '未知职位'),
            company=item.get('coname', '未知公司'),
            city=item.get('workarea_text', ''),
            salary_raw=item.get('providesalary_text', ''),
            detail_url=item.get('job_href', ''),
            pub_date=item.get('updatedate', ''),
            raw_data=json.dumps(item, ensure_ascii=False)
        )

    def _parse_dom_item(self, item) -> Optional[Job]:
        """
        解析 HTML DOM 元素，使用了极其防御性的写法防止报错
        """
        try:
            # 辅助函数：安全获取文本
            def safe_text(elem):
                return elem.get_text(strip=True) if elem else ""

            # 标题 (尝试多种 class)
            title_elem = item.select_one(".jname") or item.select_one(".title") or item.select_one("span[title]")
            title = safe_text(title_elem)
            if not title: return None # 必须有标题

            # 链接
            link = ""
            if title_elem and title_elem.name == 'a':
                link = title_elem.get('href', '')
            elif item.select_one("a"):
                link = item.select_one("a").get('href', '')

            # 公司
            company_elem = item.select_one(".cname") or item.select_one(".company_name") or item.select_one(".company")
            company = safe_text(company_elem)

            # 薪资
            salary_elem = item.select_one(".sal") or item.select_one(".salary") or item.select_one("span.text-warning")
            salary = safe_text(salary_elem)

            # 城市
            info_elem = item.select_one(".info") or item.select_one(".d")
            city = safe_text(info_elem)

            # 提取 ID
            job_id = ""
            if link:
                match = re.search(r'/(\d+)\.html', link)
                if match:
                    job_id = match.group(1)

            return Job(
                platform="51job",
                job_id=job_id,
                title=title,
                company=company,
                city=city, 
                salary_raw=salary,
                detail_url=link,
                raw_data=str(item)[:200]
            )
        except Exception as e:
            # 单个解析失败不影响整体
            return None