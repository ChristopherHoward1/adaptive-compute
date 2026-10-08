# The certificate tax: adaptivity pays, the per-case certificate eats it

Load this before planning any adaptive-compute unit, especially one that would reopen the
line closed on 2026-09-26, or any unit on LLM test-time compute (self-consistency, best-of-n).

**Status.** These are exploratory prototypes (2026-10-07), not released experiments, and no
plan-reviewer has seen them. The scripts and logs are in `work/certificate-tax-exploration/`. The
scripts are saved as `.py.txt` so the gate skips them.

**Correction (2026-10-08).** A plan-reviewer checked the GSM8K self-consistency "positive"
below. It holds only at **zero accuracy margin** against curtailed fixed-k. With any
practical margin, the certificate does not pay on GSM8K either (Exp 3, "Matched-frontier
check"). So all five setups now fit the same pattern. The promotion unit
`work/self-consistency-allocation/plan.md` was withdrawn at plan stage.

## The question

All four closed setups had the same shape: "certifying costs more than being right"
(`knowledge/shap-topk-savings.md` → "The recurring pattern"). That leaves two readings:

1. Adaptive allocation has little to gain at all.
2. Adaptive allocation gains a lot, and the per-case anytime certificate spends that gain.

The setups could not tell these apart, because each one compared certified adaptive rules
with fixed or curtailed baselines. These prototypes add the missing arm: the **Bayes-optimal
sequential rule**. It is an upper bound on what any adaptive rule can save under a known
difficulty prior.

## Exp 1: oracle frontier on a Bernoulli threshold decision

- **Setup** (`frontier*.py.txt`). The decision is whether `p > c`, scored against the true
  side. The difficulty prior is `logit p = logit c + Laplace(0, τ)`, where a larger τ means a
  wider spread of difficulty.
- **Arms.** Fixed-B; curtailed fixed-B (Besag–Clifford); a certified anytime rule (a one-sided
  truncated Beta(1,1) mixture likelihood ratio, α split across the two sides, majority vote at
  `M_max`); and a Bayes-oracle dynamic program that minimizes `E[n] + L·P(err)`, swept over L.
- **Comparison.** Costs are compared at matched error, interpolated in log-log
  (`summ.py.txt`).

| c | τ | oracle vs curtailed fixed-B, at matched error | certified vs curtailed |
|---|---|---|---|
| 0.5 | 0.5 | 1.3–2.6× | 0.70–1.17× |
| 0.5 | 1 | 1.2–3.7× | 0.78–0.99× |
| 0.5 | 2 | 1.3–5.8× | 0.58–0.94× |
| 0.1 | 0.5 | 1.1–2.8× | 0.84–0.98× |
| 0.1 | 1 | 1.0–4.0× | 0.67–1.55× |
| 0.1 | 2 | 1.0–6.1× | 0.57–0.82× |
| 0.01 | 0.5 | 1.0–2.5× | not comparable (certified error is below the fixed-B floor) |
| 0.01 | 1 | 1.0–3.5× | 0.72–0.89× |
| 0.01 | 2 | 1.0–5.2× | 0.56–0.81× |

(The oracle's ratio rises as the target error falls. The oracle is capped at `N_max` (600, 2,000
and 12,000 for c = 0.5, 0.1 and 0.01), which only understates it. The threshold c barely matters
under this symmetric prior. Curtailment's large win in the permutation-test prototype came from
null cases sitting far from the threshold, a prior shape this grid does not include.)

**Reading.** Adaptivity is worth 2–6× over curtailed fixed-B, and more as the spread of
difficulty widens. The certified rule lands at 0.6–1.6× of curtailed fixed-B, roughly even. **The
certificate consumes essentially the whole adaptive gain.** This is reading 2. The closed
line's negative was about the certificate, not about adaptivity.

