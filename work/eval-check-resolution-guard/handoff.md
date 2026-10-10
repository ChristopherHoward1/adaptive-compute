You are the implementer for this work unit. Read AGENTS.md in the repo root first — it is your contract.
Follow its build-discipline section while staying inside the plan footprint.

Work unit: work/eval-check-resolution-guard/plan.md  (read it in full; it is your source of truth)
Branch: wt/eval-check-resolution-guard (already checked out in this worktree — verify with `git branch --show-current` before changing anything)

Footprint (from the plan, repeated here as the hard boundary):
- src/adaptive_compute/benchmark.py — constant move ONLY: lift `_tune_params`'s inline default candidates into a module-level `DEFAULT_CANDIDATES` mapping keyed by instrument; `_tune_params` reads `DEFAULT_CANDIDATES[instrument]` when `candidates is None`. No other change.
- src/adaptive_compute/eval.py — add the equivalence guard helper and call it FIRST in `_check()`.
- tests/test_eval_check.py (new) — detectability tests.

Key constraints:
- Do NOT modify src/adaptive_compute/adaptive.py, betting.py, generators.py, or anything under work/*/results*. The guard must test the instruments and battery as-is; never adjust them to make the guard pass.
- Guard: for each instrument in ("eb", "betting"), take the largest-`b_max` candidate from `benchmark.DEFAULT_CANDIDATES[instrument]` (read through the module attribute, not a `from ... import` name, so tests can monkeypatch it). Run `adaptive_decision` on `BATTERY["small_effect"]` with that candidate's `b`, `alpha`, `b_max`, plus `instrument=instrument`, `margin=DEFAULT_DELTA`, `seed=12345`. Pass only if `decision == decision_from_delta(<plug-in delta>, DEFAULT_DELTA)` AND `draws_consumed < b_max`. On failure print `adaptive (<instrument>) did not certify small_effect equivalence before B_max=<n>` to stderr and return 1. Add the guard's draws to `total_draws`. Do NOT use `CHECK_ADAPTIVE_B_MAX` for the guard.
- Expected: `python -m adaptive_compute.eval --check` prints `draws_consumed=8656` (baseline on main is 7760; guard adds 704 EB + 192 betting).
- Tests in tests/test_eval_check.py:
  1. R1 grid: `monkeypatch.setattr(benchmark, "DEFAULT_CANDIDATES", {...})` with every candidate `b_max=320` (EB `(32,320)`,`(64,320)`; betting `(64,320)`), call `_check()`, assert it returns 1 and stderr contains `adaptive (eb) did not certify small_effect equivalence`.
  2. Betting branch: patch only betting to `(64,128)` (keep EB defaults), assert `_check()` returns 1 with `adaptive (betting) did not certify` in stderr.
  3. (Recommended) Call the guard helper directly on unpatched defaults and assert it passes with 896 draws.
  - Capture stderr with `contextlib.redirect_stderr(io.StringIO())` like tests/test_determinism.py. Do NOT use `capsys` — it errors under `-p no:capture`, which the gate's retry uses.
  - Always patch via `monkeypatch.setattr`, never mutate the dict in place.
- Existing tests (tests/test_benchmark.py, tests/test_determinism.py) must pass unmodified.

When done:
1. Run scripts/gate.sh from the repo root — it must pass.
2. Commit your work on this branch with a clear message.
3. Print a final summary: what changed and why, criteria partially met (if any), out-of-scope observations.
