from __future__ import annotations

import re
import sys
from urllib.parse import quote_plus

try:
    from PySide6.QtCore import QCoreApplication, QLibraryInfo, QPluginLoader, QTimer, QUrl
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSizePolicy,
        QSplitter,
        QTextEdit,
        QToolBar,
        QWidget,
    )
except (ImportError, ModuleNotFoundError) as exc:
    print(
        "PySide6 がインストールされていません。\n"
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
SEARCH_DELAY_MS = 1000
MAX_SEARCH_TEXT_LENGTH = 80
QT_PLUGIN_LOADERS: list[QPluginLoader] = []


def prepare_qt_plugins() -> None:
    """macOS で Qt の platform plugin 探索が外れる環境向けに明示設定する。"""
    plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
    QCoreApplication.setLibraryPaths([plugins_path])

    if sys.platform == "darwin":
        cocoa_plugin = f"{plugins_path}/platforms/libqcocoa.dylib"
        loader = QPluginLoader(cocoa_plugin)
        loader.load()
        QT_PLUGIN_LOADERS.append(loader)


def build_search_text(memo_text: str, use_latest_line: bool) -> str:
    """メモの入力内容から YouTube 検索に使う短い文字列を作る。"""
    lines = [line.strip() for line in memo_text.splitlines() if line.strip()]
    if not lines:
        return ""

    source_text = lines[-1] if use_latest_line else " ".join(lines)
    source_text = re.sub(r"^[\s\-・*#\d.)）]+", "", source_text)
    source_text = re.sub(r"\s+", " ", source_text).strip()
    return source_text[:MAX_SEARCH_TEXT_LENGTH]


class App(QMainWindow):
    """メモ入力欄と YouTube を 1 つのアプリ窓に並べる。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("YouTube Memo Search")

        self.last_search_text = ""
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.search_now)

        self._build_ui()
        self._size_window()
        self.browser.setUrl(QUrl(YOUTUBE_HOME_URL))

    def _build_ui(self) -> None:
        toolbar = QToolBar("検索")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        search_button = QPushButton("今すぐ検索")
        search_button.clicked.connect(self.search_now)
        toolbar.addWidget(search_button)

        self.latest_line_only = QCheckBox("直近の行を検索")
        self.latest_line_only.setChecked(True)
        self.latest_line_only.stateChanged.connect(self.schedule_search)
        toolbar.addWidget(self.latest_line_only)

        splitter = QSplitter()
        self.memo = QTextEdit()
        self.memo.setPlaceholderText("メモを書くと、右側の YouTube で自動検索します。")
        self.memo.setAcceptRichText(False)
        self.memo.setStyleSheet(
            "QTextEdit { font-size: 15px; padding: 10px; border: 1px solid #c8c8c8; }"
        )
        self.memo.textChanged.connect(self.schedule_search)

        self.browser = QWebEngineView()
        self.browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.browser.loadStarted.connect(lambda: self.status_label.setText("読み込み中..."))
        self.browser.loadFinished.connect(self._on_load_finished)

        splitter.addWidget(self.memo)
        splitter.addWidget(self.browser)
        splitter.setSizes([520, 820])
        splitter.setChildrenCollapsible(False)

        self.setCentralWidget(splitter)

        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(8, 2, 8, 2)
        self.status_label = QLabel("YouTube をアプリ内に読み込んでいます。")
        status_layout.addWidget(self.status_label)
        self.statusBar().addPermanentWidget(status_widget, 1)

    def _size_window(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            self.resize(1360, 760)
            return

        available = screen.availableGeometry()
        width = min(1440, max(1100, int(available.width() * 0.92)))
        height = min(900, max(680, int(available.height() * 0.88)))
        self.resize(width, height)
        self.move(
            available.x() + max(0, (available.width() - width) // 2),
            available.y() + max(0, (available.height() - height) // 2),
        )

    def schedule_search(self) -> None:
        self.search_timer.start(SEARCH_DELAY_MS)

    def search_now(self) -> None:
        self.search_timer.stop()
        search_text = build_search_text(
            self.memo.toPlainText(),
            self.latest_line_only.isChecked(),
        )

        if not search_text:
            self.status_label.setText("検索するメモを書いてください。")
            return
        if search_text == self.last_search_text:
            return

        encoded_query = quote_plus(search_text)
        self.last_search_text = search_text
        self.status_label.setText(f"検索中: {search_text}")
        self.browser.setUrl(QUrl(YOUTUBE_SEARCH_URL.format(query=encoded_query)))

    def _on_load_finished(self, ok: bool) -> None:
        if ok:
            if self.last_search_text:
                self.status_label.setText(f"YouTube 検索済み: {self.last_search_text}")
            else:
                self.status_label.setText("メモを書くと、右側の YouTube で自動検索します。")
            return

        self.status_label.setText("YouTube の読み込みに失敗しました。")
        QMessageBox.warning(
            self,
            "読み込みエラー",
            "YouTube の読み込みに失敗しました。ネットワーク接続を確認してください。",
        )


def main() -> int:
    prepare_qt_plugins()
    app = QApplication(sys.argv)
    window = App()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
