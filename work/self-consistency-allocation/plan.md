# Self-consistency allocation: does the certified stopping rule pay for itself?

**Slug:** self-consistency-allocation · **Date:** 2026-10-08 · **Status:** withdrawn at plan stage (2026-10-08), at the Owner's call. Not implemented; see `## Review` and the correction in `knowledge/certificate-tax.md`.

## Goal

`knowledge/certificate-tax.md` (Exp 3) found the first setup in the project where a
per-question anytime certificate beats curtailed fixed-B: LLM self-consistency
majority vote on GSM8K, at 3–6× fewer samples than curtailed fixed-k at plateau
accuracy. It also stated the phase condition, that the certificate pays only when the
difficulty spread is wide and the threshold is central. That finding is an unreviewed
prototype, read off three sets that were then used to state the condition.

This unit turns it into a pre-registered, gated experiment that can fail. It has two
parts:

1. **Replication.** Replicate the three explored sets with fresh seeds and
   pre-registered single configs.
2. **Held-out test.** Run the same pipeline on four **held-out** sets nobody has
   looked at. A zero-draw spread statistic, calibrated only on the three explored sets,
   predicts each held-out set's verdict before its arms run.

Done means an offline `eval --selfcons` run that writes per-set and headline verdicts
to `work/self-consistency-allocation/results.{md,json}`, plus a scoped `knowledge/`
note.

The setting is regime (B) of `docs/research-definition.md` §3. The question is fixed,
and a "draw" is one LLM sample from that question's answer distribution. The estimand
is the k→∞ majority answer. The unit **reopens the research line closed 2026-09-26**,
narrowly, on this consumer. It does not re-open H1 or the in-band question.

## Detectability precondition (per the 2026-09-22 decision)

Governing cold docs, loaded at plan time: `knowledge/certificate-tax.md`,
`knowledge/anytime-valid-band.md`, `knowledge/controlled-retest-discipline.md`,
`knowledge/research-doc-citations.md` and `knowledge/permutation-test-savings.md`.
The last one supplies the lesson that any certified comparison must be against a
*curtailed* baseline.

- **(D1)** The curtailed baseline is the one that dominated in the permutation-test
  unit. Curtailment on a central threshold stops when the leader's lead exceeds the
  remaining budget. It is included at every grid k, so there is no uncurtailed
  strawman.
- **(D2)** The baseline grid contains budgets that the adaptive arms can beat. On the
  explored GSM8K sets, curtailed k=129 costs 69–79 samples against 7–42 for the
  certified rule (exploration logs). On MATH-8B it does not, and that set is the
  **pre-registered expected negative**.
- **(D3)** The held-out tier can only confirm the phase condition if at least one
  held-out set is predicted to pass. All held-out sets are MATH, because
  `monkey_business` has only two GSM8K sets and both were explored, so they may all
  predict fail. If so, the headline is `HELD_OUT_UNINFORMATIVE`, not a confirmation,
  and the result rests on replication alone. This is stated now, not discovered later.

## Approach

**Data.** `ScalingIntelligence/monkey_business` on Hugging Face has about 10k samples
per question with `is_corrects` labels.

- **Explored tier** (seen in exploration; replication only): `GSM8K_Llama-3-8B-Instruct`,
  `GSM8K_Llama-3-70B-Instruct` and `MATH_Llama-3-8B-Instruct`.
- **Held-out tier** (no one has extracted or inspected them): `MATH_Llama-3-70B-Instruct`,
  `MATH_Llama-3-8B`, `MATH_Gemma-7B` and `MATH_Gemma-2B`.
- **Excluded a priori:** the Pythia MATH sets (download cost, and k→∞ accuracy is likely
  near zero), and CodeContests and MiniF2F, which are pass/fail with no answer to vote
  on.

**Extraction.** This is offline and outside the gate. It ports `extract.py.txt`
unchanged in logic:

- GSM8K answers come from `####`, and MATH answers from the last `\boxed{}` with the
  "final answer is" fallback.
- Normalization strips commas, `$` and trailing periods, and canonicalizes integral
  floats.
- An answer key counts as correct iff a majority of its samples are labelled correct.
- `purity` is recorded per set. A set with min-question purity below 0.9 is
  **excluded from verdicts** but still reported.

The output is one derived JSON per set at `data/self-consistency/<set>.json`. Each
question gets its top-30 answer keys with counts, plus a tail count, a `None` count,
the correct-key set, n and purity. Raw downloads live outside the repo at a path
passed as an argument. They are never committed or hard-coded.

**Draw stream** (controlled-retest rule 2):