The tax has a back-of-envelope form. Gaussian increments with gap d need `z_α²σ²/d²` draws for
a fixed-horizon test, against about `2σ²·log(1/α)/d²` (plus an iterated-log term) for an
anytime boundary. The ratio `2·log(1/α)/z_α²` is about 2.2× at α=0.05 and about 1.3× at
α=1e-4. Tie cases add on top of that: the certified rule abstains on 4–25% of cases in the
table, running each one to `M_max`, while the oracle gives up on them early.

## Exp 5: the oracle is reachable without knowing the prior (empirical Bayes)

`ebayes.py.txt`, run at c=0.5, τ=1. The batch has m=400 cases. Each gets a 10-draw pilot, the
prior is fitted by NPMLE (EM on a grid) across the batch, and the DP then runs with the fitted
prior.

| L | oracle n / err | EB n / err | curtailed fixed-B (n / err) |
|---|---|---|---|
| 1,000 | 42.7 / 0.070 | 45.7 / 0.072 | 95.7 / 0.080 (B=127) |
| 3,000 | 79.8 / 0.045 | 80.8 / 0.048 | 192.1 / 0.052 (B=255) |
| 10,000 | 116.3 / 0.043 | 119.6 / 0.043 | 384.6 / 0.040 (B=511) |

EB comes within 1–7% of the oracle's cost. What it gives up is *per-case* error control. It
controls the average error across the batch instead, which is the Bayes-risk or local
false-sign-rate kind of guarantee. **In batch settings the 2–6× gain is available, provided the
application can accept average-case error control.** None of the four closed setups needed
per-case control, so this is the arm they were missing.

## Exp 3: LLM self-consistency, on real samples

- **Data.** `ScalingIntelligence/monkey_business` on Hugging Face: about 10k samples per
  question with `is_corrects` labels. Three sets were used: GSM8K with Llama-3-8B-Instruct and
  with Llama-3-70B-Instruct (127 questions each), and MATH with Llama-3-8B-Instruct (128
  questions).
- **Answer extraction** (`extract.py.txt`). The extracted answer key agrees with the
  correctness labels at a purity of at least 0.9993 on GSM8K and at least 0.918 on MATH.
- **Draws.** Each question's 10k samples are taken as its answer distribution, and policies
  draw i.i.d. from it (R=300 repetitions, `M_max`=256).
- **Decision.** Majority vote, which is the central-threshold case (c=½ between leader and
  runner-up).

Results are mean samples per question at the stated accuracy
(`selfcons2.py.txt`). The k→∞ majority is the accuracy ceiling.

| | GSM8K 70B | GSM8K 8B | MATH 8B |
|---|---|---|---|
| k→∞ majority accuracy | 0.9685 | 0.8819 | 0.4297 |
| fixed k=129 | 129 / 0.9685 | 129 / 0.8746 | 129 / 0.4207 |
| curtailed k=129 | 69 / 0.9685 | 79 / 0.8748 | 112 / 0.4204 |
| certified α=0.2 (anytime) | **7.2** / 0.9681 | **30.5** / 0.8775 | 140 / 0.4237 |
| Bayes, flat prior, conf 0.95, cap 256 | **5.9** / 0.9680 | **20.9** / 0.8765 | 111 / 0.4234 |
| streak of 3 identical answers, else curtailed k=33 | 5.6 / 0.9674 | 11.2 / 0.8673 | 27 / 0.4017 |

- **~~On GSM8K the certificate pays for itself~~: superseded (2026-10-08).** The 3–6× was
  measured against curtailed k=129. The GSM8K accuracy curves are flat long before that
  point, so the 3–6× mostly buys the last 0.1–0.3 points of accuracy.
