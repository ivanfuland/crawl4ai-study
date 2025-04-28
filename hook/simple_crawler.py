import asyncio
import json
import os
import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from playwright.async_api import Page, BrowserContext, async_playwright
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from dotenv import load_dotenv
import datetime

# 加载.env文件中的环境变量
load_dotenv()

# 强制设置环境变量
os.environ["PLAYWRIGHT_BROWSER_VISIBLE"] = "1"
os.environ["PLAYWRIGHT_FORCE_VISIBLE"] = "1"  # 额外强制可见


# 全局配置 - 从环境变量中读取
TARGET_URL = os.getenv("TARGET_URL")
COOKIE_PATH = os.getenv("COOKIE_PATH")
LOGIN_URL = os.getenv("LOGIN_URL")
LOGIN_TIMEOUT = int(os.getenv("LOGIN_TIMEOUT"))  # 登录等待时间（秒）
DEBUG = False

# 配置文件路径
CONFIG_FILE_PATH = "output/site_configs.json"

# 加载或创建网站配置
def load_or_create_site_configs():
    try:
        # 确保output目录存在
        os.makedirs(os.path.dirname(CONFIG_FILE_PATH), exist_ok=True)
        
        # 尝试读取配置文件
        if os.path.exists(CONFIG_FILE_PATH):
            print(f"[CONFIG] 正在从 {CONFIG_FILE_PATH} 读取网站配置")
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # 如果配置文件不存在，直接报错
        raise FileNotFoundError(f"配置文件 {CONFIG_FILE_PATH} 不存在，请先创建配置文件")
        
    except Exception as e:
        # 不再返回默认配置，直接抛出异常
        raise Exception(f"加载配置文件出错: {e}")

# 加载网站配置
SITE_CONFIGS = load_or_create_site_configs()

# 打印当前配置
print("[CONFIG] 当前配置:")
print(f"[CONFIG] TARGET_URL: {TARGET_URL}")
print(f"[CONFIG] COOKIE_PATH: {COOKIE_PATH}")
print(f"[CONFIG] LOGIN_URL: {len(LOGIN_URL) > 20 and LOGIN_URL[:20]+'...' or LOGIN_URL}")
print(f"[CONFIG] DEBUG: {DEBUG}")
print(f"[CONFIG] 配置文件: {CONFIG_FILE_PATH}")
print(f"[CONFIG] 已加载网站配置: {', '.join([domain for domain in SITE_CONFIGS.keys() if domain != 'default'])}")
if DEBUG:
    print("[CONFIG] 网站配置详情:")
    for domain, config in SITE_CONFIGS.items():
        print(f"  - {domain}:")
        for key, value in config.items():
            if isinstance(value, list) and len(value) > 3:
                print(f"    {key}: [{value[0]}, {value[1]}, ... +{len(value)-2}项]")
            else:
                print(f"    {key}: {value}")

# 保存网站配置
def save_site_configs(configs):
    try:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)
        print(f"[CONFIG] 已保存网站配置到 {CONFIG_FILE_PATH}")
        return True
    except Exception as e:
        print(f"[CONFIG] 保存配置文件出错: {e}")
        return False

