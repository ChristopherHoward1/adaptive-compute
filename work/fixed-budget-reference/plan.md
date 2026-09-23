# Fixed-budget reference bootstrap decision procedure

**Slug:** fixed-budget-reference · **Date:** 2026-09-19 · **Status:** released v2026.9.0

## Goal

Build the **fixed-budget reference** side of the v0 experiment
(`docs/experiment-design.md` §1–2, §6–9) as real, gate-able code: a
deterministic, seeded, draws-accounted bootstrap that turns a frozen
`(E, scores_A, scores_B, y, δ, B_ref, seed)` into a decision
`{A_better, B_better, equivalent, abstain}`, plus the synthetic generator battery
whose B→∞ `Δ` is *known by construction* so every case carries a difficulty
stratum. This is the **yardstick** the first adaptive algorithm is later judged
against — so its own correctness and reproducibility must be nailed down now, and
it wires the first real `EVAL_COMMAND` into the gate.

Done looks like: given a battery member + seed, the code emits the reference
decision and the exact number of bootstrap draws consumed; re-running the same
`(params, seed)` reproduces the draws bit-for-bit; the reference recovers each
non-`boundary` member's known-by-construction decision; and a seeded, sub-second
check runs green inside `scripts/gate.sh`.

**Explicitly NOT in this unit:** the adaptive procedure (§3), the fixed-B *sweep*
baseline and large-B accuracy ceiling (§4), and the adaptive-vs-reference metric
suite — decision-agreement, false-stop rate, savings/Pareto (§5, §7's H1 test,
§8). Those are meaningless without the system-under-test and belong to the units
after this one. This unit builds only what the reference *is* and the substrate
those later metrics will run over.

## Approach

### What gets built (the shape)

A small Python package under `src/adaptive_compute/`, numpy-backed, five focused
modules plus a CLI entry that the gate calls:

- **`metrics.py`** — the paired bounded score `M` and `Δ = M(A,·) − M(B,·)`. v0
  default AUC (secondary log-loss stubbed but not required green). AUC computed by
  the Mann–Whitney rank identity (hand-rolled, no sklearn) so the only runtime dep
  is numpy and the gate stays fast.
- **`generators.py`** — the §6 battery. Each generator is a pure function of
  `(params, rng)` returning `(scores_A, scores_B, y)` for a **frozen** eval set
  `E`. The "known" quantity is the **plug-in `Δ(E)`** — `M(A,E) − M(B,E)` computed
  once, exactly, on that frozen `E` — **not** the generator's infinite-data
  population `Δ`. This is what the B→∞ bootstrap on `E` actually recovers (up to
  O(1/n) bootstrap bias), it is exact and simulation-free for all five members via
  the same code path, and it sidesteps the fact that a closed-form population AUC
  difference does not cleanly exist for the heavy-tailed / imbalanced members.
  Generator params are chosen so `Δ(E)` lands in the intended stratum (verified,
  not assumed). Members (each a distinct premature-convergence mechanism, per §6):
  1. near-δ-boundary, 2. small-effect (well inside `[−δ,+δ]`), 3. heavy-tailed
  per-row contributions (**required**), 4. rare-event / class imbalance,
  5. easy / lopsided control.
- **`bootstrap.py`** — the paired row-resampler over `E` (resample rows with
  replacement, recompute `Δ`), in batches, with **exact draw accounting** (a draw
  = one bootstrap resample). Deterministic from a `numpy.random.SeedSequence`; the
  reference stream is `spawn`ed on a **separate branch** from any future adaptive
  stream so §2's independent-seeding invariant holds structurally, not by
  convention.
- **`reference.py`** — the fixed-budget decision: run `B_ref` draws and form a
  **percentile bootstrap interval** for `Δ` at level `1−α` (the instrument is
  named and load-bearing; percentile is the v0 default), then read off
  `{A_better, B_better, equivalent}` per §1 — above `+δ`, below `−δ`, or wholly
  within `[−δ,+δ]`. **The reference never `abstain`s:** `abstain` is a `B_max`-only
  adaptive outcome (§1) and has no meaning for a fixed-budget procedure sized so
  its interval is tight; boundary cases are handled solely by `strata.py`, not by a
  reference abstain.
  - **`B_ref` sizing (finding-1 fix — genuine, not self-referential):** MCSE of the
    reference is estimated as the **empirical sd of the `B_ref` `Δ`-estimate across
    K independent reference replications** (independent `SeedSequence` branches) —
    *not* the within-run `sample_sd/√B_ref`, which under-states error under heavy
    tails (`research-definition.md` §7) and would bake false assurance into the
    check. Hard-assert `MCSE ≤ ρ·δ` (ρ=0.1, §2) **only on the well-behaved boundary
    member**, where the estimate is trustworthy; for the heavy-tailed / rare-event
    members the across-replication MCSE is **printed as a diagnostic**, not gated.
    This lives in a pytest test, not the fast `eval --check` hook.
