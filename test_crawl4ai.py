import asyncio
import json

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    JsonCssExtractionStrategy,
)

data = []

# Khai báo schema CSS extraction
schema = {
    "name": "Comment",
    "baseSelector": "div.item.section-box.bg-white",
    "fields": [
        {
            "name": "name",
            "selector": "div.item-title.font-weight-semibold a",
            "type": "text"
        },
        {
            "name": "date",
            "selector": "div.item-date.text-grey a",
            "type": "text"},
        {
            "name": "comment",
            "selector": "div.item-body.readmore-content p",
            "type": "text"
        }
    ]
}
BASE_URL = "https://congtytui1.com/companies/tma-solutions?sort_by=latest&page="
extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)


async def multi_page_commits():
    browser_cfg = BrowserConfig(headless=True, verbose=True)

    crawl_config = CrawlerRunConfig(
        wait_until="networkidle",
        cache_mode=CacheMode.BYPASS,
        scan_full_page=True,
        extraction_strategy=extraction_strategy
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for page in range(1, 61):  # ví dụ crawl thêm 3 trang
            result = await crawler.arun(
                url=BASE_URL+str(page),
                config=crawl_config)
            data.extend(json.loads(result.extracted_content))  # type: ignore


async def main():
    await multi_page_commits()
    with open("comments.json", "a", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
