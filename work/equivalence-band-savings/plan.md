# Equivalence-band savings: can any adaptive instrument beat fixed-B inside [−δ,δ]?

**Slug:** equivalence-band-savings · **Date:** 2026-09-21 · **Status:** approved

## Goal

After two released results (EB v2026.9.3, betting v2026.9.4), the H1 savings
negative has narrowed to **one stratum**: when the truth sits inside the
equivalence band `[−δ,δ]`, no adaptive instrument beats a well-chosen fixed-B at
≥2× median-draw savings — a small fixed-B (32/64) resolves equivalence cheaply
and *dominates* adaptive (betting median 192 draws, best savings 0.00×;
`work/betting-cs-retest/comparison.md`). PLAN.md forbids any general savings claim
until this residual is understood.

This unit turns that residual from an unexplained aggregate observation into a
**mechanism-level verdict**. The correct mechanism (H_eq), fixed after cold review:
the equivalence budget is **strongly position-dependent, not fixed**. To conclude
`equivalent`, the *whole* CS interval must lie in `[−δ,δ]`
(`sweep.decision_from_interval`, `adaptive.decision_from_bounds`), so a case at
`|Δ| = δ − ε` needs half-width ≲ `ε` and its required budget grows sharply as the
truth approaches the band edge (`knowledge/anytime-valid-band.md`). Adaptivity's
savings come from **difficulty heterogeneity** across cases. The observed homogeneity
of the current `equivalent` stratum is therefore an **artifact of the `small_effect`
generator** (signal_a 0.62 / signal_b 0.60 → `|Δ|≈0.02`, tightly clustered), not an
intrinsic property of equivalence decisions — so the released stratum gives adaptivity
nothing to exploit even though equivalence *is* position-heterogeneous in principle.

