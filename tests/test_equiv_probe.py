import inspect

from adaptive_compute import equiv_probe
from adaptive_compute.generators import BATTERY
from adaptive_compute.metrics import delta
from adaptive_compute.reference import DEFAULT_DELTA
from adaptive_compute.strata import classify_delta


def test_mixed_fixture_is_heterogeneous_and_in_band() -> None:
    precheck = equiv_probe.precheck_region()
    assert precheck.non_empty
    assert precheck.shallow_abs_delta is not None

    cases = equiv_probe.build_mixed_cases(
        deep_ratio=1,
        shallow_ratio=1,
        shallow_abs_delta=precheck.shallow_abs_delta,
    )
    abs_deltas = [
        abs(delta(scores_a, scores_b, y)) for _tier, _seed, (scores_a, scores_b, y) in cases
    ]

    assert max(abs_deltas) - min(abs_deltas) >= equiv_probe.HETEROGENEITY_SPREAD_MIN
    assert all(item < DEFAULT_DELTA for item in abs_deltas)
    assert all(classify_delta(item, DEFAULT_DELTA) == "equivalent" for item in abs_deltas)


def test_resolvable_yet_hard_region_is_non_empty() -> None:
    precheck = equiv_probe.precheck_region()

    assert precheck.non_empty
    assert precheck.shallow
    assert all(item.stratum == "equivalent" for item in precheck.shallow)
    assert all(item.reference_resolved for item in precheck.shallow)
    assert precheck.shallow_mean_required_draws > precheck.deep_mean_required_draws


def test_probe_replays_deterministically() -> None:
    assert (
        equiv_probe.deterministic_probe_signature() == equiv_probe.deterministic_probe_signature()
    )


def test_probe_reuses_released_savings_helpers() -> None:
    source = inspect.getsource(equiv_probe)

    assert "_summarize_stratum(" in source
    assert "pareto_verdict(" in source
    assert "fixed_b_sweep(" in source


def test_probe_pins_same_b_max_for_both_arms() -> None:
    params = equiv_probe.probe_params()

    assert params.b == equiv_probe.PROBE_B
    assert params.b_max == equiv_probe.PROBE_B_MAX
    assert len(BATTERY) == 5
