import asyncio

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig


async def multi_page_commits():
    browser_cfg = BrowserConfig(
        headless=False,  # Visible for demonstration
        verbose=True
    )
    session_id = "github_ts_commits"

    base_wait = """js:() => {
        const commits = document.querySelectorAll('li.Box-sc-g0xbh4-0 h4');
        return commits.length > 0;
    }"""

    # Step 1: Load initial commits
    config1 = CrawlerRunConfig(
        wait_for=base_wait,
        session_id=session_id,
        cache_mode=CacheMode.BYPASS,
        # Not using js_only yet since it's our first load
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url="https://github.com/microsoft/TypeScript/commits/main",
            config=config1
        )
        print("Initial commits loaded. Count:",
              result.cleaned_html.count("commit"))

        # Step 2: For subsequent pages, we run JS to click 'Next Page' if it exists
        js_next_page = """
        const selector = 'a[data-testid="pagination-next-button"]';
        const button = document.querySelector(selector);
        if (button) button.click();
        """

        # Wait until new commits appear
        wait_for_more = """js:() => {
            const commits = document.querySelectorAll('li.Box-sc-g0xbh4-0 h4');
            if (!window.firstCommit && commits.length>0) {
                window.firstCommit = commits[0].textContent;
                return false;
            }
            // If top commit changes, we have new commits
            const topNow = commits[0]?.textContent.trim();
            return topNow && topNow !== window.firstCommit;
        }"""

        for page in range(2):  # let's do 2 more "Next" pages
            config_next = CrawlerRunConfig(
                session_id=session_id,
                js_code=js_next_page,
                wait_for=wait_for_more,
                js_only=True,       # We're continuing from the open tab
                cache_mode=CacheMode.BYPASS
            )
            result2 = await crawler.arun(
                url="https://github.com/microsoft/TypeScript/commits/main",
                config=config_next
            )
            print(f"Page {page+2} commits count:",
                  result2.cleaned_html.count("commit"))

        # Optionally kill session
        await crawler.crawler_strategy.kill_session(session_id)


async def main():
    await multi_page_commits()

if __name__ == "__main__":
    asyncio.run(main())
