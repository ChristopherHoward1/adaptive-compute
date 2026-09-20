from adaptive_compute.reference import UnresolvedReferenceError
from adaptive_compute.sweep import false_stop_rate, fixed_b_sweep, pareto_verdict


def test_pareto_verdict_finds_fixed_b_that_dominates_adaptive() -> None:
    result = pareto_verdict(
        adaptive_false_stop_rate=0.02,
        adaptive_draws=(100, 120, 140),
        fixed_false_stop_rates={64: 0.01, 128: 0.03, 256: 0.0},
    )

    assert result.dominated_fixed_b == (64,)
    assert result.fixed_best_median_draws == 64.0


def test_pareto_verdict_reports_no_dominator() -> None:
    result = pareto_verdict(
        adaptive_false_stop_rate=0.02,
        adaptive_draws=(100, 120, 140),
        fixed_false_stop_rates={64: 0.03, 128: 0.01},
    )

    assert result.dominated_fixed_b == ()
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
