# Crawl4ai 使用指南

本项目演示了如何使用 crawl4ai 库进行网页内容抓取。

## 环境设置

请按照以下步骤设置您的环境:

```bash
# 创建名为 crawl4ai 的虚拟环境，使用 Python 3.10
conda create -n crawl4ai python=3.10 -y

# 激活虚拟环境
conda activate crawl4ai

# 安装 crawl4ai 库
pip install crawl4ai

# 运行 crawl4ai 安装后的设置程序
crawl4ai-setup
```

安装过程中，crawl4ai-setup 会自动执行以下操作：
- 安装 Playwright 浏览器（包括 Chromium）
- 初始化数据库
- 完成所有必要的后续配置

## 项目文件

- `test.py`: 一个简单的示例，展示如何使用 crawl4ai 库抓取特定网页（36kr文章）
- `demo_basic_crawl`: 一个更详细的示例，演示如何进行基本的网页抓取并处理结果

## 运行示例

运行 test.py 示例:

```bash
python test.py
```

test.py 中的代码将:
1. 创建一个 AsyncWebCrawler 实例，设置页面超时时间为120秒
2. 抓取 36kr 网站上的一篇文章
3. 将抓取到的内容以 Markdown 格式打印出来

运行结果将展示网页的抓取过程，包括:
- 初始化信息（Crawl4AI 版本）
- 获取和抓取目标网页的状态
- 完成状态和耗时统计
- 最终抓取的 Markdown 内容

## 高级配置

crawl4ai 支持多种高级配置选项，包括:
- 设置页面超时时间
- 配置地理位置信息
- 自定义浏览器语言和时区

请参考代码中的注释了解更多信息。

---
注意: 请替换上述环境设置部分为您实际使用的命令。 