
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


async def demo_css_structured_extraction_no_schema():
    """Extract structured data using CSS selectors"""
    print("=== 5. CSS-Based Structured Extraction ===")

    # Sample HTML for schema generation (one-time cost)
    sample_html = """
    <div class="body-post clear">
    <a class="story-link" href="https://thehackernews.com/2025/04/lazarus-hits-6-south-korean-firms-via.html">
    <div class="clear home-post-box cf">
    <div class="home-img clear">
    <div class="img-ratio"><img alt="Lazarus Hits 6 South Korean Firms via Cross EX, Innorix Flaws and ThreatNeedle Malware" class="home-img-src lazyload loaded" decoding="async" height="380" src="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEj2IHqbULQvcT8ebOyeu-ghYK-6qErvwQC9mi_SvhfW4F2py2_wJxVHFc890SDOb3a3ojsCctD6Peqw4JsEm_UOXNsnwY2acr9c75ulzoH7WaITsjyjTtT7QVMxJddd74p5HQnHJcVY2MT9evn9cB8v24imoCRisAULwEIBzDzCEuYkkxTq-WfgDRwiOHKD/w500/water.jpg" width="728"></div>
    <noscript><img alt='Lazarus Hits 6 South Korean Firms via Cross EX, Innorix Flaws and ThreatNeedle Malware' decoding='async' loading='lazy' src='https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEj2IHqbULQvcT8ebOyeu-ghYK-6qErvwQC9mi_SvhfW4F2py2_wJxVHFc890SDOb3a3ojsCctD6Peqw4JsEm_UOXNsnwY2acr9c75ulzoH7WaITsjyjTtT7QVMxJddd74p5HQnHJcVY2MT9evn9cB8v24imoCRisAULwEIBzDzCEuYkkxTq-WfgDRwiOHKD/s728-rw-e365/water.jpg'/></noscript>
    </div>
    <div class="clear home-right">
    <h2 class="home-title">Lazarus Hits 6 South Korean Firms via Cross EX, Innorix Flaws and ThreatNeedle Malware</h2>
    <div class="item-label">
    <span class="h-datetime"><i class="icon-font icon-calendar"></i>Apr 24, 2025</span>
    <span class="h-tags">Malware / Threat Intelligence</span>
    </div>
    <div class="home-desc"> At least six organizations in South Korea have been targeted by the prolific North Korea-linked Lazarus Group  as part of a campaign dubbed Operation SyncHole .  The activity targeted South Korea's software, IT, financial, semiconductor manufacturing, and telecommunications industries, according to a report from Kaspersky published today. The earliest evidence of compromise was first detected in November 2024.  The campaign involved a "sophisticated combination of a watering hole strategy and vulnerability exploitation within South Korean software," security researchers Sojun Ryu and Vasily Berdnikov said . "A one-day vulnerability in Innorix Agent was also used for lateral movement."  The attacks have been observed paving the way for variants of known Lazarus tools such as ThreatNeedle , AGAMEMNON , wAgent , SIGNBT , and COPPERHEDGE .   What makes these intrusions particularly effective is the likely exploitation of a security vulnerability in Cross EX, a legi...</div>
    </div>
    </div>
    </a>
    </div>
    """


    schema_file_path = f"schema.json"
    if os.path.exists(schema_file_path):
        with open(schema_file_path, "r") as f:
            schema = json.load(f)
    else:
        # Generate schema using LLM (one-time setup)
        schema = JsonCssExtractionStrategy.generate_schema(
            html=sample_html,
                llm_config=LLMConfig(
                    provider="openai/gpt-4o-mini",
                    api_token=openai_api_key,
                ),
            query="From https://thehackernews.com/, I have shared a sample of one news div with a title, date, and description. Please generate a schema for this news div.",
        )

        # Save the schema to a file and use it for future extractions, in result for such
        # extraction you will call LLM once
        with open("schema.json", "w") as f:
            json.dump(schema, f, indent=2)
        
        print(f"Generated schema: {json.dumps(schema, indent=2)}")
  
    # Create no-LLM extraction strategy with the generated schema
    extraction_strategy = JsonCssExtractionStrategy(schema)
    config = CrawlerRunConfig(extraction_strategy=extraction_strategy)

    # Use the fast CSS extraction (no LLM calls during extraction)
    async with AsyncWebCrawler() as crawler:
        results: List[CrawlResult] = await crawler.arun(
            "https://thehackernews.com", config=config
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
    asyncio.run(demo_css_structured_extraction_no_schema())

