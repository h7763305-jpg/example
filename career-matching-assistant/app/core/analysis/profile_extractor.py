from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

# Pythonの書き方メモ:
# - class は、関連するデータや処理をまとめた型を作るための書き方。
# - @dataclass は、プロフィールのようなデータ入れ物を簡単に作るための指定。
# - def は、あとで呼び出せる処理のまとまり「関数」を作るための書き方。
# - list[str] は、文字列のリストを意味する型の説明。例: ["Python", "AWS"]。
# - str | None は、文字列または未設定(None)が入るという意味。
# - return は、関数で作った結果を呼び出し元へ返すための書き方。


@dataclass(frozen=True)
class CandidateProfile:
    """面談内容から拾った、企業選出に使う転職者情報。

    面談文章のままだと企業データと比較しづらいため、スキル・希望条件・
    避けたい条件などの項目に分けて保持する。
    """
    current_role: str | None
    skills: list[str]
    preferred_roles: list[str]
    preferred_industries: list[str]
    preferred_location: str | None
    remote_preference: str | None
    salary_expectation: str | None
    career_goals: list[str]
    avoid_conditions: list[str]
    important_values: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_summary(interview_text: str) -> str:
    """整理したプロフィールから、レポート冒頭に出す短い面談要約を作る。"""
    profile = extract_candidate_profile(interview_text)
    summary_parts = []

    if profile.current_role:
        summary_parts.append(f"現職は{profile.current_role}。")
    if profile.skills:
        summary_parts.append(f"主な経験・スキルは{', '.join(profile.skills)}。")
    if profile.preferred_industries:
        summary_parts.append(f"関心業界は{', '.join(profile.preferred_industries)}。")
    if profile.salary_expectation:
        summary_parts.append(f"希望年収は{profile.salary_expectation}。")
    if profile.remote_preference:
        summary_parts.append(f"働き方は{profile.remote_preference}を希望。")
    if profile.avoid_conditions:
        summary_parts.append(f"避けたい条件は{', '.join(profile.avoid_conditions)}。")

    return "".join(summary_parts)


def extract_candidate_profile(interview_text: str) -> CandidateProfile:
    """面談テキストを、企業データと照合できるプロフィール項目へ整理する。

    今はMVPなのでキーワード一致で拾っている。将来LLMで読み取る形にしても、
    ここから返す CandidateProfile の項目は変えない方針。
    """
    text = interview_text.lower()

    # MVPではキーワードでプロフィールを整理する。後でLLM化しても出力形式は保つ。
    return CandidateProfile(
        current_role=_first_match(
            interview_text,
            {
                "バックエンドエンジニア": ["バックエンドエンジニア"],
                "フロントエンドエンジニア": ["フロントエンドエンジニア"],
                "インフラエンジニア": ["インフラエンジニア", "SRE", "sre"],
                "データエンジニア": ["データエンジニア"],
                "機械学習エンジニア": ["機械学習エンジニア"],
            },
        ),
        skills=_collect_matches(
            text,
            {
                "Python": ["python"],
                "FastAPI": ["fastapi"],
                "AWS": ["aws"],
                "React": ["react"],
                "TypeScript": ["typescript"],
                "Django": ["django"],
                "Terraform": ["terraform"],
                "機械学習": ["機械学習", "machine learning", "ml"],
            },
        ),
        preferred_roles=_collect_matches(
            interview_text,
            {
                "バックエンドエンジニア": ["バックエンドエンジニア"],
                "フロントエンドエンジニア": ["フロントエンドエンジニア"],
                "テックリード": ["テックリード"],
                "機械学習エンジニア": ["機械学習エンジニア"],
            },
        ),
        preferred_industries=_collect_matches(
            interview_text,
            {
                "SaaS": ["SaaS", "saas"],
                "HRTech": ["HRTech", "hrtech"],
                "AI": ["AI", "ai"],
            },
        ),
        preferred_location=_first_match(
            interview_text,
            {
                "東京": ["東京"],
                "大阪": ["大阪"],
                "福岡": ["福岡"],
            },
        ),
        remote_preference=_first_match(
            interview_text,
            {
                "週3日以上リモート": ["週3日以上のリモート", "週3以上のリモート", "週3日リモート"],
                "週1日リモート可": ["週1日でも問題", "週1日リモート"],
                "フルリモート": ["フルリモート"],
                "リモート可": ["リモート勤務", "リモート"],
            },
        ),
        salary_expectation=_first_match(
            interview_text,
            {
                "800万円以上": ["800万円以上"],
                "700万円以上": ["700万円以上"],
                "600万円以上": ["600万円以上"],
            },
        ),
        career_goals=_collect_matches(
            interview_text,
            {
                "テックリードを目指したい": ["テックリードを目指したい", "テックリード"],
                "技術的な裁量を持ちたい": ["技術的な裁量", "技術的裁量", "裁量"],
                "ユーザー体験を改善したい": ["ユーザー体験", "UX"],
                "研究開発に関わりたい": ["研究開発"],
            },
        ),
        avoid_conditions=_collect_matches(
            interview_text,
            {
                "受託開発中心": ["受託開発中心", "受託"],
                "残業が多い": ["残業が多い"],
                "原則出社": ["原則出社"],
            },
        ),
        important_values=_collect_matches(
            interview_text,
            {
                "自社プロダクト": ["自社プロダクト"],
                "技術的裁量": ["技術的な裁量", "技術的裁量", "裁量"],
                "ユーザー志向": ["ユーザー体験", "ユーザー志向"],
                "SaaS": ["SaaS", "saas"],
            },
        ),
    )


def _collect_matches(text: str, patterns: dict[str, list[str]]) -> list[str]:
    """複数候補を拾う項目用。例: スキル、希望業界、避けたい条件。"""
    matches = []
    for value, keywords in patterns.items():
        if any(keyword.lower() in text.lower() for keyword in keywords):
            matches.append(value)
    return matches


def _first_match(text: str, patterns: dict[str, list[str]]) -> str | None:
    """1つだけ採用する項目用。例: 希望勤務地、希望年収。"""
    matches = _collect_matches(text, patterns)
    return matches[0] if matches else None
