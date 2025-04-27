import asyncio
import json
import os
import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from playwright.async_api import Page, BrowserContext
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# 全局配置
TARGET_URL = "https://articles.zsxq.com/id_m5c8015ehlem.html"
COOKIE_PATH = "zsxq_cookies.json"
LOGIN_URL = "https://wx.zsxq.com/dweb2/login"
LOGIN_TIMEOUT = 60  # 登录等待时间（秒）
DEBUG = True

async def main():
    print("🔗 简化版爬虫：利用crawl4ai原生功能，保留cookie验证")

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

    # 处理登录的函数
    async def handle_login(page: Page, context: BrowserContext):
        print("[HOOK] 尝试登录知识星球...")
        
        try:
            # 确认在登录页面
            if "login" not in page.url and not await page.is_visible(".login-btn, .sign-in, .login-wall"):
                await page.goto(LOGIN_URL)
                await page.wait_for_load_state("networkidle")
            
            # 先尝试使用已有cookie
            if os.path.exists(COOKIE_PATH) and os.path.getsize(COOKIE_PATH) > 10:
                try:
                    print("[HOOK] 检测到cookie文件，尝试使用...")
                    with open(COOKIE_PATH, "r", encoding="utf-8") as f:
                        cookies = json.load(f)
                    
                    if cookies and len(cookies) > 0:
                        await context.add_cookies(cookies)
                        await page.reload()
                        await page.wait_for_load_state("networkidle")
                        
                        # 检查登录状态
                        await asyncio.sleep(3)
                        if not await page.is_visible(".login-btn, .sign-in, .login-wall"):
                            print("[HOOK] 使用cookie登录成功!")
                            login_status["is_logged_in"] = True
                            return True
                        else:
                            print("[HOOK] 使用cookie登录失败，需要手动登录")
                except Exception as e:
                    print(f"[HOOK] 使用cookie登录出错: {str(e)}")
            
            # 等待手动登录
            print(f"\n[HOOK] 请在浏览器中手动登录，将等待{LOGIN_TIMEOUT}秒...")
            print("[HOOK] 支持微信扫码登录...")
            
            for i in range(LOGIN_TIMEOUT, 0, -5):
                print(f"[HOOK] 等待登录...剩余{i}秒")
                await asyncio.sleep(5)
                
                # 检查登录状态
                login_success = False
                
                # 检查URL
                if "login" not in page.url and "/dweb2/" in page.url:
                    login_success = True
                
                # 检查用户元素
                try:
                    if await page.query_selector(".user-avatar, .username, .user-info"):
                        login_success = True
                except:
                    pass
                
                # 检查登录元素是否消失
                if not await page.is_visible(".login-btn, .sign-in, .login-wall"):
                    login_success = True
                
                if login_success:
                    print("[HOOK] 检测到登录成功！")
                    login_status["is_logged_in"] = True
                    
                    # 保存cookies
                    cookies = await context.cookies()
                    with open(COOKIE_PATH, "w", encoding="utf-8") as f:
                        json.dump(cookies, f, ensure_ascii=False, indent=2)
                    print(f"[HOOK] 已保存cookies到 {COOKIE_PATH}")
                    
                    return True
            
            print("[HOOK] 登录超时，请重试")
            return False
            
        except Exception as e:
            print(f"[HOOK] 登录过程中出错: {str(e)}")
            return False

    # Hook: 页面导航后
    async def after_goto(page: Page, context: BrowserContext, url: str, response, **kwargs):
        print(f"[HOOK] 已加载页面: {url}")
        
        # 如果是知识星球网站
        if "zsxq.com" in url:
            await page.wait_for_load_state("networkidle")
            
            # 检查内容是否可见
            content_visible = await page.is_visible(".article-title, .content, article, .post-content", timeout=3000)
            
            # 如果内容不可见且未登录，进行登录
            if not content_visible and not login_status["is_logged_in"]:
                print("[HOOK] 内容不可见，尝试登录...")
                await page.goto(LOGIN_URL)
                await page.wait_for_load_state("networkidle")
                
                # 登录
                await handle_login(page, context)
                
                # 登录成功后返回原页面
                if login_status["is_logged_in"]:
                    print("[HOOK] 登录成功，返回原始页面")
                    await page.goto(url)
                    await page.wait_for_load_state("networkidle")
            
            # 如果加载了cookie但内容不可见
            elif login_status["cookies_loaded"] and not content_visible:
                print("[HOOK] 已加载Cookie但内容不可见，可能Cookie已过期")
                await page.reload()
                
                # 再次检查内容
                content_visible_after_refresh = await page.is_visible(".article-title, .content, article, .post-content", timeout=3000)
                if not content_visible_after_refresh:
                    print("[HOOK] 刷新后仍无法看到内容，尝试重新登录")
                    login_status["is_logged_in"] = False
                    
                    await page.goto(LOGIN_URL)
                    await page.wait_for_load_state("networkidle")
                    await handle_login(page, context)
                    
                    if login_status["is_logged_in"]:
                        await page.goto(url)
                        await page.wait_for_load_state("networkidle")
            
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