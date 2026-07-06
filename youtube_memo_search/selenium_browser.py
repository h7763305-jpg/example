from __future__ import annotations

import threading
from dataclasses import dataclass

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions


@dataclass(frozen=True)
class WindowLayout:
    screen_width: int
    screen_height: int
    left_width: int
    right_width: int
    usable_height: int


class SeleniumBrowser:
    """Selenium が操作する Chrome を共通管理する。"""

    def __init__(self, layout: WindowLayout, start_url: str) -> None:
        self.layout = layout
        self.start_url = start_url
        self.driver: webdriver.Chrome | None = None
        self.lock = threading.Lock()

    def start(self) -> None:
        with self.lock:
            if self._driver_is_ready():
                return

            self._discard_driver()
            self.driver = self._create_driver(self.start_url)

    def navigate(self, url: str) -> None:
        with self.lock:
            self._navigate(url)

    def is_open(self) -> bool:
        with self.lock:
            return self._driver_is_ready()

    def close(self) -> None:
        with self.lock:
            self._discard_driver()

    def _create_driver(self, start_url: str) -> webdriver.Chrome:
        print(f"[browser] Chromeを起動します: {start_url}")
        options = ChromeOptions()
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        driver = webdriver.Chrome(options=options)
        driver.set_window_rect(
            x=self.layout.left_width,
            y=0,
            width=self.layout.right_width,
            height=self.layout.usable_height,
        )
        driver.get(start_url)
        return driver

    def _navigate_without_stealing_focus(self, url: str) -> None:
        if self.driver is None:
            return

        try:
            self.driver.execute_cdp_cmd("Page.navigate", {"url": url})
        except WebDriverException:
            self.driver.get(url)

    def _navigate(self, url: str) -> None:
        print(f"[browser] ページを開きます: {url}")
        if not self._driver_is_ready():
            self._discard_driver()
            self.driver = self._create_driver(url)
            return

        self._navigate_without_stealing_focus(url)

    def _driver_is_ready(self) -> bool:
        if self.driver is None:
            return False

        try:
            window_handles = self.driver.window_handles
            if not window_handles:
                return False
            self.driver.switch_to.window(window_handles[0])
        except WebDriverException:
            return False

        return True

    def _discard_driver(self) -> None:
        if self.driver is None:
            return

        try:
            print("[browser] Chromeを終了します")
            self.driver.quit()
        except WebDriverException:
            pass
        finally:
            self.driver = None
