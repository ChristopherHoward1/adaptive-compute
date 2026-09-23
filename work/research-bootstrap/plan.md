# Research bootstrap: definition, prior-art, first falsifiable experiment

**Slug:** research-bootstrap · **Date:** 2026-09-19 · **Status:** merged (plain PR, no release)

## Goal

Produce a minimal, healthy research repo plus an adversarially-reviewed research
specification, so that after this unit we know **exactly** what the first
falsifiable experiment is, what would invalidate it, what prior work it overlaps
with, and what we are deliberately not building. Success is the *specification*,
not the existence of the repo. **No adaptive algorithm, no bootstrap code, no
SHAP, no routing is implemented in this unit.** The deliverable is documents +
scaffold + the pinned-down next work unit.

This unit is document-authored, not code-authored (see Approach → "Who writes
this"). The plan below states the substantive scientific decisions as explicit
claims precisely so the plan-reviewer can attack them *before* they are written
up.

## Approach

### Core reframing (the load-bearing decision)

The Owner's framing spans "adaptive validation" and "adaptive explanation" as if
both are the same problem. They are not equally clean. The sharpest, most
defensible v0 lives on one side of a distinction the original brief blurs:

- **Adaptive *sample* size** (grow the number of *data points* until a decision
  about the population is stable) is genuine sequential analysis. Repeated
  peeking at an accumulating estimate of an *unknown population quantity* inflates
  Type-I error and biases downstream CIs. This is a real statistical hazard and a
  century-old field (SPRT, group-sequential, alpha-spending, always-valid
  e-processes). We should **not** claim novelty here and **not** start here.

- **Adaptive *Monte-Carlo* budget** (fix the dataset; grow the number of
  *simulation draws* — bootstrap resamples B, permutation draws, SHAP samples —
  until a decision is stable) targets a **fixed estimand**: the value the
  procedure would return at infinite draws *on this fixed data*. The error being
  controlled is *simulation/Monte-Carlo* error, not sampling error. Fixing the
  estimand removes the "my CI for the *population* is invalid" hazard —
  sampling-error inference is unaffected. It does **NOT** remove optional-stopping
  bias at the level of the *decision*: the decision is a functional of the random
  MC path, and a rule that stops the first time a running band clears δ stops
  preferentially on MC excursions to one side, so the probability of disagreeing
  with the B→∞ decision is **not** controlled by a fixed per-look MCSE threshold.
  The sequential decision therefore still needs a *sequential* guarantee. This
  side does have a well-defined reference (large-draw estimate on the *same*
  data) and hardware-independent compute accounting (count draws, not seconds).

**Decision:** v0 is exclusively **adaptive Monte-Carlo budget**, framed around a
*decision* about a fixed dataset. This is the honest, clean core. It also means
validation and explanation genuinely share one primitive ("adaptively choose the
number of MC draws to resolve a decision about a fixed estimand, given a running
MC standard error"), which is the real (deferred) justification for one repo.

### The concrete v0 experiment (first *implementation* unit, proposed — not built here)

- **Task:** a model-comparison *decision* on a fixed dataset — "is model A better
  than model B by more than a practical-equivalence margin δ on metric M?" —
  resolved via bootstrap over a fixed evaluation set. M = a paired resampled
  metric difference (e.g. ΔAUC or Δlog-loss).
- **Reference (not ground truth):** the decision the *same* bootstrap procedure
  reaches at a very large fixed budget B_ref. Explicitly labelled "what the
  full-budget same method would conclude," **never** "the true answer." The
  bootstrap can be wrong about the sampling distribution; we claim only
  decision-agreement with the full-budget same method. **Reference-noise
  discipline (required):** B_ref is itself finite and noisy, and near the δ
  boundary its own decision is a coin flip — so (a) B_ref is seeded
  *independently* from the adaptive run; (b) B_ref is large enough that its MCSE
  at the boundary is a small, stated fraction of δ; (c) cases whose B→∞ estimand
  sits *at* the boundary (no finite procedure can agree reliably) are excluded or
  scored separately, never counted as adaptive failures.
- **Adaptive procedure:** grow B in batches; maintain the running estimate and
  its Monte-Carlo standard error; stop when the decision (sign vs. the δ band) is
  resolved with MCSE small enough that further draws are unlikely to flip it, or
  a max budget is hit.
- **Stopping target for v0 (one, not six):** *decision resolution under an
  anytime-valid guarantee* — grow B in batches and maintain an **anytime-valid
  band** (a confidence sequence on the running MC average, or a bounded-
  resampling-risk construction à la Gandy 2009) that is safe to peek at every
  batch; stop when that band lies wholly inside or wholly outside the δ
  equivalence band, or at max budget. A naive fixed-level band peeked repeatedly
  is explicitly rejected (see validity note above). The **false-stop rate vs.
  B→∞** is a *pre-registered controlled quantity with a target* (e.g. ≤ α), not
  merely a reported metric. Ranking stability, CI-endpoint precision, and
  "probability of changing a decision" are named as alternatives and deferred
  with one line each on why.
- **Decision at max budget** is defined a priori (abstain vs. forced call);
  without this, false-stop rate itself is undefined. v0 default: *abstain*
  (report "undecided at budget"), scored separately from a wrong call.
- **Blindness invariant:** the adaptive procedure receives only data + δ + max
  budget + seed. It is blind to B_ref, to the reference decision, and to the true
  effect size. Any adaptive hyperparameters are fixed a priori or tuned on a
  declared tune/test split, never on the evaluation cases (prevents effect-size
  leakage).

### Deliverables (the actual files)

1. `docs/research-definition.md` — question; motivation; hypotheses in
   falsifiable form; the sample-size-vs-MC-budget distinction above; non-goals;
   terminology; experimental strategy; reference-vs-adaptive; validity threats;
   expected failure modes; **criteria under which the hypothesis is judged
   unsupported**; open questions. A hard visual separation between *what we
   believe* and *what experiments have established* (at creation: nothing
   established).
2. `docs/prior-art.md` — adjacent-work map. **Required named ancestors** (v0 is
   an application of these, not a new method): **Gandy (2009), "Sequential
   implementation of Monte Carlo tests with uniformly bounded resampling risk"**;
   **Besag & Clifford (1991)** sequential Monte-Carlo tests; **Andrews &
   Buchinsky** adaptive choice of the number of bootstrap replications B. Plus
   the broader map: sequential analysis (SPRT, group-sequential/alpha-spending),
   always-valid inference / e-processes / confidence sequences (Howard et al.),
   MCSE & bootstrap simulation-size guidance, adaptive/multi-fidelity sampling,
   SHAP approximation (KernelSHAP, sampling SHAP) & attribution stability /
   uncertainty, adaptive/dynamic inference (early-exit, cascades). Each entry:
   what it solves and precisely which part of our problem it subsumes. Primary
   sources; links recorded. **Honest residual, narrowed:** applying
   bounded-resampling-risk sequential stopping to *equivalence-band model
   comparison* and empirically characterizing the savings vs. false-stop
   trade-off — **not** a new inference method, and not a novel stopping guarantee.
   If the residual cannot survive naming these ancestors, the unit revises the
   research question now rather than in doc review.
3. `docs/experiment-design.md` — the smallest experiment that can *falsify*
   hypothesis 1: task, datasets (dataset-agnostic synthetic generators + at most
   one small real tabular set; insurance/PetFinder-agnostic), reference
   computation, adaptive computation, the single v0 stopping rule, metric set
   (with critique — see below), baselines, seeds/repetitions, failure criteria,
   statistical comparison, compute accounting (in MC draws).
   - **Baseline = a fixed-B *sweep*, judged by Pareto dominance** (not a single
     riggable "fixed small B"). The claim to establish: at the adaptive method's
     *realized* false-stop rate, no fixed B achieves both lower budget and ≤ that
     false-stop rate. Include a fixed-**large**-B baseline as the accuracy ceiling
     to show how much accuracy adaptivity concedes.
   - **Adversarial synthetic battery** targeting *premature apparent
     convergence*: near-δ-boundary effects, small effects, heavy-tailed metric
     distributions (≥ one member, since batch-MCSE under-estimation under heavy
     tails is the specific mechanism that makes a naive rule stop early),
     rare-event/imbalance. We justify *which* actually threaten the rule rather
     than listing all mechanically.
   - **Failure-mode detection is operationalized, not asserted:** false-stop rate
     is reported **stratified** by difficulty (distance of the B→∞ estimand from
     the δ boundary) and by realized stopping budget, held to a **uniform** (not
     just average) tolerance — because average savings are dominated by easy
     cases and can hide silent failure on hard ones. Heavy-tailed members carry a
     pre-registered false-stop tolerance.
4. `ARCHI.md → Verification` — the ML declarations now answerable are set
   **PROVISIONAL** (pointer to this work unit), *not* declared resolved, because
   no experiment exists yet and they will churn when the reference unit meets
   reality (EVAL_METRIC especially): **EVAL_METRIC** ≈ decision-agreement with the
   full-budget reference + MC-draws consumed (p50/p90/p99) + stratified false-stop
   rate; **GROUND_TRUTH_SOURCE** ≈ the full-budget *same-procedure* decision, with
   its stated limit (not truth); **DATA_REGIME** ≈ offline, fixed evaluation set,
   dataset-agnostic. **EVAL_COMMAND** stays PENDING — wired into the gate by the
   reference-experiment unit.
5. `PLAN.md` — record decisions; set Next to the proposed first implementation
   unit; **record the one-repo / defer-abstraction / routing-separate
   architecture call as a two-line Decision** (see below) rather than a standalone
   document.

### Architecture call (a PLAN.md Decision line, not a document)

**One repo** for adaptive validation + adaptive explainability: they share a real
implementation primitive — a bootstrap-B controller and a SHAP-sample controller
are the same "grow MC draws under an anytime-valid band until a decision
resolves" loop — but **the shared abstraction stays un-scaffolded** until the
second (explainability) consumer actually exists. **Dynamic inference routing is
deferred and likely a separate repo:** it adapts per-input on *real streaming
data* with genuine sequential/optional-stopping and label-availability issues — a
different methodology, not the MC-budget primitive. This is reversible and cheap
to record as a decision line; committing it in a full document before any code is
premature structure. The evidence that would revisit it (v0/v1 showing the
controller genuinely reused) is noted in `docs/research-definition.md`.

### Metric-set critique

Wall-clock is *secondary/engineering only* — primary compute is MC draws,
hardware-independent by construction. "Result error vs reference" is retained but
subordinated to *decision agreement*. **Stratified false-stop rate** (finding 5)
and **max-budget-hit frequency** are first-class. Nothing is dropped silently;
anything dropped is listed with a reason.

### Proposed next work unit (stated here, finalized in the docs)

**Build the fixed-budget reference bootstrap decision procedure** — deterministic,
seeded, MC-draw-accounted, over a synthetic generator + one small real set. **No
adaptivity.** This is the reference the first adaptive algorithm is later judged
against. Small enough to implement and review rigorously.

### Who writes this (a decision for the Owner, surfaced not buried)

The deliverable is a *research specification* requiring domain reasoning and
prior-art knowledge, not code. Dispatching the Codex implementer to author it
risks fabricated citations and shallow methodology. Recommendation: the
**Orchestrator authors** the documents on a branch; the fresh **plan-reviewer
grills the science now** (on the claims in this plan, with an expanded mandate —
see the spawn), and a fresh **/3-review reads the finished docs** as the diff.
"Writer never reviews" is preserved (reviewer ≠ author). The Codex worktree
implement step is skipped because there is no code to write. If the Owner prefers
strict loop mechanics, we route the mechanical scaffold through /2-implement and
keep authoring with the Orchestrator; flagged for arbitration.

## Footprint

Files to create (three docs, not four — architecture is a PLAN.md decision):
- `docs/research-definition.md`
- `docs/prior-art.md`
- `docs/experiment-design.md`

Files to modify:
- `ARCHI.md` (Verification → mark EVAL_METRIC / GROUND_TRUTH_SOURCE / DATA_REGIME PROVISIONAL with a pointer to this unit; leave EVAL_COMMAND PENDING)
- `PLAN.md` (Now + Decisions incl. the architecture call + Next)

Files NOT to touch:
- `src/`, `tests/` — no research code in this unit. Creating `experiments/`,
  `configs/`, or any placeholder module now is premature abstraction and is out
  of scope; the reference-experiment unit creates them when it needs them.
- `config.yaml`, `scripts/`, `profiles/` — harness machinery, unchanged.

## Acceptance criteria

- [ ] `docs/research-definition.md` exists and contains all of: research
      question, falsifiable hypothesis statement, non-goals, terminology,
      unsupported-criteria, open questions, and a visibly separated
      "believed vs. established (established: none)" section.
- [ ] `docs/research-definition.md` states the sample-size-vs-Monte-Carlo-budget
      distinction, notes that optional-stopping bias still applies at the
      *decision* level, and commits v0 to the MC-budget side with one
      anytime-valid stopping rule and a defined max-budget decision + blindness
      invariant.
- [ ] `docs/prior-art.md` names Gandy (2009), Besag & Clifford (1991), and
      Andrews & Buchinsky explicitly with a one-line "what it subsumes" each, and
      covers sequential analysis, always-valid/e-process inference,
      MCSE/bootstrap simulation size, adaptive/multi-fidelity sampling, SHAP
      approximation, attribution stability, and adaptive inference; and states
      the narrowed honest residual contribution.
- [ ] `docs/experiment-design.md` specifies task, reference (with the B_ref
      independent-seed + boundary-noise discipline), adaptive procedure, the
      single anytime-valid v0 stopping rule, metrics (wall-clock demoted,
      *stratified* false-stop-rate promoted), a **fixed-B sweep** baseline judged
      by Pareto dominance plus a large-B accuracy ceiling, seeds, failure
      criteria, and an adversarial battery (incl. ≥ one heavy-tailed member) aimed
      at premature convergence.
- [ ] `ARCHI.md` EVAL_METRIC, GROUND_TRUTH_SOURCE, DATA_REGIME are marked
      PROVISIONAL (pointer to this unit); EVAL_COMMAND remains PENDING with a note
      that the reference unit wires it in.
- [ ] `PLAN.md → Now → Next` names the fixed-budget reference bootstrap unit as
      the next `/1-plan`, and a Decision line records the one-repo /
      defer-abstraction / routing-separate architecture call.
- [ ] `bash scripts/gate.sh` exits 0.

## Release

Release note: Define the Adaptive Compute research program — falsifiable v0
hypothesis (adaptive Monte-Carlo budget for a decision), prior-art map, first
experiment design, and architecture decision; no algorithm implemented yet.

## Verification

- `bash scripts/gate.sh`
- Manual: Owner reads the four docs and confirms the first experiment is one they
  would run and could see fail.

## Review

Fresh cold-context Opus plan-reviewer (fresh subagent, read-only; writer ≠
reviewer preserved). Verified all codebase claims accurate (`docs/` absent, four
ML declarations PENDING as described). Verdict: **REVISE**, 8 findings. All
accepted and incorporated — no disagreements to arbitrate:

1. **Optional-stopping bias transfers at the decision level.** Retracted the
   "does not transfer directly" over-claim; v0 now mandates an anytime-valid
   band (confidence sequence / bounded-resampling-risk), and false-stop rate is a
   pre-registered controlled quantity with a target. *(Approach → validity note,
   v0 stopping target.)*
2. **Named ancestors were missing.** Added Gandy (2009), Besag–Clifford (1991),
   Andrews–Buchinsky as required entries; residual narrowed to "apply
   bounded-resampling-risk stopping to equivalence-band model comparison." *(Del.
   2.)*
3. **"Fixed small B" strawman.** Baseline is now a fixed-B *sweep* judged by
   Pareto dominance, plus a large-B accuracy ceiling. *(Del. 3.)*
4. **Reference noise at the δ boundary.** Added B_ref independent-seeding, MCSE ≪
   δ requirement, and separate handling of at-boundary estimands. *(v0 reference,
   Del. 3.)*
5. **Failure-mode detection operationalized.** Stratified false-stop rate by
   difficulty and budget with a uniform tolerance; heavy-tailed member with
   pre-registered tolerance. *(Del. 3, metric critique.)*
6. **Four docs → three.** `architecture-decision.md` collapsed to a PLAN.md
   Decision line + a pointer in research-definition. *(Footprint, Del. 5.)*
7. **ARCHI churn.** EVAL_METRIC / GROUND_TRUTH_SOURCE / DATA_REGIME marked
   PROVISIONAL, not resolved. *(Del. 4.)*
8. **Minor:** blindness invariant (adaptive blind to B_ref/reference/effect;
   hyperparameters fixed a priori or via tune/test split) and a defined
   max-budget decision (abstain) added. δ-as-user-input kept as-is (legitimate).

Reviewer affirmed as sound and not to relitigate: the sample-vs-MC-budget
distinction (its best idea), defer-the-abstraction, draws-not-wall-clock, and
routing-as-different-methodology.

Plan verdict: **REVISE → addressed; re-verify at APPROVE.** One open item is for
the Owner, not the reviewer: *who authors* (Orchestrator vs. Codex worktree) —
see Approach → "Who writes this."
