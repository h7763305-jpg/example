from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any


AREAS = [
    "渋谷駅",
    "渋谷区",
    "渋谷",
    "新宿駅",
    "新宿区",
    "新宿",
    "池袋駅",
    "池袋",
    "恵比寿駅",
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

AREA_SUFFIXES = ("駅周辺", "駅近", "周辺", "エリア")


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

    matches.sort(key=lambda item: (item[0], -len(item[1])))
    return matches[0][1]


def clean_area_candidate(candidate: str) -> str | None:
    """「渋谷で焼肉」のような表現から、場所名だけを取り出す。"""
    area = candidate.strip()
    for separator in ("。", "、", ",", " ", "に"):
        if separator in area:
            area = area.rsplit(separator, 1)[-1].strip()

    for suffix in AREA_SUFFIXES:
        if area.endswith(suffix):
            area = area.removesuffix(suffix)

    if not area or re.fullmatch(r"\d{1,2}月\d{1,2}日?", area):
        return None
    return area


def extract_area_before_genre(text: str, genre: str | None) -> str | None:
    """「渋谷で焼肉」のように、ジャンル直前の「場所で」からエリアを抜く。"""
    if not genre:
        return None

    pattern = rf"(?P<area>[^\s。、,]+?)で\s*{re.escape(genre)}"
    for match in re.finditer(pattern, text):
        area = clean_area_candidate(match.group("area"))
        if area:
            return area
    return None


def extract_standalone_area(text: str, genre: str | None) -> str | None:
    """地名だけが書かれている場合は、そのまま食べログのエリア候補検索に渡す。"""
    if genre is not None:
        return None

    area = clean_area_candidate(text)
    if area is None:
        return None
    if len(area) > 20 or re.search(r"(円|予算|個室|ランチ|夜|日付|予約)", area):
        return None
    return area


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


def build_future_date(month: int, day: int, today: date) -> date | None:
    """年が書かれていない月日を、今日以降の予約日として解釈する。"""
    try:
        selected = date(today.year, month, day)
    except ValueError:
        return None

    if selected < today:
        try:
            return date(today.year + 1, month, day)
        except ValueError:
            return None

    return selected


def build_date(year: int | None, month: int, day: int, today: date) -> date | None:
    """抽出した年月日を実在する日付に変換する。"""
    if year is None:
        return build_future_date(month, day, today)

    try:
        return date(year, month, day)
    except ValueError:
        return None


def extract_search_date(text: str, today: date | None = None) -> str | None:
    """7月12、7月12日、2026/7/12、明日などの表現から検索日を返す。"""
    base_date = today or date.today()

    relative_dates = {
        "明後日": base_date + timedelta(days=2),
        "あさって": base_date + timedelta(days=2),
        "明日": base_date + timedelta(days=1),
        "あした": base_date + timedelta(days=1),
        "今日": base_date,
        "本日": base_date,
    }
    for word, selected in relative_dates.items():
        if word in text:
            return selected.isoformat()

    patterns = [
        r"(?P<year>20\d{2})[/-](?P<month>\d{1,2})[/-](?P<day>\d{1,2})",
        r"(?P<year>20\d{2})年\s*(?P<month>\d{1,2})月\s*(?P<day>\d{1,2})日?",
        r"(?P<month>\d{1,2})月\s*(?P<day>\d{1,2})(?:日)?(?![時分秒\d])",
        r"(?<!\d)(?P<month>\d{1,2})/(?P<day>\d{1,2})(?!\d)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match is None:
            continue

        year_text = match.groupdict().get("year")
        year = int(year_text) if year_text is not None else None
        month = int(match.group("month"))
        day = int(match.group("day"))
        selected = build_date(year, month, day, base_date)
        if selected is not None:
            return selected.isoformat()

    return None


def extract_tabelog_conditions(memo_text: str) -> dict[str, Any]:
    """食べログ検索に使うエリア、ジャンル、予算、キーワード、日付を辞書で返す。"""
    text = normalize_memo_text(memo_text)
    genre = find_first_word(text, GENRES)
    area = extract_area_before_genre(text, genre) or find_first_word(text, AREAS) or extract_standalone_area(text, genre)
    budget = extract_budget(text)
    keywords = extract_keywords(text, genre)
    search_date = extract_search_date(text)

    result: dict[str, Any] = {
        "area": area,
        "genre": genre,
        "budget": budget,
        "keywords": keywords,
        "date": search_date,
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
