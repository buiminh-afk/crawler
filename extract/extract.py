import re
import time

from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.by import By


def get_precise_comment_buttons(browser):
    all_buttons = browser.find_elements(
        By.CSS_SELECTOR, 'button[aria-label*="comment"]')
    comment_buttons = []

    pattern = re.compile(r"^\d+\s+comment[s]?\s+on\s+.+?(?:’s)?\s+post$")

    for btn in all_buttons:
        aria_label = btn.get_attribute("aria-label")
        if aria_label and pattern.match(aria_label):
            comment_buttons.append(btn)

    return comment_buttons


def extract_comments_from_post(post_soup):
    comment_spans = post_soup.find_all(
        "span", class_="comments-comment-item__main-content")

    comments = []
    for span in comment_spans:
        content_div = span.find("div", class_="update-components-text")
        if content_div:
            comment_text = content_div.get_text(strip=True)
            if comment_text:
                comments.append(comment_text)
    return comments


def click_all_comment_buttons(browser):
    buttons = get_precise_comment_buttons(browser)

    for btn in buttons:
        try:
            browser.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(0.5)
            btn.click()
            time.sleep(1.5)
        except Exception as e:
            print(f"[WARN] Failed to click comment button: {e}")


def extract_comment_count(post_soup):
    comment_section = post_soup.find(
        "li", class_="social-details-social-counts__comments")
    if not comment_section:
        return 0  # không có comment

    span = comment_section.find("span", attrs={"aria-hidden": "true"})
    if span:
        text = span.get_text(strip=True)
        # Lấy số từ "2 comments" -> 2
        parts = text.split()
        if parts and parts[0].isdigit():
            return int(parts[0])
    return 0


def extract_posted_time(post_soup):
    time_container = post_soup.find(
        "span", class_="update-components-actor__sub-description")
    if not time_container:
        return ""

    time_text = time_container.get_text(strip=True)

    # Chỉ lấy phần trước dấu "•"
    if "•" in time_text:
        return time_text.split("•")[0].strip()

    return time_text


def extract_posted_by(post_soup):
    title_container = post_soup.find(
        "span", class_="update-components-actor__title")
    if not title_container:
        return ""

    # Lấy ra phần chỉ visible (bỏ phần visually-hidden)
    visible_text = title_container.find("span", attrs={"aria-hidden": "true"})
    return visible_text.get_text(strip=True) if visible_text else ""


def extract_reaction_count(post_soup):
    count_span = post_soup.find(
        "span", class_="social-details-social-counts__reactions-count")
    if not count_span:
        return 0
    try:
        count = int(count_span.get_text(strip=True).replace(',', ''))
        return count
    except ValueError:
        return 0


def extract_hashtags(container):
    if not container:
        return []

    hashtags = []
    for a in container.find_all("a", href=True):
        if "/search/results/all/?keywords=%23" in a["href"]:
            tag_text = a.get_text(strip=True)
            match = re.search(r"#\w+", tag_text)
            if match:
                hashtags.append(match.group(0))
    return hashtags


def extract_caption(container):
    if not container:
        return ""

    # Copy container để không ảnh hưởng hashtag parsing
    container_copy = bs(str(container), "html.parser")

    for a in container_copy.find_all("a"):
        a.decompose()  # Xóa thẻ <a> (hashtag/link)

    return container_copy.get_text(separator=" ", strip=True)


def get_caption_container(post_soup):
    return post_soup.find("span", class_="break-words tvm-parent-container")


def extract_reposts_count(soup):
    repost_buttons = soup.find_all(
        "button", attrs={"aria-label": re.compile(r"\d+ repost")})

    for btn in repost_buttons:
        label = btn.get("aria-label", "")
        match = re.search(r"(\d+)\s+repost", label)
        if match:
            return int(match.group(1))

    return 0


def click_all_load_more_comments(browser):
    while True:
        try:
            # Tìm nút hiện tại
            load_more_buttons = browser.find_elements(
                By.CSS_SELECTOR,
                'button[aria-label="Load more comments"]'
            )

            if not load_more_buttons:
                break  # Không còn nút nào => dừng

            clicked_any = False

            for btn in load_more_buttons:
                try:
                    browser.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(0.5)
                    btn.click()
                    time.sleep(1.5)  # chờ load comments
                    clicked_any = True
                except Exception as e:
                    print(f"[WARN] Failed to click: {e}")
                    continue

            # Nếu không click được cái nào => dừng để tránh loop vô hạn
            if not clicked_any:
                break

        except Exception as e:
            print(f"[ERROR] Load more loop failed: {e}")
            break


def click_all_see_more_buttons(browser):
    try:
        # Dùng CSS Selector cụ thể, chính xác hơn
        see_more_buttons = browser.find_elements(By.CSS_SELECTOR,
                                                 ".feed-shared-inline-show-more-text__see-more-less-toggle")

        print(f"[INFO] Found {len(see_more_buttons)} 'See more' buttons.")

        for btn in see_more_buttons:
            try:
                browser.execute_script("arguments[0].click();", btn)
                time.sleep(1)  # delay nhẹ để tránh bị drop
            except Exception as e:
                print(f"[WARN] Can't click see more: {e}")

    except Exception as e:
        print(f"[ERROR] Failed to locate see more buttons: {e}")
