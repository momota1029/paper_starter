# 補助CLIによる前方読み

`tools/reader.py` は新しいCodex CLIセッションへ凍結済みのテキストを順に送る。
nativeな役割発見や初読者の自動隔離を検証する仕組みではない。
対象はUTF-8の `.md` / `.txt` のみ。TeX、PDF、HTMLは直接扱わない。
別にテキスト版を作る場合、表示版との対応は人または担当者が確認する。
CLIと認証は別途必要であり、実行時にはモデル利用が発生する。

自然な区切りを本文の行で事前に決め、リポジトリ相対パスのJSONに保存する。
例えば `{"ends": [20, 45, 60]}` は1–20行、21–45行、46–60行の順で渡す。
最後の数字は本文の最終行。採点目標、期待する答え、修正履歴は入れない。
読者属性はsnapshotの `reader` を使うので、中立な背景であることを点検する。

```bash
python3 tools/reader.py begin RUN --plan .paper-local/reader-plan.json
```

`begin` は空の一時ディレクトリで診断と本文を含まない実セッションの確認を行い、
ローカルのrun配下に `attempt` と `reviewed_preflight_sha256` を保存・表示する。
Luna/highが既定。必要なら `--model gpt-6.1-sol` を指定する。
要求した設定、実行ファイルのハッシュ、CLI版、コマンド、入力、標準出力・エラーを残す。
HOME、CODEX_HOME、グローバル設定を変更しない。セッション記録や認証には既存の
Codex環境を使うので、それらへの通常のCLI書き込みを防ぐものではない。

統合担当が `begin.json`、`diagnostic.events.jsonl`、`handshake.events.jsonl` を実際に読み、
背景・注入された指示・読者の申告を確認する。既知のプロジェクト指示、ツール使用、
不明な診断形式、不整合な申告は停止させる。未知の指示の意味は自動判定できない。
レビュー済みのファイルに対応する表示ハッシュを使って続ける。

```bash
python3 tools/reader.py continue ATTEMPT --reviewed-preflight SHA256 --reviewer REVIEWER_ID
```

本文は常にstdinから渡し、再開先は実セッションUUIDを明示する。
本文のパス、manifest、境界計画、設計、目標、他の報告は読者へ渡さない。
各区切りで対象・射程、条件・量化、主張、根拠・機序、限界、不確かさ、混乱と回復、
未読範囲を同じ中立な質問で記録する。最後の区切りで全文終了だけを伝える。
次の入力を作る前に前のチェックポイントを保存する。
入力・出力・イベントは上書きしない。失敗と中断を残し、自動再試行も同一attemptの
再実行も行わない。変更のない原稿の再採点で好結果を選ぶ用途には使わない。

成功時の `observations.json` は `process-checked`、`isolation: not-proven`、
`goal_adjudication: pending`。`pass` や `reader_goals_met` は生成しない。
独立した担当が、隠していた事前目標と観測を照合し、報告内の意味上の不整合も調べる。
その後、[作業コマンド](../tools/README.md)のreport記録へ根拠を引き継ぐ。
`paper.py readiness` の既存の全体条件をこのrunnerだけで閉じることはできない。

この経路の最終reportには `reader_transport: "supplementary-cli-text"` と、
リポジトリ相対の `reader_receipt`（当該 `observations.json`）を記す。
`record` がそのハッシュを保存し、`readiness` がreceiptと元ログ、実行ID、
チェックポイントの一致を検査する。チェックポイントの `at / location` は
元の値、`observation` は元の観測オブジェクトを
`json.dumps(value, ensure_ascii=False, indent=2) + "\n"` で文字列化した値にする。
好ましい部分だけを要約して置き換えない。
別欄 `isolation_review` には実際に点検した情報と残る隔離上の制約、
`goal_adjudication` には設計目標との照合記録の所在を記す。
これらも申告の真偽を自動判定するものではない。隔離を確認できなければ、
`isolation: "passed"` を代記せず、未完了のまま残す。

隔離の限界: `debug prompt-input` はこのCLI版では `--ignore-user-config` を使えず、
実際の `exec` と同じ設定層ではない。実 `exec` の初期確認も読者自身の申告である。
両方を保存して確認するが、同じプロンプトだったことや完全な情報隔離は証明しない。
[公式AGENTS説明](https://learn.chatgpt.com/docs/agent-configuration/agents-md)は指示の発見と
バイト上限を説明している。read-onlyは書き込み制限であり、他ファイルの読み取り隔離
ではない。ツールイベントを見つけた時点では、そのツールが既に動いている場合もある。
一時ディレクトリは再開用に残す。削除するなら `begin.json` の正確なパスを確認する。

合成テストは輸送と保存の失敗分岐を検査する。実モデル、読者の理解、人間の通読、
native隔離の成功、原型との同等性の証拠には数えない。
