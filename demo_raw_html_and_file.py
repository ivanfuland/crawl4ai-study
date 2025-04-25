from crawl4ai import *
import os
from pathlib import Path    
import asyncio

async def demo_raw_html_and_file():
    """Process raw HTML and local files"""
    print("\n=== 11. Raw HTML and Local Files ===")

    raw_html = """
    <html><body>
        <h1>Sample Article</h1>
        <p>This is sample content for testing Crawl4AI's raw HTML processing.</p>
    </body></html>
    """

    # Save to file
    file_path = Path("tmp/sample.html").absolute()
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 如果文件已存在，先删除它
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"已删除现有文件: {file_path}")
    
    with open(file_path, "w") as f:
        f.write(raw_html)
    
    # 验证文件写入成功
    # print(f"\n文件已保存到: {file_path}")
    # print(f"文件大小: {os.path.getsize(file_path)} 字节")

    async with AsyncWebCrawler() as crawler:
        # Crawl raw HTML
        raw_result = await crawler.arun(
            url="raw:" + raw_html, config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        )
        print("\nRaw HTML processing:")
        print(f"Markdown: {raw_result.markdown.raw_markdown[:50]}...")

        # 读取本地文件内容
        with open(file_path, "r") as f:
            local_file_html = f.read()
            
        # 使用raw:协议处理本地文件内容
        file_result = await crawler.arun(
            url="raw:" + local_file_html,
            config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        )
        print("\nLocal file processing:")
        print(f"Markdown: {file_result.markdown.raw_markdown[:50]}...")

    # 不删除文件，让它保留在目录中
    # os.remove(file_path)  # 注释掉删除文件的代码
    # print(f"Processed both raw HTML and local file ({file_path})")
    # print(f"文件已保留在目录中，可以在以下位置找到: {file_path}")

if __name__ == "__main__":
    asyncio.run(demo_raw_html_and_file())
