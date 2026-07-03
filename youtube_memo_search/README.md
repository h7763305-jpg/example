# YouTube Memo Search

メモ欄に入力した内容から、アプリ内の YouTube を自動検索する PySide6 アプリです。

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

起動すると、1 つのアプリ窓の左半分にメモ欄、右半分に YouTube が表示されます。
メモ入力が止まってから約 1 秒後に、メモ内容から検索語を作って YouTube 検索を実行します。

## 使い方

- メモ欄に検索したい内容を書きます。
- 「直近の行を検索」がオンの場合は、最後に書いた空でない行だけを検索します。
- オフにすると、メモ全体から検索語を作ります。
- 「今すぐ検索」で待たずに検索できます。

## 注意

- YouTube は PySide6 の内蔵ブラウザで表示します。
- 初回セットアップ時は PySide6 のインストールに時間がかかる場合があります。
