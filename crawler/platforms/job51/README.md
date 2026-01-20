# 前程无忧51job平台爬虫（仅作学习交流使用）

> **⚠️ 重要声明：本爬虫功能仅用于学习交流目的，请遵守相关法律法规和平台使用条款，不得用于商业用途或非法用途。**

## 功能说明

本模块实现了前程无忧51job平台的数据采集功能，包括：

- 关键词搜索
- 城市/区县筛选
- 多页数据爬取
- 自动去重
- 数据保存到数据库

## 使用方法

### 命令行方式

**方式1：作为模块运行（推荐）**
```bash
# 在项目根目录（jobinsight_project）下运行
cd jobinsight_project
python -m jobinsight.crawler.platforms.job51.run --keyword python --city 上海
```

**方式2：直接运行脚本**
```bash
# 在项目根目录（jobinsight_project）下运行
cd jobinsight_project
python jobinsight/crawler/platforms/job51/run.py --keyword python --city 上海
```

**方式3：在脚本所在目录运行**
```bash
# 在 job51 目录下运行（会自动查找项目根目录）
cd jobinsight_project/jobinsight/crawler/platforms/job51
python run.py --keyword python --city 上海
```

### 使用示例

```bash
# 基本用法
python -m jobinsight.crawler.platforms.job51.run --keyword python --city 上海

# 指定区县（仅在指定单个城市时有效）
python -m jobinsight.crawler.platforms.job51.run --keyword python --city 北京 --region 海淀区

# 爬取多页
python -m jobinsight.crawler.platforms.job51.run --keyword python --city 上海 --pages 5
```

### 参数说明

- `--keyword KEYWORD`: 搜索关键词（必需）
- `--city CITY`: 城市名称（可选），如"北京"、"上海"、"全国"
- `--region REGION`: 区县名称（可选），仅在指定单个城市时有效
- `--pages PAGES`: 爬取页数（可选，默认1，最大不超过配置中的max_pages）

### 配置说明

在 `config.yaml` 中的 `job51` 节点可以配置：

```yaml
job51:
  keywords: ["Python"]           # 默认关键词
  cities: ["全国"]                # 默认城市
  delay_min: 1.0                 # 请求最小延迟（秒）
  delay_max: 2.0                 # 请求最大延迟（秒）
  max_pages: 10                  # 最大爬取页数
```

## 技术实现

### URL构造

**新版URL格式（we.51job.com）：**
```
https://we.51job.com/pc/search?keyword=<keyword>&city=<city_code>&page=<page>
```

**旧版URL格式（search.51job.com，备用）：**
```
https://search.51job.com/list/<city_code>,<region_code>,0000,00,9,99,<keyword>,2,<page>.html
```

### 城市编码

支持的主要城市编码已内置，包括：
- 全国：000000
- 北京：010000
- 上海：020000
- 广州：030200
- 深圳：030300
- 等30+个主要城市

### 页面结构适配

爬虫支持多种页面结构：
1. **JSON API响应**：如果页面使用API接口，会自动解析JSON格式
2. **HTML页面**：使用BeautifulSoup解析，支持多种CSS选择器
3. **动态渲染页面**：如果页面需要JavaScript渲染，可能需要使用Selenium（当前版本暂不支持）

### 解析策略

爬虫使用多重策略查找职位列表：
1. CSS选择器匹配（多种可能的类名）
2. 链接匹配（查找包含职位链接的元素）
3. 文本内容匹配（查找包含"职位"、"公司"等关键词的元素）

### 数据解析

使用BeautifulSoup解析HTML页面，提取：
- 职位标题
- 公司名称
- 工作地点
- 薪资范围
- 学历要求
- 工作经验
- 职位描述
- 标签/技能

### 去重机制

基于 `platform + job_id` 进行去重，避免重复数据。

## 注意事项

1. **请求频率**：已内置延迟机制，建议不要修改过小的延迟值
2. **页数限制**：默认最大10页，可在配置中调整
3. **页面结构**：如果51job页面结构变化，可能需要更新解析逻辑
4. **代理配置**：可在 `config.yaml` 的 `crawler` 节点配置代理
5. **编码问题**：关键词使用GBK编码，已自动处理

## 故障排查

### 未获取到数据

1. 检查网络连接和代理配置
2. 确认关键词和城市名称正确
3. 查看日志输出，可能页面结构已变化
4. 某些城市可能需要登录才能查看

### 解析失败

1. 检查BeautifulSoup是否正确安装
2. 查看日志中的警告信息
3. 可能需要更新CSS选择器

## 扩展开发

如需添加新的城市或区县编码，可在 `adapter.py` 中的 `CITY_CODE_MAP` 和 `REGION_CODE_MAP` 中添加。

## 法律声明

本爬虫工具仅供学习交流使用，使用者需：

1. 遵守《网络安全法》、《数据安全法》等相关法律法规
2. 遵守前程无忧51job的使用条款和robots.txt
3. 不得用于商业用途或非法用途
4. 对使用本工具产生的任何后果自行承担责任