The question this unit answers: on an equivalence population with **real,
reference-resolvable position heterogeneity**, can *any* adaptive instrument beat a
single fixed-B at ≥2× while holding false-stop? Done = (A) a short **diagnostic**
confirming the natural stratum is generator-homogeneous (the low-value framing check,
kept minimal), and (B) a **decisive probe** on a deliberately heterogeneous in-band
population — but decisive *only if* the engineered "hard/shallow" cases are actually
scored (see the resolvability hazard below), with a plainly stated verdict written to
`knowledge/`. Three honest outcomes, all valid findings: **flip** (heterogeneity lets
adaptive win → the residual was a stratum-design artifact, general claim survives,
scoped to heterogeneous populations); **no-flip with scored hard cases** (adaptive
still can't win even given heterogeneity → deep negative); or **no-flip because the
hard cases are unresolvable at `B_ref=320`** (the finding is then about *reference
resolving power*, not adaptivity — a distinct and still-useful result).

## Approach

Two offline analyses, both **isolated from every released path** per
`knowledge/controlled-retest-discipline.md`: a new `eval` subcommand writing only to
`work/equivalence-band-savings/`, the frozen 5-member `BATTERY` untouched, and the
released `--run` / `--compare` artifacts never read-back-mutated or overwritten.

**Why the released §8 metric is reused (no redefinition) — and its two teeth.**
`sweep.pareto_verdict` compares adaptive's **median** draws to each **single**
fixed-B (`sweep.py:114-126`). On a homogeneous population every case needs ~the same
budget `K`, so median ≈ `K` and a fixed-B ≈ `K` matches it — a ≥2× win is
structurally impossible. On a heterogeneous population a single fixed-B must be large
enough for the *hard* cases (or its false-stop/unresolved rate spikes), while
adaptive's median sits below it — the regime the metric rewards. **But domination has
two additional teeth:** it also requires `adaptive_false_stop_rate ≤ fixed_rate` **and**
`adaptive_nondecision_rate ≤ fixed_nondecision_rates[b]` (`sweep.py:123-126`). So
heterogeneity is *necessary but not sufficient*: if the adaptive arm's `b_max` is too
small, shallow cases **abstain**, raising `adaptive_nondecision_rate` and *blocking*
domination even when the median is low. The metric is kept unchanged, but the probe
must (i) **pin `b_max` in code and assert it** (not tune it), and (ii) **report the
abstain/nondecision rate alongside savings** so a flip or no-flip is attributable.

**(A) Diagnostic — confirm the natural stratum is generator-homogeneous (minimal).**
Restrict a fresh benchmark to `equivalent`-stratum cases under both instruments and
report the `adaptive_draws` distribution (p50/p90/p99 + CV) and the difficulty margin
`δ − |Δ|`. `MemberRun` does **not** store `Δ` (`benchmark.py:45-55`), so `Δ` is
recomputed by regeneration: `metrics.delta(*generate(replace(BATTERY[member][0],
seed=run.seed)))` (the stored `seed` equals `params.seed + seed_index`,
`benchmark.py:99-100`). This is a near-circular check (the stratum is populated almost
entirely by the single `small_effect` member, so low CV is generator-guaranteed) — it
is kept small, framed only as "the natural stratum is generator-homogeneous," and
carries none of the verdict.

**(B) Decisive mixed-equivalence probe — the answer to "any instrument."** A new,
isolated equivalence population with controlled position heterogeneity: a mixture of
"deep" cases (`Δ ≈ 0`, resolve early) and "shallow" cases (`|Δ| ≈ δ − ε`, resolve
late), all provably inside `[−δ,δ]`.

*The resolvability hazard (load-bearing).* The frozen constants collide with the
design: `DEFAULT_DELTA=0.05`, `classify_delta`'s boundary band `ρ·margin=0.005`
(`strata.py:15`) means `|Δ| ≥ 0.045` is reclassified `boundary` and **dropped** from
non-boundary strata (`benchmark.py:294`); and at `DEFAULT_B_REF=320` a case near the
edge is likely `reference_unresolved` and **dropped from `scored`**
(`benchmark.py:228,233`). So the engineered hard/shallow half is exactly the half
scoring can silently discard — collapsing the probe back to deep cases and
manufacturing a *false* no-flip. The probe therefore first proves a **non-empty
"resolvable-yet-hard" region**: cases that are (a) `equivalent`-classified (not
`boundary`) *and* (b) reference-resolved at `B_ref=320`, yet (c) meaningfully harder
than the deep cases (higher required draws). The shallow tier is placed at the hardest
`|Δ|` that still clears (a)+(b) with margin, not blindly at `δ−ε`. If that region is
empty, the honest verdict is *about reference resolving power, not adaptivity*.

*Driver.* `run_benchmark`/`_run_member_seed` are `BATTERY`-bound and `generate()`
raises on an unregistered name (`generators.py:164-169`), so the probe **cannot** run
the mixed population through them. It supplies its **own per-case driver** replicating
`_run_member_seed`'s pipeline (generate → `fixed_budget_reference` →
`adaptive_decision(instrument=...)` → `fixed_b_sweep`), builds `MemberRun`s, and reuses
`_summarize_stratum` (which takes `list[MemberRun]`, `benchmark.py:227`) →
`pareto_verdict`. Both arms at pinned `b=64` and pinned `b_max` (asserted), shared
fixed-B grid, same-stream discipline. Write per-arm savings ratio,
`fixed_b_dominating_adaptive`, abstain rate, and false-stop CI; `verdict.md` carries a
**mechanically-derived** one-line headline (computed from the JSON fields, as `_compare`
does at `eval.py:307-316`), plus a **stability check**: the headline must hold across
≥2 deep:shallow mixture ratios, else a flip is a fixture-tuning artifact.

**The mixed population is a fixture, not a battery member.** Adding it to `BATTERY`
would change `run_benchmark`'s pooled strata counts and thus the released `--run`
numbers — forbidden. It lives as a new generator *function* not registered in
`BATTERY`, called directly by the probe driver; `generate()` / `BATTERY` behavior is
diff-invariant (both dispatch through the `BATTERY` literal, `generators.py:91-169`).

Alternatives considered:
- *Mutate the `small_effect` / `equivalent` battery member to inject heterogeneity* —
  rejected: changes released `--run` classification counts, violates controlled-retest
  discipline (never mutate a released path).
- *Prose framing only, no probe* — rejected: cannot answer "can **any** adaptive
  instrument beat fixed-B" without actually testing a heterogeneous population; the
  diagnostic alone only explains the *current* stratum.
- *Redefine §8 to a mean/worst-case-matched savings metric* — rejected: the
  median-vs-single-fixed-B metric already rewards heterogeneity (subject to its
  nondecision tooth, handled by pinning `b_max`), and changing the released gate
  mid-question would confound the attribution.
- *Place the shallow tier blindly at `|Δ| ≈ δ − ε`* — rejected: those cases are
  reclassified `boundary` or left reference-unresolved at `B_ref=320` and silently
  dropped, manufacturing a false no-flip (the resolvability hazard). The shallow tier
  is placed at the hardest reference-resolvable, `equivalent`-classified `|Δ|`.

## Footprint