- Per set, base seed `500000 + set_index` (fresh; no earlier unit used 500000+).
- Per question, R=300 paths of `M_max=256` i.i.d. draws from the empirical answer
  distribution. `None` and tail draws consume a sample but cast no vote.
- Every arm reads prefixes of the **same** draw matrix, so arms differ only in their
  stopping policy.
- The decision at stop is the leader, with a seeded random tie-break. No votes means
  wrong.

**Arms.** One config per adaptive rule is the pre-registered headline; the others are
reported only.

1. **Fixed-k** and **curtailed-k**, with `k ∈ {1,3,5,9,17,33,65,129,255}` and a dense
   odd grid 1..255 for curtailed, used for matched-accuracy interpolation. Curtailed
   stops at the first t with `lead > k − t`. Its decisions must equal fixed-k's exactly.
2. **Certified** (headline α=0.05; α=0.2 reported). This is the leader-vs-runner-up
   truncated Beta(1,1) mixture likelihood ratio against ½ from `selfcons2.py.txt`. It
   stops when `LR ≥ 1/α`, and otherwise takes the majority at `M_max`. It sees only the
   vote counts.
3. **Adaptive-Consistency-style Bayes** (headline conf=0.95, cap=256). It stops when
   `P(p_lead > p_runner | Beta(1+a, 1+b)) ≥ conf`. Cite Aggarwal et al. (2023)
   (verify).
4. **ESC-style windowed** (headline window w=8, cap=256). It stops at the end of the
   first non-overlapping window of w samples whose valid votes are all identical (with
   at least one vote). Cite Li et al. (2024) (verify). This replaces the exploration's
   ad-hoc streak rule, because it is the published rule.

The incomplete beta functions use exact binomial tails on a precomputed log-factorial
table, since `a+b ≤ 256`. **numpy only; no scipy.** The prototype's scipy calls must
not be carried over.

**Verdicts** (pre-registered, all written, none collapsed). For each verdict-eligible
set:

- **V1, certified pays (headline per set).** Passes iff both of these hold:
  - `cost(curtailed k=129) / cost(certified α=0.05) ≥ 2`;
  - the lower 95% bound of `acc(certified) − acc(fixed k=129)` is `≥ −0.005`, using a
    question-cluster bootstrap with 2,000 resamples and a seeded generator.
- **V1-dense (secondary).** `cost(curtailed at the smallest dense k with acc ≥
  acc(certified) − 0.005) / cost(certified)`. This guards against k=129 being a
  favorable anchor. It is reported, not gating.
- **V2, certificate tax.** `cost(certified) / cost(Bayes)` and
  `cost(certified) / cost(ESC)`, each with both arms' accuracy.
- **V3, validity.** For each question, the certified arm's false-certification rate is
  measured against the k→∞ mode, over certified (non-abstain) stops. The rate is
  reported with a Wilson 95% interval. It passes iff no question's Wilson lower bound
  exceeds α. The guarantee is approximate because the leader is data-dependent, so
  this is a falsifiable check. Questions whose top-2 shares are tied in the empirical
  distribution are excluded from V3 and counted.
- **V4, phase-condition prediction.** The spread statistic is
  `U = fraction of questions with top-2 normalized leader share ≥ 0.9`. It is
  computed from counts only, with no draws.
  - The threshold θ is the midpoint between the largest U among explored V1-fail sets
    and the smallest U among explored V1-pass sets. It is fixed in code **before** any
    held-out arm runs.
  - If the explored sets do not separate (all pass, all fail, or overlap), V4 is
    `NOT_CALIBRATED`.
  - Each held-out set gets a prediction `U ≥ θ ⇒ pass`. The prediction is written to
    the results before that set's arms are evaluated.

**Headline** (one line):

- `REPLICATED` or `NOT_REPLICATED`: the explored tier matches its expected verdicts
  (GSM8K pass, MATH-8B fail).
- Then exactly one of:
  - `PHASE_CONFIRMED`: at least one held-out set was predicted to pass, and every
    held-out prediction was correct.
  - `PHASE_FALSIFIED`: any held-out prediction was wrong.
  - `HELD_OUT_UNINFORMATIVE`: no held-out set was predicted to pass, and all were
    correct.
  - `NOT_CALIBRATED`.

**Code shape.** New modules only. Released modules and released artifacts are
untouched (controlled-retest rules 1 and 3).

**Alternatives considered:**

- *EB-DP oracle arm* (suggested in `certificate-tax.md`): dropped. A per-question
  oracle that knows π_q is degenerate (0 draws), and a prior-oracle needs a multinomial
  DP, which is a separate unit.
- *Learned EB prior arm:* dropped, because the exploration showed it did not beat flat
  Bayes and collapsed to one sample on GSM8K-70B.
