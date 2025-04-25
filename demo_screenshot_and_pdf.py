import asyncio
import json
import os  # 添加os模块
import base64  # 添加base64模块
from typing import List  # 添加List类型
from crawl4ai import *
import pprint

# 定义当前目录
__cur_dir__ = os.path.dirname(os.path.abspath(__file__))

async def demo_screenshot_and_pdf():
    """Capture screenshot and PDF of a page"""
    print("\n=== 9. Screenshot and PDF Capture ===")

    async with AsyncWebCrawler() as crawler:
        result: List[CrawlResult] = await crawler.arun(
            # url="https://example.com",
            url="https://en.wikipedia.org/wiki/Giant_anteater",
            config=CrawlerRunConfig(screenshot=True, pdf=True),
        )

        for i, result in enumerate(result):
            if result.screenshot:
                # Save screenshot
                screenshot_path = f"{__cur_dir__}/tmp/example_screenshot.png"
                # 确保tmp文件夹存在
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                with open(screenshot_path, "wb") as f:
                    f.write(base64.b64decode(result.screenshot))
                print(f"Screenshot saved to {screenshot_path}")

            if result.pdf:
                # Save PDF
                pdf_path = f"{__cur_dir__}/tmp/example_pdf.pdf"  # 添加.pdf扩展名
                # 确保tmp文件夹存在
                os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                with open(pdf_path, "wb") as f:
                    f.write(result.pdf)
                print(f"PDF saved to {pdf_path}")

if __name__ == "__main__":
    asyncio.run(demo_screenshot_and_pdf())
