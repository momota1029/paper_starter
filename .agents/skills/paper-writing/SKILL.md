---
name: paper-writing
description: 論文の執筆・改稿・査読・翻訳・理解用ノート作成を、根拠の検証と独立した読者評価を伴う修正ループで進める。分野を問わず使う。一般的な質問への回答、索引やビルドだけの作業、スキル自体の保守には適用しない。
---

# Paper writing

Paths in code use the repository root. Resolve the target from the request and
existing project before asking questions. A natural request such as
「この資料から論文を書いて」「導入が分かりづらい」「日本語版にして」
is sufficient; no activation command is needed.

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
   [companions](../../../rules/companions.md). Delivery preparation uses
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

## Close the task honestly

Read the integrated text and inspect the rendered artifact when a render was
requested or required for delivery. Synchronize affected claims, review
records, companions, and the generated writing index. Do not create unrequested
translations or notes. Report target files, actual checks, review independence,
unresolved findings/reader goals, and any specific author decision still needed.
Successful bookkeeping is not proof of publication quality.
