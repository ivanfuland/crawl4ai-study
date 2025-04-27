import json
from pathlib import Path    
import asyncio
from typing import List
from crawl4ai import *


async def demo_js_interaction():
    # Execute JavaScript to load more content
    print("=== 7. JavaScript Interaction ===")

    # A simple page that needs JS to reveal content
    async with AsyncWebCrawler(config=BrowserConfig(headless=False)) as crawler:
        # Initial load
        news_schema = {
            "name": "news",
            "baseSelector": "tr.athing",
            "fields": [
                {
                    "name": "title",
                    "selector": "span.titleline",
                    "type": "text"
                }
            ]
        }

        results: List[CrawlResult] = await crawler.arun(
            url="https://news.ycombinator.com",
            config=CrawlerRunConfig(
                session_id="hn_session",  # Keep session
                extraction_strategy=JsonCssExtractionStrategy(schema=news_schema),
            )
        )

        news = []
        for result in results:
            if result.success:
                data = json.loads(result.extracted_content)
                news.extend(data)
                print(json.dumps(data, indent=2))
            else:
                print("Failed to extract structured data")

        print(f"Initial items: {len(news)}")

        # Click "More" link
        more_config = CrawlerRunConfig(
            js_code="document.querySelector(a.morelink).click();",
            js_only=True,  # Continue in same page
            session_id="hn_session",  # Keep session
            extraction_strategy=JsonCssExtractionStrategy(schema=news_schema),
        )

        result: List[CrawlResult] = await crawler.arun(
            url="https://news.ycombinator.com", config=more_config
        )

        # Extract new items
        for result in results:
            if result.success:
                data = json.loads(result.extracted_content)
                news.extend(data)
                print(json.dumps(data, indent=2))
            else:
                print("Failed to extract structured data")

        print(f"Total items: {len(news)}")

if __name__ == "__main__":
    asyncio.run(demo_js_interaction())
