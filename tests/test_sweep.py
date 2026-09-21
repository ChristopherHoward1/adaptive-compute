from adaptive_compute.reference import UnresolvedReferenceError
from adaptive_compute.sweep import false_stop_rate, fixed_b_sweep, pareto_verdict


def test_pareto_verdict_finds_fixed_b_that_dominates_adaptive() -> None:
    result = pareto_verdict(
        adaptive_false_stop_rate=0.02,
        adaptive_nondecision_rate=0.10,
        adaptive_draws=(100, 120, 140),
        fixed_false_stop_rates={64: 0.01, 128: 0.03, 256: 0.0},
        fixed_nondecision_rates={64: 0.05, 128: 0.00, 256: 0.30},
    )

    assert result.fixed_b_dominating_adaptive == (64,)


def test_pareto_verdict_reports_adaptive_target_savings() -> None:
    result = pareto_verdict(
        adaptive_false_stop_rate=0.02,
        adaptive_nondecision_rate=0.05,
        adaptive_draws=(100, 100, 100),
        fixed_false_stop_rates={128: 0.02, 256: 0.03, 320: 0.01},
        fixed_nondecision_rates={128: 0.05, 256: 0.05, 320: 0.01},
    )

    assert result.adaptive_dominated_fixed_b == (256,)
    assert result.best_savings_ratio == 2.56


def test_pareto_verdict_does_not_credit_unresolved_fixed_b_as_cheap_win() -> None:
    result = pareto_verdict(
        adaptive_false_stop_rate=0.02,
        adaptive_nondecision_rate=0.10,
        adaptive_draws=(100, 120, 140),
        fixed_false_stop_rates={64: 0.00},
        fixed_nondecision_rates={64: 0.95},
    )

    assert result.fixed_b_dominating_adaptive == ()
    assert result.best_savings_ratio == 0.0


def test_false_stop_rate_treats_unresolved_as_not_false_stop() -> None:
    rate = false_stop_rate(
        ("A_better", "unresolved", "equivalent"), ("A_better", "B_better", "A_better")
    )

    assert rate == 1 / 3


def test_false_stop_rate_validates_lengths() -> None:
    try:
        false_stop_rate(("A_better",), ("A_better", "B_better"))
    except ValueError as exc:
        assert "same length" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_fixed_b_sweep_runs_reference_percentile_grid() -> None:
    result = fixed_b_sweep(
        [0.0, 0.1, 0.8, 0.9],
        [0.1, 0.2, 0.7, 0.8],
        [0, 0, 1, 1],
        grid=(4, 8),
        margin=0.05,
        alpha=0.05,
        seed=12,
    )

    assert [item.b for item in result] == [4, 8]
    assert [item.draws_consumed for item in result] == [4, 8]


def test_false_stop_rate_rejects_empty_scoring() -> None:
    try:
        false_stop_rate((), ())
    except UnresolvedReferenceError:
        pass
    else:
        raise AssertionError("expected UnresolvedReferenceError")
