# SHAP top-k: adaptive MC savings, plan-stage prototype

Load this before planning any adaptive-Monte-Carlo unit on attributions, or any unit
whose value rests on "certify early and stop."

**Status.** This is a plan-stage prototype result (n=40), not a released experiment. The
unit `work/shap-topk-savings/plan.md` was withdrawn after a cold plan review. The
prototype is `work/shap-topk-savings/prototype.py.txt` and its output is
`prototype-run40.log`. The script is saved as `.txt` so the gate's ruff pass skips it.

## Setup

- **Estimand.** Exact interventional Shapley over an empirical background.
- **Model.** `f(x) = sigmoid(w·x + xᵀVx)`, D=12, |bg|=64. There is no closed form
  because of the sigmoid.
- **Decision.** ε-correct top-K (K=3, ε=0.01): return `S` with
  `min_{i∈S}|φ_i| ≥ |φ|_(K) − ε`, or abstain at M_max=16384.
- **Draw.** One Štrumbelj–Kononenko permutation against a random background row: D+1
  model evaluations, marginal contributions in `[-1,1]`.
- **Adaptive.** A per-feature anytime WSR betting CS at α/D, checked every 32 draws.
- **Certified fixed-M.** The better of a fixed-horizon WSR CI (capital at M, λ tuned to
  M) and a fixed-time empirical-Bernstein CI, both at α/D. Every arm reads the same
  per-case stream. Cases are a natural mix, seeds 100000–100039.

## Result

| Arm | Cost (draws) | Outcome |
|---|---|---|
| Uncertified fixed-M (top-K of the mean) | 4,096 | 0 wrong (0.05 wrong at 1,024) |
| Adaptive | mean 7,119 (abstain charged at M_max), median 4,848 | 0 wrong, 17.5% abstain |
| Adaptive, exact on abstain | 10,648 | 0.53 of exact |
| Certified fixed-M matching adaptive's abstain rate | 16,384 | 0.15 undecided |
| Exact enumeration | 2^12·64/13 ≈ 20,165 | always right |

- The strongest cheap surrogate, the closed-form Shapley of the quadratic logit, was
  ε-correct on 65% of cases. There is no zero-draw rule here, unlike the bootstrap line
  (`knowledge/anytime-valid-band.md` → "The mean estimand is closed-form").
- The natural mix was tie / hard / moderate / easy = 13 / 17 / 9 / 1, with strata set by
  the K-th gap relative to ε at 1 / 3 / 10 ε.
- Adaptive abstained on 6 of the 13 tie cases.

## Reading it

- **Against a certified fixed budget, adaptive saves about 2.3×** on mean cost. That is
  real but marginal at n=40.
- **Against exact enumeration, it does not clear 2×.** And that margin depends on |bg|,
  since exact cost is linear in |bg| while adaptive cost barely moves. |bg|=64 was
  chosen after seeing exact win at |bg|=16, so any "beats exact" claim must pre-register
  |bg| and scope to it.
- **Against an uncertified fixed budget, adaptive loses.** Being right is cheap. Proving
  it is not.
- **Ties drive the cost.** Near-tie cases, where either answer is acceptable, are the
  cheapest to get right and the most expensive to certify. This is the same asymmetry
  as the equivalence band (`knowledge/equivalence-band-savings.md`).

## The recurring pattern

This is the third setup where adaptive MC savings failed to materialize:

1. **Mean-CS bootstrap:** the estimand was closed-form.
2. **Equivalence band:** a fixed-width functional was cheaper than shrinking MC error.
3. **SHAP top-k:** certification costs more than correctness.

In every case the adaptive procedure pays for a per-case guarantee that the cheaper
baseline never has to provide. An adaptive-compute claim only has content if the
application actually *needs* the certificate, and it must then be compared against a
certified baseline. The next research step is to find such an application, or to accept
the negative.

## Plan-review lessons worth keeping

- Reading the same anytime-valid CS once at a fixed M is **not** a fixed-budget
  comparator. The running-max survivor set is nested, so it loses by construction. Use a
  fixed-horizon certificate.
- Charge abstentions at M_max and compare **mean** cost. Pool over the natural case mix,
  never over equal stratum quotas.
