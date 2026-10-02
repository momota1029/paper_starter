# Lecture notes: progressive understanding

These rules specialize [companions](companions.md) for research lecture or
understanding notes. They are not a new paper pipeline, and do not require an
unrequested translation or note. Use the completed authoritative research and
faithful translations where available; consult verification notes for deeper
details. Explain provisional research as provisional. Do not use a companion
to silently establish or change the upstream result.

## Reader floor and purpose

Declare the discipline, audience, and ordinary undergraduate prerequisites.
For mathematics, default to calculus, linear algebra, elementary sets/functions,
and basic proof reading. Specialist graduate theories are not presumed merely
because they are standard within the paper's field. For other disciplines,
use the corresponding introductory concepts and methods, not mathematical
conventions. An explicit different audience overrides this default.

The note itself is the overview: deepen the same research within one document.
Do not make a separate short overview by default, then start again. The future
author and new reader need reasons to want to understand what happens, why it
happens, how the argument works, and finally the technical detail. This is neither
a shortened publication proof nor a weakened verification record.

## Deepen, do not repeatedly summarize

Use this progression when it fits the material; adapt titles and granularity.

| Level | New understanding | Natural stopping point |
| --- | --- | --- |
| Picture | Objects, question, what changes, outcome, what was unknown | Explain what the research establishes and its scope |
| Reason | Toy model, analogy, plausible mechanism, intuition's limits | Explain why the result is plausible and what intuition does not prove |
| Precision | Necessary concepts, assumptions, normalization, exact claim | Connect the formal statement to the earlier picture |
| Blueprint | A few meaningful argument steps with input, output, purpose | Explain how the conclusion is reached |
| Essence | Naive failure, real bottleneck, decisive idea and evidence | Explain what is difficult and what resolves it |
| Technique | Machinery introduced when the blueprint needs it | Explain each tool's role and limits |
| Links | Specific entry points to the full research and verification | Find details by meaning, even when numbering differs |

Each level refines rather than retracts the previous one. Do not pad the note
with seven paraphrases of the main claim. Readers who stop early should have
useful understanding, not only a collection of definitions. Do not force a
proof-style blueprint on empirical or interpretive work: use the actual chain
of evidence, analysis, and inference, with uncertainty intact.

## Just-in-time prerequisites

The ordinary order is picture → a concrete problem → the tool it needs → use
that tool. A long prerequisite course before the main question is not the
default. A small early notation block is fine when needed immediately; it is
not permission to front-load all background.

Before a specialist object carries inferential weight, give the smallest
truthful bridge. Choose a working model, concrete or finite-dimensional toy
example, operational definition, bounded analogy, or black-box interface.
Show what an abstract object does and why it is needed before notation obscures
it. An example should refine naturally into the exact definition, not teach a
falsehood that must later be withdrawn.

For a black-box theorem or established method, name its input, output,
conditions, why those conditions hold here, and the next use. Readers need not
prove all standard background, but must know what is being assumed and obtained.
“Standard,” “well known,” “as usual,” and a bare citation cannot replace that
interface. Do not hide the research's own decisive idea, estimate, analytical
decision, or inference behind a black box.

Keep the prerequisite ladder in the existing design: concept, first load-bearing
use, reader knowledge there, minimal bridge, argument role, and deferred detail.
It guides teaching order, not an encyclopedic prerequisites chapter.

## Develop the actual argument

The opening is not an expanded abstract. Explain the studied objects, question,
change or comparison, conclusion, and missing knowledge in plain language.
Use only formulas necessary for that picture. Explain a theorem's meaning
before presenting its formal statement when possible.

Give the intuition's limits explicitly. For example, convergence of finitely
many observables need not imply convergence of the whole object; a descriptive
contrast need not identify a causal effect. Use subject-specific hazards, not
a pasted generic warning list.

Introduce the precise objects and assumptions in the order needed for the claim,
then map each part back to the initial picture. The argument map should contain
roughly three to seven meaningful steps where suitable, not just lemma or
section numbers. For each step explain its input, output, next use, and whether
it is established background, routine work, or genuinely difficult.

Allocate depth by difficulty. Explain what fails in the naive approach, the
idea that fixes it, the lemma/method/evidence realizing it, and the decisive
calculation or inference. Before a technical section, answer: without this tool,
where would the preceding map get stuck? A fascinating but unused technique
belongs elsewhere, not in a detour that hides the research.

For multiple families, cases, or regimes, teach shared structure once and
compare differing assumptions, normalization, evidence, extra lemmas, and failed
unifications. Do not erase an essential asymmetry with “similarly,” or reproduce
routine repetition as a full argument.

Every major section should make clear where the reader is, what becomes hard,
what new resolution is added, and what can be explained afterward. These are
content obligations, not four mandatory headings or repetitive recaps.

## Accuracy and omission

Mark informal versus exact explanations at their actual boundary. Say what an
intuition cannot establish and where the precise version appears. Never broaden
conditions, erase uncertainty, or strengthen conclusions for an easier story.

Include each decisive identity, estimate, analysis, or evidential distinction.
Explain what it controls, why it is needed, which parameters or cases it covers,
and what fails without it. A displayed equation is not itself an explanation.
For empirical work retain design limits, measurement meaning, uncertainty and
identification conditions; for interpretation retain provenance and competing
readings. Do not invent data, examples presented as real, or absent evidence.

Routine algebra, standard background proofs, repetitive calculations, purely
publication-driven lemma splits, and unused historical detail can be deferred
with precise pointers. Do not omit the meaning-determining normalization,
critical assumptions, core idea, decisive step, important asymmetry, or warning
against a plausible invalid inference. “See the paper” must not replace teaching
the bottleneck.

A new short proof, alternative analysis, or stronger claim is substantive
research, not just exposition. Verify it with fresh appropriate correctness and
argument reviewers; repair the authoritative research first, then synchronize
companions. A note is not the artifact certifying the full research.

## Voice and aids

Use the intended reader's language and register; Japanese notes normally use
plain declarative prose. Teach as in a careful live explanation, not baby talk.
Do not judge understanding with “obvious,” “easy,” or “you surely know.” Use
established terms rather than coining labels merely to explain. A term list
without what the terms do is not a bridge.

Diagrams are useful for actual dependencies, asymmetries, approximation/limit
flows, or case comparisons; do not add decoration. Exercises are optional and
should consolidate the current level (a normalization, small example, special
case). Never hide an unresolved research gap in an exercise.

Use upstream research for content and terminology, not automatically for section
order. End with semantic pointers to the full argument and verification notes;
do not force numbering to match between genres.

## Test the growth of understanding

Use the [undergraduate lecture skill](../.agents/skills/undergraduate-lecture/SKILL.md)
and [review loop](review-loop.md). The specialized reader replaces the ordinary
blind-reader slot. They receive only frozen prefixes and neutral background,
not this checklist, the ladder, upstream text, or expected answers.

Observe what the reader can explain at natural stopping points: initial result
picture, plausible mechanism, precise scope, argument map, difficult point, and
the purpose of each newly introduced tool. Check that specialist objects have a
usable model before they matter, black boxes have interfaces, technical material
has a visible purpose, and each level adds understanding without repetition.

Save first barriers and later recoveries separately. A definition several pages
later does not repair failure at an earlier required boundary. Reconcile all
observations against the fixed goals; repair at the first needed bridge and
reread with a fresh reader until closure. If no substantive content changed,
recheck affected correctness dependencies, not an unnecessary whole-paper audit.
Preserve genuine author feedback in the existing review record, by understanding
level where useful. When the picture is missing, step back rather than piling on
technical detail. Do not infer a human's understanding from a model's report.
