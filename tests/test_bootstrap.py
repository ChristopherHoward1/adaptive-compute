import numpy as np
import pytest

from adaptive_compute.bootstrap import adaptive_bootstrap_stream, paired_bootstrap_deltas
from adaptive_compute.generators import BATTERY, generate


def test_draw_accounting_reports_exact_resamples() -> None:
    params, _generator = BATTERY["small_effect"]
    scores_a, scores_b, y = generate(params)

    result = paired_bootstrap_deltas(scores_a, scores_b, y, draws=17, seed=1234, batch_size=5)

    assert result.draws_consumed == 17
    assert result.deltas.shape == (17,)


def test_same_seed_replays_draws_bit_for_bit() -> None:
    params, _generator = BATTERY["small_effect"]
    scores_a, scores_b, y = generate(params)

    first = paired_bootstrap_deltas(scores_a, scores_b, y, draws=40, seed=1234)
    second = paired_bootstrap_deltas(scores_a, scores_b, y, draws=40, seed=1234)

    assert np.array_equal(first.deltas, second.deltas)


def test_seed_sequence_input_still_consumes_reference_branch() -> None:
    params, _generator = BATTERY["small_effect"]
    scores_a, scores_b, y = generate(params)
    result = paired_bootstrap_deltas(
        scores_a,
        scores_b,
        y,
        draws=40,
        seed=np.random.SeedSequence(1234),
    )
    expected = paired_bootstrap_deltas(scores_a, scores_b, y, draws=40, seed=1234)

    assert result.seed_spawn_key == (0,)
    assert expected.seed_spawn_key == (0,)
    assert np.array_equal(result.deltas, expected.deltas)


def test_adaptive_stream_uses_adaptive_branch_and_replays_seedsequence() -> None:
    params, _generator = BATTERY["small_effect"]
    scores_a, scores_b, y = generate(params)
    seed_sequence = np.random.SeedSequence(4321)

    first = list(
        adaptive_bootstrap_stream(
            scores_a,
            scores_b,
            y,
            batch_draws=7,
            max_draws=20,
            seed=seed_sequence,
        )
    )
    second = list(
        adaptive_bootstrap_stream(
            scores_a,
            scores_b,
            y,
            batch_draws=7,
            max_draws=20,
            seed=seed_sequence,
        )
    )

    assert [batch.draws_consumed for batch in first] == [7, 7, 6]
    assert sum(batch.draws_consumed for batch in first) == 20
    assert all(batch.seed_spawn_key == (1,) for batch in first)
    assert all(np.array_equal(left.deltas, right.deltas) for left, right in zip(first, second))


def test_degenerate_resample_counts_as_zero_delta_draw() -> None:
    scores_a = np.array([0.0, 1.0, 2.0])
    scores_b = np.array([0.5, 1.5, 2.5])
    y = np.array([1, 1, 1])

    result = paired_bootstrap_deltas(scores_a, scores_b, y, draws=5, seed=99)

    assert result.draws_consumed == 5
    assert np.array_equal(result.deltas, np.zeros(5))


def test_reference_resampler_rejects_malformed_inputs() -> None:
    scores_a = np.array([0.1, 0.2, 0.3])
    scores_b = np.array([0.2, 0.3, 0.4])

    with pytest.raises(ValueError, match="binary labels"):
        paired_bootstrap_deltas(scores_a, scores_b, np.array([0, 2, 1]), draws=3, seed=11)

    with pytest.raises(ValueError, match="finite"):
        paired_bootstrap_deltas(
            np.array([0.1, np.nan, 0.3]),
            scores_b,
            np.array([0, 1, 1]),
            draws=3,
            seed=11,
        )


def test_adaptive_stream_rejects_malformed_inputs() -> None:
    scores_a = np.array([0.1, 0.2, 0.3])
    scores_b = np.array([0.2, 0.3, 0.4])

    with pytest.raises(ValueError, match="binary labels"):
        next(
            adaptive_bootstrap_stream(
                scores_a,
                scores_b,
                np.array([0, 2, 1]),
                batch_draws=3,
                max_draws=3,
                seed=11,
            )
        )

    with pytest.raises(ValueError, match="finite"):
        next(
            adaptive_bootstrap_stream(
                scores_a,
                np.array([0.2, np.inf, 0.4]),
                np.array([0, 1, 1]),
                batch_draws=3,
                max_draws=3,
                seed=11,
            )
        )


def test_reference_delta_array_matches_recorded_pre_optimization_baseline() -> None:
    params, _generator = BATTERY["heavy_tailed"]
    scores_a, scores_b, y = generate(params)

    result = paired_bootstrap_deltas(scores_a, scores_b, y, draws=12, seed=777, batch_size=5)

    expected = np.array(
        [
            float.fromhex("0x1.713d055da2340p-4"),
            float.fromhex("0x1.6eae8f2b5f090p-4"),
            float.fromhex("0x1.22f347bcd7e30p-4"),
            float.fromhex("0x1.0d689e2d4145cp-3"),
            float.fromhex("0x1.9aed6a9264e20p-4"),
            float.fromhex("0x1.9b419e145fe58p-4"),
            float.fromhex("0x1.1f29536f9b2b0p-3"),
            float.fromhex("0x1.0de614a909f44p-3"),
            float.fromhex("0x1.c9ee500257568p-4"),
            float.fromhex("0x1.18f0208e0a5acp-3"),
            float.fromhex("0x1.007f17007f170p-3"),
            float.fromhex("0x1.2943df2af5274p-3"),
        ],
        dtype=np.float64,
    )
    assert np.array_equal(result.deltas, expected)
