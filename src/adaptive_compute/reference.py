"""Fixed-budget percentile-bootstrap reference decision."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray

from adaptive_compute.bootstrap import BootstrapResult, paired_bootstrap_deltas

Decision = Literal["A_better", "B_better", "equivalent"]
DEFAULT_DELTA = 0.05
DEFAULT_ALPHA = 0.05
DEFAULT_B_REF = 320


class UnresolvedReferenceError(RuntimeError):
    """Raised when the fixed-budget interval does not resolve a reference decision."""


@dataclass(frozen=True)
class ReferenceResult:
    decision: Decision
    estimate: float
    interval: tuple[float, float]
    interval_method: str
    level: float
    draws_consumed: int
    deltas: NDArray[np.float64]


def decision_from_delta(delta: float, margin: float) -> Decision:
    if delta > margin:
        return "A_better"
    if delta < -margin:
        return "B_better"
    return "equivalent"


def _decision_from_interval(
    lower: float,
    upper: float,
    margin: float,
    b_ref: int,
) -> Decision:
    if lower > margin:
        return "A_better"
    if upper < -margin:
        return "B_better"
    if lower >= -margin and upper <= margin:
        return "equivalent"

    msg = (
        f"reference interval [{lower:.12g}, {upper:.12g}] straddles ±δ={margin:.12g} "
        f"at B_ref={b_ref}; case is boundary-adjacent or B_ref under-sized"
    )
    raise UnresolvedReferenceError(msg)


def fixed_budget_reference(
    scores_a: ArrayLike,
    scores_b: ArrayLike,
    y: ArrayLike,
    *,
    margin: float = DEFAULT_DELTA,
    alpha: float = DEFAULT_ALPHA,
    b_ref: int = DEFAULT_B_REF,
    seed: int | np.random.SeedSequence,
    batch_size: int = 128,
) -> ReferenceResult:
    if margin <= 0.0:
        msg = "margin must be positive"
        raise ValueError(msg)
    if not 0.0 < alpha < 1.0:
        msg = "alpha must be between 0 and 1"
        raise ValueError(msg)
    if b_ref <= 0:
        msg = "b_ref must be positive"
        raise ValueError(msg)

    bootstrap: BootstrapResult = paired_bootstrap_deltas(
        scores_a,
        scores_b,
        y,
        draws=b_ref,
        seed=seed,
        batch_size=batch_size,
    )
    lower, upper = np.percentile(
        bootstrap.deltas,
        [100.0 * alpha / 2.0, 100.0 * (1.0 - alpha / 2.0)],
    )
    estimate = float(np.mean(bootstrap.deltas))
    return ReferenceResult(
        decision=_decision_from_interval(float(lower), float(upper), margin, b_ref),
        estimate=estimate,
        interval=(float(lower), float(upper)),
        interval_method="percentile",
        level=1.0 - alpha,
        draws_consumed=bootstrap.draws_consumed,
        deltas=bootstrap.deltas,
    )
