"""CLI self-check and offline benchmark entry point."""

from __future__ import annotations

import argparse
import sys

import numpy as np

from adaptive_compute.adaptive import adaptive_decision
from adaptive_compute.benchmark import run_and_write_results
from adaptive_compute.bootstrap import adaptive_bootstrap_stream, paired_bootstrap_deltas
from adaptive_compute.generators import BATTERY, generate
from adaptive_compute.metrics import delta
from adaptive_compute.reference import (
    DEFAULT_ALPHA,
    DEFAULT_B_REF,
    DEFAULT_DELTA,
    UnresolvedReferenceError,
    decision_from_delta,
    fixed_budget_reference,
)
from adaptive_compute.strata import classify_delta

CHECK_MCSE_REPLICATIONS = 8
CHECK_MCSE_RHO = 0.1
CHECK_ADAPTIVE_BATCH = 64
CHECK_ADAPTIVE_B_MAX = 1024


def _hard_member_mcse(member: str, replications: int = 6) -> float:
    params, _generator = BATTERY[member]
    scores_a, scores_b, y = generate(params)
    root = np.random.SeedSequence(params.seed)
    estimates = []
    for seed_sequence in root.spawn(replications):
        bootstrap = paired_bootstrap_deltas(
            scores_a,
            scores_b,
            y,
            draws=DEFAULT_B_REF,
            seed=seed_sequence,
        )
        estimates.append(float(np.mean(bootstrap.deltas)))
    return float(np.std(estimates, ddof=1))


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

    easy_params, _generator = BATTERY["easy_lopsided"]
    easy_scores_a, easy_scores_b, easy_y = generate(easy_params)
    adaptive_first = adaptive_decision(
        easy_scores_a,
        easy_scores_b,
        easy_y,
        margin=DEFAULT_DELTA,
        alpha=DEFAULT_ALPHA,
        b=CHECK_ADAPTIVE_BATCH,
        b_max=CHECK_ADAPTIVE_B_MAX,
        seed=12345,
    )
    adaptive_second = adaptive_decision(
        easy_scores_a,
        easy_scores_b,
        easy_y,
        margin=DEFAULT_DELTA,
        alpha=DEFAULT_ALPHA,
        b=CHECK_ADAPTIVE_BATCH,
        b_max=CHECK_ADAPTIVE_B_MAX,
        seed=12345,
    )
    if adaptive_first != adaptive_second:
        print("adaptive int-seed determinism failed", file=sys.stderr)
        return 1
    seed_sequence = np.random.SeedSequence(12345)
    adaptive_ss_first = adaptive_decision(
        easy_scores_a,
        easy_scores_b,
        easy_y,
        margin=DEFAULT_DELTA,
        alpha=DEFAULT_ALPHA,
        b=CHECK_ADAPTIVE_BATCH,
        b_max=CHECK_ADAPTIVE_B_MAX,
        seed=seed_sequence,
    )
    adaptive_ss_second = adaptive_decision(
        easy_scores_a,
        easy_scores_b,
        easy_y,
        margin=DEFAULT_DELTA,
        alpha=DEFAULT_ALPHA,
        b=CHECK_ADAPTIVE_BATCH,
        b_max=CHECK_ADAPTIVE_B_MAX,
        seed=seed_sequence,
    )
    if adaptive_ss_first != adaptive_ss_second or adaptive_ss_first != adaptive_first:
        print("adaptive SeedSequence determinism failed", file=sys.stderr)
        return 1
    if (
        adaptive_first.decision == "abstain"
        or adaptive_first.draws_consumed >= CHECK_ADAPTIVE_B_MAX
    ):
        print("adaptive did not resolve easy_lopsided before B_max", file=sys.stderr)
        return 1
    if adaptive_first.draws_consumed % CHECK_ADAPTIVE_BATCH != 0:
        print("adaptive draw accounting is not batch-exact", file=sys.stderr)
        return 1
    total_draws += (
        adaptive_first.draws_consumed
        + adaptive_second.draws_consumed
        + adaptive_ss_first.draws_consumed
        + adaptive_ss_second.draws_consumed
    )

    flat_scores = np.array([0.0, 0.1, 0.2, 0.3])
    flat_y = np.array([0, 0, 1, 1])
    abstain = adaptive_decision(
        flat_scores,
        flat_scores,
        flat_y,
        margin=DEFAULT_DELTA,
        alpha=DEFAULT_ALPHA,
        b=8,
        b_max=16,
        seed=6789,
    )
    if abstain.decision != "abstain" or abstain.draws_consumed != 16:
        print("adaptive abstain accounting failed", file=sys.stderr)
        return 1
    total_draws += abstain.draws_consumed

    reference_stream = paired_bootstrap_deltas(
        easy_scores_a,
        easy_scores_b,
        easy_y,
        draws=32,
        seed=2468,
    )
    adaptive_stream = next(
        adaptive_bootstrap_stream(
            easy_scores_a,
            easy_scores_b,
            easy_y,
            batch_draws=32,
            max_draws=32,
            seed=2468,
        )
    )
    if np.array_equal(reference_stream.deltas, adaptive_stream.deltas):
        print("reference and adaptive streams unexpectedly matched", file=sys.stderr)
        return 1
    total_draws += reference_stream.draws_consumed + adaptive_stream.draws_consumed

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

    for member in ("heavy_tailed", "rare_event_imbalance"):
        hard_mcse = _hard_member_mcse(member)
        if not np.isfinite(hard_mcse):
            print(f"hard-member MCSE diagnostic failed for {member}", file=sys.stderr)
            return 1

    print(f"eval check passed; draws_consumed={total_draws}")
    return 0


def _run() -> int:
    result = run_and_write_results()
    verdict = "H1 HOLDS" if result.h1_holds else "H1 NEGATIVE RESULT"
    print(f"eval run wrote results; {verdict}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="run the seeded self-consistency check"
    )
    parser.add_argument("--run", action="store_true", help="run the offline benchmark")
    args = parser.parse_args(argv)
    if args.check:
        return _check()
    if args.run:
        return _run()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
