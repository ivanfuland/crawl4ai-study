import asyncio
from crawl4ai import *
import pprint


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
        
        # 打印整个 result 对象的详细内容
        print("\n===== result 对象详细信息 =====")
        print(f"类型: {type(result)}")
        
        if isinstance(result, list):
            # 如果结果是列表，遍历每个结果对象
            for i, res in enumerate(result):
                print(f"\n----- 结果 {i+1} -----")
                print_result_details(res)
        else:
            # 如果是单个结果对象
            print_result_details(result)
        
        # 最后打印 Markdown 内容
        print("\n===== Markdown 内容 =====")
        if isinstance(result, list) and result:
            print(result[0].markdown)
        else:
            print(result.markdown)

def print_result_details(result):
    """打印结果对象的详细属性"""
    print(f"成功状态: {result.success}")
    
    # 获取对象的所有非私有属性
    attrs = [attr for attr in dir(result) if not attr.startswith('_')]
    for attr in attrs:
        try:
            value = getattr(result, attr)
            # 对于方法，只打印名称而不执行
            if callable(value):
                print(f"{attr}: <方法>")
            else:
                # 对于大型内容，只打印类型和摘要
                if attr == 'markdown' and value:
                    if hasattr(value, 'raw_markdown'):
                        md_preview = value.raw_markdown[:100]
                        print(f"{attr}: <Markdown 对象>, 预览: {md_preview}...")
                    else:
                        print(f"{attr}: {type(value)}")
                elif attr == 'html' and value:
                    html_preview = value[:100] if isinstance(value, str) else str(value)[:100]
                    print(f"{attr}: <HTML>, 预览: {html_preview}...")
                elif attr == 'url':
                    print(f"{attr}: {value}")
                elif attr == 'success':
                    print(f"{attr}: {value}")
                elif attr == 'status_code':
                    print(f"{attr}: {value}")
                elif attr == 'error':
                    print(f"{attr}: {value}")
                else:
                    # 对于其他属性，简单显示其类型
                    print(f"{attr}: {type(value)}")
        except Exception as e:
            print(f"{attr}: <无法访问: {e}>")

if __name__ == "__main__":
    asyncio.run(main())