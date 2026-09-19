"""Paired bounded metrics for fixed evaluation sets."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]


def _as_float_vector(values: ArrayLike, name: str) -> FloatArray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1:
        msg = f"{name} must be a one-dimensional array"
        raise ValueError(msg)
    if array.size == 0:
        msg = f"{name} must be non-empty"
        raise ValueError(msg)
    if not np.all(np.isfinite(array)):
        msg = f"{name} must contain only finite values"
        raise ValueError(msg)
    return array


def _as_binary_labels(y: ArrayLike) -> NDArray[np.int_]:
    labels = np.asarray(y)
    if labels.ndim != 1:
        msg = "y must be a one-dimensional array"
        raise ValueError(msg)
    if labels.size == 0:
        msg = "y must be non-empty"
        raise ValueError(msg)
    if not np.all((labels == 0) | (labels == 1)):
        msg = "y must contain only binary labels 0/1"
        raise ValueError(msg)
    return labels.astype(np.int_, copy=False)


def _midranks(values: FloatArray) -> FloatArray:
    order = np.argsort(values, kind="mergesort")
    sorted_values = values[order]
    ranks = np.empty(values.size, dtype=np.float64)

    start = 0
    while start < values.size:
        end = start + 1
        while end < values.size and sorted_values[end] == sorted_values[start]:
            end += 1
        rank = (start + 1 + end) / 2.0
        ranks[order[start:end]] = rank
        start = end

    return ranks


def auc(scores: ArrayLike, y: ArrayLike) -> float:
    """Compute binary AUC via the Mann-Whitney rank identity."""

    score_array = _as_float_vector(scores, "scores")
    labels = _as_binary_labels(y)
    if score_array.shape != labels.shape:
        msg = "scores and y must have the same shape"
        raise ValueError(msg)

    n_pos = int(np.sum(labels == 1))
    n_neg = int(labels.size - n_pos)
    if n_pos == 0 or n_neg == 0:
        msg = "AUC requires at least one positive and one negative label"
        raise ValueError(msg)

    ranks = _midranks(score_array)
    rank_sum_pos = float(np.sum(ranks[labels == 1]))
    return (rank_sum_pos - (n_pos * (n_pos + 1) / 2.0)) / (n_pos * n_neg)


def score(scores: ArrayLike, y: ArrayLike) -> float:
    """Default bounded score M for v0."""

    return auc(scores, y)


def delta(scores_a: ArrayLike, scores_b: ArrayLike, y: ArrayLike) -> float:
    """Compute paired metric difference M(A, E) - M(B, E)."""

    scores_a_array = _as_float_vector(scores_a, "scores_a")
    scores_b_array = _as_float_vector(scores_b, "scores_b")
    labels = _as_binary_labels(y)
    if scores_a_array.shape != scores_b_array.shape or scores_a_array.shape != labels.shape:
        msg = "scores_a, scores_b, and y must have the same shape"
        raise ValueError(msg)
    return score(scores_a_array, labels) - score(scores_b_array, labels)
