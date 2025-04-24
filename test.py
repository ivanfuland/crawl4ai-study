import asyncio
from crawl4ai import *


# crun_cfg = CrawlerRunConfig(
#     url="https://browserleaks.com/geo",          # test page that shows your location
#     locale="en-US",                              # Accept-Language & UI locale
#     timezone_id="America/Los_Angeles",           # JS Date()/Intl timezone
#     geolocation=GeolocationConfig(                 # override GPS coords
#         latitude=34.0522,
#         longitude=-118.2437,
#         accuracy=10.0,
#     )
# )

async def main():
    async with AsyncWebCrawler(
        page_options={
            "page_timeout": 120000, # 增加超时时间到 120 秒
        }
    ) as crawler:
        result = await crawler.arun(
            url="https://www.36kr.com/p/3263507071788289",
        )
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())