"""Draw-accounted paired bootstrap over a frozen evaluation set."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from adaptive_compute.metrics import delta


@dataclass(frozen=True)
class BootstrapResult:
    deltas: NDArray[np.float64]
    draws_consumed: int
    seed_spawn_key: tuple[int, ...]


def seed_branches(seed: int | np.random.SeedSequence) -> tuple[np.random.SeedSequence, ...]:
    """Return independent reference/adaptive branches from a root seed."""

    root = seed if isinstance(seed, np.random.SeedSequence) else np.random.SeedSequence(seed)
    return tuple(root.spawn(2))


def reference_seed(seed: int | np.random.SeedSequence) -> np.random.SeedSequence:
    return seed_branches(seed)[0]


def adaptive_seed(seed: int | np.random.SeedSequence) -> np.random.SeedSequence:
    return seed_branches(seed)[1]


def paired_bootstrap_deltas(
    scores_a: ArrayLike,
    scores_b: ArrayLike,
    y: ArrayLike,
    *,
    draws: int,
    seed: int | np.random.SeedSequence,
    batch_size: int = 128,
) -> BootstrapResult:
    """Resample rows with replacement and recompute delta for each resample."""

    if draws < 0:
        msg = "draws must be non-negative"
        raise ValueError(msg)
    if batch_size <= 0:
        msg = "batch_size must be positive"
        raise ValueError(msg)

    scores_a_array = np.asarray(scores_a, dtype=np.float64)
    scores_b_array = np.asarray(scores_b, dtype=np.float64)
    y_array = np.asarray(y, dtype=np.int_)
    if scores_a_array.ndim != 1 or scores_b_array.ndim != 1 or y_array.ndim != 1:
        msg = "scores_a, scores_b, and y must be one-dimensional"
        raise ValueError(msg)
    if scores_a_array.shape != scores_b_array.shape or scores_a_array.shape != y_array.shape:
        msg = "scores_a, scores_b, and y must have the same shape"
        raise ValueError(msg)

    seed_sequence = seed if isinstance(seed, np.random.SeedSequence) else reference_seed(seed)
    rng = np.random.default_rng(seed_sequence)
    values = np.empty(draws, dtype=np.float64)
    n = y_array.size

    written = 0
    while written < draws:
        current = min(batch_size, draws - written)
        indices = rng.integers(0, n, size=(current, n), endpoint=False)
        for offset, sample_indices in enumerate(indices):
            values[written + offset] = delta(
                scores_a_array[sample_indices],
                scores_b_array[sample_indices],
                y_array[sample_indices],
            )
        written += current

    return BootstrapResult(
        deltas=values,
        draws_consumed=draws,
        seed_spawn_key=tuple(seed_sequence.spawn_key),
    )
