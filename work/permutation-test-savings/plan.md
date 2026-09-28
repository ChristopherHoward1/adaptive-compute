# Permutation tests: certified adaptive Monte-Carlo savings across many hypotheses

**Slug:** permutation-test-savings · **Date:** 2026-09-26 · **Status:** withdrawn at plan stage (2026-09-26). Not implemented; see `## Review` and `knowledge/permutation-test-savings.md`.

## Goal

Test the adaptive MC-budget idea where the decision *is* a certificate. The three earlier
setups died because a cheap baseline never had to certify (`knowledge/shap-topk-savings.md`
→ "The recurring pattern"). A family of permutation tests is different. The output is
"feature j is significant at family-wise α", and a fixed budget can't make that claim at
all unless `B ≥ m/α − 1`. The estimand is the permutation p-value `P*(T* ≥ T_obs)`. That
is the tail-probability functional `knowledge/anytime-valid-band.md` names as the
remaining place an MC-budget claim can have content.

Done means an offline `eval --perm` run that writes a pre-registered verdict to
`work/permutation-test-savings/results.{md,json}`. The verdict reports adaptive against
four comparators: zero-draw asymptotic tests, fixed-B, **curtailed** fixed-B and
certified fixed-B. A `knowledge/` note scopes whatever result comes out. This
operationalizes H2's "stopping machinery transfers" question on a testing consumer
(`docs/research-definition.md` §4). It does **not** re-open H1.

## Detectability precondition (per the 2026-09-22 decision)

Governing cold docs, loaded at plan time: `knowledge/anytime-valid-band.md`,
`knowledge/shap-topk-savings.md`, `knowledge/controlled-retest-discipline.md` and
`knowledge/research-doc-citations.md`.

A scratch prototype was run at plan time (`prototype.py.txt`; output
`prototype-run30.log`). Setup: 30 datasets × m=100 features, n=100, 10 signal features
per dataset. Statistic: U-centered distance covariance with y, with permutations of y
shared across features. Bonferroni threshold 5e-4, stream L=50,000. Reference at
L_EXT=500,000 for features whose 99.9% Clopper–Pearson interval straddles the threshold.
**Seeds 300000–300029 and 999000–999001 are burned.** The signal-coefficient range was
widened from `[0.05,1]` to `[0.1,2]` after the 2-dataset smoke run (seeds 999000–1)
produced 1 rejection in 200. The range is pinned below and must not move again.

Findings (3,000 features, 37 reference rejections, 2 reference-unresolved):

| Arm | Draws per dataset | Disagree with reference |
|---|---|---|
| Fixed-B, valid p `(1+S)/(1+B)`, B=1,999 | 199,900 | 7 (3 missed, 4 extra) |
| Fixed-B, B=19,999 | 1,999,900 | 0 |
| **Curtailed** fixed-B, B=1,999 (stop at first exceedance past the critical count) | 3,732 | same 7, identical decisions to fixed-B by construction |
| Curtailed fixed-B, B=19,999 | 38,754 | 0 |
| Certified fixed-B (Clopper–Pearson at 1e-4), B=19,999 | 1,999,900 | 0 wrong, 0.67% undecided |
| **Adaptive** (Beta(1,1)-mixture LR vs p=thr, anytime at 1e-4, M_max=50,000) | 81,690 (abstain charged at M_max) | 0 wrong, 0.60% abstain |

- **The zero-draw threat is cleared on this mix.** The distance-correlation t-test
  (Székely & Rizzo 2013 (verify)) is anti-conservative at n=100 with heavy tails: 65
  extra rejections out of 2,998. The Pearson t-test tests a different, linear
  hypothesis: it missed 11 of 37 reference rejections, the nonlinear signals, and added
  5 extra.
- **Ties are rare.** 0.77% of features have a reference p in `[thr/4, 4·thr]`. That is
  7% of signals (21/300) and about 0.02% of nulls, against 13/40 in SHAP.