- **`strata.py`** — classify each case by its plug-in `Δ(E)`: `boundary` when
  `Δ(E)` is within `ρ·δ` of `±δ`, else a resolved difficulty band. `boundary` cases
  are flagged so later units never score them as false stops (§2).
- **`eval.py`** (CLI, `python -m adaptive_compute.eval`) — the `EVAL_COMMAND`
  target. A `--check` mode runs a small fixed set of seeded members at a modest
  `B_ref` and exits non-zero unless: (a) draws replay bit-for-bit under a repeated
  seed, (b) the reference recovers each non-`boundary` member's known decision, and
  (c) the `B_ref` MCSE-at-boundary bound holds. Sub-second, no plots, no network.

### Reference is not truth (carried from the design)

Every surface labels the output "what the full-budget same method concludes,"
never "the true answer" (§2). The known-by-construction `Δ` of the *generators* is
the only genuine ground truth in play, and it is used solely to (i) assign strata
and (ii) check the reference recovers the right decision away from the boundary —
never fed to the procedure itself.

### Choices worth a line

- **numpy-only, hand-rolled AUC** vs. sklearn: chosen to keep one light runtime
  dep and a fast gate; AUC-by-ranks is ~5 lines and testable against a known value.
- **`SeedSequence.spawn` branching** vs. integer-offset seeds: chosen so
  reference/adaptive stream independence is a structural guarantee, not arithmetic
  the next unit can get wrong.
- **`EVAL_COMMAND` = a seeded self-consistency check** vs. a full metric run:
  chosen because no adaptive method exists to measure yet; the check that *is*
  meaningful now is determinism + known-decision recovery. (The heavier `B_ref`
  sizing lives in pytest, not this hook.) The hook deliberately re-exercises the
  same battery pytest covers — that overlap is the `EVAL_COMMAND` *wiring*, not a
  second independent check.
- **Known decision = plug-in `Δ(E)` on the frozen set** vs. population `Δ`: chosen
  because the bootstrap recovers the plug-in value, not the infinite-data
  population value; asserting recovery against a population closed-form would be
  flaky on the imbalance / heavy-tail members and force footprint creep (finding 2).

## Footprint

Files to create:
- `src/adaptive_compute/metrics.py`
- `src/adaptive_compute/generators.py`
- `src/adaptive_compute/bootstrap.py`
- `src/adaptive_compute/reference.py`
- `src/adaptive_compute/strata.py`
- `src/adaptive_compute/eval.py`
- `scripts/gate.d/eval.sh` (runs `python -m adaptive_compute.eval --check`)
- `tests/test_metrics.py`, `tests/test_bootstrap.py`, `tests/test_reference.py`,
  `tests/test_generators.py`, `tests/test_determinism.py`

Files to modify:
- `pyproject.toml` — add `numpy` to `[project] dependencies` (first runtime dep);
  keep line-length/tool config as-is. **Gate-env note (finding 5):** the gate runs
  pytest and imports the package, so the environment must have numpy installed
  (`pip install -e .`) — otherwise this surfaces as a gate failure, not a missing
  dep. mypy is unaffected (`ignore_missing_imports = true`).
- `ARCHI.md` — Verification: set **EVAL_COMMAND** to the wired command;
  **GROUND_TRUTH_SOURCE** and **DATA_REGIME** move PROVISIONAL → resolved (the
  reference and the fixed synthetic regime now concretely exist). **EVAL_METRIC
  stays PROVISIONAL** — the decision-agreement/false-stop metric is undefined until
  the adaptive method exists. (Layout section: note the new modules.)
- `PLAN.md` — Orchestrator-owned (not modified by the implementer): Now/Next
  updated to mark this unit implementing and set Next to the **adaptive procedure
  (§3)**. Done at approval time, outside the worktree diff.

Files NOT to touch:
- `scripts/gate.sh`, `scripts/release.sh`, `config.yaml` — harness machinery. The
  eval check is added as a `gate.d/*.sh` hook, which `gate.sh` already auto-runs;
  no change to the runner itself.
- `profiles/`, `.claude/` — unchanged.

