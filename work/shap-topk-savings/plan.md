# SHAP top-k: certified adaptive Monte-Carlo savings on a no-closed-form estimand

**Slug:** shap-topk-savings · **Date:** 2026-09-23 · **Status:** withdrawn at plan stage (2026-09-23). Not implemented; see `## Review` and `knowledge/shap-topk-savings.md`.

## Goal

Test the adaptive MC-budget idea on an estimand where draws actually buy accuracy. The
previous line died because `E*[Δ*]` equals the plug-in `Δ(E)`, which costs zero draws
(PR #22, `knowledge/anytime-valid-band.md` → "The mean estimand is closed-form").
Shapley attributions of a nonlinear model have no cheap closed form. Exact
interventional Shapley costs `2^D · |bg|` model evaluations, while a permutation draw
(Štrumbelj–Kononenko) costs `D+1`.

The decision is **ε-correct top-k feature identification**: return a set `S` of `K`
features with `min_{i∈S} |φ_i| ≥ |φ|_(K) − ε`, or abstain at `M_max`. Done means an
offline `eval --shap` run that writes a pre-registered, per-stratum verdict to
`work/shap-topk-savings/`. The verdict reports adaptive against three comparators:
exact enumeration, a certified fixed-M budget, and an oracle-tuned *uncertified*
fixed-M budget. A `knowledge/` note scopes whatever result comes out.

This operationalizes H2 (`docs/research-definition.md` §4) as a savings question in
its own right. It does **not** re-open H1.

## Detectability precondition (per the 2026-09-22 decision)

Governing cold docs, loaded at plan time: `knowledge/anytime-valid-band.md` (including
the closed-form section in PR #22), `knowledge/equivalence-band-savings.md` and
`knowledge/controlled-retest-discipline.md`.

A scratch prototype was run at plan time (D=8, K=2, |bg|=16, ε=0.01, α=0.05, betting CS
at α/D per feature, 60 cases, seeds 1000–1059; **these seeds are burned and excluded
from the test split**). It found:

- **No zero-cost surrogate.** The linear-term ranking `|w_j (x_j − mean bg_j)|` was
  ε-correct on only 40% of cases, and permutation MC matched exact φ to about 1e-3.
- **Difficulty is heterogeneous.** The K-th/(K+1)-th gap ranged over 0.005–0.093
  (10th–90th percentile). Adaptive draws ranged over 382 / 820 / 1680 / 6144 / 14099
  (10th/25th/50th/75th/90th percentile), with 4/60 abstentions at 16384 and 0 wrong.
- **Against a certified fixed-M, adaptive wins.** Reading the *same* betting CS once at a
  pre-set M, the non-decision rate was 0.78 at 512, 0.47 at 2048, 0.18 at 8192 and 0.10
  at 16384. No grid M reached adaptive's 0.067 abstain rate. A fixed-time empirical-
  Bernstein CI was worse at every M.
- **Against an uncertified oracle-tuned fixed-M, adaptive loses.** Plain top-k of the
  point estimate had error 0.033 at M=512 and 0 at M≥2048, which beats adaptive's median
  of 1680. It is right without being able to certify. This is the fixed-width asymmetry
  again (`knowledge/equivalence-band-savings.md`), and the plan reports it rather than
  hiding it.
- **The closed-form trap reappears at small D.** At D=8, |bg|=16, exact enumeration costs
  4096 evaluations, about 455 permutations, so it beats adaptive. That is why this plan
  uses **D=12, |bg|=64**: exact costs 262,144 evaluations, about 20,165 permutations.

What the experiment must be able to express, enforced below:

- (P1) Exact enumeration must be more expensive than adaptive's median, in evaluations.
- (P2) The fixed-M grid must extend far enough that a certified fixed-M *can* match
  adaptive's abstain rate. The grid goes to 4·M_max, so there is no grid-ceiling
  strawman.
- (P3) The linear surrogate must not solve the task.

If any of these fails on the test run, the verdict is `NOT_DETECTABLE`, not positive and
not negative.

## Approach

**Pre-registered constants (fixed a priori, no tuning split):** D=12, K=3, |bg|=64,
ε=0.01, α=0.05, per-feature CS level α/D (union bound), batch b=32 permutations,
M_max=16384, `FIXED_M_GRID = (64, 128, …, 65536)` (doubling, up to 4·M_max), and a
betting grid of 2001 points.

**Battery.** Each case is a random `f(x) = sigmoid(w·x + xᵀVx)`, with V strictly upper
triangular for pairwise interactions, plus a query point x and a background of 64
points, all seeded. Exact interventional Shapley over the empirical background is
computed by vectorized enumeration of 2^12 coalitions. The uniformly sampled background
point is part of the draw, so a draw is an unbiased estimate of the exact φ.

Cases are stratified by `g = |φ|_(K) − |φ|_(K+1)` relative to ε:
- `tie`: g < ε (either set is ε-correct)
- `hard`: ε ≤ g < 3ε
- `moderate`: 3ε ≤ g < 10ε
- `easy`: g ≥ 10ε

Seeds are drawn from a fixed test range starting above the burned prototype seeds, and
enumerated until every stratum has **≥ 100 cases**. Quota filling conditions only on the
exact φ, never on any procedure's outcome. The run records the seed range used.

**Draw stream.** Per case, one seeded stream of permutation draws. Draw t is a vector in
`[-1,1]^D` of marginal contributions along a random permutation against a random
background row. The stream is generated to `max(FIXED_M_GRID)`. Every arm reads a prefix
of the **same** stream, so the only difference between arms is the reading policy
(controlled-retest rule 2). Draws and model evaluations (`draws·(D+1)`) are both
recorded.

**Arms.**
1. **Adaptive:** a per-feature WSR betting CS at α/D. After each batch it forms |φ|
   intervals, takes the top-K by point estimate, and stops when
   `min_{i∈S} lower|φ_i| > max_{j∉S} upper|φ_j| − ε`. At M_max it abstains. It is blind
   to exact φ, strata and the reference.
2. **Certified fixed-M:** at each grid M, a single read of (a) the same betting CS and
   (b) a fixed-time empirical-Bernstein CI at α/D. The decision is certified if the same
   separation holds, otherwise it is a non-decision. Per M, the arm takes the better of
   (a) and (b), which is generous to the baseline.
3. **Uncertified fixed-M:** plain top-K of the prefix mean at each grid M, with no
   abstention.
4. **Exact enumeration:** cost `2^D·|bg|` evaluations, error 0.

**Verdicts (pre-registered, all written, none collapsed):**
- **V0, detectability:** P1, P2 and P3 hold, otherwise the headline is `NOT_DETECTABLE`.
  - P1: adaptive's pooled median evaluations ≤ ½ of exact-enumeration cost.
  - P2: some certified grid M has non-decision ≤ adaptive's pooled abstain rate.
  - P3: the surrogate's ε-correct rate is < 1 − α.
- **V1, certified savings (headline):** passes iff every one of these holds:
  - adaptive's per-stratum false-stop upper Wilson CI ≤ α;
  - no certified fixed-M with M ≤ adaptive's pooled median has both non-decision ≤
    adaptive abstain and error ≤ adaptive error;
  - `M_match / median ≥ 2`, where M_match is the smallest certified grid M whose
    non-decision ≤ adaptive abstain rate and whose error ≤ adaptive error, both pooled.
  The same numbers are also reported per stratum.
- **V2, uncertified oracle comparator (reported, not gating):** `M_oracle` is the
  smallest grid M whose uncertified error is ≤ α in every stratum. The run reports
  `M_oracle / adaptive median`, which is expected to be < 1.
- **Headline string:** `CERTIFIED_POSITIVE` if V0 and V1 pass, `NEGATIVE` if V0 passes
  and V1 fails, `NOT_DETECTABLE` if V0 fails. The V2 ratio is always printed on the same
  line.

**Code shape.** New modules only. The released `benchmark.py`, `sweep.py`, `betting.py`
and `--run` / `--compare` / `--equiv-probe` paths stay unchanged (controlled-retest rule
1). A vectorized `(D, grid)` betting state lives in the new module, because a
per-feature `BettingCSState` loop is too slow at 12 × 65536 steps per case. A guard test
pins it to `BettingCSState` per feature.

**Alternatives considered:**
- KernelSHAP / Covert–Lee convergence detection: prior art, deferred. A later unit
  compares against it.
- Tuning b or α on a split: rejected. Everything is pinned a priori to remove degrees of
  freedom after two negatives.
- A boundary-stratum exclusion as in H1: unnecessary, because ε-correctness is exactly
  defined against the exact φ.

## Footprint

Files to create:
- `src/adaptive_compute/shapley.py`: the sigmoid-polynomial case generator, exact
  interventional Shapley by vectorized enumeration, the seeded permutation-draw stream
  with draw and evaluation accounting, and the linear surrogate.
- `src/adaptive_compute/shap_bench.py`: the vectorized multi-feature betting state, the
  fixed-time EB CI, the adaptive top-K stopper, the fixed-M arms, stratification and
  quota filling, the V0/V1/V2 verdicts, and the writers for
  `work/shap-topk-savings/results.{md,json}`.
- `tests/test_shapley.py`, `tests/test_shap_bench.py`
- `knowledge/shap-topk-savings.md`: result and scope, written from the run.
- `work/shap-topk-savings/results.md`, `results.json`: generated by `eval --shap`.

Files to modify:
- `src/adaptive_compute/eval.py`: add the `--shap` flag, plus a small fast determinism
  check in `_check()` (a 2-case, small-M replay).
- `docs/research-definition.md`: one line under H2 pointing to this unit's
  operationalization.

Files NOT to touch:
- `src/adaptive_compute/{benchmark,sweep,betting,adaptive,reference,equiv_probe}.py`
  and all released `work/*/results*` artifacts. These are released baselines
  (controlled-retest rule 3).

## Acceptance criteria

- [ ] **Exact Shapley is correct.** A test on a D=4 case checks exact φ against a
  brute-force Shapley formula written independently of the vectorized path, to 1e-12.
  A test checks that exact φ sums to `f(x) − mean f(bg)` (efficiency). A test checks that
  the mean of 20,000 permutation draws is within 5e-3 of exact φ at D=6.
- [ ] **Draws are bounded and accounted for.** Every draw vector lies in `[-1,1]^D`. The
  recorded evaluation count equals `draws·(D+1)` exactly.
- [ ] **Vectorized CS guard.** For a random `(n, D)` draw matrix, the vectorized state's
  per-feature bounds equal `BettingCSState(grid=_mean_grid(2001))` bounds per feature.
  The test must fail if a single feature's column is permuted between the two.
- [ ] **Same-stream guard.** The adaptive arm's consumed draws equal the prefix of the
  case stream of the same length. The test reconstructs the stream independently and
  never compares a value to itself.
- [ ] **Blindness.** The adaptive stopper's signature takes no exact-φ, stratum or
  reference argument. Checked by diff inspection plus a test that calls it with only its
  declared inputs.
- [ ] **Determinism.** Two `eval --shap` runs on a reduced configuration produce
  byte-identical `results.json`. `eval --check` includes the 2-case replay and stays
  under its current runtime by at most +10s.
- [ ] **Quota and seeds.** `results.json` records the seed range. It shows ≥ 100 scored
  cases per stratum and no seed in 1000–1059.
- [ ] **All verdicts present.** `results.md` reports, per stratum and pooled: adaptive
  false stops with Wilson CI, abstain rate, draws and evaluations at p50/p90/p99; the
  certified-arm non-decision and error at each grid M, with the source (a) or (b) that
  won; uncertified error at each grid M; exact-enumeration cost; the surrogate ε-correct
  rate; V0 with P1/P2/P3 individually; V1; V2; and the single headline line with the V2
  ratio on it.
- [ ] **Released artifacts untouched.**
  `git diff origin/main...wt/shap-topk-savings -- work/adaptive-procedure work/betting-cs-retest work/equivalence-band-savings src/adaptive_compute/benchmark.py src/adaptive_compute/sweep.py src/adaptive_compute/betting.py src/adaptive_compute/adaptive.py src/adaptive_compute/reference.py src/adaptive_compute/equiv_probe.py`
  is empty.
- [ ] **Scoped knowledge note.** `knowledge/shap-topk-savings.md` states the headline and
  explicitly scopes any positive as *against a certified fixed budget*, with the V2
  uncertified comparison next to it.
- [ ] `bash scripts/gate.sh` exits 0.

## Release

Release note: Add `eval --shap`, an offline SHAP top-k experiment comparing an adaptive
certified stopper against exact enumeration and against certified and uncertified
fixed-M budgets, with a pre-registered verdict.

## Verification

- `PYTHONPATH=src python -m adaptive_compute.eval --shap` (offline; may take tens of
  minutes), then inspect `work/shap-topk-savings/results.md`.
- `PYTHONPATH=src python -m adaptive_compute.eval --check`

## Review

**Cold plan-reviewer, rev 1: REVISE, 9 findings. The Orchestrator agreed with all of them.**

1. Arm (a), the same betting CS read once at M, is dominated by construction. The
   running-max survivor set (`betting.py:167`) is nested over time, so V1 could not
   come out negative. It must be replaced by a fixed-horizon certificate.
2. P2 was vacuous for the same reason.
3. Cost must be *mean* draws with abstentions charged at M_max, not the median.
4. Pool over the natural case mix, not equal stratum quotas. Easy is about 1% of cases
   at D=12.
5. The tie stratum's false-stop denominator must be decided cases, which makes the
   quota sample-size-bound. The tie stratum abstains about 38% of the time.
6. The cited evidence was gathered at D=8, not the pinned constants. |bg|=64 was chosen
   after seeing exact enumeration win at |bg|=16, and |bg| decides P1.
7. P3 needs the strongest cheap surrogate: the closed-form Shapley of the quadratic
   logit.
8. Runtime is unbounded without a scored-case cap. Pin the test seed start.
9. Several acceptance criteria were uncheckable as written: the reduced-config
   interface, the check-runtime baseline, the CS-guard tolerance and overflow case, the
   blindness test, and a redundant V1 clause.

**Rev-2 evidence instead of a rev-2 plan.** A prototype applying findings 1, 3, 4, 6
and 7 (`prototype.py.txt`, output in `prototype-run40.log`; 40 natural-mix cases,
seeds 100000–100039, shared stream, fixed-horizon WSR and EB certificates) showed the
unit's most likely pre-registered outcome:

- P1 fails narrowly: adaptive with exact fallback costs 0.53 of exact.
- Certified savings are marginal: about 2.3× on mean cost.
- The uncertified fixed-M comparator is cheaper than adaptive.

The Owner chose to write the result up rather than build the unit. `eval --check`
baseline wall time on `main` was 44.7s, measured under concurrent load.

Plan verdict: REVISE