- **Against certified fixed-B, adaptive saves about 24×**, compared with 2.3× in SHAP.
- **Curtailed fixed-B dominates adaptive.** At the conventional B=1,999 it is about 22×
  cheaper with 0.23% disagreement. At the oracle-picked B=19,999 it is 2.1× cheaper
  with 0 disagreement. Curtailment is Besag & Clifford (1991) in its simplest form. It
  yields exactly the fixed-B decisions, and fixed-B p-values are valid at any B, so it
  needs no anytime machinery.
- **Adaptive's cost is signals.** Nulls average 76 draws. Signals average 7,486, because
  certifying a rejection against the B→∞ decision takes about `log(1/ε)/thr` draws or
  more. Beta(1,1) needs about 40,000 draws for S=0, against about 18,400 for a
  fixed-horizon Clopper–Pearson interval.

What the experiment must be able to express (enforced below):

- **(P1)** Neither zero-draw rival matches the reference to within adaptive's error plus
  abstain rate.
- **(P2)** The certified fixed-B grid reaches adaptive's abstain rate, so there is no
  grid-ceiling strawman. The grid runs to 49,999, which is ≥ M_max.
- **(P3)** The reference is resolved on ≥ 99% of features.

If any fails, the verdict is `NOT_DETECTABLE`.

**Expected outcome, stated before building.** V1 passes at about 24× and V2 shows
curtailment cheaper than adaptive. That is a *positive for sequential MC testing* which
is classical, and a *negative for the anytime-valid instrument's specific contribution*
under Bonferroni. The unit is worth building only if the Owner wants that on record as a
released artifact. The alternative is the BH/FDR extension below.

## Approach

**Pre-registered constants (fixed a priori, no tuning split):**

- n=100, m=100, 10 signals per dataset, α=0.05, threshold `α/m = 5e-4`.
- Signal forms {x, x², |x|, sin 2x, sign x}, each standardized. Coefficients are
  log-uniform on `[0.1, 2]`.
- Feature marginals are N(0,1) or t₃, 50/50. Noise is N(0,1) or t₃, 50/50 per dataset.
- Per-feature resampling risk `ε = 1e-4` (family 0.01).
- `M_max = L = 50,000`. `FIXED_B_GRID = (1999, 3999, 7999, 19999, 49999)`.
- Reference extension `L_EXT = 500,000` for straddling features, using a 99.9%
  Clopper–Pearson interval.
- Datasets: **100**, seeds from 400000 up, recorded in the output.

**Draw stream.** Per dataset, one seeded stream of y-permutations shared across all m
features. Every arm reads prefixes of the same exceedance matrix, so arms differ only in
reading policy (controlled-retest rule 2). The reference extension uses a separate
seeded stream.

**Arms.**

1. **Adaptive:** per feature, a Beta(1,1)-mixture likelihood ratio against `p = thr`.
   It stops when `LR ≥ 1/ε`. The side is taken from `S/n` versus thr; the MLE always
   lies inside the confidence set. At M_max it abstains. It is blind to the reference,
   to signal labels and to the effect size.
2. **Fixed-B:** valid p `(1+S_B)/(1+B)`, rejecting iff `≤ thr`, at each grid B.
3. **Curtailed fixed-B:** arm 2's decisions, stopping a feature as soon as its
   exceedance count passes the critical count. Its decisions must equal arm 2's exactly.
4. **Certified fixed-B:** a Clopper–Pearson interval at ε at each grid B. It decides iff
   the interval excludes thr, otherwise it is undecided.
5. **Zero-draw:** the distance-correlation t-test and the Pearson t-test, each at thr.

**Verdicts (pre-registered, all written, none collapsed):**

- **V0, detectability:** P1, P2 and P3, each reported individually.
- **V1, certified savings (headline):** passes iff all of these hold:
  - adaptive's wrong-rate upper Wilson CI ≤ ε·10 on decided, reference-resolved
    features;
  - `B_match·m / adaptive mean draws per dataset ≥ 2`, where `B_match` is the smallest
    certified grid B with undecided rate ≤ adaptive's abstain rate and wrong ≤ adaptive
    wrong. Pooled over the natural mix.
