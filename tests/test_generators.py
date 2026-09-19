from adaptive_compute.generators import BATTERY, generate
from adaptive_compute.metrics import delta
from adaptive_compute.reference import DEFAULT_DELTA
from adaptive_compute.strata import classify_delta


def test_battery_contains_all_required_members() -> None:
    assert set(BATTERY) == {
        "near_delta_boundary",
        "small_effect",
        "heavy_tailed",
        "rare_event_imbalance",
        "easy_lopsided",
    }
    assert "heavy_tailed" in BATTERY


def test_battery_members_land_in_intended_strata() -> None:
    for params, _generator in BATTERY.values():
        scores_a, scores_b, y = generate(params)
        plugin_delta = delta(scores_a, scores_b, y)

        assert classify_delta(plugin_delta, DEFAULT_DELTA) == params.intended_stratum


def test_constructed_at_boundary_delta_classifies_as_boundary() -> None:
    assert classify_delta(DEFAULT_DELTA * 1.05, DEFAULT_DELTA) == "boundary"
    assert classify_delta(-DEFAULT_DELTA * 0.95, DEFAULT_DELTA) == "boundary"
