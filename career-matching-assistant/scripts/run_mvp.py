from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Pythonのコード説明:
# - import は、別ファイルや標準ライブラリの機能をこのファイルで使えるようにする。
# - def は、あとで呼び出せる処理のまとまり「関数」を作るための書き方。
# - return は、関数の処理結果を呼び出し元へ返すための書き方。
# - for は、リストの中身を1つずつ取り出して同じ処理を繰り返すための書き方。
# - dict は {"summary": ...} のような、項目名と値をセットで持つデータ。


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.analysis.profile_extractor import (  # noqa: E402
    build_summary,
    extract_candidate_profile,
)
from app.core.matching.company_matcher import select_companies  # noqa: E402


# 何も指定されなかった場合に使う、標準の面談テキストと企業データ。
DEFAULT_INTERVIEW = ROOT / "data/sample/interview.txt"
DEFAULT_COMPANIES = ROOT / "data/sample/companies.json"


def main() -> None:
    """MVP全体の流れを実行する入口。

    1. 面談テキストを読む
    2. 企業データを読む
    3. 面談内容から転職者プロフィールを整理する
    4. 企業データと照合して企業候補を選出する
    5. 人が読みやすいレポートとして表示・保存する
    """
    args = _parse_args()
    interview_path = _resolve_path(args.interview)
    companies_path = _resolve_path(args.companies)

    # 入力ファイルを読み込む。面談はテキスト、企業データはJSON形式で扱う。
    interview_text = interview_path.read_text(encoding="utf-8")
    companies = json.loads(companies_path.read_text(encoding="utf-8"))

    # 面談文章をそのまま企業と比べるのではなく、先に比較しやすいプロフィールへ整理する。
    profile = extract_candidate_profile(interview_text)
    result = {
        "summary": build_summary(interview_text),
        "candidate_profile": profile.to_dict(),
        "selected_companies": select_companies(profile.to_dict(), companies),
    }

    report = _format_report(result, interview_path, companies_path)
    print(report)

    if args.output:
        output_path = _resolve_path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report + "\n", encoding="utf-8")
        print(f"\n保存先: {output_path}")


def _parse_args() -> argparse.Namespace:
    """実行時に指定できる入力・出力ファイルを受け取る。"""
    parser = argparse.ArgumentParser(
        description="面談テキストと企業データを照合し、マッチする企業候補を選出します。"
    )
    parser.add_argument(
        "--interview",
        default=str(DEFAULT_INTERVIEW),
        help="面談テキストファイルのパス",
    )
    parser.add_argument(
        "--companies",
        default=str(DEFAULT_COMPANIES),
        help="企業データJSONファイルのパス",
    )
    parser.add_argument(
        "--output",
        help="レポートを保存するパス。指定しない場合はターミナル表示のみ。",
    )
    return parser.parse_args()


def _resolve_path(path_text: str) -> Path:
    """相対パスで指定されたファイルを、プロジェクト直下からのパスとして解釈する。"""
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def _format_report(
    result: dict[str, Any], interview_path: Path, companies_path: Path
) -> str:
    """プログラム内部の辞書データを、アドバイザーが読みやすい文章形式に変換する。"""
    profile = result["candidate_profile"]
    selected_companies = result["selected_companies"]
    lines = [
        "============================================================",
        "企業選出レポート",
        "============================================================",
        "",
        f"面談ファイル: {interview_path}",
        f"企業データ: {companies_path}",
        "",
        "【面談要約】",
        result["summary"] or "要約できる情報がありません。",
        "",
        "【転職者プロフィール】",
        f"現職・職種: {_value_or_dash(profile.get('current_role'))}",
        f"スキル: {_join_or_dash(profile.get('skills', []))}",
        f"希望職種: {_join_or_dash(profile.get('preferred_roles', []))}",
        f"希望業界: {_join_or_dash(profile.get('preferred_industries', []))}",
        f"希望勤務地: {_value_or_dash(profile.get('preferred_location'))}",
        f"リモート希望: {_value_or_dash(profile.get('remote_preference'))}",
        f"希望年収: {_value_or_dash(profile.get('salary_expectation'))}",
        f"キャリア志向: {_join_or_dash(profile.get('career_goals', []))}",
        f"避けたい条件: {_join_or_dash(profile.get('avoid_conditions', []))}",
        f"重視する価値観: {_join_or_dash(profile.get('important_values', []))}",
        "",
        "【選出企業】",
    ]

    # 選出結果は、理由・懸念点・追加質問を分けて確認できる形に整える。
    for index, company in enumerate(selected_companies, start=1):
        lines.extend(
            [
                "",
                f"{index}. {company['company_name']}",
                f"選出区分: {company['selection_label']}",
                "選出理由:",
                *_format_list(company["selection_reasons"]),
                "懸念点:",
                *_format_list(company["concerns"]),
                "追加確認すべき質問:",
                *_format_list(company["follow_up_questions"]),
            ]
        )

    return "\n".join(lines)


def _format_list(values: list[str]) -> list[str]:
    if not values:
        return ["- なし"]
    return [f"- {value}" for value in values]


def _join_or_dash(values: list[str]) -> str:
    return ", ".join(values) if values else "-"


def _value_or_dash(value: str | None) -> str:
    return value if value else "-"


if __name__ == "__main__":
    main()

