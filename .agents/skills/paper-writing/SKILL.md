---
name: paper-writing
description: 論文の執筆・改稿・査読・翻訳・理解用ノート作成を、根拠の検証と独立した読者評価を伴う修正ループで進める。分野を問わず使う。一般的な質問への回答、索引やビルドだけの作業、スキル自体の保守には適用しない。
---

# Paper writing

Paths in code use the repository root. Resolve the target from the request and
existing project before asking questions. A natural request such as
「この資料から論文を書いて」「導入が分かりづらい」「日本語版にして」
is sufficient; no activation command is needed.
An output choice such as 「pf/enだけで」 is also sufficient. Follow the output-set
contract in [pipeline](../../../rules/pipeline.md): preserve the chosen artifacts
in `design.md`, create only those requested, and do not count unselected
translations or lecture notes as missing completion requirements. A lecture
may be produced directly from the authoritative paper without a translation.

## Establish scope and read the rules

1. Inspect `writing/<slug>/meta.toml`, the current manuscript, `evidence.md`,
   `claims.json`, `design.md`, `corpus.md`, `quality-contract.md`, and existing review records where
   present. Do not manufacture missing facts to fill these records. For a new
   project use [workspace rules](../../../rules/workspace.md) and the portable
   [tool commands](../../../tools/README.md).
2. Read [review-loop](../../../rules/review-loop.md) first and select the
   smallest sufficient risk level. State changed risks and actual review roles.
3. For every prose task, read
   [logical-writing](../../../rules/logical-writing.md),
   [argument-audit](../../../rules/argument-audit.md), and
   [prose](../../../rules/prose.md). For new or substantial production also
   read [pipeline](../../../rules/pipeline.md).
4. Select the relevant evidence contract from
   [research profiles](../../../rules/research-profiles.md). Mixed methods
   combine relevant obligations; a new field can add a project-specific
   contract without changing shared rules. Read
   [quality contracts](../../../rules/quality-contract.md) and preserve inherited
   attribution, external-input coverage, and binding corpus/author constraints.
   Record absent decisions as unresolved, not as permission to weaken them.
5. Read [sources](../../../rules/sources.md) when using evidence, citations,
   or close-paper exemplars, and [reviewer roles](../../../rules/reviewer-roles.md)
   and [configured agents](../../../docs/agents.md) before delegation. Use the
   actual role definitions in `.codex/agents/`, including their model and effort.
   Translation or explanatory companions additionally use
   [companions](../../../rules/companions.md). Undergraduate-accessible research
   notes (including an established `[slug]_lec.tex` target) additionally use
   [undergraduate-lecture](../undergraduate-lecture/SKILL.md)
   once as an overlay, without recursively starting another pipeline. CVs and
   grant/application interviews instead use
   [application-interview](../application-interview/SKILL.md), not this workflow.
   Delivery preparation uses
   [release](../../../rules/release.md).

The rules are the single source of truth. Do not make competing skill-local
copies. A delegated reviewer follows its assigned read boundary, not this
primary-only routing procedure. Never send this skill to a blind reader.

## Execute the selected loop

- Separate research verification from public exposition. Establish which
  claims are evidenced, provisional, contradicted, or unresolved before writing.
- For new papers or major structural changes, select two to four close actual papers and record
  their architecture, detail allocation, register, exact locations, and any
  justified departure. If sources are unavailable, record that limit and
  produce only an explicitly provisional design.
- Fix reader goals, preserved claims, baseline, and repair scope before
  generation. Resolve routine choices from evidence; ask only for substantive
  missing decisions. Never turn every section title into an approval gate.
- Design, writing, and independent audit use separate fresh contexts when
  available. All writers operate sequentially in one working tree. Assign one
  build owner. Read-only specialists may run in parallel.
- Freeze the reviewed version; actually execute the selected independent
  checks. A generated review packet is not a completed review. Collect reports
  before comparison. Adjudicate findings against the artifact and evidence.
- When the selected plan uses native forward-reader feedback on PDF/Markdown/text,
  automatically use
  [reader-loop commands](../../../tools/blind-review/READER_LOOP.md) to bind the
  fixed contract, source dependencies, original baseline, observations and adopted
  repairs. Read that recipe before preparing the run. It calls the shared
  blind-review preparation once; do not also prepare a duplicate pass, ask the
  user to invoke `$blind-referee`, or require a hand-written CLI command.
  The standalone `$blind-referee` entry remains report-only. For supported text,
  the existing supplementary reader transport is a separately labeled option,
  not evidence of native isolation. It retains its own checkpoint/receipt format;
  do not feed incompatible receipts into this state machine or relabel them
  native. On that alternate path, keep the same fixed goals, baseline, adopted
  repair and fresh-review cycle in the existing project ledger under review-loop
  rules. Unsupported formats or manual reviews follow those same record duties.
- A clean specialist report still includes positive coverage of external inputs,
  attribution placement, and binding constraints, or a scoped reason why none
  apply. Reader summaries must evidence scope and conditions, not just fluency;
  missing observation is not proof of understanding or misunderstanding.
- Send one accepted repair bundle to the writer. Use a fresh reviewer for
  material repairs and a fresh forward reader for reader-goal failures. Recheck
  the affected dependency cone. Return to design on structural mismatch or
  divergence; do not keep polishing unchanged assumptions.
- Preserve unknowns, failed checks, unread scope, and actual stop states.
  Continue useful in-scope work when a tool or decision is missing. A local
  self-read is useful but cannot replace independent review or a human read.
- In an authorized revision task, repeat the adopted repair → affected checks →
  fresh review cycle until the scoped convergence conditions in review-loop hold.
  There is no default two/three-round cutoff. Explicit resource budgets and
  missing authority, evidence, isolation or independent reviewers are unfinished
  stop states, not permission to call the task converged. Report-only tasks never
  acquire edit authority from this loop. Do not repeat unchanged failed inputs;
  persistent failure returns to design, not a favorable-reader lottery.

## Close the task honestly

Read the integrated text and inspect the rendered artifact when a render was
requested or required for delivery. Synchronize affected claims, review
records, companions, and the generated writing index. Do not create unrequested
translations or notes. Report target files, actual checks, review independence,
unresolved findings/reader goals, and any specific author decision still needed.
Successful bookkeeping is not proof of publication quality.
