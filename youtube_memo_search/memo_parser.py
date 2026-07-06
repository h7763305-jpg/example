from __future__ import annotations

import re
from typing import Any


AREAS = [
    "渋谷",
    "新宿",
    "池袋",
    "恵比寿",
    "銀座",
    "東京",
    "品川",
    "上野",
    "横浜",
    "吉祥寺",
    "六本木",
    "中目黒",
    "代官山",
]

GENRES = [
    "焼肉",
    "寿司",
    "鮨",
    "居酒屋",
    "ラーメン",
    "カフェ",
    "イタリアン",
    "フレンチ",
    "中華",
    "和食",
    "そば",
    "うどん",
    "カレー",
    "バー",
    "ビストロ",
]

KEYWORD_CANDIDATES = [
    "個室",
    "夜",
    "ランチ",
    "デート",
    "飲み放題",
    "食べ放題",
    "駅近",
    "子連れ",
    "接待",
    "女子会",
    "深夜",
    "禁煙",
    "喫煙",
    "テラス",
    "おしゃれ",
]


def normalize_memo_text(memo_text: str) -> str:
    """改行や句読点を検索しやすい形にそろえる。"""
    text = memo_text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_first_word(text: str, candidates: list[str]) -> str | None:
    """候補リストのうち、メモに最初に出てきた言葉を返す。"""
    matches: list[tuple[int, str]] = []
    for candidate in candidates:
        position = text.find(candidate)
        if position >= 0:
            matches.append((position, candidate))

    if not matches:
        return None

    matches.sort(key=lambda item: item[0])
    return matches[0][1]


def extract_budget(text: str) -> int | None:
    """5000円以内、5,000円まで、予算5000円のような表現から金額を抜き出す。"""
    yen_match = re.search(r"(\d{1,3}(?:,\d{3})+|\d{3,6})\s*円", text)
    if yen_match:
        return int(yen_match.group(1).replace(",", ""))

    budget_match = re.search(r"予算\s*(\d{3,6})", text)
    if budget_match:
        return int(budget_match.group(1))

    return None


def extract_keywords(text: str, genre: str | None) -> list[str]:
    """メモに含まれる条件キーワードを重複なしで返す。"""
    keywords: list[str] = []
    for keyword in KEYWORD_CANDIDATES:
        if keyword in text and keyword != genre and keyword not in keywords:
            keywords.append(keyword)
    return keywords


def extract_tabelog_conditions(memo_text: str) -> dict[str, Any]:
    """食べログ検索に使うエリア、ジャンル、予算、キーワードを辞書で返す。"""
    text = normalize_memo_text(memo_text)
    area = find_first_word(text, AREAS)
    genre = find_first_word(text, GENRES)
    budget = extract_budget(text)
    keywords = extract_keywords(text, genre)

    result: dict[str, Any] = {
        "area": area,
        "genre": genre,
        "budget": budget,
        "keywords": keywords,
    }
    print(f"[parser] {result}")
    return result


def build_tabelog_keyword_text(conditions: dict[str, Any]) -> str:
    """ジャンルとキーワードを食べログのキーワード欄に入れる文字列へ変換する。"""
    words: list[str] = []

    genre = conditions.get("genre")
    if isinstance(genre, str) and genre:
        words.append(genre)

    keywords = conditions.get("keywords")
    if isinstance(keywords, list):
        for keyword in keywords:
            if isinstance(keyword, str) and keyword and keyword not in words:
                words.append(keyword)

    return " ".join(words)
