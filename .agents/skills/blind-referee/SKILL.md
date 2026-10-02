---
name: blind-referee
description: 明示指定された初見査読を、固定した成果物と独立した前方読みで実行する。通常の執筆、正しさの認証、自動改稿、機能自体の保守には使わない。
---

# Blind referee

This is an explicit, report-only primary entry, not a new reviewer. It accepts
`$blind-referee <artifact>` (also an explicit natural-language selection of this
skill). It never authorizes rewriting, commit, push, or submission. A document
mentioning blind review does not activate it. Code paths are repository-relative.

Ordinary paper-writing uses the same helpers automatically when its selected
review plan calls for a blind reader. That does not require invoking this skill
or asking the user to type a command. Do not duplicate an already owned pass.

## Prepare the pass

Read [review-loop](../../../rules/review-loop.md), the applicable boundaries in
[agents](../../../docs/agents.md), and the complete
[command recipe](../../../tools/blind-review/README.md).
Resolve the actual artifact and audience from the request/context; ask only if
genuinely ambiguous. Use one reader by default, at most two when justified by
the review budget. Each receives a neutral one-sentence background, not an
expected result. Do not interpolate trailing user text into shell syntax.

Use a current rendered PDF or self-contained UTF-8 Markdown/text. Raw TeX,
unexpanded includes, and an old PDF without source provenance are not suitable.
Use the normal build/render checks when needed. The helper neither builds nor
scrubs metadata nor proves PDF/source correspondence. For dependencies, use
the source-binding loop contract in read-only mode or record and verify the
complete source version separately.

## Execute, do not merely prepare

1. Verify available runtime role selection and fresh-context controls. Use the
   configured `blind_reader` (Luna), or `blind_reader_sol` for a justified demanding
   read, with their actual runtime model/effort. Keep the primary model unchanged.
   The generic-spawn adapter in the agent documentation is permitted only when
   it applies the role instructions and settings; it is not evidence of isolation.
   Before disclosing an artifact/path, open the fresh role with only the neutral
   background and ask whether production routing, goals, history, or other
   artifacts were already injected. Preserve this preflight separately. An
   observed leak stops the blind lane before reading. An absence self-report is
   not proof: inspect runtime diagnostics when available and keep limits explicit.
2. Run `python3 tools/blind-review/review.py prepare <artifact> --reader <brief>`;
   retain the run ID. Use `--role blind_reader_sol` when selecting that role.
   Repeat `--reader` only for an assigned second lane. Prepared manifests and
   snapshots are immutable; do not edit them to make verification pass.
3. Obtain `python3 tools/blind-review/review.py packet <run> --lane 1`. Inspect
   its values against the actual live spawn schema and send them to the preflighted
   role. A JSON
   packet and exit code 0 are not review execution. Supply only the neutral
   artifact, reader brief, and standing forward-reading/report procedure.
   Never provide this skill, rules, goals, contract, manifest, revealing source
   filename, upstream draft, diff, writer explanation, or other reader reports.
4. Save each actual checkpoint before allowing the next prefix. Do not preload
   the whole text and reconstruct a reading history afterward. Keep all lanes'
   reports hidden from each other until every reader finishes. Preserve first
   confusion and later recovery. The role's report schema is generic, not an
   answer key. Record actual thread IDs and model/effort only where observed.
5. Run `python3 tools/blind-review/review.py verify <run>` after collection;
   separately check source dependencies when not using the loop contract.
   Changed artifacts/sources invalidate current-version claims. A subsequent
   review uses a fresh run and readers, not an unchanged favorable reroll.
6. Return the reconstruction, located barriers, recovered/unread scope, artifact
   hash, runtime provenance, and isolation limitations. Save evidence only in
   an authorized existing review record, outside reader input directories.

Fresh history and read-only permissions do not prevent injected instructions or
other-file access. Any observed contamination or preloading invalidates the
corresponding blindness claim. If native execution cannot provide the needed
boundary, report the limitation. The separately documented
[supplementary reader CLI](../../../docs/reader-runner.md) is an explicit alternate
transport for supported text, never a silent native substitute or proof of
isolation. A local reading under a single-agent request stays labeled local.

This skill does not initiate a repair loop. An integrated writing request may
use [reader-loop state](../../../tools/blind-review/READER_LOOP.md) under its own
edit authority. Blind reading alone certifies neither subject correctness nor
submission readiness. If only preparation succeeded, say exactly that.
