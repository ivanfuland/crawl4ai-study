import asyncio
import json
import os
from dotenv import load_dotenv
from crawl4ai import *
import pprint   
import sys

load_dotenv()

# 检查 OPENAI_API_KEY 环境变量是否存在
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("错误: 未找到 OPENAI_API_KEY 环境变量。请确保已设置该环境变量或在 .env 文件中添加它。")
    sys.exit(1)

async def demo_llm_structured_extraction_no_schema():
    """Create a simple LLM extraction strategy (no schema required)"""
    extraction_strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token=openai_api_key,
        ),
        instruction="This is news.ycombinator.com, extract all news, and for each, I want title, source url, number of comments.",
        extract_type="schema",
        schema={"title": "string", "url": "string", "comments": "int"},
        extra_args={
            "temperature": 0.0,
            "max_tokens": 4096,
        },
        verbose=True,
    )

    config = CrawlerRunConfig(extraction_strategy=extraction_strategy)

    async with AsyncWebCrawler() as crawler:
        results: List[CrawlResult] = await crawler.arun(
            "https://news.ycombinator.com/", config=config
        )

        for result in results:
            print(f"URL: {result.url}")
            print(f"Success: {result.success}")
            if result.success:
                data = json.loads(result.extracted_content)
                print(json.dumps(data, indent=2))
            else:
                print("Failed to extract structured data")

if __name__ == "__main__":
    asyncio.run(demo_llm_structured_extraction_no_schema())
