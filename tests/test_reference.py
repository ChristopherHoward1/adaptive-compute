import numpy as np
import pytest

from adaptive_compute import reference as reference_module
from adaptive_compute.bootstrap import BootstrapResult, paired_bootstrap_deltas
from adaptive_compute.generators import BATTERY, generate
from adaptive_compute.metrics import delta
from adaptive_compute.reference import (
    DEFAULT_B_REF,
    DEFAULT_DELTA,
    UnresolvedReferenceError,
    decision_from_delta,
    fixed_budget_reference,
)
from adaptive_compute.strata import classify_delta


def test_reference_interval_straddling_margin_raises_unresolved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def straddling_bootstrap(*args: object, **kwargs: object) -> BootstrapResult:
        del args, kwargs
        return BootstrapResult(
            deltas=np.array([0.049, 0.051, 0.20], dtype=np.float64),
            draws_consumed=3,
            seed_spawn_key=(),
        )

    monkeypatch.setattr(reference_module, "paired_bootstrap_deltas", straddling_bootstrap)

    with pytest.raises(UnresolvedReferenceError, match=r"straddles ±δ=0\.05"):
        fixed_budget_reference(
            [0.0, 1.0],
            [0.0, 1.0],
            [0, 1],
            margin=DEFAULT_DELTA,
            alpha=1.0 / 3.0,
            b_ref=3,
            seed=123,
        )


def test_boundary_stratum_routes_away_from_reference_decision() -> None:
    params, _generator = BATTERY["near_delta_boundary"]
    scores_a, scores_b, y = generate(params)
    plugin_delta = delta(scores_a, scores_b, y)
    assert classify_delta(plugin_delta, DEFAULT_DELTA) == "boundary"

    with pytest.raises(UnresolvedReferenceError, match=r"straddles ±δ=0\.05"):
        fixed_budget_reference(scores_a, scores_b, y, seed=90_000 + params.seed)


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

    estimates = []
    for seed_sequence in root.spawn(16):
        bootstrap = paired_bootstrap_deltas(
            scores_a,
            scores_b,
            y,
            draws=DEFAULT_B_REF,
            seed=seed_sequence,
        )
        estimates.append(float(np.mean(bootstrap.deltas)))
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
