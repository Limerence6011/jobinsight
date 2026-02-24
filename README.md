# JobInsight — 岗位招聘数据分析与可视化系统 / Job Recruitment Data Analysis & Visualization System

> **⚠️ 重要声明：本项目所有数据采集功能仅用于学习交流目的，请遵守相关法律法规和平台使用条款，不得用于商业用途或非法用途。**

[English](#english) | [中文](#chinese)

---

<a name="english"></a>
## English

### Overview

JobInsight is a comprehensive Python-based job recruitment data analysis and visualization system. It covers the complete data pipeline:

**Web Crawling → Data Storage → Data Cleaning → Statistical Analysis → Visualization Dashboard → Job Recommendation → Dynamic Trends**

> Default Data Source: RemoteOK Public JSON Feed (easy to get started)  
> You can extend it to integrate with mainstream job platforms in the `jobinsight/crawler/adapters/` directory (requires proper authorization and compliance).

---

### Features

#### Core Modules

- **Web Crawling (Required)**
  - `Requests` + Adapter Pattern
  - Default: RemoteOK API (`remoteok_api.py`), crawls job title, company, location, tags, description, URL, etc.
  - Extensible: Add new adapters in `jobinsight/crawler/adapters/`

- **Data Storage**
  - MySQL + SQLAlchemy
  - Key field: `crawl_date` (for dynamic trends)
  - Automatic data cleaning and normalization

- **Data Processing**
  - Pandas/Numpy statistics and aggregation
  - Salary parsing: `salary_avg/min/max` (supports multiple formats)
  - City, education, experience normalization

- **Visualization (Interactive)**
  - Pyecharts: City popularity Top, job posting trends, skills/tags word cloud
  - Matplotlib: Static chart export (optional)

- **Job Recommendation (Required)**
  - Hard filters (city/minimum salary/education/experience/keywords)
  - Soft matching ranking (TF-IDF + cosine similarity + salary weighting)

- **Dynamic Trends (Required)**
  - Daily collection (optional APScheduler scheduling), trends automatically reflect market changes by `crawl_date`

- **Web Interface (Integrated)**
  - Flask + Bootstrap: Home (crawl), Dashboard (visualization), Recommend (recommendation)
  - Enhanced crawl success notifications with detailed statistics
  - Autocomplete for city and skills input based on database data
  - Form value persistence after submission

---

### Requirements

- Python 3.7+ (recommended 3.11)
- MySQL 5.7+ or MySQL 8.0+
- Playwright (for 51job crawler)
- Windows/macOS/Linux

---

### Installation

1. **Generate Project Framework**

   Use the project generator to create the complete JobInsight project:

   ```bash
   # Use default output directory (/mnt/data/jobinsight)
   python generate_project.py

   # Or specify custom output directory
   python generate_project.py --output-dir ./my_jobinsight_project

   # View help
   python generate_project.py --help
   ```

2. **Navigate to Project Directory**

   ```bash
   cd /mnt/data/jobinsight  # or your specified directory
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure MySQL Database**

   Edit `config.yaml` and set your MySQL database configuration:
   
   ```yaml
   database:
     host: "localhost"
     port: 3306
     user: "root"
     password: "your_password"
     database: "jobinsight"
     charset: "utf8mb4"
   ```

5. **Initialize Database**

   ```bash
   # Create database and tables
   python init_database.py
   ```

---

### Quick Start

#### Method 1: One-Click Startup (Recommended for First Time)

```bash
# Start with environment check and optional initial data collection
python run.py --crawl-first
```

This will:
- Check Python version, required modules, configuration files
- Initialize database (create tables if needed)
- Optionally perform initial data collection
- Start Web application and scheduled tasks

#### Method 2: Quick Web App Startup

```bash
# Quick start Web application only (environment already configured)
python run_web.py
```

#### Manual Data Collection

```bash
# Run crawler manually
python run_crawl.py --keyword python --city Remote
```

#### Access Web Interface

After starting, visit: http://localhost:5000

---

### Project Structure

```
jobinsight/
├── utils/          # Utilities (logging, HTTP client, salary parsing, etc.)
├── crawler/        # Crawler module
│   ├── adapters/   # Legacy adapters
│   ├── platforms/  # Platform-specific crawlers (job51, boss, etc.)
│   └── run_crawl.py
├── storage/        # Data storage (SQLAlchemy models, database operations)
├── pipeline/       # Data processing pipeline
├── analytics/      # Data analysis (statistics, trends, recommendations)
├── viz/            # Visualization (PyEcharts, Matplotlib)
└── webapp/         # Web application (Flask app, templates)
```

---

### Configuration

Edit `config.yaml` to adjust settings:

```yaml
app:
  data_days_window: 30    # Data window in days
  topn: 20                # Number of recommendation results

database:
  host: "localhost"       # MySQL host
  port: 3306              # MySQL port
  user: "root"            # MySQL user
  password: "your_password"  # MySQL password
  database: "jobinsight"  # Database name
  charset: "utf8mb4"      # Character set

crawler:
  data_sources: ["remoteok_api"]
  default_keyword: "python"
  pages: 1
  polite_sleep_min: 0.6    # Request delay (seconds)
  polite_sleep_max: 1.5
  proxy_http: "http://127.0.0.1:7897"  # Proxy settings (optional)
  proxy_https: "http://127.0.0.1:7897"

recommend:
  weight_similarity: 0.75  # Similarity weight
  weight_salary: 0.25      # Salary weight
```

---

### Usage Examples

#### Command Line Crawler

```bash
# Crawl Python-related jobs
python run_crawl.py --keyword python

# Crawl jobs in specific city
python run_crawl.py --keyword data --city "San Francisco"

# Crawl multiple pages
python run_crawl.py --keyword backend --pages 3
```

#### Web Interface

1. **Home**: Manually trigger data collection
   - Real-time crawl progress with detailed statistics
   - Beautiful success notification with city distribution and timing breakdown
   - Hover to pause auto-close for detailed review
   
2. **Dashboard**: View visualization charts (city popularity, trends, word cloud)
   - Interactive charts powered by PyEcharts
   - Error handling with user-friendly messages
   
3. **Recommend**: Enter criteria to get personalized job recommendations
   - **Autocomplete**: City and skills suggestions based on current database
   - **Form persistence**: All input values preserved after submission
   - **Smart matching**: Multi-word skills input with intelligent suggestions
   - **Keyboard navigation**: Arrow keys, Enter, and ESC support

---

### Extension Development

#### Adding New Crawler Adapters

1. Create a new file in `jobinsight/crawler/adapters/`
2. Implement `JobAdapter` protocol (refer to `remoteok_api.py`)
3. Register the new adapter in `crawler/run_crawl.py`

#### Custom Visualization

- Modify `jobinsight/viz/charts_pyecharts.py` to add new charts
- Integrate new charts in `webapp/app.py`

#### Adjust Recommendation Algorithm

- Modify weights and algorithm logic in `jobinsight/analytics/recommend.py`

---

### Scripts

- **`run.py`**: One-click startup script (with environment check, database initialization)
- **`run_web.py`**: Quick Web app startup (only starts Web service)
- **`run_crawl.py`**: Data collection script (manual trigger with beautiful output)
- **`init_database.py`**: Database initialization script (creates MySQL database and tables)

### API Endpoints

- **`GET /api/autocomplete`**: Get city and skills suggestions for autocomplete
  - Returns: `{ "cities": [...], "skills": [...] }`
  - Based on current database data (last 30 days, configurable)

---

### Latest Features

#### Enhanced User Experience

1. **Crawl Success Notifications**
   - Beautiful card-style notifications with detailed statistics
   - Shows: collection count, keyword, city filter, timing breakdown, city distribution
   - Hover to pause auto-close (10 seconds default)
   - Smooth animations and visual feedback

2. **Smart Autocomplete**
   - City input: Real-time suggestions from database
   - Skills input: Multi-word support with intelligent matching
   - Keyboard navigation: Arrow keys, Enter, ESC
   - Auto-deduplication: Prevents duplicate skill entries

3. **Form Persistence**
   - All form values preserved after submission
   - Easy to adjust criteria and re-run recommendations
   - Seamless user experience

### Notes

1. **Educational Purpose Only**: All data collection features in this project are for learning and research purposes only
2. **Data Source Compliance**: This project uses RemoteOK public API as a demo data source by default
3. **Authorization Requirements**: Integrating with mainstream platforms requires proper authorization and compliance
4. **Scheduled Tasks**: Default daily collection at 09:00 (adjustable in `webapp/app.py`)
5. **Database**: MySQL database is required. Make sure MySQL service is running and database is created using `init_database.py`
6. **Proxy Support**: Configure proxy settings in `config.yaml` for network access (optional)

### Job51 Platform Configuration

For detailed Job51 (前程无忧) platform parameter configuration, please refer to:
- [Platform README](jobinsight/crawler/platforms/README.md#前程无忧51job平台参数说明)
- Configuration file: `config.yaml` → `job51` section

Key parameters include:
- `keywords`: Search keywords (list)
- `cities`: Target cities (list, max 5)
- `salary_min/max`: Salary range (monthly, in CNY)
- `experience_levels`: Work experience requirements
- `education_levels`: Education requirements
- `max_pages`: Maximum pages to crawl (recommended: ≤20)
- `delay_min/max`: Request delay range (recommended: 1-3 seconds)

---

### License

This project is for learning and research purposes only.

---

### Support

For issues, please check the documentation or submit an Issue.

---

<a name="chinese"></a>
## 中文

### 项目简介

JobInsight 是一个基于 Python 的岗位招聘数据分析与可视化系统，覆盖完整链路：

**爬虫采集 → 数据入库 → 清洗/处理 → 统计分析 → 可视化看板 → 岗位推荐 → 趋势动态化**

> 默认数据源：RemoteOK 公共 JSON Feed（便于你一键跑通全链路）  
> 后续你可在 `jobinsight/crawler/adapters/` 中扩展对接"主流招聘平台"适配器（按合规/授权方式实现）。

---

### 功能概览

#### 核心功能模块

- **爬虫采集（必选）**
  - `Requests` + 适配器模式 & `Playwright`（针对动态网页）
  - 支持平台：
    - RemoteOK API (`remoteok_api.py`) - 默认，简单易用
    - 前程无忧 51job (`crawler/platforms/job51`) - 使用 Playwright 模拟交互
  - 待实现/占位：Boss直聘、智联招聘
  - 支持扩展：在 `jobinsight/crawler/platforms/` 中添加新的平台适配器

- **数据存储**
  - MySQL + SQLAlchemy
  - 关键字段：`crawl_date`（用于动态趋势）
  - 自动数据清洗和标准化

- **数据清洗与处理**
  - Pandas/Numpy 统计与聚合
  - 薪资解析：`salary_avg/min/max`（支持多种格式）
  - 城市、学历、经验标准化

- **可视化（交互式为主）**
  - Pyecharts：城市热度 Top、岗位数量趋势、技能/标签词云
  - Matplotlib：预留静态图导出（可选）

- **岗位推荐（必选）**
  - 硬条件过滤（城市/最低薪资/学历/经验/关键词）
  - 软匹配排序（TF-IDF + 余弦相似度 + 薪资加权）

- **动态趋势（必选）**
  - 每日采集一次（可选 APScheduler 定时），趋势图按 `crawl_date` 自动体现市场变化

- **Web 界面（可选但已集成）**
  - Flask + Bootstrap：首页（采集）、看板（dashboard）、推荐（recommend）
  - 优化的采集成功提示，显示详细统计信息
  - 基于数据库的自动完成功能（城市、技能关键词）
  - 表单提交后保留输入值

---

### 环境要求

- Python 3.7+（推荐 3.11）
- MySQL 5.7+ 或 MySQL 8.0+
- Windows/macOS/Linux 均可

---

### 安装步骤

1. **生成项目框架**

   使用项目生成器创建完整的 JobInsight 项目：

   ```bash
   # 使用默认输出目录 (/mnt/data/jobinsight)
   python generate_project.py

   # 或指定自定义输出目录
   python generate_project.py --output-dir ./my_jobinsight_project

   # 查看帮助信息
   python generate_project.py --help
   ```

2. **进入生成的项目目录**

   ```bash
   cd /mnt/data/jobinsight  # 或你指定的目录
   ```

3. **安装依赖**

   ```bash
   pip install -r requirements.txt
   playwright install  # 安装 Playwright 浏览器内核
   ```

4. **配置 MySQL 数据库**

   编辑 `config.yaml` 文件，设置 MySQL 数据库配置：
   
   ```yaml
   database:
     host: "localhost"
     port: 3306
     user: "root"
     password: "your_password"
     database: "jobinsight"
     charset: "utf8mb4"
   ```

5. **初始化数据库**

   ```bash
   # 创建数据库和表结构
   python init_database.py
   ```

---

### 快速开始

#### 方式一：一键启动（推荐首次使用）

```bash
# 启动前进行环境检查，并可选择执行初始数据采集
python run.py --crawl-first
```

这将执行：
- 检查 Python 版本、必要模块、配置文件
- 初始化数据库（创建表结构）
- 可选：执行初始数据采集
- 启动 Web 应用和定时任务调度器

#### 方式二：快速启动 Web 应用

```bash
# 仅快速启动 Web 应用（环境已配置好时使用）
python run_web.py
```

#### 手动数据采集

```bash
# 手动运行爬虫采集数据
python run_crawl.py --keyword python --city Remote
```

#### 访问 Web 界面

启动后访问：http://localhost:5000

---

### 项目结构

```
jobinsight/
├── utils/          # 工具模块（日志、HTTP客户端、薪资解析等）
├── crawler/        # 爬虫模块
│   ├── adapters/   # 旧版适配器
│   ├── platforms/  # 分平台爬虫实现 (job51, boss 等)
│   └── run_crawl.py
├── storage/        # 数据存储（SQLAlchemy模型、数据库操作）
├── pipeline/       # 数据处理管道
├── analytics/      # 数据分析（统计、趋势、推荐）
├── viz/            # 可视化（PyEcharts、Matplotlib）
└── webapp/         # Web应用（Flask应用、模板）
```

---

### 配置说明

编辑 `config.yaml` 文件可以调整：

```yaml
app:
  data_days_window: 30    # 数据窗口天数
  topn: 20                # 推荐结果数量

database:
  host: "localhost"       # MySQL 主机地址
  port: 3306              # MySQL 端口
  user: "root"            # MySQL 用户名
  password: "your_password"  # MySQL 密码
  database: "jobinsight"  # 数据库名称
  charset: "utf8mb4"      # 字符集

crawler:
  data_sources: ["remoteok_api"]
  default_keyword: "python"
  pages: 1
  polite_sleep_min: 0.6    # 请求延迟（秒）
  polite_sleep_max: 1.5
  proxy_http: "http://127.0.0.1:7897"  # 代理配置（可选）
  proxy_https: "http://127.0.0.1:7897"

recommend:
  weight_similarity: 0.75  # 相似度权重
  weight_salary: 0.25      # 薪资权重
```

---

### 使用示例

#### 命令行爬虫

```bash
# 爬取 Python 相关岗位
python run_crawl.py --keyword python

# 爬取指定城市的岗位
python run_crawl.py --keyword data --city "San Francisco"

# 爬取多页数据
python run_crawl.py --keyword backend --pages 3

# 爬取前程无忧 51job (需要 Playwright)
python -m jobinsight.crawler.platforms.job51.run --keyword python --city 上海
```

#### Web 界面使用

1. **首页**：手动触发数据采集
   - 实时显示采集进度和详细统计信息
   - 美观的成功提示卡片，包含城市分布和耗时详情
   - 鼠标悬停时暂停自动关闭，方便查看详情
   
2. **看板**：查看可视化图表（城市热度、趋势、词云）
   - 基于 PyEcharts 的交互式图表
   - 友好的错误提示信息
   
3. **推荐**：输入条件获取个性化岗位推荐
   - **自动完成**：城市和技能关键词基于当前数据库智能推荐
   - **表单保留**：提交后所有输入值自动保留，方便调整
   - **智能匹配**：技能关键词支持多词输入，智能建议
   - **键盘导航**：支持方向键、回车、ESC 等快捷键

---

### 扩展开发

#### 添加新的爬虫适配器

1. 在 `jobinsight/crawler/platforms/` 目录下创建新目录
2. 实现 `Adapter` 类（参考 `job51/adapter.py`）
3. 创建 `run.py` 脚本用于独立运行

#### 自定义可视化

- 修改 `jobinsight/viz/charts_pyecharts.py` 添加新图表
- 在 `webapp/app.py` 中集成新图表

#### 调整推荐算法

- 修改 `jobinsight/analytics/recommend.py` 中的权重和算法逻辑

---

### 启动脚本说明

- **`run.py`**: 一键启动脚本（包含环境检查、数据库初始化等功能）
- **`run_web.py`**: 快速 Web 应用启动（仅启动 Web 服务）
- **`run_crawl.py`**: 数据采集脚本（手动触发，带美观的输出统计）
- **`init_database.py`**: 数据库初始化脚本（创建 MySQL 数据库和表结构）

### API 接口

- **`GET /api/autocomplete`**: 获取城市和技能关键词建议（用于自动完成）
  - 返回格式：`{ "cities": [...], "skills": [...] }`
  - 基于当前数据库数据（最近 30 天，可配置）

---

### 最新功能特性

#### 用户体验优化

1. **采集成功提示优化**
   - 美观的卡片式提示框，显示详细统计信息
   - 包含：采集数量、关键词、城市过滤、耗时详情、城市分布
   - 鼠标悬停时暂停自动关闭（默认 10 秒）
   - 流畅的动画效果和视觉反馈

2. **智能自动完成**
   - 城市输入：基于数据库实时推荐
   - 技能关键词：支持多词输入，智能匹配
   - 键盘导航：支持方向键、回车、ESC
   - 自动去重：避免重复输入技能关键词

3. **表单值保留**
   - 提交后所有表单输入值自动保留
   - 方便调整条件后重新生成推荐
   - 流畅的用户体验

### 注意事项

1. **学习交流用途**：本项目所有数据采集功能仅用于学习交流目的，请勿用于商业用途
2. **数据源合规**：本项目默认使用 RemoteOK 公开 API 作为演示数据源
3. **授权要求**：对接国内主流平台需要相应的授权和合规处理
4. **定时任务**：定时采集任务默认在每天 09:00 执行（可在 `webapp/app.py` 中调整）
5. **数据库**：需要 MySQL 数据库。请确保 MySQL 服务已启动，并使用 `init_database.py` 创建数据库
6. **代理配置**：可在 `config.yaml` 中配置代理设置以支持网络访问（可选）

### 前程无忧51job平台参数配置

详细的前程无忧51job平台参数说明，请参考：
- [平台README文档](jobinsight/crawler/platforms/README.md#前程无忧51job平台参数说明)
- 配置文件：`config.yaml` → `job51` 节点

主要参数包括：
- `keywords`: 搜索关键词（列表形式）
- `cities`: 目标城市（列表，最多5个）
- `salary_min/max`: 薪资范围（月薪，单位：元）
- `experience_levels`: 工作经验要求
- `education_levels`: 学历要求
- `max_pages`: 最大爬取页数（建议≤20页）
- `delay_min/max`: 请求延迟范围（建议1-3秒）

**配置示例**：
```yaml
job51:
  keywords: ["Python", "Python开发"]
  cities: ["北京", "上海"]
  salary_min: 10000
  salary_max: 30000
  experience_levels: ["1-3年", "3-5年"]
  education_levels: ["本科", "硕士"]
  max_pages: 10
  delay_min: 1.0
  delay_max: 2.0
```

---

### 许可证

本项目仅供学习和研究使用。

---

### 支持

如有问题，请查看文档或提交 Issue。
