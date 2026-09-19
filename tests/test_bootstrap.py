import numpy as np

from adaptive_compute.bootstrap import paired_bootstrap_deltas
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
