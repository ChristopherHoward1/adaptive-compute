# Permutation tests: adaptive MC savings, plan-stage prototype

Load this before planning any adaptive-Monte-Carlo unit on hypothesis tests, or any
unit that claims a certificate is "required".

**Status.** This is a plan-stage prototype result, not a released experiment. The unit
`work/permutation-test-savings/plan.md` was withdrawn on 2026-09-26 after a cold plan
review, and the research line was closed. The prototype is
`work/permutation-test-savings/prototype.py.txt` and its output is
`prototype-run30.log`. Seeds 300000–300029, 999000–999001 and 8800000–8800002 (the
reviewer's re-run) are burned.

## Setup

- **Data.** 30 datasets, each with m=100 features, n=100 rows and 10 signal features.
  Signals take the forms {x, x², |x|, sin 2x, sign x} with log-uniform coefficients on
  `[0.1, 2]`. Marginals and noise are N(0,1) or t₃.
- **Test.** U-centered distance covariance of each feature with y. The permutations of
  y are shared across features.
- **Threshold.** Bonferroni at `α/m = 5e-4`.
- **Draw.** One permutation of y.
- **Adaptive arm.** Per feature, a Beta(1,1)-mixture likelihood ratio against
  `p = thr`, anytime-valid at per-feature risk `ε = 1e-4`, with `M_max = 50,000`. This
  is a Gandy (2009)-type rule.

## Result

| Arm | Draws per dataset | Outcome |
|---|---|---|
| Fixed-B, valid p `(1+S)/(1+B)`, B=1,999 | 199,900 | 7 of 3,000 differ from the B→∞ decision |
| Curtailed fixed-B, B=1,999 | 3,732 | identical to fixed-B |
| Curtailed fixed-B, B=19,999 | 38,754 | 0 differ |
| Certified fixed-B (Clopper–Pearson), B=19,999, full | 1,999,900 | 0.67% undecided |
| Certified fixed-B, curtailed, B=19,999 (reviewer, 3 datasets) | 57,630 | 1.33% undecided |
| Adaptive (30 datasets / reviewer's 3) | 81,690 / 95,374 | 0 wrong, 0.6% / 1.0% abstain |

- **Zero-draw rivals did not match.** The distance-correlation t-test was
  anti-conservative, with 65 extra rejections. The Pearson t-test missed 11 of 37
  nonlinear signals. But the dCor t-test is a weak rival; a moment-matched approximation
  of the permutation null was never tried.
- **Ties were rare.** 0.77% of features had a reference p in `[thr/4, 4·thr]`.
- **Against the naive full certified fixed-B, adaptive looked about 24× cheaper.** That
  comparison is a strawman. Certified fixed-B's decision is monotone in S, so it
  curtails too. Against the curtailed version the ratio is about 0.4–1.7×.
- **Adaptive's cost is certifying rejections.** An exceedance count of S=0 needs about
  18,400 draws to certify with a fixed-horizon Clopper–Pearson interval, and about
  40,000 with the Beta(1,1) mixture.

## Reading it

- **The large saving is classical curtailment:** Besag & Clifford (1991). You stop
  shuffling a feature once the fixed-B decision is determined. That gives exactly the
  fixed-B decisions for about 1/50th of the draws, and it needs no anytime machinery.
- **The fixed-B test was never "uncertified."** `(1+S)/(1+B)` is a valid p-value at any
  B, so B=1,999 gives exact family-wise control. The anytime rule certifies something
  else: agreement with the B→∞ decision, at an extra `m·ε` of error. A
  "disagreement" between them is two valid tests disagreeing, not a mistake.
- **Prior art covers the rest.** The adaptive arm is Gandy (2009). The BH/FDR extension
  has direct ancestors in MMCTest (Gandy & Hahn (verify)) and AMT (Zhang, Zou & Tse,
  2019 (verify)).

This is the fourth setup where the anytime-valid certificate did not pay for itself.
The pattern is summarized in `knowledge/shap-topk-savings.md` → "The recurring
pattern".
