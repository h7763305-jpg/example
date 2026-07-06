from __future__ import annotations

import re
import sys
import threading
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk
from urllib.parse import quote_plus, urlparse

try:
    from selenium import webdriver
    from selenium.common.exceptions import WebDriverException
    from selenium.webdriver.chrome.options import Options as ChromeOptions
except ModuleNotFoundError as exc:
    print(
        "selenium がインストールされていません。\n"
        "次のコマンドでセットアップしてから起動してください。\n\n"
        "cd /Users/izumikahiroto/Desktop/dev/youtube_memo_search\n"
        "python3 -m venv .venv\n"
        "source .venv/bin/activate\n"
        "pip install -r requirements.txt\n"
        "python3 app.py",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc


YOUTUBE_HOME_URL = "https://www.youtube.com/"
YOUTUBE_SEARCH_URL = "https://www.youtube.com/results?search_query={query}"
MAX_SEARCH_TEXT_LENGTH = 80


@dataclass(frozen=True)
class WindowLayout:
    screen_width: int
    screen_height: int
    left_width: int
    right_width: int
    usable_height: int


def create_layout(root: tk.Tk) -> WindowLayout:
    """画面サイズから、左のメモ欄と右のブラウザ領域を決める。"""
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    left_width = max(520, screen_width // 2)
    right_width = max(520, screen_width - left_width)
    usable_height = max(640, screen_height - 80)
    return WindowLayout(
        screen_width=screen_width,
        screen_height=screen_height,
        left_width=left_width,
        right_width=right_width,
        usable_height=usable_height,
    )


def build_memo_target_text(memo_text: str, use_latest_line: bool) -> str:
    """メモの入力内容から、検索やURL判定に使う文字列を作る。"""
    lines = [line.strip() for line in memo_text.splitlines() if line.strip()]
    if not lines:
        return ""

    source_text = lines[-1] if use_latest_line else " ".join(lines)
    source_text = re.sub(r"^[\s\-・*#\d.)）]+", "", source_text)
    return re.sub(r"\s+", " ", source_text).strip()


def build_search_text(memo_text: str, use_latest_line: bool) -> str:
    """メモの入力内容から YouTube 検索に使う短い文字列を作る。"""
    return build_memo_target_text(memo_text, use_latest_line)[:MAX_SEARCH_TEXT_LENGTH]


def normalize_url(text: str) -> str | None:
    """URLとして開ける文字列なら、ブラウザ用のURLに整える。"""
    candidate = text.strip()
    if not candidate or re.search(r"\s", candidate):
        return None

    if candidate.startswith(("www.", "youtube.com/", "youtu.be/")):
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return candidate

    return None


class YouTubeBrowser:
    """Selenium が操作するブラウザを管理する。"""

    def __init__(self, layout: WindowLayout) -> None:
        self.layout = layout
        self.driver: webdriver.Chrome | None = None
        self.lock = threading.Lock()

    def start(self) -> None:
        with self.lock:
            if self._driver_is_ready():
                return

            self._discard_driver()
            self.driver = self._create_driver(YOUTUBE_HOME_URL)

    def search(self, search_text: str) -> bool:
        if not search_text:
            return False

        with self.lock:
            encoded_query = quote_plus(search_text)
            search_url = YOUTUBE_SEARCH_URL.format(query=encoded_query)
            self._navigate(search_url)
            return True

    def open_url(self, url: str) -> bool:
        if not url:
            return False

        with self.lock:
            self._navigate(url)
            return True

    def is_open(self) -> bool:
        with self.lock:
            return self._driver_is_ready()

    def close(self) -> None:
        with self.lock:
            self._discard_driver()

    def _create_driver(self, start_url: str) -> webdriver.Chrome:
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
            self.driver.quit()
        except WebDriverException:
            pass
        finally:
            self.driver = None


class App(tk.Tk):
    """tkinter のメモ入力画面と Selenium 検索処理をつなぐ。"""

    def __init__(self) -> None:
        super().__init__()
        self.title("YouTube Memo Search")

        self.layout_info = create_layout(self)
        self.geometry(f"{self.layout_info.left_width}x{self.layout_info.usable_height}+0+0")
        self.minsize(480, 520)

        self.browser = YouTubeBrowser(self.layout_info)
        self.last_search_text = ""
        self.latest_line_only = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(value="ブラウザを起動しています...")

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._start_browser)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=(12, 10, 12, 6))
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(1, weight=1)

        search_button = ttk.Button(toolbar, text="検索", command=lambda: self._search_now(force=True))
        search_button.grid(row=0, column=0, sticky="w")

        check = ttk.Checkbutton(
            toolbar,
            text="直近の行を検索",
            variable=self.latest_line_only,
        )
        check.grid(row=0, column=1, sticky="w", padx=(12, 0))

        note_frame = ttk.Frame(self, padding=(12, 0, 12, 8))
        note_frame.grid(row=1, column=0, sticky="nsew")
        note_frame.columnconfigure(0, weight=1)
        note_frame.rowconfigure(0, weight=1)

        self.memo = tk.Text(
            note_frame,
            wrap="word",
            undo=True,
            font=("Hiragino Sans", 15),
            padx=12,
            pady=12,
            relief="solid",
            borderwidth=1,
        )
        self.memo.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(note_frame, orient="vertical", command=self.memo.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.memo.configure(yscrollcommand=scrollbar.set)

        status = ttk.Label(self, textvariable=self.status_text, padding=(12, 0, 12, 12))
        status.grid(row=2, column=0, sticky="ew")

    def _start_browser(self) -> None:
        threading.Thread(target=self._start_browser_in_background, daemon=True).start()

    def _start_browser_in_background(self) -> None:
        try:
            self.browser.start()
        except WebDriverException as exc:
            self.after(0, self._show_browser_error, exc)
            return

        self.after(0, self.status_text.set, "メモを書いて「検索」を押すと、右側の YouTube に反映します。")
        self.after(0, self._schedule_focus_return)

    def _show_browser_error(self, exc: WebDriverException) -> None:
        self.status_text.set("ブラウザの起動に失敗しました。")
        messagebox.showerror(
            "Selenium エラー",
            "Chrome または ChromeDriver の起動に失敗しました。\n\n"
            "requirements.txt の依存関係をインストールし、Chrome が入っているか確認してください。\n\n"
            f"{exc}",
        )

    def _search_now(self, force: bool = False) -> None:
        memo_text = self.memo.get("1.0", "end").strip()
        target_text = build_memo_target_text(memo_text, self.latest_line_only.get())
        target_url = normalize_url(target_text)
        search_text = target_text[:MAX_SEARCH_TEXT_LENGTH]

        if not target_text:
            self.status_text.set("検索するメモを書いてください。")
            return

        action_key = f"url:{target_url}" if target_url else f"search:{search_text}"
        if not force and action_key == self.last_search_text and self.browser.is_open():
            return

        if target_url:
            self.status_text.set(f"URLを開いています: {target_url}")
        else:
            self.status_text.set(f"検索中: {search_text}")

        threading.Thread(
            target=self._navigate_in_background,
            args=(target_url, search_text, action_key),
            daemon=True,
        ).start()
        self._schedule_focus_return()

    def _navigate_in_background(self, target_url: str | None, search_text: str, action_key: str) -> None:
        try:
            if target_url:
                self.browser.open_url(target_url)
            else:
                self.browser.search(search_text)
        except WebDriverException as exc:
            self.after(0, self._show_search_error, exc)
            return

        self.last_search_text = action_key
        if target_url:
            self.after(0, self.status_text.set, f"URLを開きました: {target_url}")
        else:
            self.after(0, self.status_text.set, f"YouTube 検索済み: {search_text}")
        self.after(0, self._schedule_focus_return)

    def _show_search_error(self, exc: WebDriverException) -> None:
        self.status_text.set("検索に失敗しました。")
        messagebox.showerror("検索エラー", f"YouTube 検索に失敗しました。\n\n{exc}")

    def _return_focus_to_memo(self) -> None:
        try:
            self.memo.configure(state="normal")
            self.deiconify()
            self.lift()
            self.attributes("-topmost", True)
            self.after(120, self._release_topmost)
            self.focus_force()
            self.memo.focus_force()
        except tk.TclError:
            return

    def _release_topmost(self) -> None:
        try:
            self.attributes("-topmost", False)
            self.memo.focus_force()
        except tk.TclError:
            return

    def _schedule_focus_return(self) -> None:
        for delay_ms in (50, 200, 500, 1000, 1800):
            self.after(delay_ms, self._return_focus_to_memo)

    def _on_close(self) -> None:
        self.status_text.set("終了しています...")
        try:
            self.browser.close()
        finally:
            self.destroy()


def main() -> int:
    app = App()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
