import asyncio
from crawl4ai import *
import pprint

async def demo_parallel_crawl():
    """Crawl multiple URLs in parallel"""
    print("\n=== 2. Parallel Crawling ===")

    urls = [
        "https://news.ycombinator.com/",
        "https://example.com/",
        "https://httpbin.org/html",
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

if __name__ == "__main__":
    asyncio.run(demo_parallel_crawl())
