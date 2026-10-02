# 作業コマンド

Python 3.11 以上。外部API、追加Pythonパッケージ、グローバルなインストールは不要。
以下はリポジトリ直下で実行する。別のコピーへ実行する場合はサブコマンドの前に
`--root /path/to/workspace` を置く。スクリプトの場所が既定のルートになる。

## 原稿と索引

```bash
python3 tools/paper.py new my-paper --title '題名' --profile theory --language ja
python3 tools/paper.py index
python3 tools/paper.py index --check
python3 tools/paper.py check
```

`new` は同名の研究を上書きしない。profile は
`theory / empirical / qualitative / review / mixed / custom`。
`--format tex` なら英語用の最小TeXひな型、既定はMarkdown。
`meta.toml` で正本、読者、執筆者ID等を管理する。
`quality-contract.md` は読者の知識境界・帰属方針・拘束条件への案内であり、
新規作成時は未設定である。`design.md / evidence.md / corpus.md` の実際の記録へ
結び、未設定を合格にしない。既存プロジェクトには
[契約ひな型](../templates/project/quality-contract.md)を追加して実情に合わせる。
`inputs` はプロジェクト外のデータ・コード・出典等へのリポジトリ相対パスの配列。
例は `inputs = ["refs/source/excerpt.txt"]`。外部依存は漏れなく宣言する。

`check` はローカルリンクのファイル到達性、規則の索引、設定、メタデータ、
主張記録、研究一覧の鮮度を検査する。リンクのアンカー・外部URL・原稿の意味は検査しない。
ひな型を作った直後の空の主張記録は `check` を通るが `readiness` は通らない。

主要主張の `claims.json` の例:

```json
{
  "claims": [
    {
      "id": "C1",
      "statement": "原稿で実際に主張する文と成立条件",
      "kind": "original",
      "status": "pending",
      "location": "原稿 §3",
      "evidence": "evidence.md の C1。未検証の箇所を明記する"
    }
  ]
}
```

kind は `original / cited / routine / unresolved`、status は
`pending / verified / contradicted`。形式の正しさと内容の真偽は別である。
原稿の主要な主張を漏れなく台帳へ対応づけるのは内容レビューの責務。

## ビルド

```bash
python3 tools/paper.py build my-paper
```

MarkdownにはPandoc、TeXにはlatexmkとLuaLaTeXが必要。
プロジェクトディレクトリを基準に実行する。画像やinputの相対パスもそこから解決する。
生成物は `output/<slug>/<slug>.html` または `.pdf`。
前回の成功出力があれば `archive/` に保存する。失敗で前の出力を上書きしない。
`build.json` に入力ハッシュと出力ハッシュを記録する。
目視は別作業。HTMLの数式表示にはMathJaxが使われるため、オフラインの
配布条件は別途確認する。投稿用パッケージの作成は自動化していない。

## 版を凍結する

```bash
python3 tools/paper.py snapshot my-paper --contributor designer-session --contributor editor-session
```

標準出力の `.paper-local/reviews/<slug>/<run>` を以後の `RUN` に代入する。
表示済みの成果物も読む場合は `--artifact output/my-paper/my-paper.pdf` 等を加える。
`writer_id` に加えて、設計・修正に参加した全ての担当を `--contributor` で記録する。
その担当のレビューは独立判定に数えられない。

```bash
python3 tools/paper.py verify RUN
python3 tools/paper.py packet RUN --role reader
```

凍結対象はプロジェクト内の入力（inbox・reviews・既知の補助ファイルを除く）、
宣言した `inputs` と存在する `index.bib`。必要な原典・データ・コードを
inputs に宣言しなかった場合、それらの変更は検出できない。
新しいファイルや削除も含め、現在の入力と凍結時の入力が違うと `verify` は失敗する。
履歴だけを調べる `verify RUN --frozen-only` は現行版の確認には使えない。
取得中に入力が変わった場合、未完成のrunを残して失敗する。新しいrunで再実行する。

reader packetには原稿の場所・中立な読者属性・前方読みの手順だけが入る。
**packetの出力後に、実際の新しい読者を起動する必要がある。**
TeXは先にレンダリングして渡す。全文を一度に読んだ後から初読を再現してはいけない。
ハッシュや read-only は情報隔離を保証しない。同じファイルシステムを使う場合も、
読者が隣接する設計・採点基準・報告を読まないよう入力範囲を制限する。

Markdown / UTF-8 テキストについては [順次読者の実行](../docs/reader-runner.md) を
使える。これは診断と初期応答の点検を挟む補助CLIで、nativeな初読の隔離を
保証するものではない。送信する本文は一片ずつで、採点目標や設計は送らない。

