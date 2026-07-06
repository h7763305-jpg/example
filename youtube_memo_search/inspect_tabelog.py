from __future__ import annotations

import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By

from tabelog_selectors import TABELOG_SELECTORS


def main() -> int:
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://tabelog.com/"
    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(target_url)
        print(f"title={driver.title}")
        print(f"url={driver.current_url}")

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
    finally:
        driver.quit()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
