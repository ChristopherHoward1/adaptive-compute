import contextlib
import io

import numpy as np

from adaptive_compute import eval as eval_module
from adaptive_compute.bootstrap import adaptive_seed, paired_bootstrap_deltas, reference_seed
from adaptive_compute.generators import BATTERY, generate


def test_delta_draws_are_bit_identical_for_same_params_and_seed() -> None:
    params, _generator = BATTERY["heavy_tailed"]
    scores_a, scores_b, y = generate(params)

    first = paired_bootstrap_deltas(scores_a, scores_b, y, draws=60, seed=777)
    second = paired_bootstrap_deltas(scores_a, scores_b, y, draws=60, seed=777)

    assert np.array_equal(first.deltas, second.deltas)


def test_reference_and_future_adaptive_branches_are_distinct() -> None:
    params, _generator = BATTERY["small_effect"]
    scores_a, scores_b, y = generate(params)
    ref_seed = reference_seed(777)
    adapt_seed = adaptive_seed(777)

    reference = paired_bootstrap_deltas(scores_a, scores_b, y, draws=60, seed=ref_seed)
    adaptive = paired_bootstrap_deltas(scores_a, scores_b, y, draws=60, seed=adapt_seed)

    assert ref_seed.spawn_key != adapt_seed.spawn_key
    assert not np.array_equal(reference.deltas, adaptive.deltas)


def test_eval_check_fails_when_replay_is_perturbed(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    original = eval_module.paired_bootstrap_deltas
    calls = 0

    def perturbed(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        result = original(*args, **kwargs)
        if calls == 2:
            result.deltas[0] += 1.0
        return result

    monkeypatch.setattr(eval_module, "paired_bootstrap_deltas", perturbed)

    with contextlib.redirect_stderr(io.StringIO()):
        assert eval_module.main(["--check"]) == 1
