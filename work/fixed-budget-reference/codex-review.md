**Findings**

HIGH: `src/adaptive_compute/bootstrap.py:19` / `:60` does not preserve the plan’s SeedSequence branching invariant. If `paired_bootstrap_deltas(..., seed=root_seed_sequence)` is called with a root `SeedSequence`, it uses that root directly instead of spawning the reference branch. Two callers using the same root `SeedSequence` directly can replay identical bootstrap draws, and the returned `seed_spawn_key` can be `()`, not the reference branch key. The plan explicitly makes `SeedSequence.spawn` branching the structural guarantee that reference and future adaptive streams are independent, so this should be enforced or the API should reject unbranched/root `SeedSequence` inputs.

LOW: The failure-mode test for `eval --check` only perturbs replay determinism. The acceptance criterion says the check should exit non-zero for determinism, recovery, or sizing failures; recovery/sizing branches are implemented, but not covered by deliberate perturbation tests.

Codex verdict: REQUEST CHANGES
