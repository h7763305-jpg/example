from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from memo_parser import build_tabelog_keyword_text
from selenium_browser import SeleniumBrowser
from tabelog_selectors import TABELOG_SELECTORS


TABELOG_HOME_URL = "https://tabelog.com/"
TABELOG_SEARCH_URL = "https://tabelog.com/rstLst/"
WAIT_SECONDS = 8
JAPANESE_WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]
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


def input_area(driver: WebDriver, area: str | None) -> str | None:
    """エリア欄に入力し、食べログの第一候補名を返す。"""
    if not area:
        print("[tabelog] エリアは未指定です")
        return None

    area_input = wait_for_any_selector(driver, TABELOG_SELECTORS["area_inputs"])
    area_input.clear()
    area_input.send_keys(area)
    print(f"[tabelog] エリアを入力: {area}")
    selected_area = select_area_suggestion(driver, area)
    if selected_area:
        area_input = wait_for_any_selector(driver, TABELOG_SELECTORS["area_inputs"])
        set_input_value(driver, area_input, selected_area)
        print(f"[tabelog] エリア欄を第一候補名に更新: {selected_area}")
    return selected_area


def get_visible_area_suggestions(driver: WebDriver):
    """食べログのエリア候補リストから、表示中の候補を返す。"""
    suggestions = []
    for selector in TABELOG_SELECTORS["area_suggestion_items"]:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            if element.is_displayed() and element.text.strip():
                suggestions.append(element)
    return suggestions


def normalize_area_name(value: str) -> str:
    """候補名を比較しやすいように空白を取り除く。"""
    return "".join(value.split())


def get_primary_suggestion_text(suggestion_text: str) -> str:
    """候補要素の複数行テキストから、先頭の候補名だけを返す。"""
    lines = [line.strip() for line in suggestion_text.splitlines() if line.strip()]
    if not lines:
        return ""
    return lines[0]


def get_area_match_names(area: str) -> list[str]:
    """入力エリアから、食べログ候補と照合する名前を作る。"""
    normalized_area = normalize_area_name(area)
    base_area = normalized_area
    for suffix in ("駅周辺", "駅近", "周辺", "エリア"):
        if base_area.endswith(suffix):
            base_area = base_area.removesuffix(suffix)

    if base_area.endswith(("駅", "区", "市", "町")):
        names = [base_area]
    else:
        names = [f"{base_area}駅", base_area]

    unique_names: list[str] = []
    for name in names:
        if name and name not in unique_names:
            unique_names.append(name)
    return unique_names


def area_suggestion_matches(area: str, suggestion_text: str) -> bool:
    """候補の先頭名が、入力エリアと同じ系統か判定する。"""
    primary_text = normalize_area_name(get_primary_suggestion_text(suggestion_text))
    if not primary_text:
        return False

    for name in get_area_match_names(area):
        if primary_text == name or primary_text.startswith(name):
            return True
    return False


def select_area_suggestion(driver: WebDriver, area: str) -> str | None:
    """食べログが出した一番上のエリア候補を優先して選択する。"""
    suggestions = WebDriverWait(driver, WAIT_SECONDS).until(
        lambda active_driver: get_visible_area_suggestions(active_driver)
    )

    selected = suggestions[0]
    selected_text = selected.text.strip()
    selected_area = get_primary_suggestion_text(selected_text)
    if area_suggestion_matches(area, selected_text):
        print(f"[tabelog] 一番上のエリア候補が入力と一致: {selected_area}")
    else:
        print(f"[tabelog] 一番上のエリア候補をそのまま選択: {selected_area}")

    driver.execute_script("arguments[0].click()", selected)
    print(f"[tabelog] エリア候補を選択: {selected_text}")
    return selected_area or None


def set_input_value(driver: WebDriver, element, value: str) -> None:
    """JS側の検索処理にも伝わるように、input値を入れてchangeイベントを出す。"""
    driver.execute_script(
        """
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """,
        element,
        value,
    )


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
    try:
        button.click()
    except WebDriverException:
        driver.execute_script("arguments[0].click()", button)
    print("[tabelog] 検索ボタンをクリック")
    return True


