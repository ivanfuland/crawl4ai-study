from crawl4ai import *
import os
from pathlib import Path    
import asyncio

async def demo_deep_crawl():
    """Deep crawling with BFS strategy"""
    print("\n=== 6. Deep Crawling ===")

    filter_chain = FilterChain([
        DomainFilter(allowed_domains=["crawl4ai.com"])
    ])

    deep_crawl_strategy = BFSDeepCrawlStrategy(
        max_depth=1, max_pages=5, filter_chain=filter_chain
    )

    async with AsyncWebCrawler() as crawler:
        results: List[CrawlResult] = await crawler.arun(
            url="https://docs.crawl4ai.com",
            config=CrawlerRunConfig(deep_crawl_strategy=deep_crawl_strategy),
        )

    print(f"Deep crawl returned {len(results)} pages:")
    for i, result in enumerate(results):
        depth = result.metadata.get("depth", "unknown")
        print(f"{i + 1}. {result.url} (Depth: {depth})")

if __name__ == "__main__":
    asyncio.run(demo_deep_crawl())