- **V2, curtailment comparator (reported, not gating):** the ratio of adaptive's mean
  cost to curtailed cost at B=1,999 and at `B_oracle`, the smallest grid B with 0
  disagreement, with the disagreement count at each.
- **Headline:** `CERTIFIED_POSITIVE`, `NEGATIVE` or `NOT_DETECTABLE`, with both V2
  ratios on the same line.

**Code shape.** New modules only. The released `benchmark.py`, `sweep.py`, `betting.py`,
`adaptive.py`, `reference.py`, `equiv_probe.py` and the existing eval paths stay
unchanged (controlled-retest rule 1).

**Alternatives considered:**

- *BH/FDR instead of Bonferroni:* the BH threshold depends on all p-values, so plain
  curtailment has no fixed critical count. This is where anytime-valid allocation could
  have content not covered by Besag–Clifford. Prior art: AMT, Zhang, Zou & Tse (2019)
  (verify). This is the stronger research question and a larger unit. Deferred pending
  the Owner's call.
- *A tighter anytime instrument, i.e. a prior concentrated near thr:* rejected for this
  unit. Choosing it after seeing the Beta(1,1) signal cost is tuning on burned data. Even
  at the fixed-horizon floor of about 18,400 draws per certified rejection, adaptive
  still trails curtailed B=19,999.

## Footprint

Files to create:
- `src/adaptive_compute/permtest.py`: dataset generator, U-centered dCov, the shared
  permutation-exceedance stream with draw accounting, and the zero-draw rivals.
- `src/adaptive_compute/perm_bench.py`: the arms, reference with extension, V0/V1/V2
  verdicts, and the writers for `work/permutation-test-savings/results.{md,json}`.
- `tests/test_permtest.py`, `tests/test_perm_bench.py`
- `knowledge/permutation-test-savings.md`: result and scope, written from the run.
- `work/permutation-test-savings/results.md`, `results.json`: generated.

Files to modify:
- `src/adaptive_compute/eval.py`: add the `--perm` flag and a small-config determinism
  replay in `_check()`.
- `docs/research-definition.md`: one line under H2 pointing here.
- `knowledge/README.md`: an index line.

Files NOT to touch:
- `src/adaptive_compute/{benchmark,sweep,betting,adaptive,reference,equiv_probe}.py`
  and all released `work/*/results*` artifacts.

## Acceptance criteria

- [ ] **dCov is correct.** A test checks U-centered dCov against a naive double-loop
  implementation on n=12, to 1e-12. A test checks that it is invariant to jointly
  permuting x and y.
- [ ] **Exceedance stream.** The observed statistic under the identity permutation
  counts as an exceedance. A test checks that the stream prefix of length t equals an
  independently regenerated stream of length t, with no self-comparison.
- [ ] **Curtailment equivalence.** For every dataset and grid B, the curtailed decisions
  equal the fixed-B decisions. This is asserted in the run and tested on synthetic
  exceedance matrices, including one with S exactly at the critical count.
- [ ] **Anytime validity smoke.** On 2,000 simulated Bernoulli streams at `p = thr·1.5`
  and `p = thr/1.5`, adaptive's wrong-side rate is ≤ ε·10.
- [ ] **Blindness.** The adaptive stopper's signature takes only the exceedance stream,
  thr, ε and M_max. Checked by diff inspection plus a test.
- [ ] **Determinism.** Two `eval --perm --datasets 2` runs produce byte-identical
  `results.json`. `eval --check` includes a 1-dataset, small-L replay and adds ≤ 10s to
  its `main` baseline, which is measured and recorded in the handoff.
- [ ] **Seeds.** `results.json` records the seed range. It contains no seed in
  300000–300029 or 999000–999001, and 100 datasets.
- [ ] **All verdicts present.** `results.md` reports P1/P2/P3 individually, and V1 with
  `B_match` and the ratio. For each arm and grid B it reports cost and disagreement split
  into missed and extra. It also reports the near-threshold rate, adaptive's null and
  signal mean draws, V2 at both B values, and one headline line.
