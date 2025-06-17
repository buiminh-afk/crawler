import asyncio
import json

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

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
            "name": "comment",
            "selector": "div.item-body.readmore-content p",
            "type": "text"
        }
    ]
}

extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)


async def main():
    browser_cfg = BrowserConfig(headless=True, verbose=True)
    crawl_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_for="css:li.page-item",
        exclude_external_links=True,
        extraction_strategy=extraction_strategy,
    )

    data = []

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for page in range(1, 4):  # crawl từ page 1 đến 3 chẳng hạn
            url = f"https://congtytui1.com/companies/tma-solutions?sort_by=latest&page={page}"
            result = await crawler.arun(url=url, config=crawl_cfg)

            if not result.success:
                print(f"Lỗi khi crawl page {page}: {result.error_message}")
                continue

            extracted = json.loads(result.extracted_content)
            data.extend(extracted)

    # Ghi dữ liệu hợp lệ vào JSON file
    with open("comments_all_pages.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ Crawl xong, đã ghi dữ liệu vào comments_all_pages.json")

if __name__ == "__main__":
    asyncio.run(main())
