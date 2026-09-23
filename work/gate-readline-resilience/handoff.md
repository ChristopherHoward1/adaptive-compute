You are the implementer for this work unit. Read AGENTS.md in the repo root first — it is your contract.
Follow its build-discipline section while staying inside the plan footprint.

Work unit: work/gate-readline-resilience/plan.md  (read it in full; it is your source of truth — the Approach and Acceptance criteria sections are exact, including output strings)
Branch: wt/gate-readline-resilience (already checked out in this worktree — verify with `git branch --show-current` before changing anything)

Footprint (from the plan, repeated here as the hard boundary):
- scripts/gate.sh — the Python/pytest block only (plus the new helper and its two-line comment)
- tests/test-scripts.sh — five new gate-fixture cases
- ARCHI.md — line 43 (Verification: mention the one-shot pytest retry on signal death) and line 21 (`knowledge/` is no longer "empty but for a README")

Key constraints:
- Helper runs `pytest -q` exactly ONCE itself (prints `▶ pytest -q`), captures rc (gate.sh uses `set -uo pipefail`, no `-e`). rc 0 → pass; 1..128 → print `✗ FAILED: pytest -q`, set fail=1, NO retry; >128 → print exactly `⚠ pytest died by signal (exit <rc>) — known native-readline crash under pytest capture; retrying once with -p no:capture` then `run pytest -q -p no:capture` (final, no loop).
- Do NOT use an always-on `-p no:capture`, a readline shim, or any pyproject `addopts` change. Do not touch tests/*.py, src/, or pyproject.toml.
- Test fixtures: use `setup_gate_fixture` (tests/test-scripts.sh:578); add `pyproject.toml` and a `tests/test_x.py` marker file to the fixture repo or the pytest block is skipped. The gate runs under `PATH='$GATE_BIN'` (only bash, git, awk) — the fake `pytest` must be pure bash (`#!/usr/bin/env bash`), logging `echo "$*" >>"<abs log path>"` to `$TMP/<fixture-name>/pytest.log` (baked in via unquoted heredoc or exported env). Assertions (grep, line counts) run under the normal PATH, like the existing gate cases around line 1206+.
- The "real signal death" case must use `kill -SEGV $$` in the fake (not `exit 139`).
- Every assertion in the plan's five cases must be implemented, including exact log line contents (`-q`, then `-q -p no:capture`) and call counts.
- The pytest segfault may hit YOUR environment: that is exactly what this unit fixes. Do NOT set PYTEST_ADDOPTS or a PYTHONPATH shim when running the final gate. In your summary, state whether the `⚠` retry line fired in your gate runs.
- `bash scripts/archi-fresh.sh` must exit 0 after your commit (ARCHI.md committed with or after scripts/ changes).
- shellcheck clean.

When done:
1. Run scripts/gate.sh from the repo root — it must pass.
2. Commit your work on this branch with a clear message.
3. Print a final summary: what changed and why, criteria partially met (if any), out-of-scope observations, and whether the ⚠ retry fired.