## Acceptance criteria

- [x] `python -c "import adaptive_compute.reference, adaptive_compute.generators, adaptive_compute.bootstrap, adaptive_compute.metrics, adaptive_compute.strata, adaptive_compute.eval"` succeeds.
- [x] **AUC correctness:** `test_metrics.py` asserts the hand-rolled AUC equals a
      hard-coded known value on a small fixed fixture (tolerance ≤ 1e-9).
- [x] **Determinism:** `test_determinism.py` asserts two runs with the same
      `(params, seed)` produce a bit-identical array of `Δ` draws
      (`np.array_equal`), and that reference/adaptive spawned streams differ.
- [x] **Draw accounting:** a run reporting budget `B_ref` consumed exactly `B_ref`
      resamples (asserted in `test_bootstrap.py`), and the CLI prints the count.
- [x] **Decision instrument named:** `reference.py` reads the decision off a
      percentile bootstrap interval at level `1−α`; the reference returns only
      `{A_better, B_better, equivalent}` and has no `abstain` path (asserted: the
      returned decision is never `abstain`).
- [x] **Known-decision recovery:** `test_reference.py` asserts the reference
      returns the decision implied by the **plug-in `Δ(E)`** (sign vs `±δ`) for each
      non-`boundary` battery member at the unit's `B_ref` and seed.
- [x] **`B_ref` sizing (genuine):** `test_reference.py` estimates MCSE as the sd of
      the `B_ref` `Δ`-estimate across K independent reference replications and
      asserts `≤ ρ·δ` (ρ=0.1) **on the well-behaved boundary member**; for the
      heavy-tailed and rare-event members it computes the same statistic and prints
      it as a diagnostic (no hard assert). The within-run `sample_sd/√B` estimator
      is explicitly not used.
- [x] **Strata from `Δ(E)`:** `test_generators.py` asserts each member's plug-in
      `Δ(E)` lands in the intended stratum, and that a constructed at-boundary case
      (`|Δ(E) ∓ δ| < ρ·δ`) classifies as `boundary`.
- [x] **Battery completeness:** all five §6 members present, ≥1 heavy-tailed
      (asserted by an inventory test).
- [x] **Gate wiring:** `scripts/gate.d/eval.sh` exists, runs
      `python -m adaptive_compute.eval --check`, and completes in < 5 s; `--check`
      exits non-zero if determinism, recovery, or sizing fails (verify by a
      deliberately perturbed seed in a test, not in the committed hook).
- [x] `ARCHI.md` EVAL_COMMAND is set to the wired command; GROUND_TRUTH_SOURCE and
      DATA_REGIME are resolved; EVAL_METRIC remains PROVISIONAL with a pointer to
      the adaptive unit.
- [x] `bash scripts/gate.sh` exits 0 (includes ruff, mypy, pytest, shellcheck over
      the new `eval.sh`, and the new eval hook).

## Release

Release note: Add the fixed-budget reference bootstrap decision procedure and the
adversarial synthetic generator battery (deterministic, seeded, draws-accounted;
no adaptivity) — the yardstick for the adaptive method — and wire EVAL_COMMAND
into the gate.

## Verification

- `bash scripts/gate.sh`
- `python -m adaptive_compute.eval --check` (the wired eval; also runs in the gate)
- Manual: Owner confirms the reference decision + draw count for one battery member
  is reproducible across two invocations.

## Review

Fresh cold-context read-only reviewer (stood in as a `Plan`-type subagent because
the named `plan-reviewer` agent type is unregistered in this harness build; writer
≠ reviewer preserved, read-only enforced mechanically). Verified against actual
code: `gate.sh` lines 140–142 auto-run `gate.d/*.sh` (wiring claim holds), mypy
`ignore_missing_imports` covers numpy, and §10 supports the scoping. Verdict:
**REVISE**, 5 findings. All accepted and incorporated — no disagreements to
arbitrate:

1. **`B_ref` MCSE check was self-defeating.** Gating on the within-run
   `sample_sd/√B` is exactly the estimate heavy tails under-state — false assurance
   baked into the gate. Now: MCSE = sd of the `B_ref` estimate across K independent
   reference replications; hard-assert only on the well-behaved boundary member;
   heavy-tailed/rare-event sizing printed as a diagnostic; the whole check lives in
   pytest, not the fast `eval --check` hook. *(Approach → reference.py; criteria.)*
