"""Adaptive bootstrap stopping with an anytime empirical-Bernstein CS.

The controller maintains a confidence sequence for the bounded mean
``E*[Δ*]`` where each bootstrap draw ``Δ*`` is in ``[-1, 1]``. The interval uses
an empirical-Bernstein style anytime boundary for bounded observations, following
the confidence-sequence framing of Howard et al. (2021), "Time-uniform,
nonparametric, nonasymptotic confidence sequences."
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike

from adaptive_compute.bootstrap import adaptive_bootstrap_stream

AdaptiveDecision = Literal["A_better", "B_better", "equivalent", "abstain"]


@dataclass(frozen=True)
class AdaptiveResult:
    decision: AdaptiveDecision
    draws_consumed: int
    n_batches: int
    final_bounds: tuple[float, float]


def empirical_bernstein_bounds(
    values: ArrayLike,
    *,
    alpha: float,
    max_looks: int = 1,
) -> tuple[float, float]:
    """Return a finite-horizon empirical-Bernstein CS for a mean in [-1, 1]."""

    samples = np.asarray(values, dtype=np.float64)
    if samples.ndim != 1 or samples.size == 0:
        msg = "values must be a non-empty one-dimensional array"
        raise ValueError(msg)
    if not 0.0 < alpha < 1.0:
        msg = "alpha must be between 0 and 1"
        raise ValueError(msg)
    if max_looks <= 0:
        msg = "max_looks must be positive"
        raise ValueError(msg)
    if np.any(samples < -1.0) or np.any(samples > 1.0):
        msg = "values must lie in [-1, 1]"
        raise ValueError(msg)

    n = samples.size
    mean = float(np.mean(samples))
    variance = float(np.var(samples, ddof=1)) if n > 1 else 0.25
    log_term = float(np.log((2.0 * max_looks) / alpha))
    radius = float(
        np.sqrt((2.0 * variance * log_term) / n) + (14.0 * log_term) / (3.0 * max(1, n - 1))
    )
    return max(-1.0, mean - radius), min(1.0, mean + radius)


def decision_from_bounds(
    lower: float,
    upper: float,
    *,
    margin: float,
) -> AdaptiveDecision | None:
    if lower > margin:
        return "A_better"
    if upper < -margin:
        return "B_better"
    if lower >= -margin and upper <= margin:
        return "equivalent"
    return None


def adaptive_decision(
    scores_a: ArrayLike,
    scores_b: ArrayLike,
    y: ArrayLike,
    *,
    margin: float,
    alpha: float,
    b: int,
    b_max: int,
    seed: int | np.random.SeedSequence,
) -> AdaptiveResult:
    """Run the blind adaptive procedure."""

    if margin <= 0.0:
        msg = "margin must be positive"
        raise ValueError(msg)
    if not 0.0 < alpha < 1.0:
        msg = "alpha must be between 0 and 1"
        raise ValueError(msg)
    if b <= 0:
        msg = "b must be positive"
        raise ValueError(msg)
    if b_max <= 0:
        msg = "b_max must be positive"
        raise ValueError(msg)

    stream = adaptive_bootstrap_stream(
        scores_a,
        scores_b,
        y,
        batch_draws=b,
        max_draws=b_max,
        seed=seed,
    )
    values = np.empty(b_max, dtype=np.float64)
    draws = 0
    batches = 0
    bounds = (-1.0, 1.0)
    max_looks = ceil(b_max / b)

    while draws < b_max:
        batch = next(stream)
        current = batch.draws_consumed
        batch_values = batch.deltas

        values[draws : draws + current] = batch_values[:current]
        draws += current
        batches += 1
        bounds = empirical_bernstein_bounds(values[:draws], alpha=alpha, max_looks=max_looks)
        decision = decision_from_bounds(bounds[0], bounds[1], margin=margin)
        if decision is not None:
            return AdaptiveResult(
                decision=decision,
                draws_consumed=draws,
                n_batches=batches,
                final_bounds=bounds,
            )

    return AdaptiveResult(
        decision="abstain",
        draws_consumed=draws,
        n_batches=batches,
        final_bounds=bounds,
    )