## 実際のレビューを記録する

[reportひな型](../templates/review.json)をローカルにコピーして、実際の報告を記録する。
`run_id` はmanifestのID、`reviewer_id` は実際の人またはセッションの識別子。
`evidence` は実際の観測・根拠を保存したテキストへのリポジトリ相対パス。
レビューをしていない欄を埋めてはいけない。

```bash
python3 tools/paper.py record RUN .paper-local/my-report.json
python3 tools/paper.py readiness RUN
```

role は `correctness / argument / sources / bibliography / structure / reader / render / human`。
kind は `ai / human`、verdict は `pending / pass / fail / blocked`。
`scope` に実際に読んだ範囲、`unread` に未読範囲の配列を記す。
`findings` は指摘の配列で、各指摘には位置・根拠・重要度を含める。
最終検査では各指摘の status が `closed / rejected / not-applicable` のいずれかで、
reason に閉鎖の証拠または判定の理由を持つ必要がある。
修正しただけの指摘は閉鎖済みにしない。

### 指摘なしでも必要な確認一覧

`argument / sources / structure` の最終報告は `coverage` も必要である。
一覧には監査範囲 `scope`、具体的な `items`、対象が本当にない場合だけ
`none_reason` を記す。一覧と該当なしを同時に宣言しない。

| role | coverage のキー | items 各要素の必須文字列 |
| --- | --- | --- |
| argument | external_inputs | input, definition, statement, application, source |
| sources | attribution | concept, first_use, attribution, policy, support |
| structure | constraints | id, strength, basis, checked_location, decision |

definition / statement / application は原稿の正確な位置と確認内容、source は
出典版・箇所、policy は適用した帰属位置の規則と根拠を書く。strength は
`hard / strong / weak`。decision は遵守・許可された逸脱・その根拠を区別する。
同一入力の複数の適用位置も確認し、問題なしという一語だけで代用しない。
例（実際の査読結果ではない）:

```json
{
  "coverage": {
    "external_inputs": {
      "scope": "原稿全文と、そこで利用した補題",
      "items": [{
        "input": "E1: 読者の既有知識外の補題",
        "definition": "§2第1段落: 対象とノルムを定義",
        "statement": "§2補題1: 仮定と結論を明記",
        "application": "§3第2段落: 各仮定への代入と得る評価を照合",
        "source": "実物を確認した資料の版・補題番号をここへ記す"
      }],
      "none_reason": ""
    }
  }
}
```

形式検査は空の一覧・必須欄の不足を拒否するだけで、網羅性・所在の真偽・
著者承認の有効性は判断しない。凍結した品質契約と本文による独立監査が必要。
`readiness` は品質契約の欠落と未設定マーカーも拒否するが、マーカーを消すだけで
契約が成立するわけではない。過去の報告をこの形式へ架空に補完しない。

readerでは `isolation = "passed"`、設計側で照合した `reader_goals_met = true`、
実際の読み順に作られた checkpoints が必要。チェックポイントは次の形:

```json
{"at": "2026-10-02T12:00:00+00:00", "location": "導入第1段落まで", "observation": "この時点で本文から読めた内容と最初の混乱。後続は未読。"}
```

目標と観測の照合結果は統合担当が保存する。読者へ目標を見せて埋めさせない。
時刻と申告が正しくても、実際の先読みの有無はツールだけでは証明できない。

`record` は報告と観測資料をrunへ追記して保存し、既存の報告を上書きしない。
誤検出の判定・修正・再確認の過去記録も残す。
現在のCLIは保守的な**全体最終検査専用**で、全8観点の記録、未読範囲なし、
独立した専門担当と初読者、実際の人間の通読を要求する。
一人の専門担当が複数観点を担当できるが、初読と情報を持つ専門監査は兼務しない。
過去のrunで使った読者IDは新しい初読者として認めない。

局所改稿の差分閉鎖は [review-loop](../rules/review-loop.md) に沿って台帳で行い、
`readiness` の全体条件を満たすために不要な全体査読を起動しない。
不合格報告があるrunは履歴として残す。必要な修正と判定の後に新しい凍結版を作り、
最終検査用の実際の報告を揃える。古い指摘を消して新runを合格にするのは禁止。

この検査は虚偽の申告や書かれていない欠陥を見破る仕組みではない。
研究の正しさ、読者の理解、倫理・投稿要件の適合は本文と原資料を読む担当が判断する。

## 実装の検査

```bash
python3 -m unittest discover -s tools/tests -v
python3 tools/paper.py check
```

テストの架空のpass報告はソフトウェアの分岐検査専用で、実際の論文の査読結果ではない。
