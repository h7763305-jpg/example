# Career Matching Assistant

面談内容から、それにマッチする企業を選出するためのMVPです。

## Current MVP

現時点では外部企業データベースや音声入力は使わず、サンプル面談テキストとサンプル企業DBで最小動作を確認します。

```txt
面談テキスト
-> 転職者プロフィール整理
-> サンプル企業DBと照合
-> マッチする企業候補を選出
```

## Run

標準のサンプルを実行します。

```bash
python3 scripts/run_mvp.py
```

面談ファイルを指定して実行します。

```bash
python3 scripts/run_mvp.py --interview data/sample/interview_frontend.txt
```

結果をファイルに保存します。

```bash
python3 scripts/run_mvp.py --output outputs/result.txt
```

出力内容:

- 面談要約
- 転職者プロフィール
- 選出企業
- 選出区分
- 選出理由
- 懸念点
- 追加確認すべき質問

## Web

入力内容に合わせてマッチする企業を検索する静的Web画面を起動します。

```bash
python3 -m http.server 4173
```

ブラウザで以下を開きます。

```txt
http://127.0.0.1:4173/web/index.html
```

## Selection Labels

- マッチ度が高い
- マッチしている
- 条件確認が必要
- 現時点ではマッチが弱い
