import asyncio
from crawl4ai import *
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import pprint

async def demo_fit_markdown():
    """Generate focused markdown with LLM content filter"""
    print("\n=== 3. Fit Markdown with LLM Content Filter ===")

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            # "https://en.wikipedia.org/wiki/Python_(programming_language)",
            "https://www.36kr.com/p/3263874023259905",
            config=CrawlerRunConfig(
                markdown_generator=DefaultMarkdownGenerator(
                    content_filter=PruningContentFilter()
                )
            ),
        )

    # Print stats and save the fit markdown
    print(f"Raw: {len(result.markdown.raw_markdown)} chars")
    print(f"Fit: {len(result.markdown.fit_markdown)} chars")

if __name__ == "__main__":
    asyncio.run(demo_fit_markdown())