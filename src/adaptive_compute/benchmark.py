"""Offline adaptive-vs-reference benchmark harness."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from statistics import NormalDist

import numpy as np

from adaptive_compute.adaptive import adaptive_decision
from adaptive_compute.generators import BATTERY, GeneratorParams, generate
from adaptive_compute.metrics import delta
from adaptive_compute.reference import (
    DEFAULT_ALPHA,
    DEFAULT_B_REF,
    DEFAULT_DELTA,
    Decision,
    ReferenceResult,
    UnresolvedReferenceError,
    fixed_budget_reference,
)
from adaptive_compute.strata import classify_delta
from adaptive_compute.sweep import decision_from_interval, pareto_verdict

DEFAULT_BATCH = 32
DEFAULT_B_MAX = 320
DEFAULT_N_TUNE = 24
DEFAULT_N_TEST = 500
TEST_SEED_OFFSET = 10_000
FIXED_B_GRID = (32, 64, 128, DEFAULT_B_REF)
RESULTS_MD = Path("work/adaptive-procedure/results.md")
RESULTS_JSON = Path("work/adaptive-procedure/results.json")


@dataclass(frozen=True)
class AdaptiveParams:
    b: int
    alpha: float
    b_max: int


@dataclass(frozen=True)
class MemberRun:
    member: str
    stratum: str
    seed: int
    reference_decision: Decision | None
    adaptive_decision: str
    adaptive_draws: int
    reference_unresolved: bool
    fixed_decisions: dict[int, str]


@dataclass(frozen=True)
class StratumSummary:
    stratum: str
    scored: int
    false_stops: int
    false_stop_rate: float
    false_stop_ci: tuple[float, float]
    draws_p50: float
    draws_p90: float
    draws_p99: float
    abstain_rate: float
    reference_unresolved: int
    pareto_dominated_fixed_b: tuple[int, ...]
    pareto_best_savings_ratio: float


@dataclass(frozen=True)
class BenchmarkResult:
    tuned_params: AdaptiveParams
    n_tune: int
    n_test: int
    summaries: tuple[StratumSummary, ...]
    heavy_tailed_false_stop_rate: float | None
    h1_holds: bool
    runs: tuple[MemberRun, ...]


def wilson_interval(k: int, n: int, *, level: float = 0.95) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    z = NormalDist().inv_cdf(0.5 + level / 2.0)
    phat = k / n
    denom = 1.0 + z * z / n
    center = (phat + z * z / (2.0 * n)) / denom
    half = z * np.sqrt((phat * (1.0 - phat) + z * z / (4.0 * n)) / n) / denom
    return max(0.0, center - half), min(1.0, center + half)


def _seeded_params(params: GeneratorParams, seed_index: int) -> GeneratorParams:
    return replace(params, seed=params.seed + seed_index)


def _fixed_decisions_from_reference(reference: ReferenceResult | None) -> dict[int, str]:
    if reference is None:
        return {b: "unresolved" for b in FIXED_B_GRID}
    decisions: dict[int, str] = {}
    for b in FIXED_B_GRID:
        lower, upper = np.percentile(
            reference.deltas[:b],
            [100.0 * DEFAULT_ALPHA / 2.0, 100.0 * (1.0 - DEFAULT_ALPHA / 2.0)],
        )
        decisions[b] = decision_from_interval(float(lower), float(upper), margin=DEFAULT_DELTA)
    return decisions


def _run_member_seed(
    name: str,
    params: GeneratorParams,
    adaptive_params: AdaptiveParams,
    seed_index: int,
) -> MemberRun:
    seeded = _seeded_params(params, seed_index)
    scores_a, scores_b, y = generate(seeded)
    plugin_delta = delta(scores_a, scores_b, y)
    stratum = classify_delta(plugin_delta, DEFAULT_DELTA)
    run_seed = 90_000 + seeded.seed

    reference: ReferenceResult | None
    reference_decision: Decision | None
    reference_unresolved = False
    try:
        reference = fixed_budget_reference(
            scores_a,
            scores_b,
            y,
            seed=run_seed,
            b_ref=DEFAULT_B_REF,
        )
        reference_decision = reference.decision
    except UnresolvedReferenceError:
        reference = None
        reference_decision = None
        reference_unresolved = True

    adaptive = adaptive_decision(
        scores_a,
        scores_b,
        y,
        margin=DEFAULT_DELTA,
        alpha=adaptive_params.alpha,
        b=adaptive_params.b,
        b_max=adaptive_params.b_max,
        seed=run_seed,
    )
    return MemberRun(
        member=name,
        stratum=stratum,
        seed=seeded.seed,
        reference_decision=reference_decision,
        adaptive_decision=adaptive.decision,
        adaptive_draws=adaptive.draws_consumed,
        reference_unresolved=reference_unresolved,
        fixed_decisions=_fixed_decisions_from_reference(reference),
    )


def _tune_params(n_tune: int) -> AdaptiveParams:
    candidates = (
        AdaptiveParams(b=DEFAULT_BATCH, alpha=DEFAULT_ALPHA, b_max=DEFAULT_B_MAX),
        AdaptiveParams(b=64, alpha=DEFAULT_ALPHA, b_max=DEFAULT_B_MAX),
    )
    best = candidates[0]
    best_score = (1.0, float(DEFAULT_B_MAX))
    for candidate in candidates:
        runs = [
            _run_member_seed(name, params, candidate, i)
            for name, (params, _generator) in BATTERY.items()
            if name != "near_delta_boundary"
            for i in range(n_tune)
        ]
        scored = [run for run in runs if run.reference_decision is not None]
        false_rate = float(
            np.mean(
                [
                    run.adaptive_decision != "abstain"
                    and run.adaptive_decision != run.reference_decision
                    for run in scored
                ]
            )
        )
        median_draws = float(np.median([run.adaptive_draws for run in scored]))
        score = (false_rate, median_draws)
        if score < best_score:
            best = candidate
            best_score = score
    return best


def _summarize_stratum(stratum: str, runs: list[MemberRun]) -> StratumSummary:
    scored = [run for run in runs if run.reference_decision is not None]
    false_stops = sum(
        run.adaptive_decision != "abstain" and run.adaptive_decision != run.reference_decision
        for run in scored
    )
    rate = false_stops / len(scored) if scored else 0.0
    draws = [run.adaptive_draws for run in runs]
    fixed_rates = {}
    for b in FIXED_B_GRID:
        fixed_rates[b] = (
            sum(
                run.fixed_decisions[b] != "unresolved"
                and run.fixed_decisions[b] != run.reference_decision
                for run in scored
            )
            / len(scored)
            if scored
            else 0.0
        )
    pareto = pareto_verdict(
        adaptive_false_stop_rate=rate,
        adaptive_draws=tuple(run.adaptive_draws for run in scored),
        fixed_false_stop_rates=fixed_rates,
    )
    return StratumSummary(
        stratum=stratum,
        scored=len(scored),
        false_stops=false_stops,
        false_stop_rate=rate,
        false_stop_ci=wilson_interval(false_stops, len(scored)),
        draws_p50=float(np.percentile(draws, 50)),
        draws_p90=float(np.percentile(draws, 90)),
        draws_p99=float(np.percentile(draws, 99)),
        abstain_rate=float(np.mean([run.adaptive_decision == "abstain" for run in runs])),
        reference_unresolved=sum(run.reference_unresolved for run in runs),
        pareto_dominated_fixed_b=pareto.dominated_fixed_b,
        pareto_best_savings_ratio=pareto.best_savings_ratio,
    )


def run_benchmark(
    *,
    n_tune: int = DEFAULT_N_TUNE,
    n_test: int = DEFAULT_N_TEST,
) -> BenchmarkResult:
    tuned = _tune_params(n_tune)
    runs = [
        _run_member_seed(name, params, tuned, TEST_SEED_OFFSET + i)
        for name, (params, _generator) in BATTERY.items()
        if name != "near_delta_boundary"
        for i in range(n_test)
    ]
    non_boundary = [run for run in runs if run.stratum != "boundary"]
    strata = tuple(sorted({run.stratum for run in non_boundary}))
    summaries = tuple(
        _summarize_stratum(stratum, [run for run in non_boundary if run.stratum == stratum])
        for stratum in strata
    )
    heavy_runs = [
        run
        for run in non_boundary
        if run.member == "heavy_tailed" and run.reference_decision is not None
    ]
    heavy_false = None
    if heavy_runs:
        heavy_false = float(
            np.mean(
                [
                    run.adaptive_decision != "abstain"
                    and run.adaptive_decision != run.reference_decision
                    for run in heavy_runs
                ]
            )
        )
    h1_holds = all(
        summary.false_stop_ci[1] <= DEFAULT_ALPHA and not summary.pareto_dominated_fixed_b
        for summary in summaries
    )
    return BenchmarkResult(
        tuned_params=tuned,
        n_tune=n_tune,
        n_test=n_test,
        summaries=summaries,
        heavy_tailed_false_stop_rate=heavy_false,
        h1_holds=h1_holds,
        runs=tuple(runs),
    )


def _summary_markdown(result: BenchmarkResult) -> str:
    verdict = "H1 HOLDS" if result.h1_holds else "H1 NEGATIVE RESULT"
    lines = [
        "# Adaptive Procedure First Result",
        "",
        f"Verdict: **{verdict}**.",
        "",
        (
            f"Tuned on {result.n_tune} seeds/member; tested on {result.n_test} "
            f"seeds/member with b={result.tuned_params.b}, "
            f"alpha={result.tuned_params.alpha}, B_max={result.tuned_params.b_max}."
        ),
        "",
        (
            "| stratum | scored | false-stop rate | 95% CI | draws p50/p90/p99 "
            "| abstain | ref unresolved | fixed-B dominating adaptive |"
        ),
        "| --- | ---: | ---: | --- | --- | ---: | ---: | --- |",
    ]
    for summary in result.summaries:
        ci = f"[{summary.false_stop_ci[0]:.4f}, {summary.false_stop_ci[1]:.4f}]"
        draws = f"{summary.draws_p50:.0f}/{summary.draws_p90:.0f}/{summary.draws_p99:.0f}"
        dominated = ", ".join(str(b) for b in summary.pareto_dominated_fixed_b) or "none"
        lines.append(
            f"| {summary.stratum} | {summary.scored} | {summary.false_stop_rate:.4f} "
            f"| {ci} | {draws} | {summary.abstain_rate:.4f} "
            f"| {summary.reference_unresolved} | {dominated} |"
        )
    heavy = result.heavy_tailed_false_stop_rate
    lines.extend(
        [
            "",
            "## Heavy-Tailed Check",
            "",
            f"Realized false-stop rate: {heavy:.4f}" if heavy is not None else "No scored runs.",
            "",
            "## Pareto Savings",
            "",
            (
                "A fixed-B entry listed in the table has lower median draws and false-stop "
                "rate no higher than adaptive in that stratum; `none` means no fixed-B grid "
                "point dominated the adaptive run."
            ),
            "",
            (
                "H1 requires both the per-stratum false-stop CI check and no fixed-B "
                "dominator; a listed fixed-B dominator makes this a negative result."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def write_results(
    result: BenchmarkResult,
    *,
    md_path: Path = RESULTS_MD,
    json_path: Path = RESULTS_JSON,
) -> None:
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_summary_markdown(result), encoding="utf-8")
    json_path.write_text(
        json.dumps(asdict(result), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def run_and_write_results() -> BenchmarkResult:
    result = run_benchmark()
    write_results(result)
    return result
