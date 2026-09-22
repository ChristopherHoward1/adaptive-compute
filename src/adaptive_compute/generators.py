"""Deterministic synthetic battery for the fixed-budget reference."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

Scores = tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.int_]]
Generator = Callable[["GeneratorParams", np.random.Generator], Scores]
EquivalencePosition = Literal["center", "offset"]
MixedEquivalenceCase = tuple[EquivalencePosition, int, Scores]


@dataclass(frozen=True)
class GeneratorParams:
    name: str
    n: int
    positive_rate: float
    signal_a: float
    signal_b: float
    noise_scale: float = 1.0
    seed: int = 0
    intended_stratum: str = "moderate"
    tail_df: float = 1.5


def _labels(n: int, positive_rate: float, rng: np.random.Generator) -> NDArray[np.int_]:
    if n < 2:
        msg = "n must be at least 2"
        raise ValueError(msg)
    if not 0.0 < positive_rate < 1.0:
        msg = "positive_rate must be between 0 and 1"
        raise ValueError(msg)

    n_pos = min(n - 1, max(1, int(round(n * positive_rate))))
    labels = np.zeros(n, dtype=np.int_)
    labels[:n_pos] = 1
    rng.shuffle(labels)
    return labels


def _normal_scores(
    y: NDArray[np.int_],
    signal: float,
    noise_scale: float,
    rng: np.random.Generator,
) -> NDArray[np.float64]:
    return signal * y + rng.normal(0.0, noise_scale, size=y.size)


def near_delta_boundary(params: GeneratorParams, rng: np.random.Generator) -> Scores:
    y = _labels(params.n, params.positive_rate, rng)
    shared = rng.normal(0.0, params.noise_scale, size=params.n)
    scores_b = params.signal_b * y + shared + rng.normal(0.0, 0.18, size=params.n)
    scores_a = params.signal_a * y + shared + rng.normal(0.0, 0.18, size=params.n)
    return scores_a.astype(np.float64), scores_b.astype(np.float64), y


def small_effect(params: GeneratorParams, rng: np.random.Generator) -> Scores:
    y = _labels(params.n, params.positive_rate, rng)
    shared = rng.normal(0.0, params.noise_scale, size=params.n)
    scores_b = params.signal_b * y + shared + rng.normal(0.0, 0.12, size=params.n)
    scores_a = params.signal_a * y + shared + rng.normal(0.0, 0.12, size=params.n)
    return scores_a.astype(np.float64), scores_b.astype(np.float64), y


def heavy_tailed(params: GeneratorParams, rng: np.random.Generator) -> Scores:
    y = _labels(params.n, params.positive_rate, rng)
    common = rng.standard_t(params.tail_df, size=params.n) * params.noise_scale
    scores_b = params.signal_b * y + common + rng.standard_t(params.tail_df, size=params.n) * 0.45
    scores_a = params.signal_a * y + common + rng.standard_t(params.tail_df, size=params.n) * 0.45
    return scores_a.astype(np.float64), scores_b.astype(np.float64), y


def rare_event_imbalance(params: GeneratorParams, rng: np.random.Generator) -> Scores:
    y = _labels(params.n, params.positive_rate, rng)
    shared = rng.normal(0.0, params.noise_scale, size=params.n)
    scores_b = params.signal_b * y + shared + rng.normal(0.0, 0.2, size=params.n)
    scores_a = params.signal_a * y + shared + rng.normal(0.0, 0.2, size=params.n)
    return scores_a.astype(np.float64), scores_b.astype(np.float64), y


def easy_lopsided(params: GeneratorParams, rng: np.random.Generator) -> Scores:
    y = _labels(params.n, params.positive_rate, rng)
    scores_b = _normal_scores(y, params.signal_b, params.noise_scale, rng)
    scores_a = _normal_scores(y, params.signal_a, params.noise_scale, rng)
    return scores_a.astype(np.float64), scores_b.astype(np.float64), y


def _calibrated_equivalence_case(
    *,
    seed: int,
    target_abs_delta: float,
    n: int,
    positive_rate: float,
    signal_b: float,
    noise_scale: float,
) -> Scores:
    from adaptive_compute.metrics import delta

    rng = np.random.default_rng(seed)
    y = _labels(n, positive_rate, rng)
    shared = rng.normal(0.0, noise_scale, size=n)
    scores_b_noise = rng.normal(0.0, 0.12, size=n)
    scores_a_noise = rng.normal(0.0, 0.12, size=n)
    scores_b = signal_b * y + shared + scores_b_noise

    lo = 0.0
    hi = 2.0
    best_delta = float("inf")
    best_scores_a = signal_b * y + shared + scores_a_noise
    for _ in range(22):
        gap = (lo + hi) / 2.0
        candidate = (signal_b + gap) * y + shared + scores_a_noise
        candidate_delta = delta(candidate, scores_b, y)
        if abs(abs(candidate_delta) - target_abs_delta) < abs(abs(best_delta) - target_abs_delta):
            best_delta = candidate_delta
            best_scores_a = candidate
        if abs(candidate_delta) < target_abs_delta:
            lo = gap
        else:
            hi = gap

    return best_scores_a.astype(np.float64), scores_b.astype(np.float64), y


def mixed_equivalence(
    *,
    seed: int,
    center: int,
    offset: int,
    max_abs_delta: float,
    center_abs_delta: float = 0.0,
    n: int = 720,
    positive_rate: float = 0.5,
    signal_b: float = 0.60,
    noise_scale: float = 0.45,
) -> tuple[MixedEquivalenceCase, ...]:
    """Build a deterministic, unregistered in-band equivalence position spread."""

    if center <= 0 or offset <= 0:
        msg = "center and offset counts must be positive"
        raise ValueError(msg)
    if not 0.0 <= center_abs_delta < max_abs_delta:
        msg = "center_abs_delta must be non-negative and below max_abs_delta"
        raise ValueError(msg)
    if n < 2:
        msg = "n must be at least 2"
        raise ValueError(msg)

    cases: list[MixedEquivalenceCase] = []
    for index in range(center):
        case_seed = seed + index
        cases.append(
            (
                "center",
                case_seed,
                _calibrated_equivalence_case(
                    seed=case_seed,
                    target_abs_delta=center_abs_delta,
                    n=n,
                    positive_rate=positive_rate,
                    signal_b=signal_b,
                    noise_scale=noise_scale,
                ),
            )
        )
    for index in range(offset):
        case_seed = seed + 1_000 + index
        cases.append(
            (
                "offset",
                case_seed,
                _calibrated_equivalence_case(
                    seed=case_seed,
                    target_abs_delta=max_abs_delta,
                    n=n,
                    positive_rate=positive_rate,
                    signal_b=signal_b,
                    noise_scale=noise_scale,
                ),
            )
        )
    return tuple(cases)


BATTERY: Mapping[str, tuple[GeneratorParams, Generator]] = {
    "near_delta_boundary": (
        GeneratorParams(
            name="near_delta_boundary",
            n=360,
            positive_rate=0.5,
            signal_a=0.82,
            signal_b=0.60,
            noise_scale=1.0,
            seed=1101,
            intended_stratum="boundary",
        ),
        near_delta_boundary,
    ),
    "small_effect": (
        GeneratorParams(
            name="small_effect",
            n=360,
            positive_rate=0.5,
            signal_a=0.62,
            signal_b=0.60,
            noise_scale=1.0,
            seed=1201,
            intended_stratum="equivalent",
        ),
        small_effect,
    ),
    "heavy_tailed": (
        GeneratorParams(
            name="heavy_tailed",
            n=420,
            positive_rate=0.45,
            signal_a=1.40,
            signal_b=0.42,
            noise_scale=1.0,
            seed=1301,
            intended_stratum="moderate",
            tail_df=1.4,
        ),
        heavy_tailed,
    ),
    "rare_event_imbalance": (
        GeneratorParams(
            name="rare_event_imbalance",
            n=520,
            positive_rate=0.04,
            signal_a=1.05,
            signal_b=0.42,
            noise_scale=1.0,
            seed=1401,
            intended_stratum="moderate",
        ),
        rare_event_imbalance,
    ),
    "easy_lopsided": (
        GeneratorParams(
            name="easy_lopsided",
            n=360,
            positive_rate=0.5,
            signal_a=2.00,
            signal_b=0.15,
            noise_scale=1.0,
            seed=1501,
            intended_stratum="easy",
        ),
        easy_lopsided,
    ),
}


def generate(params: GeneratorParams) -> Scores:
    """Instantiate a frozen evaluation set from params and its recorded seed."""

    try:
        generator = BATTERY[params.name][1]
    except KeyError as exc:
        msg = f"unknown generator: {params.name}"
        raise ValueError(msg) from exc
    return generator(params, np.random.default_rng(params.seed))
