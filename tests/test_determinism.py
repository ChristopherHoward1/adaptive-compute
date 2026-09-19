import contextlib
import io
from types import SimpleNamespace

import numpy as np

from adaptive_compute import eval as eval_module
from adaptive_compute.bootstrap import (
    BootstrapResult,
    adaptive_seed,
    paired_bootstrap_deltas,
    reference_seed,
)
from adaptive_compute.generators import BATTERY, generate
from adaptive_compute.reference import DEFAULT_B_REF


def test_delta_draws_are_bit_identical_for_same_params_and_seed() -> None:
    params, _generator = BATTERY["heavy_tailed"]
    scores_a, scores_b, y = generate(params)

    first = paired_bootstrap_deltas(scores_a, scores_b, y, draws=60, seed=777)
    second = paired_bootstrap_deltas(scores_a, scores_b, y, draws=60, seed=777)

    assert np.array_equal(first.deltas, second.deltas)


def test_delta_draws_replay_when_reusing_the_same_seedsequence_object() -> None:
    # spawn() advances a SeedSequence's child counter; reusing the same object
    # must still replay bit-identically (seed_branches clones before spawning).
    params, _generator = BATTERY["small_effect"]
    scores_a, scores_b, y = generate(params)
    ss = np.random.SeedSequence(1234)

    first = paired_bootstrap_deltas(scores_a, scores_b, y, draws=60, seed=ss)
    second = paired_bootstrap_deltas(scores_a, scores_b, y, draws=60, seed=ss)

    assert np.array_equal(first.deltas, second.deltas)
    # and equal to the int-seed stream, since SeedSequence(1234) ~ int 1234
    from_int = paired_bootstrap_deltas(scores_a, scores_b, y, draws=60, seed=1234)
    assert np.array_equal(first.deltas, from_int.deltas)


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


def test_eval_check_fails_when_recovery_is_perturbed(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def wrong_reference(*args, **kwargs):  # type: ignore[no-untyped-def]
        del args, kwargs
        return SimpleNamespace(decision="B_better", draws_consumed=DEFAULT_B_REF)

    monkeypatch.setattr(eval_module, "fixed_budget_reference", wrong_reference)

    with contextlib.redirect_stderr(io.StringIO()):
        assert eval_module.main(["--check"]) == 1


def test_eval_check_fails_cleanly_when_reference_raises(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def unresolved_reference(*args, **kwargs):  # type: ignore[no-untyped-def]
        del args, kwargs
        raise eval_module.UnresolvedReferenceError("straddled at B_ref")

    monkeypatch.setattr(eval_module, "fixed_budget_reference", unresolved_reference)

    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        assert eval_module.main(["--check"]) == 1
    assert "did not resolve" in stderr.getvalue()


def test_eval_check_fails_when_sizing_mcse_overflows(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    original = eval_module.paired_bootstrap_deltas

    def high_variance_sizing(*args, **kwargs):  # type: ignore[no-untyped-def]
        seed = kwargs["seed"]
        draws = kwargs["draws"]
        if isinstance(seed, np.random.SeedSequence):
            offset = 0.0 if seed.spawn_key[-1] % 2 == 0 else eval_module.DEFAULT_DELTA
            return BootstrapResult(
                deltas=np.full(draws, offset, dtype=np.float64),
                draws_consumed=draws,
                seed_spawn_key=tuple(seed.spawn_key),
            )
        return original(*args, **kwargs)

    monkeypatch.setattr(eval_module, "paired_bootstrap_deltas", high_variance_sizing)

    with contextlib.redirect_stderr(io.StringIO()):
        assert eval_module.main(["--check"]) == 1
