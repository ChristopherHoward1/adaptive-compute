# Adaptive Compute — Prior-Art Map

**Status:** v0, 2026-09-19. Purpose: prevent us from re-inventing a standard
technique and calling it novel. Each entry states *what it already solves* and
*which part of our problem it subsumes*.

**Citation caveat.** Entries are recorded by author / title / venue / year, which
we are confident of; exact DOIs and URLs should be re-verified against a primary
source before any are quoted in an external write-up. Where we are less certain of
a detail it is marked *(verify)*.

---

## The near-exact ancestors (v0 is an application of these)

These solve *most* of what v0's stopping rule does. v0 is not a new stopping
method; it is these methods applied to an equivalence-band model-comparison
decision, with an empirical savings/false-stop characterization.

- **Gandy, A. (2009). "Sequential Implementation of Monte Carlo Tests With
  Uniformly Bounded Resampling Risk." *JASA* 104(488), 1504–1511.**
  Subsumes: the core guarantee. A sequential rule for deciding the outcome of a
  Monte-Carlo test (e.g. is a p-value above or below a threshold) that grows the
  number of resamples adaptively while **uniformly bounding the "resampling
  risk"** — the probability that the sequential decision differs from the
  infinite-resample decision. This is almost exactly our "false-stop rate vs.
  B→∞, controlled below α", for a one-sided threshold. v0's job is to carry it to
  a *two-sided equivalence band* `[−δ, +δ]` and characterize savings.
- **Besag, J. & Clifford, P. (1991). "Sequential Monte Carlo p-values."
  *Biometrika* 78(2), 301–304.**
  Subsumes: the original idea of stopping Monte-Carlo resampling early once the
  p-value decision is clear, with valid error control. The direct ancestor of
  Gandy.
- **Andrews, D. W. K. & Buchinsky, M. (2000). "A Three-Step Method for Choosing
  the Number of Bootstrap Repetitions." *Econometrica* 68(1), 23–51.**
  Subsumes: choosing the bootstrap simulation size B to control the *simulation*
  error of a bootstrap quantity to a target relative accuracy — the "how many
  resamples is enough" question in regime B, though targeting an estimate's
  precision rather than a decision.

**Honest residual after these.** Applying bounded-resampling-risk sequential
stopping to **equivalence-band model comparison** (two-sided, practical-
equivalence δ) and empirically characterizing the **savings vs. uniform
false-stop trade-off** across a difficulty-stratified battery. This is an
*application + empirical* contribution and engineering, **not** a new inference
method or a new stopping guarantee. If even this residual collapses under a
closer reading of Gandy's two-sided extensions, we narrow again — that is a
finding, not a failure.

## Sequential analysis (regime A — deliberately not our setting)

- **Wald, A. (1945/1947). Sequential Probability Ratio Test.** The origin of
  optional-stopping error control; subsumes the *sample-size* version of the
  problem we are avoiding.
- **Group-sequential designs & alpha-spending (Pocock 1977; O'Brien & Fleming
  1979; Lan & DeMets 1983).** Subsumes controlled interim analyses of accumulating
  *data*. Relevant only as the thing regime B is *not*.

## Always-valid / anytime-valid inference (the instrument v0 borrows)

- **Robbins, H. (1970). "Statistical methods related to the law of the iterated
  logarithm."** Origin of confidence sequences.
- **Howard, S. R., Ramdas, A., McAuliffe, J. & Sekhon, J. (2021).
  "Time-uniform, nonparametric, nonasymptotic confidence sequences." *Annals of
  Statistics.*** Subsumes: bands that are safe to peek at every batch — the exact
  instrument v0 needs so that per-batch inspection is valid.
- **Waudby-Smith, R. & Ramdas, A. (2024). "Estimating means of bounded random
  variables by betting." *JRSS-B.*** Subsumes: tight empirical-Bernstein
  confidence sequences for **bounded** variables — directly applicable to a
  bounded, paired metric difference. A leading candidate instrument.
- **Ramdas, A., Grünwald, P., Vovk, V. & Shafer, G. (2023). "Game-theoretic
  statistics and safe anytime-valid inference." *Statistical Science.*** Subsumes:
  the e-process / test-martingale framework underpinning the above.

## Monte-Carlo error & bootstrap simulation size

- **Efron, B. & Tibshirani, R. (1993). *An Introduction to the Bootstrap.***
  Foundational; MCSE of bootstrap estimates and the 1/√B convergence we exploit.
- **Koehler, E., Brown, E. & Haneuse, S. (2009). "On the Assessment of Monte
  Carlo Error." *The American Statistician* 63(2).** Subsumes: how to estimate and
  report MCSE — the quantity our band is built on, and the batch-estimate that
  heavy tails break.

## Adaptive / multi-fidelity sampling

- **Successive halving & Hyperband (Jamieson & Talwalkar 2016; Li et al. 2017,
  *JMLR*).** Subsumes: allocating a *budget* adaptively across candidates by early
  elimination. Shares the "spend compute where it matters" spirit but targets
  hyperparameter search across arms, not a single fixed-data decision.

## Approximate explainability (track 2 — not v0)

- **Lundberg, S. & Lee, S.-I. (2017). "A Unified Approach to Interpreting Model
  Predictions." *NeurIPS.*** SHAP / KernelSHAP; sampling-based Shapley estimation.
- **Štrumbelj, E. & Kononenko, I. (2014). "Explaining prediction models and
  individual predictions with feature contributions." *KAIS.*** Sampling
  estimator of Shapley values — a Monte-Carlo estimator with its own MCSE, hence a
  natural regime-B target for H2.
- **Covert, I. & Lee, S.-I. (2021). "Improving KernelSHAP: Practical Shapley
  Value Estimation Using Linear Regression." *AISTATS.*** Subsumes: **convergence
  detection and uncertainty for KernelSHAP** — i.e. someone has already built
  stopping/uncertainty for SHAP. Track 2 must build *on* this, not around it, and
  H2's "same controller" claim will be tested against it.
- **Attribution stability / uncertainty** *(verify specific cites)* — e.g. work on
  the instability of feature attributions and on confidence intervals for Shapley
  values. Establishes that "explanation converged" ≠ "matches reference", the
  premature-convergence trap H2 must detect.

## Dynamic / adaptive inference (routing — deferred, separate methodology)

- **Graves, A. (2016). "Adaptive Computation Time for Recurrent Neural
  Networks."** Per-input compute allocation inside a model.
- **Teerapittayanon, S. et al. (2016). "BranchyNet: Fast Inference via Early
  Exiting."** and **Schwartz, R. et al. (2020). "The Right Tool for the Job."**
  Subsumes: cheap-model-then-expensive-model cascades / early exit on *live
  inputs*. Shares the "allocate compute by uncertainty" intuition but operates on
  streaming data with genuine sequential/label-availability issues — regime A, not
  our fixed-data MC-budget primitive. This is why routing is deferred and likely a
  separate repository (see [`../PLAN.md`](../PLAN.md)).
- **Han, Y. et al. (2021). "Dynamic Neural Networks: A Survey." *IEEE TPAMI.***
  Map of the routing/early-exit landscape for when track 3 is revisited.

---

## Bottom line

The stopping *guarantee* is not ours to invent — Gandy (2009) and the
confidence-sequence literature already provide it. Our contribution, if it
survives experiment, is narrow and empirical: **how much Monte-Carlo compute a
bounded-resampling-risk rule actually saves on equivalence-band model comparison,
and whether it does so without silently failing on hard cases.** Everything in
[`research-definition.md`](research-definition.md) is scoped to defend exactly
that claim and no more.
