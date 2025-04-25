import asyncio
from crawl4ai import *
import pprint

async def demo_parallel_crawl():
    """Crawl multiple URLs in parallel"""
    print("\n=== 2. Parallel Crawling ===")

    urls = [
        "https://www.aibase.com/zh/news/17507",
        "https://www.aibase.com/zh/news/17505",
        "https://www.aibase.com/zh/news/17502",
    ]

    async with AsyncWebCrawler() as crawler:
        results: List[CrawlResult] = await crawler.arun_many(
            urls=urls,
        )

    print(f"Crawled {len(results)} URLs in parallel:")
    for i, result in enumerate(results):
        print(
            f"{i + 1}. {result.url} - {'Success' if result.success else 'Failed'}"
        )
        print(f"First 100 chars: {result.markdown.raw_markdown[:100]}...")

if __name__ == "__main__":
    asyncio.run(demo_parallel_crawl())
