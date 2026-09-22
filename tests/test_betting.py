import numpy as np
import pytest

from adaptive_compute.adaptive import (
    adaptive_decision,
    decision_from_bounds,
    empirical_bernstein_bounds,
)
from adaptive_compute.betting import (
    _mean_grid,
    _running_max_hedged_capital,
    betting_cs_bounds,
    hedged_capital_path,
)
from adaptive_compute.bootstrap import adaptive_bootstrap_stream
from adaptive_compute.generators import BATTERY, generate
from adaptive_compute.reference import DEFAULT_ALPHA, DEFAULT_DELTA


def test_input_contract_matches_delta_space_bounds() -> None:
    invalid_inputs = (
        [],
        [[0.0]],
        [-1.1, 0.0],
        [0.0, 1.1],
    )
    for values in invalid_inputs:
        with pytest.raises(ValueError):
            betting_cs_bounds(values, alpha=DEFAULT_ALPHA)

    with pytest.raises(ValueError):
        betting_cs_bounds([0.0], alpha=0.0)
    with pytest.raises(ValueError):
        empirical_bernstein_bounds([0.0], alpha=0.0)

    lower, upper = betting_cs_bounds(np.zeros(64), alpha=DEFAULT_ALPHA)
    assert -1.0 <= lower <= upper <= 1.0


def test_predictable_bound_ignores_future_suffix_changes() -> None:
    prefix = np.array([-0.04, 0.02, 0.01, -0.03, 0.00, 0.03] * 12)
    future_a = np.linspace(-1.0, 1.0, 64)
    future_b = future_a[::-1] * 0.25
    first = (np.concatenate([prefix, future_a]) + 1.0) / 2.0
    second = (np.concatenate([prefix, future_b]) + 1.0) / 2.0
    prefix_x = (prefix + 1.0) / 2.0

    assert not np.array_equal(future_a, future_b)
    for mean in (0.25, 0.5, 0.75):
        prefix_path = hedged_capital_path(prefix_x, m=mean)
        assert np.array_equal(hedged_capital_path(first, m=mean)[: prefix.size], prefix_path)
        assert np.array_equal(hedged_capital_path(second, m=mean)[: prefix.size], prefix_path)


def test_capital_sanity_under_centered_null_stream() -> None:
    root = np.random.SeedSequence(20260921)
    final_capitals = []
    crossings = 0
    for seed_sequence in root.spawn(2000):
        rng = np.random.default_rng(seed_sequence)
        samples = rng.binomial(1, 0.5, size=16).astype(np.float64)
        path = hedged_capital_path(samples, m=0.5)
        final_capitals.append(float(path[-1]))
        crossings += int(np.max(path) >= 1.0 / DEFAULT_ALPHA)

    assert np.mean(final_capitals) == pytest.approx(1.0, abs=0.08)
    assert crossings <= 20


def test_fixed_seed_coverage_sanity_has_explicit_miss_bound() -> None:
    root = np.random.SeedSequence(20260922)
    true_delta = 0.24
    misses = 0
    for seed_sequence in root.spawn(300):
        rng = np.random.default_rng(seed_sequence)
        x_samples = rng.binomial(1, 0.62, size=192).astype(np.float64)
        lower, upper = betting_cs_bounds(2.0 * x_samples - 1.0, alpha=DEFAULT_ALPHA)
        misses += int(not lower <= true_delta <= upper)

    assert misses <= 20


def test_rescale_round_trip_matches_x_space_grid_mapping() -> None:
    deltas = np.array([-0.2, 0.0, 0.1, -0.1, 0.05, -0.05])
    grid = _mean_grid(401)
    max_capital = _running_max_hedged_capital((deltas + 1.0) / 2.0, grid=grid, c=0.5)
    survivors = grid[max_capital < 1.0 / DEFAULT_ALPHA]
    expected = (float(2.0 * survivors[0] - 1.0), float(2.0 * survivors[-1] - 1.0))

    assert betting_cs_bounds(deltas, alpha=DEFAULT_ALPHA) == expected


def test_drop_in_stream_equivalence_for_fixed_batch_prefix() -> None:
    params, _generator = BATTERY["small_effect"]
    scores_a, scores_b, y = generate(params)
    seed = 90_000 + params.seed
    eb = adaptive_decision(
        scores_a,
        scores_b,
        y,
        margin=DEFAULT_DELTA,
        alpha=DEFAULT_ALPHA,
        b=64,
        b_max=2048,
        seed=seed,
        instrument="eb",
    )
    betting = adaptive_decision(
        scores_a,
        scores_b,
        y,
        margin=DEFAULT_DELTA,
        alpha=DEFAULT_ALPHA,
        b=64,
        b_max=2048,
        seed=seed,
        instrument="betting",
    )
    replay_stream = adaptive_bootstrap_stream(
        scores_a,
        scores_b,
        y,
        batch_draws=64,
        max_draws=2048,
        seed=seed,
    )
    replayed = np.concatenate([batch.deltas for batch in replay_stream])

    eb_consumed = _replay_consumed_deltas(replayed, instrument="eb", b=64, b_max=2048)
    betting_consumed = _replay_consumed_deltas(
        replayed,
        instrument="betting",
        b=64,
        b_max=2048,
    )

    assert np.array_equal(eb_consumed, replayed[: eb.draws_consumed])
    assert np.array_equal(betting_consumed, replayed[: betting.draws_consumed])
    assert _replay_decision(replayed, instrument="eb", b=64, b_max=2048) == (
        eb.decision,
        eb.draws_consumed,
    )
    assert _replay_decision(replayed, instrument="betting", b=64, b_max=2048) == (
        betting.decision,
        betting.draws_consumed,
    )


def test_betting_resolves_equivalent_case_faster_than_eb() -> None:
    params, _generator = BATTERY["small_effect"]
    scores_a, scores_b, y = generate(params)
    seed = 90_000 + params.seed

    eb = adaptive_decision(
        scores_a,
        scores_b,
        y,
        margin=DEFAULT_DELTA,
        alpha=DEFAULT_ALPHA,
        b=64,
        b_max=2048,
        seed=seed,
        instrument="eb",
    )
    betting = adaptive_decision(
        scores_a,
        scores_b,
        y,
        margin=DEFAULT_DELTA,
        alpha=DEFAULT_ALPHA,
        b=64,
        b_max=2048,
        seed=seed,
        instrument="betting",
    )

    assert eb.decision == "equivalent"
    assert betting.decision == "equivalent"
    assert betting.draws_consumed < eb.draws_consumed


def _replay_decision(
    deltas: np.ndarray,
    *,
    instrument: str,
    b: int,
    b_max: int,
) -> tuple[str, int]:
    max_looks = int(np.ceil(b_max / b))
    for draws in range(b, b_max + b, b):
        prefix = deltas[:draws]
        if instrument == "eb":
            bounds = empirical_bernstein_bounds(
                prefix,
                alpha=DEFAULT_ALPHA,
                max_looks=max_looks,
            )
        else:
            bounds = betting_cs_bounds(prefix, alpha=DEFAULT_ALPHA)
        decision = decision_from_bounds(bounds[0], bounds[1], margin=DEFAULT_DELTA)
        if decision is not None:
            return decision, draws
    return "abstain", b_max


def _replay_consumed_deltas(
    deltas: np.ndarray,
    *,
    instrument: str,
    b: int,
    b_max: int,
) -> np.ndarray:
    _decision, draws = _replay_decision(deltas, instrument=instrument, b=b, b_max=b_max)
    return deltas[:draws]
