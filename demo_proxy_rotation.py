from crawl4ai import *
import asyncio

async def demo_proxy_rotation():
    """Proxy rotation for multiple requests"""
    print("\n=== 10. Proxy Rotation ===")

    # Example proxies (replace with real ones)
    proxies = [
        ProxyConfig(server="http://example.com:8080"),
    ]

    proxy_strategy = RoundRobinProxyStrategy(proxies)

    print(f"Using {len(proxies)} proxies in rotation")
    print(
        "* Note: This example uses placeholder proxies - replace with real ones to test"
    )

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(
            url="https://docs.crawl4ai.com",
            config=CrawlerRunConfig(
                proxy_rotation_strategy=proxy_strategy, cache_mode=CacheMode.BYPASS
            )
        )

    # In a real scenario, these would be run and the proxies would rotate
    print("In a real scenario, requests would rotate through the available proxies")

if __name__ == "__main__":
    asyncio.run(demo_proxy_rotation())
