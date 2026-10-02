# Frozen reader-contract loop

This deterministic state machine supplements [blind-review inputs](README.md).
The primary performs actual delegation, adjudication, authorized repair, build,
and fresh review. Commands only prepare/check records and print handoffs; they
never call models or edit prose. Existing correctness and source checks remain
separate from reader recovery. Use [review rules](../../rules/review-loop.md)
and the [paper-writing skill](../../.agents/skills/paper-writing/SKILL.md).

## Workflow

1. Before repairing, freeze a small contract for the actual field, genre, scope,
   reader and existing edit authority. Preserve the current draft as the first
   baseline. For new production, design the contract first and freeze the first
   draft as baseline. Store private JSON under `.paper-local/`.
2. Prepare the artifact, contract and all relevant source dependency hashes:

   ```sh
   python3 tools/blind-review/reader_loop.py prepare output/example/paper.pdf --contract .paper-local/reader-contract.json --reader "A reader with introductory knowledge of this field." --role blind_reader --revision "actual source revision and working-tree context"
   python3 tools/blind-review/review.py packet <run> --lane 1
   ```

   Do not run a second `review.py prepare` for this pass. The primary checks
   dependency completeness, rendered-source equivalence and rendering.
3. Actually invoke each selected role with fresh context and the actual runtime
   model/effort settings. Before giving any artifact/path, perform a context
   preflight with only neutral background and the standing procedure: ask whether
   production routing, goals, history or other artifacts are already visible.
   Keep that response separately and stop a contaminated blind lane. Check runtime
   diagnostics where available; a denial of contamination is not authentication.
   Only then give the artifact, neutral background and standing
   forward-reading procedure. Do not disclose this document, contract, expected
   answers or history. Collect brief reconstruction before each next portion.
4. After all readers finish, verify, retain their original responses outside the
   reader folders, and record each actual report:

   ```sh
   python3 tools/blind-review/review.py verify <run>
   python3 tools/blind-review/reader_loop.py record <run> --lane 1 --report .paper-local/reader-report.json --agent-id "observed runtime thread ID" --execution native
   python3 tools/blind-review/reader_loop.py editor-packet <run>
   ```

   `native`, `local`, and `synthetic` describe the actual execution. An auxiliary
   CLI reading is not a native review. Its receipt/checkpoint format belongs to
   the separate [reader runner](../../docs/reader-runner.md), not this report
   parser; retain that path's evidence and the same fixed-contract cycle in the
   project ledger rather than inventing a converted native observation.
   Never invent observations, missing report
   fields or observed IDs. Missing/failed isolation is not restored by claiming
   the reader ignored leaked context. Reader IDs must be fresh across all lanes
   and rounds, including local/synthetic observations; changing an execution
   label cannot reset freshness. The helper does not authenticate supplied IDs
   or provenance.
5. Invoke a fresh read-only `structure_reviewer` to compare all observations with
   the frozen contract. The designer/writer cannot serve as independent auditor.
   The primary checks and adopts the reconciliation against textual evidence:

   ```sh
   python3 tools/blind-review/reader_loop.py reconcile <run> --assessment .paper-local/reader-assessment.json
   python3 tools/blind-review/reader_loop.py status <run>
   ```

   Every goal requires an assessment for every assigned reader, with checkpoint
   references. Required recovery must occur by the original `by` boundary; later
   explanations cannot retroactively satisfy it. Every event needs a disposition.
   Code validates coverage and references, not the truth of semantic judgments.
6. Only `REPAIR` permits `repair-packet`. Invoke the writer for one accepted repair
   bundle within `edit_targets`, rebuild once, and run affected correctness,
   citation, argument and rendering checks. Then freeze the changed artifact:

   ```sh
   python3 tools/blind-review/reader_loop.py repair-packet <run>
   python3 tools/blind-review/reader_loop.py advance <run> --revision "actual repaired source revision"
   ```

   Use the new run ID and new readers from the natural entry, not the diff.
   Preserve the first baseline, contract and selected reader role across every
   round. Unchanged sources, unchanged artifact bytes, any return to a previous
   artifact hash, or changed read-only dependencies reject advancement.
   Do not weaken goals, reuse readers or retry unchanged text until a pass appears.
   Reconsider the design when the necessary repair exceeds authorized scope.

The default has **no round cap**: continue authorized repair and fresh review
until closure or a real blocker. `max_rounds` may be omitted or `null`. An explicit
positive integer caps the entire loop, including the initial and final readings;
exhaustion is unfinished work, never convergence. Individual commands terminate
after their operation; the primary owns continuation. A user stop, missing author
decision, unavailable runtime or isolation failure must be reported with remaining
checks, never converted to a passing record. Read-only requests produce reports.

## Contract schema (version 1)

```json
{
  "schema_version": 1,
  "scope": "Introduction",
  "entry": "Beginning of the artifact",
  "goals": [
    {"id": "G1", "by": "End of opening paragraph",
     "outcome": "Explain the problem and why the proposed approach is needed",
     "required": true}
  ],
  "preserve": ["Preserve supported claims, uncertainty, terminology and citations"],
  "sources": ["writing/example/paper.md", "writing/example/references.bib"],
  "edit_targets": ["writing/example/paper.md"],
  "mode": "edit",
  "max_rounds": null,
  "max_repair_scale": "section"
}
```

