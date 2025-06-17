import argparse
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

import extract  # ensure this module has all required extraction helpers

# === Constants ===
SCROLL_PAUSE_TIME = 1.5
MAX_SCROLLS = 2
COOKIE_PATH = "linkedin_cookies.json"
SEARCH_URL = "https://www.linkedin.com/search/results/content/?keywords=%23{}&origin=SWITCH_SEARCH_VERTICAL"


# === Login LinkedIn ===
def parse_args() -> tuple[str, str]:
    parser = argparse.ArgumentParser(description="LinkedIn hashtag scraper")

    parser.add_argument(
        "--hashtag",
        required=True,
        help="Hashtag to search for (e.g., tmasolutions)"
    )
    parser.add_argument(
        "--output",
        default="./output",
        help="Output folder (default: ./output)"
    )

    args = parser.parse_args()

    # Normalize hashtag
    hashtag = args.hashtag.strip()
    if hashtag.startswith("#"):
        hashtag = hashtag.replace("#", "")

    # Ensure output folder exists
    os.makedirs(args.output, exist_ok=True)

    return hashtag, args.output

# === Init Selenium Browser ===


def init_browser() -> WebDriver:
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    })
    return webdriver.Chrome(options=options)


# === Login LinkedIn ===
def login_linkedin(browser: WebDriver, username: str, password: str) -> bool:
    browser.get("https://www.linkedin.com/login")
    time.sleep(2)

    browser.find_element(By.ID, "username").send_keys(username)
    browser.find_element(By.ID, "password").send_keys(password)
    browser.find_element(By.ID, "password").submit()

    input("Login and solve CAPTCHA if required, then press Enter to continue...")

    time.sleep(5)
    return "feed" in browser.current_url


# === Scroll Feed ===
def scroll_linkedin_feed(browser: WebDriver) -> None:
    last_height = browser.execute_script("return document.body.scrollHeight")
    scrolls = 0
    no_change_count = 0

    while True:
        browser.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = browser.execute_script(
            "return document.body.scrollHeight")

        if new_height == last_height:
            no_change_count += 1
        else:
            no_change_count = 0

        if no_change_count >= 3 or scrolls >= MAX_SCROLLS:
            break

        last_height = new_height
        scrolls += 1
        print(f"[Scroll] {scrolls}/{MAX_SCROLLS}")


# === Trigger all dynamic content buttons ===
def click_all_interactions(browser: WebDriver) -> None:
    print("Clicking all 'see more' buttons...")
    extract.click_all_see_more_buttons(browser)

    print("Clicking all comment buttons...")
    extract.click_all_comment_buttons(browser)

    print("Clicking all 'load more comments'...")
    extract.click_all_load_more_comments(browser)


# === Extract all posts ===
def extract_posts(browser: WebDriver) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(browser.page_source, "html.parser")
    posts = soup.find_all("li", class_="artdeco-card mb2")

    results = []

    for post in posts:
        container = extract.get_caption_container(post)

        result = {
            "posted_by": extract.extract_posted_by(post),
            "posted": extract.extract_posted_time(post),
            "caption": extract.extract_caption(container),
            "hashtags": extract.extract_hashtags(container),
            "reacts": extract.extract_reaction_count(post),
            "reposts": extract.extract_reposts_count(post),
            "comment_count": extract.extract_comment_count(post),
            "comments": extract.extract_comments_from_post(post)
        }

        results.append(result)

    return results


# === Save to JSON ===
def save_results_to_file(data: List[Dict[str, Any]], filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[Saved] {filename}")


# === MAIN ENTRY ===
def main() -> None:
    hashtag, output_folder = parse_args()
    load_dotenv()
    username = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")

    if not username or not password:
        print("[Error] Missing LinkedIn credentials in .env")
        return

    browser = init_browser()

    if not login_linkedin(browser, username, password):
        print("[Error] Login failed or captcha not passed")
        return

    print("[Info] Logged in successfully")

    browser.get(SEARCH_URL.format(hashtag))
    time.sleep(5)

    scroll_linkedin_feed(browser)
    click_all_interactions(browser)

    print("[Info] Extracting posts...")
    posts = extract_posts(browser)

    today = datetime.today().strftime('%Y-%m-%d')
    save_results_to_file(
        posts, f"{output_folder}/{hashtag}_{today}.json")

    browser.quit()


if __name__ == "__main__":
    main()
