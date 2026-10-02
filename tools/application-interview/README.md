# 対話型の履歴書・申請書作成

「履歴書を作りたい」「科研費の申請書を手伝って」「前の申請書の続きを進めたい」
という通常の依頼から、同じ会話で作成・編集・再開する。質問は原則一つ、最大三つ。
短い回答もその場で下書きに反映する。常駐プロセスや追加 API キーは不要。
一般的な制度の質問やこの機能の保守では、本人情報の聞き取りを開始しない。
詳細は [スキル](../../.agents/skills/application-interview/SKILL.md)、担当の設定は
[モデルの振り分け](../../docs/agents.md) を参照。

## 保存と CLI

Python 3.11 以降、標準ライブラリのみ。通常はエージェントが実行する。

```sh
python3 -B tools/application-interview/session.py init cv-academic --kind cv
python3 -B tools/application-interview/session.py init grant-draft --kind grant
python3 -B tools/application-interview/session.py status cv-academic
python3 -B tools/application-interview/session.py check cv-academic
python3 -B tools/application-interview/session.py check cv-academic --complete
```

Windows では必要に応じて `py -3` を使う。任意の作業ディレクトリから実行でき、
保存先はスクリプトを配置したリポジトリの `.application-local/<slug>/`。
`--root PATH` をサブコマンドの前に渡すと、明示した既存ディレクトリを保存先にできる。
`kind` は `cv / grant / other`。`init` は同じ kind の有効なセッションを再開し、
既存ファイルを上書きしない。同じ kind でも別用途の書類には別 slug を使う。

```text
.application-local/<slug>/
  session.json   # 項目、根拠、未確認事項、次の質問
  draft.md       # 回答を反映した本文
```

原本・抽出テキスト・要件メモ・書き出したファイルも既定ではこのフォルダに置く。
指定された既存 Word/TeX 等があればそのファイルが対象であり、勝手に置き換えない。
この CLI は対話や Word/PDF 編集を行わない。会話と文章編集はエージェントが担う。

ルートの `.gitignore` と `init` が作る配下の `*` の ignore ガードで除外する。
ガードが変更されていたら個人情報を保存せず調査する。Git 除外は暗号化でも同期除外
でもなく、追跡済みファイルには効かない。提出、メール、commit/push は自動実行しない。

## チェックポイント

UTF-8 JSON、`schema_version = 1`。エージェントが本文と一緒に更新する。
`target` は `audience / purpose / fiscal_year / scheme / format / source_path /
output_path / deadline / institutional_deadline` の文字列を持つ。
`requirements` は `status / source / checked_at / note` を持ち、状態は
`unverified / verified / not_applicable`。`verified` には資料の所在と ISO 日付を、
`not_applicable` には理由を記録する。grant の完全性チェックは実際の年度・種目の
確認記録を要求するが、記録の真偽やその資料が最新かは CLI では確かめられない。

`fields` の各要素は `id / label / required / status / value / sources / note`。
`required` は真偽値、値は文字列、根拠は短い所在文字列の配列。初期項目は会話の
手がかりで、一律の必須欄や公式様式ではない。実際の要件から項目を追加・分割する。

| status | 意味 |
| --- | --- |
| `missing` | 未入力。記載なしを「無し」と推測しない |
| `candidate` | 資料からの候補、曖昧な回答、未採用の提案 |
| `confirmed` | 明確な回答または適切な資料で確認。値と根拠が必要 |
| `conflict` | 根拠が矛盾し未解決 |
| `deferred` | 後回し。既知の部分を保ち、同じ問いを繰り返さない |
| `not_applicable` | 非該当。理由と根拠または本人の判断が必要 |

独立して不確かな事実は別 ID にする。投稿中・受理済み・掲載済み、予定・現職、
年だけ判明・月日まで判明を混同しない。根拠には `user:日付:回答の箇所`、
`file:パス@版:節`、`official:URL:見出し:checked 日付` など短い所在を使う。

`pending_questions` は `field_ids` と `question` の最大三件の配列。用途確認など、
個別欄に対応しない質問の `field_ids` は空でもよい。回答した質問を取り除き、
次の質問を保存してからユーザーに聞く。`round` は回答を取り込んだ回数、`notes` は
短い引継ぎ情報。全文の会話を保存しない。`phase` は
`interviewing / drafting / review / paused / ready_for_user`。

「今日はここまで」では `paused` と再開メモを保存する。「続き」では両ファイルを
読み、回答済み・保留済みの質問を繰り返さない。「一旦見せて」や質問不要の指示では
未完成の下書きを渡せる。`ready_for_user` は本人確認用の手渡しで、提出済みや要件
適合を意味しない。部分的な下書きなら未確認事項と未達のチェックを明記する。

`check` は構造、ID、状態、根拠の所在記録と両保存ファイルの存在を調べる。
`--complete` は必須欄、保留中の質問、値を伴う未確認事項、要件の確認状態も調べる。
根拠の正しさ、要件の網羅、本文との一致、字数・ページ・表示、資格や提出可能性は
保証しない。実資料との照合と最終的な本人の内容確認が別に必要。

破損した JSON や不足ファイルは初期化し直さず保全する。ファイルは排他的に新規
作成するが、フォルダ全体のトランザクションや任意の同時編集のロックではない。
同じファイルを複数の担当で編集しない。

## 検証

```sh
python3 -B -m unittest discover -s tools/tests -p 'test_application_session.py' -v
python3 tools/paper.py check
```

テストは一時ディレクトリと架空データを使う。起動・保存・復帰、破損とパス逸脱の
拒否、未確認情報や要件による完了チェックの失敗を検査する。静的成功は実モデルの
起動や対話品質の測定ではない。自然な開始、短い回答の即時反映、保留後の再開、
曖昧な年月や投稿状態の保持、様式への対応は実際の会話でも別に確かめる。
