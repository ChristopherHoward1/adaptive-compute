**Findings**

HIGH: [src/adaptive_compute/bootstrap.py:19](/Users/cboyfly/Documents/repos/adaptive-compute/src/adaptive_compute/bootstrap.py:19) accepts `np.random.SeedSequence`, but `seed_branches()` calls `root.spawn(2)` directly on it. `SeedSequence.spawn()` mutates the sequence’s child counter, so replaying with the same `SeedSequence` object is not bit-identical. That breaks the core determinism acceptance criterion for an accepted seed type. Concrete failure: create one `ss = np.random.SeedSequence(1234)`, call `paired_bootstrap_deltas(..., seed=ss)` twice, and the second call uses later children, producing different draws. Clone from `entropy`/`spawn_key` before spawning, or stop accepting `SeedSequence` as a replayable public seed.

HIGH: [tests/test_reference.py:87](/Users/cboyfly/Documents/repos/adaptive-compute/tests/test_reference.py:87) says hard-member MCSE is diagnostic-only, but the diagnostic computes estimates via `fixed_budget_reference()`. That function raises `UnresolvedReferenceError` whenever an interval straddles the margin, so heavy-tailed / rare-event members are still hard-gated on resolution before the diagnostic can print. This contradicts the plan’s explicit “diagnostic, not gated” treatment for those members. The diagnostic should use `paired_bootstrap_deltas()` and `np.mean(...)` directly, matching the boundary MCSE test, so only finiteness is asserted.

I couldn’t run the pasted diff locally because this checkout is still on `main` and does not contain the new files; the findings above are from the supplied plan/diff.

Codex verdict: REQUEST CHANGES
