---
name: undergraduate-lecture
description: 学部水準で研究の筋を追える講義・理解用ノートの作成、改稿、前提知識の橋渡し、初読確認に使う。paper-writing の追加規則であり、一般的な会話説明、スライドのみの依頼、機能自体の保守には使わない。
---

# Undergraduate lecture

This overlays [paper-writing](../paper-writing/SKILL.md), not a second pipeline.
When entered directly, read that skill once and retain its risk level,
verification, review, build, record, and authority boundaries. Do not recurse.
Read [lecture prose](../../../rules/prose-lecture.md) in full before design or
writing. Produce only the companion the user requested.
An established `[slug]_lec.tex` target also selects this overlay; preserve an
explicit author-specified audience instead of inferring a different one from
the filename.

## Reader and prerequisite contract

Set the discipline and actual undergraduate background explicitly. Do not
assume field-specialist graduate knowledge. For mathematics, default to ordinary
calculus, linear algebra, elementary sets/functions, and basic proof reading;
not functional analysis, advanced probability, or the paper's specialist field.
Other disciplines use their own introductory training, not this math checklist.
The goal is following the research argument, not reproving all background.

For new notes or substantial accessibility rewrites, normally select L2. The
`designer` builds the ordinary design plus a compact prerequisite ladder in
`design.md`, not a separate registry. For each needed concept record:

1. concept/notation and its first inference-bearing use;
2. what the reader knows at that point;
3. the smallest needed working model, toy example, operational definition,
   black-box interface, purpose-before-notation, or dependency bridge;
4. its job in the argument and what deeper details may safely wait.

Fix observable reader goals at natural boundaries before generation. Do not
front-load the entire prerequisite ladder into the lecture. `writer` receives
the accepted design and lecture rules. Motivation and a truthful picture precede
machinery; every technical step must have a reason. Standard background can be
black-boxed only with explicit input, output, and applicability. The paper's own
decisive idea cannot disappear behind a citation or “see the paper.”

## First read and convergence

`undergraduate_reader` replaces the normal blind-reader accessibility slot;
do not activate both merely because both exist. Read
[agent routing](../../../docs/agents.md) and
[reader-loop commands](../../../tools/blind-review/READER_LOOP.md). Select
`--role undergraduate_reader` when preparing its frozen run. The loop helper
does not execute that role: actually invoke it with fresh history and its
Luna/high runtime settings.

Give only frozen prefixes, a neutral reader-background sentence, and the
standing reading procedure. Never send the prerequisite ladder, goals, upstream
manuscript, rules, diff, expected barriers, or past reports. Save short actual
reconstructions before reading onward. A simulated floor is not a real student.

A fresh `structure_reviewer` and the primary reconcile observed barriers with
the fixed contract. Distinguish ordinary difficulty, absent observations, and
genuine missing bridges. Locate the first point where the reader needs the
bridge; adding definitions after that point does not close an earlier goal.
Batch the smallest sufficient repair into one writer pass, build once, recheck
affected correctness/dependencies, and reread with a fresh undergraduate reader.
Repeat until accepted barriers and required goals close; no default total round
cap. A scope/authority/resource/isolation stop remains explicitly unfinished.

Do not weaken a claim for accessibility. New arguments or stronger claims go
through ordinary substantive verification and upstream synchronization first.
Record unread scope and human-reading needs. Reader-goal closure does not prove
correctness or that real undergraduates will understand the text.
