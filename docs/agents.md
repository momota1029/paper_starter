# カスタムサブエージェントとモデルの振り分け

このフォルダには、実際に読み込むプロジェクト設定 [.codex/config.toml](../.codex/config.toml) と、役割ごとの [.codex/agents/](../.codex/agents/) の TOML 定義を含める。主担当のモデルは固定せず、ユーザーの選択を維持する。サブエージェントでは、限定した抽出・照合に `gpt-6-luna`、設計・執筆・論証の判断に `gpt-6.1-sol` を使い、どちらも reasoning effort を `high` に指定する。

設定形式は 2026-10-02 に確認した [OpenAI 公式の Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) に基づく。現行のローカル Codex は `.codex/agents/` の独立した TOML をカスタム定義として扱い、`name`、`description`、`developer_instructions` を必要とする。本スターターでは各ファイルにモデル・推論強度・sandbox も明示する。

互換性のため、`config.toml` にも `[agents.<role>]` の `description` と
`config_file = "agents/<role>.toml"` を登録してある。内容の正本は各役のTOMLで、
プロジェクト設定には説明と参照先だけを置く。相対パスは宣言元の設定を基準にする。
[公式 Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference#configtoml)

## 通常の依頼から起動する

主担当は依頼の対象とリスクを読み取り、[paper-writing スキル](../.agents/skills/paper-writing/SKILL.md) と [review-loop.md](../rules/review-loop.md) に従って必要な役だけを選ぶ。利用者が毎回「Luna を呼ぶ」「構造監査を行う」と指定する必要はない。明示的な単独作業の指定は優先する。通常の質問、索引更新、誤字だけの変更で全役を起動しない。

| 依頼・観測されたリスク | 起動する役 | モデル | 入出力・報告上の区分 |
| --- | --- | --- | --- |
| ファイル、記号、引用、規則候補の一覧が必要 | [inventory](../.codex/agents/inventory.toml) | Luna | 所在と範囲を抽出。独立レビューの合格には数えない |
| 新規論文、大幅改稿、節順の設計、採用指摘を修正計画へまとめる | [designer](../.codex/agents/designer.toml) | Sol | Spec。自分の設計を独立 Audit しない |
| 確定した設計・修正束を原稿へ反映、翻訳 | [writer](../.codex/agents/writer.toml) | Sol | Generate。通常の原稿編集権限を持つ唯一のサブエージェント |
| 新規・変更された結論、証明、分析、専門的な解釈 | [correctness_reviewer](../.codex/agents/correctness_reviewer.toml) | Sol | `correctness` |
| 主述、指示語、定義、量化、推論、段落の論拠 | [argument_reviewer](../.codex/agents/argument_reviewer.toml) | Sol | `argument` |
| 引用が主張を支えるか、帰属・新規性の判断 | [source_reviewer](../.codex/agents/source_reviewer.toml) | Sol | `sources` |
| 引用キー、書誌情報、版・資料同一性、配布物の照合 | [bibliography_reviewer](../.codex/agents/bibliography_reviewer.toml) | Luna | `bibliography` |
| 節の依存、導入、圧縮、媒体に合う情報配置 | [structure_reviewer](../.codex/agents/structure_reviewer.toml) | Sol | `structure`。設計者とは別の新しい担当 |
| 原稿を初めて読む読者の理解を観測 | [blind_reader](../.codex/agents/blind_reader.toml) | Luna | `reader`。専門性の保証には使わない |
| 難しい読解、必要な修正後も残る読書障害の再確認 | [blind_reader_sol](../.codex/agents/blind_reader_sol.toml) | Sol | `reader`。履歴を継承しない新しい初読者 |
| 生成済み PDF・HTML 等の表示・組版確認 | [render_reviewer](../.codex/agents/render_reviewer.toml) | Luna | `render`。実際に表示を見た範囲だけ報告 |
| 現行版の人間による最終通読 | 人間の担当者 | 対象外 | `human`。AI の定義を作らず、AI の報告で代用しない |

`Luna` は `gpt-6-luna`、`Sol` は `gpt-6.1-sol` の略記。表の報告区分は [tools/paper.py](../tools/paper.py) の役割名に対応する。モデル名、役割名、実行ごとの `reviewer_id` は別物である。同じ役割でも各独立実行には別の ID を付け、設計・執筆に参加した ID を記録する。初読者と情報を持つ専門監査者を同一実行で兼任させない。

## 起動予算と引継ぎ

設定上の上限は主担当を除く同時 3 スレッドである。一ラウンドのレビュー人数や総ラウンド数の上限ではない。L0–L3 のリスク別予算は [review-loop.md](../rules/review-loop.md) を使い、必要な担当が 3 人を超える場合は独立した組に分ける。設計、執筆、修正後の検査のような依存する工程を並列にしない。

主担当は対象版、範囲、必要な入力、制約、返す報告を明示する。専門監査には対象資料と必要な規則を渡せる。原稿の結論を追認させる指示は渡さない。報告の採否、記録、修正束の作成、ビルド、完了判断は主担当が行う。葉の担当はさらにエージェントを起動せず、Git 操作や外部送信を行わない。レビュー担当は原稿・台帳を編集せず、観測を返し、主担当が保存する。

Luna が用語の意味、資料同一性、適用条件、因果、引用支持などを決められない場合は、該当する Sol 役へ範囲を絞って引き継ぐ。これは通常の経路であり、毎回の利用者承認を追加しない。難しい読みは最初から `blind_reader_sol` を選んでよい。修正後も同じ読書障害が残る場合は、設計を再検討したうえで新しい Sol 読者を使う。Luna の不合格を消すため、未変更の原稿を合格するまで読み直させてはならない。

## 初読者の隔離

二つの `blind_reader` 定義だけは、リポジトリ規則・スキル・設計への読み込みを指示しない。主担当が新しい履歴のない実行を作り、中立な読者属性と、凍結した原稿の最初のまとまりだけを渡す。読み手の報告を保存してから次のまとまりを渡す。ファイルの場所を知らせる場合も、読める行・ページの範囲を明示し、全文を先に読み込ませない。

読者目標、期待回答、`AGENTS.md` の制作ルーティング、設計、差分、過去の読者報告、モデルを切り替えた理由は渡さない。Sol へ切り替える場合も、Luna の会話を継続しない。報告は意味の理解、本文の根拠、最初の混乱、後の回復、未読範囲の観測であり、修正文や内的思考の記録ではない。

ランタイムが自動注入した規則や履歴を含め、隔離できない情報が先に見えていたら `ISOLATION_FAILED` を記録する。「無視した」と説明しても初読の独立性は復元しない。汚染されていない別の環境で断片を渡すか、独立の人間に読んでもらう。代替が使えなければ、他の許可された作業を進め、初読確認を未完了として残す。

テキストには [補助CLIによる前方読み](reader-runner.md) も使える。Luna/Sol を
実引数で指定し、本文前の診断点検、順次提示、元ログの保存を行う。
native起動と同一の手法とは扱わず、完全隔離や理解の自動認定は行わない。

## 読み込み、モデル指定、実行の確認

プロジェクト設定は、そのフォルダを信頼したローカル環境で読み込まれる。
最初に開く際は設定内容を読み、クライアントの通常のプロジェクト信頼の手順を使う。
スターターが利用者のグローバル設定や信頼状態を自動変更することはない。
未信頼で無効になった設定と、構文誤りやモデル利用不可を区別する。
[プロジェクト設定の条件](https://learn.chatgpt.com/docs/config-file/config-reference#configtoml)

公式仕様では、カスタム定義に明記した `model` と `model_reasoning_effort` が優先される。ファイル適用前の設定は、明示的な spawn 値、`[agents]` の既定、親の値の順に解決される。したがって、名前付き定義を選べるクライアントでは、表の役割名を実際の起動先に指定する。モデル名を依頼本文へ書くだけで、選択が行われたとは扱わない。[設定の優先関係](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents)

汎用 spawn しか公開されていない環境では、主担当が対応 TOML を読み、`developer_instructions` の内容を役割依頼へ渡し、モデルと推論強度を実際のツール引数に指定する。例えば、この形式のツールでは次の値を使う。これは引数の例であり、環境に存在しない API を仮定して実行しない。

```json
{
  "task_name": "argument_check_01",
  "fork_turns": "none",
  "model": "gpt-6.1-sol",
  "reasoning_effort": "high",
  "message": "対応する developer_instructions と、対象版・範囲・入力・返す報告をここに渡す"
}
```

この汎用経路では TOML の sandbox 設定が自動適用されるとは限らない。利用できる権限制御を確認し、少なくともレビュー担当へ読み取り専用の指示を渡す。ローカル Codex でも親セッションの実行時権限がカスタム設定に優先する場合があるため、`sandbox_mode` の記述だけで強制隔離されたとは報告しない。[権限の継承](https://learn.chatgpt.com/docs/agent-configuration/subagents#approvals-and-sandbox-controls)

最初の利用時と設定変更後は、次を区別して記録する。

1. **静的確認:** TOML が読め、必須キー・名前・モデル・推論強度・権限が予定通りである。
2. **設定の発見:** クライアントが実際に当該プロジェクトとカスタム役を読み込んだことを、利用できる設定診断・役割一覧で確かめる。
3. **起動時の指定:** 選択した定義または実際の spawn 引数、実行 ID を残す。
4. **実行時の観測:** メタデータやクライアントの表示で実モデル・推論強度・権限を確認する。担当の自己紹介は証拠にしない。観測できなければ「要求値のみ確認、実行時設定は未確認」と残す。

設定ファイルの追加や構文検査だけでは、現在のセッションへの再読み込み、モデル利用権、実際の起動は検証できない。モデルまたはカスタム役が使えない場合は、その失敗と未実施の確認を明示する。別モデルへ黙って差し替えたり、主担当の自己点検を独立確認に数えたりしない。指定されたモデルで可能な作業を続け、残る独立確認は `INDEPENDENT_CHECKS_INCOMPLETE` とする。代替モデルの利用が既に許可されていれば実際の値を記録して使い、指定モデルで実行したとは記さない。
