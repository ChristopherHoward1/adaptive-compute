# Adaptive Compute — v0 Experiment Design

**Status:** v0 proposal, 2026-09-19. No code exists. This design specifies the
smallest experiment that can **falsify** H1 in
[`research-definition.md`](research-definition.md).

The experiment compares an **adaptive** Monte-Carlo stopping procedure against a
**fixed-budget reference** and a **fixed-B sweep** baseline, on a decision:
*"is the candidate model better than the reference model by more than δ, worse by
more than δ, or practically equivalent, on metric M over a fixed evaluation
set?"*

**In plain terms.** We build synthetic cases where we *know* the right answer by
construction, then run three procedures on each: the adaptive stopper (the thing
under test), a big fixed-budget run (our stand-in for the "full-budget answer",
not truth), and a grid of plain fixed budgets (the honest competitor). The
adaptive method wins only if it (a) reaches the full-budget answer at least as
reliably as the fixed grid *in every difficulty band, not just on average*, and
(b) does so with materially fewer draws. Cases sitting right on the δ boundary
are scored separately — no finite procedure can call those reliably, so counting
them would just measure noise. Everything here is designed to *falsify* that
claim if it's false.

---

## 1. Task and estimand

- **Data:** a fixed evaluation set `E` of `(x, y)` pairs and two trained models
  A (candidate), B (reference). Both models and `E` are frozen for a run.
- **Metric difference:** `Δ = M(A, E) − M(B, E)`, with M a paired, bounded score
  (v0 default: AUC; secondary: log-loss). Bounded matters — it lets us use an
  empirical-Bernstein confidence sequence.
- **Randomness:** the bootstrap over `E` (resample rows of `E` with replacement,
  recompute Δ). **This is the only source of Monte-Carlo randomness** — the data
  and models are fixed, so the estimand is the B→∞ bootstrap value of the decision
  on `E`. We are *not* resampling training data or adding examples (that would be
  regime A).
- **Decision:** given margin δ, output one of `{A_better, B_better, equivalent,
  abstain}` where the first three are read off whether the resolved interval for
  `Δ` sits above `+δ`, below `−δ`, or within `[−δ, +δ]`; `abstain` is only
  possible at `B_max`.

## 2. Reference (not ground truth)

- The reference decision is that of the **same** bootstrap procedure at a large
  fixed budget `B_ref`.
- **`B_ref` seeded independently** of every adaptive run (no shared streams).
- **`B_ref` sized** so its own MCSE at the δ boundary is ≤ `ρ·δ` for a small
  stated `ρ` (target `ρ = 0.1`; verify empirically that `B_ref` achieves it).
- **At-boundary estimands:** cases whose B→∞ `Δ` lies within `ρ·δ` of `±δ` are
  placed in a separate **`boundary` stratum** (this `Δ` is *known by
  construction* for the synthetic generators of §6, and *estimated from `B_ref`*
  for the optional real dataset); no finite procedure can
  agree reliably there, so they are scored on their own and never counted as
  adaptive false stops. This prevents the headline metric from measuring
  reference noise instead of method quality.
- The reference is labelled everywhere as *"what the full-budget same method
  concludes"*, never *"the true answer"* (see validity threats,
  [`research-definition.md`](research-definition.md) §7).

## 3. Adaptive procedure (system under test)

- Inputs (blindness invariant): `E, A, B, δ, B_max, seed`. **Not** `B_ref`, the
  reference decision, or the true effect.
- Grow the bootstrap in batches of size `b`. After each batch maintain an
  **anytime-valid** interval for `Δ` (candidate instruments: empirical-Bernstein
  confidence sequence for bounded means; or a Gandy-style bounded-resampling-risk
  rule). Coverage parameter `α`.
  - *Note on `α`.* The band's miscoverage level and the decision-level
    **false-stop tolerance** (§5, §8) are written with the same symbol `α`
    deliberately: the anytime-valid guarantee is precisely what makes the
    band-miscoverage level bound the false-stop rate. They are conceptually
    distinct (one is about the interval, one about the decision vs. B→∞) and the
    experiment *measures* the realized false-stop rate rather than assuming it
    equals the nominal band level.
- **Stop** when the interval lies wholly above `+δ`, wholly below `−δ`, or wholly
  inside `[−δ, +δ]`; else continue; at `B_max` return `abstain`.
- Hyperparameters (`b`, `α`, instrument choice) are **fixed a priori** or tuned on
  a **disjoint tune split** of generator seeds, never on the evaluation battery.

## 4. Baselines

