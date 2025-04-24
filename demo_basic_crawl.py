import asyncio
from crawl4ai import *
import pprint


async def demo_basic_crawl():
    """
    演示如何使用 crawl4ai 库进行基本的网页抓取，
    并将抓取到的内容转换为 Markdown 格式。
    """
    # 打印标题，标识当前操作
    print("\n== 1. Basic Web Crawling ==")

    # 创建 AsyncWebCrawler 实例。
    # 使用 async with 确保资源在使用后正确释放。
    async with AsyncWebCrawler() as crawler:
        # 异步执行抓取任务，目标 URL 是一个 36kr 的文章页面。
        # arun 返回一个包含 CrawlResult 对象的列表。
        results: List[CrawlResult] = await crawler.arun(
            url="https://www.36kr.com/p/3263507071788289",
        )

        # 遍历抓取结果列表 (通常只有一个结果，除非有重定向或错误)
        for i, result in enumerate(results):
            print(f"Result {i + 1}:")

            print(f"raw_markdown: {result.markdown.raw_markdown}")
            print(f"fit_markdown: {result.markdown.fit_markdown}")
            print(f"fit_html: {result.markdown.fit_html}")

            # if result.success:
            #     # 如果成功，打印 Markdown 内容的长度
            #     print(f"Markdown length: {len(result.markdown.raw_markdown)} chars")
            #     # 打印 Markdown 内容的前 100 个字符作为预览
            #     print(f"First 100 chars: {result.markdown.raw_markdown[:100]}...")
            # else:
            #     # 如果失败，打印失败信息
            #     print("Failed to crawl the URL")

# 当脚本作为主程序直接运行时执行以下代码
if __name__ == "__main__":
    # 使用 asyncio.run() 来运行异步函数 demo_basic_crawl
    asyncio.run(demo_basic_crawl())
