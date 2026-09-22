import inspect
from functools import lru_cache

from adaptive_compute import equiv_probe
from adaptive_compute.generators import BATTERY
from adaptive_compute.metrics import delta
from adaptive_compute.reference import DEFAULT_B_REF, DEFAULT_DELTA
from adaptive_compute.strata import classify_delta


@lru_cache(maxsize=None)
def _small_probe(instrument: str) -> equiv_probe.ProbeRun:
    return equiv_probe.run_probe(instrument=instrument, cases_per_ratio=12)  # type: ignore[arg-type]


def test_mixed_fixture_is_position_spread_and_in_band() -> None:
    cases = equiv_probe.build_mixed_cases(cases_per_ratio=12)
    abs_deltas = [
        abs(delta(scores_a, scores_b, y)) for _position, _seed, (scores_a, scores_b, y) in cases
    ]

    assert max(abs_deltas) <= equiv_probe.FIXTURE_MAX_ABS_DELTA + 1e-12
    assert max(abs_deltas) - min(abs_deltas) >= equiv_probe.FIXTURE_MIN_ABS_DELTA_SPREAD
    assert all(item < DEFAULT_DELTA for item in abs_deltas)
    assert all(classify_delta(item, DEFAULT_DELTA) == "equivalent" for item in abs_deltas)


def test_mechanism_diagnostic_is_per_instrument() -> None:
    eb = _small_probe("eb")
    betting = _small_probe("betting")

    assert eb.mechanism.fixed_plateau_gap <= equiv_probe.PLATEAU_TOL
    assert betting.mechanism.fixed_plateau_gap <= equiv_probe.PLATEAU_TOL
    assert eb.mechanism.eb_width_at_b_ref is not None
    assert eb.mechanism.eb_width_at_b_ref > DEFAULT_DELTA
    assert betting.mechanism.cheapest_fixed_equivalent_median < betting.summary.draws_p50
    assert betting.mechanism.adaptive_crossing_median < DEFAULT_B_REF


def test_probe_feasibility_guards_hold_on_scored_cases() -> None:
    for instrument in ("eb", "betting"):
        probe = _small_probe(instrument)

        assert probe.summary.scored == probe.scored
        assert probe.reference_resolved_fraction >= equiv_probe.MIN_REFERENCE_RESOLVED_FRACTION
        assert probe.summary.abstain_rate <= equiv_probe.MAX_ABSTAIN_RATE
        assert probe.summary.fixed_b_dominating_adaptive


def test_probe_replays_deterministically() -> None:
    assert (
        equiv_probe.deterministic_probe_signature() == equiv_probe.deterministic_probe_signature()
    )


def test_probe_reuses_released_savings_helpers() -> None:
    source = inspect.getsource(equiv_probe)

    assert "_summarize_stratum(" in source
    assert "pareto_verdict(" in source
    assert "fixed_b_sweep(" in source
    assert "PROBE_FIXED_B_GRID" not in source


def test_probe_pins_same_b_max_for_both_arms_and_preserves_battery() -> None:
    params = equiv_probe.probe_params()

    assert params.b == equiv_probe.PROBE_B
    assert params.b_max == equiv_probe.PROBE_B_MAX
    assert _small_probe("eb").params.b_max == params.b_max
    assert _small_probe("betting").params.b_max == params.b_max
    assert len(BATTERY) == 5
