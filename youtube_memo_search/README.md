# YouTube Memo Search

メモ欄に入力した内容から、YouTube を自動検索する tkinter + Selenium アプリです。

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
メモ入力が止まってから約 1 秒後に、メモ内容から検索語を作って YouTube 検索を実行します。

## 使い方

- メモ欄に検索したい内容を書きます。
- 「直近の行を検索」がオンの場合は、最後に書いた空でない行だけを検索します。
- オフにすると、メモ全体から検索語を作ります。
- 「今すぐ検索」で待たずに検索できます。

## 注意

- Chrome がインストールされている環境を想定しています。
- Selenium Manager が自動で対応ドライバを取得します。初回だけ時間がかかる場合があります。
- YouTube の画面は tkinter 内に埋め込むのではなく、Selenium が起動したブラウザを右半分に配置します。
