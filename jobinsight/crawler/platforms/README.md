# 爬虫平台模块

> **重要声明：本项目所有数据采集功能仅用于学习交流目的，请遵守相关法律法规和平台使用条款。**

本目录包含按网站分类的爬虫平台实现。

## 目录结构

```
platforms/
├── remoteok/          # RemoteOK 平台
│   ├── __init__.py
│   ├── adapter.py     # 平台适配器
│   └── run.py         # 独立执行脚本
├── boss/              # BOSS直聘平台
│   ├── __init__.py
│   ├── adapter.py
│   └── run.py
├── zhilian/           # 智联招聘平台
│   ├── __init__.py
│   ├── adapter.py
│   └── run.py
└── job51/             # 前程无忧51job平台
    ├── __init__.py
    ├── adapter.py
    └── run.py
```

## 使用方法

### RemoteOK 平台

```bash
# 使用模块方式执行
python -m jobinsight.crawler.platforms.remoteok.run --keyword python --city Remote

# 或直接执行（需要设置 PYTHONPATH）
cd jobinsight_project
python -m jobinsight.crawler.platforms.remoteok.run --keyword python --city Remote
```

### BOSS直聘平台

```bash
python -m jobinsight.crawler.platforms.boss.run --keyword python --city 北京
```

### 智联招聘平台

```bash
python -m jobinsight.crawler.platforms.zhilian.run --keyword python --city 北京
```

### 前程无忧51job平台

```bash
python -m jobinsight.crawler.platforms.job51.run --keyword python --city 上海
```

## 通用参数

所有平台的执行脚本都支持以下参数：

- `--keyword KEYWORD`: 搜索关键词（必需）
- `--city CITY`: 城市过滤（可选）
- `--pages PAGES`: 页数（可选，默认1）

## 适配器接口

每个平台的 `adapter.py` 需要实现以下接口：

```python
class PlatformAdapter:
    platform = "platform_name"
    
    def __init__(self, client: Optional[HttpClient] = None):
        self.client = client or HttpClient()
    
    def fetch(self, keyword: str, city: Optional[str], page: int) -> str:
        """获取数据"""
        pass
    
    def parse(self, payload: str) -> Iterable[JobPost]:
        """解析数据"""
        pass
```

## 注意事项

1. **学习交流用途**: 本项目所有数据采集功能仅用于学习交流目的，请勿用于商业用途
2. **授权要求**: BOSS直聘、智联招聘、前程无忧等平台需要相应的授权和合规处理
3. **代理配置**: 可在 `config.yaml` 中配置代理设置
4. **数据合规**: 请确保遵守各平台的使用条款和法律法规
5. **合理使用**: 请设置合适的请求延迟和页数限制，避免对目标网站造成压力

---

## 前程无忧51job平台参数说明

### 全局配置参数（config.yaml）

前程无忧51job平台的爬取参数在 `config.yaml` 文件的 `job51` 节点下配置。以下为详细说明：

#### 基础搜索参数

| 参数名称 | 类型 | 默认值 | 说明 | 填写建议 |
|---------|------|--------|------|---------|
| `keywords` | 列表 | `["Python"]` | 搜索关键词，支持多个关键词 | 使用规范职位名称，如"Python开发"、"数据分析"等 |
| `cities` | 列表 | `["全国"]` | 搜索城市，使用规范城市名称 | 可选值：`["全国"]` 或 `["北京", "上海"]` 等，最多5个城市 |
| `regions` | 列表 | `["不限"]` | 区县筛选，仅在指定单个城市时有效 | 如 `["海淀区", "朝阳区"]`，多城市时建议设为 `["不限"]` |

#### 筛选条件参数

| 参数名称 | 类型 | 默认值 | 可选值 | 说明 |
|---------|------|--------|--------|------|
| `salary_min` | 整数 | `0` | - | 最低薪资（月薪，单位：元） |
| `salary_max` | 整数 | `50000` | - | 最高薪资（月薪，单位：元） |
| `experience_levels` | 列表 | `["不限"]` | `不限`、`1年以下`、`1-3年`、`3-5年`、`5-10年`、`10年以上` | 工作经验要求 |
| `education_levels` | 列表 | `["不限"]` | `不限`、`高中`、`大专`、`本科`、`硕士`、`博士` | 学历要求 |
| `company_sizes` | 列表 | `["不限"]` | `不限`、`20人以下`、`20-99人`、`100-499人`、`500-999人`、`1000-9999人`、`10000人以上` | 公司规模 |
| `company_types` | 列表 | `["不限"]` | `不限`、`国企`、`外资/合资`、`民营`、`上市公司`、`事业单位`、`其他` | 公司性质 |
| `job_terms` | 列表 | `["全职"]` | `不限`、`全职`、`实习`、`兼职` | 职位类型 |

