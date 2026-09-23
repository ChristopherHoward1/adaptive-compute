# Gate readline resilience

**Slug:** gate-readline-resilience · **Date:** 2026-09-22 · **Status:** released v2026.9.6

## Goal

In the implementer's sandbox, the conda Python sometimes segfaults on `import readline`. pytest does that import during capture setup: `_pytest/capture.py::pytest_load_initial_conftests` calls `_readline_workaround()` unconditionally. So the crash happens before any test is collected, `pytest -q` dies from a signal (exit 139), and `scripts/gate.sh` reports FAIL. This has happened **4 times across 3 units**: `adaptive-procedure`, `betting-cs-retest`, and `equivalence-band-savings` twice (`work/equivalence-band-savings/retro.md:58`). Each time, the implementer fixed it by hand with `PYTEST_ADDOPTS='-p no:capture'` or a `PYTHONPATH` readline shim. The crash does **not** reproduce in the Orchestrator shell as of 2026-09-22: `import readline` succeeds under TERM=dumb, empty, unset, and xterm, and `pytest -q` passes 55/55. So it depends on the environment and is intermittent. Done means the gate recovers from a pytest signal death by itself, with no manual workaround, and never retries an ordinary (non-signal) test failure.

## Approach

In the Python section of `scripts/gate.sh`, replace `run pytest -q` with a small helper. The helper runs pytest **itself**; it does not probe first and then call `run`.

1. Print `▶ pytest -q`, then run `pytest -q` once and capture its exit code.
2. If the code is 0, pass. If it is non-zero and ≤128 (1 = tests failed, 2 = interrupted, 4 = usage error, 5 = no tests collected), print `✗ FAILED: pytest -q` and set `fail=1`. That is the same output and meaning as today, with no retry.
3. If the code is >128, meaning a signal killed pytest (139 for SIGSEGV, 134 for SIGABRT), print:
   `⚠ pytest died by signal (exit <rc>) — known native-readline crash under pytest capture; retrying once with -p no:capture`
   Then run the retry through the existing `run` function: `run pytest -q -p no:capture`. That result is final, and there is no loop.

A two-line comment above the helper names the symptom (`_readline_workaround` in a faulthandler trace, pytest exiting 139) and says why `-p no:capture` is the fix, so a later grep finds it.

- **Why wait for the signal instead of probing `import readline` first:** the crash is intermittent, so a probe can pass and pytest can still crash afterwards.
- **Why exit code >128 means a signal death here:** `pytest` is a console script with a python shebang, and it is exec'd directly. faulthandler prints its trace and then re-raises the signal, so bash sees 128+signal. The reviewer verified this.
- **Why `-p no:capture`:** `capture` is a default plugin that can be disabled. Disabling it skips `_readline_workaround` completely. `python -X importtime -m pytest -q -p no:capture` imports no `readline` and passes 55/55 (reviewer-verified). `-s` / `--capture=no` does **not** help, because the hook still runs (`work/adaptive-procedure/notes-round3.md:12348`). No test in `tests/` or `src/` uses `capsys`, `capfd`, or `caplog`, so turning capture off breaks no fixture.

**Known limit (accepted):** a *test* that crashes intermittently in native code also exits with a signal. It would be retried once, and could pass with only the `⚠` line as a trace. A test that crashes every time still fails on the retry. The `⚠` line appears in the gate output, so nothing is hidden. Narrowing the trigger to runs whose stderr contains `_readline_workaround` was considered and rejected: tee'ing stderr to a temp file adds complexity for a rare case.

Alternatives considered:
- An always-on `-p no:capture`: rejected. It permanently changes pytest's behavior and would break any future `capsys` test.
- A committed `readline.py` shim: rejected. It hides a stdlib module from the code under test.
- Only documenting the workaround: rejected. It still costs a round-trip every time.
- A new `knowledge/` doc: dropped. The `⚠` line and the in-script comment carry the text someone would search for.

## Footprint

Files to modify:
- `scripts/gate.sh`: the Python/pytest block only, plus the helper and its comment.
- `tests/test-scripts.sh`: new gate-fixture cases (see the criteria below).
- `ARCHI.md`:
  - Line 43 (Verification): the gate's pytest step now includes the one-shot retry when pytest dies by a signal.
  - Line 21: `knowledge/` is no longer "empty but for a README".
  - This edit is required: `release.sh:120` → `archi-fresh.sh` refuses to release if something under `scripts/` was committed after `ARCHI.md`.

Files NOT to touch:
- `tests/*.py` and `src/`: this is harness-only work.
- `pyproject.toml` `[tool.pytest.ini_options]`: no global `addopts` change.

## Acceptance criteria

Fixture notes, which apply to every case below:
- Each case uses `setup_gate_fixture` (`tests/test-scripts.sh:578`), which creates no `pyproject.toml` and no `tests/*`. The case must add both, or the pytest block is skipped.
- The restricted `PATH` has only bash, git and awk. The fake `pytest` must be pure bash (`#!/usr/bin/env bash`). It logs to an absolute path outside `$GATE_REPO`: `$TMP/<fixture-name>/pytest.log`. Bake that path into the fake with an unquoted heredoc, or export it in the `bash -c`, so the fake can write `echo "$*" >>"<log>"`.
- `ruff` and `shellcheck` are absent there, so they show as skipped.