All sources must exist at canonical repository-relative paths. Include relevant
build dependencies; the helper does not discover them. `edit_targets` is a subset
of `sources`, not permission to change every dependency. `mode: "read-only"`
requires `edit_targets: []`; `edit` needs at least one explicit writable source.
Scales: `sentence`, `paragraph`, `section`, `architecture`. One to twenty goals
with distinct IDs are required, including at least one required goal. Optional
goals must be optional before reading; no goal may disappear during reconciliation.
A mistaken contract returns to design; no prepared contract can be overwritten.

## Reader report schema (version 1)

The standing role provides this generic form without receiving the contract.
Checkpoints are observations at natural boundaries, not an answer key.

```json
{
  "schema_version": 1,
  "prefix_isolation": true,
  "checkpoints": [
    {"id": "C1", "location": "Opening paragraph",
     "summary": "The approach is introduced, but its purpose is unclear here",
     "evidence": ["Opening paragraph: 'We introduce the approach ...'"]}
  ],
  "events": [
    {"id": "E1", "kind": "MISSING_PAYOFF", "location": "Opening paragraph",
     "reading": "I cannot identify the problem it addresses",
     "evidence": "The definition precedes any explanation of its purpose",
     "recovery": null}
  ],
  "unread": ["Body after the Introduction"]
}
```

Events: `STUMBLE`, `BACKTRACK`, `LOST_THREAD`, `WRONG_MODEL`, `MISSING_PAYOFF`.
`recovery` is null or the later recovery location; do not erase the initial event.
At least one checkpoint with evidence is required; event/unread lists may be empty.
These are concise observed answers, not hidden reasoning. Preloading the full
artifact means `prefix_isolation: false`; never manufacture a checkpoint history.
Checkpoint `evidence` contains nonempty strings, not `{text, locator}` objects;
event `evidence` is a single string. Preserve original replies when requesting a
serialization-only correction. Do not turn reformatting into a new reading,
backfill missing observations, or hide an initially incorrect isolation flag.

An undergraduate prerequisite event may additionally contain nonempty `concept`
and `minimal_bridge` strings and a `bridge_kind` from `WORKING_MODEL`, `TOY_EXAMPLE`,
`OPERATIONAL_DEFINITION`, `BLACK_BOX_INTERFACE`, `PURPOSE_BEFORE_NOTATION`, or
`DEPENDENCY_BRIDGE`. These observations are preserved unchanged in the receipt;
the code neither invents them nor rewrites them into a standard reader's report.

## Primary-adopted reconciliation

```json
{
  "goals": [
    {"lane": 1, "goal": "G1", "status": "missing", "checkpoints": ["C1"],
     "reason": "C1 does not recover the purpose by the opening boundary"}
  ],
  "events": [
    {"lane": 1, "event": "E1", "disposition": "repair",
     "reason": "Purpose is needed before the definition",
     "evidence": "C1 and the opening paragraph"}
  ],
  "repair": {
    "scale": "paragraph",
    "instructions": "Move the source-supported purpose before the definition",
    "closure": ["A fresh reader recovers the purpose at the opening boundary"]
  }
}
```

Exactly one row per `(lane, goal)` and `(lane, event)` is required. Goal status is
`recovered`, `partial`, `missing`, or `misread`. Event disposition is `repair`,
`defer`, `tolerate_stumble` (only `STUMBLE`), `textual_counterevidence`,
`allowed_background`, or `contract_allows_deferral`. Rejections need concrete
textual/contractual evidence. "Minor" or "out of scope" does not close an event.
Every unmet required goal or accepted/deferred event needs one repair specification
at its actual scale, even if only reporting/design is authorized. If none remain,
`repair` must be null. Choose the smallest sufficient repair, not the smallest diff.

## Status and integrity

| `next_action` | Meaning |
| --- | --- |
| `REPAIR` | Unmet goals/events; another repair is within frozen authority and any explicit cap |
| `RETURN_TO_DESIGN` | Necessary repair exceeds authorized scale; work remains unfinished |
| `STOP_BUDGET` | Explicit round cap reached with unmet goals/events; unfinished |
| `REPORT_ONLY` | Original request authorizes diagnosis but no repair |
| `LIMITED_REVIEW` | Recovery reported with local/synthetic execution or failed prefix isolation |
| `HUMAN_READ` | Goals recovered in reported native observations; human and other checks remain |

Exit 0 means the command completed, not that the paper passed. Status reports the
scope, entry, unread ranges, first baseline and artifact hash. It never certifies
human comprehension. `HUMAN_READ` is not full manuscript closure. Do not claim
unread sections were checked. Only actual human feedback closes human reading.

`loop.json`, `observation-<lane>.json`, and `reconciliation.json` sit beside the
manifest under `.paper-local/blind-review/<run>/`, outside reader inputs. Records
are write-once and sealed against accidental corruption. Historical validation
checks snapshots while explicitly skipping comparison to today's live source;
normal `review.py verify` always checks the current source. Checks are best-effort
against concurrent writers. Seals are not signatures and do not resist an actor
rewriting both payload and seal.

Keep real run/thread IDs, requested and observed runtime settings, actual checks,
accepted findings, failures and remaining human work in the project's existing
review ledger. This transient folder is not a second publication registry.
No execution, provenance, build equivalence, semantic grading, prefix enforcement,
or disciplinary correctness is automatically certified by these commands.
