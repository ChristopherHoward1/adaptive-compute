# Adaptive Monte-Carlo stopping procedure + first-result eval harness

**Slug:** adaptive-procedure · **Date:** 2026-09-20 · **Status:** reviewed

## Goal

Build the **system under test** of the v0 experiment (`docs/experiment-design.md`
§3–§8): an **adaptive** bootstrap-budget procedure that grows Monte-Carlo draws in
batches under an **anytime-valid** band and stops as soon as the decision
`{A_better, B_better, equivalent}` is resolved (or `abstain`s at `B_max`), consuming
its seed on the reserved **adaptive** branch. Then build the **eval harness** that
judges it against the already-released fixed-budget reference across the §6 battery
and the **fixed-B sweep** baseline (§4), producing the project's **first real
result**: per-stratum false-stop rate (with binomial CI), draws p50/p90/p99,
abstain rate, and the Pareto/savings comparison of §7–§8.

Done looks like: `adaptive.py` turns a blind `(scores_A, scores_B, y, δ, α, b,
B_max, seed)` into a decision + exact draws consumed, reproducibly on the adaptive
seed branch; an offline `eval --run` sweeps the battery × many seeds and writes a
results artifact scoring H1 against §8's failure criteria; the fast `eval --check`
gate hook stays sub-second and green; and deferrals **D1** (degenerate resample)
and **D2** (hard-member diagnostic via the raising reference) are resolved where
this unit owns them.

**Explicitly NOT in this unit:** the shared validation/explainability abstraction
(PLAN decision 2026-09-19 keeps it un-scaffolded until the explainability consumer
exists); the optional real tabular dataset (§6 stretch goal); dynamic inference
routing (deferred, likely separate repo). The optional log-loss secondary metric
stays stubbed. No change to `reference.py`'s decision functional (see Approach —
we *target* it, we do not alter it).

## Approach

### The load-bearing decision: the anytime-valid instrument (Owner sign-off)

The band must both (i) keep the §6 heavy-tail member genuinely adversarial and §8
falsifiable, and (ii) agree with the released reference at `B→∞` on every scored
case, so a false stop measures *premature convergence*, not instrument mismatch.

**Chosen instrument: an empirical-Bernstein / betting confidence sequence for the
bounded mean `E*[Δ*]`** — §3's literal instrument ("confidence sequence for bounded
means"). `Δ* = M(A,·)−M(B,·) ∈ [−1,1]` is bounded, so EB applies directly, and it
adapts to *empirical variance* — exactly the quantity the heavy-tailed member
(`tail_df=1.4`) inflates. As batches arrive, maintain the anytime-valid interval
`[L_t, U_t]` for the mean; **stop** when it lies wholly above `+δ` (`A_better`),
wholly below `−δ` (`B_better`), or wholly inside `[−δ,+δ]` (`equivalent`);
`abstain` at `B_max`. Its `B→∞` target is `decision_from_delta(E*[Δ*], δ)`.

**Why this agrees with the reference despite a different-looking functional.** The
reference reads its verdict off a percentile interval, *but* the battery is
constructed so `fixed_budget_reference(...).decision == decision_from_delta(
plugin_delta, δ)` for every non-`boundary` member — the released `eval --check`
asserts exactly this recovery invariant. Since `E*[Δ*] → plugin_delta`, the mean-CS
`B→∞` verdict **coincides with the reference verdict on all scored cases**. The two
functionals can only diverge inside `[−δ,+δ]` neighbourhoods of `±δ` — the
`boundary` stratum, which §2/§8 exclude from false-stop scoring. So there is no
mismatch on scored cases, and heavy tails stay adversarial. *(This is the correction
to an earlier draft that targeted a tail-probability CS on `p_hi=P(Δ*>δ)`,
`p_lo=P(Δ*<−δ)`: that reduction is algebraically exact for the reference's three
resolved verdicts **in the B→∞ functional** — the fourth, straddle branch of
`_decision_from_interval` maps to reference-unresolved, not a verdict — but its
0/1 indicators are bounded regardless of Δ's tail, which **neuters** the heavy-tail
trap and risks a trivially-passing §8. Documented as the rejected alternative in
`knowledge/anytime-valid-band.md`.)*

