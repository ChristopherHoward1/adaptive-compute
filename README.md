# Adaptive Compute

Monte Carlo evaluation often runs for a fixed simulation budget: a set number of
bootstrap resamples or permutations. How many draws it takes to resolve the
downstream decision varies from case to case, so a fixed budget can spend more
draws than an easy decision needs and fewer than a hard one requires. This
project tests whether a procedure can instead stop once further draws are
unlikely to change the decision, while bounding how often it disagrees with a
large fixed-budget reference.

## Research question

Can we stop a Monte Carlo procedure once additional draws are unlikely to change
the decision?

Made precise: for an iterative Monte Carlo procedure on a fixed dataset, can an
adaptive stopping rule reach the same decision as a large fixed-budget reference
run using materially fewer draws, while keeping the probability of a different
decision below a bound α (here 0.05) in every difficulty stratum? The experiment
design fixes "materially fewer" in advance as a median-draw reduction of at least
2×, required in each stratum rather than on average.

The decision under test is an equivalence-band comparison of two models on a
fixed evaluation set. Given a margin δ, the procedure returns one of:

- **A better than B** — the resolved interval for the metric difference lies above +δ;
- **B better than A** — it lies below −δ;
- **equivalent** — it lies within [−δ, +δ];
- **abstain** — the budget is exhausted before the interval resolves.

## Compute and stopping

Compute is measured in Monte Carlo draws (a bootstrap resample, later a
permutation or sampled attribution coalition), not wall-clock time.

The evaluation dataset stays fixed; only the number of simulation draws grows.
The sequential randomness comes from the simulation, not from collecting new
observations, so this differs from sequential sampling of a population: any
interval about the population is as valid as the underlying method, and stopping
does not touch it. The stopping time does depend on the simulated path, though. A
rule that halts the first time a running band clears δ stops preferentially on
paths that happened to wander across it, and a fixed-time interval's coverage is
guaranteed only at a preset number of draws, not at a data-dependent stopping
time. The rule therefore uses an anytime-valid confidence sequence, whose
coverage holds simultaneously at every budget and so survives optional stopping.
The target is the decision the same procedure would reach with unlimited draws on
that exact data; for the synthetic cases that decision is known by construction,
and the fixed-budget reference run recovers it.

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

Decision agreement held. On every scored non-boundary case in the battery the
adaptive procedure resolved and returned the reference decision. The false-stop
rate was 0 in each difficulty stratum (Wilson upper 95% bound below α = 0.05),
including the heavy-tailed cases, and the procedure never abstained.

Compute savings did not. H1 asks the adaptive rule to use at least 2× fewer draws
than a fixed budget that reaches the same decisions at least as reliably, and to
do so in every stratum. It met this in none of them:

- **easy and equivalent strata** — a fixed budget as small as 32 resamples
  reached the same decisions with the same reliability, while the adaptive rule
  used a median of 128 draws (easy) and 768 (equivalent).
- **moderate stratum** — the adaptive rule was more reliable than every fixed
  budget in the sweep {32, 64, 128, 320}, but used more draws than all of them
  (median 448), so no equally reliable fixed budget was expensive enough for it to
  beat by 2×.

The procedure agreed with the reference throughout but did not save draws against
the fixed-budget sweep. Details in [`PLAN.md`](PLAN.md).

## What's next

The stopping rule uses a finite-horizon empirical-Bernstein confidence sequence
for the bounded mean difference, following Howard et al. (2021), with a tuned
draw cap of `B_max = 2048`. At the budgets where a fixed-budget bootstrap already
resolves these cases, this band's half-width stays wider than δ, so an
equivalence decision in particular cannot resolve until many more draws
accumulate. This experiment evaluates that one stopping rule; it does not
establish that adaptive stopping is generally compute-inefficient.

The next experiment replaces the band with a betting confidence sequence
(Waudby-Smith & Ramdas, 2024), which the literature reports as tighter for
bounded variables, and holds the decision task, battery, and 2× criterion fixed.
Whether tighter finite-budget bands translate into earlier stopping is the open
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

Every run is reproducible from its generator parameters and seed.

## License

See [`LICENSE`](LICENSE).
