"""Draw-accounted paired bootstrap over a frozen evaluation set."""

from __future__ import annotations

from collections.abc import Iterator
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
    """Return independent reference/adaptive branches from a root seed.

    A caller-supplied ``SeedSequence`` is cloned before spawning: ``spawn``
    advances the sequence's ``n_children_spawned`` counter, so spawning the
    original object would make a second call with the same object produce
    different children. Cloning from ``(entropy, spawn_key, pool_size)`` with a
    fresh counter keeps replay bit-identical when the same object is reused, and
    never mutates the caller's object.
    """

    root = seed if isinstance(seed, np.random.SeedSequence) else np.random.SeedSequence(seed)
    clone = np.random.SeedSequence(
        entropy=root.entropy,
        spawn_key=root.spawn_key,
        pool_size=root.pool_size,
    )
    return tuple(clone.spawn(2))


def reference_seed(seed: int | np.random.SeedSequence) -> np.random.SeedSequence:
    return seed_branches(seed)[0]


def adaptive_seed(seed: int | np.random.SeedSequence) -> np.random.SeedSequence:
    return seed_branches(seed)[1]


def _validated_arrays(
    scores_a: ArrayLike,
    scores_b: ArrayLike,
    y: ArrayLike,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.int_]]:
    scores_a_array = np.asarray(scores_a, dtype=np.float64)
    scores_b_array = np.asarray(scores_b, dtype=np.float64)
    y_array = np.asarray(y, dtype=np.int_)
    if scores_a_array.ndim != 1 or scores_b_array.ndim != 1 or y_array.ndim != 1:
        msg = "scores_a, scores_b, and y must be one-dimensional"
        raise ValueError(msg)
    if scores_a_array.shape != scores_b_array.shape or scores_a_array.shape != y_array.shape:
        msg = "scores_a, scores_b, and y must have the same shape"
        raise ValueError(msg)
    if y_array.size == 0:
        msg = "scores_a, scores_b, and y must be non-empty"
        raise ValueError(msg)
    return scores_a_array, scores_b_array, y_array


def _resample_deltas(
    scores_a: NDArray[np.float64],
    scores_b: NDArray[np.float64],
    y: NDArray[np.int_],
    *,
    rng: np.random.Generator,
    draws: int,
    batch_size: int,
) -> NDArray[np.float64]:
    values = np.empty(draws, dtype=np.float64)
    n = y.size

    written = 0
    while written < draws:
        current = min(batch_size, draws - written)
        indices = rng.integers(0, n, size=(current, n), endpoint=False)
        for offset, sample_indices in enumerate(indices):
            sample_y = y[sample_indices]
            if np.all(sample_y == sample_y[0]):
                values[written + offset] = 0.0
                continue
            values[written + offset] = delta(
                scores_a[sample_indices],
                scores_b[sample_indices],
                sample_y,
            )
        written += current
    return values


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

    scores_a_array, scores_b_array, y_array = _validated_arrays(scores_a, scores_b, y)

    seed_sequence = reference_seed(seed)
    rng = np.random.default_rng(seed_sequence)
    values = _resample_deltas(
        scores_a_array,
        scores_b_array,
        y_array,
        rng=rng,
        draws=draws,
        batch_size=batch_size,
    )
    return BootstrapResult(
        deltas=values,
        draws_consumed=draws,
        seed_spawn_key=tuple(seed_sequence.spawn_key),
    )


def adaptive_bootstrap_stream(
    scores_a: ArrayLike,
    scores_b: ArrayLike,
    y: ArrayLike,
    *,
    batch_draws: int,
    max_draws: int | None = None,
    seed: int | np.random.SeedSequence,
) -> Iterator[BootstrapResult]:
    """Yield sequential adaptive-branch bootstrap batches from one RNG."""

    if batch_draws <= 0:
        msg = "batch_draws must be positive"
        raise ValueError(msg)
    if max_draws is not None and max_draws < 0:
        msg = "max_draws must be non-negative"
        raise ValueError(msg)

    scores_a_array, scores_b_array, y_array = _validated_arrays(scores_a, scores_b, y)
    seed_sequence = adaptive_seed(seed)
    rng = np.random.default_rng(seed_sequence)
    yielded = 0
    while max_draws is None or yielded < max_draws:
        current = batch_draws if max_draws is None else min(batch_draws, max_draws - yielded)
        values = _resample_deltas(
            scores_a_array,
            scores_b_array,
            y_array,
            rng=rng,
            draws=current,
            batch_size=current,
        )
        yielded += current
        yield BootstrapResult(
            deltas=values,
            draws_consumed=current,
            seed_spawn_key=tuple(seed_sequence.spawn_key),
        )