Files to add:
- `src/adaptive_compute/generators.py` — a **new** `mixed_equivalence` generator
  *function* (deep `Δ≈0` + shallow, hardest-reference-resolvable `|Δ|` mixture inside
  `[−δ,δ]`, parameterized by deep:shallow ratio and seed), **not** added to the
  `BATTERY` mapping. `generate()` and `BATTERY` stay diff-invariant.
- `src/adaptive_compute/equiv_probe.py` — the probe module: its **own per-case
  driver** replicating `_run_member_seed`'s pipeline (generate →
  `fixed_budget_reference` → `adaptive_decision(instrument=…)` → `fixed_b_sweep` →
  build `MemberRun`), a **resolvability precheck** (proves the resolvable-yet-hard
  region is non-empty before scoring), pinned `b=64`/`b_max` constants, the diagnostic
  (A) over the frozen battery's `equivalent` cases with `Δ` recomputed by regeneration,
  and the two-arm probe (B) reusing `_summarize_stratum` + `pareto_verdict`. Emits the
  mechanically-derived headline.
- `tests/test_equiv_probe.py` — guard-tests that can fail: (i) the mixed population's
  per-case `|Δ|` spread ≥ an explicit threshold (fails if homogeneous) **and** all
  `|Δ| < δ` (fails on band leak); (ii) the resolvable-yet-hard region is non-empty and
  its shallow tier needs strictly more reference draws than the deep tier; (iii) probe
  determinism (int-seed replay); (iv) the probe calls `pareto_verdict` / does not
  reimplement savings; (v) `b_max` is the pinned constant in both arms.
- `work/equivalence-band-savings/diagnostic.md`, `probe-eb.json`, `probe-betting.json`,
  `verdict.md` — generated by `eval --equiv-probe`.
- `knowledge/equivalence-band-savings.md` — the corrected mechanism (equivalence budget
  is position-dependent; natural stratum homogeneity is a generator artifact), the
  diagnostic result, and the recorded verdict (incl. the reference-resolving-power
  branch); cross-linked from `anytime-valid-band.md`.

Files to modify:
- `src/adaptive_compute/eval.py` — add the `--equiv-probe` subcommand (delegates to
  `equiv_probe.py`) + a light `--check` determinism assertion for it. `--run` /
  `--compare` behavior unchanged.
- `knowledge/anytime-valid-band.md` — one cross-reference line to the new doc.

Files NOT to touch (live hazard — released baselines / controlled-experiment constants):
- `src/adaptive_compute/generators.py` **`BATTERY` mapping** — the frozen 5 members
  and their params/seeds are the released baseline; adding a member changes released
  `--run` counts. (Adding an *unregistered* function is fine.)
- `src/adaptive_compute/benchmark.py` released constants, `sweep.py`, `reference.py`,
  `metrics.py`, `bootstrap.py`, `adaptive.py`, `betting.py`, `strata.py` — the
  reference labels, instruments, stream/seed semantics, and §8 metric are fixed.
- `work/adaptive-procedure/results.*`, `work/betting-cs-retest/results-*.*`,
  `comparison.md` — released artifacts, never rewritten.

## Acceptance criteria

- [ ] **Resolvable-yet-hard region proven non-empty (precheck, load-bearing):** the probe
  asserts the mixed population contains cases that are `equivalent`-classified (not
  `boundary`) **and** reference-resolved at `B_ref=320`, whose shallow tier requires
  strictly more reference draws than the deep tier. If empty, `verdict.md` says so and
  frames the finding as reference-resolving-power, not adaptivity. `test_equiv_probe.py`
  guards non-emptiness with a test that can fail.
- [ ] **Mixed fixture is verifiably heterogeneous and in-band:** `test_equiv_probe.py`
  asserts per-case `|Δ|` spread ≥ an explicit threshold (fails if homogeneous) **and**
  all `|Δ| < δ` (fails on band leak) — perturb/reconstruct, never self-compare.
- [ ] **Diagnostic (A):** `diagnostic.md` reports, for the frozen battery's `equivalent`
  stratum under both instruments, the `adaptive_draws` distribution (p50/p90/p99 + CV)
  and `δ − |Δ|` (Δ recomputed by regeneration), framed as "the natural stratum is
  generator-homogeneous"; deterministic on int-seed replay.
- [ ] **Probe (B) pins the adaptive knobs in code:** both arms use `b=64` and a **pinned
  `b_max` constant** (asserted equal in code, not tuned); `probe-eb.json` /
  `probe-betting.json` carry each arm's `pareto_best_savings_ratio`,
  `fixed_b_dominating_adaptive`, **abstain/nondecision rate**, false-stop count + CI, and
  draw percentiles, scored via `_summarize_stratum` → `pareto_verdict` on the shared
  fixed-B grid.
