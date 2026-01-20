# 前程无忧51job平台适配器（仅作学习交流使用）

from __future__ import annotations
import re
import time
import json
import urllib.parse
from typing import Iterable, Optional, Dict
from bs4 import BeautifulSoup
from ...base import JobPost, now_iso
from ....utils.http import HttpClient
from ....utils.log import get_logger

logger = get_logger(__name__)

# 城市编码映射（部分主要城市）
CITY_CODE_MAP = {
    "全国": "000000",
    "北京": "010000",
    "上海": "020000",
    "广州": "030200",
    "深圳": "030300",
    "杭州": "080200",
    "南京": "070200",
    "成都": "090200",
    "武汉": "180200",
    "西安": "200200",
    "苏州": "070300",
    "天津": "050000",
    "重庆": "060000",
    "青岛": "120300",
    "大连": "230200",
    "宁波": "080300",
    "厦门": "090300",
    "长沙": "190200",
    "郑州": "170200",
    "济南": "120200",
    "合肥": "150200",
    "福州": "090400",
    "无锡": "070400",
    "佛山": "030400",
    "东莞": "030500",
    "石家庄": "160200",
    "哈尔滨": "220200",
    "长春": "240200",
    "沈阳": "230300",
    "昆明": "250200",
    "南昌": "130200",
    "南宁": "140200",
    "太原": "260200",
    "贵阳": "270200",
    "海口": "280200",
    "兰州": "290200",
    "银川": "300200",
    "西宁": "310200",
    "乌鲁木齐": "320200",
    "拉萨": "330200",
}

# 区县编码映射（示例，可根据需要扩展）
REGION_CODE_MAP = {
    "不限": "000000",
    # 北京
    "海淀区": "010100",
    "朝阳区": "010200",
    "西城区": "010300",
    "东城区": "010400",
    # 上海
    "浦东新区": "020100",
    "黄浦区": "020200",
    "徐汇区": "020300",
    "长宁区": "020400",
    # 可以继续添加其他城市的区县
}