2. **Population Δ vs plug-in Δ(E).** "Known decision" is now the plug-in `Δ(E)` on
   the frozen `E` — what the bootstrap actually recovers — computed once, exactly,
   same code path for all five members. Dropped the per-member population
   closed-forms that don't cleanly exist for heavy-tailed/imbalanced AUC. *(Approach
   → generators.py, strata.py; criteria.)*
3. **Interval instrument unnamed + invented abstain.** Named the instrument
   (percentile bootstrap interval at `1−α`); removed the reference `abstain`
   (a `B_max`-only adaptive outcome per §1) — the reference returns
   `{A_better, B_better, equivalent}` and boundary is handled purely by strata.
   *(Approach → reference.py; criteria.)*
4. **Simpler version.** Adopted: the simplification the reviewer proposed *is*
   findings 1+2 applied — plug-in `Δ(E)` recovery, and `B_ref` sizing as a
   diagnostic rather than a self-referential gate assertion. The spine
   (deterministic seeded bootstrap, exact draw accounting, `SeedSequence.spawn`
   branching, recovery) is unchanged.
5. **Minor.** Added the gate-env numpy note (`pip install -e .`) and stated the
   `eval --check`/pytest overlap is intentional wiring, not two independent checks.

Reviewer affirmed as sound: the §10 scoping (§1–2, §6–9; §3/§4/§5 excluded), the
gate-wiring mechanism, and consistency with the science docs.

Plan verdict: **REVISE → addressed.** No open items for the Owner.

---

### Code review (/3-review) — six rounds, dual APPROVE

Two independent cold reviewers per round: the `code-reviewer` (stood in as a
read-only `Plan`-type subagent, as the named agent type is unregistered in this
build; writer ≠ reviewer preserved) and Codex via `scripts/codex-review.sh`. The
code-reviewer APPROVED every round; Codex issued REQUEST CHANGES rounds 1–5 and
APPROVED round 6. Each round fixed distinct, real findings (not churn on one
issue). Two findings needed Owner arbitration; both are recorded as Decisions
below. Accepted deferrals: `deferrals.md` D1 (degenerate zero-positive resample)
and D2 (hard-member MCSE diagnostic uses the raising reference) → both routed to
the adaptive unit.

- **R1** (Codex REQUEST CHANGES / code-reviewer APPROVE): removed the silent
  point-estimate fallback (decision read strictly off the percentile interval);
  added `B_ref` sizing to `--check`; reverted an out-of-scope `-p no:capture`.
  Deferred the degenerate-resample crash (D1).
- **R2** (Codex REQUEST CHANGES / code-reviewer APPROVE): straddle-interval
  semantics → **Owner decision** (see below); widened the `heavy_tailed` margin.
- **R3** (Codex REQUEST CHANGES / code-reviewer APPROVE): `SeedSequence` branching
  → **Owner decision** (see below); non-vacuous boundary-routing test; `--check`
  recovery/sizing failure-path tests.
- **R4** (Codex REQUEST CHANGES / code-reviewer APPROVE): honest `--check` draw
  count (count the replay run; now 7040); clean `UnresolvedReferenceError` exit
  instead of a traceback.
- **R5** (Codex REQUEST CHANGES / code-reviewer APPROVE): clone the `SeedSequence`
  before spawning so a reused object replays bit-identically (round-4's hardening
  had made `spawn` mutate the caller's object). Deferred the hard-member diagnostic
  consistency issue (D2).
- **R6**: **Codex APPROVE + code-reviewer APPROVE.** Gate green (pytest 22,
  `eval --check` draws_consumed=7040, 185 shell-suite checks). Remaining findings
  all LOW/non-blocking.

**Owner decisions (arbitrated during review):**
1. *Straddle → loud error (R2).* A fixed-budget reference at a correctly-sized
   `B_ref` must resolve every non-`boundary` case cleanly; a percentile interval
   that straddles a ±δ edge is boundary-adjacent or under-sized, so it **raises
   `UnresolvedReferenceError`** rather than silently returning `equivalent`. The
   scored pipeline classifies by plug-in `Δ(E)` via strata first, so the raise is
   unreachable on scored (non-boundary) cases. Decision set `{A_better, B_better,
   equivalent}` unchanged; no `abstain`.
2. *Reference resampler always branches (R3).* `paired_bootstrap_deltas` (the
   reference resampler) **always** routes its seed through `reference_seed`
   (`spawn` branch [0]) for both `int` and `SeedSequence` inputs, making
   reference/adaptive stream independence structural; the adaptive branch [1] is
   reserved for the next unit.

Code-review verdict: APPROVE
Codex-review verdict: APPROVE
