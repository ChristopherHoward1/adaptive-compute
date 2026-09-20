"""Fixed-B sweep baselines and Pareto comparison helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike

from adaptive_compute.bootstrap import paired_bootstrap_deltas
from adaptive_compute.reference import Decision, UnresolvedReferenceError

SweepDecision = Decision | Literal["unresolved"]


@dataclass(frozen=True)
class FixedBResult:
    b: int
    decision: SweepDecision
    interval: tuple[float, float]
    draws_consumed: int


@dataclass(frozen=True)
class ParetoResult:
    dominated_fixed_b: tuple[int, ...]
    best_savings_ratio: float
    adaptive_median_draws: float
    fixed_best_median_draws: float | None


def decision_from_interval(
    lower: float,
    upper: float,
    *,
    margin: float,
) -> SweepDecision:
    if lower > margin:
        return "A_better"
    if upper < -margin:
        return "B_better"
    if lower >= -margin and upper <= margin:
        return "equivalent"
    return "unresolved"


def fixed_b_sweep(
    scores_a: ArrayLike,
    scores_b: ArrayLike,
    y: ArrayLike,
    *,
    grid: tuple[int, ...],
    margin: float,
    alpha: float,
    seed: int | np.random.SeedSequence,
) -> tuple[FixedBResult, ...]:
    if not grid:
        msg = "grid must be non-empty"
        raise ValueError(msg)
    if any(b <= 0 for b in grid):
        msg = "grid entries must be positive"
        raise ValueError(msg)

    max_b = max(grid)
    bootstrap = paired_bootstrap_deltas(scores_a, scores_b, y, draws=max_b, seed=seed)
    results = []
    for b in grid:
        deltas = bootstrap.deltas[:b]
        lower, upper = np.percentile(
            deltas,
            [100.0 * alpha / 2.0, 100.0 * (1.0 - alpha / 2.0)],
        )
        results.append(
            FixedBResult(
                b=b,
                decision=decision_from_interval(float(lower), float(upper), margin=margin),
                interval=(float(lower), float(upper)),
                draws_consumed=b,
            )
        )
    return tuple(results)


def false_stop_rate(
    decisions: tuple[SweepDecision, ...],
    reference_decisions: tuple[Decision, ...],
) -> float:
    if len(decisions) != len(reference_decisions):
        msg = "decisions and reference_decisions must have the same length"
        raise ValueError(msg)
    scored = [
        decision != "unresolved" and decision != reference
        for decision, reference in zip(decisions, reference_decisions, strict=True)
    ]
    if not scored:
        raise UnresolvedReferenceError("no scored decisions")
    return float(np.mean(scored))


def pareto_verdict(
    *,
    adaptive_false_stop_rate: float,
    adaptive_draws: tuple[int, ...],
    fixed_false_stop_rates: dict[int, float],
) -> ParetoResult:
    if not adaptive_draws:
        msg = "adaptive_draws must be non-empty"
        raise ValueError(msg)
    adaptive_median = float(np.median(adaptive_draws))
    dominated = tuple(
        b
        for b, fixed_rate in sorted(fixed_false_stop_rates.items())
        if b < adaptive_median and fixed_rate <= adaptive_false_stop_rate
    )
    best_fixed = min(dominated) if dominated else None
    savings = float(best_fixed / adaptive_median) if best_fixed is not None else 0.0
    return ParetoResult(
        dominated_fixed_b=dominated,
        best_savings_ratio=savings,
        adaptive_median_draws=adaptive_median,
        fixed_best_median_draws=float(best_fixed) if best_fixed is not None else None,
    )
