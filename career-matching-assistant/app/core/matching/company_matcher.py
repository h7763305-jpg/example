from __future__ import annotations

import re
from typing import Any

# Pythonの書き方メモ:
# - def は、あとで呼び出せる処理のまとまり「関数」を作るための書き方。
# - if / elif / else は、条件によって処理を分けるための書き方。
# - for は、企業や条件を1つずつ見ていくための繰り返し処理。
# - set は、リスト同士の共通点を調べやすくするためのデータ型。
# - append は、リストに理由・懸念点・質問を追加する処理。
# - return は、判定結果を呼び出し元へ返すための書き方。


SelectionResult = dict[str, Any]


def select_companies(
    candidate_profile: dict[str, Any], companies: list[dict[str, Any]]
) -> list[SelectionResult]:
    """転職者プロフィールと各企業を照合し、見やすい順に並べて返す。"""
    results = [_evaluate_company(candidate_profile, company) for company in companies]
    return sorted(results, key=_sort_key)


def _evaluate_company(
    candidate_profile: dict[str, Any], company: dict[str, Any]
) -> SelectionResult:
    """1社分について、合う理由・懸念点・追加確認質問を作る。"""
    reasons: list[str] = []
    concerns: list[str] = []
    follow_up_questions: list[str] = []

    # 各観点を順番に見て、合っている点は reasons、不安な点は concerns に入れる。
    _check_role(candidate_profile, company, reasons, concerns, follow_up_questions)
    _check_skills(candidate_profile, company, reasons, concerns, follow_up_questions)
    _check_industry(candidate_profile, company, reasons, concerns)
    _check_location(candidate_profile, company, reasons, concerns)
    _check_remote(candidate_profile, company, reasons, concerns, follow_up_questions)
    _check_salary(candidate_profile, company, reasons, concerns, follow_up_questions)
    _check_values(candidate_profile, company, reasons, concerns)
    _check_avoid_conditions(candidate_profile, company, concerns)

    # 集まった理由と懸念点から、ユーザー向けの選出区分を決める。
    label = _decide_label(reasons, concerns)

    if not follow_up_questions and label in {"条件確認が必要", "現時点ではマッチが弱い"}:
        follow_up_questions.append("候補者にとって優先度の高い条件を追加確認する")

    return {
        "company_name": company["company_name"],
        "selection_label": label,
        "selection_reasons": reasons,
        "concerns": concerns,
        "follow_up_questions": follow_up_questions,
    }


def _check_role(
    profile: dict[str, Any],
    company: dict[str, Any],
    reasons: list[str],
    concerns: list[str],
    follow_up_questions: list[str],
) -> None:
    """希望職種と企業の募集職種が合っているかを見る。"""
    preferred_roles = set(profile.get("preferred_roles", []))
    open_roles = set(company.get("open_roles", []))

    if preferred_roles & open_roles:
        reasons.append("希望職種と募集職種が一致している")
    elif "テックリード" in preferred_roles and any("テックリード" in role for role in open_roles):
        reasons.append("テックリード志向と募集ポジションが近い")
        follow_up_questions.append("テックリード候補として求められるリード経験の水準を確認する")
    else:
        concerns.append("希望職種と募集職種の一致が弱い")
        follow_up_questions.append("募集職種が候補者の希望キャリアに合うか確認する")


def _check_skills(
    profile: dict[str, Any],
    company: dict[str, Any],
    reasons: list[str],
    concerns: list[str],
    follow_up_questions: list[str],
) -> None:
    """候補者のスキルが、必須スキル・歓迎スキルと重なるかを見る。"""
    skills = set(profile.get("skills", []))
    required = set(company.get("required_skills", []))
    preferred = set(company.get("preferred_skills", []))
    required_matches = sorted(skills & required)
    preferred_matches = sorted(skills & preferred)
    missing_required = sorted(required - skills)

    if required_matches:
        reasons.append(f"必須スキルと一致している: {', '.join(required_matches)}")
    if preferred_matches:
        reasons.append(f"歓迎スキルと一致している: {', '.join(preferred_matches)}")
    if missing_required:
        concerns.append(f"必須スキルの確認が必要: {', '.join(missing_required)}")
        follow_up_questions.append(f"{', '.join(missing_required)}の実務経験があるか確認する")


def _check_industry(
    profile: dict[str, Any],
    company: dict[str, Any],
    reasons: list[str],
    concerns: list[str],
) -> None:
    """希望業界と企業の業界が一致しているかを見る。"""
    preferred_industries = set(profile.get("preferred_industries", []))
    industry = company.get("industry")

    if industry in preferred_industries:
        reasons.append(f"関心業界と一致している: {industry}")
    elif preferred_industries:
        concerns.append(f"関心業界との一致は弱い: {industry}")


def _check_location(
    profile: dict[str, Any],
    company: dict[str, Any],
    reasons: list[str],
    concerns: list[str],
) -> None:
    """希望勤務地と企業の勤務地が一致しているかを見る。"""
    preferred_location = profile.get("preferred_location")
    location = company.get("location")

    if preferred_location and location == preferred_location:
        reasons.append(f"希望勤務地と一致している: {location}")
    elif preferred_location:
        concerns.append(f"希望勤務地と異なる: {location}")


