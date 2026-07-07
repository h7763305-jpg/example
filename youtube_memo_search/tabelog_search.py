from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import urlencode

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from memo_parser import build_tabelog_keyword_text
from selenium_browser import SeleniumBrowser
from tabelog_selectors import TABELOG_SELECTORS


TABELOG_HOME_URL = "https://tabelog.com/"
TABELOG_SEARCH_URL = "https://tabelog.com/rstLst/"
WAIT_SECONDS = 8
BUDGET_SELECT_VALUES = {
    1000: "1",
    2000: "2",
    3000: "3",
    4000: "4",
    5000: "5",
    6000: "6",
    8000: "7",
    10000: "8",
    15000: "9",
    20000: "10",
    30000: "11",
    40000: "12",
    50000: "13",
    60000: "14",
    80000: "15",
    100000: "16",
}


def find_first_visible(driver: WebDriver, selectors: list[str]):
    """候補selectorの中から、最初に見つかった表示中の要素を返す。"""
    for selector in selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for element in elements:
            if element.is_displayed():
                print(f"[tabelog] selector found: {selector}")
                return element
    return None


def wait_for_any_selector(driver: WebDriver, selectors: list[str]):
    """候補selectorのどれかが表示されるまで待つ。"""
    def locate_visible_element(active_driver: WebDriver):
        return find_first_visible(active_driver, selectors)

    return WebDriverWait(driver, WAIT_SECONDS).until(locate_visible_element)


def open_tabelog_home(browser: SeleniumBrowser) -> None:
    """食べログトップページを開く。"""
    print("[tabelog] 食べログを開きます")
    browser.navigate(TABELOG_HOME_URL)


def input_area(driver: WebDriver, area: str | None) -> bool:
    """エリア欄に入力する。"""
    if not area:
        print("[tabelog] エリアは未指定です")
        return False

    area_input = wait_for_any_selector(driver, TABELOG_SELECTORS["area_inputs"])
    area_input.clear()
    area_input.send_keys(area)
    print(f"[tabelog] エリアを入力: {area}")
    return True


def input_keyword(driver: WebDriver, keyword_text: str) -> bool:
    """ジャンルとキーワードを検索欄に入力する。"""
    if not keyword_text:
        print("[tabelog] ジャンル/キーワードは未指定です")
        return False

    keyword_input = wait_for_any_selector(driver, TABELOG_SELECTORS["keyword_inputs"])
    keyword_input.clear()
    keyword_input.send_keys(keyword_text)
    print(f"[tabelog] ジャンル/キーワードを入力: {keyword_text}")
    return True


def get_budget_select_value(budget: int) -> str:
    """食べログの予算selectに入れる値を返す。指定金額以上の一番近い上限を選ぶ。"""
    for candidate_budget, select_value in BUDGET_SELECT_VALUES.items():
        if budget <= candidate_budget:
            return select_value
    return BUDGET_SELECT_VALUES[100000]


def select_budget(driver: WebDriver, budget: int | None) -> bool:
    """結果ページの予算上限selectが見つかれば、指定予算に近い上限を選ぶ。"""
    if budget is None:
        print("[tabelog] 予算は未指定です")
        return False

    budget_select = find_first_visible(driver, TABELOG_SELECTORS["max_budget_selects"])
    if budget_select is None:
        print("[tabelog] 予算上限selectが見つかりません")
        return False

    select = Select(budget_select)
    select_value = get_budget_select_value(budget)
    select.select_by_value(select_value)
    selected_text = select.first_selected_option.text
    print(f"[tabelog] 予算上限を選択: {selected_text}")
    return True


def submit_budget_form(driver: WebDriver) -> bool:
    """予算selectを含むフォームを送信して、予算条件を反映する。"""
    budget_select = find_first_visible(driver, TABELOG_SELECTORS["max_budget_selects"])
    if budget_select is None:
        return False

    driver.execute_script("arguments[0].form.submit()", budget_select)
    print("[tabelog] 予算フォームを送信")
    return True


def click_search(driver: WebDriver) -> bool:
    """検索ボタンをクリックする。"""
    button = wait_for_any_selector(driver, TABELOG_SELECTORS["search_buttons"])
    button.click()
    print("[tabelog] 検索ボタンをクリック")
    return True


def build_fallback_search_url(conditions: dict[str, Any]) -> str:
    """入力欄操作に失敗したとき用に、検索URLを組み立てる。"""
    keyword_text = build_tabelog_keyword_text(conditions)
    budget = conditions.get("budget")
    selected_date = normalize_search_date(conditions.get("date"))

    params: dict[str, str] = {}
    area = conditions.get("area")
    if isinstance(area, str) and area:
        params["sa"] = area
    if keyword_text:
        params["sw"] = keyword_text
        params["sk"] = keyword_text
    if isinstance(budget, int):
        params["LstCosT"] = get_budget_select_value(budget)
        params["RdoCosTp"] = "2"
    if selected_date is not None:
        params["svd"] = selected_date.strftime("%Y%m%d")

    query = urlencode(params)
    if not query:
        return TABELOG_HOME_URL
    return f"{TABELOG_SEARCH_URL}?{query}"


def normalize_search_date(value: Any) -> date | None:
    """UIで選ばれた日付文字列を、食べログURLに渡せる日付へ変換する。"""
    if not isinstance(value, str) or not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def search_tabelog(browser: SeleniumBrowser, conditions: dict[str, Any]) -> bool:
    """食べログの画面を操作して検索する。"""
    print(f"[tabelog] 検索条件: {conditions}")

    if normalize_search_date(conditions.get("date")) is not None:
        search_url = build_fallback_search_url(conditions)
        print(f"[tabelog] 日付指定ありのためURLで検索します: {search_url}")
        browser.navigate(search_url)
        return True

    open_tabelog_home(browser)

    if browser.driver is None:
        raise WebDriverException("Chrome driver is not ready.")

    driver = browser.driver
    keyword_text = build_tabelog_keyword_text(conditions)
    budget = conditions.get("budget")

    try:
        input_area(driver, conditions.get("area"))
        input_keyword(driver, keyword_text)
        click_search(driver)

        if isinstance(budget, int):
            WebDriverWait(driver, WAIT_SECONDS).until(lambda active_driver: "rstLst" in active_driver.current_url)
            select_budget(driver, budget)
            submit_budget_form(driver)
    except (TimeoutException, WebDriverException) as exc:
        fallback_url = build_fallback_search_url(conditions)
        print(f"[tabelog] 入力欄操作に失敗したためURLで検索します: {exc}")
        print(f"[tabelog] fallback URL: {fallback_url}")
        browser.navigate(fallback_url)

    return True
