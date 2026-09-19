You are resuming as the implementer for work/fixed-budget-reference/plan.md, in the SAME worktree on branch wt/fixed-budget-reference. Review round 2 raised findings; the Owner has decided the resolution. Read work/fixed-budget-reference/plan.md and work/fixed-budget-reference/deferrals.md first.

Stay inside the plan footprint. Re-run scripts/gate.sh until green, commit, and print an updated summary. If any item cannot be fixed within the plan's scope, STOP and explain rather than working around it.

## Must fix

**1. (HIGH — Owner decision) A straddling percentile interval must be a LOUD ERROR, not a silent `equivalent` bucket.**
Right now `reference._decision_from_interval` maps a straddling interval (one that is neither wholly above `+δ`, nor wholly below `−δ`, nor wholly within `[−δ,+δ]`) to `equivalent`. That is a false-equivalence: the interval extends past `+δ`/`−δ` yet reports equivalent. The Owner's decision: the fixed-budget reference, at a correctly-sized `B_ref`, should resolve every NON-boundary case cleanly; a straddle means the case is boundary-adjacent or `B_ref` is under-sized, and must be surfaced, not bucketed.

Implement:
- Keep `Decision = Literal["A_better","B_better","equivalent"]` (still three outcomes, still NO abstain).
- In the interval read-off: wholly above `+δ` → `A_better`; wholly below `−δ` → `B_better`; wholly within `[−δ,+δ]` → `equivalent`. For the remaining (straddling) case, RAISE a dedicated exception — define `class UnresolvedReferenceError(RuntimeError)` (or similar, in reference.py) — with a message naming the interval bounds and `δ`, e.g. "reference interval [lo, hi] straddles ±δ=… at B_ref=…; case is boundary-adjacent or B_ref under-sized". Do NOT fall back to the point estimate and do NOT return equivalent.
- The scored pipeline must classify by the plug-in `Δ(E)` via `strata.classify_delta` FIRST and only invoke the reference decision on NON-boundary cases. Ensure `eval._check`'s recovery loop already skips `boundary` members (it does today) so it never triggers the raise on the scored path; keep that ordering explicit.

Tests (in tests/test_reference.py):
- REPLACE the current `test_..._straddling_margin_resolves_to_equivalent` with a test asserting a straddling interval RAISES `UnresolvedReferenceError` (construct bounds that cross a δ edge, e.g. lower < δ < upper).
- Non-boundary known-decision recovery (existing test) MUST still pass unchanged — those cases resolve cleanly and never raise.
- Add a test showing a boundary case (`|Δ(E) ∓ δ| < ρ·δ`) is classified `boundary` by strata and is therefore routed away from the reference decision (i.e., the gating that prevents the raise on scored cases).

**2. (MEDIUM — code-reviewer) Widen the `heavy_tailed` member's margin so recovery is not razor-thin.**
At the committed seed, `heavy_tailed`'s percentile interval lower bound is +0.0549 against δ=0.05 — only 0.005 of slack, fragile to any reseed. Adjust the `heavy_tailed` generator effect size and/or `B_ref` so its `B_ref` interval clears its δ boundary with a comfortable margin (target: lower bound ≥ δ + a few × the member's MCSE), WITHOUT removing the heavy-tail mechanism (heavy-tailed per-row score contributions — that is the whole point of the member). Its plug-in `Δ(E)` must remain in a non-boundary stratum and recovery must stay green.

## Do NOT

- Do not touch `PLAN.md`, `scripts/gate.sh`, `scripts/release.sh`, `config.yaml`, `profiles/`, `.claude/`.
- Do not address the degenerate zero-positive/zero-negative resample issue — DEFERRED to the adaptive unit (deferrals.md D1). Leave `metrics.auc()` / `bootstrap.py` behavior as-is on that point.
- Do not reintroduce the point-estimate fallback or any `-p no:capture` addopts.

When done: `scripts/gate.sh` green from the repo root, commit on this branch with a clear message, and print what changed (name the new exception type and the heavy_tailed params you chose).
