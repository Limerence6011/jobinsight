import json
import logging
import time
import random
import re
from typing import Iterator, Dict, Any, Optional
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from jobinsight.crawler.base import BaseAdapter, JobPost as Job 

logger = logging.getLogger(__name__)

class Job51Adapter(BaseAdapter):
    """
    前程无忧 (51job) 适配器 - UI 交互翻页版
    """

    def __init__(self, client=None):
        self.client = client
        self.base_url = "https://we.51job.com/pc/search"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        # 城市编码映射表
        self.city_map = {
            "全国": "000000", "上海": "020000", "北京": "010000", "广州": "030200", "深圳": "040000",
            "武汉": "180200", "西安": "200200", "杭州": "080200", "南京": "070200", "成都": "090200",
            "重庆": "060000", "天津": "050000", "苏州": "070300", "长沙": "190200", "大连": "230300",
            "济南": "120200", "青岛": "120300", "郑州": "170200", "东莞": "030800", "福州": "110200",
            "宁波": "080300", "合肥": "150200", "哈尔滨": "220200", "长春": "240200", "石家庄": "160200",
            "昆明": "250200", "贵阳": "260200", "南昌": "130200", "无锡": "070400", "佛山": "030600"
        }

    def _get_city_code(self, city_name: str) -> str:
        if not city_name: return ""
        for k, v in self.city_map.items():
            if k in city_name: return v
        return ""

    def _build_url(self, keyword: str, city: str = None) -> str:
        # 注意：这里不再依赖 page 参数拼 URL，因为 URL 参数可能无效
        # 我们只通过 URL 进入第一页，然后通过 UI 操作翻页
        city_code = self._get_city_code(city)
        params = {
            "keyword": keyword,
            "searchType": 2,
            "sortType": 0,
            "metro": "",
            "jobArea": city_code
        }
        return f"{self.base_url}?{urlencode(params)}"

    def fetch(self, keyword: str, city: str = None, page: int = 1, **kwargs) -> str:
        # 构建基础 URL (始终是第 1 页状态)
        url = self._build_url(keyword, city)
        logger.info(f"[Job51] 启动 Playwright: {url} (目标: 第 {page} 页)")
        
        result_payload = ""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent=random.choice(self.user_agents)
                )
                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
                
                page_obj = context.new_page()
                page_obj.goto(url)
                
                # 等待首屏加载
                try:
                    page_obj.wait_for_load_state("networkidle", timeout=10000)
                except:
                    pass

                # === 核心修复：UI 交互翻页 ===
                if page > 1:
                    logger.info(f"[Job51] 正在执行 UI 翻页操作，目标页码: {page}")
                    
                    # 1. 滚动到底部让分页条可见
                    page_obj.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)

                    # 2. 尝试找到 "跳转到" 输入框 (最快方式)
                    # 51job 的输入框通常在 .el-pagination__jump 或类似结构中
                    jump_success = False
                    try:
                        input_box = page_obj.locator(".el-pagination__jump input, input.el-input__inner").first
                        if input_box.is_visible():
                            input_box.fill(str(page))
                            input_box.press("Enter")
                            logger.info(f"[Job51] 已使用输入框跳转到第 {page} 页")
                            jump_success = True
                    except Exception as e:
                        logger.warning(f"[Job51] 输入框跳转失败: {e}")

                    # 3. 如果输入框失败，尝试点击 "下一页" 按钮 (逐页点击)
                    # 注意：fetch 是无状态的，每次打开都是第1页，所以要点击 (page-1) 次
                    if not jump_success:
                        logger.info(f"[Job51] 尝试点击 '下一页' 按钮 {page-1} 次")
                        next_btn = page_obj.locator("button.btn-next, li.next, .btn-next").first
                        if next_btn.is_visible():
                            for i in range(page - 1):
                                next_btn.click()
                                time.sleep(1.5) # 每次点击后稍作等待
                            logger.info("[Job51] 点击翻页完成")
                        else:
                            logger.warning("[Job51] 未找到 '下一页' 按钮，可能只有一页或选择器失效")

                    # 4. 再次等待数据加载
                    time.sleep(3) 
                    try:
                        page_obj.wait_for_load_state("networkidle", timeout=5000)
                    except:
                        pass

                # === 数据获取 ===
                # 如果进行了翻页操作，window.__SEARCH_RESULT__ 可能还是旧的 (Page 1)，
                # 所以如果是翻页后，我们强制使用 HTML 解析，不读内存 JSON，防止数据重复。
                
                if page == 1:
                    # 第1页尝试获取 JSON (速度快)
                    json_data = page_obj.evaluate("""
                        window.__SEARCH_RESULT__ ? JSON.stringify(window.__SEARCH_RESULT__) : null
                    """)
                    if json_data and len(json_data) > 100:
                        result_payload = "JSON_PREFIX:" + json_data
                    else:
                        result_payload = page_obj.content()
                else:
                    # 第N页直接获取渲染后的 HTML (最稳妥)
                    logger.info("[Job51] 翻页后直接获取 HTML 源码")
                    result_payload = page_obj.content()
                
                browser.close()
        except Exception as e:
            logger.error(f"[Job51] Playwright error: {e}")
            return ""
        return result_payload

    def parse(self, content: str) -> Iterator[Job]:
        if not content: return

        if content.startswith("JSON_PREFIX:"):
            logger.info("[Job51] JSON 解析模式")
            try:
                data = json.loads(content.replace("JSON_PREFIX:", "", 1))
                job_list = data.get('engine_search_result', []) or data.get('job_search_result', [])
                for item in job_list:
                    yield self._parse_json_item(item)
            except Exception as e:
                logger.error(f"[Job51] JSON Error: {e}")
        else:
            logger.info("[Job51] HTML 解析模式")
            soup = BeautifulSoup(content, 'lxml')
            
            job_items = soup.select(".j_joblist > div") or \
                        soup.select(".joblist-item") or \
                        soup.select("div[class*='joblist'] > div")
            
            logger.info(f"[Job51] 解析到 {len(job_items)} 个 DOM 元素")
            
            for item in job_items:
                job = self._parse_dom_item(item)
                if job:
                    yield job

    def _parse_json_item(self, item: Dict[str, Any]) -> Job:
        edu_list = item.get('attribute_text', [])
        education = edu_list[0] if len(edu_list) > 0 else ""
        experience = edu_list[1] if len(edu_list) > 1 else ""
        
        return Job(
            platform="51job",
            job_id=str(item.get('jobid', '')),
            title=item.get('job_name', ''),
            company=item.get('coname', ''),
            city=item.get('workarea_text', ''),
            salary_raw=item.get('providesalary_text', ''),
            detail_url=item.get('job_href', ''),
            education=education,
            education_raw=education,
            experience=experience,
            exp_raw=experience,
            description=None,
            pub_date=item.get('updatedate', ''),
            raw_data=json.dumps(item, ensure_ascii=False)
        )

    def _parse_dom_item(self, item) -> Optional[Job]:
        try:
            def safe_text(elem): return elem.get_text(strip=True) if elem else ""

            # 1. 标题
            title_elem = item.select_one(".jname") or item.select_one(".title") or item.select_one("span[title]")
            title = safe_text(title_elem)
            if not title: return None

            # 2. 链接与 ID
            link = ""
            job_id = ""
            a_tag = item.select_one("a")
            if a_tag:
                link = a_tag.get('href', '')
                match = re.search(r'/([^/]+)\.html', link)
                if match:
                    job_id = match.group(1)

            # 3. 公司
            company = safe_text(item.select_one(".cname") or item.select_one(".company"))

            # 4. 薪资
            salary = safe_text(item.select_one(".sal") or item.select_one(".salary"))

            # 5. 混合信息
            info_text = safe_text(item.select_one(".info") or item.select_one(".d") or item.select_one(".sensor"))
            
            city = ""
            edu_raw = ""
            exp_raw = ""
            
            if info_text:
                parts = [p.strip() for p in info_text.split('|')]
                if len(parts) >= 1: city = parts[0]
                if len(parts) >= 2: exp_raw = parts[1]
                if len(parts) >= 3: edu_raw = parts[2]
            
            if not city:
                 city = safe_text(item.select_one(".area"))

            return Job(
                platform="51job",
                job_id=job_id,
                title=title,
                company=company,
                city=city,
                salary_raw=salary,
                detail_url=link,
                education_raw=edu_raw,
                exp_raw=exp_raw,
                description=None,
                raw_data=str(item)[:100]
            )
        except Exception as e:
            return None