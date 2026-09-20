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