def _check_remote(
    profile: dict[str, Any],
    company: dict[str, Any],
    reasons: list[str],
    concerns: list[str],
    follow_up_questions: list[str],
) -> None:
    """リモート希望と企業の勤務条件が近いかを見る。"""
    remote_preference = profile.get("remote_preference")
    remote_policy = company.get("remote_policy", "")

    if not remote_preference:
        return

    if remote_preference == "週1日リモート可" and "週1" in remote_policy:
        reasons.append(f"リモート希望と勤務条件が近い: {remote_policy}")
    elif "フルリモート" in remote_policy or "週3" in remote_policy:
        reasons.append(f"リモート希望と勤務条件が近い: {remote_policy}")
    elif "週1" in remote_policy or "原則出社" in remote_policy:
        concerns.append(f"リモート希望と勤務条件にズレがある: {remote_policy}")
        follow_up_questions.append("リモート勤務頻度が候補者の希望を満たすか確認する")
    else:
        concerns.append(f"リモート条件の確認が必要: {remote_policy}")
        follow_up_questions.append("実際のリモート勤務頻度を確認する")


def _check_salary(
    profile: dict[str, Any],
    company: dict[str, Any],
    reasons: list[str],
    concerns: list[str],
    follow_up_questions: list[str],
) -> None:
    """希望年収が企業の年収レンジに届きそうかを見る。"""
    expected = _parse_salary_floor(profile.get("salary_expectation"))
    salary_floor, salary_ceiling = _parse_salary_range(company.get("salary_range", ""))

    if expected is None or salary_floor is None or salary_ceiling is None:
        follow_up_questions.append("希望年収と提示レンジの詳細を確認する")
        return

    if salary_ceiling >= expected:
        reasons.append(f"希望年収に届く可能性がある: {company.get('salary_range')}")
        if salary_floor < expected:
            follow_up_questions.append("提示年収が希望額に届く条件を確認する")
    else:
        concerns.append(f"希望年収に届かない可能性がある: {company.get('salary_range')}")
        follow_up_questions.append("年収条件を満たせるか確認する")


def _check_values(
    profile: dict[str, Any],
    company: dict[str, Any],
    reasons: list[str],
    concerns: list[str],
) -> None:
    """自社プロダクト志向など、候補者が重視する価値観と企業文化を見る。"""
    values = set(profile.get("important_values", []))
    culture = set(company.get("culture", []))
    matches = sorted(values & culture)

    if matches:
        reasons.append(f"重視する価値観と近い: {', '.join(matches)}")
    elif values:
        concerns.append("重視する価値観との一致が明確ではない")


def _check_avoid_conditions(
    profile: dict[str, Any], company: dict[str, Any], concerns: list[str]
) -> None:
    """候補者が避けたい条件に企業が近くないかを見る。"""
    avoid_conditions = profile.get("avoid_conditions", [])
    # 企業の複数項目をまとめて検索し、受託・残業・原則出社などのNG条件を検出する。
    searchable_text = " ".join(
        [
            company.get("industry", ""),
            company.get("remote_policy", ""),
            company.get("workload_notes", ""),
            " ".join(company.get("culture", [])),
            company.get("hiring_notes", ""),
        ]
    )

    for condition in avoid_conditions:
        if condition == "受託開発中心" and "受託" in searchable_text:
            concerns.append("避けたい条件に近い: 受託開発中心")
        if condition == "残業が多い" and "残業が多い" in searchable_text:
            concerns.append("避けたい条件に近い: 残業が多い")
        if condition == "原則出社" and "原則出社" in searchable_text:
            concerns.append("避けたい条件に近い: 原則出社")


def _decide_label(reasons: list[str], concerns: list[str]) -> str:
    # 強い懸念がある企業は、理由があっても上位扱いにしない。
    hard_concerns = [
        concern
        for concern in concerns
        if concern.startswith("避けたい条件")
        or concern.startswith("希望勤務地と異なる")
        or concern.startswith("希望年収に届かない")
        or concern.startswith("希望職種と募集職種")
    ]

    if hard_concerns:
        return "現時点ではマッチが弱い"
    if len(reasons) >= 5 and not concerns:
        return "マッチ度が高い"
    if len(reasons) >= 4 and len(concerns) <= 1:
        return "マッチ度が高い"
    if len(reasons) >= 3:
        return "マッチしている"
    return "条件確認が必要"


def _sort_key(result: SelectionResult) -> tuple[int, int]:
    """選出区分が強い企業、懸念点が少ない企業の順に並べる。"""
    label_order = {
        "マッチ度が高い": 0,
        "マッチしている": 1,
        "条件確認が必要": 2,
        "現時点ではマッチが弱い": 3,
    }
    return (
        label_order.get(result["selection_label"], 99),
        len(result["concerns"]),
    )


def _parse_salary_floor(value: str | None) -> int | None:
    """「700万円以上」のような希望年収から、比較用の数値だけ取り出す。"""
    if not value:
        return None

    match = re.search(r"(\d+)万円以上", value)
    return int(match.group(1)) if match else None


def _parse_salary_range(value: str) -> tuple[int | None, int | None]:
    """「650万円-900万円」のような年収レンジから、下限と上限を取り出す。"""
    match = re.search(r"(\d+)万円-(\d+)万円", value)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))
