# カスタムサブエージェントとモデルの振り分け

このフォルダには、実際に読み込むプロジェクト設定 [.codex/config.toml](../.codex/config.toml) と、役割ごとの [.codex/agents/](../.codex/agents/) の TOML 定義を含める。主担当のモデルは固定せず、ユーザーの選択を維持する。限定した抽出・照合は `gpt-6-luna`、指示解釈・分解・設計・執筆・証明は `gpt-6.1-sol`、証明の難所は `gpt-6-astra` を使う。指示解釈とタスク分解の reasoning effort は `medium`、Astra の証明役は `xhigh`、他の同梱役は `high` とする。

設定形式は 2026-10-10 に再確認した [OpenAI 公式の Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) に基づく。現行のローカル Codex は `.codex/agents/` の独立した TOML をカスタム定義として扱い、`name`、`description`、`developer_instructions` を必要とする。本スターターでは各ファイルにモデル・推論強度・sandbox も明示する。

互換性のため、`config.toml` にも `[agents.<role>]` の `description` と
`config_file = "agents/<role>.toml"` を登録してある。内容の正本は各役のTOMLで、
プロジェクト設定には説明と参照先だけを置く。相対パスは宣言元の設定を基準にする。
[公式 Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference#configtoml)

## 通常の依頼から起動する

まず [指示の合議・タスク分解・証明の引継ぎ](../rules/agent-orchestration.md) に従う。Luna が主担当なら、新しいユーザーの作業指示や途中の訂正ごとに `intent_interpreter` と目的・範囲・完了条件を照合する。索引更新や誤字修正も短く照合するが、全体設計や全役レビューは起動しない。停止・権限撤回は合議を待たず直ちに守る。

合議後は依頼の対象とリスクを読み取り、該当するスキルを選ぶ。論文の仕事では [paper-writing スキル](../.agents/skills/paper-writing/SKILL.md) と [review-loop.md](../rules/review-loop.md) に従い、保守・索引・申請書を論文制作へ広げない。利用者が毎回役割名を指定する必要はない。明示的な単独作業の指定は優先し、挨拶・進捗だけの質問・内部報告は必須合議を起動しない。

| 依頼・観測されたリスク | 起動する役 | モデル | 入出力・報告上の区分 |
| --- | --- | --- | --- |
| Luna が新しい作業指示・途中の訂正を受ける | [intent_interpreter](../.codex/agents/intent_interpreter.toml) | Sol / medium | 指示原文と既存制約から目的・範囲・完了条件を返す。承認・独立レビューではない |
| 複数依存や難所により実行順が不明、方針が実質的に変わる | [task_decomposer](../.codex/agents/task_decomposer.toml) | Sol / medium | 通常二〜四件の実行可能な割当。明確な単純作業では省略 |
| 指定した命題の証明構成、既存の穴の修復、反例探索 | [prover](../.codex/agents/prover.toml) | Sol / high | 読み取り専用の証明報告。作成側であり独立査読ではない |
| Sol が残した具体的な証明の難所、中核の衝突、明示された難問 | [prover_astra](../.codex/agents/prover_astra.toml) | Astra / xhigh | 主担当が引継ぎ票を渡す。元の定理を維持し、導出・反例・残る穴を返す |
| ファイル、記号、引用、規則候補の一覧が必要 | [inventory](../.codex/agents/inventory.toml) | Luna | 所在と範囲を抽出。独立レビューの合格には数えない |
| 新規論文、大幅改稿、節順の設計、採用指摘を修正計画へまとめる | [designer](../.codex/agents/designer.toml) | Sol | Spec。自分の設計を独立 Audit しない |
| 確定した設計・修正束を原稿へ反映、翻訳 | [writer](../.codex/agents/writer.toml) | Sol | Generate。通常の原稿編集権限を持つ唯一のサブエージェント |
| 新規・変更された結論、証明、分析、専門的な解釈 | [correctness_reviewer](../.codex/agents/correctness_reviewer.toml) | Sol | `correctness` |
| 主述、指示語、定義、量化、推論、段落の論拠 | [argument_reviewer](../.codex/agents/argument_reviewer.toml) | Sol | `argument` |
| 引用が主張を支えるか、帰属・新規性の判断 | [source_reviewer](../.codex/agents/source_reviewer.toml) | Sol | `sources` |
| 引用キー、書誌情報、版・資料同一性、配布物の照合 | [bibliography_reviewer](../.codex/agents/bibliography_reviewer.toml) | Luna | `bibliography` |
| 節の依存、導入、圧縮、媒体に合う情報配置 | [structure_reviewer](../.codex/agents/structure_reviewer.toml) | Sol | `structure`。設計者とは別の新しい担当 |
| 意味・範囲を保つ文章改稿の差分比較（比較基準が固定済み） | [comparative_prose_reviewer](../.codex/agents/comparative_prose_reviewer.toml) | Luna | `structure` の補助報告。改稿前版と現行版を比較し、初読や正確性の確認には数えない |
| 原稿を初めて読む読者の理解を観測 | [blind_reader](../.codex/agents/blind_reader.toml) | Luna | `reader`。専門性の保証には使わない |
| 難しい読解、必要な修正後も残る読書障害の再確認 | [blind_reader_sol](../.codex/agents/blind_reader_sol.toml) | Sol | `reader`。履歴を継承しない新しい初読者 |
| 生成済み PDF・HTML 等の表示・組版確認 | [render_reviewer](../.codex/agents/render_reviewer.toml) | Luna | `render`。実際に表示を見た範囲だけ報告 |
| 学部水準の講義ノートの前提知識・理解の観測 | [undergraduate_reader](../.codex/agents/undergraduate_reader.toml) | Luna | 通常の初読者枠を置換。概念を使う前の橋渡しを観測 |
| 履歴書・申請書の項目抽出や質問候補 | [application_interviewer](../.codex/agents/application_interviewer.toml) | Luna | 裏方の読み取り役。主担当が同じ会話で通常一問を聞く |
| 履歴書・申請書の事実・要件の確認 | [application_reviewer](../.codex/agents/application_reviewer.toml) | Luna | 原稿制作から独立した限定チェック。資格や内容の曖昧さはSolへ |
| 現行版の人間による最終通読 | 人間の担当者 | 対象外 | `human`。AI の定義を作らず、AI の報告で代用しない |

`Luna` は `gpt-6-luna`、`Sol` は `gpt-6.1-sol`、`Astra` は `gpt-6-astra` の略記。表で推論強度を省略した既存役は全て `high`。論文の報告区分は [tools/paper.py](../tools/paper.py) の役割名に対応する。指示解釈・分解・証明の四役と申請書の二役は論文の最終確認人数に数えず、新しいレビュー区分も作らない。モデル名、役割名、実行ごとの `reviewer_id` は別物である。同じ役割でも各独立実行には別の ID を付け、設計・証明の構成・執筆に参加した ID を記録する。初読者と情報を持つ専門監査者を同一実行で兼任させない。

この表は分野横断で再利用する役割のカタログであり、全分野の専門家が同梱されているという意味ではない。変更した結論・証明・分析に必要な専門性が一般の `correctness_reviewer` の範囲を超える場合、プロジェクト契約で必要な専門家・独立担当・根拠を特定し、必要なら専用の役割定義を追加する。適任者を確保できない場合は、一般レビューで代用せず `INDEPENDENT_CHECKS_INCOMPLETE` として未確認範囲を残す。役割数の多さ自体を品質指標にしない。

`comparative_prose_reviewer` は改稿前の固定基準版があり、主張・根拠・範囲を変えない文章改善を問う場合だけ使う。基準版と現行版の差から読者向けの具体的な利得が示せなければ基準版を維持する。主張、証明、解釈、引用支持、または分野慣行を変える差分は比較評価の対象外として、該当する独立役へ回す。これは任意の補助確認であり、通常の構造監査や初読を置き換えない。

## 起動予算と引継ぎ

設定上の上限は主担当を除く同時 3 スレッドである。一ラウンドのレビュー人数や総ラウンド数の上限ではない。L0–L3 のリスク別予算は [review-loop.md](../rules/review-loop.md) を使い、必要な担当が 3 人を超える場合は独立した組に分ける。設計、執筆、修正後の検査のような依存する工程を並列にしない。

主担当は対象版、範囲、必要な入力、制約、返す報告を明示する。専門監査には対象資料と必要な規則を渡せる。原稿の結論を追認させる指示は渡さない。報告の採否、記録、修正束の作成、ビルド、完了判断は主担当が行う。葉の担当はさらにエージェントを起動せず、Git 操作や外部送信を行わない。レビュー担当は原稿・台帳を編集せず、観測を返し、主担当が保存する。

指示解釈・分解・証明も同じ三枠を使う。証明の通常の同時割当は二つまで、
うち Astra は一つまで。Sol がエスカレーション報告を返したら、主担当が
`prover_astra` を新しい履歴で起動する。依存関係のない別の補題は並行して解ける。
難所・引継ぎ票・進展のない反復の扱いは [証明の運用](../rules/agent-orchestration.md)
を正本とし、ここで別の失敗回数や承認条件を追加しない。

Luna が用語の意味、資料同一性、適用条件、因果、引用支持などを決められない場合は、該当する Sol 役へ範囲を絞って引き継ぐ。これは通常の経路であり、毎回の利用者承認を追加しない。難しい読みは最初から `blind_reader_sol` を選んでよい。修正後も同じ読書障害が残る場合は、設計を再検討したうえで新しい Sol 読者を使う。Luna の不合格を消すため、未変更の原稿を合格するまで読み直させてはならない。

## 初読者の隔離

本文やファイルの場所を渡す前に、新しい役の実行へ中立な読者属性だけを示し、
制作ルーティング・目標・履歴・別の原稿が既に注入されていないかを確認する。
その応答は読解checkpointとは別に保存する。漏洩が観測された実行へ本文を
渡して盲検読者と扱わない。ただし「見えていない」という自己申告も隔離の証明では
ない。利用できる実行診断を確認し、後で判明した漏洩は過去の判定にも反映する。

二つの `blind_reader` と `undergraduate_reader` は、リポジトリ規則・スキル・設計への読み込みを指示しない。主担当が新しい履歴のない実行を作り、中立な読者属性と、凍結した原稿の最初のまとまりだけを渡す。読み手の報告を保存してから次のまとまりを渡す。ファイルの場所を知らせる場合も、読める行・ページの範囲を明示し、全文を先に読み込ませない。

[blind-referee](../.agents/skills/blind-referee/SKILL.md) は明示実行の報告専用入口。
通常の執筆は同じ [凍結・ループの補助](../tools/blind-review/READER_LOOP.md) を
必要時に自動利用する。`undergraduate_reader` は
[講義用 overlay](../.agents/skills/undergraduate-lecture/SKILL.md) で通常の初読者を置き換える。
別の追加パネルではない。ループの観測JSONは論文全体の最終報告と同一形式ではなく、
`paper.py readiness` の全役・人間・最終版の確認を飛ばす証拠にはならない。

[application-interview](../.agents/skills/application-interview/SKILL.md) の担当は
本人への質問を代行せず、限定した候補や確認結果を返す。本文の大幅編集は同じ
`writer` の申請書モードへ渡す。論文用の設計・引用契約を自動適用しない。

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

特に `prover` は Sol/high を固定しているため、この役に Astra の spawn 値を
添えるだけでは切替にならない。名前付き起動では **`prover_astra` を選ぶ**。
こちらの定義は Astra/xhigh を固定している。通常の役を実行中に書き換えて
共有設定を切り替える必要はない。`intent_interpreter` は Luna を支援する
Sol/medium の役であり、合議役自身を Luna で起動しない。

Astra の `xhigh` は、2026-10-10 の汎用起動確認で `high` が
`unsupported_value`（受理する値は `xhigh`）として拒否されたことに対応する。
この観測を全てのクライアントの利用権・対応強度の保証には広げない。
環境が要求値を拒否したらエラーを残し、実際に受理される設定を確認する。

同日の汎用起動では、Sol/medium の指示解釈役と、修正後の Astra/xhigh の証明役から
応答を回収した。前者は合成した範囲縮小の指示、後者は小さな証明の引継ぎ票で
確認したもので、難問での性能評価ではない。指定値と応答取得は確認したが、
実モデル・推論強度の独立したメタデータと native の役割自動読込は未確認である。

汎用 spawn しか公開されていない環境では、主担当が対応 TOML を読み、`developer_instructions` の内容を役割依頼へ渡し、モデルと推論強度を実際のツール引数に指定する。例えば、この形式のツールでは次の値を使う。これは引数の例であり、環境に存在しない API を仮定して実行しない。

```json
{
  "task_name": "intent_01",
  "fork_turns": "none",
  "model": "gpt-6.1-sol",
  "reasoning_effort": "medium",
  "message": "intent_interpreter.toml の developer_instructions 全文と、ユーザー指示原文・既存制約・対象版・返す報告をここに渡す"
}
```

証明の引継ぎでは、元の役の会話を継続せず、次のように新しい担当へ渡す。
同じ形式で通常の証明を起動するときは `prover.toml` と Sol/high を選ぶ。

```json
{
  "task_name": "proof_gap_astra_01",
  "fork_turns": "none",
  "model": "gpt-6-astra",
  "reasoning_effort": "xhigh",
  "message": "prover_astra.toml の developer_instructions 全文と、運用規則に従う命題・仮定・基準版・確定部分・失敗した方法・今回の一点・成功条件をここに渡す"
}
```

この汎用経路では TOML の sandbox 設定が自動適用されるとは限らない。利用できる権限制御を確認し、少なくともレビュー担当へ読み取り専用の指示を渡す。ローカル Codex でも親セッションの実行時権限がカスタム設定に優先する場合があるため、`sandbox_mode` の記述だけで強制隔離されたとは報告しない。[権限の継承](https://learn.chatgpt.com/docs/agent-configuration/subagents#approvals-and-sandbox-controls)

最初の利用時と設定変更後は、次を区別して記録する。

1. **静的確認:** TOML が読め、必須キー・名前・モデル・推論強度・権限が予定通りである。
2. **設定の発見:** クライアントが実際に当該プロジェクトとカスタム役を読み込んだことを、利用できる設定診断・役割一覧で確かめる。
3. **起動時の指定:** 選択した定義または実際の spawn 引数、実行 ID を残す。
4. **実行時の観測:** メタデータやクライアントの表示で実モデル・推論強度・権限を確認する。担当の自己紹介は証拠にしない。観測できなければ「要求値のみ確認、実行時設定は未確認」と残す。

設定ファイルの追加や構文検査だけでは、現在のセッションへの再読み込み、モデル利用権、実際の起動は検証できない。モデルまたはカスタム役が使えない場合は、その失敗と未実施の確認を明示する。別モデルへ黙って差し替えたり、主担当の自己点検を独立確認に数えたりしない。指定されたモデルで可能な作業を続け、残る独立確認は `INDEPENDENT_CHECKS_INCOMPLETE` とする。代替モデルの利用が既に許可されていれば実際の値を記録して使い、指定モデルで実行したとは記さない。
