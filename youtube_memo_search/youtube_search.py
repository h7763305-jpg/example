from __future__ import annotations

from urllib.parse import quote_plus

from selenium_browser import SeleniumBrowser


YOUTUBE_HOME_URL = "https://www.youtube.com/"
YOUTUBE_SEARCH_URL = "https://www.youtube.com/results?search_query={query}"


def search_youtube(browser: SeleniumBrowser, search_text: str) -> bool:
    """YouTube の検索結果ページを開く。"""
    if not search_text:
        return False

    encoded_query = quote_plus(search_text)
    search_url = YOUTUBE_SEARCH_URL.format(query=encoded_query)
    print(f"[youtube] 検索します: {search_text}")
    browser.navigate(search_url)
    return True
