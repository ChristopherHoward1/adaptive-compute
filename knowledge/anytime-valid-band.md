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

See `knowledge/equivalence-band-savings.md` for the offline probe showing how
this position-dependent equivalence budget behaves on a heterogeneous in-band
fixture.

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
anytime-valid instrument can resolve at far smaller budgets, but it still has to be
scored against the same fixed-B Pareto gate.)

## Betting CS (WSR)

The betting re-test adds a Waudby-Smith--Ramdas hedged-capital confidence sequence
as a selectable instrument. Each bootstrap draw `Delta* ∈ [-1, 1]` is rescaled to
`X = (Delta* + 1) / 2 ∈ [0, 1]`, the CS is built for `mu_X`, and the reported
interval is mapped back to Delta-space with `2 * [l, u] - 1`.

For a grid of candidate means `m ∈ [0, 1]`, the implementation maintains
`K_t(m) = 0.5 * (K_t^+(m) + K_t^-(m))`, where
`K_t^±(m) = product_i (1 ± lambda_i(m)(X_i - m))`. The betting fraction is the
approx-GRAPA plug-in
`abs(mean_{<i} - m) / (var_{<i} + (mean_{<i} - m)^2)`, truncated to
`[0, c / max(m, 1 - m)]` with `c = 0.5`. The first two draws use `lambda = 0`
because the plug-in is based only on past data. The CS keeps exactly those grid
points whose running maximum capital has not crossed `1 / alpha`:
`max_{s <= t} K_s(m) < 1 / alpha`. Predictability of `lambda_i` and the running
maximum are the load-bearing validity mechanics; there is no `max_looks` union
bound.

This resolves smaller than the EB band because it spends evidence through a
data-adaptive martingale rather than carrying EB's finite-horizon linear term at
every look. In the `work/betting-cs-retest` A/B, betting tuned `B_max = 512` with
the shared `b = 64` and reduced held-out median draws from EB's `128/768/448`
(`easy/equivalent/moderate`) to `64/192/128`. The recorded verdict did **not** flip:
both arms passed the false-stop test, but betting's `savings_pareto_pass` remained
false because the equivalent stratum still had fixed-B dominators under the shared
fixed-B grid.

For the follow-up equivalence-band retest and its structural-negative scoping, see
`knowledge/equivalence-band-savings.md`: adaptive savings are a directional-decision
story here, not an equivalence-decision story.