- [ ] **Released artifacts untouched.**
  `git diff origin/main...wt/permutation-test-savings -- work/adaptive-procedure work/betting-cs-retest work/equivalence-band-savings src/adaptive_compute/benchmark.py src/adaptive_compute/sweep.py src/adaptive_compute/betting.py src/adaptive_compute/adaptive.py src/adaptive_compute/reference.py src/adaptive_compute/equiv_probe.py`
  is empty.
- [ ] **Scoped knowledge note.** `knowledge/permutation-test-savings.md` states the
  headline, scopes any positive as *against certified fixed-B*, puts V2 next to it, and
  names Besag–Clifford curtailment as the dominating classical rule if V2 shows it.
- [ ] `bash scripts/gate.sh` exits 0.

## Release

Release note: Add `eval --perm`, an offline multiple-permutation-test experiment
comparing an anytime-valid adaptive stopper against zero-draw, fixed-B, curtailed and
certified fixed-B baselines, with a pre-registered verdict.

## Verification

- `PYTHONPATH=src python -m adaptive_compute.eval --perm` (offline; about an hour at 100
  datasets), then inspect `work/permutation-test-savings/results.md`.
- `PYTHONPATH=src python -m adaptive_compute.eval --check`

## Review

**Cold plan-reviewer, rev 1: REVISE, 10 findings. The Orchestrator agrees with all of
them. The reviewer recommends withdrawing at plan stage; that choice is the Owner's.**

1. **V1's 24× is a strawman (severe).** Certified fixed-B's decision is monotone in S,
   so it can be curtailed exactly like arm 3. The certified-curtailed arm cost 57,630
   draws per dataset at B=19,999 (1.33% undecided) and 134,919 at B=49,999. Adaptive
   cost 95,374 with 1.0% abstain. Reviewer re-run, 3 fresh datasets, seeds
   8800000–8800002. The certified ratio is about 0.4–1.7×, so V1 flips to NEGATIVE.
   The 24× was curtailment of nulls, not anytime validity.
2. **Prior art subsumes the adaptive arm.** Gandy (2009) is exactly this per-feature
   threshold decision with bounded resampling risk (`docs/prior-art.md`). The BH/FDR
   extension has MMCTest (Gandy & Hahn (verify)) and AMT (verify) as direct ancestors.
   Any successor plan must state novelty against both.
3. **The Goal's premise is overstated.** Fixed B=1,999 with `(1+S)/(1+B)` gives exact
   FWER control. The adaptive arm certifies agreement with the B→∞ decision, at an
   extra `m·ε` of error, so its total bound is `α + mε`. The fixed-B "disagreements" are
   two valid tests disagreeing, not errors. The application needs a certificate only if
   reproducibility against B→∞ is the product.
4. **Not worth building.** The expected outcome is textbook-predictable, and the
   prototype already establishes it. Record it in `knowledge/` plus one PLAN.md Decision
   line, with no `src/` change.
5. **The expected V1 number was wrong under the plan's own rule.** B=19,999 is 0.667%
   undecided, which is above adaptive's 0.600%, so B_match would be 49,999, giving about
   61×. The step-function match is knife-edge. Abstains charged at M_max are about 30k
   of adaptive's 81.7k draws per dataset.
6. **The anytime smoke test was vacuous.** At p = thr·1.5 nearly every stream abstains
   at M_max. It should test at p = thr (Ville) plus far-side sign cases.
7. **scipy is not a runtime dependency.** The runtime is numpy-only, and the footprint
   omitted this.
8. **The reference shared the arms' stream,** which biases `B_oracle` toward large B.
   The extension also reused the same generator, contrary to the plan text.
9. **Acceptance-criteria gaps:** equivalence for the certified-curtailed arm, a concrete
   blindness assertion, the `--datasets` flag missing from the footprint, a
   near-threshold wrong-rate subset, and a formula for P1.
10. **The dCor t-test is a weak zero-draw rival** (a high-dimension asymptotic). A
    moment-matched or Pearson-III approximation of the permutation null is the fair
    one.

Plan verdict: REVISE
