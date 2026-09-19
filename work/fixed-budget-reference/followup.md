You are resuming as the implementer for work/fixed-budget-reference/plan.md, in the SAME worktree on branch wt/fixed-budget-reference. The gate passed, but independent review (round 1) raised findings you must address. Read work/fixed-budget-reference/plan.md and work/fixed-budget-reference/deferrals.md first.

Stay inside the plan footprint. Re-run scripts/gate.sh until green, commit, and print an updated summary. If any item cannot be fixed within the plan's scope, STOP and explain rather than working around it.

## Must fix

**1. (HIGH) `src/adaptive_compute/reference.py` — the reference decision must be read off the percentile interval, not a silent point-estimate fallback.**
`_decision_from_interval` currently falls back to `decision_from_delta(estimate, margin)` (the point estimate `np.mean(deltas)`) whenever the percentile interval straddles a δ edge. The plan makes the percentile interval load-bearing: the decision is `A_better` iff the interval lies wholly above `+δ`, `B_better` iff wholly below `−δ`, `equivalent` iff wholly within `[−δ, +δ]`. The reference has NO abstain, so the remaining case — the interval straddles a δ edge (neither wholly outside nor wholly inside) — needs an EXPLICIT, documented, plan-consistent rule, not a point-estimate fallback that can report `A_better`/`B_better` from an interval that does not clear δ.
- Remove the point-estimate fallback from the interval-based path.
- Define the straddle case explicitly. A defensible, plan-consistent rule: an interval that cannot be placed wholly above `+δ` or wholly below `−δ` has not resolved a directional call, so it resolves to `equivalent` (it fails to exclude the equivalence band). Choose and DOCUMENT the rule in a comment/docstring; it must still return one of `{A_better, B_better, equivalent}` and never abstain.
- Add a test (in `tests/test_reference.py`) that constructs a case whose percentile interval straddles a δ edge and asserts the documented outcome — so the behavior is pinned, not incidental.
- Non-boundary known-decision recovery (existing test) MUST still pass unchanged.

**2. (HIGH) `src/adaptive_compute/eval.py` — `--check` must also verify B_ref sizing, per the plan's gate-wiring criterion.**
`--check` currently verifies bit-for-bit replay and non-boundary recovery, but not sizing. Add a cheap across-independent-replication MCSE check on the well-behaved boundary member ONLY: spawn a small number K of independent `SeedSequence` branches (e.g. K=8), take `np.std(estimate, ddof=1)` of the per-replication B_ref Δ-estimate, and exit non-zero if it exceeds `ρ·δ` (ρ=0.1). Use the SAME genuine estimator as the pytest sizing test (NOT within-run `sd/√B`). Keep `--check` fast (sub-second / well under 5s): boundary member only, modest K. The heavier K=16 pytest assertion stays as-is. After this, `python -m adaptive_compute.eval --check` enforces determinism + recovery + sizing.

## Cleanup

**3. (LOW) `pyproject.toml` — remove `addopts = "-p no:capture"`.**
The plan scoped the pyproject change to adding `numpy` and "keep tool config as-is." Disabling pytest output capture repo-wide is wider than declared. Remove it. The MCSE diagnostic `print(...)` in `tests/test_reference.py` can stay — pytest surfaces prints on failure, and the diagnostic is informational; do not disable global capture to show it on pass. Ensure the suite still passes.

## Do NOT

- Do not touch `PLAN.md`, `scripts/gate.sh`, `scripts/release.sh`, `config.yaml`, `profiles/`, `.claude/`.
- Do not address the degenerate zero-positive/zero-negative resample issue — it is DEFERRED to the adaptive unit (see `deferrals.md` D1). Leave `metrics.auc()` / `bootstrap.py` behavior as-is on that point.

When done: `scripts/gate.sh` green from the repo root, commit on this branch with a clear message, and print what changed.