- [ ] **Verdict is mechanically derived and stability-checked:** `verdict.md`'s one-line
  headline (does any adaptive instrument dominate a single fixed-B at ≥2× while the
  false-stop upper CI ≤ α, on the heterogeneous population?) is computed from the JSON
  fields — not hand-written — and holds across ≥2 deep:shallow mixture ratios (a
  ratio-sensitive flip is reported as a fixture-tuning artifact, not a win).
- [ ] **Reuses released savings logic:** `git diff` shows the probe calls
  `sweep.pareto_verdict` / `fixed_b_sweep` and `benchmark._summarize_stratum`; no
  reimplemented Pareto/savings arithmetic.
- [ ] **Released paths untouched:** `git diff` shows `generators.BATTERY` unchanged
  (still exactly 5 members), `benchmark.py` released constants unchanged, and
  `work/adaptive-procedure/`, `work/betting-cs-retest/` artifacts unchanged (empty diff).
- [ ] `eval --check` gains a light `--equiv-probe` determinism assertion;
  `bash scripts/gate.sh` exits 0.
- [ ] `knowledge/equivalence-band-savings.md` records the corrected mechanism, the
  diagnostic finding, and the verdict (incl. the reference-resolving-power branch),
  claiming nothing beyond what the artifacts show; `anytime-valid-band.md` cross-links it.

## Release

Release note: Add an offline equivalence-band probe (`eval --equiv-probe`) that
diagnoses difficulty heterogeneity in the `equivalent` stratum and tests, on a
deliberately heterogeneous in-band population under both adaptive instruments, whether
any adaptive instrument beats a single fixed-B at ≥2× — resolving whether the residual
H1 savings negative is structural to equivalence-at-fixed-δ or a synthetic-stratum
artifact.

## Verification

- `bash scripts/gate.sh` (shellcheck + ruff + ruff format + mypy + pytest + `gate.d/`
  hooks incl. `eval --check`).
- `python -m adaptive_compute.eval --equiv-probe` then read
  `work/equivalence-band-savings/verdict.md` — confirm both arms populated, the mixed
  population's heterogeneity reported, and the headline verdict present and consistent
  with `probe-eb.json` / `probe-betting.json`.
- `git diff --stat` confirms `work/adaptive-procedure/` and `work/betting-cs-retest/`
  artifacts and `BATTERY` are untouched.

## Out of scope (follow-on decisions, not this unit)

- If the probe *flips* (heterogeneity lets adaptive win), whether to promote a
  heterogeneous-equivalence member into the frozen battery and re-open the general
  savings claim — a separate `/1-plan` unit and an Owner decision.
- Any change to the released §8 metric or the frozen battery.

## Review

Cold `plan-reviewer` (fresh read-only Opus subagent, code-verified) — verdict
**REVISE**, 5 must-fix + 4 optional. All accepted and applied; no disagreements to
route to the Owner.

1. **H_eq was factually backwards.** Equivalence needs the whole interval inside
   `[−δ,δ]`, so budget is *position-dependent* (grows toward the edge), not a fixed
   target; the natural stratum's homogeneity is a `small_effect`-generator artifact.
   **Applied:** Goal/Approach rewritten around the corrected mechanism.
2. **Resolvability confound would manufacture a false null** — shallow cases get
   reclassified `boundary` or left reference-unresolved at `B_ref=320` and dropped from
   `scored`. **Applied:** added a non-empty "resolvable-yet-hard" precheck + acceptance
   criterion + guard-test; shallow tier placed at the hardest reference-resolvable
   `|Δ|`; a reference-resolving-power branch added to the verdict.
3. **Verdict tunable via `b_max` and mixture ratio** (`pareto_verdict`'s nondecision
   tooth fights heterogeneity). **Applied:** `b_max` pinned in code + asserted, abstain
   rate reported, headline required stable across ≥2 mixture ratios.
4. **Can't reuse `run_benchmark`/`_run_member_seed`** (BATTERY-bound; `generate()`
   raises on unregistered name). **Applied:** probe supplies its own per-case driver in
   a new `equiv_probe.py`, reuses `_summarize_stratum` + `pareto_verdict`.
5. **`MemberRun` doesn't store `Δ`.** **Applied:** diagnostic recomputes `Δ` by
   regeneration; footprint corrected.
6–7. Diagnostic reframed as a minimal "natural stratum is generator-homogeneous" check
   (near-circular, carries none of the verdict); headline made mechanically-derived and
   asserted.

Plan verdict: **APPROVE** (post-revision)