async def manual_login():
    """使用直接的playwright方式打开浏览器登录，并暂停等待用户手动操作。"""
    print("[LOGIN] 正在启动直接浏览器登录...")
    
    # 确保output目录存在
    os.makedirs(os.path.dirname(COOKIE_PATH), exist_ok=True)
    
    async with async_playwright() as playwright:
        # 启动浏览器
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                "--disable-gpu",
                "--no-sandbox",
                "--disable-web-security",
                "--window-size=1280,800"
            ]
        )
        
        # 创建上下文
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        
        # 打开页面
        page = await context.new_page()
        print("[LOGIN] 成功创建浏览器窗口")
        
        # 访问登录页面
        print(f"[LOGIN] 正在导航到登录页面: {LOGIN_URL}")
        await page.goto(LOGIN_URL)
        await page.wait_for_load_state("networkidle")
        print("[LOGIN] 已加载登录页面")
        
        # >>> 暂停等待手动登录 <<<
        print("\n>>> [LOGIN] 脚本已暂停，请在弹出的浏览器窗口中完成登录操作.<<<")
        print(">>> 完成登录后，请回到这里，按 'Resume' (或类似按钮) 恢复脚本执行.<<<\n")
        await page.pause() 
        # 用户在此处手动登录，然后手动恢复脚本

        print("[LOGIN] 脚本已恢复执行，正在检查登录状态...")
        login_success = False
        try:
            # --- 从配置中获取登录成功指标 ---
            # 首先尝试确定当前页面对应哪个域名配置
            current_domain = None
            for domain in SITE_CONFIGS.keys():
                if domain != "default" and domain in page.url:
                    current_domain = domain
                    break
            
            # 获取对应的登录成功指标
            login_indicators = None
            if current_domain:
                login_indicators = SITE_CONFIGS[current_domain].get("login_success_indicators", {})
                print(f"[LOGIN CHECK] 使用 {current_domain} 的登录检测规则")
            else:
                # 如果找不到匹配的域名配置，使用默认配置
                login_indicators = SITE_CONFIGS["default"].get("login_success_indicators", {})
                print("[LOGIN CHECK] 未找到匹配的域名配置，使用默认登录检测规则")
            
            # 对URL进行检查
            url_check_passed = True
            
            # 检查URL包含项
            for url_fragment in login_indicators.get("url_contains", []):
                if url_fragment not in page.url:
                    print(f"[LOGIN CHECK] URL不包含 '{url_fragment}'")
                    url_check_passed = False
                    break
                else:
                    print(f"[LOGIN CHECK] URL包含 '{url_fragment}' ✓")
            
            # 检查URL不包含项
            for url_fragment in login_indicators.get("url_not_contains", []):
                if url_fragment in page.url:
                    print(f"[LOGIN CHECK] URL包含被排除的字符串 '{url_fragment}'")
                    url_check_passed = False
                    break
                else:
                    print(f"[LOGIN CHECK] URL不包含排除项 '{url_fragment}' ✓")
            
            # 如果URL检查通过，检查DOM元素
            if url_check_passed:
                elements_check_passed = True
                for selector in login_indicators.get("elements_exist", []):
                    element = await page.query_selector(selector)
                    if not element:
                        print(f"[LOGIN CHECK] 未找到元素 '{selector}'")
                        elements_check_passed = False
                        break
                    else:
                        print(f"[LOGIN CHECK] 找到元素 '{selector}' ✓")
                
                # 综合判断
                login_success = elements_check_passed

        except Exception as e:
            print(f"[LOGIN CHECK] 检查登录状态时出错: {e}")
            login_success = False # 出错则认为未登录
        
        if login_success:
            print("[LOGIN] 检测到登录成功！保存cookie...")
            cookies = await context.cookies()
            # 确保output目录存在
            os.makedirs(os.path.dirname(COOKIE_PATH), exist_ok=True)
            with open(COOKIE_PATH, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            print(f"[LOGIN] 已保存cookies到 {COOKIE_PATH}")
            
            await browser.close()
            print("[LOGIN] 浏览器已关闭")
            return True
        else:
            print("[LOGIN] 未能确认登录成功，请检查登录操作或登录成功判断逻辑")
            await browser.close()
            print("[LOGIN] 浏览器已关闭")
            return False

# 通用的登录状态检查函数
async def check_login_status(page, domain=None):
    """
    根据配置检查页面是否处于登录状态
    Args:
        page: playwright页面对象
        domain: 可选，指定域名，如不指定则从URL自动判断
    Returns:
        bool: 是否已登录
    """
    try:
        # 如果未指定域名，尝试从URL中提取
        if not domain:
            for config_domain in SITE_CONFIGS.keys():
                if config_domain != "default" and config_domain in page.url:
                    domain = config_domain
                    break
        
        # 获取登录指标
        login_indicators = None
        if domain and domain in SITE_CONFIGS:
            login_indicators = SITE_CONFIGS[domain].get("login_success_indicators", {})
        else:
            login_indicators = SITE_CONFIGS["default"].get("login_success_indicators", {})
        
        # 验证URL包含项
        for url_fragment in login_indicators.get("url_contains", []):
            if url_fragment not in page.url:
                return False
        
        # 验证URL不包含项
        for url_fragment in login_indicators.get("url_not_contains", []):
            if url_fragment in page.url:
                return False
        
        # 验证DOM元素存在
        for selector in login_indicators.get("elements_exist", []):
            element = await page.query_selector(selector)
            if not element:
                return False
                
        # 所有检查通过
        return True
    except Exception as e:
        print(f"[LOGIN CHECK] 检查登录状态出错: {e}")
        return False  # 出错时默认为未登录

async def main():
    """原爬虫主函数"""
    print("🔗 简化版爬虫：利用crawl4ai原生功能，保留cookie验证")
    
    # 检查是否需要手动登录
    if not os.path.exists(COOKIE_PATH):
        print(f"[MAIN] Cookie文件不存在于 {COOKIE_PATH}，需要先进行手动登录")
        login_success = await manual_login()
        if not login_success:
            print("[MAIN] 登录失败，请重试")
            return
    
    # 1) 配置浏览器
    browser_config = BrowserConfig(
        headless=False,  # 可视模式，便于调试
        viewport={"width": 1280, "height": 800},
        verbose=True
    )

    # 2) 配置爬虫运行参数
    crawler_run_config = CrawlerRunConfig(
        js_code="""
            // 尝试展开内容和移除遮挡
            function enhancePage() {
                // 点击展开按钮
                const expandButtons = document.querySelectorAll('.read-more, .expand, .show-more, .view-all, button:contains("查看更多")');
                for (const button of expandButtons) {
                    button.click();
                }
                
                // 滚动页面触发加载
                window.scrollTo(0, document.body.scrollHeight);
                
                // 移除遮挡层
                const overlays = document.querySelectorAll('.overlay, .mask, .modal, .login-modal');
                for (const overlay of overlays) {
                    overlay.remove();
                }
                
                // 确保可以滚动
                document.body.style.overflow = 'auto';               
            }
            
            // 执行页面增强
            enhancePage();
            setTimeout(enhancePage, 3000); // 增加延时至3秒，给内容更多加载时间
        """,
        wait_for="body", 
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            # 使用基本配置
            content_filter=PruningContentFilter(),
            options={
                "ignore_links": False,
                "escape_html": True
            }
        )
    )

    # 3) 创建爬虫实例
    crawler = AsyncWebCrawler(config=browser_config)

    # 登录状态管理
    login_status = {
        "is_logged_in": False,
        "cookies_loaded": False
    }

    # Hook: 页面和上下文创建后
    async def on_page_context_created(page: Page, context: BrowserContext, **kwargs):
        print("[HOOK] 设置页面和上下文...")
        
        # 设置超时
        page.set_default_timeout(60000)
        
        # 尝试加载已保存的cookie
        if os.path.exists(COOKIE_PATH):
            try:
                with open(COOKIE_PATH, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    if cookies and len(cookies) > 0:
                        await context.add_cookies(cookies)
                        print(f"[HOOK] 成功加载 {len(cookies)} 个cookie")
                        login_status["cookies_loaded"] = True
                        # 不再假设cookie一定有效，将在页面加载后检查
                        login_status["is_logged_in"] = False  # 初始设为False，等页面加载后验证
                        print("[HOOK] Cookie已加载，登录状态将在页面加载后验证")
                    else:
                        print("[HOOK] Cookie文件存在但为空或无效")
            except Exception as e:
                print(f"[HOOK] 加载Cookie失败: {str(e)}")
        
        return page

    # Hook: 页面导航前
    async def before_goto(page: Page, context: BrowserContext, url: str, **kwargs):
        print(f"[HOOK] 准备访问: {url}")
        
        # 基本HTTP头
        headers = {
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        
        # 设置HTTP头
        await page.set_extra_http_headers(headers)
        
        return page

    # Hook: 页面导航后
    async def after_goto(page: Page, context: BrowserContext, url: str, response, **kwargs):
        print(f"[HOOK] 已加载页面: {url}")
        
        # 提取域名
        domain = None
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            domain = match.group(1)
        
        # 根据URL确定使用哪个网站配置
        site_config = None
        matched_domain = None
        for config_domain, config in SITE_CONFIGS.items():
            if config_domain != "default" and config_domain in url:
                site_config = config
                matched_domain = config_domain
                print(f"[HOOK] 使用 {config_domain} 的配置")
                break
        
        # 如果没有匹配的配置，使用默认配置
        if site_config is None:
            site_config = SITE_CONFIGS["default"]
            print(f"[HOOK] 未找到匹配的域名配置，使用默认配置")
            # 提取当前域名仅用于日志记录
            if domain:
                print(f"[HOOK] 当前域名: {domain} (未配置)")
        
        try:
            # 等待页面加载
            wait_for_load = site_config.get("wait_for_load", "domcontentloaded")
            timeout = site_config.get("timeout", 10000)
            print(f"[HOOK] 等待页面加载 ({wait_for_load})，超时: {timeout}ms")
            await page.wait_for_load_state(wait_for_load, timeout=timeout)
            
            # 检查内容是否可见
            content_selectors = site_config.get("content_selectors", [])
            if content_selectors:
                selector_str = ", ".join(content_selectors)
                content_visible = await page.is_visible(selector_str, timeout=3000)
                print(f"[HOOK] 内容可见性检查: {content_visible}")
                
                # 如果配置了需要刷新检查且内容不可见，尝试刷新
                if not content_visible and site_config.get("needs_refresh_check", False) and login_status["cookies_loaded"]:
                    print("[HOOK] 内容不可见，尝试刷新页面...")
                    await page.reload()
                    await page.wait_for_load_state(wait_for_load, timeout=timeout)
                    
                    # 再次检查内容可见性
                    content_visible = await page.is_visible(selector_str, timeout=3000)
                    if not content_visible:
                        print("[HOOK] 刷新后仍无法看到内容，检查登录状态...")
                        # 使用通用登录检查函数
                        login_status["is_logged_in"] = await check_login_status(page, matched_domain)
                        if not login_status["is_logged_in"]:
                            print("[HOOK] 登录检查失败，Cookie可能已失效")
                        else:
                            print("[HOOK] 登录状态正常，但内容仍然不可见")
            
            # 额外等待时间
            extra_wait = site_config.get("extra_wait", 0)
            if extra_wait > 0:
                print(f"[HOOK] 额外等待 {extra_wait} 秒...")
                await asyncio.sleep(extra_wait)
            
            # 执行滚动行为
            scroll_behavior = site_config.get("scroll_behavior", None)
            if scroll_behavior:
                print(f"[HOOK] 执行滚动行为: {scroll_behavior}")
                if scroll_behavior == "full":
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                elif scroll_behavior == "half_then_full":
                    await page.evaluate("""
                        window.scrollTo(0, document.body.scrollHeight / 2);
                        setTimeout(() => {
                            window.scrollTo(0, document.body.scrollHeight);
                        }, 1000);
                    """)
                await asyncio.sleep(2)  # 滚动后等待
            
            # 调试模式下截图
            if DEBUG and site_config.get("screenshot_debug", False):
                filename = url.split("//")[-1].replace("/", "_")[:30]
                screenshot_path = f"debug_{filename}.png"
                print(f"[HOOK] 保存页面截图到 {screenshot_path}")
                await page.screenshot(path=screenshot_path, full_page=True)
                
        except Exception as e:
            print(f"[HOOK] 处理页面时出错: {e}")
            # 继续执行，不中断流程
        
        return page

    # 注册钩子函数
    crawler.crawler_strategy.set_hook("on_page_context_created", on_page_context_created)
    crawler.crawler_strategy.set_hook("before_goto", before_goto)
    crawler.crawler_strategy.set_hook("after_goto", after_goto)

    # 启动爬虫
    await crawler.start()

    # 运行爬虫访问目标URL
    result = await crawler.arun(TARGET_URL, config=crawler_run_config)

    if result.success:
        print("\n爬取成功！")
        print("URL:", result.url)
        print("HTML长度:", len(result.html))
        print(f"登录状态: {'已登录' if login_status['is_logged_in'] else '未登录'}")
        
        # 从metadata获取标题
        page_title = "未知标题"
        if hasattr(result, 'metadata') and result.metadata and result.metadata.get("title"):
            page_title = result.metadata.get("title")
            print(f"页面标题: {page_title}")
        
        # 处理页面标题，替换非法字符，用于创建文件夹
        safe_title = "".join([c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in page_title])
        safe_title = safe_title.strip()
        if len(safe_title) > 50:
            safe_title = safe_title[:50]
        
        # 添加时间戳确保唯一性
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = f"{safe_title}_{timestamp}" if safe_title else f"unnamed_page_{timestamp}"
        
        # 根据页面标题创建目录
        title_dir = os.path.join("output", safe_title)
        os.makedirs(title_dir, exist_ok=True)
        print(f"[OUTPUT] 创建目录: {title_dir}")
        
        # 保存HTML结果
        html_path = os.path.join(title_dir, "crawled_content.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(result.html)
            print(f"已保存HTML内容到 {html_path}")        
        
        # 保存Markdown结果
        md_path = os.path.join(title_dir, "crawled_content.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(result.markdown.fit_markdown)
            print(f"已保存Markdown内容到 {md_path}")
    else:
        print("爬取失败:", result.error_message)

    await crawler.close()

if __name__ == "__main__":
    asyncio.run(main()) 