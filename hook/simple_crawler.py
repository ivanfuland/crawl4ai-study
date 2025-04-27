import asyncio
import json
import os
import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from playwright.async_api import Page, BrowserContext, async_playwright
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


# 强制设置环境变量
import os
os.environ["PLAYWRIGHT_BROWSER_VISIBLE"] = "1"
os.environ["PLAYWRIGHT_FORCE_VISIBLE"] = "1"  # 额外强制可见


# 全局配置
TARGET_URL = "https://articles.zsxq.com/id_m5c8015ehlem.html"
COOKIE_PATH = "zsxq_cookies.json"
LOGIN_URL = "https://wx.zsxq.com/dweb2/login"
LOGIN_TIMEOUT = 60  # 登录等待时间（秒）
DEBUG = False

async def manual_login():
    """使用直接的playwright方式打开浏览器登录"""
    print("[LOGIN] 正在启动直接浏览器登录...")
    
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
        await page.goto(LOGIN_URL)
        await page.wait_for_load_state("networkidle")
        print("[LOGIN] 已加载登录页面")
        
        # 等待手动登录
        print(f"[LOGIN] 请在浏览器窗口中完成登录，等待{LOGIN_TIMEOUT}秒")
        
        login_success = False
        for i in range(LOGIN_TIMEOUT // 5):
            print(f"[LOGIN] 等待登录...剩余{LOGIN_TIMEOUT - i*5}秒")
            await asyncio.sleep(5)
            
            # 检查登录状态
            if "login" not in page.url and "/dweb2/" in page.url:
                login_success = True
                break
            
            try:
                has_user_avatar = await page.query_selector(".user-avatar, .username, .user-info")
                if has_user_avatar:
                    login_success = True
                    break
            except:
                pass
            
            if not await page.is_visible(".login-btn, .sign-in, .login-wall"):
                login_success = True
                break
        
        if login_success:
            print("[LOGIN] 登录成功！保存cookie...")
            cookies = await context.cookies()
            with open(COOKIE_PATH, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            print(f"[LOGIN] 已保存cookies到 {COOKIE_PATH}")
            
            # 测试跳转到文章页面
            print("[LOGIN] 正在测试访问文章页面...")
            await page.goto(TARGET_URL)
            await page.wait_for_load_state("networkidle")
            
            # 截图保存测试
            await page.screenshot(path="article_test.png")
            print("[LOGIN] 已保存文章页面截图到article_test.png")
            
            await browser.close()
            return True
        else:
            print("[LOGIN] 登录超时，请重试")
            await browser.close()
            return False

async def main():
    """原爬虫主函数"""
    print("🔗 简化版爬虫：利用crawl4ai原生功能，保留cookie验证")
    
    # 检查是否需要手动登录
    if not os.path.exists(COOKIE_PATH):
        print("[MAIN] Cookie文件不存在，需要先进行手动登录")
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
            setTimeout(enhancePage, 1500);
        """,
        wait_for="body",
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter()
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
                        login_status["is_logged_in"] = True  # 假设cookie有效
                    else:
                        print("[HOOK] Cookie文件存在但为空或无效")
            except Exception as e:
                print(f"[HOOK] 加载Cookie失败: {str(e)}")
        
        return page

    # Hook: 页面导航前
    async def before_goto(page: Page, context: BrowserContext, url: str, **kwargs):
        print(f"[HOOK] 准备访问: {url}")
        
        # 设置浏览器头信息
        await page.set_extra_http_headers({
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        })
        
        return page

    # Hook: 页面导航后
    async def after_goto(page: Page, context: BrowserContext, url: str, response, **kwargs):
        print(f"[HOOK] 已加载页面: {url}")
        
        # 如果是知识星球网站
        if "zsxq.com" in url:
            await page.wait_for_load_state("networkidle")
            
            # 检查内容是否可见
            content_visible = await page.is_visible(".article-title, .content, article, .post-content", timeout=3000)
            
            # 如果内容不可见且已加载cookie但有效，尝试刷新
            if not content_visible and login_status["cookies_loaded"]:
                print("[HOOK] 内容不可见，尝试刷新页面...")
                await page.reload()
                await page.wait_for_load_state("networkidle")
                
                # 再次检查内容可见性
                content_visible = await page.is_visible(".article-title, .content, article, .post-content", timeout=3000)
                if not content_visible:
                    print("[HOOK] 刷新后仍无法看到内容，Cookie可能已失效")
                    print("[HOOK] 请重新运行脚本并删除cookie文件以重新登录")
                    login_status["is_logged_in"] = False
            
            # 调试模式下截图
            if DEBUG:
                await page.screenshot(path="page_debug.png", full_page=True)
        
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
        
        # 保存HTML结果
        with open("crawled_content.html", "w", encoding="utf-8") as f:
            f.write(result.html)
            print("已保存HTML内容到 crawled_content.html")        
        
        # 保存Markdown结果
        with open("crawled_content.md", "w", encoding="utf-8") as f:
            f.write(result.markdown.fit_markdown)
            print("已保存Markdown内容到 crawled_content.md")
    else:
        print("爬取失败:", result.error_message)

    await crawler.close()

if __name__ == "__main__":
    asyncio.run(main()) 