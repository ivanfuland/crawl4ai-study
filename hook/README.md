# 知识星球爬虫工具

这是一个专门为爬取知识星球文章内容设计的Python爬虫工具，使用crawl4ai库实现。该工具支持自动处理登录、保存cookie，并能有效提取文章内容，输出为HTML和Markdown格式。

## 功能特点

- **自动登录处理**：支持cookie持久化和微信扫码登录
- **内容增强**：自动点击"展开更多"按钮，移除遮挡层
- **完整提取**：获取文章的完整HTML和优化后的Markdown内容
- **可视化调试**：提供调试模式和截图功能
- **稳定可靠**：自动处理登录状态变化，处理cookie过期情况

## 依赖项

- Python 3.7+
- crawl4ai
- playwright
- asyncio

## 使用方法

### 安装依赖

```bash
pip install crawl4ai playwright asyncio
playwright install
```

### 配置目标URL

在脚本开头部分，可以修改以下配置常量：

```python
# 全局配置
TARGET_URL = "https://articles.zsxq.com/id_m5c8015ehlem.html"  # 目标文章URL
COOKIE_PATH = "zsxq_cookies.json"  # Cookie保存路径
LOGIN_TIMEOUT = 60  # 登录等待时间（秒）
DEBUG = True  # 是否启用调试
```

### 运行脚本

```bash
python simple_crawler.py
```

首次运行时，脚本会打开浏览器窗口等待您登录知识星球账号（支持微信扫码登录）。登录成功后，脚本会保存cookie以便后续使用。

## 工作原理

1. **Cookie管理**：脚本会自动检查是否有保存的cookie，有则尝试使用，无效则引导用户登录
2. **内容增强**：通过JavaScript脚本点击"展开更多"按钮并移除内容遮挡层
3. **异步处理**：使用asyncio和playwright实现高效的异步网页爬取
4. **智能提取**：使用crawl4ai的内容过滤机制提取有价值的内容

## 配置选项

您可以在脚本中修改以下配置来自定义爬虫行为：

- `browser_config`：浏览器配置（窗口大小、是否无头模式等）
- `crawler_run_config`：爬虫运行配置（JS增强脚本、等待策略等）
- `DEBUG`：调试模式（启用后会保存页面截图）

## 输出文件

脚本运行成功后，将生成以下文件：

- `crawled_content.html`：完整HTML内容
- `crawled_content.md`：优化后的Markdown内容
- `page_debug.png`：页面截图（仅在DEBUG=True时生成）
- `zsxq_cookies.json`：保存的cookie信息

## 注意事项

- 由于知识星球的反爬机制，过于频繁的访问可能导致账号被限制
- 请遵守知识星球的用户协议，不要爬取和分享付费内容
- 定期更新脚本以适应知识星球可能的界面变化 