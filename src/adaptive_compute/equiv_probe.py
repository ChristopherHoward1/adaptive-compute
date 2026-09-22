"""Offline equivalence-band estimator-asymmetry probe."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from math import ceil
from pathlib import Path

import numpy as np

from adaptive_compute.adaptive import (
    AdaptiveInstrument,
    adaptive_decision,
    empirical_bernstein_bounds,
)
from adaptive_compute.benchmark import (
    FIXED_B_GRID,
    TARGET_SAVINGS_RATIO,
    AdaptiveParams,
    MemberRun,
    StratumSummary,
    _summarize_stratum,
    run_benchmark,
)
from adaptive_compute.betting import BettingCSState, _mean_grid
from adaptive_compute.bootstrap import adaptive_bootstrap_stream, paired_bootstrap_deltas
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
DETERMINISM_CASES_PER_RATIO = 12
PROBE_RATIOS = ((1, 1), (2, 1))
FIXTURE_MAX_ABS_DELTA = 0.024
FIXTURE_MIN_ABS_DELTA_SPREAD = 0.020
MAX_ABSTAIN_RATE = 0.05
MIN_REFERENCE_RESOLVED_FRACTION = 0.95
DIAGNOSTIC_FIXED_B_GRID = (32, 64, 128, DEFAULT_B_REF, 640, 960, 4 * DEFAULT_B_REF)
DIAGNOSTIC_ADAPTIVE_GRID = (
    64,
    128,
    192,
    DEFAULT_B_REF,
    512,
    768,
    1024,
    1536,
    2048,
    4096,
    PROBE_B_MAX,
)
PLATEAU_TOL = 4.0 * DEFAULT_DELTA / np.sqrt(DEFAULT_B_REF)


@dataclass(frozen=True)
class CaseMechanism:
    position: str
    seed: int
    abs_delta: float
    fixed_half_widths: dict[int, float]
    cheapest_fixed_equivalent: int | None
    adaptive_half_widths: dict[int, float]
    adaptive_crossing_draws: int | None


@dataclass(frozen=True)
class MechanismDiagnostic:
    instrument: AdaptiveInstrument
    max_looks: int
    fixed_b_grid: tuple[int, ...]
    adaptive_draw_grid: tuple[int, ...]
    fixed_width_at_b_ref: float
    fixed_width_at_4x_b_ref: float
    fixed_plateau_gap: float
    eb_width_at_b_ref: float | None
    adaptive_crossing_median: float
    cheapest_fixed_equivalent_median: float
    cases: tuple[CaseMechanism, ...]


@dataclass(frozen=True)
class ProbeRun:
    instrument: AdaptiveInstrument
    ratio: str
    params: AdaptiveParams
    summary: StratumSummary
    mechanism: MechanismDiagnostic
    abs_delta_spread: float
    min_band_gap: float
    generated: int
    scored: int
    reference_resolved_fraction: float
    false_stop_ci_upper_le_alpha: bool
    headline: str


def probe_params() -> AdaptiveParams:
    params = AdaptiveParams(b=PROBE_B, alpha=DEFAULT_ALPHA, b_max=PROBE_B_MAX)
    assert params.b == PROBE_B
    assert params.b_max == PROBE_B_MAX
    return params


def _reference_seed(case_seed: int) -> int:
    return 90_000 + case_seed


def _fixed_seed(case_seed: int) -> int:
    return 180_000 + case_seed


def _mix_counts(center_ratio: int, offset_ratio: int, *, cases_per_ratio: int) -> tuple[int, int]:
    unit = cases_per_ratio // (center_ratio + offset_ratio)
    return center_ratio * unit, offset_ratio * unit


def build_mixed_cases(
    *,
    center_ratio: int = 1,
    offset_ratio: int = 1,
    seed: int = PROBE_BASE_SEED,
    cases_per_ratio: int = PROBE_CASES_PER_RATIO,
) -> tuple[MixedEquivalenceCase, ...]:
    center, offset = _mix_counts(
        center_ratio,
        offset_ratio,
        cases_per_ratio=cases_per_ratio,
    )
    return mixed_equivalence(
        seed=seed,
        center=center,
        offset=offset,
        max_abs_delta=FIXTURE_MAX_ABS_DELTA,
    )


def _run_case(
    position: str,
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
    assert set(fixed_decisions) == set(FIXED_B_GRID)
    return MemberRun(
        member=f"mixed_equivalence_{position}",
        stratum=stratum,
        seed=case_seed,
        reference_decision=reference_decision,
        adaptive_decision=adaptive.decision,
        adaptive_draws=adaptive.draws_consumed,
        reference_unresolved=reference_unresolved,
        fixed_decisions=fixed_decisions,
    )


def _half_width(interval: tuple[float, float]) -> float:
    return (interval[1] - interval[0]) / 2.0


def _fixed_half_widths(
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    y: np.ndarray,
    *,
    seed: int,
) -> tuple[dict[int, float], int | None]:
    bootstrap = paired_bootstrap_deltas(
        scores_a,
        scores_b,
        y,
        draws=max(DIAGNOSTIC_FIXED_B_GRID),
        seed=seed,
    )
    widths: dict[int, float] = {}
    cheapest: int | None = None
    for b in DIAGNOSTIC_FIXED_B_GRID:
        lower, upper = np.percentile(
            bootstrap.deltas[:b],
            [100.0 * DEFAULT_ALPHA / 2.0, 100.0 * (1.0 - DEFAULT_ALPHA / 2.0)],
        )
        widths[b] = (float(upper) - float(lower)) / 2.0
        if cheapest is None and lower >= -DEFAULT_DELTA and upper <= DEFAULT_DELTA:
            cheapest = b
    return widths, cheapest


def _adaptive_half_widths(
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    y: np.ndarray,
    *,
    seed: int,
    params: AdaptiveParams,
    instrument: AdaptiveInstrument,
) -> tuple[dict[int, float], int | None]:
    values = np.empty(params.b_max, dtype=np.float64)
    widths: dict[int, float] = {}
    crossing: int | None = None
    draws = 0
    max_looks = ceil(params.b_max / params.b)
    betting_state = BettingCSState(grid=_mean_grid(401)) if instrument == "betting" else None
    for batch in adaptive_bootstrap_stream(
        scores_a,
        scores_b,
        y,
        batch_draws=params.b,
        max_draws=params.b_max,
        seed=seed,
    ):
        current = batch.draws_consumed
        values[draws : draws + current] = batch.deltas[:current]
        draws += current
        if instrument == "eb":
            bounds = empirical_bernstein_bounds(
                values[:draws],
                alpha=params.alpha,
                max_looks=max_looks,
            )
        else:
            assert betting_state is not None
            betting_state.update_delta(batch.deltas[:current])
            bounds = betting_state.bounds(alpha=params.alpha)
        width = _half_width(bounds)
        if draws in DIAGNOSTIC_ADAPTIVE_GRID:
            widths[draws] = width
        if crossing is None and width < DEFAULT_DELTA:
            crossing = draws
        if draws >= max(DIAGNOSTIC_ADAPTIVE_GRID) and crossing is not None:
            break
    return widths, crossing


def mechanism_diagnostic(
    instrument: AdaptiveInstrument,
    cases: tuple[MixedEquivalenceCase, ...],
    *,
    params: AdaptiveParams | None = None,
) -> MechanismDiagnostic:
    params = probe_params() if params is None else params
    case_payload: list[CaseMechanism] = []
    for position, case_seed, (scores_a, scores_b, y) in cases:
        fixed_widths, cheapest_fixed = _fixed_half_widths(
            scores_a,
            scores_b,
            y,
            seed=_fixed_seed(case_seed),
        )
        adaptive_widths, adaptive_crossing = _adaptive_half_widths(
            scores_a,
            scores_b,
            y,
            seed=_reference_seed(case_seed),
            params=params,
            instrument=instrument,
        )
        case_payload.append(
            CaseMechanism(
                position=position,
                seed=case_seed,
                abs_delta=abs(delta(scores_a, scores_b, y)),
                fixed_half_widths=fixed_widths,
                cheapest_fixed_equivalent=cheapest_fixed,
                adaptive_half_widths=adaptive_widths,
                adaptive_crossing_draws=adaptive_crossing,
            )
        )

    fixed_b_ref = float(np.median([case.fixed_half_widths[DEFAULT_B_REF] for case in case_payload]))
    fixed_4x = float(
        np.median([case.fixed_half_widths[4 * DEFAULT_B_REF] for case in case_payload])
    )
    crossings = [
        case.adaptive_crossing_draws
        for case in case_payload
        if case.adaptive_crossing_draws is not None
    ]
    cheapest = [
        case.cheapest_fixed_equivalent
        for case in case_payload
        if case.cheapest_fixed_equivalent is not None
    ]
    eb_width_at_b_ref = (
        float(np.median([case.adaptive_half_widths[DEFAULT_B_REF] for case in case_payload]))
        if instrument == "eb"
        else None
    )
    return MechanismDiagnostic(
        instrument=instrument,
        max_looks=ceil(params.b_max / params.b),
        fixed_b_grid=DIAGNOSTIC_FIXED_B_GRID,
        adaptive_draw_grid=DIAGNOSTIC_ADAPTIVE_GRID,
        fixed_width_at_b_ref=fixed_b_ref,
        fixed_width_at_4x_b_ref=fixed_4x,
        fixed_plateau_gap=abs(fixed_4x - fixed_b_ref),
        eb_width_at_b_ref=eb_width_at_b_ref,
        adaptive_crossing_median=float(np.median(crossings)) if crossings else float("inf"),
        cheapest_fixed_equivalent_median=float(np.median(cheapest)) if cheapest else float("inf"),
        cases=tuple(case_payload),
    )


def _headline(summary: StratumSummary) -> str:
    fixed_dominates = bool(summary.fixed_b_dominating_adaptive)
    adaptive_flip = (
        summary.pareto_best_savings_ratio >= TARGET_SAVINGS_RATIO
        and not fixed_dominates
        and summary.false_stop_ci[1] <= DEFAULT_ALPHA
    )
    return "adaptive-flip" if adaptive_flip else "deep-negative"


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


def _assert_probe_guards(probe: ProbeRun) -> None:
    assert probe.params.b == PROBE_B
    assert probe.params.b_max == PROBE_B_MAX
    assert probe.reference_resolved_fraction >= MIN_REFERENCE_RESOLVED_FRACTION
    assert probe.summary.abstain_rate <= MAX_ABSTAIN_RATE
    assert probe.abs_delta_spread >= FIXTURE_MIN_ABS_DELTA_SPREAD
    assert probe.min_band_gap > 0.0
    assert probe.mechanism.fixed_plateau_gap <= PLATEAU_TOL
    if probe.instrument == "eb":
        assert probe.mechanism.eb_width_at_b_ref is not None
        assert probe.mechanism.eb_width_at_b_ref > DEFAULT_DELTA
    else:
        assert probe.mechanism.cheapest_fixed_equivalent_median < probe.summary.draws_p50


def run_probe(
    *,
    instrument: AdaptiveInstrument,
    center_ratio: int = 1,
    offset_ratio: int = 1,
    cases_per_ratio: int = PROBE_CASES_PER_RATIO,
) -> ProbeRun:
    params = probe_params()
    cases = build_mixed_cases(
        center_ratio=center_ratio,
        offset_ratio=offset_ratio,
        cases_per_ratio=cases_per_ratio,
    )
    abs_deltas = [
        abs(delta(scores_a, scores_b, y)) for _pos, _seed, (scores_a, scores_b, y) in cases
    ]
    assert max(abs_deltas) <= FIXTURE_MAX_ABS_DELTA + 1e-12
    assert all(item < DEFAULT_DELTA for item in abs_deltas)

    runs = [
        _run_case(position, case_seed, scores, params, instrument=instrument)
        for position, case_seed, scores in cases
    ]
    scored_equivalent = [
        run for run in runs if run.stratum == "equivalent" and run.reference_decision is not None
    ]
    summary = _summarize_probe_stratum(scored_equivalent)
    mechanism = mechanism_diagnostic(instrument, cases, params=params)
    generated = len(cases)
    resolved = generated - sum(run.reference_unresolved for run in runs)
    probe = ProbeRun(
        instrument=instrument,
        ratio=f"{center_ratio}:{offset_ratio}",
        params=params,
        summary=summary,
        mechanism=mechanism,
        abs_delta_spread=max(abs_deltas) - min(abs_deltas),
        min_band_gap=min(DEFAULT_DELTA - item for item in abs_deltas),
        generated=generated,
        scored=len(scored_equivalent),
        reference_resolved_fraction=resolved / generated if generated else 0.0,
        false_stop_ci_upper_le_alpha=summary.false_stop_ci[1] <= DEFAULT_ALPHA,
        headline=_headline(summary),
    )
    _assert_probe_guards(probe)
    return probe


def _natural_stratum_diagnostic(instrument: AdaptiveInstrument) -> dict[str, object]:
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


def _format_curve(widths: dict[int, float]) -> str:
    return ", ".join(f"{draws}:{width:.4f}" for draws, width in sorted(widths.items()))


def write_diagnostic(
    eb: ProbeRun,
    betting: ProbeRun,
) -> tuple[dict[str, object], ...]:
    natural = tuple(_natural_stratum_diagnostic(instrument) for instrument in ("eb", "betting"))
    lines = [
        "# Equivalence-Band Estimator Asymmetry",
        "",
        (
            "The fixture spans in-band positions only. It does not claim difficulty "
            "heterogeneity; the measured mechanism is fixed-width percentile intervals "
            "versus shrinking anytime-valid confidence sequences."
        ),
        "",
        "## Mechanism curves",
        "",
        (
            f"Scored with b={PROBE_B}, B_max={PROBE_B_MAX}, "
            f"max_looks={eb.mechanism.max_looks}, fixed-B scoring grid={FIXED_B_GRID}. "
            f"The diagnostic-only fixed curve samples through {4 * DEFAULT_B_REF} draws."
        ),
        "",
        "| arm | fixed w(B_ref) | fixed w(4*B_ref) | plateau gap | adaptive w(B_ref) | "
        "median adaptive crossing | median fixed B* |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for probe in (eb, betting):
        eb_width = (
            f"{probe.mechanism.eb_width_at_b_ref:.4f}"
            if probe.mechanism.eb_width_at_b_ref is not None
            else "n/a"
        )
        lines.append(
            f"| {probe.instrument} | {probe.mechanism.fixed_width_at_b_ref:.4f} | "
            f"{probe.mechanism.fixed_width_at_4x_b_ref:.4f} | "
            f"{probe.mechanism.fixed_plateau_gap:.4f} | {eb_width} | "
            f"{probe.mechanism.adaptive_crossing_median:.0f} | "
            f"{probe.mechanism.cheapest_fixed_equivalent_median:.0f} |"
        )
    lines.extend(
        [
            "",
            "## Representative case curves",
            "",
            "| arm | seed | `|Delta|` | w_fix(B) | w_ad(n) |",
            "| --- | ---: | ---: | --- | --- |",
        ]
    )
    for probe in (eb, betting):
        case = probe.mechanism.cases[-1]
        lines.append(
            f"| {probe.instrument} | {case.seed} | {case.abs_delta:.4f} | "
            f"{_format_curve(case.fixed_half_widths)} | "
            f"{_format_curve(case.adaptive_half_widths)} |"
        )
    lines.extend(
        [
            "",
            "## Natural equivalent stratum",
            "",
            (
                "This frozen-battery diagnostic is generator-homogeneous context only; "
                "the verdict is the scored in-band fixture above."
            ),
            "",
            "| instrument | scored | adaptive draws p50/p90/p99 | draws CV | "
            "delta - `|Delta|` p50/p90/p99 | gap CV |",
            "| --- | ---: | --- | ---: | --- | ---: |",
        ]
    )
    for item in natural:
        draws = f"{item['draws_p50']:.0f}/{item['draws_p90']:.0f}/{item['draws_p99']:.0f}"
        gaps = f"{item['band_gap_p50']:.4f}/{item['band_gap_p90']:.4f}/{item['band_gap_p99']:.4f}"
        lines.append(
            f"| {item['instrument']} | {item['scored']} | {draws} | "
            f"{item['draws_cv']:.3f} | {gaps} | {item['band_gap_cv']:.3f} |"
        )
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    DIAGNOSTIC_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return natural


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
    payload = asdict(primary)
    payload["stability"] = [asdict(item) for item in stability]
    path.write_text(json.dumps(_jsonable(payload), indent=2), encoding="utf-8")


def _stable_headline(probes: tuple[ProbeRun, ...]) -> str:
    return (
        "adaptive-flip"
        if all(probe.headline == "adaptive-flip" for probe in probes)
        else "deep-negative"
    )


def _dominators_text(summary: StratumSummary) -> str:
    return ", ".join(str(b) for b in summary.fixed_b_dominating_adaptive) or "none"


def _write_verdict(eb: tuple[ProbeRun, ...], betting: tuple[ProbeRun, ...]) -> str:
    arm_headlines = {"eb": _stable_headline(eb), "betting": _stable_headline(betting)}
    overall = (
        "deep-negative"
        if all(headline == "deep-negative" for headline in arm_headlines.values())
        else "adaptive-flip"
    )
    detail = (
        "fixed-B dominates both adaptive instruments inside the equivalence band"
        if overall == "deep-negative"
        else "at least one adaptive instrument beat the released fixed-B grid"
    )
    lines = [
        "# Equivalence-Band Savings Verdict",
        "",
        f"Headline verdict: **{overall}** — {detail}.",
        "",
        "| arm | stable headline | primary ratio | scored/generated | median draws | "
        "best savings | fixed-B dominators | abstain | ref resolved | false stops | 95% CI |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for probe in (eb[0], betting[0]):
        ci = f"[{probe.summary.false_stop_ci[0]:.4f}, {probe.summary.false_stop_ci[1]:.4f}]"
        lines.append(
            f"| {probe.instrument} | {arm_headlines[probe.instrument]} | {probe.ratio} | "
            f"{probe.scored}/{probe.generated} | {probe.summary.draws_p50:.0f} | "
            f"{probe.summary.pareto_best_savings_ratio:.2f}x | "
            f"{_dominators_text(probe.summary)} | {probe.summary.abstain_rate:.4f} | "
            f"{probe.reference_resolved_fraction:.3f} | {probe.summary.false_stops} | {ci} |"
        )
    lines.extend(
        [
            "",
            (
                f"Fixture cap: |Delta| <= {FIXTURE_MAX_ABS_DELTA:.3f}; "
                f"primary spread {eb[0].abs_delta_spread:.4f}; "
                f"minimum band gap {eb[0].min_band_gap:.4f}."
            ),
            (
                "Mechanism: EB has w_ad(B_ref)="
                f"{eb[0].mechanism.eb_width_at_b_ref:.4f} > delta={DEFAULT_DELTA:.4f}; "
                "betting resolves below B_ref, but its median fixed B*="
                f"{betting[0].mechanism.cheapest_fixed_equivalent_median:.0f} is below "
                f"its adaptive median {betting[0].summary.draws_p50:.0f}."
            ),
            (
                "The headline is mechanically derived from probe JSON fields and checked "
                f"across ratios {', '.join(probe.ratio for probe in eb)}."
            ),
        ]
    )
    VERDICT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return overall


def run_and_write_probe() -> str:
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    all_probes: dict[AdaptiveInstrument, tuple[ProbeRun, ...]] = {}
    for instrument in ("eb", "betting"):
        probes = tuple(
            run_probe(instrument=instrument, center_ratio=center, offset_ratio=offset)
            for center, offset in PROBE_RATIOS
        )
        _write_probe_json(probes[0], probes)
        all_probes[instrument] = probes
    write_diagnostic(all_probes["eb"][0], all_probes["betting"][0])
    return _write_verdict(all_probes["eb"], all_probes["betting"])


def deterministic_probe_signature() -> tuple[object, ...]:
    probe = run_probe(
        instrument="betting",
        center_ratio=1,
        offset_ratio=1,
        cases_per_ratio=DETERMINISM_CASES_PER_RATIO,
    )
    return (
        probe.summary.scored,
        probe.summary.false_stops,
        probe.summary.draws_p50,
        tuple(probe.summary.fixed_b_dominating_adaptive),
        round(probe.mechanism.fixed_plateau_gap, 6),
        round(probe.mechanism.cheapest_fixed_equivalent_median, 6),
        probe.headline,
    )
