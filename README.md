# Crawl4ai 学习与演示项目

本项目旨在学习和演示 `crawl4ai` 库的各种功能，通过一系列示例代码展示其在网页抓取、数据提取和自动化方面的应用。

## 环境设置

请按照以下步骤设置您的开发环境:

1.  **创建并激活虚拟环境** (推荐使用 Conda):
    ```bash
    # 创建名为 crawl4ai 的虚拟环境，建议使用 Python 3.10 或更高版本
    conda create -n crawl4ai python=3.10 -y

    # 激活虚拟环境
    conda activate crawl4ai
    ```

2.  **安装 crawl4ai 库:**
    ```bash
    pip install crawl4ai
    ```

3.  **运行 crawl4ai 安装后的设置程序:**
    ```bash
    crawl4ai-setup
    ```
    此命令将自动执行以下操作：
    *   安装 Playwright 及其所需的浏览器驱动 (例如 Chromium)。
    *   初始化必要的数据库或配置。
    *   完成其他必要的设置。

## 环境变量配置

本项目可能需要使用 API 密钥或其他敏感配置（例如 OpenAI API Key 用于 LLM 提取）。这些信息通过 `.env` 文件管理。

1.  复制 `.env.example` 文件并重命名为 `.env`:
    ```bash
    # 在 Windows 上
    copy .env.example .env

    # 在 Linux/Mac 上
    cp .env.example .env
    ```

2.  编辑 `.env` 文件，填入您的实际密钥或配置值。例如：
    ```dotenv
    OPENAI_API_KEY=your_actual_openai_api_key_here
    # 根据需要添加其他环境变量，例如代理设置、登录凭据等
    ```

或者，您也可以直接在操作系统中设置环境变量。

## 配置文件说明

*   **`output/site_configs.json`**: (如果存在) 此文件用于存储针对特定网站的爬取配置。
    *   **用途**: 允许为不同域名（如 `zsxq.com`, `km.netease.com`）定制爬取行为，例如加载等待策略 (`wait_for_load`)、超时时间 (`timeout`)、滚动方式 (`scroll_behavior`) 以及 **登录成功判断逻辑 (`login_success_indicators`)**。
    *   **登录成功指示器**: `login_success_indicators` 部分非常重要，它定义了如何判断自动登录是否成功。可以基于 URL (`url_contains`, `url_not_contains`) 或页面上是否存在特定元素 (`elements_exist`) 来判断。
    *   **近期修改 (zsxq.com)**: 我们已更新 `zsxq.com` 的 `elements_exist` 列表，加入了 `.user-avatar`, `.user-container`, `.avatar`, `.header-container`, `app-header` 等选择器，以更准确地识别登录成功状态。
    *   **`default` 配置**: 提供一个默认配置集，适用于未在文件中显式定义的其他网站。

## 示例脚本说明

本项目包含多个 `demo_*.py` 脚本，演示了 `crawl4ai` 的不同功能：

*   `demo_basic_crawl.py`: 演示基本的网页抓取流程。
*   `demo_css_structured_extraction_no_schema.py`: 演示使用 CSS 选择器进行结构化数据提取，无需预定义 Schema。
*   `demo_deep_crawl.py`: 演示深度爬取，自动发现并抓取链接。
*   `demo_fit_markdown.py`: 演示如何优化和适配抓取的 Markdown 内容。
*   `demo_js_interaction.py`: 演示如何在抓取前或抓取过程中执行 JavaScript 脚本与页面交互（例如点击按钮、填充表单）。
*   `demo_llm_structured_extraction_no_schema.py`: 演示利用大型语言模型 (LLM) 进行结构化数据提取，无需预定义 Schema。
*   `demo_media_and_links.py`: 演示如何提取页面中的媒体文件（图片、视频）和链接。
*   `demo_parallel_crawl.py`: 演示如何并行抓取多个 URL 以提高效率。
*   `demo_proxy_rotation.py`: 演示如何配置和使用代理服务器进行抓取。
*   `demo_raw_html_and_file.py`: 演示如何获取原始 HTML 内容并将其保存到文件。
*   `demo_screenshot_and_pdf.py`: 演示如何对网页进行截图或将其保存为 PDF 文件。

## Hook 脚本说明

*   **`hook/simple_crawler.py`**: 此脚本是一个更复杂的示例，专门用于处理**需要登录**才能访问内容的网站。
    *   **主要功能**: 
        *   检查是否存在有效的 Cookie 文件 (路径由 `COOKIE_PATH` 环境变量指定)。
        *   如果 Cookie 不存在或无效，则启动一个**手动登录流程**: 打开浏览器让用户手动登录，然后根据配置验证登录状态并保存 Cookie。
        *   如果已有有效 Cookie，则加载 Cookie 进行后续抓取。
        *   使用 `crawl4ai` 抓取目标 URL (由 `TARGET_URL` 环境变量指定) 的内容。
        *   利用 `output/site_configs.json` 文件为目标网站定制爬取行为和登录验证逻辑。
    *   **如何配置 `site_configs.json`**: 
        *   此脚本**严重依赖** `output/site_configs.json` 文件来判断登录是否成功。
        *   您需要为目标网站的域名 (例如 `zsxq.com`) 添加一个条目。
        *   在该条目下，`login_success_indicators` 字段至关重要。
        *   配置 `url_contains` / `url_not_contains` 来指定登录成功后 URL 应包含/不应包含的特定字符串。
        *   配置 `elements_exist` 列表，包含一些只有在登录成功后页面上才会出现的 CSS 选择器。脚本会在用户手动登录后检查这些元素是否存在，以确认登录状态。
        *   您还可以配置 `wait_for_load`, `timeout`, `extra_wait`, `scroll_behavior` 等参数来优化该网站的爬取过程。
    *   **环境变量依赖**: 此脚本还需要设置 `TARGET_URL`, `COOKIE_PATH`, `LOGIN_URL` 等环境变量。

## 运行示例

要运行任何一个示例脚本，请确保您的虚拟环境已激活，并且已根据需要配置好 `.env` 文件。然后执行：

```bash
# 例如，运行基础爬取演示
python demo_basic_crawl.py

# 例如，运行 LLM 结构化提取演示 (需要配置 OpenAI API Key)
python demo_llm_structured_extraction_no_schema.py
```

请查看每个脚本的源代码以了解其具体功能和用法。

## 注意事项

*   请确保遵守目标网站的 `robots.txt` 规则和使用条款。
*   负责任地使用爬虫，避免对目标网站造成过大负担。
*   处理登录和 Cookie 时，请注意安全性和隐私保护。

---
注意: 请替换上述环境设置部分为您实际使用的命令。 