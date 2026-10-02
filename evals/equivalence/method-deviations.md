# Execution deviations and limits — 2026-10-02

The preregistered inputs, scoring axes, floors and reader goals were not changed
after generation. No production rule was tuned on these examples.

## Native reader isolation failed

A fresh native Luna reader received only R63's first source-text block as its
assigned reading, but reported `ISOLATION_FAILED` because AGENTS instructions
were automatically present in its context. Its observations are excluded from
reader-goal closure. No further block was supplied to that reader.

This is an actual runtime limitation, not a hypothetical warning. The shipped
rules correctly require failure disclosure, but `fork_turns: none` alone did
not produce the intended instruction-free reader in this environment.

## Separate supplementary reader sessions

The parent checked a different execution method rather than retrying the same
contaminated setup. Fresh CLI sessions ran outside either repository, with
`--ignore-user-config`, `project_doc_max_bytes=0`, `agents.enabled=false`,
`web_search=disabled`, read-only permissions, and explicit Luna/high settings.
No persistent user configuration was changed. The prompt diagnostic showed
generic platform/skill-catalog context but no project AGENTS or writing rules.
The actual reader events showed no tool actions. This is evidence of scoped
input delivery, not a claim that read-only mode forbids reading other files.

The use of a separate CLI is supplementary to the controlled content experiment.
It is **not** validation of the source environment's native blind-review helper,
the starter's automatic role selection, or native reader isolation.

The diagnostic choice follows the documented instruction-discovery behavior:
Codex normally adds global and project guidance, with `project_doc_max_bytes`
limiting that input. See [official AGENTS guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
Exact CLI options were also checked against installed CLI help (0.159.2).

Each artifact has its own fresh session. Blocks are supplied in order at the
introduction, main-proof and ending boundaries. A checkpoint is saved before
creating/delivering the next input. Session resumption preserves observations;
no later manuscript text is available in an earlier input.

On R63 and R42, an initial resume command combined a literal prompt with stdin.
Unlike the initial exec command, resume did not append that stdin. Both readers
reported that no new block had arrived. Those empty-input responses are kept
locally, not scored. The parent then passed a prompt-plus-block file using the
documented `-` stdin argument. No observation was erased or favorable answer
selected; the missing input, not the manuscript, changed.

For the wording-only repaired artifact R91, the first new reader report printed
`ISOLATION_FAILED` while explicitly saying no extra manuscript instructions
were supplied. Before sending any next text, the parent asked only for factual
clarification of that contradiction. The same reader answered `Absent` and
identified the status label as inconsistent. Both reports are retained. This
was not a new manuscript-rating attempt, and no favorable content response was
selected. The discrepancy illustrates why a self-reported status label alone
is not sufficient evidence of isolation or failure.

## What was not compared

The two reviewer orders were reversed to reduce a simple order effect. Both
reviewers were blind to the artifact-to-condition mapping, but this was not a
double-blind experiment: the integrating parent knew the mapping and chose
the tasks. Each arm has one generation per case; there is no variance estimate.

Both arms received verified source claims and proof ingredients, not unverified
research notes. This tests exposition of correct mathematics, not discovery of
hidden false assumptions. The same mathematical corpus was deliberately supplied
to both arms. It does not test finding a suitable corpus from an empty setup.
There are no external mathematical citations in these articles, so first-use
attribution and advanced external-input auditing were not exercised by them.

No human reader, field expert, journal assessment, long original research
manuscript, Japanese version, as-configured model comparison, or nonmathematical
paired article was executed. Requested runtime settings and an actual backend
model identity are different observations; only the former was available here.