def submit_search_form(driver: WebDriver) -> bool:
    """トップページの検索フォームを送信する。"""
    search_input = find_first_visible(driver, TABELOG_SELECTORS["area_inputs"] + TABELOG_SELECTORS["keyword_inputs"])
    if search_input is None:
        click_search(driver)
        return True

    form_exists = driver.execute_script("return Boolean(arguments[0].form)", search_input)
    if form_exists:
        driver.execute_script("arguments[0].form.submit()", search_input)
        print("[tabelog] 検索フォームを送信")
        return True

    search_input.send_keys(Keys.ENTER)
    print("[tabelog] Enterで検索")
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


def replace_query_param(url: str, key: str, value: str) -> str:
    """既存URLのquery parameterを1つ差し替える。"""
    parsed = urlparse(url)
    query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query_params[key] = value
    return urlunparse(parsed._replace(query=urlencode(query_params)))


def normalize_search_date(value: Any) -> date | None:
    """UIで選ばれた日付文字列を、食べログURLに渡せる日付へ変換する。"""
    if not isinstance(value, str) or not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def format_tabelog_display_date(selected_date: date) -> str:
    """食べログの日付入力欄に表示する文字列へ変換する。"""
    weekday = JAPANESE_WEEKDAYS[selected_date.weekday()]
    return f"{selected_date.year}/{selected_date.month}/{selected_date.day}({weekday})"


def set_date_input_values(driver: WebDriver, selectors: list[str], value: str) -> int:
    """指定selectorに一致する日付入力欄へ値を入れる。"""
    updated_count = 0
    for selector in selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for element in elements:
            driver.execute_script(
                """
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """,
                element,
                value,
            )
            updated_count += 1
    return updated_count


def select_visit_date(driver: WebDriver, selected_date: date | None) -> bool:
    """検索結果ページの来店日入力欄へ、メモから抽出した日付を反映する。"""
    if selected_date is None:
        return False

    compact_date = selected_date.strftime("%Y%m%d")
    display_date = format_tabelog_display_date(selected_date)

    WebDriverWait(driver, WAIT_SECONDS).until(
        lambda active_driver: active_driver.find_elements(By.CSS_SELECTOR, "input[name='svd'], input[name='search_date']")
    )
    hidden_count = set_date_input_values(driver, TABELOG_SELECTORS["visit_date_hidden_inputs"], compact_date)
    visible_count = set_date_input_values(driver, TABELOG_SELECTORS["visit_date_inputs"], display_date)
    print(f"[tabelog] 来店日を選択: {display_date} ({compact_date}) hidden={hidden_count} visible={visible_count}")
    return hidden_count + visible_count > 0


def search_tabelog(browser: SeleniumBrowser, conditions: dict[str, Any]) -> bool:
    """食べログの画面を操作して検索する。"""
    print(f"[tabelog] 検索条件: {conditions}")
    selected_date = normalize_search_date(conditions.get("date"))

    open_tabelog_home(browser)

    if browser.driver is None:
        raise WebDriverException("Chrome driver is not ready.")

    driver = browser.driver
    keyword_text = build_tabelog_keyword_text(conditions)
    budget = conditions.get("budget")

    try:
        selected_area = input_area(driver, conditions.get("area"))
        if selected_area:
            conditions["area"] = selected_area
        input_keyword(driver, keyword_text)
        submit_search_form(driver)
        WebDriverWait(driver, WAIT_SECONDS).until(lambda active_driver: "rstLst" in active_driver.current_url)

        if selected_date is not None:
            dated_url = replace_query_param(driver.current_url, "svd", selected_date.strftime("%Y%m%d"))
            browser.navigate(dated_url)
            select_visit_date(driver, selected_date)

        if isinstance(budget, int):
            select_budget(driver, budget)
            submit_budget_form(driver)
    except (TimeoutException, WebDriverException) as exc:
        fallback_url = build_fallback_search_url(conditions)
        print(f"[tabelog] 入力欄操作に失敗したためURLで検索します: {exc}")
        print(f"[tabelog] fallback URL: {fallback_url}")
        browser.navigate(fallback_url)

    return True