- *Using the explored sets for headline claims:* rejected. Their configs were picked
  while looking. They serve as replication only.

## Footprint

Files to create:
- `src/adaptive_compute/selfcons_data.py`: answer extraction and normalization, the
  per-set count builder from a raw `monkey_business` JSON, and the loader/validator for
  `data/self-consistency/*.json`.
- `src/adaptive_compute/selfcons.py`: the shared draw matrix, the four arm families,
  the binomial-tail Beta helpers, the cluster bootstrap, V1–V4 and the headline, and
  the writers for `work/self-consistency-allocation/results.{md,json}`.
- `tests/test_selfcons_data.py`, `tests/test_selfcons.py`
- `tests/fixtures/selfcons_tiny.json`: a hand-built set of about 6 questions covering
  unanimous, contested, exact-tie and all-`None` cases.
- `data/self-consistency/<set>.json` × 7: generated offline by `--selfcons-extract`.
  Each file is ≤ 1 MB and JSON (not a `ds-hygiene` data extension).
- `work/self-consistency-allocation/results.md`, `results.json`: generated.
- `knowledge/self-consistency-allocation.md`: result and scope, written from the run.

Files to modify:
- `src/adaptive_compute/eval.py`:
  - add `--selfcons` (optional `--sets` and `--reps` for small runs);
  - add `--selfcons-extract RAW_DIR`;
  - add to `_check()` a determinism replay on `tests/fixtures/selfcons_tiny.json`
    (R=20) that adds ≤ 5 s.
- `knowledge/README.md`: an index line.
- `knowledge/certificate-tax.md`: a status-line pointer to this unit.
- `docs/research-definition.md`: a status-line note that the line is reopened for this
  consumer only.

Files NOT to touch:
- `src/adaptive_compute/{benchmark,sweep,betting,adaptive,reference,equiv_probe,strata,bootstrap}.py`
  and all released `work/*/results*` artifacts.
- `work/certificate-tax-exploration/`, which is the exploration record.

## Acceptance criteria

- [ ] **Extraction.** Tests cover GSM8K `####` parsing, MATH nested-brace `\boxed{}`,
  the "final answer is" fallback, normalization (`1,000.` → `1000`, `3.0` → `3`), and
  the majority-label correct-key rule, including a key with exactly half its samples
  labelled correct, which counts as **not** correct.
- [ ] **Beta helpers are exact.** The binomial-tail `P(Beta(a+1,b+1) > ½)` matches a
  brute-force rational-arithmetic computation (`fractions.Fraction`) to 1e-12 for all
  `a+b ≤ 40`. No `scipy` import appears anywhere in `src/` (grep).
- [ ] **Curtailment equivalence.** For every set and every grid k, curtailed decisions
  equal fixed-k decisions path for path. This is asserted in the run and tested on the
  fixture, including a path where the lead equals `k − t` exactly, which must not stop.
- [ ] **Shared stream.** A test reconstructs the draw matrix for one question from its
  seed and checks that each arm's decision equals the leader of the reconstructed
  matrix's prefix at that arm's stop time. A deliberately perturbed draw after an arm's
  stop leaves that arm's decision unchanged (rule 4: the test can fail).
- [ ] **Blindness.** The stopping functions take only the vote-count arrays and their
  own parameters. They never receive correctness labels, the k→∞ mode or π. Checked
  by signature test plus diff inspection.
- [ ] **Anytime validity smoke.** On 2,000 simulated two-answer streams at leader share
  exactly ½ + 1e-9 (Ville boundary), the certified arm's false-certification rate is
  ≤ α at α=0.05. At shares 0.3 and 0.7, at least 95% certify the correct side.
- [ ] **V4 ordering.** θ is computed from the explored tier only. A test feeds a
  held-out set whose U would move θ and asserts that θ is unchanged. In
  `results.json`, each held-out prediction is recorded with its U and θ.
- [ ] **Determinism.** Two `eval --selfcons --sets GSM8K_Llama-3-8B-Instruct --reps 20`
  runs produce byte-identical `results.json`. `eval --check` passes with the fixture
  replay, and its added time is measured and recorded in the handoff.
- [ ] **All verdicts present.** `results.md` gives, for each set:
  - purity and eligibility;
  - k→∞ majority accuracy;
  - mean samples and accuracy for every arm and config;
  - V1 with its ratio and CI;
  - V1-dense, V2, V3 (with the max per-question rate, Wilson bounds, and the excluded
    tie count) and U.

  It also gives θ, the held-out predictions, and the single headline line.
