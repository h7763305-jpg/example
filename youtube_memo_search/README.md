# YouTube Memo Search

メモ欄に入力した内容から、ボタン操作で YouTube を検索する tkinter + Selenium アプリです。

## セットアップ

```bash
cd /Users/izumikahiroto/Desktop/dev/youtube_memo_search
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 起動

```bash
python3 app.py
```

起動すると、左半分にメモ欄、右半分に Selenium が操作するブラウザが開きます。
メモを書いて「検索」を押すと、メモ内容から検索語を作って YouTube 検索を実行します。
URL を貼って「検索」を押した場合は、その URL を直接開きます。
入力中は YouTube に反映しません。
YouTube のタブや Chrome ウィンドウを閉じた場合も、次の検索時に Chrome を開き直します。

## 使い方

- メモ欄に検索したい内容を書きます。
- 「検索」を押すと YouTube に反映します。
- URL を開きたい場合は、`https://...` や `youtube.com/...` を貼って「検索」を押します。
- 「直近の行を検索」がオンの場合は、最後に書いた空でない行だけを検索します。
- オフにすると、メモ全体から検索語を作ります。

## 注意

- Chrome がインストールされている環境を想定しています。
- Selenium Manager が自動で対応ドライバを取得します。初回だけ時間がかかる場合があります。
- YouTube の画面は tkinter 内に埋め込むのではなく、Selenium が起動したブラウザを右半分に配置します。
