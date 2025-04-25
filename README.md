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

## 环境变量配置

本项目使用 `.env` 文件存储敏感信息（如 API 密钥）。出于安全考虑，此文件不应提交到版本控制系统中。

请复制 `.env.example` 文件并将其重命名为 `.env`，然后填入您的实际 API 密钥：

```bash
# 在 Windows 上
copy .env.example .env

# 在 Linux/Mac 上
cp .env.example .env
```

然后编辑 `.env` 文件，添加您的实际 API 密钥：

```
OPENAI_API_KEY=your_actual_api_key_here
```

或者，您也可以直接在系统中设置环境变量：

```bash
# Windows 命令行
set OPENAI_API_KEY=your_actual_api_key_here

# PowerShell
$env:OPENAI_API_KEY="your_actual_api_key_here"

# Linux/Mac
export OPENAI_API_KEY="your_actual_api_key_here"
```

## 项目文件

- `test.py`: 一个简单的示例，展示如何使用 crawl4ai 库抓取特定网页（36kr文章）
- `demo_basic_crawl.py`: 一个更详细的示例，演示如何进行基本的网页抓取并处理结果
- `demo_llm_structured_extraction_no_schema.py`: 演示如何使用 LLM 进行结构化数据提取
- `.env.example`: 环境变量配置模板，用于说明需要设置哪些环境变量

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