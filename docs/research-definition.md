# Adaptive Compute — Research Definition

**Status:** v0 specification, 2026-09-19. Nothing in this document has been
experimentally established. See [§9 Believed vs. Established](#9-believed-vs-established).

This document defines *what we are investigating and how we would know we are
wrong*. The concrete first experiment lives in
[`experiment-design.md`](experiment-design.md); the prior art we are building on
lives in [`prior-art.md`](prior-art.md).

---

## 1. Research question

> For an iterative Monte-Carlo evaluation procedure run on a **fixed dataset**,
> can we allocate simulation draws adaptively — stopping when the *decision* the
> procedure supports is resolved — so as to spend materially fewer draws than a
> large fixed budget, while keeping the probability of reaching a *different
> decision than the full-budget procedure* below a pre-set bound?

The unit of computation is the **Monte-Carlo draw** (a bootstrap resample, a
permutation, later a sampled attribution coalition), not wall-clock seconds. This
makes "compute saved" hardware-independent by construction.

## 2. Motivation

Many ML evaluation and explanation procedures are Monte-Carlo estimators run at a
fixed, conventional budget (e.g. "1000 bootstrap resamples", "N permutations",
"M SHAP samples") chosen by habit rather than by the precision the *decision*
needs. When the answer is lopsided, most of that budget is wasted; when it is
genuinely close, the fixed budget may be too small to resolve it. Allocating
draws to the difficulty of the decision is the obvious move. The question is
whether it can be done with a *stated, controlled* probability of changing the
conclusion — otherwise it is just "fewer iterations often looks similar", which
is not a result.

## 3. The distinction the project rests on

There are two very different things one might call "adaptive compute". We commit
to exactly one for v0.

**(A) Adaptive *sample* size** — grow the number of *data points* until a
decision about the *population* is stable. This is genuine sequential analysis.
The estimand is unknown and the data are random draws from it, so repeatedly
peeking at an accumulating estimate and stopping on a threshold inflates Type-I
error and biases downstream confidence intervals. This is a mature field (SPRT,
group-sequential designs, alpha-spending, always-valid e-processes; see
[`prior-art.md`](prior-art.md)). **We do not start here and we claim no novelty
here.**

**(B) Adaptive *Monte-Carlo* budget** — fix the dataset; grow the number of
*simulation draws* until a decision is stable. The estimand is now **fixed**: the
value the procedure returns in the limit of infinite draws *on this exact data*
(call it the B→∞ value). The error being controlled is *simulation* error, not
sampling error.

Fixing the estimand removes one hazard entirely: our confidence interval *for the
population* is exactly as (in)valid as the underlying statistical method — the
adaptivity does not touch it, because we never add data. **But it does not remove
optional-stopping bias at the level of the decision.** The decision is a
functional of the random Monte-Carlo path; a rule that stops the first time a
running band clears a threshold stops *preferentially* on paths that have
wandered across it, so the probability of disagreeing with the B→∞ decision is
**not** controlled by a fixed per-look precision threshold. The sequential
decision therefore still needs a *sequential* guarantee (an anytime-valid band or
a bounded-resampling-risk construction — see [§6](#6-stopping-rule-v0)).

v0 lives entirely in regime (B). This is the whole reason the project can make a
*controlled* claim rather than an anecdotal one.

## 4. Hypotheses (falsifiable)

**H1 (primary).** There exists an adaptive Monte-Carlo stopping procedure for
equivalence-band model comparison on fixed data such that, across a
pre-registered battery of cases, it (i) reaches the same decision as a
large-fixed-budget reference with probability ≥ 1 − α *uniformly* across
difficulty strata, and (ii) consumes, in expectation, materially fewer draws
(target: ≥ 2× median reduction) than the fixed budget needed to match that
uniform decision-agreement.

*How H1 is falsified.* H1 is **unsupported** if any of the following hold on
held-out cases the stopping rule was not tuned on:
- the realized false-stop rate exceeds α in *any* difficulty stratum (average
  agreement hiding hard-case failure counts as falsification, not success);
- no median-draw reduction ≥ the target survives at a false-stop rate ≤ α; i.e.
  the adaptive method does not Pareto-dominate the fixed-B sweep
  ([`experiment-design.md`](experiment-design.md));
- the savings vanish once cases whose B→∞ estimand sits *at* the δ boundary are
  scored honestly (see [§7](#7-validity-threats)).

**H2 (secondary, not tested in v0).** The same stopping machinery transfers to a
sampling-based *explanation* decision (e.g. top-k feature-set stability) without a
new stopping guarantee. Stated here to fix scope; deferred until H1 is settled.

## 5. Non-goals (v0)

- Reproducing every numerical estimate to high precision — we target the
  **decision**, not four-decimal fidelity.
- Adaptive *sample* size / sequential hypothesis testing on streaming data
  (regime A above).
- SHAP or any attribution method (explanation is track 2; see H2).
- Dynamic inference routing (deferred; see [`../PLAN.md`](../PLAN.md) Decisions).
- Any generic "adaptive compute framework", scheduler, registry, or plugin
  system. The shared abstraction is deferred until a second consumer exists.
- Wall-clock optimization. Wall-clock is a secondary engineering metric only.

## 6. Stopping rule (v0)

One rule, not a menu:

- Grow B in batches on fixed data; maintain the running estimate of the metric
  difference Δ (e.g. ΔAUC or Δlog-loss between candidate and reference model on a
  fixed evaluation set).
- Maintain an **anytime-valid** band around the running Monte-Carlo average —
  a confidence sequence, or a bounded-resampling-risk construction in the style
  of Gandy (2009) — that is *safe to inspect after every batch*.
- **Stop** when that band lies wholly inside, or wholly outside, the
  practical-equivalence band `[−δ, +δ]`; or at a maximum draw budget `B_max`.
- **Decision at `B_max`:** *abstain* ("undecided at budget"), scored separately
  from a wrong call. Without a defined max-budget decision, the false-stop rate
  is itself undefined.
- **Blindness invariant:** the procedure receives only `data, δ, B_max, seed`. It
  is blind to `B_ref`, to the reference decision, and to the true effect size.
  Any hyperparameters are fixed a priori or tuned on a declared tune/test split,
  never on the evaluation cases.

Alternatives considered and deferred (one line each):
- *CI-endpoint precision* — optimizes a number, not the decision; wrong target.
- *Ranking stability across >2 models* — a natural v1 generalization; adds
  multiplicity we don't want to debug in v0.
- *Explicit "probability of changing the decision"* — attractive but requires
  modeling the path; the anytime-valid band gives the guarantee more directly.

## 7. Validity threats

- **Optional stopping at the decision level** — addressed by the anytime-valid
  band ([§6](#6-stopping-rule-v0)); the naive fixed-level peeked band is
  explicitly rejected.
- **Reference is not ground truth** — a large-B bootstrap converges to the B→∞
  *bootstrap* distribution, which can still be wrong about the true sampling
  distribution. We therefore claim only *decision-agreement with the full-budget
  same method*, never correctness. Any statement of the form "adaptive matches
  truth" is out of bounds.
- **Reference noise at the boundary** — `B_ref` is finite; near δ its own
  decision is a coin flip. Mitigations (required in
  [`experiment-design.md`](experiment-design.md)): seed `B_ref` independently of
  the adaptive run; size `B_ref` so its MCSE at the boundary is a small stated
  fraction of δ; exclude or separately score cases whose B→∞ estimand sits *at*
  the boundary.
- **Preferential stopping on easy cases** — average savings are dominated by easy
  cases and can hide silent failure on hard ones. Addressed by reporting
  false-stop rate **stratified** by difficulty and by realized budget, under a
  *uniform* tolerance.
- **Heavy tails break batch-MCSE** — under heavy-tailed metric distributions the
  batch estimate of Monte-Carlo error under-states the true error, the exact
  mechanism that makes a naive rule stop early. The battery includes ≥ one
  heavy-tailed member with a pre-registered tolerance.
- **Benchmark gaming / information leakage** — the blindness invariant
  ([§6](#6-stopping-rule-v0)) and the tune/test split guard against handing the
  algorithm δ-relative effect sizes a real user would not have. δ *itself* is a
  legitimate user input (equivalence margins are set by users).
- **Tuning against the reference data** — hyperparameters are frozen before the
  evaluation battery; the battery is generated from held-out seeds.

## 8. Expected failure modes

- The anytime-valid band is *too* conservative, so `B_max` is hit often and
  savings evaporate — plausible and would falsify the "materially fewer draws"
  half of H1. This is the most likely honest negative result.
- Heavy-tailed / rare-event cases blow the uniform false-stop tolerance even when
  the average looks great.
- On easy, lopsided comparisons the savings are real but *uninteresting* (a fixed
  small B would also have worked) — the fixed-B sweep baseline is designed to
  expose exactly this.

## 9. Believed vs. established

**Established by experiment:** *nothing.* This is a specification written before
any code exists.

**Currently believed (to be tested):** the regime-B framing is sound; an
anytime-valid stopping rule can deliver a controlled false-stop rate; there is
enough easy-vs-hard spread in realistic comparisons for adaptivity to save draws.
All three are hypotheses, not findings.

## 10. Terminology

- **Draw** — one Monte-Carlo unit (a bootstrap resample; later a permutation or
  sampled coalition). The compute currency.
- **Estimand (B→∞ value)** — what the procedure returns in the infinite-draw
  limit on fixed data. The fixed target of regime B.
- **Reference / `B_ref`** — a large fixed-budget run of the *same* procedure; a
  finite, noisy stand-in for the B→∞ decision. **Not** ground truth.
- **Decision** — the equivalence-band verdict: candidate better / worse /
  practically-equivalent / (at `B_max`) abstain.
- **δ (delta)** — the practical-equivalence margin, a user input.
- **False stop** — the adaptive run halts with a *different* decision than the
  reference on a case where the reference decision is itself well-resolved.
- **MCSE** — Monte-Carlo standard error, the simulation error of a draw-based
  estimate.
- **Anytime-valid band** — an interval sequence whose coverage guarantee holds
  simultaneously at all sample sizes, hence safe to peek at every batch.

## 11. Open questions

- Which anytime-valid instrument gives the tightest bands at realistic B for
  bounded, paired metric differences — an empirical-Bernstein confidence
  sequence, or a Gandy-style bounded-resampling-risk rule? (Resolve empirically
  in the reference/adaptive units.)
- Is one small *real* tabular dataset worth the reproducibility cost, or do
  synthetic generators alone give a stronger falsification test? (Leaning
  synthetic-first; see [`experiment-design.md`](experiment-design.md).)
- What evidence from v0/v1 would justify pulling dynamic inference routing into
  this repository versus splitting it out? (Recorded as a deferred decision in
  [`../PLAN.md`](../PLAN.md).)
- Does the explanation track (H2) truly reuse the *same* controller, or only a
  similar-looking one? This is the test of whether one repository is correct.
