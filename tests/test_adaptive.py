import inspect

import numpy as np

from adaptive_compute.adaptive import (
    adaptive_decision,
    decision_from_bounds,
    empirical_bernstein_bounds,
)
from adaptive_compute.generators import BATTERY, generate
from adaptive_compute.reference import DEFAULT_DELTA, fixed_budget_reference


def test_public_entry_is_blind() -> None:
    signature = inspect.signature(adaptive_decision)

    assert tuple(signature.parameters) == (
        "scores_a",
        "scores_b",
        "y",
        "margin",
        "alpha",
        "b",
        "b_max",
        "seed",
    )
    assert "b_ref" not in signature.parameters
    assert "reference_decision" not in signature.parameters
    assert "plugin_delta" not in signature.parameters


def test_adaptive_determinism_on_int_and_seedsequence() -> None:
    params, _generator = BATTERY["easy_lopsided"]
    scores_a, scores_b, y = generate(params)

    first = adaptive_decision(
        scores_a,
        scores_b,
        y,
        margin=DEFAULT_DELTA,
        alpha=0.05,
        b=64,
        b_max=1024,
        seed=777,
    )
    second = adaptive_decision(
        scores_a,
        scores_b,
        y,
        margin=DEFAULT_DELTA,
        alpha=0.05,
        b=64,
        b_max=1024,
        seed=777,
    )
    seed_sequence = np.random.SeedSequence(777)
    from_ss = adaptive_decision(
        scores_a,
        scores_b,
        y,
        margin=DEFAULT_DELTA,
        alpha=0.05,
        b=64,
        b_max=1024,
        seed=seed_sequence,
    )
    from_same_ss = adaptive_decision(
        scores_a,
        scores_b,
        y,
        margin=DEFAULT_DELTA,
        alpha=0.05,
        b=64,
        b_max=1024,
        seed=seed_sequence,
    )

    assert first == second
    assert from_ss == from_same_ss
    assert first == from_ss


def test_draw_accounting_resolved_and_abstain_cases() -> None:
    params, _generator = BATTERY["easy_lopsided"]
    scores_a, scores_b, y = generate(params)

    resolved = adaptive_decision(
        scores_a,
        scores_b,
        y,
        margin=DEFAULT_DELTA,
        alpha=0.05,
        b=64,
        b_max=1024,
        seed=123,
    )
    assert resolved.decision == "A_better"
    assert resolved.draws_consumed < 1024
    assert resolved.draws_consumed % 64 == 0

    abstain = adaptive_decision(
        [0.0, 0.1, 0.2, 0.3],
        [0.0, 0.1, 0.2, 0.3],
        [0, 0, 1, 1],
        margin=DEFAULT_DELTA,
        alpha=0.05,
        b=7,
        b_max=20,
        seed=123,
    )
    assert abstain.decision == "abstain"
    assert abstain.draws_consumed == 20


def test_stop_decision_uses_bounds_only() -> None:
    assert decision_from_bounds(0.051, 0.20, margin=DEFAULT_DELTA) == "A_better"
    assert decision_from_bounds(-0.20, -0.051, margin=DEFAULT_DELTA) == "B_better"
    assert decision_from_bounds(-0.049, 0.049, margin=DEFAULT_DELTA) == "equivalent"
    assert decision_from_bounds(0.049, 0.20, margin=DEFAULT_DELTA) is None

    lower, upper = empirical_bernstein_bounds(np.zeros(2000), alpha=0.05)
    assert decision_from_bounds(lower, upper, margin=DEFAULT_DELTA) == "equivalent"


def test_generative_budget_agrees_with_reference_for_resolved_classes() -> None:
    for member in ("easy_lopsided", "small_effect"):
        params, _generator = BATTERY[member]
        scores_a, scores_b, y = generate(params)
        reference = fixed_budget_reference(scores_a, scores_b, y, seed=90_000 + params.seed)
        adaptive = adaptive_decision(
            scores_a,
            scores_b,
            y,
            margin=DEFAULT_DELTA,
            alpha=0.05,
            b=64,
            b_max=4096,
            seed=90_000 + params.seed,
        )

        assert adaptive.decision == reference.decision

    params, _generator = BATTERY["easy_lopsided"]
    scores_a, scores_b, y = generate(params)
    swapped_reference = fixed_budget_reference(scores_b, scores_a, y, seed=90_000 + params.seed)
    swapped = adaptive_decision(
        scores_b,
        scores_a,
        y,
        margin=DEFAULT_DELTA,
        alpha=0.05,
        b=64,
        b_max=4096,
        seed=90_000 + params.seed,
    )

    assert swapped_reference.decision == "B_better"
    assert swapped.decision == swapped_reference.decision
