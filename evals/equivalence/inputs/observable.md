# Source packet O: observable diameter under metric and mass perturbation

Write a complete, self-contained English expository mathematical article from
these notes. This is an elementary worked result, not a claimed novel research
contribution. Readers know metric spaces, finite probability and basic
inequalities but need observable diameter defined. Include exact statements,
complete proofs, the metric-sharp example, and the mass-threshold limitation.
Use LaTeX article format. The author approves a short expository article with
main result early and proofs in the main text; a long research-literature survey
is neither requested nor supported. Do not put benchmark/task metadata in prose.

## Verified mathematical ingredients to organize

X is a nonempty finite set with two metrics d and e, with |d(x,y)-e(x,y)|≤δ
for all x,y, δ≥0. For probability weights μ on X and 0≤κ<1, define

ObsDiam(X,d,μ;κ) = sup over 1-Lipschitz f:(X,d)→R of
  min over A⊆X with μ(A)≥1-κ of osc_A f,
where osc_A f=max_A f-min_A f. Such A are nonempty. This is the discarded-mass
parameter convention; define it explicitly rather than switching conventions.

For any d-1-Lipschitz f set g(x)=min_y[f(y)+e(x,y)]. Then g is e-1-Lipschitz and
f(x)-δ≤g(x)≤f(x). Justify both statements directly. Consequently osc_A f ≤
osc_A g+δ for any nonempty A; the constant is δ, not an unnecessary 2δ.

Total variation TV(μ,ν) is sup_A |μ(A)-ν(A)|, equal here to
(1/2)Σ_x|μ(x)-ν(x)|. If TV(μ,ν)≤τ and 0≤τ≤κ<1, then

ObsDiam(X,d,μ;κ) ≤ ObsDiam(X,e,ν;κ-τ)+δ.

Proof ingredients: a minimizing set for g under ν at mass 1-(κ-τ) has μ mass
at least 1-κ; the preceding oscillation bound then applies. Minima exist
because X is finite. Take the supremum only after establishing the bound for
every f. Interchanging the pairs gives the corresponding reversed comparison
with its own shifted discarded-mass parameter. When μ=ν, τ=0 gives absolute
difference at the same κ at most δ.

Metric sharpness: X={a,b}, both weights 1/2, κ<1/2, distances d(a,b)=s+δ,
e(a,b)=s with s>0. Every eligible A is X, and observable diameter equals the
distance, so the metric bound is attained.

Mass threshold: distance 1 on {a,b}, κ=0.4, μ=(0.6,0.4),
ν_ε=(0.6-ε,0.4+ε), 0<ε<0.1. Then TV=ε,
ObsDiam(μ;κ)=0 while ObsDiam(ν_ε;κ)=1. Thus arbitrarily small mass perturbation
need not give same-κ continuity. This does not contradict the shifted bound.
Do not silently replace ≥1-κ by >1-κ, omit τ≤κ, or claim same-parameter
continuity from this theorem. All results are finite-space statements.

## Editorial reference access

The orchestrator supplies the same two locally available published-paper
exemplars to both conditions for architecture only. They are not evidence of
novelty or sources for an unverified theorem attribution. Prove all ingredients
used here. External factual claims or new bibliographic citations are optional
only if their actual sources are read and their supporting location recorded.
