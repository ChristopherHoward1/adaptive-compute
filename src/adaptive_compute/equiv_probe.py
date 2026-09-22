"""Offline equivalence-band heterogeneity probe."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from statistics import fmean

import numpy as np

from adaptive_compute.adaptive import AdaptiveInstrument, adaptive_decision
from adaptive_compute.benchmark import (
    FIXED_B_GRID,
    TARGET_SAVINGS_RATIO,
    AdaptiveParams,
    MemberRun,
    StratumSummary,
    _summarize_stratum,
    run_benchmark,
    wilson_interval,
)
from adaptive_compute.generators import BATTERY, MixedEquivalenceCase, generate, mixed_equivalence
from adaptive_compute.metrics import delta
from adaptive_compute.reference import (
    DEFAULT_ALPHA,
    DEFAULT_B_REF,
    DEFAULT_DELTA,
    Decision,
    UnresolvedReferenceError,
    fixed_budget_reference,
)
from adaptive_compute.strata import classify_delta
from adaptive_compute.sweep import fixed_b_sweep, pareto_verdict

PROBE_DIR = Path("work/equivalence-band-savings")
DIAGNOSTIC_MD = PROBE_DIR / "diagnostic.md"
VERDICT_MD = PROBE_DIR / "verdict.md"
PROBE_B = 64
PROBE_B_MAX = 8192
PROBE_BASE_SEED = 7_028
PROBE_CASES_PER_RATIO = 96
PRECHECK_CASES_PER_RATIO = 12
PROBE_RATIOS = ((1, 1), (2, 1))
SHALLOW_TARGET_CANDIDATES = (0.038, 0.037, 0.036, 0.035, 0.034, 0.033)
REQUIRED_DRAW_GRID = (32, 64, 96, 128, 160, 192, 224, 256, 288, DEFAULT_B_REF)
HETEROGENEITY_SPREAD_MIN = 0.025


@dataclass(frozen=True)
class RequiredDraw:
    tier: str
    seed: int
    abs_delta: float
    required_draws: int | None
    reference_resolved: bool
    stratum: str


@dataclass(frozen=True)
class RegionPrecheck:
    shallow_abs_delta: float | None
    non_empty: bool
    deep_mean_required_draws: float
    shallow_mean_required_draws: float
    deep: tuple[RequiredDraw, ...]
    shallow: tuple[RequiredDraw, ...]


@dataclass(frozen=True)
class ProbeRun:
    instrument: AdaptiveInstrument
    ratio: str
    params: AdaptiveParams
    summary: StratumSummary
    heterogeneity_spread: float
    min_band_gap: float
    false_stop_ci_upper_le_alpha: bool
    headline: str
    precheck: RegionPrecheck


def probe_params() -> AdaptiveParams:
    params = AdaptiveParams(b=PROBE_B, alpha=DEFAULT_ALPHA, b_max=PROBE_B_MAX)
    # Pinned high enough that the empirical-Bernstein arm can resolve shallow
    # in-band cases whose equivalence budget is set by delta - |Delta|.
    assert params.b == PROBE_B
    assert params.b_max == PROBE_B_MAX
    return params


def _reference_seed(case_seed: int) -> int:
    return 90_000 + case_seed


def _fixed_seed(case_seed: int) -> int:
    return 180_000 + case_seed


def _required_reference_draws(
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    y: np.ndarray,
    *,
    seed: int,
) -> int | None:
    for result in fixed_b_sweep(
        scores_a,
        scores_b,
        y,
        grid=REQUIRED_DRAW_GRID,
        margin=DEFAULT_DELTA,
        alpha=DEFAULT_ALPHA,
        seed=seed,
    ):
        if result.decision != "unresolved":
            return result.b
    return None


def _assess_case(
    tier: str, seed: int, scores: tuple[np.ndarray, np.ndarray, np.ndarray]
) -> RequiredDraw:
    scores_a, scores_b, y = scores
    plugin_delta = delta(scores_a, scores_b, y)
    stratum = classify_delta(plugin_delta, DEFAULT_DELTA)
    resolved = False
    try:
        fixed_budget_reference(
            scores_a, scores_b, y, seed=_reference_seed(seed), b_ref=DEFAULT_B_REF
        )
        resolved = True
    except UnresolvedReferenceError:
        resolved = False
    required = (
        _required_reference_draws(scores_a, scores_b, y, seed=_reference_seed(seed))
        if resolved
        else None
    )
    return RequiredDraw(
        tier=tier,
        seed=seed,
        abs_delta=abs(plugin_delta),
        required_draws=required,
        reference_resolved=resolved,
        stratum=stratum,
    )


def _mix_counts(deep_ratio: int, shallow_ratio: int, *, cases_per_ratio: int) -> tuple[int, int]:
    unit = cases_per_ratio // (deep_ratio + shallow_ratio)
    deep = deep_ratio * unit
    shallow = shallow_ratio * unit
    return deep, shallow


def build_mixed_cases(
    *,
    deep_ratio: int,
    shallow_ratio: int,
    seed: int = PROBE_BASE_SEED,
    shallow_abs_delta: float,
    cases_per_ratio: int = PROBE_CASES_PER_RATIO,
) -> tuple[MixedEquivalenceCase, ...]:
    deep, shallow = _mix_counts(deep_ratio, shallow_ratio, cases_per_ratio=cases_per_ratio)
    return mixed_equivalence(
        seed=seed,
        deep=deep,
        shallow=shallow,
        shallow_abs_delta=shallow_abs_delta,
    )


def precheck_region(
    *,
    deep_ratio: int = 1,
    shallow_ratio: int = 1,
    seed: int = PROBE_BASE_SEED,
    cases_per_ratio: int = PRECHECK_CASES_PER_RATIO,
) -> RegionPrecheck:
    deep_count, shallow_count = _mix_counts(
        deep_ratio, shallow_ratio, cases_per_ratio=cases_per_ratio
    )
    for candidate in SHALLOW_TARGET_CANDIDATES:
        cases = mixed_equivalence(
            seed=seed,
            deep=deep_count,
            shallow=shallow_count,
            shallow_abs_delta=candidate,
        )
        assessed = tuple(_assess_case(tier, case_seed, scores) for tier, case_seed, scores in cases)
        deep = tuple(item for item in assessed if item.tier == "deep")
        shallow = tuple(item for item in assessed if item.tier == "shallow")
        deep_required = [item.required_draws for item in deep if item.required_draws is not None]
        shallow_required = [
            item.required_draws for item in shallow if item.required_draws is not None
        ]
        shallow_scored = [
            item
            for item in shallow
            if item.stratum == "equivalent"
            and item.reference_resolved
            and item.required_draws is not None
        ]
        shallow_mean = fmean(shallow_required) if shallow_required else 0.0
        deep_mean = fmean(deep_required) if deep_required else 0.0
        if shallow_scored and len(shallow_scored) == len(shallow) and shallow_mean > deep_mean:
            return RegionPrecheck(
                shallow_abs_delta=candidate,
                non_empty=True,
                deep_mean_required_draws=deep_mean,
                shallow_mean_required_draws=shallow_mean,
                deep=deep,
                shallow=shallow,
            )
    return RegionPrecheck(
        shallow_abs_delta=None,
        non_empty=False,
        deep_mean_required_draws=0.0,
        shallow_mean_required_draws=0.0,
        deep=(),
        shallow=(),
    )


def _run_case(
    tier: str,
    case_seed: int,
    scores: tuple[np.ndarray, np.ndarray, np.ndarray],
    params: AdaptiveParams,
    *,
    instrument: AdaptiveInstrument,
) -> MemberRun:
    scores_a, scores_b, y = scores
    plugin_delta = delta(scores_a, scores_b, y)
    stratum = classify_delta(plugin_delta, DEFAULT_DELTA)
    reference_decision: Decision | None = None
    reference_unresolved = False
    try:
        reference = fixed_budget_reference(
            scores_a,
            scores_b,
            y,
            seed=_reference_seed(case_seed),
            b_ref=DEFAULT_B_REF,
        )
        reference_decision = reference.decision
    except UnresolvedReferenceError:
        reference_unresolved = True

    adaptive = adaptive_decision(
        scores_a,
        scores_b,
        y,
        margin=DEFAULT_DELTA,
        alpha=params.alpha,
        b=params.b,
        b_max=params.b_max,
        seed=_reference_seed(case_seed),
        instrument=instrument,
    )
    fixed_decisions = {
        result.b: result.decision
        for result in fixed_b_sweep(
            scores_a,
            scores_b,
            y,
            grid=FIXED_B_GRID,
            margin=DEFAULT_DELTA,
            alpha=DEFAULT_ALPHA,
            seed=_fixed_seed(case_seed),
        )
    }
    return MemberRun(
        member=f"mixed_equivalence_{tier}",
        stratum=stratum,
        seed=case_seed,
        reference_decision=reference_decision,
        adaptive_decision=adaptive.decision,
        adaptive_draws=adaptive.draws_consumed,
        reference_unresolved=reference_unresolved,
        fixed_decisions=fixed_decisions,
    )


def _headline(summary: StratumSummary) -> str:
    passes_false_stop = summary.false_stop_ci[1] <= DEFAULT_ALPHA
    flips = (
        summary.pareto_best_savings_ratio >= TARGET_SAVINGS_RATIO
        and not summary.fixed_b_dominating_adaptive
        and passes_false_stop
    )
    return "flip" if flips else "deep-negative"


def _summarize_probe_stratum(runs: list[MemberRun]) -> StratumSummary:
    summary = _summarize_stratum("equivalent", runs)
    scored = [run for run in runs if run.reference_decision is not None]
    fixed_false_stop_rates = {
        b: (
            sum(
                run.fixed_decisions[b] != "unresolved"
                and run.fixed_decisions[b] != run.reference_decision
                for run in scored
            )
            / len(scored)
        )
        for b in FIXED_B_GRID
    }
    released_pareto = pareto_verdict(
        adaptive_false_stop_rate=summary.false_stop_rate,
        adaptive_nondecision_rate=summary.abstain_rate,
        adaptive_draws=tuple(run.adaptive_draws for run in scored),
        fixed_false_stop_rates=fixed_false_stop_rates,
        fixed_nondecision_rates=summary.fixed_b_unresolved_rates,
        target_savings=TARGET_SAVINGS_RATIO,
    )
    assert released_pareto.best_savings_ratio == summary.pareto_best_savings_ratio
    assert released_pareto.fixed_b_dominating_adaptive == summary.fixed_b_dominating_adaptive
    return summary


def run_probe(
    *,
    instrument: AdaptiveInstrument,
    deep_ratio: int,
    shallow_ratio: int,
    precheck: RegionPrecheck | None = None,
    cases_per_ratio: int = PROBE_CASES_PER_RATIO,
) -> ProbeRun:
    if precheck is None:
        precheck = precheck_region(deep_ratio=deep_ratio, shallow_ratio=shallow_ratio)
    if not precheck.non_empty or precheck.shallow_abs_delta is None:
        empty_summary = StratumSummary(
            stratum="equivalent",
            scored=0,
            false_stops=0,
            false_stop_rate=0.0,
            false_stop_ci=wilson_interval(0, 0),
            draws_p50=0.0,
            draws_p90=0.0,
            draws_p99=0.0,
            abstain_rate=0.0,
            reference_unresolved=0,
            fixed_b_unresolved_rates={b: 0.0 for b in FIXED_B_GRID},
            adaptive_dominated_fixed_b=(),
            fixed_b_dominating_adaptive=(),
            pareto_best_savings_ratio=0.0,
        )
        return ProbeRun(
            instrument=instrument,
            ratio=f"{deep_ratio}:{shallow_ratio}",
            params=probe_params(),
            summary=empty_summary,
            heterogeneity_spread=0.0,
            min_band_gap=0.0,
            false_stop_ci_upper_le_alpha=False,
            headline="reference-resolving-power",
            precheck=precheck,
        )

    assert probe_params().b_max == PROBE_B_MAX
    cases = build_mixed_cases(
        deep_ratio=deep_ratio,
        shallow_ratio=shallow_ratio,
        shallow_abs_delta=precheck.shallow_abs_delta,
        cases_per_ratio=cases_per_ratio,
    )
    deltas = [abs(delta(scores_a, scores_b, y)) for _tier, _seed, (scores_a, scores_b, y) in cases]
    runs = [
        _run_case(tier, case_seed, scores, probe_params(), instrument=instrument)
        for tier, case_seed, scores in cases
    ]
    scored_equivalent = [
        run for run in runs if run.stratum == "equivalent" and run.reference_decision is not None
    ]
    summary = _summarize_probe_stratum(scored_equivalent)
    headline = _headline(summary)
    return ProbeRun(
        instrument=instrument,
        ratio=f"{deep_ratio}:{shallow_ratio}",
        params=probe_params(),
        summary=summary,
        heterogeneity_spread=max(deltas) - min(deltas),
        min_band_gap=min(DEFAULT_DELTA - item for item in deltas),
        false_stop_ci_upper_le_alpha=summary.false_stop_ci[1] <= DEFAULT_ALPHA,
        headline=headline,
        precheck=precheck,
    )


def _diagnostic_for_instrument(instrument: AdaptiveInstrument) -> dict[str, object]:
    result = run_benchmark(
        n_tune=1,
        n_test=32,
        instrument=instrument,
        candidates=(probe_params(),),
    )
    equivalent = [
        run
        for run in result.runs
        if run.stratum == "equivalent" and run.reference_decision is not None
    ]
    draws = [run.adaptive_draws for run in equivalent]
    band_gaps = []
    for run in equivalent:
        params, _generator = BATTERY[run.member]
        scores_a, scores_b, y = generate(replace(params, seed=run.seed))
        band_gaps.append(DEFAULT_DELTA - abs(delta(scores_a, scores_b, y)))
    return {
        "instrument": instrument,
        "scored": len(equivalent),
        "draws_p50": float(np.percentile(draws, 50)),
        "draws_p90": float(np.percentile(draws, 90)),
        "draws_p99": float(np.percentile(draws, 99)),
        "draws_cv": float(np.std(draws) / np.mean(draws)) if draws else 0.0,
        "band_gap_p50": float(np.percentile(band_gaps, 50)),
        "band_gap_p90": float(np.percentile(band_gaps, 90)),
        "band_gap_p99": float(np.percentile(band_gaps, 99)),
        "band_gap_cv": float(np.std(band_gaps) / np.mean(band_gaps)) if band_gaps else 0.0,
    }


def write_diagnostic() -> tuple[dict[str, object], ...]:
    payload = tuple(_diagnostic_for_instrument(instrument) for instrument in ("eb", "betting"))
    lines = [
        "# Equivalence Stratum Diagnostic",
        "",
        (
            "This near-circular diagnostic only checks that the frozen natural "
            "`equivalent` stratum is generator-homogeneous; the verdict comes from "
            "the mixed probe, not this table."
        ),
        "",
        "| instrument | scored | adaptive draws p50/p90/p99 | draws CV | "
        "delta - `|Delta|` p50/p90/p99 | gap CV |",
        "| --- | ---: | --- | ---: | --- | ---: |",
    ]
    for item in payload:
        draws = f"{item['draws_p50']:.0f}/{item['draws_p90']:.0f}/{item['draws_p99']:.0f}"
        gaps = f"{item['band_gap_p50']:.4f}/{item['band_gap_p90']:.4f}/{item['band_gap_p99']:.4f}"
        lines.append(
            f"| {item['instrument']} | {item['scored']} | {draws} | "
            f"{item['draws_cv']:.3f} | {gaps} | {item['band_gap_cv']:.3f} |"
        )
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    DIAGNOSTIC_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def _json_payload(primary: ProbeRun, stability: tuple[ProbeRun, ...]) -> dict[str, object]:
    payload = asdict(primary)
    payload["stability"] = [asdict(item) for item in stability]
    return payload


def _jsonable(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _write_probe_json(primary: ProbeRun, stability: tuple[ProbeRun, ...]) -> None:
    path = PROBE_DIR / f"probe-{primary.instrument}.json"
    path.write_text(
        json.dumps(_jsonable(_json_payload(primary, stability)), indent=2),
        encoding="utf-8",
    )


def _stable_headline(probes: tuple[ProbeRun, ...]) -> str:
    headlines = {probe.headline for probe in probes}
    if "reference-resolving-power" in headlines:
        return "reference-resolving-power"
    if headlines == {"flip"}:
        return "flip"
    if "flip" in headlines:
        return "fixture-tuning-artifact"
    return "deep-negative"


def _write_verdict(eb: tuple[ProbeRun, ...], betting: tuple[ProbeRun, ...]) -> str:
    arm_headlines = {"eb": _stable_headline(eb), "betting": _stable_headline(betting)}
    if "reference-resolving-power" in arm_headlines.values():
        overall = "reference-resolving-power"
        detail = "the engineered shallow tier could not be proven scored at B_ref=320."
    elif "fixture-tuning-artifact" in arm_headlines.values():
        overall = "fixture-tuning-artifact"
        detail = "a flip was sensitive to the deep:shallow ratio."
    elif "flip" in arm_headlines.values():
        overall = "flip"
        detail = "at least one adaptive instrument met the fixed-B Pareto and false-stop gates."
    else:
        overall = "deep-negative"
        detail = "no adaptive instrument met the fixed-B Pareto and false-stop gates."

    lines = [
        "# Equivalence-Band Savings Verdict",
        "",
        f"Headline verdict: **{overall}** — {detail}",
        "",
        "| arm | stable headline | primary ratio | scored | median draws | best savings | "
        "fixed-B dominators | abstain | false stops | 95% CI |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |",
    ]
    for probe in (eb[0], betting[0]):
        ci = f"[{probe.summary.false_stop_ci[0]:.4f}, {probe.summary.false_stop_ci[1]:.4f}]"
        dominators = ", ".join(str(b) for b in probe.summary.fixed_b_dominating_adaptive) or "none"
        lines.append(
            f"| {probe.instrument} | {arm_headlines[probe.instrument]} | {probe.ratio} | "
            f"{probe.summary.scored} | {probe.summary.draws_p50:.0f} | "
            f"{probe.summary.pareto_best_savings_ratio:.2f}x | {dominators} | "
            f"{probe.summary.abstain_rate:.4f} | {probe.summary.false_stops} | {ci} |"
        )
    lines.extend(
        [
            "",
            (
                f"Precheck selected shallow |Delta| ~= {eb[0].precheck.shallow_abs_delta}; "
                f"deep mean required draws {eb[0].precheck.deep_mean_required_draws:.1f}, "
                f"shallow mean required draws {eb[0].precheck.shallow_mean_required_draws:.1f}."
            ),
            (
                "The headline is mechanically derived from the JSON fields and checked "
                f"across ratios {', '.join(probe.ratio for probe in eb)}."
            ),
        ]
    )
    VERDICT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return overall


def run_and_write_probe() -> str:
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    write_diagnostic()
    all_probes: dict[AdaptiveInstrument, tuple[ProbeRun, ...]] = {}
    prechecks = {
        (deep, shallow): precheck_region(
            deep_ratio=deep,
            shallow_ratio=shallow,
            cases_per_ratio=PROBE_CASES_PER_RATIO,
        )
        for deep, shallow in PROBE_RATIOS
    }
    for instrument in ("eb", "betting"):
        probe_list: list[ProbeRun] = []
        for deep, shallow in PROBE_RATIOS:
            probe_list.append(
                run_probe(
                    instrument=instrument,
                    deep_ratio=deep,
                    shallow_ratio=shallow,
                    precheck=prechecks[(deep, shallow)],
                )
            )
        probes = tuple(probe_list)
        _write_probe_json(probes[0], probes)
        all_probes[instrument] = probes
    return _write_verdict(all_probes["eb"], all_probes["betting"])


def deterministic_probe_signature() -> tuple[object, ...]:
    precheck = precheck_region()
    probe = run_probe(
        instrument="betting",
        deep_ratio=1,
        shallow_ratio=1,
        precheck=precheck,
        cases_per_ratio=PRECHECK_CASES_PER_RATIO,
    )
    return (
        precheck.shallow_abs_delta,
        round(precheck.deep_mean_required_draws, 6),
        round(precheck.shallow_mean_required_draws, 6),
        probe.summary.scored,
        probe.summary.false_stops,
        probe.summary.draws_p50,
        round(probe.summary.pareto_best_savings_ratio, 6),
        probe.headline,
    )
