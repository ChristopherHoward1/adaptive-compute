import numpy as np

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