- **Matched-frontier check.** These figures compare the certified rule at α=0.05 with the
  smallest curtailed k that reaches its accuracy minus a margin (from the logs).
  - **At margin 0.005**, the certified rule loses on GSM8K-70B and gives only a small
    saving on GSM8K-8B:
    - On GSM8K-70B the ratio is about **0.4×**. Curtailed k=9 reaches 0.9648 at 5.3
      samples, against 0.9685 at 12.4 for the certified rule.
    - On GSM8K-8B the ratio is about **1.3×**. Curtailed k=65 reaches 0.8715 at 40.4
      samples, against 0.8778 at 42.1 for the certified rule.
  - **At zero margin**, the ratios are 2.8× and 3.6×.
  - **The margin decides the verdict.** The certificate pays only if the user values
    tenths of an accuracy point at several times the compute.
- **The uncertified rules do somewhat better.** Flat Bayes at conf 0.95 and the streak/ESC
  rule beat curtailed fixed-k modestly at practical margins. For example, on GSM8K-70B
  flat Bayes reaches 0.9680 at 5.9 samples, against 0.9673 at 9.6 for curtailed k=17.
  This fits the tax reading: the adaptive gain is real but small, and the certificate eats
  it.
- **On MATH there is little to gain** (1.1–1.9×). Answers are dispersed on most questions, so
  nearly every question is a near-tie: no difficulty spread, no gain. This matches the τ
  trend in Exp 1.
- **Validity held** (`certcheck.py.txt`, R=1000). The certified rule tests a data-dependent
  leader, so its guarantee is only approximate. Even so, across about 300k certified stops no
  question's false-certification rate exceeded α: the worst was 0.121 at α=0.2 and 0.032 at
  α=0.05.
- **A learned prior did not beat the flat Bayes rule.** The empirical-Bayes prior over the
  top-2 share, fitted leave-one-out across questions, was no better. On GSM8K-70B at confidence
  0.9 the learned prior is so concentrated on unanimity that it stops after a single sample.
- **Mode agreement is not accuracy.** On MATH, raising agreement with the k→∞ mode from 0.78
  to 0.89 buys only 0.012 accuracy, because the mode is wrong on 57% of questions. A rule that
  certifies the mode spends compute on a target the user does not care about.
- **Prior art (verify before citing).** Adaptive-Consistency (Aggarwal et al., 2023) and
  Early-Stopping Self-Consistency (Li et al., 2024) propose Bayesian and windowed stopping for
  this setting. The contribution would therefore be the frame: the oracle bound, the tax, and
  the phase condition. It would not be a new rule.

## The condition, stated once

An adaptive rule beats curtailed fixed-B materially only when two things hold. First, the
cases' difficulty, measured as `1/gap²`, must be spread widely. Second, the threshold must
sit where curtailment cannot exploit it: a central threshold, or cases whose bulk lies near
it. A per-case anytime certificate then costs about `2·log(1/α)/z_α²`, plus abstentions on
ties. It pays only if the spread gain exceeds that.

- **Bootstrap mean CS:** a closed form existed. The certificate does not even arise.
- **Equivalence band, SHAP ties:** the cases were ties-dominated, so there was no spread.
- **Permutation tests:** the bulk sat far from the threshold, so curtailment already captured
  the gain.
- **GSM8K self-consistency:** central threshold and huge spread, but the accuracy curve
  plateaus within about 10–20 samples. Curtailed fixed-k at a matched practical margin is
  already cheap, so the certificate does not pay (2026-10-08 correction).

## If the line is ever reopened

The self-consistency unit sketched below was planned and **withdrawn at plan stage
(2026-10-08)**; see `work/self-consistency-allocation/plan.md` → Review. Any successor must
gate on the matched curtailed frontier with a margin fixed and justified in advance, never
on a fixed-k anchor. The original sketch follows.

The candidate unit is **self-consistency compute allocation**. Pre-register the arms: fixed-k,
curtailed-k, certified, flat-Bayes, streak (Exp 3), plus the EB-DP oracle bound. Pre-register
the data and the 2× criterion. Test on more than one model and task. The detectability
precondition is met on GSM8K: the curtailed grid contains budgets the adaptive rules beat. It
is **not** met on MATH-8B, so report that one as the expected negative. Cite
Adaptive-Consistency and ESC as the rules being evaluated, not invented.
