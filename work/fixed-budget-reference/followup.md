You are resuming as the implementer for work/fixed-budget-reference/plan.md, in the SAME worktree on branch wt/fixed-budget-reference. Review round 3 raised findings; the Owner authorized this fix round. Read work/fixed-budget-reference/plan.md and work/fixed-budget-reference/deferrals.md first.

Stay inside the plan footprint. Re-run scripts/gate.sh until green, commit, and print an updated summary.

## Must fix

**1. (HIGH) Enforce the reference/adaptive SeedSequence branching structurally, even for a raw SeedSequence input.**
Today `src/adaptive_compute/bootstrap.py:63` uses a passed `SeedSequence` directly:
`seed_sequence = seed if isinstance(seed, np.random.SeedSequence) else reference_seed(seed)`.
That bypasses the reference branch split for raw-SeedSequence callers, so the plan's "structural, not by convention" independence guarantee holds only for int seeds. `paired_bootstrap_deltas` IS the reference resampler, so it must ALWAYS consume the reference branch.
- Change it so the seed ALWAYS routes through `reference_seed(seed)` (which spawns and takes branch [0]) regardless of whether `seed` is an `int` or a `SeedSequence`. After this, `seed_spawn_key` is the reference branch key (non-empty), never `()`.
- The future adaptive resampler will use `adaptive_seed` (branch [1]); do not add it here (no adaptive code this unit).
- This changes the exact draws produced for SeedSequence inputs (they now go through one more spawn). Update any test that asserts specific draws/spawn_key for a SeedSequence input accordingly. The across-replication sizing checks must still hold: passing K independent spawned children still yields K independent reference streams (each child spawns its own branch [0]) — verify the boundary-member MCSE assertion still passes with comfortable headroom.
- Determinism for int seeds must be unchanged (int already routed through `reference_seed`); the bit-for-bit replay test must still pass.

## Also fix (LOW, bundled by Owner)

**2. `tests/test_reference.py` — the boundary-routing test is vacuous.**
`test_boundary_stratum_routes_away_from_reference_decision` sets a flag then guards the reference call behind `if classify_delta(...) != "boundary"`, which is a dead branch after the preceding assert, so it never exercises real routing. Rewrite it to actually assert the scored-pipeline behavior: e.g. assert that for a boundary member `classify_delta(delta(E)) == "boundary"` AND that invoking the reference decision directly on that boundary case raises `UnresolvedReferenceError` (the loud error), so the test would catch a regression that forgot to skip boundary members. Make it a real, non-vacuous test.

**3. `--check` recovery/sizing failure branches are untested.**
Add deliberate-perturbation tests (mirroring `test_eval_check_fails_when_replay_is_perturbed`) that drive `eval._check`'s `return 1` branches for (a) a recovery mismatch and (b) a sizing/MCSE overflow, so all three documented failure modes of `python -m adaptive_compute.eval --check` are covered, not just determinism. Keep them fast.

## Do NOT

- Do not touch `PLAN.md`, `scripts/gate.sh`, `scripts/release.sh`, `config.yaml`, `profiles/`, `.claude/`.
- Do not reopen D1 (degenerate zero-positive resample — deferred to the adaptive unit).
- Do not change the straddle→`UnresolvedReferenceError` behavior or reintroduce `-p no:capture`.

When done: `scripts/gate.sh` green from the repo root, commit on this branch with a clear message, and print what changed. (Note: if your sandbox pytest hits a `readline`/capture segfault, report it — it is an environment artifact; the authoritative gate runs in the repo env.)
