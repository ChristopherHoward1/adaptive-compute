# Implementer notes — betting-cs-retest (dispatch 1)

Implemented within the planned footprint.

## What changed
- Added WSR betting CS in `src/adaptive_compute/betting.py`.
- Added `instrument="eb" | "betting"` to `adaptive.py`, defaulting to `"eb"`.
- Threaded `instrument` through benchmark/eval, fixed `b=64`, tuned only `B_max`, changed §7 pass logic to `<= DEFAULT_ALPHA` (deferral A5).
- Added deterministic betting tests in `tests/test_betting.py`.
- Generated `work/betting-cs-retest/results-eb.{md,json}`, `results-betting.{md,json}`, `comparison.md`.
- Updated `knowledge/anytime-valid-band.md` with the WSR construction and recorded verdict.

## Headline A/B result: NO flip
Betting preserved §7 (`false_stop_test_pass=True`) and reduced median draws substantially
(equivalent 704 -> 192), but `savings_pareto_pass` stayed `False`.

## Verification (implementer)
- `python -m adaptive_compute.eval --compare` passed and regenerated artifacts.
- `scripts/gate.sh` passed: 49 passed, hooks passed, GATE: PASS.
- Gate run needed `PYTHONPATH=<readline-noreadline-stub>` because the implementer's Python
  install segfaults on `import readline` under pytest capture (known env-specific friction;
  `gate-readline-resilience` candidate). Stub is outside the repo.

## Blocked
- Could not commit: `git add` failed — real git dir outside writable sandbox
  (`.git/worktrees/betting-cs-retest/index.lock: Operation not permitted`).
  Working-tree changes ready but uncommitted. Orchestrator to commit.