**Owner sign-off:** this defines what "false stop" measures and keeps §6/§8
falsifiable, so the Orchestrator does not commit it silently — the plan recommends
the mean CS and the Owner confirms before `/2-implement`.

### What gets built (shape)

- **`src/adaptive_compute/adaptive.py`** — the controller. Inputs are **blind**
  (`E, A, B, δ, α, b, B_max, seed`; never `B_ref`, the reference decision, or the
  true effect — enforced by signature). Grows draws in batches of `b` on the
  **adaptive** seed branch and maintains the mean-CS interval, returning
  `AdaptiveResult{decision ∈ {A_better,B_better,equivalent,abstain}, draws_consumed,
  n_batches, final_bounds}`.
- **Adaptive resampler — one committed design (finding 3).** Extract the inner
  resample kernel of `paired_bootstrap_deltas` (given an `rng`, `n`, and a count →
  Δ* array) into a shared private helper, so the **reference path stays
  byte-identical** (regression-guarded). Add a new
  `adaptive_bootstrap_stream(...)` in `bootstrap.py` that routes its seed through
  **`adaptive_seed`** (branch [1], per `knowledge/bootstrap-seed-and-determinism.md`
  — this is the contract's first branch-[1] consumer) into a **single**
  `default_rng`, and yields successive batches of `b` Δ* draws pulled sequentially
  from that one generator. One generator (not per-batch sub-seeds) makes draw
  accounting exact and replay bit-identical on **both** seed paths (int and reused
  `SeedSequence`, since `adaptive_seed`→`seed_branches` clones before spawning).
  Reference (branch [0]) and adaptive (branch [1]) streams are independent by
  construction, satisfying acceptance criterion 2 without the muddy
  `[1]→[0]` double-branch the per-batch-subseed route would create.
- **`src/adaptive_compute/sweep.py`** — the §4 baselines: the fixed-B *sweep* (the
  reference percentile decision at a grid `B ∈ {B₁<…<B_k}`, no early stopping) and
  the **Pareto** test (§4/§8: is any fixed-B dominated — lower median draws *and*
  false-stop ≤ adaptive's — at the ≥2× target?).
- **`src/adaptive_compute/benchmark.py`** — the offline harness: run adaptive +
  sweep over the battery × N seeds, score decision-agreement vs
  `fixed_budget_reference(...).decision`, per-stratum false-stop rate with a
  **binomial CI** (H1 test = upper CI ≤ α in *every* non-`boundary` stratum, §7–§8),
  draws p50/p90/p99, abstain frequency, and the Pareto/savings summary. Writes
  `work/adaptive-procedure/results.md` (+ a JSON companion) — the **first real
  result**. Not run by the gate. Two mechanisms named to avoid mid-run surprises
  (finding 4):
  - **Seed sweep + disjoint splits.** Per member, instantiate N seeds via
    `dataclasses.replace(params, seed=base+i)` (`generators.py` untouched). Splits
    are disjoint ranges: **tune** `i ∈ [0, N_tune)`, **test** `i ∈ [10_000,
    10_000+N_test)`; hyperparameters (`b, α`) frozen on tune, all headline numbers
    from test. `N_test` set so the false-stop-rate CI half-width ≤ 0.01 at the
    tolerance (§7, target ≥ 500).
  - **Reference straddle policy.** `fixed_budget_reference` *raises*
    `UnresolvedReferenceError` on a straddle; over N seeds a non-`boundary` case can
    straddle at `b_ref=320`. Such a `(member, seed)` has no reference verdict, so it
    is **excluded from false-stop scoring and counted/reported** as
    `reference_unresolved` (never a traceback, never silently scored). Expected rare
    on non-boundary members; if it is not, that itself is reported.
- **`src/adaptive_compute/eval.py`** — extend the CLI: `--run` invokes the
  benchmark (offline); `--check` stays the fast seeded smoke and gains adaptive
  coverage (below). **D2 fix:** the hard-member MCSE diagnostic recomputes its
  per-replication estimate via `paired_bootstrap_deltas(...) + np.mean(...)`
  directly, never through the raising `fixed_budget_reference` (per `deferrals.md`).
- **Degenerate-resample policy (D1).** A bootstrap resample can draw all-positive or
  all-negative rows, which `metrics.auc` rejects. Over a full `--run` (many seeds ×
  draws) this becomes reachable. Define the policy in `bootstrap.py`/`adaptive.py`
  and test it. **Recommended:** treat a degenerate resample as the no-information
  value **AUC = 0.5 for each model ⇒ Δ* = 0**, counted as a normal draw (keeps draw
  accounting exact and is the natural centre); reviewer may prefer a guarded
  reject-and-redraw (must then define its accounting). Choice recorded in the unit.

### `eval --check` additions (fast gate hook, keep < a few seconds)

- Adaptive **determinism** on **both** seed paths (int and reused `SeedSequence`),
  per the seed contract's two-path rule.
- Adaptive **draw accounting** exact and ≤ `B_max`.
- Adaptive **resolves** the `easy_lopsided` member (large true Δ) well under
  `B_max`, and **abstains** on a constructed unresolvable case at a tiny `B_max`.
- Reference/adaptive streams are **independent** (branch [0] vs [1]) — asserted.
- D2 diagnostic prints cleanly (no raise) for the hard members.

### Choices worth a line

- **Mean confidence sequence (§3's literal instrument)** vs. a tail-probability CS on
  `p_hi/p_lo` — chose the mean CS: it keeps the heavy-tail member adversarial and
  still agrees with the reference on all scored cases (load-bearing decision above).
- **Anytime-valid CS** vs. a naive per-batch percentile band: the naive band peeks
  and inflates false stops under optional stopping (PLAN decision 2026-09-19); the
  CS is the whole point.
- **Offline `--run` writes an artifact; gate `--check` stays a smoke** — the ≥500-seed
  battery run (§7) is seconds-to-minutes of numpy and must not enter the sub-second
  gate; the meaningful gate check is determinism + easy-case resolution + abstain.
- **D1 = defined Δ*=0 on degenerate draw** vs. reject-and-redraw — chosen for exact
  draw accounting; reviewer may flip.

## Footprint

Files to create:
- `src/adaptive_compute/adaptive.py`
- `src/adaptive_compute/sweep.py`
- `src/adaptive_compute/benchmark.py`
- `tests/test_adaptive.py`, `tests/test_sweep.py`, `tests/test_benchmark.py`
- `work/adaptive-procedure/results.md` (+ `results.json`) — the first-result artifact
- `knowledge/anytime-valid-band.md` — the CS instrument + estimand-alignment
  contract (why the band targets the reference functional; the `p_hi/p_lo`
  reduction), so it is not re-derived by the routing/explainability consumers.

Files to modify:
- `src/adaptive_compute/eval.py` — add `--run`; extend `--check` (adaptive coverage);
  apply the **D2** diagnostic fix.
- `src/adaptive_compute/bootstrap.py` — batched/streaming draws for the adaptive
  loop and the **D1** degenerate-resample policy, *without* changing the reference
  path's behavior or its draw accounting (reference results must stay bit-identical).
- `tests/test_bootstrap.py`, `tests/test_determinism.py` — cover the new batched path
  and D1; keep the existing reference-path assertions green (regression guard).
- `ARCHI.md` — Layout: new modules; **EVAL_METRIC** PROVISIONAL → **resolved** (the
  decision-agreement / per-stratum false-stop / draws / Pareto suite now exists and
  is named); note `eval --run` as the offline result path.
- `PLAN.md` — Orchestrator-owned (not in the implementer diff): Now/Next + a
  Decisions line for the estimand-alignment choice and the H1 outcome. Done at
  approval/release time, outside the worktree.

Files NOT to touch:
- `src/adaptive_compute/reference.py` — the reference functional is **frozen**; we
  target it, never alter it (changing it is a separate unit). Live hazard: editing
  it would silently redefine "agreement" and invalidate the comparison.
- `scripts/gate.sh`, `scripts/release.sh`, `config.yaml`, `profiles/`, `.claude/`.

## Acceptance criteria

- [ ] **Blindness:** `adaptive.py`'s public entry takes none of `B_ref`, the
      reference decision, or the true/plug-in Δ (asserted by signature inspection in
      `test_adaptive.py`).
- [ ] **Adaptive determinism (both paths):** same `(params, seed)` int **and** reused
      `SeedSequence` object each reproduce a bit-identical decision + draw count
      (`test_adaptive.py` / `test_determinism.py`), and the adaptive stream differs
      from the reference stream (branch [1] vs [0]).
- [ ] **Draw accounting:** `draws_consumed` equals the exact resamples spent and is
      `≤ B_max`; a resolved run reports `< B_max`; an unresolvable case at small
      `B_max` returns `abstain` with `draws_consumed == B_max`.
- [ ] **Instrument correct & anytime-valid:** the mean-CS interval `[L_t,U_t]` gates
      the stop; a test asserts the stop fires only when `[L_t,U_t]` lies wholly on
      one side of `±δ` or wholly inside `[−δ,+δ]` (no peeking on the raw batch mean).
- [ ] **Reference-functional agreement (definitional):** at generous `B_max` the
      adaptive decision equals `fixed_budget_reference(...).decision` for ≥1 member
      per resolved class — `A_better`/`equivalent` from the battery, and **`B_better`
      from a constructed fixture** (an A-favored member with `scores_a`/`scores_b`
      swapped; no `BATTERY` member is B-favored — finding 5).
- [ ] **D1 resolved:** a forced degenerate resample (all-positive or all-negative
      draw) follows the defined policy (no uncaught `ValueError`); draw accounting
      stays exact under it (`test_bootstrap.py`).
- [ ] **D2 resolved:** the hard-member MCSE diagnostic (added by this unit) computes
      via `paired_bootstrap_deltas + np.mean` and **never routes through
      `fixed_budget_reference`** (asserted structurally; the raising path is not on
      the diagnostic's call graph).
- [ ] **Sweep + Pareto:** `sweep.py` produces the fixed-B grid decisions and a Pareto
      verdict; `test_sweep.py` asserts the domination logic on a synthetic fixture
      (a hand-built case where a fixed-B is/ isn't dominated).
- [ ] **Reference path unchanged:** existing `reference.py` outputs and
      `eval --check` reference draw count are bit-identical to pre-unit
      (regression assertion / `git`-diff of a recorded value).
- [ ] **First result produced:** `python -m adaptive_compute.eval --run` writes
      `work/adaptive-procedure/results.{md,json}` with, per non-`boundary` stratum:
      false-stop rate + binomial CI, draws p50/p90/p99, abstain rate, the
      `reference_unresolved` count, and the Pareto savings summary; the artifact
      states plainly whether **H1 holds or is a negative result** per §8 (either is
      acceptable and shippable), and reports the heavy-tail member's realized
      false-stop rate specifically (the §6-required adversarial check).
- [ ] **Gate green & fast:** `bash scripts/gate.sh` exits 0; `eval --check` stays
      sub-second-ish (< 5 s) and its adaptive assertions fail on a deliberately
      perturbed seed (tested, not committed-perturbed).
- [ ] `ARCHI.md` EVAL_METRIC is resolved (names the suite) and lists the new modules.

## Release

Release note: Add the adaptive Monte-Carlo stopping procedure (anytime-valid
confidence sequence on the reference's decision functional, blind, seeded on the
adaptive branch), the fixed-B sweep + Pareto baseline, and the offline eval harness
that produces the v0 first result (per-stratum false-stop rate, draws, savings);
resolve deferrals D1 and D2; EVAL_METRIC resolved.

## Verification

- `bash scripts/gate.sh`
- `python -m adaptive_compute.eval --check` (fast; also in the gate)
- `python -m adaptive_compute.eval --run` (offline; writes the result artifact) —
  Owner reviews `work/adaptive-procedure/results.md` and the H1 verdict.

## Review

Fresh cold read-only reviewer (stood in as a `Plan`-type subagent; the named
`plan-reviewer` agent type is unregistered in this harness build — writer ≠ reviewer
preserved, read-only enforced). It verified the reduction algebra against
`_decision_from_interval`, the seed contract, the deferrals, and the battery.
Verdict: **REVISE**, 5 findings. All accepted; incorporated as follows:

1. **Primary instrument risked making §6's heavy-tail member (and §8's tolerance)
   vacuous** — a tail-probability CS on bounded 0/1 indicators is immune to tail
   heaviness by construction, so H1 could pass without stress-testing premature
   convergence, and §3 literally specifies the mean CS. **Fixed:** switched the
   chosen instrument to the **mean CS**, which keeps heavy tails adversarial *and*
   (because the battery is built so the reference verdict == `decision_from_delta`
   on non-boundary members) still coincides with the reference on all scored cases.
   The tail-prob reduction is retained only as the documented rejected alternative.
   Routed to the Owner for sign-off (below), per the reviewer's point that this
   defines what "false stop" measures.
2. **"Exact against `_decision_from_interval`" was overstated.** The reduction is
   exact for the three resolved verdicts *in the B→∞ functional*; the fourth
   (straddle) branch maps to reference-*unresolved*, and the released reference is a
   finite-B percentile draw. **Fixed:** wording now says "B→∞ bootstrap functional"
   and names the straddle→unresolved mapping.
3. **Adaptive seeding was under-specified ("either/or") and risked contract drift.**
   **Fixed:** committed to one design — shared inner resample kernel (reference path
   byte-identical) + a new `adaptive_bootstrap_stream` routing through
   `adaptive_seed` (branch [1]) via a single generator; both-path determinism and
   exact accounting specified.
4. **Benchmark straddle exposure and seed-sweep mechanism unspecified.** **Fixed:**
   named the `dataclasses.replace(params, seed=…)` sweep with disjoint tune/test
   ranges, and a `reference_unresolved` exclude-and-report policy for straddles over
   many seeds.
5. **No `B_better` battery member** for the agreement criterion. **Fixed:** that
   class uses a constructed swapped-scores fixture; criterion reworded.

Reviewer also confirmed D1/D2 land correctly here, and clarified D2 is *adding* the
hard-member diagnostic in the correct (non-raising) pattern, not fixing an existing
raising call — criterion reworded accordingly.

**Owner sign-off (2026-09-20):** confirmed the **mean confidence sequence** as the
anytime-valid instrument (vs. the tail-probability alternative). No open items.

Plan verdict: **REVISE → addressed; APPROVED.**

---

### Code review (/3-review) — three rounds, dual APPROVE

Two independent cold reviewers per round: the `code-reviewer` (stood in as a read-only
`Plan`-type subagent, the named agent type being unregistered in this build; writer ≠
reviewer preserved) and Codex via `scripts/codex-review.sh`. Reached dual APPROVE at
round 3. Accepted deferrals: `deferrals.md` A1–A5 (all latent LOW). The result is a
genuine, non-artifact **H1 NEGATIVE**: the adaptive method resolves every non-boundary
case with a **zero false-stop rate** in all strata (§7 test PASS, heavy-tail member 0.0000,
no vacuous abstain), but **fails §8's ≥2× savings/Pareto gate** — its median draws
(448 moderate / 768 equivalent) exceed the whole fixed-B grid, so it does not beat a
well-chosen fixed budget on compute. Honest negative, shippable per §8.

- **R1** (both REQUEST CHANGES): CRITICAL — the first result was a *vacuous artifact*: a
  too-loose EB boundary (linear term 0.1215 > δ) plus `B_max=320` made `equivalent`/`moderate`
  abstain ~100%, so the false-stop 0.0 was meaningless and §6/§8 non-falsifiable. HIGH — the
  fixed-B/Pareto comparison was scored on the reference's own draws with unresolved fixed-B
  credited cheap budget, and the §8 ≥2× gate was unchecked. HIGH — a decision resolving on the
  final batch was discarded as `abstain`. Fixed: finite-horizon EB boundary + tuned `B_max=2048`
  (tune split), fair independent-stream fixed-B with symmetric non-decision accounting, ≥2× gate
  wired in, terminal-batch resolution honored, and the AUC kernel optimized.
- **R2** (code-reviewer APPROVE / Codex REQUEST CHANGES): the round-1 optimization had dropped
  reference-path input validation (silent Δ*=0 on malformed input) and broke bit-identity (~1e-16
  reassociation drift); `N_test=500` missed the §7 CI-precision commitment. Fixed: validation
  restored on both paths, original arithmetic association restored (bit-identical), `N_test=2000`,
  and a §7-test/§8-conclusion breakdown added to the artifact.
- **R3**: **both APPROVE.** Anchor independently verified bit-identity (max abs diff 0.0),
  restored validation, `N_test=2000` (Wilson upper at k=0,n=2000 = 0.0019 ≪ 0.01), and the valid
  §8 negative. Remaining findings all LOW → `deferrals.md` A1–A5.

Code-review verdict: APPROVE
Codex-review verdict: APPROVE
