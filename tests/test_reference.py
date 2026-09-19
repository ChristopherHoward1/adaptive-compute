import numpy as np

from adaptive_compute.generators import BATTERY, generate
from adaptive_compute.metrics import delta
from adaptive_compute.reference import (
    DEFAULT_B_REF,
    DEFAULT_DELTA,
    decision_from_delta,
    fixed_budget_reference,
)
from adaptive_compute.strata import classify_delta


def test_reference_recovers_plugin_decision_for_non_boundary_members() -> None:
    for params, _generator in BATTERY.values():
        scores_a, scores_b, y = generate(params)
        plugin_delta = delta(scores_a, scores_b, y)
        if classify_delta(plugin_delta, DEFAULT_DELTA) == "boundary":
            continue

        result = fixed_budget_reference(scores_a, scores_b, y, seed=90_000 + params.seed)

        assert result.interval_method == "percentile"
        assert result.level == 0.95
        assert result.draws_consumed == DEFAULT_B_REF
        assert result.decision in {"A_better", "B_better", "equivalent"}
        assert result.decision == decision_from_delta(plugin_delta, DEFAULT_DELTA)


def test_reference_mcse_sizing_uses_independent_replications() -> None:
    params, _generator = BATTERY["near_delta_boundary"]
    scores_a, scores_b, y = generate(params)
    root = np.random.SeedSequence(20260919)

    estimates = [
        fixed_budget_reference(scores_a, scores_b, y, seed=seed_sequence).estimate
        for seed_sequence in root.spawn(16)
    ]
    mcse = float(np.std(estimates, ddof=1))

    assert mcse <= 0.1 * DEFAULT_DELTA


def test_reference_mcse_diagnostics_for_hard_members() -> None:
    for member in ("heavy_tailed", "rare_event_imbalance"):
        params, _generator = BATTERY[member]
        scores_a, scores_b, y = generate(params)
        root = np.random.SeedSequence(params.seed)
        estimates = [
            fixed_budget_reference(scores_a, scores_b, y, seed=seed_sequence).estimate
            for seed_sequence in root.spawn(6)
        ]
        mcse = float(np.std(estimates, ddof=1))
        print(f"{member} reference MCSE diagnostic: {mcse:.6f}")
        assert np.isfinite(mcse)
