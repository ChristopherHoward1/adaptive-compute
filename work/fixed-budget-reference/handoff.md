You are the implementer for this work unit. Read AGENTS.md in the repo root first — it is your contract.
Follow its build-discipline section while staying inside the plan footprint.

Work unit: work/fixed-budget-reference/plan.md  (read it in full; it is your source of truth)
Branch: wt/fixed-budget-reference (already checked out in this worktree — verify with `git branch --show-current` before changing anything)

This unit implements the FIXED-BUDGET REFERENCE side of the v0 experiment defined in
`docs/experiment-design.md` §1–2 and §6–9. Read those sections; they are the spec the
plan condenses. There is NO adaptivity in this unit (§3), NO fixed-B sweep baseline (§4),
and NO adaptive-vs-reference metric suite (§5). Build only the reference + generators +
harness.

Footprint (from the plan, repeated here as the hard boundary):

Create:
- src/adaptive_compute/metrics.py     — paired bounded score M and Δ = M(A,·) − M(B,·); AUC via the Mann–Whitney rank identity (hand-rolled, numpy only, no sklearn).
- src/adaptive_compute/generators.py  — the §6 battery (5 members: near-δ-boundary, small-effect, heavy-tailed [required], rare-event/imbalance, easy/lopsided). Each is a pure fn of (params, rng) → (scores_A, scores_B, y) on a FROZEN eval set E.
- src/adaptive_compute/bootstrap.py   — paired row-resampler over E (resample rows with replacement, recompute Δ) in batches, with EXACT draw accounting (1 draw = 1 resample). Deterministic from numpy.random.SeedSequence; the reference stream is .spawn()'d on a SEPARATE branch from any future adaptive stream.
- src/adaptive_compute/reference.py   — fixed-budget decision at B_ref; see the four load-bearing constraints below.
- src/adaptive_compute/strata.py      — classify each case by its plug-in Δ(E): `boundary` when |Δ(E) ∓ δ| < ρ·δ, else a resolved difficulty band.
- src/adaptive_compute/eval.py        — CLI `python -m adaptive_compute.eval`; `--check` mode = the EVAL_COMMAND (see below).
- scripts/gate.d/eval.sh              — runs `python -m adaptive_compute.eval --check`. Must be shellcheck-clean (`set -uo pipefail`, `cd "$(git rev-parse --show-toplevel)"`), match the style of the other gate.d/*.sh hooks.
- tests/test_metrics.py, tests/test_bootstrap.py, tests/test_reference.py, tests/test_generators.py, tests/test_determinism.py

Modify:
- pyproject.toml — add numpy to [project] dependencies (first runtime dep). Keep line-length/tool config as-is. Ensure the package still installs and imports.
- ARCHI.md — Verification section: set EVAL_COMMAND to the wired command; move GROUND_TRUTH_SOURCE and DATA_REGIME from PROVISIONAL → resolved; LEAVE EVAL_METRIC PROVISIONAL (with a pointer noting the adaptive unit resolves it). Add the new modules to the Layout section.
- PLAN.md — do NOT edit; the Orchestrator owns it. (Listed in the plan footprint but the Orchestrator has already updated it.)

Do NOT touch: scripts/gate.sh, scripts/release.sh, config.yaml, profiles/, .claude/. The eval check is a gate.d/*.sh hook; gate.sh already auto-runs those — do not modify the runner.

KEY CONSTRAINTS (these are the load-bearing decisions from plan review — get them exactly right):

1. KNOWN DECISION = PLUG-IN Δ(E), NOT POPULATION Δ. The "known" quantity for every
   generator member is the plug-in Δ(E) = M(A,E) − M(B,E) computed ONCE, exactly, on the
   frozen E — this is what the B→∞ bootstrap recovers. Do NOT derive or assert any
   infinite-data population closed-form for AUC (it does not cleanly exist for the
   heavy-tailed / imbalanced members). Strata AND the "expected decision" both come from
   this single exact Δ(E). Same code path for all five members.

2. B_ref SIZING = GENUINE ACROSS-REPLICATION MCSE, NOT within-run sd/√B. Estimate the
   reference's MCSE as the empirical standard deviation of the B_ref Δ-estimate across K
   INDEPENDENT reference replications (independent SeedSequence branches). Do NOT use the
   within-run sample_sd/√B_ref — heavy tails under-state it and that would bake false
   assurance into the check. HARD-ASSERT MCSE ≤ ρ·δ (ρ=0.1) ONLY on the well-behaved
   boundary member. For the heavy-tailed and rare-event members, compute the same
   statistic and PRINT it as a diagnostic (no assert). This sizing lives in
   tests/test_reference.py (pytest), NOT in the fast eval.py --check hook. Keep B_ref and K
   modest so pytest stays fast (target the whole suite well under a few seconds).

3. DECISION INSTRUMENT NAMED; REFERENCE NEVER ABSTAINS. reference.py forms a PERCENTILE
   bootstrap interval for Δ at level 1−α, then returns exactly one of
   {A_better, B_better, equivalent} by whether that interval sits above +δ, below −δ, or
   wholly within [−δ,+δ]. There is NO `abstain` outcome for the reference (abstain is a
   B_max-only adaptive outcome per §1). Boundary cases are handled by strata.py, never by a
   reference abstain.

4. EVAL_COMMAND (`python -m adaptive_compute.eval --check`) is a seeded self-consistency
   check: it must exit non-zero unless (a) the Δ-draws replay bit-for-bit under a repeated
   (params, seed) — use np.array_equal — and (b) the reference recovers the plug-in-Δ(E)
   decision for each NON-boundary battery member at the unit's B_ref and seed. It must be
   sub-second, no plots, no network. The overlap with pytest is intentional (this is the
   EVAL_COMMAND wiring), so keep it self-contained.

Determinism is non-negotiable: every run reproducible from (generator params, seed);
record/return them. Report the exact number of draws consumed. numpy is the only runtime
dep; hand-roll AUC (no sklearn/scipy).

When done:
1. Run scripts/gate.sh from the repo root — it must pass (ruff check, ruff format --check, mypy src, pytest, shellcheck over the new eval.sh, and your new gate.d/eval.sh hook). Ensure numpy is installed in the env (`pip install -e .` if needed) so imports + pytest succeed.
2. Commit your work on this branch with a clear message.
3. Print a final summary: what changed and why, which acceptance criteria are met, and any out-of-scope observations. If you find you cannot stay within the footprint, STOP and report the footprint conflict rather than expanding scope.
