# 51job爬虫测试说明

## 当前状态

51job平台已经改版，页面采用SPA（单页应用）架构，需要JavaScript渲染才能显示职位数据。当前适配器支持以下方式：

### 1. API接口调用（优先）
- 尝试调用 `https://we.51job.com/api/job/search-pc` API接口
- 注意：新版本API可能需要签名验证，如果直接调用失败，会回退到HTML解析

### 2. HTML页面解析（备用）
- 使用旧版URL格式：`https://search.51job.com/list/...`
- 注意：如果页面结构变化，可能无法解析

## 测试方法

### 方法1：使用独立测试脚本

```bash
python test_job51.py --keyword Python --city 上海 --pages 1
```

### 方法2：使用平台运行脚本

```bash
python -m jobinsight.crawler.platforms.job51.run --keyword Python --city 上海 --pages 1
```

### 方法3：使用测试目录中的脚本

```bash
python tests/test_job51_crawler.py --keyword Python --city 上海 --pages 1
```

## 常见问题

### 1. 无法解析到职位数据

**原因：**
- 页面结构已变化
- API需要签名验证
- 需要登录才能访问

**解决方案：**
1. 检查网络连接和代理配置
2. 尝试使用不同的城市（如"全国"）
3. 查看日志了解具体错误信息
4. 如果API需要签名，可能需要实现签名算法或使用Selenium等工具

### 2. 城市编码未找到

**原因：**
- 输入的城市名称不在编码映射表中

**解决方案：**
- 使用标准城市名称（如"北京"、"上海"）
- 或使用"全国"进行搜索

### 3. 请求被限制

**原因：**
- 请求频率过高
- IP被限制

**解决方案：**
- 增加请求延迟（在config.yaml中调整delay_min和delay_max）
- 使用代理
- 减少爬取页数

## 配置说明

在 `config.yaml` 中配置：

```yaml
job51:
  keywords: ["Python"]
  cities: ["全国"]
  delay_min: 1.0      # 最小延迟（秒）
  delay_max: 2.0      # 最大延迟（秒）
  max_pages: 10       # 最大页数
```

## 调试方法

如果遇到问题，可以使用调试脚本：

```bash
python debug_job51.py
```

这会：
1. 获取页面内容
2. 检查是否包含JSON数据
3. 查找职位相关链接
4. 保存完整HTML到 `job51_debug.html` 供分析

## 注意事项

1. **仅作学习交流使用**：请遵守相关法律法规和平台使用条款
2. **请求频率**：建议延迟设置在1-3秒之间
3. **页数限制**：建议单次爬取不超过10页
4. **数据准确性**：由于页面结构可能变化，解析的数据可能不完整
