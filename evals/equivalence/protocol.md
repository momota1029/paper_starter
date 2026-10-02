# Paired writing evaluation — preregistered 2026-10-02

This protocol was saved before any paired design or manuscript was generated.
It tests a bounded behavioral comparison, not statistical equivalence or
publication readiness. The two new synthetic mathematical source packets are
not the earlier paragraph-repair fixtures. They contain no original research
claim. No private research manuscript is republished.

## Conditions and scope

- Two full English expository mathematical articles, each with introduction,
  exact statements, complete proofs, examples and limitations, are generated
  under the current `doc` rules and under Paper Starter rules.
- Same source packet, reader background, permitted corpus, output format and
  requested writer model/effort in both arms: Sol (`gpt-6.1-sol`), high.
  This deliberately controls for model choice: the source environment currently
  pins its writer to Luna, whereas the starter pins its writer to Sol. This is
  **not** an as-configured runtime comparison.
- A fresh designer per arm, then a different fresh writer per arm, uses the
  actual applicable rules. Writers run sequentially. Designers may inspect the
  same two local published-paper exemplars; only architecture observations,
  not their text, enter the released record. No third-party source is copied.
- Source rules are read-only. No skill/rule tuning takes place before the
  baseline is scored. Input/rule hashes and actual prompts are retained locally.
- The common orchestration supplies design, writing, blinded review and one
  accepted repair bundle, then fresh closure checks if material changes occur.
  This compares the content rules under a controlled loop, not native role
  discovery, automatic triggering, trust settings or the entire `doc` toolchain.
- Reviewers receive neutral variant labels, artifacts and (for specialist
  review) source packets and this rubric, never condition identities. A fresh
  reader per artifact receives only neutral background and successive text
  blocks; its observation is recorded before the next block is supplied.
  No filesystem sandbox or backend model identity is claimed without evidence.
  Forward readers see mathematical source text in LaTeX blocks, not the full
  PDF in advance; this tests exposition rather than human PDF reading. Rendered
  pages are checked separately. Specialist scoring is performed independently
  by two fresh reviewers; record both scores without averaging away failures.

## Prespecified observations and decision

Source-aware reviewers separately score each paper from 0 to 4 on:

1. Mathematical correctness and scope (quantifiers, endpoints, hypotheses).
2. Explicit logical support (definitions, proof dependencies, application steps).
3. Structure and claim/evidence hierarchy.
4. Evidential restraint (no invented novelty, attribution, results or sources).
5. Prose usability for the declared reader (precise referents and useful detail).

Anchors: 0 unusable; 1 central failure; 2 material repair required; 3 usable with
local minor repair; 4 no substantive defect found in the assigned scope.
Findings require a location, evidence and severity; stylistic preference alone
is not a defect. Numerical scores are diagnostic, not objective measurements.

Required common reader goals, frozen before generation:

- By the end of the introduction: recover the problem, scope, main bound and
  distinction between what is and is not claimed; later proof may be deferred.
- By the end of the main proof: recover the hypotheses, the pivotal inequality
  and how the proof establishes the stated conclusion.
- By the end: explain the limitation/counterexample and its relation to the
  main result. Preserve first confusion even if later text resolves it.

For a **bounded no-material-regression finding**, each starter paper must have
no accepted blocking/major finding and no missing/misread required reader goal
after the executed loop. Each specialist axis must be at least 3, with total
at least 18/20. Against the corresponding source-rule article, no axis may fall
by more than 1 and total may not fall by more than 2. Both arms must meet the
absolute floor; joint failure cannot establish equivalence. Report first-pass
and repaired results separately, including rejected findings and reasons.

Any failing condition yields a localized gap, not a favorable aggregate.
An unexecuted check remains unknown. No repeated unchanged evaluation to obtain
a favorable verdict. A reader-goal failure needs a fresh reader after repair.
Mechanical and visual PDF checks supplement but do not replace content review.

## Limits and follow-up

These two finite metric-measure examples do not establish all-genre equivalence,
long-paper quality, real literature discovery, original proof validity,
Japanese writing/translation, actual human comprehension, or runtime automatic
role routing. No human approval may be fabricated. Cross-domain short fixtures
from the previous run remain separate evidence, not a matched comparison.
Any change to the production rules after this baseline must be identified and
tested on a new held-out task before claiming improved generalization.
