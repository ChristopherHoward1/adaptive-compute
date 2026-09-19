"""CLI self-check for the fixed-budget reference unit."""

from __future__ import annotations

import argparse
import sys

import numpy as np

from adaptive_compute.bootstrap import paired_bootstrap_deltas
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

CHECK_MCSE_REPLICATIONS = 8
CHECK_MCSE_RHO = 0.1


def _check() -> int:
    total_draws = 0
    for name, (params, _generator) in BATTERY.items():
        scores_a, scores_b, y = generate(params)
        plugin_delta = delta(scores_a, scores_b, y)
        branch_seed = 90_000 + params.seed
        first = paired_bootstrap_deltas(
            scores_a,
            scores_b,
            y,
            draws=DEFAULT_B_REF,
            seed=branch_seed,
        )
        second = paired_bootstrap_deltas(
            scores_a,
            scores_b,
            y,
            draws=DEFAULT_B_REF,
            seed=branch_seed,
        )
        if not np.array_equal(first.deltas, second.deltas):
            print(f"determinism failed for {name}", file=sys.stderr)
            return 1

        # Count every resample consumed, including the replay run, so the
        # printed total is the exact draw count spent by the check.
        total_draws += first.draws_consumed + second.draws_consumed
        # Classify from the plug-in delta before invoking the fixed-budget
        # reference; boundary members are deliberately outside recovery scoring.
        stratum = classify_delta(plugin_delta, DEFAULT_DELTA)
        if stratum == "boundary":
            continue

        try:
            result = fixed_budget_reference(
                scores_a,
                scores_b,
                y,
                b_ref=DEFAULT_B_REF,
                seed=branch_seed,
            )
        except UnresolvedReferenceError:
            # A non-boundary member should always resolve at B_ref; if one ever
            # straddles, fail the check cleanly instead of aborting on a traceback.
            print(
                f"reference did not resolve for non-boundary member {name}",
                file=sys.stderr,
            )
            return 1
        expected = decision_from_delta(plugin_delta, DEFAULT_DELTA)
        if result.decision != expected:
            print(
                f"decision recovery failed for {name}: expected {expected}, got {result.decision}",
                file=sys.stderr,
            )
            return 1
        total_draws += result.draws_consumed

    params, _generator = BATTERY["near_delta_boundary"]
    scores_a, scores_b, y = generate(params)
    root = np.random.SeedSequence(20260919)
    estimates = []
    for seed_sequence in root.spawn(CHECK_MCSE_REPLICATIONS):
        bootstrap = paired_bootstrap_deltas(
            scores_a,
            scores_b,
            y,
            draws=DEFAULT_B_REF,
            seed=seed_sequence,
        )
        estimates.append(float(np.mean(bootstrap.deltas)))
        total_draws += bootstrap.draws_consumed

    mcse = float(np.std(estimates, ddof=1))
    if mcse > CHECK_MCSE_RHO * DEFAULT_DELTA:
        print(
            f"B_ref sizing failed for near_delta_boundary: "
            f"MCSE {mcse:.6f} > {CHECK_MCSE_RHO * DEFAULT_DELTA:.6f}",
            file=sys.stderr,
        )
        return 1

    print(f"eval check passed; draws_consumed={total_draws}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="run the seeded self-consistency check"
    )
    args = parser.parse_args(argv)
    if args.check:
        return _check()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
