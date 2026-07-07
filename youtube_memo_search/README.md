# Memo Search

Tkinter のメモ欄に入力した内容から、Selenium でブラウザ検索を操作する試作アプリです。
現在は食べログ検索を主対象にし、既存の YouTube 検索も切り替えで残しています。

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

起動すると、左半分にメモ欄、右半分に Selenium が操作する Chrome が開きます。
メモを書いて「検索」を押すと、メモ欄全体から食べログ向けにエリア、ジャンル、予算、キーワードをルールベースで抽出して検索します。
メモに日付を書いた場合は、その日付を食べログ検索URLへ反映します。

## メモ例

```text
7月12日に渋谷で焼肉。夜で5000円以内。個室がある店。
```

抽出例:

```json
{
  "area": "渋谷",
  "genre": "焼肉",
  "budget": 5000,
  "keywords": ["個室", "夜"],
  "date": "2026-07-12"
}
```

## ファイル構成

- `app.py`: Tkinter 画面と検索ボタン処理
- `memo_parser.py`: メモから食べログ検索条件を抽出
- `selenium_browser.py`: Chrome 起動、画面配置、ページ移動、終了処理
- `tabelog_search.py`: 食べログの入力欄、予算欄、検索ボタン操作
- `tabelog_selectors.py`: 食べログ画面の selector 管理
- `youtube_search.py`: YouTube 検索処理
- `inspect_tabelog.py`: 食べログ画面の selector 確認用スクリプト

## 注意

- Chrome がインストールされている環境を想定しています。
- Selenium Manager が自動で対応ドライバを取得します。初回だけ時間がかかる場合があります。
- 食べログの画面構造が変わると selector の調整が必要です。その場合は `tabelog_selectors.py` を更新します。
- 予算は食べログの結果ページにある上限予算 `LstCosT` に反映します。
- 日付は食べログ検索URLの `svd` パラメータへ `YYYYMMDD` 形式で反映します。
- 日付表現は `7月12`、`7月12日`、`2026/7/12`、`2026年7月12日`、`今日`、`明日`、`明後日` に対応しています。
