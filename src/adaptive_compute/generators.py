"""Deterministic synthetic battery for the fixed-budget reference."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

Scores = tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.int_]]
Generator = Callable[["GeneratorParams", np.random.Generator], Scores]


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
            signal_a=1.25,
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