- **Fixed-B sweep** — the same bootstrap decision at each of a grid of fixed
  budgets `B ∈ {B₁ < … < B_k}`, *no* early stopping. This is the honest
  competitor. **Fairness = Pareto dominance:** for the adaptive method's realized
  (uniform) false-stop rate, the claim is that *no* fixed `B` in the sweep
  achieves both a lower median budget *and* a false-stop rate ≤ the adaptive
  method's. A single "small B" is not a baseline.
- **Fixed-large-B (accuracy ceiling)** — a large fixed budget short of `B_ref`,
  to show how much decision-accuracy adaptivity concedes relative to just
  spending a lot.

## 5. Metrics

Primary (decision-centric):
- **Decision agreement** with the reference, overall and **stratified** by
  difficulty and by realized budget.
- **False-stop rate** — fraction of *well-resolved* (non-`boundary`) cases where
  the adaptive decision differs from the reference. Held to a **uniform**
  tolerance `≤ α` across strata, not merely on average.
- **Draws consumed** — p50 / p90 / p99, in bootstrap resamples. The compute
  currency.
- **Max-budget-hit (abstain) frequency.**

Secondary (engineering only):
- **Wall-clock** — reported, never used to define success; hardware-dependent.

Explicitly demoted: "result error vs reference" (|Δ_adaptive − Δ_ref|) is
recorded for diagnostics but is *subordinate* to decision agreement — the project
targets decisions, not precise magnitudes.

## 6. Adversarial synthetic battery (targets premature convergence)

Dataset-agnostic generators (insurance/PetFinder-agnostic); each parameterizes a
distribution of `(scores_A, scores_B, y)` on `E` so the B→∞ `Δ` is *known by
construction*, letting us place each case in a difficulty stratum:

- **Near-δ-boundary** — true `Δ` set just outside `±δ`. The headline
  premature-convergence trap: the running band can transiently clear δ.
- **Small effect** — true `Δ` near 0, well inside `[−δ, +δ]`; tests early, correct
  `equivalent` calls without over-spending.
- **Heavy-tailed metric** (≥ 1 member, **required**) — heavy-tailed per-row score
  contributions so the batch MCSE *under*-estimates true error; the specific
  mechanism that makes a naive rule stop early. Pre-registered false-stop
  tolerance.
- **Rare-event / class imbalance** — few positives, so AUC's variance is dominated
  by a handful of rows; MCSE looks small transiently.
- **Easy / lopsided** (control) — large true `Δ`; adaptive *should* win big here,
  and the fixed-B sweep should also do fine, exposing "savings that don't matter".

We justify inclusion by *mechanism* (each targets a distinct way the rule can
fail), not by mechanically enumerating distributions. Multimodality and extreme
high-variance members are **excluded from v0** unless a member above fails to
exercise the relevant mechanism — added only if they buy a distinct failure mode.

Optionally, **at most one small real tabular dataset** (e.g. a standard binary
UCI-style set) as a reality check. Leaning synthetic-first because known-by-
construction estimands make falsification sharper; the real set is a stretch goal,
not a requirement.

## 7. Seeds, repetitions, statistical comparison

- Each battery member instantiated over **many independent seeds** (target ≥ 500
  per member; final count set so the false-stop-rate estimate has a stated
  precision, e.g. half-width ≤ 0.01 at the tolerance). Tune/test seed splits are
  disjoint.
- **False-stop rate** reported per stratum with a binomial CI; the H1 test is
  whether the *upper* CI bound is ≤ α in **every** stratum.
- **Savings** reported as the median-draw ratio adaptive-vs-the-cheapest-fixed-B
  that matches the adaptive false-stop rate (the Pareto comparison of §4).

## 8. Failure criteria (restated operationally)

H1 is **unsupported** if, on held-out seeds:
- any non-`boundary` stratum's false-stop upper CI exceeds α; **or**
- no fixed-B in the sweep is Pareto-dominated at the target median-draw
  reduction (≥ 2×); **or**
- savings depend on mis-scoring `boundary` cases.

Any of these is a publishable negative result, not a bug to paper over.

## 9. Compute accounting

- Compute is **counted in bootstrap resamples (draws)**, logged per run: total,
  and per-decision-outcome.
- Determinism: every run is reproducible from `(generator params, seed)`; the
  harness records them. This is what makes the eventual `EVAL_COMMAND` cheap and
  gate-able.

## 10. What this design deliberately omits

No adaptive algorithm is *built* by this document — it specifies the yardstick.
The **first implementation unit** is the fixed-budget reference procedure and the
generators/harness of §1–2 and §6–9, with **no adaptivity**. The adaptive
procedure of §3 is the unit after that. See [`../PLAN.md`](../PLAN.md) → Now.
