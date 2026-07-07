from __future__ import annotations

import json
import re
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.parse import urlparse

try:
    from selenium.common.exceptions import WebDriverException

    from memo_parser import extract_search_date, extract_tabelog_conditions
    from selenium_browser import SeleniumBrowser, WindowLayout
    from tabelog_search import TABELOG_HOME_URL, search_tabelog
    from youtube_search import YOUTUBE_HOME_URL, search_youtube
except ModuleNotFoundError as exc:
    print(
        "selenium がインストールされていない。\n"
        "次のコマンドでセットアップしてから起動してください。\n\n"
        "cd /Users/izumikahiroto/Desktop/dev/youtube_memo_search\n"
        "python3 -m venv .venv\n"
        "source .venv/bin/activate\n"
        "pip install -r requirements.txt\n"
        "python3 app.py",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc


MAX_SEARCH_TEXT_LENGTH = 80
SEARCH_TARGETS = {
    "食べログ": TABELOG_HOME_URL,
    "YouTube": YOUTUBE_HOME_URL,
}


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


def build_memo_target_text(memo_text: str) -> str:
    """メモの入力内容全体から、検索やURL判定に使う文字列を作る。"""
    lines = [line.strip() for line in memo_text.splitlines() if line.strip()]
    if not lines:
        return ""

    source_text = " ".join(lines)
    return re.sub(r"\s+", " ", source_text).strip()


def normalize_url(text: str) -> str | None:
    """URLとして開ける文字列なら、ブラウザ用のURLに整える。"""
    candidate = text.strip()
    if not candidate or re.search(r"\s", candidate):
        return None

    if candidate.startswith(("www.", "youtube.com/", "youtu.be/", "tabelog.com/")):
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return candidate

    return None


class App(tk.Tk):
    """tkinter のメモ入力画面と Selenium 検索処理をつなぐ。"""

    def __init__(self) -> None:
        super().__init__()
        self.title("Memo Search")

        self.layout_info = create_layout(self)
        self.geometry(f"{self.layout_info.left_width}x{self.layout_info.usable_height}+0+0")
        self.minsize(520, 560)

        self.search_target = tk.StringVar(value="食べログ")
        self.status_text = tk.StringVar(value="ブラウザを起動しています...")
        self.extracted_text = tk.StringVar(value="抽出結果: 未実行")
        self.last_action_key = ""
        self.browser = SeleniumBrowser(self.layout_info, SEARCH_TARGETS[self.search_target.get()])

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._start_browser)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=(12, 10, 12, 6))
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(2, weight=1)

        search_button = ttk.Button(toolbar, text="検索", command=lambda: self._search_now(force=True))
        search_button.grid(row=0, column=0, sticky="w")

        target_select = ttk.Combobox(
            toolbar,
            textvariable=self.search_target,
            values=list(SEARCH_TARGETS.keys()),
            state="readonly",
            width=10,
        )
        target_select.grid(row=0, column=1, sticky="w", padx=(10, 0))
        target_select.bind("<<ComboboxSelected>>", self._on_target_changed)

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
        self.memo.bind("<KeyPress>", self._handle_memo_key)
        self.memo.bind("<KeyPress-space>", self._insert_space)
        self.memo.bind("<KeyPress-KP_Space>", self._insert_space)

        scrollbar = ttk.Scrollbar(note_frame, orient="vertical", command=self.memo.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.memo.configure(yscrollcommand=scrollbar.set)

        result = ttk.Label(
            self,
            textvariable=self.extracted_text,
            padding=(12, 2, 12, 4),
            wraplength=max(420, self.layout_info.left_width - 24),
        )
        result.grid(row=2, column=0, sticky="ew")

        status = ttk.Label(self, textvariable=self.status_text, padding=(12, 0, 12, 12))
        status.grid(row=3, column=0, sticky="ew")

    def _on_target_changed(self, _event: tk.Event) -> None:
        target = self.search_target.get()
        self.status_text.set(f"検索先を切り替えました: {target}")
        self.browser.start_url = SEARCH_TARGETS[target]

    def _handle_memo_key(self, event: tk.Event) -> str | None:
        if self._is_space_key(event):
            return self._insert_space(event)
        return None

    def _is_space_key(self, event: tk.Event) -> bool:
        # macOSのTkでは日本語入力中にkeysymだけではスペースを拾えない場合がある。
        return (
            event.keysym in {"space", "KP_Space"}
            or event.char in {" ", "　"}
            or event.keycode == 49
        )

    def _insert_space(self, _event: tk.Event) -> str:
        self.memo.insert("insert", " ")
        print("[ui] スペースを入力")
        return "break"

    def _start_browser(self) -> None:
        threading.Thread(target=self._start_browser_in_background, daemon=True).start()

    def _start_browser_in_background(self) -> None:
        try:
            self.browser.start()
        except WebDriverException as exc:
            self.after(0, self._show_browser_error, exc)
            return

        self.after(0, self.status_text.set, "メモを書いて「検索」を押すと、右側のブラウザに反映します。")
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
        target_text = build_memo_target_text(memo_text)
        target_url = normalize_url(target_text)
        selected_date = extract_search_date(target_text)

        if not target_text:
            self.status_text.set("検索するメモを書いてください。")
            return

        search_target = self.search_target.get()
        action_key = self._build_action_key(search_target, target_text, target_url, selected_date)
        if not force and action_key == self.last_action_key and self.browser.is_open():
            return

        self.status_text.set(f"{search_target}で検索中...")
        threading.Thread(
            target=self._navigate_in_background,
            args=(search_target, target_url, target_text, selected_date, action_key),
            daemon=True,
        ).start()
        self._schedule_focus_return()

    def _build_action_key(
        self,
        search_target: str,
        target_text: str,
        target_url: str | None,
        selected_date: str | None,
    ) -> str:
        date_part = selected_date or "date:none"
        if target_url:
            return f"{search_target}:url:{target_url}:{date_part}"
        return f"{search_target}:text:{target_text}:{date_part}"

    def _navigate_in_background(
        self,
        search_target: str,
        target_url: str | None,
        target_text: str,
        selected_date: str | None,
        action_key: str,
    ) -> None:
        try:
            if target_url:
                self.browser.navigate(target_url)
                self.after(0, self.extracted_text.set, "抽出結果: URLを直接開きました")
            elif search_target == "食べログ":
                conditions = extract_tabelog_conditions(target_text)
                if conditions.get("date") is None:
                    conditions["date"] = selected_date
                conditions_json = json.dumps(conditions, ensure_ascii=False)
                self.after(0, self.extracted_text.set, f"抽出結果: {conditions_json}")
                search_tabelog(self.browser, conditions)
            else:
                search_text = target_text[:MAX_SEARCH_TEXT_LENGTH]
                self.after(0, self.extracted_text.set, f"検索語: {search_text}")
                search_youtube(self.browser, search_text)
        except WebDriverException as exc:
            self.after(0, self._show_search_error, exc)
            return

        self.last_action_key = action_key
        self.after(0, self.status_text.set, f"{search_target}検索を実行しました。")
        self.after(0, self._schedule_focus_return)

    def _show_search_error(self, exc: WebDriverException) -> None:
        self.status_text.set("検索に失敗しました。")
        messagebox.showerror("検索エラー", f"検索に失敗しました。\n\n{exc}")

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
