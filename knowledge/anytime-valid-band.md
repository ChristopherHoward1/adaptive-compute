# Anytime-valid band for the adaptive procedure

The adaptive procedure uses an empirical-Bernstein-style confidence sequence for
the bounded bootstrap mean `E*[Delta*]`, where each paired-bootstrap draw
`Delta* = M(A, E*) - M(B, E*)` lies in `[-1, 1]`.

The controller stops only when the current confidence sequence is wholly above
`+delta` (`A_better`), wholly below `-delta` (`B_better`), or wholly inside
`[-delta, +delta]` (`equivalent`). Otherwise it continues to the next batch or
returns `abstain` at `B_max`. This is an anytime-valid rule: the stopping decision
is based on a confidence sequence intended to remain valid under optional
stopping, not on a freshly peeked fixed-time interval.

Reference: Howard et al. (2021), "Time-uniform, nonparametric, nonasymptotic
confidence sequences." The implementation uses a finite-horizon
empirical-Bernstein boundary for bounded observations, with a union-bound
allocation over the configured batch looks, and clips the resulting interval to
`[-1, 1]`. `B_max` is selected on the tune split from candidates large enough for
this boundary to resolve non-boundary low-variance cases; the held-out test split
then reports the honest result without retuning.

## Why the mean is the estimand

The released fixed-budget reference makes its finite-budget decision from a
percentile interval, but the non-boundary synthetic battery is constructed so the
reference verdict recovers `decision_from_delta(plugin_delta, delta)`. As the
bootstrap budget grows, `E*[Delta*]` targets that same plug-in decision functional
on scored cases. Boundary-adjacent cases may straddle and are excluded from
false-stop scoring.

False stops therefore measure premature adaptive convergence against the released
reference, not disagreement about the asymptotic estimand.

## Rejected alternative

A tail-probability confidence sequence on indicators such as
`1{Delta* > delta}` and `1{Delta* < -delta}` was rejected. It is bounded and can
represent the three resolved reference branches in the infinite-budget functional,
but it discards the magnitude and variance of `Delta*`. That would make the
heavy-tailed battery member much less adversarial and could turn the evaluation
into an easier problem than the experiment design intended.

Naive per-batch percentile intervals are also rejected: repeatedly checking a
fixed-time interval after each batch is not optional-stopping valid.

## Reading the result: the abstain-vacuity trap

**False-stop rate is only meaningful conditioned on a low abstain / non-decision
rate.** Read the abstain column *before* the false-stop column. A procedure that
abstains on ~100% of a stratum records a false-stop rate of 0 trivially — it never
makes a wrong call because it barely makes calls — and it will pass every mechanical
check (`eval --check`, determinism, accounting) while the headline "H1 negative" it
prints is scientifically vacuous. This was the v0 first-result artifact's initial
state (`equivalent`/`moderate` abstained ~100% at `B_max=320`) and only a cold
reviewer, reading the artifact's own numbers, caught it. Any consumer of the result
must confirm the adaptive procedure actually *resolves* before trusting a false-stop
rate.

## Sizing `B_max` against the boundary, not against `B_ref`

`B_max` must be sized against **this boundary's resolving power**, never set equal to
`B_ref`. The finite-horizon empirical-Bernstein radius is dominated by its linear
term `≈ 14·log_term/(3n)`; at `n = 320` that term alone is ≈ 0.121 — larger than a
typical `δ = 0.05`, so the interval half-width *cannot* fall below δ and an
`equivalent` case (which needs the band wholly inside `[−δ, +δ]`) is unresolvable at
that budget regardless of variance. The reference's percentile interval resolves at
`B_ref` because it is a *fixed-width* functional; the mean CS must instead shrink
Monte-Carlo error below δ, which takes many more draws. Pick `B_max` on the tune
split from candidates large enough for the boundary to resolve non-boundary
low-variance cases, and expect it to exceed `B_ref` substantially. (A tighter
anytime-valid instrument — a Waudby-Smith–Ramdas betting CS — would resolve at far
smaller budgets; the v0 EB negative is specific to this boundary's looseness.)
