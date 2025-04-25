import asyncio
import json
from crawl4ai import *
import pprint

async def demo_media_and_links():
    """Extract media and links from a page"""
    print("\n=== 8. Media and Links Extraction ===")

    async with AsyncWebCrawler() as crawler:
        result: List[CrawlResult] = await crawler.arun("https://www.youtube.com/watch?v=Sftq4QFh0s0")

        for i, result in enumerate(result):
            # Extract and save all images
            images = result.media.get("images", [])
            print(f"Found {len(images)} images")            

            # Extract and save all videos
            videos = result.media.get("videos", [])
            print(f"Found {len(videos)} videos")

            # Extract and save all links (internal and external)
            internal_links = result.links.get("internal", [])
            external_links = result.links.get("external", [])
            print(f"Found {len(internal_links)} internal links")
            print(f"Found {len(external_links)} external links")

            # Save everything to files
            with open("images.json", "w") as f:
                json.dump(images, f, indent=2)

            with open("videos.json", "w") as f:
                json.dump(videos, f, indent=2)

            with open("links.json", "w") as f:
                json.dump(
                    {"internal": internal_links, "external": external_links},
                    f,
                    indent=2,
                )

if __name__ == "__main__":
    asyncio.run(demo_media_and_links())
