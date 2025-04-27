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

# 打印当前配置
print("[CONFIG] 当前配置:")
print(f"[CONFIG] TARGET_URL: {TARGET_URL}")
print(f"[CONFIG] COOKIE_PATH: {COOKIE_PATH}")
print(f"[CONFIG] LOGIN_URL: {len(LOGIN_URL) > 20 and LOGIN_URL[:20]+'...' or LOGIN_URL}")
print(f"[CONFIG] DEBUG: {DEBUG}")

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
            # --- 登录成功检查逻辑 ---
            # 检查1: URL是否已跳转到目标KM网站
            if "km.netease.com" in page.url and "login.netease.com" not in page.url:
                 print("[LOGIN CHECK] 检测到URL已跳转至 km.netease.com")
                 login_success = True
            
            # 检查2: (可选) 检查页面上是否出现特定元素，例如用户名或退出按钮
            # 请根据实际情况修改下面的选择器
            # if not login_success:
            #    user_element_selector = ".user-name, #logout-button, .avatar" # 示例选择器
            #    user_element = await page.query_selector(user_element_selector)
            #    if user_element:
            #        print(f"[LOGIN CHECK] 检测到用户元素: {user_element_selector}")
            #        login_success = True

            # 检查3: (备用) 之前的检查逻辑，检查 URL 是否包含 /dweb2/ 或用户头像等
            if not login_success:
                 if "login" not in page.url and "/dweb2/" in page.url: # 之前的逻辑
                     print("[LOGIN CHECK] 检测到 URL 不含 'login' 且包含 '/dweb2/' (旧逻辑)")
                     login_success = True
            if not login_success:
                 has_user_avatar = await page.query_selector(".user-avatar, .username, .user-info") # 之前的逻辑
                 if has_user_avatar:
                    print("[LOGIN CHECK] 检测到用户头像/信息元素 (旧逻辑)")
                    login_success = True

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
            
            # # 测试跳转到文章页面 (暂时注释掉，避免干扰)
            # print("[LOGIN] 正在测试访问文章页面...")
            # await page.goto(TARGET_URL)
            # await page.wait_for_load_state("networkidle")
            # await page.screenshot(path="article_test.png")
            # print("[LOGIN] 已保存文章页面截图到article_test.png")
            
            await browser.close()
            print("[LOGIN] 浏览器已关闭")
            return True
        else:
            print("[LOGIN] 未能确认登录成功，请检查登录操作或登录成功判断逻辑")
            await browser.close()
            print("[LOGIN] 浏览器已关闭")
            return False

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
        
        # 如果是网易KM网站 
        elif "km.netease.com" in url:
            print("[HOOK] 检测到网易KM页面，进行特殊处理...")
            
            # 等待网络空闲，等待时间稍长一些 (30秒)
            try:
                print("[HOOK] 等待网络空闲...")
                await page.wait_for_load_state("networkidle", timeout=30000)
                print("[HOOK] 网络空闲状态已达成")
                
                # 额外等待可能的动态内容
                print("[HOOK] 等待额外5秒以确保动态内容加载...")
                await asyncio.sleep(5)
                
                # 执行滚动以触发可能的懒加载
                print("[HOOK] 执行滚动以触发懒加载...")
                await page.evaluate("""
                    window.scrollTo(0, document.body.scrollHeight / 2);
                    setTimeout(() => {
                        window.scrollTo(0, document.body.scrollHeight);
                    }, 1000);
                """)
                
                # 再等待以确保内容加载
                await asyncio.sleep(2)
                
                # 检查KM页面上内容元素是否存在
                content_selectors = [
                    ".article-content", 
                    ".km-blog-content", 
                    ".markdown-body", 
                    "article", 
                    ".content-wrapper"
                ]
                
                for selector in content_selectors:
                    if await page.is_visible(selector, timeout=1000):
                        print(f"[HOOK] 检测到内容元素: {selector}")
                        break
                else:
                    print("[HOOK] 未找到预期的内容元素，但继续尝试抓取...")
                
                # 调试模式下截图
                if DEBUG:
                    print("[HOOK] 保存页面截图...")
                    await page.screenshot(path="km_debug.png", full_page=True)
                    
            except Exception as e:
                print(f"[HOOK] 处理KM页面时出错: {e}")
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