# Blind-review input commands

These standard-library commands freeze a rendered artifact and prepare minimal
inputs for the existing native reader roles. They do not execute a model, edit
a manuscript, or establish reviewer independence. Policy remains in
[review-loop.md](../../rules/review-loop.md); the optional explicit skill is
[blind-referee](../../.agents/skills/blind-referee/SKILL.md).

Use Python 3.11 or later from the repository root:

```sh
python3 tools/blind-review/review.py prepare output/example/paper.pdf --reader "A reader familiar with the field's introductory concepts." --role blind_reader
python3 tools/blind-review/review.py packet <run> --lane 1
python3 tools/blind-review/review.py verify <run>
```

`prepare` returns a new run ID. Inputs may be rendered PDF or self-contained
UTF-8 `.md`/`.txt`, not raw TeX. A PDF signature check does not verify rendering.
Supply one neutral background sentence per `--reader`, at most two readers.
The primary checks its semantic neutrality and the requested review scope.

`packet` prints a request with `agent_type`, `fork_turns: "none"`, and a JSON
message containing only `target_artifact` and `reader_background`. Valid roles
are `blind_reader`, `blind_reader_sol`, and `undergraduate_reader`. Choose the role
at `prepare` (default `blind_reader`); it is frozen in the manifest. An optional
`packet --role` only asserts the same role and cannot replace it. Selecting a
role does not make it available or invoke it. The primary must use the actual
runtime schema and the shipped role's model/effort settings; see
[agent routing](../../docs/agents.md). A generic spawn requires explicit runtime
model/effort arguments and that role's standing procedure. Do not pass author
intent, contract goals, previous reports, or production instructions to readers.

Readers follow the standing forward-reading procedure: record reconstruction
at a natural boundary before loading the next part. A neutral artifact path is
not permission to preload the entire artifact. All assigned reports remain
separate until collection finishes. Verify afterward; an altered source or
snapshot invalidates applicability to the current version. Bind source inputs
as well as the rendered artifact using [reader_loop.py](READER_LOOP.md) when
revising toward a frozen reader contract. That command already prepares the
artifact; do not prepare a second run for the same review.

## Local records and limits

```text
.paper-local/blind-review/<run>/
  manifest.json
  reader-1/artifact.pdf
  reader-2/artifact.pdf       # only when a second reader was assigned
```

Extensions match the input. Runs are ignored by Git, exclusively created,
never overwritten, and never automatically deleted. An incomplete run is kept
for inspection; absence of its manifest means preparation did not complete.
Reader folders may contain only their artifact. Reports belong outside those
folders. Preparation checks source bytes before and after copying, not a
filesystem-wide lock. Paths reject traversal, symlinks and junctions.

Hash equality proves neither a model run nor access isolation. Native agents
may receive injected guidance or access other files; disclose observed leakage.
If isolation fails, retain the failure and mark independent reading incomplete.
Do not substitute the auxiliary [text reader CLI](../../docs/reader-runner.md)
and claim native equivalence. Such evidence must retain its actual provenance.
`native` receipts remain primary-supplied claims, not authenticated attestations.
No helper proves prefix isolation, disciplinary correctness, build equivalence,
human comprehension, or PDF legibility. Artifact metadata and embedded comments
are not stripped: "blind" here concerns production history, not author anonymity.

Run synthetic regression checks through normal discovery:

```sh
python3 -m unittest discover -s tools/tests -p 'test_blind_review.py' -v
python3 -m unittest discover -s tools/tests -p 'test_reader_loop.py' -v
```

Tests use temporary fictional artifacts and never call a model or the network.
