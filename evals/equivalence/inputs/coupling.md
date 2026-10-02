# Source packet C: concentration transfer from a finite coupling

Write a complete, self-contained English expository mathematical article from
these notes. This is an elementary worked result, not a claimed novel research
contribution. Intended readers know metric spaces, finite probability and basic
inequalities, but no optimal transport theory. Include a precise main theorem,
proof, useful consequence and a worked limitation. Do not pad to a page count.
Use LaTeX article format. The author approves a short expository article with
main result early and proofs in the main text; a long research-literature survey
is neither requested nor supported. Do not put benchmark/task metadata in prose.

## Verified mathematical ingredients to organize

X is a nonempty finite metric space with distance d; μ and ν are probability
weights. A coupling π(x,y) ≥ 0 has row sums μ(x) and column sums ν(y). For r ≥ 0,
suppose the sum of π(x,y) over d(x,y)>r is at most η, where 0≤η≤1.
For every 1-Lipschitz f:X→R, center a∈R and t≥0,

ν({y: |f(y)-a|>t+r}) ≤ μ({x: |f(x)-a|>t}) + η.

Underlying inclusion: if |f(x)-a|≤t and d(x,y)≤r then |f(y)-a|≤t+r.
An arbitrary coupling suffices; there is no need to assert existence of an
optimal coupling or a duality theorem. The bound can be capped at 1.

If a coupling has mean distance D=Σπ(x,y)d(x,y), then for every r>0 its bad mass
is at most D/r. This gives an explicit radius/error tradeoff. If D=0, every
positive-weight pair is on the diagonal and μ=ν; do not divide by zero.
Both the radius increment and an exceptional mass are meaningful; average
distance alone does not imply all coupled pairs are close.

Concrete check: X={0,10}, usual distance, μ=δ_0,
ν=(1-ε)δ_0+εδ_10, 0<ε<1. The unique coupling has D=10ε.
For f(x)=x, a=0, t=0, r<10, the left tail is ε. Thus a nonzero mean-distance
bound cannot give exact support containment in a small interval without an
exceptional mass. For r=10 the strict tail vanishes: endpoints matter.

The estimate applies to each Lipschitz observable under the same coupling;
it does not assert that a chosen center is also a median for ν. It does not
compare two different metric spaces without specified common-space data.

## Editorial reference access

The orchestrator supplies the same two locally available published-paper
exemplars to both conditions for architecture only. They are not evidence of
novelty or sources for an unverified theorem attribution. Prove all ingredients
used here. External factual claims or new bibliographic citations are optional
only if their actual sources are read and their supporting location recorded.
