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
        # job51 平台不使用 HttpClient，直接使用 Playwright，无需代理
        self.client = client
        self.base_url = "https://we.51job.com/pc/search"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
 # 51job 城市编码全量表 (按省份区域划分)
        self.city_map = {
            # === 直辖市 & 特别行政区 ===
            "全国": "000000",
            "北京": "010000", 
            "上海": "020000", 
            "天津": "050000", 
            "重庆": "060000",
            "香港": "360000", 
            "澳门": "370000", 
            "台湾": "380000", # 注意：台湾省在51job通常归类较特殊，以此为准

            # === 广东省 (03xxxx / 深圳单独 040000) ===
            "广州": "030200", "深圳": "040000", "珠海": "030500", "汕头": "030400",
            "韶关": "031200", "佛山": "030600", "江门": "030900", "湛江": "031000",
            "茂名": "031400", "肇庆": "031100", "惠州": "030300", "梅州": "031500",
            "汕尾": "031900", "河源": "031800", "阳江": "031700", "清远": "031600",
            "东莞": "030800", "中山": "030700", "潮州": "031300", "揭阳": "032000",
            "云浮": "032100",

            # === 江苏省 (07xxxx) ===
            "南京": "070200", "无锡": "070400", "徐州": "070700", "常州": "070500",
            "苏州": "070300", "南通": "070800", "连云港": "071200", "淮安": "071100",
            "盐城": "071300", "扬州": "070600", "镇江": "070900", "泰州": "071000",
            "宿迁": "071400", "昆山": "071500", # 昆山虽是县级市，但51job常单列

            # === 浙江省 (08xxxx) ===
            "杭州": "080200", "宁波": "080300", "温州": "080400", "嘉兴": "080500",
            "湖州": "080800", "绍兴": "080600", "金华": "080700", "衢州": "081000",
            "舟山": "081100", "台州": "080900", "丽水": "081200",

            # === 安徽省 (15xxxx) ===
            "合肥": "150200", "芜湖": "150300", "蚌埠": "150400", "淮南": "150500",
            "马鞍山": "150600", "淮北": "150700", "铜陵": "150800", "安庆": "150900",
            "黄山": "151000", "滁州": "151100", "阜阳": "151200", "宿州": "151300",
            "六安": "151400", "亳州": "151500", "池州": "151600", "宣城": "151700",

            # === 福建省 (11xxxx) ===
            "福州": "110200", "厦门": "110300", "莆田": "110600", "三明": "110700",
            "泉州": "110400", "漳州": "110500", "南平": "110800", "龙岩": "110900",
            "宁德": "111000",

            # === 江西省 (13xxxx) ===
            "南昌": "130200", "景德镇": "130500", "萍乡": "130600", "九江": "130300",
            "新余": "130700", "鹰潭": "130800", "赣州": "130400", "吉安": "130900",
            "宜春": "131000", "抚州": "131100", "上饶": "131200",

            # === 山东省 (12xxxx) ===
            "济南": "120200", "青岛": "120300", "淄博": "120700", "枣庄": "121100",
            "东营": "121200", "烟台": "120400", "潍坊": "120500", "济宁": "120900",
            "泰安": "121000", "威海": "120600", "日照": "121300", "临沂": "120800",
            "德州": "121400", "聊城": "121500", "滨州": "121600", "菏泽": "121700",

            # === 河南省 (17xxxx) ===
            "郑州": "170200", "开封": "170400", "洛阳": "170300", "平顶山": "170500",
            "安阳": "170600", "鹤壁": "170700", "新乡": "170800", "焦作": "170900",
            "濮阳": "171000", "许昌": "171100", "漯河": "171200", "三门峡": "171300",
            "南阳": "171400", "商丘": "171500", "信阳": "171600", "周口": "171700",
            "驻马店": "171800",

            # === 湖北省 (18xxxx) ===
            "武汉": "180200", "黄石": "180500", "十堰": "180600", "宜昌": "180300",
            "襄阳": "180400", "鄂州": "180700", "荆门": "180800", "孝感": "180900",
            "荆州": "181000", "黄冈": "181100", "咸宁": "181200", "随州": "181300",
            "恩施": "181400", "仙桃": "181500", "潜江": "181600", "天门": "181700",

            # === 湖南省 (19xxxx) ===
            "长沙": "190200", "株洲": "190300", "湘潭": "190400", "衡阳": "190500",
            "邵阳": "190600", "岳阳": "190700", "常德": "190800", "张家界": "190900",
            "益阳": "191000", "郴州": "191100", "永州": "191200", "怀化": "191300",
            "娄底": "191400", "湘西": "191500",

            # === 河北省 (16xxxx) ===
            "石家庄": "160200", "唐山": "160300", "秦皇岛": "160700", "邯郸": "160800",
            "邢台": "160900", "保定": "160400", "张家口": "161000", "承德": "161100",
            "沧州": "161200", "廊坊": "160500", "衡水": "161300", "雄安新区": "160600",

            # === 山西省 (21xxxx) ===
            "太原": "210200", "大同": "210300", "阳泉": "210400", "长治": "210500",
            "晋城": "210600", "朔州": "210700", "晋中": "210800", "运城": "210900",
            "忻州": "211000", "临汾": "211100", "吕梁": "211200",

            # === 四川省 (09xxxx) ===
            "成都": "090200", "自贡": "090600", "攀枝花": "090700", "泸州": "090800",
            "德阳": "090400", "绵阳": "090300", "广元": "090900", "遂宁": "091000",
            "内江": "091100", "乐山": "091200", "南充": "091300", "眉山": "091400",
            "宜宾": "090500", "广安": "091500", "达州": "091600", "雅安": "091700",
            "巴中": "091800", "资阳": "091900", "阿坝": "092000", "甘孜": "092100",
            "凉山": "092200",

            # === 陕西省 (20xxxx) ===
            "西安": "200200", "铜川": "200500", "宝鸡": "200400", "咸阳": "200300",
            "渭南": "200600", "延安": "200700", "汉中": "200800", "榆林": "200900",
            "安康": "201000", "商洛": "201100",

            # === 辽宁省 (23xxxx) ===
            "沈阳": "230200", "大连": "230300", "鞍山": "230400", "抚顺": "230500",
            "本溪": "230600", "丹东": "230700", "锦州": "230800", "营口": "230900",
            "阜新": "231000", "辽阳": "231100", "盘锦": "231200", "铁岭": "231300",
            "朝阳": "231400", "葫芦岛": "231500",

            # === 吉林省 (24xxxx) ===
            "长春": "240200", "吉林市": "240300", "四平": "240400", "辽源": "240500",
            "通化": "240600", "白山": "240700", "松原": "240800", "白城": "240900",
            "延边": "241000",

            # === 黑龙江省 (22xxxx) ===
            "哈尔滨": "220200", "齐齐哈尔": "220400", "鸡西": "220500", "鹤岗": "220600",
            "双鸭山": "220700", "大庆": "220300", "伊春": "220800", "佳木斯": "220900",
            "七台河": "221000", "牡丹江": "221100", "黑河": "221200", "绥化": "221300",

            # === 云南省 (25xxxx) ===
            "昆明": "250200", "曲靖": "250300", "玉溪": "250400", "保山": "250500",
            "昭通": "250600", "丽江": "250700", "普洱": "250800", "临沧": "250900",
            "楚雄": "251000", "红河": "251100", "文山": "251200", "西双版纳": "251300",
            "大理": "251400",

            # === 贵州省 (26xxxx) ===
            "贵阳": "260200", "六盘水": "260300", "遵义": "260400", "安顺": "260500",
            "毕节": "260600", "铜仁": "260700", "黔西南": "260800", "黔东南": "260900",
            "黔南": "261000",

            # === 广西 (14xxxx) ===
            "南宁": "140200", "柳州": "140400", "桂林": "140300", "梧州": "140500",
            "北海": "140600", "防城港": "140700", "钦州": "140800", "贵港": "140900",
            "玉林": "141000", "百色": "141100", "贺州": "141200", "河池": "141300",
            "来宾": "141400", "崇左": "141500",

            # === 海南省 (10xxxx) ===
            "海口": "100200", "三亚": "100300", "三沙": "100400", "儋州": "100500",

            # === 甘肃省 (27xxxx) ===
            "兰州": "270200", "嘉峪关": "270300", "金昌": "270400", "白银": "270500",
            "天水": "270600", "武威": "270700", "张掖": "270800", "平凉": "270900",
            "酒泉": "271000", "庆阳": "271100", "定西": "271200", "陇南": "271300",

            # === 宁夏 (29xxxx) ===
            "银川": "290200", "石嘴山": "290300", "吴忠": "290400", "固原": "290500",
            "中卫": "290600",

            # === 青海省 (31xxxx) ===
            "西宁": "310200", "海东": "310300",

            # === 新疆 (30xxxx) ===
            "乌鲁木齐": "300200", "克拉玛依": "300300", "吐鲁番": "300400", "哈密": "300500",
            "昌吉": "300600", "博尔塔拉": "300700", "巴音郭楞": "300800", "阿克苏": "300900",
            "喀什": "301000", "和田": "301100", "伊犁": "301200",

            # === 西藏 (32xxxx) ===
            "拉萨": "320200", "日喀则": "320300", "昌都": "320400", "林芝": "320500",
            "山南": "320600", "那曲": "320700",

            # === 内蒙古 (05xxxx - 注意：前缀与天津相同，但分段不同) ===
            "呼和浩特": "050200", "包头": "050300", "乌海": "050400", "赤峰": "050500",
            "通辽": "050600", "鄂尔多斯": "050700", "呼伦贝尔": "050800", "巴彦淖尔": "050900",
            "乌兰察布": "051000", "兴安盟": "051100", "锡林郭勒": "051200", "阿拉善": "051300"
        }
    def _get_city_code(self, city_name: str) -> str:
        """
        根据城市名称获取对应的51job城市编码
        
        匹配策略：
        1. 优先精确匹配（完全相等）
        2. 其次包含匹配（城市名包含在输入中）
        3. 处理特殊情况（如"吉林市"需要精确匹配，避免匹配到"吉林"）
        
        Args:
            city_name: 城市名称，如"北京"、"北京市"、"上海"等
        
        Returns:
            城市编码字符串，如"010000"，如果未找到则返回空字符串
        """
        if not city_name:
            return ""
        
        city_name = city_name.strip()
        
        # 1. 优先精确匹配
        if city_name in self.city_map:
            return self.city_map[city_name]
        
        # 2. 处理带"市"的情况（如"北京市" -> "北京"）
        if city_name.endswith("市"):
            city_name_no_suffix = city_name[:-1]
            if city_name_no_suffix in self.city_map:
                return self.city_map[city_name_no_suffix]
        
        # 3. 处理特殊情况：需要精确匹配的城市（避免误匹配）
        # 例如："吉林市"应该匹配"吉林市"而不是"吉林"
        special_cities = ["吉林市", "拉萨", "香港", "澳门", "台湾"]
        for special in special_cities:
            if city_name == special or city_name.startswith(special):
                if special in self.city_map:
                    return self.city_map[special]
        
        # 4. 包含匹配（按长度从长到短排序，优先匹配更长的城市名）
        # 例如："乌鲁木齐"应该优先匹配"乌鲁木齐"而不是"乌鲁"
        sorted_cities = sorted(self.city_map.keys(), key=len, reverse=True)
        for city_key in sorted_cities:
            if city_key in city_name or city_name in city_key:
                return self.city_map[city_key]
        
        # 5. 如果都没匹配到，返回空字符串
        logger.warning(f"[Job51] 未找到城市 '{city_name}' 的编码，将使用全国搜索")
        return ""
    
    def get_all_cities(self) -> list[str]:
        """
        获取所有支持的城市列表（按省份分组）
        
        Returns:
            城市名称列表，按省份顺序排列
        """
        return list(self.city_map.keys())
    
    def get_cities_by_province(self) -> dict[str, list[str]]:
        """
        按省份分组获取城市列表
        
        Returns:
            字典，key为省份名称，value为该省份下的城市列表
        """
        # 定义省份分组
        provinces = {
            "直辖市": ["全国", "北京", "上海", "天津", "重庆"],
            "特别行政区": ["香港", "澳门", "台湾"],
            "广东省": ["广州", "深圳", "珠海", "汕头", "韶关", "佛山", "江门", "湛江", 
                      "茂名", "肇庆", "惠州", "梅州", "汕尾", "河源", "阳江", "清远",
                      "东莞", "中山", "潮州", "揭阳", "云浮"],
            "江苏省": ["南京", "无锡", "徐州", "常州", "苏州", "南通", "连云港", "淮安",
                      "盐城", "扬州", "镇江", "泰州", "宿迁", "昆山"],
            "浙江省": ["杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州",
                      "舟山", "台州", "丽水"],
            "安徽省": ["合肥", "芜湖", "蚌埠", "淮南", "马鞍山", "淮北", "铜陵", "安庆",
                      "黄山", "滁州", "阜阳", "宿州", "六安", "亳州", "池州", "宣城"],
            "福建省": ["福州", "厦门", "莆田", "三明", "泉州", "漳州", "南平", "龙岩", "宁德"],
            "江西省": ["南昌", "景德镇", "萍乡", "九江", "新余", "鹰潭", "赣州", "吉安",
                      "宜春", "抚州", "上饶"],
            "山东省": ["济南", "青岛", "淄博", "枣庄", "东营", "烟台", "潍坊", "济宁",
                      "泰安", "威海", "日照", "临沂", "德州", "聊城", "滨州", "菏泽"],
            "河南省": ["郑州", "开封", "洛阳", "平顶山", "安阳", "鹤壁", "新乡", "焦作",
                      "濮阳", "许昌", "漯河", "三门峡", "南阳", "商丘", "信阳", "周口", "驻马店"],
            "湖北省": ["武汉", "黄石", "十堰", "宜昌", "襄阳", "鄂州", "荆门", "孝感",
                      "荆州", "黄冈", "咸宁", "随州", "恩施", "仙桃", "潜江", "天门"],
            "湖南省": ["长沙", "株洲", "湘潭", "衡阳", "邵阳", "岳阳", "常德", "张家界",
                      "益阳", "郴州", "永州", "怀化", "娄底", "湘西"],
            "河北省": ["石家庄", "唐山", "秦皇岛", "邯郸", "邢台", "保定", "张家口", "承德",
                      "沧州", "廊坊", "衡水", "雄安新区"],
            "山西省": ["太原", "大同", "阳泉", "长治", "晋城", "朔州", "晋中", "运城",
                      "忻州", "临汾", "吕梁"],
            "四川省": ["成都", "自贡", "攀枝花", "泸州", "德阳", "绵阳", "广元", "遂宁",
                      "内江", "乐山", "南充", "眉山", "宜宾", "广安", "达州", "雅安",
                      "巴中", "资阳", "阿坝", "甘孜", "凉山"],
            "陕西省": ["西安", "铜川", "宝鸡", "咸阳", "渭南", "延安", "汉中", "榆林",
                      "安康", "商洛"],
            "辽宁省": ["沈阳", "大连", "鞍山", "抚顺", "本溪", "丹东", "锦州", "营口",
                      "阜新", "辽阳", "盘锦", "铁岭", "朝阳", "葫芦岛"],
            "吉林省": ["长春", "吉林市", "四平", "辽源", "通化", "白山", "松原", "白城", "延边"],
            "黑龙江省": ["哈尔滨", "齐齐哈尔", "鸡西", "鹤岗", "双鸭山", "大庆", "伊春",
                        "佳木斯", "七台河", "牡丹江", "黑河", "绥化"],
            "云南省": ["昆明", "曲靖", "玉溪", "保山", "昭通", "丽江", "普洱", "临沧",
                      "楚雄", "红河", "文山", "西双版纳", "大理"],
            "贵州省": ["贵阳", "六盘水", "遵义", "安顺", "毕节", "铜仁", "黔西南", "黔东南", "黔南"],
            "广西壮族自治区": ["南宁", "柳州", "桂林", "梧州", "北海", "防城港", "钦州",
                            "贵港", "玉林", "百色", "贺州", "河池", "来宾", "崇左"],
            "海南省": ["海口", "三亚", "三沙", "儋州"],
            "甘肃省": ["兰州", "嘉峪关", "金昌", "白银", "天水", "武威", "张掖", "平凉",
                      "酒泉", "庆阳", "定西", "陇南"],
            "宁夏回族自治区": ["银川", "石嘴山", "吴忠", "固原", "中卫"],
            "青海省": ["西宁", "海东"],
            "新疆维吾尔自治区": ["乌鲁木齐", "克拉玛依", "吐鲁番", "哈密", "昌吉", "博尔塔拉",
                            "巴音郭楞", "阿克苏", "喀什", "和田", "伊犁"],
            "西藏自治区": ["拉萨", "日喀则", "昌都", "林芝", "山南", "那曲"],
            "内蒙古自治区": ["呼和浩特", "包头", "乌海", "赤峰", "通辽", "鄂尔多斯",
                        "呼伦贝尔", "巴彦淖尔", "乌兰察布", "兴安盟", "锡林郭勒", "阿拉善"]
        }
        
        result = {}
        for province, cities in provinces.items():
            # 只包含在city_map中存在的城市
            available_cities = [city for city in cities if city in self.city_map]
            if available_cities:
                result[province] = available_cities
        
        return result

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