class Job51Adapter:
    """
    前程无忧51job平台适配器
    
    NOTE: 仅作学习交流使用，需要授权和合规处理
    """
    platform = "job51"
    
    def __init__(self, client: Optional[HttpClient] = None):
        self.client = client or HttpClient()
    
    def _get_city_code(self, city: Optional[str]) -> str:
        """获取城市编码"""
        if not city or city == "全国" or city == "不限":
            return "000000"
        # 尝试精确匹配
        city_code = CITY_CODE_MAP.get(city)
        if city_code:
            return city_code
        # 尝试模糊匹配（去除可能的"市"后缀）
        city_clean = city.replace('市', '').replace('省', '')
        city_code = CITY_CODE_MAP.get(city_clean)
        if city_code:
            return city_code
        # 尝试包含匹配（如"上海"匹配"上海市"）
        for key, code in CITY_CODE_MAP.items():
            if city in key or key in city:
                return code
        logger.warning(f"未找到城市编码: {city}，将使用默认编码000000")
        return "000000"  # 返回默认值
    
    def _get_region_code(self, region: Optional[str]) -> str:
        """获取区县编码"""
        if not region or region == "不限":
            return "000000"
        region_code = REGION_CODE_MAP.get(region)
        if not region_code:
            return "000000"
        return region_code
    
    def _build_search_url(self, keyword: str, city: Optional[str] = None, 
                         region: Optional[str] = None, page: int = 1) -> str:
        """
        构建搜索URL
        
        支持两种URL格式：
        1. 新版：https://we.51job.com/pc/search (推荐)
        2. 旧版：https://search.51job.com/list/... (备用)
        """
        # 优先使用新版URL格式
        base_url = "https://we.51job.com/pc/search"
        
        # 构建查询参数
        params = {
            'keyword': keyword,
            'page': str(page)
        }
        
        # 添加城市参数（新版可能支持城市编码或城市名称）
        if city and city != "全国" and city != "不限":
            city_code = self._get_city_code(city)
            if city_code != "000000":
                # 尝试同时添加城市编码和城市名称（某些API可能支持）
                params['city'] = city_code
                params['cityName'] = city
            else:
                # 如果找不到编码，直接使用城市名称
                params['city'] = city
                params['cityName'] = city
        
        # 添加区县参数（仅在指定城市时有效）
        if region and region != "不限" and city and city != "全国":
            region_code = self._get_region_code(region)
            if region_code != "000000":
                params['region'] = region_code
        
        # 构建完整URL
        query_string = urllib.parse.urlencode(params, encoding='utf-8')
        url = f"{base_url}?{query_string}"
        
        return url
    
    def fetch(self, keyword: str, city: Optional[str] = None, 
             region: Optional[str] = None, page: int = 1) -> str:
        """
        获取51job搜索结果
        
        优先尝试API接口，如果失败则尝试HTML页面
        
        Args:
            keyword: 搜索关键词
            city: 城市名称
            region: 区县名称
            page: 页码（从1开始）
        
        Returns:
            JSON或HTML内容
        """
        # 方法1: 尝试使用API接口（推荐）
        api_url = self._build_api_url(keyword, city, region, page)
        if api_url:
            try:
                uuid = self._get_uuid()
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Referer": "https://we.51job.com/pc/search",
                    "From-Domain": "51job_web",
                    "uuid": uuid,
                    "partner": "www_google_com",
                }
                
                logger.info(f"尝试API接口: {api_url[:100]}...")
                response = self.client.get(api_url, headers=headers)
                
                # 检查响应类型
                content_type = response.headers.get('Content-Type', '')
                response_text = response.text
                
                logger.debug(f"API响应类型: {content_type}")
                logger.debug(f"API响应长度: {len(response_text)} 字符")
                logger.debug(f"API响应预览: {response_text[:300]}")
                
                if 'application/json' in content_type:
                    try:
                        data = response.json()
                        status = data.get('status')
                        logger.debug(f"API响应status: {status}")
                        if status == '1':  # 成功
                            logger.info("API接口请求成功")
                            return json.dumps(data, ensure_ascii=False)
                        else:
                            logger.warning(f"API返回失败状态: {data.get('message', '未知错误')}")
                    except json.JSONDecodeError as e:
                        logger.debug(f"API响应JSON解析失败: {e}")
                        logger.debug(f"响应内容: {response_text[:500]}")
                else:
                    # 可能是反爬虫页面
                    logger.warning("API返回非JSON响应，可能是反爬虫页面或需要签名")
                    logger.debug(f"响应内容: {response_text[:500]}")
            except Exception as e:
                logger.debug(f"API请求失败: {e}")
        
        # 方法2: 尝试使用旧版search.51job.com的URL（可能更稳定）
        old_url = self._build_old_search_url(keyword, city, region, page)
        if old_url:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Referer": "https://www.51job.com/",
                }
                logger.info(f"尝试旧版URL: {old_url}")
                response = self.client.get(old_url, headers=headers)
                html_content = response.text
                # 检查是否包含职位列表
                if 'j_joblist' in html_content or 'el' in html_content:
                    logger.info("使用旧版URL成功获取数据")
                    return html_content
            except Exception as e:
                logger.debug(f"旧版URL请求失败: {e}")
        
        # 方法3: 使用新版we.51job.com的HTML页面
        url = self._build_search_url(keyword, city, region, page)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://we.51job.com/",
        }
        
        try:
            logger.info(f"请求URL: {url}")
            response = self.client.get(url, headers=headers)
            return response.text
        except Exception as e:
            logger.error(f"获取51job数据失败: {e}")
            raise
    
    def _build_old_search_url(self, keyword: str, city: Optional[str] = None,
                              region: Optional[str] = None, page: int = 1) -> Optional[str]:
        """
        构建旧版search.51job.com的URL格式
        
        格式: https://search.51job.com/list/<city_code>,<region_code>,0000,00,9,99,<keyword>,2,<page>.html
        """
        city_code = self._get_city_code(city)
        region_code = self._get_region_code(region) if region else "000000"
        
        # URL编码关键词（使用GBK编码）
        keyword_encoded = urllib.parse.quote(keyword.encode('gbk'))
        
        # 构建URL
        url = f"https://search.51job.com/list/{city_code},{region_code},0000,00,9,99,{keyword_encoded},2,{page}.html"
        return url
    
    def _build_api_url(self, keyword: str, city: Optional[str] = None,
                      region: Optional[str] = None, page: int = 1) -> Optional[str]:
        """
        构建API接口URL
        
        根据HAR文件分析，实际API接口为：
        https://we.51job.com/api/job/search-pc
        
        注意：新版本API可能需要签名验证，如果直接调用失败，会回退到HTML解析
        
        参数说明：
        - api_key: 固定值 "51job"
        - timestamp: 时间戳
        - keyword: 搜索关键词
        - searchType: 搜索类型，2表示职位搜索
        - jobArea: 城市编码
        - pageNum: 页码
        - pageSize: 每页数量
        - sortType: 排序方式，0=默认
        - pageCode: 页面代码，固定值 "sou|sou|soulb"
        - scene: 场景，固定值 7
        """
        import time
        base_url = "https://we.51job.com/api/job/search-pc"
        
        # 获取时间戳
        timestamp = int(time.time() * 1000)  # 使用毫秒时间戳
        
        params = {
            'api_key': '51job',
            'timestamp': str(timestamp),
            'keyword': keyword or '',
            'searchType': '2',  # 2表示职位搜索
            'function': '',
            'industry': '',
            'jobArea': self._get_city_code(city) if city and city != "全国" and city != "不限" else '',
            'jobArea2': '',
            'landmark': '',
            'metro': '',
            'salary': '',
            'workYear': '',
            'degree': '',
            'companyType': '',
            'companySize': '',
            'jobType': '',
            'issueDate': '',
            'sortType': '0',  # 0=默认排序
            'pageNum': str(page),
            'requestId': '',
            'pageSize': '50',  # 每页50条（增加获取数量）
            'source': '1',
            'accountId': '',
            'pageCode': 'sou|sou|soulb',
            'scene': '7',
        }
        
        query_string = urllib.parse.urlencode(params, encoding='utf-8')
        return f"{base_url}?{query_string}"
    
    def _generate_sign(self, params: Dict[str, str], uuid: str = "") -> str:
        """
        生成API请求签名
        
        注意：根据HAR文件，API需要sign签名，但签名算法可能比较复杂
        暂时返回空字符串，如果API返回错误，可能需要实现签名算法
        """
        # TODO: 实现签名算法（如果需要）
        # 从HAR文件看，sign是一个SHA256哈希值
        # 暂时返回空，让API请求失败后使用HTML方式
        return ""
    
    def _get_uuid(self) -> str:
        """
        生成UUID（设备ID）
        
        从HAR文件看，uuid是一个32位的十六进制字符串
        可以生成一个固定的UUID或随机生成
        """
        import uuid
        # 生成一个固定的UUID（基于机器和进程）
        return str(uuid.uuid4()).replace('-', '')[:32]
    
    def _parse_salary(self, salary_text: str) -> str:
        """解析薪资文本"""
        if not salary_text or salary_text.strip() == "":
            return ""
        # 清理薪资文本
        salary_text = salary_text.strip()
        # 移除常见的无用字符
        salary_text = re.sub(r'\s+', '', salary_text)
        return salary_text
    
    def _parse_education(self, edu_text: str) -> str:
        """解析学历要求"""
        if not edu_text:
            return ""
        edu_text = edu_text.strip()
        # 标准化学历表述
        edu_map = {
            "初中及以下": "初中",
            "高中": "高中",
            "中专": "高中",
            "大专": "大专",
            "本科": "本科",
            "硕士": "硕士",
            "博士": "博士",
        }
        for key, value in edu_map.items():
            if key in edu_text:
                return value
        return edu_text
    
    def _parse_experience(self, exp_text: str) -> str:
        """解析工作经验"""
        if not exp_text:
            return ""
        exp_text = exp_text.strip()
        # 标准化经验表述
        if "不限" in exp_text or "无要求" in exp_text:
            return "不限"
        return exp_text
    
    def _parse_api_item(self, item: Dict) -> JobPost:
        """
        解析API返回的JSON格式职位数据
        
        根据实际API响应结构提取字段：
        - jobId: 职位ID
        - jobName: 职位名称
        - companyName: 公司名称
        - jobAreaString: 工作地点
        - provideSalaryString: 薪资
        - workYearString: 工作经验
        - degreeString: 学历要求
        - jobHref: 职位链接
        - jobTags: 职位标签
        - jobDescribe: 职位描述
        
        Args:
            item: API返回的职位数据字典
        
        Returns:
            JobPost对象
        """
        # 提取基本字段
        job_id = str(item.get('jobId', ''))
        title = str(item.get('jobName', '')).strip()
        company = str(item.get('companyName', '')).strip()
        city = str(item.get('jobAreaString', '')).strip()
        salary_raw = self._parse_salary(str(item.get('provideSalaryString', '')))
        education_raw = self._parse_education(str(item.get('degreeString', '')))
        exp_raw = self._parse_experience(str(item.get('workYearString', '')))
        detail_url = str(item.get('jobHref', '')).strip()
        description = str(item.get('jobDescribe', '')).strip()
        
        # 提取标签
        tags = []
        job_tags = item.get('jobTags', [])
        if isinstance(job_tags, list):
            tags = [str(tag) for tag in job_tags if tag]
        
        # 如果没有job_id，尝试从URL中提取
        if not job_id and detail_url:
            job_id_match = re.search(r'/(\d+)\.html', detail_url)
            if job_id_match:
                job_id = job_id_match.group(1)
        
        # 生成job_id（如果还是没有）
        if not job_id:
            job_id = f"{title}_{company}".replace(' ', '_').replace('/', '_')[:50]
        
        # 处理URL（确保是完整URL）
        if detail_url and not detail_url.startswith('http'):
            if detail_url.startswith('//'):
                detail_url = 'https:' + detail_url
            elif detail_url.startswith('/'):
                detail_url = 'https://jobs.51job.com' + detail_url
            else:
                detail_url = 'https://jobs.51job.com/' + detail_url
        
        return JobPost(
            platform=self.platform,
            job_id=job_id[:128],
            title=title[:256] if title else "未知职位",
            company=company[:256] if company else "未知公司",
            city=city[:128] if city else "Unknown",
            salary_raw=salary_raw[:128],
            education_raw=education_raw,
            exp_raw=exp_raw,
            tags=tags[:20],
            detail_url=detail_url,
            description=description[:5000] if description else "",
            crawl_time=now_iso(),
        )
    
    def parse(self, payload: str) -> Iterable[JobPost]:
        """
        解析51job搜索结果
        
        支持JSON API响应和HTML页面解析
        
        Args:
            payload: HTML或JSON内容
        
        Returns:
            JobPost迭代器
        """
        # 方法1: 尝试解析JSON响应（API接口）
        try:
            data = json.loads(payload)
            if isinstance(data, dict):
                # 检查是否是API响应格式
                status = data.get('status')
                if status == '1':  # 成功
                    resultbody = data.get('resultbody', {})
                    job_data = resultbody.get('job', {})
                    items = job_data.get('items', [])
                    
                    if isinstance(items, list) and len(items) > 0:
                        logger.info(f"从API响应解析到 {len(items)} 个职位")
                        for item in items:
                            yield self._parse_api_item(item)
                        return
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.debug(f"JSON解析失败: {e}")
            pass
        
        # 方法2: 解析HTML页面
        soup = BeautifulSoup(payload, 'html.parser')
        
        # 查找职位列表容器 - 针对we.51job.com的新页面结构
        job_list = []
        
        # 策略1: 查找所有包含职位链接的元素（最可靠的方法）
        # we.51job.com的职位链接可能格式：/we/job/xxx.html 或 /jobs/xxx.html
        job_links = soup.find_all('a', href=re.compile(r'/we/job/|/jobs/|/job/|/position/|jobId=|jobid=', re.I))
        if job_links:
            logger.debug(f"找到 {len(job_links)} 个职位相关链接")
            # 过滤掉导航链接（如APP下载、首页等）
            filtered_links = []
            for link in job_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                # 排除明显的导航链接
                if not re.search(r'app|download|首页|登录|注册', href + text, re.I):
                    filtered_links.append(link)
            
            if filtered_links:
                logger.debug(f"过滤后剩余 {len(filtered_links)} 个职位链接")
                # 找到包含这些链接的父容器（通常是职位项）
                seen_parents = set()
                for link in filtered_links:
                    # 向上查找包含职位信息的父容器
                    parent = link.find_parent(['div', 'li', 'article', 'section'])
                    if parent:
                        parent_id = id(parent)
                        if parent_id not in seen_parents:
                            seen_parents.add(parent_id)
                            job_list.append(parent)
                if job_list:
                    logger.debug(f"通过链接找到 {len(job_list)} 个职位项")
        
        # 策略2: 如果策略1失败，尝试CSS选择器
        # 优先尝试旧版search.51job.com的类名
        if not job_list:
            selectors = [
                # 旧版search.51job.com的类名（优先）
                'div.el',  # 最常见的职位项类名
                'div[class="el"]',  # 精确匹配
                'div.j_joblist',  # 职位列表容器
                'div.job_item',
                # we.51job.com可能使用的类名
                'div[class*="job-card"]',
                'div[class*="jobCard"]',
                'div[class*="job-item"]',
                'div[class*="jobItem"]',
                'div[class*="position-item"]',
                'div[class*="positionItem"]',
                'div[class*="job-list-item"]',
                'div[class*="search-item"]',
                'div[class*="result-item"]',
                'div[class*="job"]',
                'div[class*="item"]',
                'div[class*="card"]',
                'div[role="listitem"]',
                'div[data-testid*="job"]',
                'div[data-id]',  # 可能包含职位ID
            ]
            
            for selector in selectors:
                try:
                    candidates = soup.select(selector)
                    if candidates:
                        # 过滤：只保留看起来像职位项的div
                        filtered = [elem for elem in candidates 
                                  if elem.find('a', href=re.compile(r'/jobs/|/job/|/we/|/position/'))
                                  or '职位' in elem.get_text() 
                                  or '公司' in elem.get_text()
                                  or '薪资' in elem.get_text()
                                  or '工作' in elem.get_text()]
                        if filtered:
                            job_list = filtered
                            logger.debug(f"使用选择器找到职位列表: {selector}, 数量: {len(job_list)}")
                            break
                except Exception as e:
                    logger.debug(f"选择器 {selector} 失败: {e}")
                    continue
        
        # 如果CSS选择器失败，尝试find_all
        if not job_list:
            # 查找包含职位链接的div容器
            job_links = soup.find_all('a', href=re.compile(r'/jobs/|/job/|/we/'))
            if job_links:
                # 找到包含这些链接的父容器
                seen = set()
                for link in job_links:
                    parent = link.find_parent('div')
                    if parent and id(parent) not in seen:
                        seen.add(id(parent))
                        job_list.append(parent)
        
        # 如果还是找不到，尝试更通用的方法
        if not job_list:
            # 查找所有包含职位相关文本的div
            job_list = soup.find_all('div', class_=re.compile(r'job|item|card|list', re.I))
            # 过滤：只保留包含职位链接或职位相关文本的div
            job_list = [elem for elem in job_list 
                       if elem.find('a', href=re.compile(r'/jobs/|/job/|/we/')) 
                       or '职位' in elem.get_text() 
                       or '公司' in elem.get_text()]
        
        if not job_list:
            logger.warning("未找到职位列表，可能页面结构已变化或需要登录")
            # 输出部分HTML用于调试
            if len(payload) > 0:
                logger.debug("页面长度: %d 字符", len(payload))
                # 保存部分HTML到日志（前2000字符）
                logger.debug("页面内容预览: %s", payload[:2000])
                # 尝试查找所有可能的职位相关元素
                all_links = soup.find_all('a', href=True)
                job_related_links = [link for link in all_links 
                                    if re.search(r'job|position|职位|岗位', link.get('href', ''), re.I) 
                                    or re.search(r'job|position|职位|岗位', link.get_text(), re.I)]
                if job_related_links:
                    logger.debug(f"找到 {len(job_related_links)} 个可能的职位相关链接")
                    logger.debug("示例链接: %s", job_related_links[0].get('href') if job_related_links else '')
            return
        
        for job_elem in job_list:
            try:
                # 提取职位标题和链接 - 针对we.51job.com的新结构
                title_elem = None
                title = ""
                detail_url = ""
                
                # 提取职位标题和链接 - 多重策略
                title_elem = None
                title = ""
                detail_url = ""
                
                # 策略1: 查找包含职位链接的a标签（最可靠）
                title_elem = job_elem.find('a', href=re.compile(r'/jobs/|/job/|/we/|/position/|jobId=|jobid=', re.I))
                
                # 策略2: 查找包含data属性或特定类名的链接
                if not title_elem:
                    title_elem = job_elem.find('a', attrs={'data-testid': re.compile(r'job|title', re.I)})
                
                # 策略3: 如果job_elem本身就是a标签
                if not title_elem and job_elem.name == 'a' and job_elem.get('href'):
                    href = job_elem.get('href', '')
                    if re.search(r'/jobs/|/job/|/we/|/position/|jobId=|jobid=', href, re.I):
                        title_elem = job_elem
                
                # 策略4: 查找包含title/name/job类的a标签
                if not title_elem:
                    title_elem = job_elem.find('a', class_=re.compile(r'title|name|job|position', re.I))
                
                # 策略5: 查找任何包含文本的a标签
                if not title_elem:
                    title_elem = job_elem.find('a')
                
                # 策略6: 如果没有a标签，尝试从其他元素提取标题
                if not title_elem:
                    # 查找包含职位名称的span、div、h标签等元素
                    title_elem = (job_elem.find('span', class_=re.compile(r'title|name|job|position', re.I)) or
                                 job_elem.find('div', class_=re.compile(r'title|name|job|position', re.I)) or
                                 job_elem.find('h1') or job_elem.find('h2') or 
                                 job_elem.find('h3') or job_elem.find('h4') or
                                 job_elem.find('p', class_=re.compile(r'title|name', re.I)))
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    # 如果是a标签，提取链接
                    if title_elem.name == 'a':
                        detail_url = title_elem.get('href', '')
                    else:
                        # 如果不是a标签，尝试在同级或父级查找链接
                        link_elem = job_elem.find('a', href=re.compile(r'/jobs/|/job/|/we/|/position/|jobId=|jobid=', re.I))
                        if link_elem:
                            detail_url = link_elem.get('href', '')
                
                # 如果还是没有标题，尝试从job_elem的直接文本中提取
                if not title:
                    # 获取所有文本，取第一行作为标题
                    all_text = job_elem.get_text(separator='\n', strip=True)
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    if lines:
                        title = lines[0]
                
                if not title:
                    # 如果还是找不到标题，跳过
                    continue
                
                # 处理URL
                if detail_url:
                    if not detail_url.startswith('http'):
                        if detail_url.startswith('//'):
                            detail_url = 'https:' + detail_url
                        elif detail_url.startswith('/'):
                            detail_url = 'https://we.51job.com' + detail_url
                        else:
                            detail_url = 'https://we.51job.com/' + detail_url
                elif not detail_url and title:
                    # 如果没有找到URL，尝试从job_elem中查找任何链接
                    any_link = job_elem.find('a', href=True)
                    if any_link:
                        detail_url = any_link.get('href', '')
                        if detail_url and not detail_url.startswith('http'):
                            if detail_url.startswith('//'):
                                detail_url = 'https:' + detail_url
                            elif detail_url.startswith('/'):
                                detail_url = 'https://we.51job.com' + detail_url
                
                # 提取公司名称 - 支持多种选择器
                company = ""
                company_selectors = [
                    ('a', re.compile(r'company|com|corp', re.I)),
                    ('span', re.compile(r'company|com|corp', re.I)),
                    ('div', re.compile(r'company|com|corp', re.I)),
                    ('p', re.compile(r'company|com', re.I)),
                ]
                for tag, pattern in company_selectors:
                    company_elem = job_elem.find(tag, class_=pattern)
                    if company_elem:
                        company = company_elem.get_text(strip=True)
                        break
                
                # 如果还是找不到，尝试查找包含"公司"文本的元素
                if not company:
                    all_text = job_elem.get_text()
                    # 简单的启发式方法：查找公司名称（通常在职位名称之后）
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    for i, line in enumerate(lines):
                        if title in line and i + 1 < len(lines):
                            company = lines[i + 1]
                            break
                
                # 提取工作地点
                # 旧版search.51job.com: span.d.at 或类似结构
                city = ""
                location_selectors = [
                    ('span', re.compile(r'd\.at|area|city|location|address|place', re.I)),  # 旧版常用d.at
                    ('div', re.compile(r'area|city|location|address|place', re.I)),
                    ('p', re.compile(r'area|city|location', re.I)),
                ]
                for tag, pattern in location_selectors:
                    city_elem = job_elem.find(tag, class_=pattern)
                    if city_elem:
                        city = city_elem.get_text(strip=True)
                        break
                
                # 提取薪资
                # 旧版search.51job.com: span.sal
                salary_raw = ""
                salary_selectors = [
                    ('span', re.compile(r'sal|salary|money|pay|wage', re.I)),  # 旧版常用sal
                    ('div', re.compile(r'salary|money|pay|wage', re.I)),
                    ('p', re.compile(r'salary|money', re.I)),
                ]
                for tag, pattern in salary_selectors:
                    salary_elem = job_elem.find(tag, class_=pattern)
                    if salary_elem:
                        salary_raw = self._parse_salary(salary_elem.get_text(strip=True))
                        break
                
                # 提取学历要求
                education_raw = ""
                edu_selectors = [
                    ('span', re.compile(r'edu|education|degree', re.I)),
                    ('div', re.compile(r'edu|education|degree', re.I)),
                ]
                for tag, pattern in edu_selectors:
                    edu_elem = job_elem.find(tag, class_=pattern)
                    if edu_elem:
                        education_raw = self._parse_education(edu_elem.get_text(strip=True))
                        break
                
                # 提取工作经验
                exp_raw = ""
                exp_selectors = [
                    ('span', re.compile(r'exp|experience|work|year', re.I)),
                    ('div', re.compile(r'exp|experience|work|year', re.I)),
                ]
                for tag, pattern in exp_selectors:
                    exp_elem = job_elem.find(tag, class_=pattern)
                    if exp_elem:
                        exp_raw = self._parse_experience(exp_elem.get_text(strip=True))
                        break
                
                # 提取职位描述（可能在不同位置）
                desc_elem = job_elem.find('div', class_=re.compile(r'desc|description|info'))
                if not desc_elem:
                    desc_elem = job_elem.find('p', class_=re.compile(r'desc|description|info'))
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # 提取标签/技能（可能在描述中或单独标签）
                tags = []
                tag_elems = job_elem.find_all('span', class_=re.compile(r'tag|skill|label'))
                for tag_elem in tag_elems:
                    tag_text = tag_elem.get_text(strip=True)
                    if tag_text:
                        tags.append(tag_text)
                
                # 如果没有找到标签，尝试从描述中提取
                if not tags and description:
                    # 简单的关键词提取（可以根据需要改进）
                    common_skills = ['Python', 'Java', 'JavaScript', 'SQL', 'Linux', 'MySQL', 
                                   'Docker', 'Kubernetes', 'React', 'Vue', 'Spring', 'Django']
                    for skill in common_skills:
                        if skill.lower() in description.lower():
                            tags.append(skill)
                
                # 生成job_id（使用URL或标题+公司名）
                job_id = ""
                if detail_url:
                    # 尝试从URL中提取ID
                    job_id_match = re.search(r'/(?:jobs|job|we|position)/(\d+)', detail_url)
                    if job_id_match:
                        job_id = job_id_match.group(1)
                    else:
                        # 从URL中提取其他唯一标识
                        job_id_match = re.search(r'/([^/]+)\.html', detail_url)
                        if job_id_match:
                            job_id = job_id_match.group(1)
                
                if not job_id:
                    # 使用标题+公司名生成ID
                    job_id = f"{title}_{company}".replace(' ', '_').replace('/', '_')[:50]
                    if not job_id:
                        job_id = f"{title}_{company}_{city}".replace(' ', '_').replace('/', '_')[:50]
                
                # 清理数据
                if not title:
                    continue
                
                # 如果没有公司名，尝试从其他位置提取或使用默认值
                if not company:
                    company = "未知公司"
                
                yield JobPost(
                    platform=self.platform,
                    job_id=str(job_id),
                    title=title[:256],
                    company=company[:256],
                    city=city[:128] if city else "Unknown",
                    salary_raw=salary_raw[:128],
                    education_raw=education_raw,
                    exp_raw=exp_raw,
                    tags=tags[:20],  # 限制标签数量
                    detail_url=detail_url,
                    description=description[:5000] if description else "",  # 限制描述长度
                    crawl_time=now_iso(),
                )
            except Exception as e:
                logger.warning(f"解析职位信息失败: {e}")
                continue
