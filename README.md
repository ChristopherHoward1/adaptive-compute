# Adaptive Compute

Monte-Carlo evaluation procedures usually run for a fixed number of draws —
"1000 bootstrap resamples" — chosen by convention rather than by what the
decision needs. When the answer is lopsided, most of those draws are wasted;
when it is close, the fixed budget may be too small to resolve it. This project
asks whether a procedure can instead stop once more draws are unlikely to change
the decision, with a stated bound on how often it disagrees with the full-budget
answer.

## Research question

Can we stop a Monte-Carlo procedure once additional draws are unlikely to change
the decision?

Made precise: for an iterative Monte-Carlo procedure on a fixed dataset, can an
adaptive stopping rule reach the same decision as a large fixed-budget run using
materially fewer draws, while keeping the probability of a different decision
below a preset bound α? "Materially fewer" is preregistered as a ≥2× median-draw
reduction, and it must hold in every difficulty stratum, not just on average.

The decision under test is an equivalence-band model comparison: given a margin
δ, is candidate model A better than reference model B by more than δ, worse by
more than δ, or practically equivalent, on a fixed evaluation set?

## What counts as compute

Compute is counted in Monte-Carlo draws (a bootstrap resample, a permutation,
later a sampled attribution coalition), not wall-clock time, so a reported saving
does not depend on the hardware.

The dataset stays fixed; only the Monte-Carlo budget grows. The target is the
decision the same procedure would reach with infinite draws on that exact data.
This is not sequential analysis: we never add data to learn about an unknown
population, so the validity of any interval is untouched by stopping. What
stopping can bias is the decision. A rule that halts the first time a running
band clears δ stops preferentially on paths that happened to wander across it, so
the band must be anytime-valid — safe to inspect after every batch.

## Documentation

- [`docs/research-definition.md`](docs/research-definition.md) — the question,
  the falsifiable hypotheses, and the validity threats.
- [`docs/prior-art.md`](docs/prior-art.md) — prior work on stopping guarantees
  (Gandy 2009; the confidence-sequence literature) and the narrower empirical
  question tested here.
- [`docs/experiment-design.md`](docs/experiment-design.md) — the synthetic
  battery, baselines, decision rule, and falsification criteria.

## Current result (v2026.9.3)

The first experiment does not support H1.

The adaptive procedure matched the full-budget reference decision on every
non-boundary case in the test battery, including the heavy-tailed condition. The
false-stop rate was 0 in every difficulty stratum (upper 95% CI below α = 0.05),
and it abstained on none of them.

It did not save draws. H1 requires a ≥2× median-draw reduction in every
non-boundary stratum, achieved against a fixed budget the adaptive rule
Pareto-dominates. The easy stratum clears this (2.5×), but the two strata that
decide the criterion do not: in the `equivalent` and `moderate` strata no fixed
budget in the sweep is dominated at any saving. A plain fixed budget reaches the
same decisions with fewer draws than the adaptive rule's median of 768 and 448
draws respectively. The procedure is reliable but more expensive than the
baseline it must beat.

Details in [`PLAN.md`](PLAN.md).

## What's next

Stopping time depends heavily on the width of the confidence band. The band used
here is a finite-horizon empirical-Bernstein confidence sequence (following
Howard et al. 2021), capped at a maximum budget of `B_max = 2048` draws. Its
bands are loose at the budgets tested, which is what pushes the draw count above
the fixed-budget grid. The negative result is therefore specific to this
instrument, not to adaptive stopping in general.

The next experiment replaces it with a tighter betting confidence sequence
(Waudby-Smith & Ramdas, 2024) and evaluates the same decision, battery, and ≥2×
criterion. Whether a tighter band materially reduces stopping time is the open
question.

## The code

Python 3.12, `src/` layout, numpy-only runtime.

| Module | Role |
| --- | --- |
| `metrics.py` | numpy-only AUC and paired `Δ` |
| `generators.py` | the five-member frozen synthetic battery (near-boundary, small-effect, heavy-tailed, rare-event/imbalance, easy/lopsided) |
| `bootstrap.py` | paired row-resampler with exact draw accounting and `SeedSequence.spawn` branches |
| `reference.py` | the fixed-budget percentile-bootstrap decision |
| `adaptive.py` | the blind adaptive bootstrap controller (empirical-Bernstein confidence sequence) |
| `sweep.py` | fixed-B sweep and Pareto helpers |
| `strata.py` | plug-in `Δ(E)` difficulty classification |
| `benchmark.py` | offline first-result harness |
| `eval.py` | `python -m adaptive_compute.eval` entry point |

```bash
python -m adaptive_compute.eval --check   # fast decision check
python -m adaptive_compute.eval --run     # offline benchmark, writes results.{md,json}
```

Every run is reproducible from its generator parameters and seed; the harness
records both.

## License

See [`LICENSE`](LICENSE).