The cases:
- [ ] **Exit 139, then green on retry.** Setup: the fake logs its args, exits 0 if its args contain `no:capture`, and otherwise exits 139. Expected:
  - `gate.sh` exits 0, and the output contains `⚠ pytest died by signal (exit 139)` and `GATE: PASS`.
  - The log has exactly two lines: `-q`, then `-q -p no:capture`.
- [ ] **Real signal death, then green on retry.** Setup: the fake logs its args, exits 0 if its args contain `no:capture`, and otherwise runs `kill -SEGV $$`. Expected: `gate.sh` exits 0, and the output contains `⚠ pytest died by signal (exit 139)` and `GATE: PASS`. This proves the helper's exit-code capture sees a real signal death, not just an `exit 139`.
- [ ] **Real test failure is not retried.** Setup: the fake logs its args and exits 1. Expected:
  - `gate.sh` exits non-zero.
  - The output contains `✗ FAILED: pytest -q` and has no `⚠ pytest died by signal` line.
  - The log has exactly one line, `-q`.
- [ ] **Persistent crash still fails.** Setup: the fake logs its args and always exits 139. Expected:
  - `gate.sh` exits non-zero.
  - The output contains the `⚠` line and `✗ FAILED: pytest -q -p no:capture`.
  - The log has exactly two lines. There is no retry loop.
- [ ] **Healthy path unchanged.** Setup: the fake logs its args and exits 0. Expected:
  - `gate.sh` exits 0, and the output contains `▶ pytest -q` and `GATE: PASS`, with no `⚠` line.
  - The log has exactly one line, `-q`.
- [ ] All the cases above live in `tests/test-scripts.sh`, so the gate runs them itself.
- [ ] `bash scripts/archi-fresh.sh` exits 0 on the branch.
- [ ] **Environment smoke check (not proof of the fix; the crash may not reproduce):** `bash scripts/gate.sh` exits 0 in the worktree without any manual `PYTEST_ADDOPTS`/`PYTHONPATH` workaround. The implementer reports whether the `⚠` retry fired.

## Release

Release note: Gate retries pytest once with `-p no:capture` when pytest dies by a signal (the native-`readline` segfault under pytest capture), so the known sandbox crash no longer fails the gate or needs a manual workaround; ordinary (non-signal) test failures are never retried.

## Verification

- `bash tests/test-scripts.sh`
- `bash scripts/archi-fresh.sh`
- `bash scripts/gate.sh`, run with no `PYTEST_ADDOPTS` set.

## Review

Round 1: the fresh `plan-reviewer` returned REVISE. Its checks confirmed the core design: exit code >128 does mean a signal death under a console-script pytest, `-p no:capture` does bypass `_readline_workaround`, and there are no capture fixtures. All six findings were applied, with no disagreements:
1. `ARCHI.md` added to the footprint, plus the `archi-fresh.sh` criterion. Without it, release would refuse.
2. Added a case where the fake pytest really is killed by a signal (`kill -SEGV`). The live-environment gate run is relabelled as a smoke check.
3. Reworded the Goal and release note to "never retries an ordinary (non-signal) test failure". Documented the intermittent native test-crash limit and accepted it (option a).
4. Tightened each case's assertions: every fake logs its args, the retry's args must be exact, and the `✗ FAILED` and `▶` lines are checked. Added the fixture notes (pyproject and tests markers, a pure-bash fake).
5. The helper runs pytest itself exactly once. No probe followed by `run`.
6. Corrected the count to "4 occurrences / 3 units". Dropped the knowledge doc (the reviewer's optional simplification) along with the moot README-index clause.

Round 2 (a fresh plan-reviewer on rev 2): APPROVE. It verified that all six round-1 fixes landed in the code paths they cite. It confirmed that `kill -SEGV $$` in a pure-bash fake under the restricted PATH gives rc=139 to the caller (bash 3.2 and 5). It also confirmed that the retry going through `run` produces the `▶`/`✗ FAILED` strings the criteria assert on. Minor findings:
1. The fake's log path was unspecified. Applied: the fixture notes now say where the log lives.
2. A pre-set `PYTEST_ADDOPTS='-p no:capture'` would pass the flag twice on retry. That is moot, since a run with the flag already set never crashes, so no handling is needed.
3. The verdict line needed updating. Done.

Plan verdict: APPROVE

### Code review (round 1)

The fresh `code-reviewer` returned APPROVE, and Codex returned APPROVE (`codex-review.md`). All eight acceptance criteria were verified as met, and the gate passed with `PYTEST_ADDOPTS` unset. In the implementer's sandbox the real segfault occurred (`Segmentation fault: 11  pytest -q`), and the `⚠` retry recovered to green. LOW notes, recorded here and not sent back:
1. The `gate.sh:24-25` comment says "exit 139", but the trigger is any code above 128. An OOM kill (137) would also be retried once. This is within the plan's accepted Known limit, and the `⚠` line still appears.
2. The five new fixture cases in `tests/test-scripts.sh` repeat the same setup block. This is style only.

Code-review verdict: APPROVE
Codex-review verdict: APPROVE