#### 爬取控制参数

| 参数名称 | 类型 | 默认值 | 说明 | 填写建议 |
|---------|------|--------|------|---------|
| `ordering` | 字符串 | `"发布时间"` | 排序方式 | `发布时间`（最新优先）、`相关度`、`薪资` |
| `page_size` | 整数 | `50` | 每页显示数量 | 建议不超过50，避免单次请求过大 |
| `max_pages` | 整数 | `10` | 最大爬取页数 | 根据需求设置，建议不超过20页 |
| `delay_min` | 浮点数 | `1.0` | 请求最小延迟（秒） | 建议1.0-2.0秒，避免请求过快 |
| `delay_max` | 浮点数 | `2.0` | 请求最大延迟（秒） | 建议2.0-3.0秒，随机延迟更自然 |

### 配置示例

```yaml
job51:
  # 搜索Python开发相关职位
  keywords: ["Python", "Python开发"]
  # 搜索北京和上海的职位
  cities: ["北京", "上海"]
  # 不限制区县
  regions: ["不限"]
  # 薪资范围：10k-30k
  salary_min: 10000
  salary_max: 30000
  # 工作经验：1-5年
  experience_levels: ["1-3年", "3-5年"]
  # 学历：本科及以上
  education_levels: ["本科", "硕士", "博士"]
  # 公司规模：100人以上
  company_sizes: ["100-499人", "500-999人", "1000-9999人", "10000人以上"]
  # 公司性质：不限
  company_types: ["不限"]
  # 职位类型：全职
  job_terms: ["全职"]
  # 按发布时间排序
  ordering: "发布时间"
  # 每页50条，最多爬取10页
  page_size: 50
  max_pages: 10
  # 请求延迟1-2秒
  delay_min: 1.0
  delay_max: 2.0
```

### 填写指南

1. **关键词填写**：
   - 使用规范的职位名称，避免过于宽泛或过于具体
   - 多个关键词用列表形式：`["Python", "数据分析"]`
   - 避免使用特殊字符

2. **城市选择**：
   - 使用规范城市名称（如"北京"、"上海"，不是"北京市"、"上海市"）
   - 选择"全国"表示不限制城市
   - 最多选择5个城市

3. **区县筛选**：
   - 仅在指定单个城市时使用
   - 多城市时建议设为 `["不限"]`
   - 使用规范区县名称

4. **薪资范围**：
   - 确保 `salary_min` ≤ `salary_max`
   - 单位统一为"元/月"
   - 避免设置极端值

5. **合理设置爬取参数**：
   - `max_pages` 建议不超过20页，避免数据量过大
   - `delay_min` 和 `delay_max` 建议设置在1-3秒之间
   - `page_size` 建议不超过50

### 技术说明

前程无忧51job的搜索URL结构通常为：
```
https://search.51job.com/list/<city_code>,<region_code>,0000,00,9,99,<keyword>,2,<page>.html
```

- `city_code`: 城市编码（如北京：010000，上海：020000）
- `region_code`: 区县编码（仅在指定区县时使用）
- `keyword`: 关键词（需要URL编码）
- `page`: 页码（从1开始）

爬虫实现时需要：
1. 将城市名称转换为对应的城市编码
2. 将关键词进行URL编码
3. 处理分页逻辑，先获取总页数再循环爬取
4. 设置合理的请求延迟，避免被封禁

### 重要提醒

⚠️ **请务必遵守以下原则**：

1. **仅用于学习交流**：本项目所有数据采集功能仅用于学习交流目的
2. **遵守法律法规**：请确保遵守《网络安全法》、《数据安全法》等相关法律法规
3. **尊重平台规则**：请遵守前程无忧51job的使用条款和robots.txt
4. **合理使用**：设置合适的请求频率和爬取量，避免对目标网站造成压力
5. **数据保护**：采集的数据请妥善保管，不得用于商业用途或非法用途
