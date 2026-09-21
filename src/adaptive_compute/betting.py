"""Waudby-Smith--Ramdas betting confidence sequence for bounded means."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray


def _mean_grid(grid_size: int) -> NDArray[np.float64]:
    if grid_size < 3:
        msg = "grid_size must be at least 3"
        raise ValueError(msg)
    return np.linspace(0.0, 1.0, grid_size, dtype=np.float64)


def _lambda_grid(
    *,
    grid: NDArray[np.float64],
    past_mean: float,
    past_variance: float,
    c: float,
) -> NDArray[np.float64]:
    diff = past_mean - grid
    raw = np.abs(diff) / (past_variance + diff * diff)
    cap = c / np.maximum(grid, 1.0 - grid)
    return np.minimum(raw, cap)


def hedged_capital_path(
    values: ArrayLike,
    *,
    m: float,
    c: float = 0.5,
) -> NDArray[np.float64]:
    """Return the hedged capital process at one candidate mean in X-space."""

    samples = _validated_x_values(values)
    if not 0.0 <= m <= 1.0:
        msg = "m must lie in [0, 1]"
        raise ValueError(msg)
    if not 0.0 < c < 1.0:
        msg = "c must be between 0 and 1"
        raise ValueError(msg)

    capital_plus = 1.0
    capital_minus = 1.0
    path = np.empty(samples.size, dtype=np.float64)
    past_mean = 0.5
    m2 = 0.0
    count = 0
    for index, sample in enumerate(samples):
        if count < 2:
            lambda_value = 0.0
        else:
            past_variance = max(m2 / (count - 1), 1e-6)
            lambda_value = float(
                _lambda_grid(
                    grid=np.array([m], dtype=np.float64),
                    past_mean=past_mean,
                    past_variance=past_variance,
                    c=c,
                )[0]
            )
        centered = sample - m
        capital_plus *= 1.0 + lambda_value * centered
        capital_minus *= 1.0 - lambda_value * centered
        path[index] = 0.5 * (capital_plus + capital_minus)

        count += 1
        delta = sample - past_mean
        past_mean += delta / count
        m2 += delta * (sample - past_mean)
    return path


def betting_cs_bounds(
    values: ArrayLike,
    *,
    alpha: float,
    grid_size: int = 401,
    c: float = 0.5,
) -> tuple[float, float]:
    """Return a WSR hedged-capital confidence sequence for a mean in [-1, 1]."""

    samples_delta = np.asarray(values, dtype=np.float64)
    if samples_delta.ndim != 1 or samples_delta.size == 0:
        msg = "values must be a non-empty one-dimensional array"
        raise ValueError(msg)
    if not 0.0 < alpha < 1.0:
        msg = "alpha must be between 0 and 1"
        raise ValueError(msg)
    if not 0.0 < c < 1.0:
        msg = "c must be between 0 and 1"
        raise ValueError(msg)
    if np.any(samples_delta < -1.0) or np.any(samples_delta > 1.0):
        msg = "values must lie in [-1, 1]"
        raise ValueError(msg)

    state = BettingCSState(grid=_mean_grid(grid_size), c=c)
    state.update_delta(samples_delta)
    return state.bounds(alpha=alpha)


@dataclass
class BettingCSState:
    grid: NDArray[np.float64]
    c: float = 0.5

    def __post_init__(self) -> None:
        if self.grid.ndim != 1 or self.grid.size == 0:
            msg = "grid must be a non-empty one-dimensional array"
            raise ValueError(msg)
        if np.any(self.grid < 0.0) or np.any(self.grid > 1.0):
            msg = "grid must lie in [0, 1]"
            raise ValueError(msg)
        if not 0.0 < self.c < 1.0:
            msg = "c must be between 0 and 1"
            raise ValueError(msg)
        self.capital_plus = np.ones(self.grid.size, dtype=np.float64)
        self.capital_minus = np.ones(self.grid.size, dtype=np.float64)
        self.max_capital = np.ones(self.grid.size, dtype=np.float64)
        self.past_mean = 0.5
        self.m2 = 0.0
        self.count = 0

    def update_delta(self, values: ArrayLike) -> None:
        samples_delta = np.asarray(values, dtype=np.float64)
        if samples_delta.ndim != 1 or samples_delta.size == 0:
            msg = "values must be a non-empty one-dimensional array"
            raise ValueError(msg)
        if np.any(samples_delta < -1.0) or np.any(samples_delta > 1.0):
            msg = "values must lie in [-1, 1]"
            raise ValueError(msg)
        self.update_x((samples_delta + 1.0) / 2.0)

    def update_x(self, samples: NDArray[np.float64]) -> None:
        for sample in samples:
            if self.count < 2:
                lambdas = np.zeros(self.grid.size, dtype=np.float64)
            else:
                past_variance = max(self.m2 / (self.count - 1), 1e-6)
                lambdas = _lambda_grid(
                    grid=self.grid,
                    past_mean=self.past_mean,
                    past_variance=past_variance,
                    c=self.c,
                )
            centered = sample - self.grid
            self.capital_plus *= 1.0 + lambdas * centered
            self.capital_minus *= 1.0 - lambdas * centered
            self.max_capital = np.maximum(
                self.max_capital,
                0.5 * (self.capital_plus + self.capital_minus),
            )

            self.count += 1
            delta = sample - self.past_mean
            self.past_mean += delta / self.count
            self.m2 += delta * (sample - self.past_mean)

    def bounds(self, *, alpha: float) -> tuple[float, float]:
        if not 0.0 < alpha < 1.0:
            msg = "alpha must be between 0 and 1"
            raise ValueError(msg)
        survivors = self.grid[self.max_capital < 1.0 / alpha]
        if survivors.size == 0:
            return -1.0, 1.0

        # ponytail: this interval is the convex hull of surviving grid means,
        # valid exactly at grid points and conservative in practice with the
        # 401-point grid. If a future unit needs arbitrary non-grid means,
        # upgrade to continuous inversion or pad by one grid cell.
        lower = float(2.0 * survivors[0] - 1.0)
        upper = float(2.0 * survivors[-1] - 1.0)
        return max(-1.0, lower), min(1.0, upper)


def _running_max_hedged_capital(
    samples: NDArray[np.float64],
    *,
    grid: NDArray[np.float64],
    c: float,
) -> NDArray[np.float64]:
    capital_plus = np.ones(grid.size, dtype=np.float64)
    capital_minus = np.ones(grid.size, dtype=np.float64)
    max_capital = np.ones(grid.size, dtype=np.float64)
    past_mean = 0.5
    m2 = 0.0
    count = 0

    for sample in samples:
        if count < 2:
            lambdas = np.zeros(grid.size, dtype=np.float64)
        else:
            past_variance = max(m2 / (count - 1), 1e-6)
            lambdas = _lambda_grid(
                grid=grid,
                past_mean=past_mean,
                past_variance=past_variance,
                c=c,
            )
        centered = sample - grid
        capital_plus *= 1.0 + lambdas * centered
        capital_minus *= 1.0 - lambdas * centered
        max_capital = np.maximum(max_capital, 0.5 * (capital_plus + capital_minus))

        count += 1
        delta = sample - past_mean
        past_mean += delta / count
        m2 += delta * (sample - past_mean)
    return max_capital


def _validated_x_values(values: ArrayLike) -> NDArray[np.float64]:
    samples = np.asarray(values, dtype=np.float64)
    if samples.ndim != 1 or samples.size == 0:
        msg = "values must be a non-empty one-dimensional array"
        raise ValueError(msg)
    if np.any(samples < 0.0) or np.any(samples > 1.0):
        msg = "values must lie in [0, 1]"
        raise ValueError(msg)
    return samples
