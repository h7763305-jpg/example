from __future__ import annotations

import sys
import time

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By

from tabelog_search import normalize_search_date, select_area_suggestion, select_visit_date
from tabelog_selectors import TABELOG_SELECTORS


def main() -> int:
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://tabelog.com/"
    selected_date = normalize_search_date(sys.argv[2]) if len(sys.argv) > 2 else None
    area_text = sys.argv[3] if len(sys.argv) > 3 else None
    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(target_url)
        if selected_date is not None:
            select_visit_date(driver, selected_date)
        if area_text:
            area_input = next(
                element
                for element in driver.find_elements(By.CSS_SELECTOR, "input[name='sa'], input[placeholder*='エリア']")
                if element.is_displayed()
            )
            area_input.clear()
            area_input.send_keys(area_text)
            time.sleep(2)
            select_area_suggestion(driver, area_text)
            time.sleep(1)

        print(f"title={driver.title}")
        print(f"url={driver.current_url}")

        if area_text:
            print("\n[area_candidate_elements]")
            printed_count = 0
            for element in driver.find_elements(By.CSS_SELECTOR, "a, li, div, button"):
                try:
                    text = " ".join(
                        [
                            element.text or "",
                            element.get_attribute("class") or "",
                            element.get_attribute("href") or "",
                            element.get_attribute("role") or "",
                        ]
                    ).strip()
                except StaleElementReferenceException:
                    continue
                if area_text in text and printed_count < 80:
                    print(f"{element.tag_name}: {text[:260]}")
                    printed_count += 1

        for group_name, selectors in TABELOG_SELECTORS.items():
            print(f"\n[{group_name}]")
            for selector in selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                visible_count = sum(1 for element in elements if element.is_displayed())
                print(f"{selector}: total={len(elements)} visible={visible_count}")

        print("\n[budget_related_elements]")
        words = ["予算", "価格", "金額", "price", "budget", "yen"]
        for element in driver.find_elements(By.CSS_SELECTOR, "input, select, button, a, label"):
            text = " ".join(
                [
                    element.text or "",
                    element.get_attribute("name") or "",
                    element.get_attribute("id") or "",
                    element.get_attribute("class") or "",
                    element.get_attribute("href") or "",
                ]
            ).strip()
            if any(word.lower() in text.lower() for word in words):
                print(f"{element.tag_name}: {text[:220]}")

        print("\n[date_related_elements]")
        date_words = ["日付", "日時", "予約", "空席", "人数", "date", "svd", "svt", "svps", "visit"]
        for element in driver.find_elements(By.CSS_SELECTOR, "input, select, button, a, label"):
            text = " ".join(
                [
                    element.text or "",
                    element.get_attribute("name") or "",
                    element.get_attribute("id") or "",
                    element.get_attribute("class") or "",
                    element.get_attribute("value") or "",
                    element.get_attribute("placeholder") or "",
                    element.get_attribute("aria-label") or "",
                    element.get_attribute("href") or "",
                ]
            ).strip()
            if any(word.lower() in text.lower() for word in date_words):
                print(f"{element.tag_name}: {text[:260]}")
    finally:
        driver.quit()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