- [ ] **Released artifacts untouched.**
  `git diff origin/main...wt/self-consistency-allocation -- work/adaptive-procedure work/betting-cs-retest work/equivalence-band-savings work/certificate-tax-exploration src/adaptive_compute/benchmark.py src/adaptive_compute/sweep.py src/adaptive_compute/betting.py src/adaptive_compute/adaptive.py src/adaptive_compute/reference.py src/adaptive_compute/equiv_probe.py src/adaptive_compute/strata.py src/adaptive_compute/bootstrap.py`
  is empty.
- [ ] **No hard-coded paths, sizes OK.** `ds-hygiene.sh` passes, and every
  `data/self-consistency/*.json` is ≤ 1 MB.
- [ ] **Scoped knowledge note.** `knowledge/self-consistency-allocation.md` states the
  headline and scopes any positive as *against curtailed fixed-k at k=129, on these
  models and tasks*. It puts V2 next to V1. It names Adaptive-Consistency and ESC as
  the prior-art rules being evaluated, not invented, with citations marked `(verify)`.
  It says plainly which result came from the held-out tier and which from the explored
  tier.
- [ ] `bash scripts/gate.sh` exits 0.

## Release

Release note: Add `eval --selfcons`, a pre-registered offline experiment on LLM
self-consistency sampling (`monkey_business`). It compares an anytime-certified
stopping rule against fixed, curtailed, Adaptive-Consistency-style and ESC-style
baselines, with a held-out test of the spread/phase condition.

## Verification

Offline, run by the Orchestrator after the gate is green. The raw downloads are about
5 GB, outside the repo.

- `PYTHONPATH=src python -m adaptive_compute.eval --selfcons-extract <raw_dir>`, then
  commit `data/self-consistency/*.json`.
- `PYTHONPATH=src python -m adaptive_compute.eval --selfcons`, then inspect
  `work/self-consistency-allocation/results.md`.
- `PYTHONPATH=src python -m adaptive_compute.eval --check`

## Review

**Cold plan-reviewer, rev 1: REVISE, 7 findings. The Orchestrator re-checked findings 1–2
against the exploration logs and agrees with all seven.**

1. **(Blocking) The k=129 anchor flatters the certified rule.** The GSM8K accuracy
   curves are flat long before k=129.
   - **GSM8K-70B:** curtailed k=9 reaches 0.9648 at 5.3 samples, and k=17 reaches
     0.9673 at 9.6. Certified α=0.05 reaches 0.9685 at 12.4.
   - **GSM8K-8B:** curtailed k=65 reaches 0.8715 at 40.4. Certified reaches 0.8778 at
     42.1.
   - **What the ratio depends on:** with an accuracy margin of 0.005, V1-dense is about
     0.4× (70B) and 1.3× (8B), so the certificate loses. With zero margin it is about
     2.8× and 3.6×. The "3–6×" therefore buys the last 0.1–0.3 percentage points of
     accuracy, and its size is set by the margin choice.
   - **Bayes and ESC-style rules:** flat Bayes at conf 0.95 beats curtailed only modestly
     at practical margins (70B: 5.9 samples at 0.9680, against 9.6 at 0.9673).
2. **(Blocking) The expected `REPLICATED` contradicts the data, even under the plan's own V1.**
   On GSM8K-8B at α=0.05 the ratio is 79.4/42.1 = 1.88, which is below 2.
3. **(High) The held-out tier is likely uninformative.**
   - Every held-out set is MATH.
   - θ is calibrated from three points.
   - There is no outcome for "no eligible held-out set".
4. **(High) Reopening the line needs an explicit Owner decision.**
5. **(Medium) The tie-break noise must be part of the shared, pre-drawn stream.**
6. **(Medium) The raw format and fetch step are unstated.** There is a risk of
   dependency creep and of `json.load` on files of about 0.7 GB.
7. **(Low) Gaps in the acceptance criteria:**
   - The Beta-helper test should check the full log-LR, not only the tail.
   - The JSON size cap needs a `find -size +1M` check, because `ds-hygiene` ignores
     `.json`.
   - The smoke test needs a seed and a defined pass bar.

**Orchestrator's reading.** Findings 1–2 reproduce the 2026-09-23 and 2026-09-26 pattern
at plan stage. Against a matched curtailed frontier with any practical accuracy margin,
the certificate does not pay on GSM8K either. The 3–6× in `knowledge/certificate-tax.md`
holds only at zero margin. The Owner chooses between:

- withdrawing the unit and correcting `knowledge/certificate-tax.md`, which is the
  reviewer's recommendation; or
- a narrowed replication-only unit, with V1 gated on the matched frontier and a
  justified margin.

Plan verdict: REVISE
