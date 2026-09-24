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

## Current result (v2026.9.6)

H1 is not supported. The research line is paused for a re-think.

Decision agreement held throughout. In every experiment, on every scored
non-boundary case, the adaptive procedure returned the reference decision. The
false-stop rate was 0 in each difficulty stratum, heavy-tailed cases included.

Compute savings did not hold up. Across four experiments:

- **Empirical-Bernstein band (v2026.9.3).** The adaptive rule met the 2× criterion
  in no stratum. Its median draws (448 moderate, 768 equivalent) exceeded every
  budget in the fixed-B sweep {32, 64, 128, 320}.
- **Betting confidence sequence (v2026.9.4).** A Waudby-Smith–Ramdas betting band
  cut median draws 2–5× and passed the 2× criterion in the easy and moderate
  strata. The equivalent stratum still failed, because small fixed budgets already
  resolve equivalence.
- **Equivalence band (v2026.9.5).** That failure is structural. The fixed-B
  percentile interval is a fixed-width functional whose half-width plateaus near
  the reference budget. An anytime-valid band must instead shrink Monte Carlo
  error below δ. Fixed-B dominates both instruments inside [−δ, +δ].
- **Directional decisions.** The adaptive procedure estimates `E*[Δ*]`, which
  equals the closed-form plug-in `Δ(E)` up to bootstrap bias. A zero-draw rule on
  `Δ(E)` matched the reference on 586/586 held-out cases, and fixed-B at `B=32`
  agreed on 99.4% of directional cases. So no directional savings exist to find.

A plan-stage prototype on SHAP top-k attributions, where no zero-draw shortcut
exists, found adaptive about 2.3× cheaper than a certified fixed budget. It was
not 2× cheaper than exact enumeration, and it cost more than an uncertified fixed
budget that was never wrong. The unit was withdrawn before implementation.

In each setup, certifying a decision cost more than simply being right. Details:
[`knowledge/equivalence-band-savings.md`](knowledge/equivalence-band-savings.md),
[`knowledge/anytime-valid-band.md`](knowledge/anytime-valid-band.md),
[`knowledge/shap-topk-savings.md`](knowledge/shap-topk-savings.md).

## What's next

A further experiment needs an application that actually requires a per-case
certificate, where an uncertified cheap answer is not acceptable. Without one,
the negative result stands as the finding. See [`PLAN.md`](PLAN.md).

## The code

Python 3.12, `src/` layout, numpy-only runtime.

| Module | Role |
| --- | --- |
| `metrics.py` | numpy-only AUC and paired `Δ` |
| `generators.py` | the five-member frozen synthetic battery (near-boundary, small-effect, heavy-tailed, rare-event/imbalance, easy/lopsided) |
| `bootstrap.py` | paired row-resampler with exact draw accounting and `SeedSequence.spawn` branches |
| `reference.py` | the fixed-budget percentile-bootstrap decision |
| `adaptive.py` | the blind adaptive bootstrap controller (empirical-Bernstein confidence sequence) |
| `betting.py` | Waudby-Smith–Ramdas betting confidence sequence, selectable via `instrument="betting"` |
| `sweep.py` | fixed-B sweep and Pareto helpers |
| `strata.py` | plug-in `Δ(E)` difficulty classification |
| `benchmark.py` | offline adaptive-vs-reference harness |
| `equiv_probe.py` | equivalence-band probe |
| `eval.py` | `python -m adaptive_compute.eval` entry point |

```bash
python -m adaptive_compute.eval --check   # fast decision check
python -m adaptive_compute.eval --run     # offline benchmark, writes results.{md,json}
python -m adaptive_compute.eval --compare # EB vs betting A/B on the same stream
python -m adaptive_compute.eval --equiv-probe  # equivalence-band probe
```

Every run is reproducible from its generator parameters and seed.

## License

See [`LICENSE`](LICENSE).
