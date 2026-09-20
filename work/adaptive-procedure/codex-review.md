**HIGH** `src/adaptive_compute/bootstrap.py`: the new `_validated_arrays` path no longer validates finite scores or binary labels before replacing the old `metrics.delta(...)` call. `_resample_deltas` then treats `y == 1` as positive and every other value as negative, so inputs like `y=[0,2]` or NaN scores silently produce bootstrap deltas instead of raising. That changes the frozen reference path’s trust-boundary behavior and can yield silent wrong scientific results. Reuse the existing metric validation or add equivalent finite/binary checks before resampling.

**HIGH** `src/adaptive_compute/benchmark.py`: `h1_holds` folds Pareto/savings into the H1 verdict. The plan defines the H1 test as “upper CI ≤ α in every non-boundary stratum,” while Pareto/savings is a separate comparison. As written, a run with acceptable false-stop CIs but less than 2x savings will be reported as `H1 NEGATIVE RESULT`, which misstates the statistical result artifact.

**MEDIUM** `src/adaptive_compute/benchmark.py`: `DEFAULT_N_TEST = 500` does not satisfy the plan’s stated “CI half-width ≤ 0.01 at the tolerance” requirement. Around a 0.05 false-stop rate, a 95% Wilson interval with n=500 has roughly double that half-width. Either increase `N_test` or revise the stated precision contract.

Codex verdict: REQUEST CHANGES
