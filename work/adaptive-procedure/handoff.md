You are the implementer for this work unit. Read AGENTS.md in the repo root first — it is your contract.
Follow its build-discipline section while staying inside the plan footprint.

Work unit: work/adaptive-procedure/plan.md  (read it in full; it is your source of truth)
Branch: wt/adaptive-procedure (already checked out in this worktree — verify with `git branch --show-current` before changing anything)

Footprint (from the plan, repeated here as the hard boundary):

Files to CREATE:
- src/adaptive_compute/adaptive.py
- src/adaptive_compute/sweep.py
- src/adaptive_compute/benchmark.py
- tests/test_adaptive.py, tests/test_sweep.py, tests/test_benchmark.py
- knowledge/anytime-valid-band.md
- work/adaptive-procedure/results.md AND work/adaptive-procedure/results.json (the first-result artifact, produced by running `python -m adaptive_compute.eval --run`)

Files to MODIFY:
- src/adaptive_compute/eval.py — add `--run` (offline benchmark); extend `--check` with the adaptive coverage listed in the plan; apply the D2 diagnostic fix.
- src/adaptive_compute/bootstrap.py — extract the inner resample kernel and add `adaptive_bootstrap_stream(...)`; add the D1 degenerate-resample policy. MUST keep the reference path (`paired_bootstrap_deltas`) byte-identical.
- tests/test_bootstrap.py, tests/test_determinism.py — cover the new batched path and D1; keep existing reference-path assertions green.
- ARCHI.md — Layout: new modules; EVAL_METRIC PROVISIONAL → resolved (name the suite); note `eval --run`.

Files you MUST NOT touch (live hazards):
- src/adaptive_compute/reference.py — the reference decision functional is FROZEN. You target it; you never alter it. Changing it silently redefines "agreement" and invalidates the whole comparison.
- scripts/gate.sh, scripts/release.sh, config.yaml, profiles/, .claude/, PLAN.md (Orchestrator-owned).

Key constraints:
- INSTRUMENT (Owner-confirmed): the anytime-valid band is an empirical-Bernstein / betting CONFIDENCE SEQUENCE on the BOUNDED MEAN E*[Δ*] (Δ* ∈ [−1,1]). Do NOT implement the tail-probability variant — it is the rejected alternative (document why in knowledge/anytime-valid-band.md). The CS must be anytime-valid (valid under optional stopping); a naive per-batch percentile band is wrong and will fail review. Cite the instrument you use (e.g. Howard et al. 2021 empirical-Bernstein CS, or Waudby-Smith & Ramdas betting CS) in the module docstring and the knowledge doc.
- BLINDNESS: adaptive.py's public entry takes (scores_a, scores_b, y, δ, α, b, B_max, seed) and NONE of B_ref, the reference decision, or the true/plug-in Δ. Enforce by signature.
- SEED CONTRACT (read knowledge/bootstrap-seed-and-determinism.md — load-bearing): the new adaptive resampler routes its seed through `adaptive_seed` (branch [1]) — it is the first branch-[1] consumer. Use a SINGLE `default_rng(adaptive_seed(seed))` and pull successive batches of b draws from it (not per-batch sub-seeds). Determinism must hold on BOTH seed paths: same int seed twice, AND the same SeedSequence object reused twice, each bit-identical in decision + draw count. Reference (branch [0]) and adaptive (branch [1]) streams must be independent.
- DRAW ACCOUNTING: exact; draws_consumed ≤ B_max; a resolved run reports < B_max; an unresolvable case at small B_max returns `abstain` with draws_consumed == B_max.
- D1 (degenerate resample, all-positive or all-negative draw → metrics.auc raises ValueError): apply the plan's recommended policy — treat a degenerate resample as AUC=0.5 for each model ⇒ Δ*=0, counted as a normal draw — unless you have a clearly better reason; either way it must be explicit, tested, and keep draw accounting exact. This must NOT change reference-path output at committed seeds (regression-guard it).
- D2 (hard-member MCSE diagnostic): the diagnostic you ADD for the hard members must compute its per-replication estimate via `paired_bootstrap_deltas(...) + np.mean(...)` and NEVER route through `fixed_budget_reference` (which raises on a straddle). Assert structurally.
- BENCHMARK: per member, sweep N seeds via `dataclasses.replace(params, seed=base+i)` (do NOT edit generators.py). Disjoint splits: tune i∈[0,N_tune); test i∈[10_000,10_000+N_test). Freeze (b,α) on tune; all headline numbers from test. Size N_test so the false-stop-rate CI half-width ≤ 0.01 at the tolerance (§7 target ≥500). Score decision-agreement vs `fixed_budget_reference(...).decision`; a (member,seed) whose reference RAISES UnresolvedReferenceError is EXCLUDED from false-stop scoring and counted/reported as `reference_unresolved` (never a traceback).
- FIXED-B SWEEP + PARETO (sweep.py): the reference percentile decision at a grid of fixed B, no early stopping; plus the Pareto verdict (§4/§8: is any fixed-B dominated — lower median draws AND false-stop ≤ adaptive's — at the ≥2× target?). Test the domination logic on a hand-built fixture.
- B_better AGREEMENT FIXTURE: no BATTERY member is B-favored; construct the B_better case by swapping scores_a/scores_b on an A-favored member.
- eval --check must stay FAST (well under 5 s), no network, no plots. eval --run is the offline heavy path that writes the results artifact.
- RESULTS ARTIFACT (work/adaptive-procedure/results.{md,json}): per non-boundary stratum — false-stop rate + binomial CI, draws p50/p90/p99, abstain rate, reference_unresolved count, Pareto savings summary; the heavy-tailed member's realized false-stop rate reported specifically; and a plain statement of whether H1 HOLDS or is a NEGATIVE result per §8. A negative result is fully acceptable and shippable — report honestly, do not tune to pass.

When done:
1. Run scripts/gate.sh from the repo root — it must pass (ruff, mypy, pytest, shellcheck, gate.d hooks incl. eval --check).
2. Run `python -m adaptive_compute.eval --run` to generate the results artifact, and commit it.
3. Commit your work on this branch with a clear message.
4. Print a final summary: what changed and why, which acceptance criteria are met (and any only-partially met), the H1 verdict from the run, and any out-of-scope observations for the Orchestrator.
