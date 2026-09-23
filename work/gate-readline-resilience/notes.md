Dispatching implementer in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
  codex exec --sandbox workspace-write - < /Users/cboyfly/Documents/repos/adaptive-compute/work/gate-readline-resilience/handoff.md
OpenAI Codex v0.139.0
--------
workdir: /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
model: gpt-5.5
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR]
reasoning effort: none
reasoning summaries: none
session id: 01a0ce3b-cef5-7513-ab44-519d954980f0
--------
user
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

codex
I’ll start by reading the repo contract and the work-unit plan, then I’ll verify the branch before touching anything. After that I’ll trace the existing gate/test flow so the edits stay exactly inside the requested footprint.
exec
/bin/zsh -lc "sed -n '1,220p' AGENTS.md" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
# Implementer Contract

You are the implementer. Your source of truth is the handoff you received; it names the work unit (`work/<slug>/plan.md`), the branch, and the file footprint.

## Rules

1. **Scope is the plan. Nothing more.** No refactoring adjacent code, no speculative features. If the work seems to require a file outside the declared footprint, stop and say so instead of expanding it yourself.
2. **You are in a worktree on a pre-created branch.** Verify the branch matches the handoff before changing anything. Do not switch, merge, rebase, or reset.
3. **Run the gate before finishing:** `scripts/gate.sh` from the repo root. Do not report done while it fails.
4. **Finish with a summary**: what changed and why, any acceptance criteria only partially met (and why), anything you noticed but left out of scope.
5. **Stop and surface** rather than guess when: acceptance criteria conflict, the plan seems wrong against the actual code, or a decision belongs to the Orchestrator or Owner.

## Build Discipline

Run this after you understand the task and trace the real flow end to end:

1. Does this need to exist at all? If it is speculative, skip it and say so in one line.
2. Already in this codebase? Reuse the helper, util, type, or pattern that lives here.
3. Stdlib does it? Use stdlib.
4. Native platform feature covers it? Use the platform.
5. Already-installed dependency solves it? Use it. Do not add a dependency for what a few lines do.
6. Can it be one line? Make it one line.
7. Only then write the minimum code that works.

For bug fixes, fix the root cause, not the named symptom: grep every caller of the function you touch and prefer one shared guard over per-caller patches.

Never be lazy about understanding the problem, input validation at trust boundaries, error handling that prevents data loss, security, accessibility, or anything explicitly requested or named in the plan.

Use a `ponytail:` comment for a deliberate simplification that cuts a real corner; name the ceiling and upgrade path.

Honest and brief beats thorough and padded.

exec
/bin/zsh -lc "sed -n '1,260p' work/gate-readline-resilience/plan.md" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
# Gate readline resilience

**Slug:** gate-readline-resilience · **Date:** 2026-09-22 · **Status:** approved

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

exec
/bin/zsh -lc 'pwd && git branch --show-current' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
wt/gate-readline-resilience

codex
Branch and contract check out: we’re on `wt/gate-readline-resilience`, and the plan is very explicit about the three-file boundary. I’m going to inspect the current pytest gate block, the fixture helper, nearby gate tests, and the ARCHI lines before making the smallest patch.
exec
/bin/zsh -lc "sed -n '1,220p' scripts/gate.sh" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
#!/usr/bin/env bash
# The gate. Exit 0 = pass. Non-zero = fail, and everything printed is the
# feedback the implementer gets. Agents do not overrule this script.
#
# Auto-detects the stacks present and runs every applicable check.
# Profile- or project-specific checks go in scripts/gate.d/*.sh (run last).
set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 1

fail=0
fail_message() {
  echo "GATE: FAIL — fix everything marked ✗ above."
}

run() {
  echo "▶ $*"
  if ! "$@"; then
    fail=1
    echo "✗ FAILED: $*"
  fi
}

required_tools=
if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
  required_tools=$GATE_REQUIRED_TOOLS
elif [[ -f config.yaml ]]; then
  required_tools=$(awk '
    /^[^[:space:]#][^:]*:/ {
      f = ($0 ~ /^gate:[[:space:]]*($|#)/)
      next
    }
    f && /^[[:space:]]*required_tools:/ {
      sub(/^[[:space:]]*required_tools:[[:space:]]*/, "")
      sub(/[[:space:]]+#.*$/, "")
      gsub(/^[[:space:]]+|[[:space:]]+$/, "")
      if (($0 ~ /^".*"$/) || ($0 ~ /^'\''.*'\''$/)) {
        sub(/^["'\'']/, "")
        sub(/["'\'']$/, "")
      }
      print
      exit
    }
  ' config.yaml)
fi

missing_required=()
if [[ -n "$required_tools" ]]; then
  IFS=: read -r -a required_tool_list <<<"$required_tools"
  for tool in "${required_tool_list[@]}"; do
    [[ -z "$tool" ]] && continue
    if ! command -v "$tool" >/dev/null; then
      missing_required+=("$tool")
    fi
  done
fi

if [[ ${#missing_required[@]} -gt 0 ]]; then
  for tool in "${missing_required[@]}"; do
    echo "✗ missing required tool: $tool"
  done
  fail_message
  exit 1
fi

skip() {
  echo "⊘ skipped: $1 (not installed)"
}

# --- Node ---------------------------------------------------------------
if [[ -f package.json ]]; then
  if command -v node >/dev/null; then
    typecheck_script=0
    for s in lint typecheck test; do
      if node -e "process.exit(require('./package.json').scripts?.['$s'] ? 0 : 1)" 2>/dev/null; then
        run npm run --silent "$s"
        [[ "$s" == typecheck ]] && typecheck_script=1
      fi
    done
    # No typecheck script but a TypeScript project: let the compiler judge.
    if [[ $typecheck_script -eq 0 && -f tsconfig.json ]]; then
      if npx --no-install tsc --version >/dev/null 2>&1; then
        run npx --no-install tsc --noEmit
      else
        skip tsc
      fi
    fi
  else
    skip node
  fi
fi

# --- Python -------------------------------------------------------------
if [[ -f pyproject.toml || -f setup.py || -f requirements.txt ]]; then
  if command -v ruff >/dev/null; then
    run ruff check .
  else
    skip ruff
  fi
  if compgen -G "tests/*" >/dev/null; then
    if command -v pytest >/dev/null; then
      run pytest -q
    else
      skip pytest
    fi
  fi
fi

# --- Shell --------------------------------------------------------------
shell_files=()
while IFS= read -r f; do shell_files+=("$f"); done \
  < <(git ls-files '*.sh' 2>/dev/null)
if [[ ${#shell_files[@]} -gt 0 ]]; then
  if command -v shellcheck >/dev/null; then
    run shellcheck "${shell_files[@]}"
  else
    skip shellcheck
  fi
fi

# --- Rust / Go ----------------------------------------------------------
if [[ -f Cargo.toml ]]; then
  if command -v cargo >/dev/null; then
    run cargo clippy -q -- -D warnings
    run cargo test -q
  else
    skip cargo
  fi
fi
if [[ -f go.mod ]]; then
  if command -v go >/dev/null; then
    run go vet ./...
    run go test ./...
  else
    skip go
  fi
fi

# --- Profile / project extensions ---------------------------------------
for hook in scripts/gate.d/*.sh; do
  [[ -f "$hook" ]] && run bash "$hook"
done

if [[ $fail -eq 0 ]]; then
  echo "GATE: PASS"
else
  fail_message
fi
exit $fail

exec
/bin/zsh -lc "sed -n '1160,1285p' tests/test-scripts.sh" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
exec
/bin/zsh -lc "sed -n '540,660p' tests/test-scripts.sh" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
  git -C '$SYNC_WORKTREE' status --porcelain | grep -Fx 'A  AGENTS.md'
"

# Pins the scoped `git add -- work/<slug>`: `git add -A` would stage this edit as a
# side effect of a bookkeeping command, changing what a later worktree commit picks up.
setup_worktree_sync_fixture sync-unrelated-unstaged
printf '# unstaged unrelated edit\n' >>"$SYNC_WORKTREE/config.yaml"
check_exit "worktree sync-artifacts leaves unrelated unstaged edit alone" 0 "" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
check "worktree sync-artifacts does not stage unrelated worktree edit" bash -c "
  git -C '$SYNC_WORKTREE' status --porcelain | grep -Fx ' M config.yaml'
"

# Pins the commit guard against `|| true`: a real commit failure must propagate, not be
# swallowed. Hooks live in the common dir, so this fires for the linked worktree too.
setup_worktree_sync_fixture sync-commit-failure
cat >"$SYNC_PRIMARY/.git/hooks/pre-commit" <<'EOF'
#!/bin/sh
exit 1
EOF
chmod +x "$SYNC_PRIMARY/.git/hooks/pre-commit"
check_fails "worktree sync-artifacts propagates a failed artifact commit" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
rm -f "$SYNC_PRIMARY/.git/hooks/pre-commit"

setup_worktree_sync_fixture sync-primary-non-main
git -C "$SYNC_PRIMARY" checkout -q -b owner-fix
check_exit "worktree sync-artifacts accepts primary checkout on non-main branch" 0 "" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
check "worktree sync-artifacts synced from non-main primary checkout" bash -c "
  git -C '$SYNC_PRIMARY' ls-tree -r --name-only wt/demo -- work/demo/handoff.md | grep -Fx work/demo/handoff.md
"

setup_worktree_sync_fixture sync-wrong-branch
(
  cd "$SYNC_PRIMARY" || exit 1
  git worktree remove "$SYNC_WORKTREE" >/dev/null
  git branch wt/other
  git worktree add -q "$SYNC_WORKTREE" wt/other
  git -C "$SYNC_WORKTREE" config user.email tester@example.com
  git -C "$SYNC_WORKTREE" config user.name Tester
) || { echo "FAIL: sync wrong-branch setup"; exit 1; }
check_exit "worktree sync-artifacts refuses expected path on wrong branch" 1 "no worktree for demo" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
check "worktree sync-artifacts wrong branch receives no artifact commit" bash -c "
  [ -z \"\$(git -C '$SYNC_PRIMARY' log --format=%s wt/other | grep '^Record artifacts for demo$')\" ] &&
  ! git -C '$SYNC_PRIMARY' ls-tree -r --name-only wt/other -- work/demo/handoff.md | grep -q .
"

# --- gate.sh tool visibility and required-tool preflight
setup_gate_fixture gate-node-missing
(
  cd "$GATE_REPO" || exit 1
  printf '{"scripts":{"lint":"true"}}\n' >package.json
  git add package.json
  git commit -qm node-marker
)
check "gate reports skipped node when package.json exists and node is missing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: node (not installed)' <<<\"\$out\""

setup_gate_fixture gate-all-skips
(
  cd "$GATE_REPO" || exit 1
  mkdir -p tests
  printf '{"scripts":{"lint":"true"}}\n' >package.json
  printf '[project]\nname = "fixture"\n' >pyproject.toml
  printf 'fn main() {}\n' >Cargo.toml
  printf 'module example.com/fixture\n' >go.mod
  printf 'def test_fixture():\n    assert True\n' >tests/test_fixture.py
  printf '#!/usr/bin/env bash\ntrue\n' >script.sh
  git add -A
  git commit -qm all-markers
)
check "gate reports skipped lines for every missing guarded tool" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); for tool in node ruff pytest shellcheck cargo go; do grep -Fq \"⊘ skipped: \$tool (not installed)\" <<<\"\$out\" || exit 1; done"

setup_gate_fixture gate-shell-only
(
  cd "$GATE_REPO" || exit 1
  printf '#!/usr/bin/env bash\ntrue\n' >script.sh
  git add script.sh
  git commit -qm shell-only
)
check "gate does not report absent cargo go or node in shell-only repo" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); ! grep -Eq 'skipped: (cargo|go|node)' <<<\"\$out\""

setup_gate_fixture gate-python-no-tests
(
  cd "$GATE_REPO" || exit 1
  printf '[project]\nname = "fixture"\n' >pyproject.toml
  git add pyproject.toml
  git commit -qm python-no-tests
)
check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""

setup_gate_fixture gate-node-runs
write_fake_tool "$GATE_BIN/node"
write_fake_tool "$GATE_BIN/npm"
(
  cd "$GATE_REPO" || exit 1
  printf '{"scripts":{"lint":"true"}}\n' >package.json
  git add package.json
  git commit -qm node-runs
)
check "gate does not report skipped node when node check runs" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '▶ npm run --silent lint' <<<\"\$out\" && ! grep -Fq 'skipped: node' <<<\"\$out\""

setup_gate_fixture gate-tsc-fallback
write_fake_node "$GATE_BIN/node"
write_fake_tool "$GATE_BIN/npm"
write_fake_tool "$GATE_BIN/npx"
(
  cd "$GATE_REPO" || exit 1
  printf '{"scripts":{"lint":"true"}}\n' >package.json
  printf '{}\n' >tsconfig.json
  git add package.json tsconfig.json
  git commit -qm tsc-fallback
)
check "gate runs tsc --noEmit when TS project has no typecheck script" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '▶ npx --no-install tsc --noEmit' <<<\"\$out\" && ! grep -Fq 'skipped: tsc' <<<\"\$out\""

setup_gate_fixture gate-tsc-has-script
write_fake_node "$GATE_BIN/node"
write_fake_tool "$GATE_BIN/npm"
write_fake_tool "$GATE_BIN/npx"
(
  cd "$GATE_REPO" || exit 1
  printf '{"scripts":{"typecheck":"tsc --noEmit"}}\n' >package.json
  printf '{}\n' >tsconfig.json
  git add package.json tsconfig.json
  git commit -qm tsc-has-script
)
check "gate does not add tsc fallback when a typecheck script exists" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '▶ npm run --silent typecheck' <<<\"\$out\" && ! grep -Fq 'tsc --noEmit' <<<\"\$out\" && ! grep -Fq 'skipped: tsc' <<<\"\$out\""

setup_gate_fixture gate-tsc-missing

 succeeded in 0ms:
    cat >"$FAN_IMPL" <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
cat >/dev/null
branch=$(git branch --show-current)
git config user.email tester@example.com
git config user.name Tester
if [[ ! -f work/demo/plan.md ]]; then
  printf 'missing-seed\n' >result.txt
elif [[ "${FAN_PASS_MODE:-some}" == all-fail ]]; then
  printf 'fail\n' >result.txt
elif [[ "$branch" == wt/demo-fan-2 || "$branch" == wt/demo-fan-3 ]]; then
  printf 'pass\n' >result.txt
else
  printf 'fail\n' >result.txt
fi
printf '%s\n' "$branch" >branch.txt
if [[ "${FAN_COMMIT_MODE:-commit}" == commit ]]; then
  git add result.txt branch.txt
  git commit -qm "implement $branch"
fi
EOF
    chmod +x "$FAN_IMPL"

    cat >config.yaml <<EOF
implementer:
  command: 'FAN_PASS_MODE=$pass_mode FAN_COMMIT_MODE=$commit_mode $FAN_IMPL'
worktrees:
  dir: $FAN_WTS
EOF
    git add config.yaml scripts
    git commit -qm init
    git push -q -u origin main
    printf '# Demo plan\n' >work/demo/plan.md
    printf 'handoff\n' >work/demo/handoff.md
  )
}

setup_gate_fixture() {
  local name="$1"
  local tmp_root="$TMP/$name"

  GATE_REPO="$tmp_root/repo"
  GATE_BIN="$tmp_root/bin"
  mkdir -p "$GATE_REPO/scripts" "$GATE_BIN"
  git init -q -b main "$GATE_REPO"
  (
    cd "$GATE_REPO" || exit 1
    git config user.email tester@example.com
    git config user.name Tester
    cp "$ROOT/scripts/gate.sh" scripts/gate.sh
    git add -A
    git commit -qm init
  )
  ln -sf "$(command -v bash)" "$GATE_BIN/bash"
  ln -sf "$(command -v git)" "$GATE_BIN/git"
  ln -sf "$(command -v awk)" "$GATE_BIN/awk"
}

setup_state_fixture() {
  local name="$1"
  local mode="$2"
  local tmp_root="$TMP/$name"

  STATE_REPO="$tmp_root/repo"
  mkdir -p "$STATE_REPO/scripts" "$STATE_REPO/work/demo"
  git init -q -b main "$STATE_REPO"
  (
    cd "$STATE_REPO" || exit 1
    git config user.email tester@example.com
    git config user.name Tester
    cp "$ROOT/scripts/state.sh" scripts/state.sh
    chmod +x scripts/state.sh

    case "$mode" in
      missing-plan)
        ;;
      plan)
        printf '# Demo\n\n' >work/demo/plan.md
        ;;
      implement)
        printf '# Demo\n\nPlan verdict: APPROVE\n' >work/demo/plan.md
        ;;
      review-gate)
        printf '# Demo\n\nPlan verdict: APPROVE\n' >work/demo/plan.md
        printf 'handoff\n' >work/demo/handoff.md
        ;;
      review-single-sentinel)
        {
          printf '# Demo\n\n'
          printf 'Plan verdict: APPROVE\n'
          printf 'Code-review verdict: APPROVE\n'
        } >work/demo/plan.md
        printf 'handoff\n' >work/demo/handoff.md
        printf 'codex review\n' >work/demo/codex-review.md
        ;;
      release)
        {
          printf '# Demo\n\n'
          printf 'Plan verdict: APPROVE\n'
          printf 'Code-review verdict: APPROVE\n'
          printf 'Codex-review verdict: APPROVE\n'
        } >work/demo/plan.md
        printf 'handoff\n' >work/demo/handoff.md
        printf 'codex review\n' >work/demo/codex-review.md
        ;;
      retro)
        {
          printf '# Demo\n\n'
          printf 'Plan verdict: APPROVE\n'
          printf 'Code-review verdict: APPROVE\n'
          printf 'Codex-review verdict: APPROVE\n'
        } >work/demo/plan.md
        printf 'handoff\n' >work/demo/handoff.md
        printf 'codex review\n' >work/demo/codex-review.md
        printf ' demo \n' >work/.last-released
        ;;
      done)
        {
          printf '# Demo\n\n'
          printf 'Plan verdict: APPROVE\n'

exec
/bin/zsh -lc "nl -ba ARCHI.md | sed -n '1,70p'" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
     1	# Architecture
     2	
     3	_A snapshot of what the codebase IS — regenerated by `/init` and `/compact`, never hand-groomed._
     4	
     5	## Stack
     6	
     7	Python 3.12 (`src/` layout) for the research code, plus the agentic-coding harness (Bash `set -uo pipefail` scripts + Markdown skills/agents) as the development machinery. The first research slice is the fixed-budget reference bootstrap and deterministic synthetic battery. The implementer runtime is Codex (`config.yaml`); reviewers are Claude (`opus`) plus a Codex second reviewer. Profile: `machine-learning`.
     8	
     9	## Layout
    10	
    11	- `CLAUDE.md` / `ARCHI.md` / `PLAN.md` — the hot context tier (loaded every session, ~300-line budget).
    12	- `config.yaml` — the single knob: `profile: machine-learning`, per-role models, implementer runtime (`codex`), gate command + required tools (`shellcheck`), worktree dir (`../adaptive-compute-worktrees`).
    13	- `src/adaptive_compute/` — the Python package. `metrics.py` implements numpy-only AUC and paired `Δ`; `generators.py` holds the five-member frozen synthetic battery; `bootstrap.py` is the paired row-resampler with exact draw accounting and `SeedSequence.spawn` branches; `reference.py` is the fixed-budget percentile-bootstrap decision; `adaptive.py` is the blind adaptive bootstrap controller with an empirical-Bernstein confidence sequence; `sweep.py` holds fixed-B sweep and Pareto helpers; `benchmark.py` runs the offline first-result harness; `strata.py` classifies plug-in `Δ(E)` difficulty; `eval.py` exposes `python -m adaptive_compute.eval`.
    14	- `tests/` — `test_smoke.py` (package-import smoke test), `test-scripts.sh` (the harness's shell smoke suite), and fixed-budget reference tests for metrics, generators, bootstrap determinism/accounting, reference decisions, and eval-check failure behavior.
    15	- `pyproject.toml` — package metadata + numpy runtime dependency + tool config: ruff (lint `E,F,I` + format), pytest (`pythonpath=["src"]`), mypy.
    16	- `skills/` — the loop stages (`1-plan`…`5-retro`) plus `init` and `compact`; exposed to Claude Code via the `.claude/skills → ../skills` symlink.
    17	- `.claude/agents/` — fresh-subagent reviewers (`plan-reviewer`, `code-reviewer`, `fan-selector`): read-only tools, separate model, cold context.
    18	- `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
    19	- `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
    20	- `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
    21	- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
    22	- `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
    23	- `AGENTS.md` — the implementer's contract.
    24	
    25	## Entry points
    26	
    27	- **The loop:** `/1-plan` → `/2-implement` → `/3-review` → `/4-release` → `/5-retro`, invoked as skills from the orchestrator session.
    28	- **`scripts/gate.sh`** — run from anywhere; `cd`s to repo root, auto-detects stacks (here: Python + Shell), runs applicable checks + `gate.d/*.sh` hooks. Exit 0 = pass.
    29	- **`python -m adaptive_compute.eval --run`** — offline adaptive benchmark path; writes `work/adaptive-procedure/results.md` and `results.json` outside the fast gate.
    30	- **`scripts/release.sh <slug>`** / **`worktree.sh`** / **`agent-exec.sh`** / **`state.sh`** — as documented in the harness, with one local divergence: `release.sh tag-after-merge` locates the release commit by its `VERSION` transition on `origin/main` and tags that SHA (not the branch tip), so merge-commit / squash / non-ff PR merges tag correctly. The current-version guard (`origin/main:VERSION` must equal the release version) is retained.
    31	
    32	## Conventions
    33	
    34	- **Writer never reviews.** Reviews come only from fresh `.claude/agents/` subagents (read-only, separate model).
    35	- **The gate and release are scripts, and authoritative.** Never overrule `gate.sh` or `release.sh`.
    36	- **Implementation happens in worktrees, never in this checkout.** Use `worktree.sh`.
    37	- Vendor/model names live only in `config.yaml`.
    38	- All shell scripts must pass `shellcheck`; Python must pass `ruff check`, `ruff format --check`, `mypy src`, and `pytest` (enforced by the gate).
    39	- **Notebooks are exploratory-only** (`machine-learning` profile): correctness-critical logic moves to a `.py` module under the gate; tracked notebooks must be output-stripped (`nb-clean.sh` enforces this once any `*.ipynb` is tracked).
    40	
    41	## Verification
    42	
    43	`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
    44	
    45	### ML profile declarations
    46	
    47	- **EVAL_METRIC** — RESOLVED as the adaptive first-result suite: decision agreement against the fixed-budget reference, per-stratum false-stop rate with binomial CI, draws consumed (p50/p90/p99), abstain rate, reference-unresolved count, and fixed-B Pareto/savings comparison.
    48	- **GROUND_TRUTH_SOURCE** — RESOLVED for this unit. Synthetic cases use the plug-in `Δ(E) = M(A,E) - M(B,E)` computed once on the frozen generated evaluation set for strata and expected-decision checks. The fixed-budget reference is labelled as the full-budget same-procedure conclusion, not truth.
    49	- **EVAL_COMMAND** — `python -m adaptive_compute.eval --check`, wired through `scripts/gate.d/eval.sh`; `python -m adaptive_compute.eval --run` is the offline result-producing command.
    50	- **DATA_REGIME** — RESOLVED for this unit. Offline, fixed evaluation sets from the five-member synthetic generator battery: near-δ-boundary, small-effect, heavy-tailed, rare-event/imbalance, and easy/lopsided. No streaming, no added data.
    51	- **NOTEBOOK_STRATEGY** — Exploratory-only, single-author under `notebooks/<initials>/`. `nb-clean.sh` enabled (no-op until a notebook is tracked).
    52	- **REPO_HYGIENE** — `ds-hygiene.sh` enabled with defaults (`DS_DATA_MAX_BYTES=1048576`, `DS_DATA_ALLOW_DIRS=tests/fixtures`, `DS_PATH_SCAN=1`).

codex
The existing `run` helper already gives the exact `▶` and `✗ FAILED` format the plan wants for the retry, so I can add a focused `run_pytest` helper in the Python block and leave the rest of the script alone. I’m reading a bit more of the gate test section now to place the new fixture cases beside the existing gate coverage.
exec
/bin/zsh -lc "sed -n '1285,1405p' tests/test-scripts.sh" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
exec
/bin/zsh -lc "sed -n '1,120p' tests/test-scripts.sh" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
setup_gate_fixture gate-tsc-missing
write_fake_node "$GATE_BIN/node"
write_fake_tool "$GATE_BIN/npm"
(
  cd "$GATE_REPO" || exit 1
  printf '{"scripts":{"lint":"true"}}\n' >package.json
  printf '{}\n' >tsconfig.json
  git add package.json tsconfig.json
  git commit -qm tsc-missing
)
check "gate reports skipped tsc when TS project has no typecheck script and tsc is absent" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: tsc (not installed)' <<<\"\$out\""

setup_gate_fixture gate-required-present
write_fake_tool "$GATE_BIN/fixturetool"
check "gate required tool passes when fake executable is on PATH" bash -c "cd '$GATE_REPO' && GATE_REQUIRED_TOOLS=fixturetool PATH='$GATE_BIN' bash scripts/gate.sh"

setup_gate_fixture gate-required-missing
check "gate required tool fails and names missing executable" bash -c "cd '$GATE_REPO' && out=\$(GATE_REQUIRED_TOOLS=fixturetool PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq 'fixturetool' <<<\"\$out\""

setup_gate_fixture gate-required-two-missing
check "gate required tool preflight reports every missing executable" bash -c "cd '$GATE_REPO' && out=\$(GATE_REQUIRED_TOOLS=one:two PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq 'one' <<<\"\$out\" && grep -Fq 'two' <<<\"\$out\""

setup_gate_fixture gate-required-no-run-lines
write_fake_tool "$GATE_BIN/node"
write_fake_tool "$GATE_BIN/npm"
(
  cd "$GATE_REPO" || exit 1
  printf '{"scripts":{"lint":"true"}}\n' >package.json
  git add package.json
  git commit -qm node-marker
)
check "gate required tool preflight aborts before stack checks" bash -c "cd '$GATE_REPO' && out=\$(GATE_REQUIRED_TOOLS=missingtool PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && ! grep -Fq '▶' <<<\"\$out\""

setup_gate_fixture gate-no-config
check "gate runs without config.yaml or GATE_REQUIRED_TOOLS" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && ! grep -Fq 'config.yaml' <<<\"\$out\""

setup_gate_fixture gate-env-overrides-config
write_fake_tool "$GATE_BIN/presenttool"
(
  cd "$GATE_REPO" || exit 1
  printf 'gate:\n  required_tools: missing_from_config\n' >config.yaml
  git add config.yaml
  git commit -qm config
)
check "gate uses GATE_REQUIRED_TOOLS instead of config required_tools" bash -c "cd '$GATE_REPO' && GATE_REQUIRED_TOOLS=presenttool PATH='$GATE_BIN' bash scripts/gate.sh"

setup_gate_fixture gate-config-required
(
  cd "$GATE_REPO" || exit 1
  printf 'gate:\n  required_tools: configtool\n' >config.yaml
  git add config.yaml
  git commit -qm config
)
check "gate reads required_tools from config.yaml" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq 'configtool' <<<\"\$out\""

setup_gate_fixture gate-commented-required
(
  cd "$GATE_REPO" || exit 1
  printf 'gate:\n  command: scripts/gate.sh\n  # required_tools: shellcheck\n' >config.yaml
  git add config.yaml
  git commit -qm config
)
check "gate ignores commented-out required_tools" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && ! grep -Fq 'missing required tool' <<<\"\$out\""

setup_gate_fixture gate-unrelated-required
(
  cd "$GATE_REPO" || exit 1
  printf 'gate:\n  command: scripts/gate.sh\nother:\n  required_tools: should_not_apply\n' >config.yaml
  git add config.yaml
  git commit -qm config
)
check "gate ignores required_tools outside gate section" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && ! grep -Fq 'should_not_apply' <<<\"\$out\""

setup_gate_fixture gate-empty-env-overrides-config
(
  cd "$GATE_REPO" || exit 1
  printf 'gate:\n  required_tools: shellcheck\n' >config.yaml
  git add config.yaml
  git commit -qm config
)
check "gate treats empty GATE_REQUIRED_TOOLS as no required tools" bash -c "cd '$GATE_REPO' && out=\$(GATE_REQUIRED_TOOLS= PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && ! grep -Fq 'missing required tool' <<<\"\$out\""

# --- agent-exec.sh argument validation
check_fails "agent-exec rejects missing handoff" bash scripts/agent-exec.sh /tmp nonexistent-handoff.md

setup_agent_exec_fixture agent-commit commit
check_exit "agent-exec exits 0 when implementer commits" 0 "" bash -c "cd '$AGENT_PRIMARY' && bash scripts/agent-exec.sh '$AGENT_WORKTREE' '$AGENT_HANDOFF'"

setup_agent_exec_fixture agent-relative-worktree commit
check_exit "agent-exec exits 0 with relative worktree path when implementer commits" 0 "" bash -c "cd '$AGENT_PRIMARY' && bash scripts/agent-exec.sh '../wts/demo-wt' '$AGENT_HANDOFF'"

setup_agent_exec_fixture agent-cd-elsewhere-commit cd-elsewhere-commit
check_exit "agent-exec exits 0 when implementer cd's elsewhere then commits" 0 "" bash -c "cd '$AGENT_PRIMARY' && bash scripts/agent-exec.sh '$AGENT_WORKTREE' '$AGENT_HANDOFF'"

setup_agent_exec_fixture agent-dirty dirty
check_exit "agent-exec exits 0 when implementer leaves uncommitted changes" 0 "" bash -c "cd '$AGENT_PRIMARY' && bash scripts/agent-exec.sh '$AGENT_WORKTREE' '$AGENT_HANDOFF'"

setup_agent_exec_fixture agent-predirty-clean predirty-clean
check_exit "agent-exec exits 0 when dirty redispatch cleans tree without commit" 0 "" bash -c "cd '$AGENT_PRIMARY' && bash scripts/agent-exec.sh '$AGENT_WORKTREE' '$AGENT_HANDOFF'"

setup_agent_exec_fixture agent-nothing nothing
check_exit "agent-exec exits non-zero when implementer produces nothing" 1 "no new commit" bash -c "cd '$AGENT_PRIMARY' && bash scripts/agent-exec.sh '$AGENT_WORKTREE' '$AGENT_HANDOFF'"

# --- opt-in notebook cleanliness hook
NB_REPO="$TMP/notebook-clean"
git init -q -b main "$NB_REPO"
(
  cd "$NB_REPO" || exit 1
  git config user.email tester@example.com
  git config user.name Tester
  mkdir -p scripts/gate.d notebooks/cb
  cp "$ROOT/scripts/gate.d/examples/nb-clean.sh" scripts/gate.d/nb-clean.sh
  cat >notebooks/cb/dirty.ipynb <<'EOF'
{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 7,
   "metadata": {},
   "outputs": [
    {

 succeeded in 0ms:
#!/usr/bin/env bash
# Smoke tests for the deterministic layer. Run from repo root: bash tests/test-scripts.sh
set -uo pipefail

pass=0; fail=0
check() {
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "ok: $desc"; pass=$((pass+1))
  else
    echo "FAIL: $desc"; fail=$((fail+1))
  fi
}
check_fails() {
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "FAIL: $desc (expected non-zero exit)"; fail=$((fail+1))
  else
    echo "ok: $desc"; pass=$((pass+1))
  fi
}
check_exit() {
  local desc="$1"
  local expected="$2"
  local stderr_substring="$3"
  shift 3
  local err
  local status

  err=$(mktemp)
  if "$@" >/dev/null 2>"$err"; then
    status=0
  else
    status=$?
  fi

  if [[ "$status" -eq "$expected" ]] \
    && { [[ -z "$stderr_substring" ]] || grep -Fq -- "$stderr_substring" "$err"; }; then
    echo "ok: $desc"; pass=$((pass+1))
  else
    echo "FAIL: $desc (exit $status, expected $expected; stderr: $(tr '\n' ' ' <"$err"))"
    fail=$((fail+1))
  fi
  rm -f "$err"
}

ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT" || exit 1

# This suite runs nested inside scripts/gate.sh (via the gate.d/ hook), so an inherited
# value would reach every fixture gate and abort it. Keep this here, not beside the gate
# cases — a guard that works only because of where it sits is lost by the next case
# added above it. See knowledge/test-helper-contract.md.
unset GATE_REQUIRED_TOOLS

commit_fixture() {
  local repo="$1"
  local stamp="$2"
  local msg="$3"

  (
    cd "$repo" || exit 1
    git add -A
    GIT_AUTHOR_DATE="$stamp" GIT_COMMITTER_DATE="$stamp" git commit -qm "$msg"
  )
}

write_release_fixture_date() {
  local bin_dir="$1"
  local ym="$2"
  local ymd="$3"

  mkdir -p "$bin_dir"
  cat >"$bin_dir/date" <<EOF
#!/usr/bin/env bash
case "\${1:-}" in
  +%Y.%-m) printf '%s\n' "$ym" ;;
  +%F) printf '%s\n' "$ymd" ;;
  *) /bin/date "\$@" ;;
esac
EOF
  chmod +x "$bin_dir/date"
}

setup_release_fixture() {
  local name="$1"
  local version="$2"
  local verdict_line="$3"
  local gate_mode="$4"
  local archi_mode="$5"
  local codex_verdict_line="${6-Codex-review verdict: APPROVE}"
  local marker_slug="${7-}"
  local retro_content="${8-__missing__}"
  local tmp_root="$TMP/$name"

  REL_PRIMARY="$tmp_root/primary"
  REL_WORKTREE="$tmp_root/demo-wt"
  REL_REMOTE="$tmp_root/remote.git"
  REL_FAKEBIN="$tmp_root/bin"

  mkdir -p "$tmp_root"
  git init -q -b main "$REL_PRIMARY"
  git init -q --bare "$REL_REMOTE"
  (
    cd "$REL_PRIMARY" || exit 1
    git config user.email tester@example.com
    git config user.name Tester
    git remote add origin "$REL_REMOTE"

    mkdir -p scripts skills/3-review skills/1-plan/prompts work/demo
    cp "$ROOT/scripts/release.sh" scripts/release.sh
    cp "$ROOT/scripts/archi-fresh.sh" scripts/archi-fresh.sh
    cat >scripts/gate.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
if [[ -f GATE_FAIL ]]; then
  echo "GATE: FAIL"
  exit 1
fi

exec
/bin/zsh -lc 'rg -n "write_fake|check_exit|check_fails|gate-" tests/test-scripts.sh' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
14:check_fails() {
22:check_exit() {
699:write_fake_tool() {
711:write_fake_node() {
739:check_exit "archi-fresh passes when ARCHI is newer than source paths" 0 "" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"
742:check_exit "archi-fresh reports stale source paths" 1 "skills/" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"
743:check_exit "archi-fresh stale message says to refresh branch ARCHI" 1 "refresh ARCHI on the branch" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"
746:check_exit "archi-fresh treats equal epochs as fresh" 0 "" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"
749:check_exit "archi-fresh default ref checks current branch history" 0 "" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"
750:check_exit "archi-fresh explicit ref selects branch history" 1 "skills/" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh wt/demo"
753:check_exit "archi-fresh exits 2 when one side has no history" 2 "ARCHI.md has no git history" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"
763:check_exit "state missing plan exits non-zero" 1 "not a work unit" bash -c "cd '$STATE_REPO' && bash scripts/state.sh demo"
865:check_exit "codex-review approve exits 0" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
869:check_exit "codex-review accepts indented approve verdict" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
872:check_exit "codex-review request-changes exits 1" 1 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
875:check_exit "codex-review ignores branch reviewer.command override" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
878:check_exit "codex-review missing verdict exits 2" 2 "no verdict" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
881:check_exit "codex-review missing reviewer.command exits 2" 2 "reviewer.command" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
884:check_exit "codex-review parser stops before later command" 2 "reviewer.command" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
887:check_exit "codex-review ignores commented command and uses real one" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
890:check_exit "codex-review missing branch plan exits 2 before reviewer" 2 "cannot read plan" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
895:check_exit "codex-review reviewer failure exits 2 before verdict parsing" 2 "reviewer command failed (exit 42)" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
901:check_exit "codex-review refuses wt checkout as root" 2 "primary checkout" bash -c "cd '$COD_WORKTREE' && bash '$COD_PRIMARY/scripts/codex-review.sh' demo"
904:check_exit "codex-review artifact-only run exits 0" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
915:check_exit "codex-review with branch artifacts exits 0" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
920:check_exit "codex-review from subdirectory exits 0" 0 "" bash -c "cd '$COD_PRIMARY/subdir' && bash ../scripts/codex-review.sh demo"
940:check_exit "codex-review with a deferral ledger exits 0" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
953:check_exit "codex-review passes custom round number" 0 "" bash -c "cd '$COD_PRIMARY' && REVIEW_ROUND=3 bash scripts/codex-review.sh demo"
959:check_exit "codex-review excludes origin-main-only changes" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
967:check_exit "codex-review falls back to local main without origin/main" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
988:check_fails "worktree add without slug fails" bash -c "cd '$SB' && bash wt.sh add"
1099:check_exit "worktree sync-artifacts without slug fails" 1 "usage: worktree.sh sync-artifacts <slug>" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts"
1101:check_exit "worktree sync-artifacts refuses missing worktree" 1 "no worktree for no-wt" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts no-wt"
1107:check_exit "worktree sync-artifacts refuses missing primary work dir" 1 "primary checkout has no work/no-primary directory" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts no-primary"
1108:check_exit "worktree sync-artifacts refuses invocation from unit worktree" 1 "sync-artifacts must run from the primary checkout" bash -c "cd '$SYNC_WORKTREE' && bash scripts/worktree.sh sync-artifacts demo"
1112:check_exit "worktree sync-artifacts copies primary artifacts" 0 "" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
1138:check_exit "worktree sync-artifacts idempotent no-op exits zero" 0 "" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
1142:check_exit "worktree sync-artifacts refreshes changed artifact" 0 "" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
1147:check_exit "worktree sync-artifacts leaves pending worktree plan edit uncommitted" 0 "" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
1157:check_exit "worktree sync-artifacts ignores unrelated staged files" 0 "" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
1167:check_exit "worktree sync-artifacts leaves unrelated unstaged edit alone" 0 "" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
1180:check_fails "worktree sync-artifacts propagates a failed artifact commit" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
1185:check_exit "worktree sync-artifacts accepts primary checkout on non-main branch" 0 "" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
1199:check_exit "worktree sync-artifacts refuses expected path on wrong branch" 1 "no worktree for demo" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
1206:setup_gate_fixture gate-node-missing
1215:setup_gate_fixture gate-all-skips
1230:setup_gate_fixture gate-shell-only
1239:setup_gate_fixture gate-python-no-tests
1248:setup_gate_fixture gate-node-runs
1249:write_fake_tool "$GATE_BIN/node"
1250:write_fake_tool "$GATE_BIN/npm"
1259:setup_gate_fixture gate-tsc-fallback
1260:write_fake_node "$GATE_BIN/node"
1261:write_fake_tool "$GATE_BIN/npm"
1262:write_fake_tool "$GATE_BIN/npx"
1272:setup_gate_fixture gate-tsc-has-script
1273:write_fake_node "$GATE_BIN/node"
1274:write_fake_tool "$GATE_BIN/npm"
1275:write_fake_tool "$GATE_BIN/npx"
1285:setup_gate_fixture gate-tsc-missing
1286:write_fake_node "$GATE_BIN/node"
1287:write_fake_tool "$GATE_BIN/npm"
1297:setup_gate_fixture gate-required-present
1298:write_fake_tool "$GATE_BIN/fixturetool"
1301:setup_gate_fixture gate-required-missing
1304:setup_gate_fixture gate-required-two-missing
1307:setup_gate_fixture gate-required-no-run-lines
1308:write_fake_tool "$GATE_BIN/node"
1309:write_fake_tool "$GATE_BIN/npm"
1318:setup_gate_fixture gate-no-config
1321:setup_gate_fixture gate-env-overrides-config
1322:write_fake_tool "$GATE_BIN/presenttool"
1331:setup_gate_fixture gate-config-required
1340:setup_gate_fixture gate-commented-required
1349:setup_gate_fixture gate-unrelated-required
1358:setup_gate_fixture gate-empty-env-overrides-config
1368:check_fails "agent-exec rejects missing handoff" bash scripts/agent-exec.sh /tmp nonexistent-handoff.md
1371:check_exit "agent-exec exits 0 when implementer commits" 0 "" bash -c "cd '$AGENT_PRIMARY' && bash scripts/agent-exec.sh '$AGENT_WORKTREE' '$AGENT_HANDOFF'"
1374:check_exit "agent-exec exits 0 with relative worktree path when implementer commits" 0 "" bash -c "cd '$AGENT_PRIMARY' && bash scripts/agent-exec.sh '../wts/demo-wt' '$AGENT_HANDOFF'"
1377:check_exit "agent-exec exits 0 when implementer cd's elsewhere then commits" 0 "" bash -c "cd '$AGENT_PRIMARY' && bash scripts/agent-exec.sh '$AGENT_WORKTREE' '$AGENT_HANDOFF'"
1380:check_exit "agent-exec exits 0 when implementer leaves uncommitted changes" 0 "" bash -c "cd '$AGENT_PRIMARY' && bash scripts/agent-exec.sh '$AGENT_WORKTREE' '$AGENT_HANDOFF'"
1383:check_exit "agent-exec exits 0 when dirty redispatch cleans tree without commit" 0 "" bash -c "cd '$AGENT_PRIMARY' && bash scripts/agent-exec.sh '$AGENT_WORKTREE' '$AGENT_HANDOFF'"
1386:check_exit "agent-exec exits non-zero when implementer produces nothing" 1 "no new commit" bash -c "cd '$AGENT_PRIMARY' && bash scripts/agent-exec.sh '$AGENT_WORKTREE' '$AGENT_HANDOFF'"
1438:check_fails "notebook hook flags dirty tracked notebook" bash -c "cd '$NB_REPO' && bash scripts/gate.d/nb-clean.sh"
1458:check_exit "ds hygiene hook flags oversized tracked artifact" 1 "data/too-big.parquet" bash -c "cd '$DS_REPO' && DS_DATA_MAX_BYTES=10 bash scripts/gate.d/ds-hygiene.sh"
1460:check_exit "ds hygiene hook treats empty allow dirs as no allowed dirs" 1 "tests/fixtures/allowed.csv" bash -c "cd '$DS_REPO' && DS_DATA_MAX_BYTES=10 DS_DATA_ALLOW_DIRS='' bash scripts/gate.d/ds-hygiene.sh"
1461:check_exit "ds hygiene hook flags Unix local path in Python" 1 "src/user_path.py" bash -c "cd '$DS_REPO' && DS_DATA_MAX_BYTES=1000 bash scripts/gate.d/ds-hygiene.sh"
1462:check_exit "ds hygiene hook flags Windows local path in Python" 1 "src/windows_path.py" bash -c "cd '$DS_REPO' && DS_DATA_MAX_BYTES=1000 bash scripts/gate.d/ds-hygiene.sh"
1463:check_exit "ds hygiene hook still flags artifact when path scan is disabled" 1 "data/too-big.parquet" bash -c "cd '$DS_REPO' && DS_DATA_MAX_BYTES=10 DS_PATH_SCAN='' bash scripts/gate.d/ds-hygiene.sh"
1464:check_exit "ds hygiene hook still flags local path when artifact scan is disabled" 1 "src/user_path.py" bash -c "cd '$DS_REPO' && DS_DATA_MAX_BYTES='' bash scripts/gate.d/ds-hygiene.sh"
1569:check_exit "ds hygiene hook ignores empty allow-dir prefix" 1 "data/raw/outside.csv" bash -c "cd '$DS_EMPTY_PREFIX_REPO' && DS_DATA_MAX_BYTES=10 DS_DATA_ALLOW_DIRS=':data/samples' bash scripts/gate.d/ds-hygiene.sh"
1624:fan_dirty_gate_manifest="$TMP/fan-dirty-gate-manifest.out"
1648:check_fails "release version compare rejects .9 after .10" bash scripts/release.sh check-version 2026.8.9 2026.8.10
1652:check_fails "release refuses without code-review approval" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"
1655:check_exit "release refuses without codex-review approval" 1 "Codex-review verdict: APPROVE" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"
1657:setup_release_fixture release-gate-fails 2026.8.9 "Code-review verdict: APPROVE" fail fresh
1658:check_fails "release refuses when gate fails" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"
1661:check_fails "release refuses when ARCHI.md is stale" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"
1664:check_fails "release refuses when computed version does not exceed VERSION" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"
1716:check_exit "release refuses marker with missing retro" 1 "has no retro.md" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"
1719:check_exit "release refuses marker with empty retro" 1 "has no retro.md" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"
1734:check_exit "release refuses deleted last-released marker" 1 "marker deleted" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"
1745:check_exit "release refuses mutated last-released marker" 1 "marker differs" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"
1755:check_exit "release refuses symlinked last-released marker" 1 "marker is a symlink" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"
1764:check_exit "release refuses last-released marker with extra trailing newline" 1 "marker differs" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"
1767:check_exit "release re-run on release branch names merge guidance" 1 "merge its PR instead of re-running release" bash -c "
1780:check_exit "release refuses empty bootstrap last-released marker" 1 "malformed" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"
1789:check_exit "release refuses multi-line bootstrap last-released marker" 1 "malformed" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"
1799:check_exit "release refuses symlinked bootstrap last-released marker" 1 "marker is a symlink" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"

codex
I’ve got the shape: new tests can sit right after the existing “python no tests” fixture, since these specifically pin the Python/pytest path. I’m going to patch only `scripts/gate.sh`, that test block, and the two ARCHI lines the handoff names.
exec
/bin/zsh -lc "sed -n '680,725p' tests/test-scripts.sh" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
        git branch wt/demo
        printf '# Demo\n\nPlan verdict: APPROVE\n' >work/demo/plan.md
        ;;
      *)
        echo "unknown state fixture mode: $mode" >&2
        exit 1
        ;;
    esac

    if [[ "$mode" != branch-approve ]]; then
      git add -A
      git commit -qm "$mode"
    else
      git add work/demo/plan.md
      git commit -qm primary-plan
    fi
  )
}

write_fake_tool() {
  local path="$1"
  mkdir -p "$(dirname "$path")"
  cat >"$path" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
  chmod +x "$path"
}
# A node stand-in that honors the gate's `node -e "... scripts?.['x'] ..."`
# probe by checking package.json, so the typecheck-fallback path is testable
# without a real node toolchain. Any other invocation exits 0.
write_fake_node() {
  local path="$1"
  mkdir -p "$(dirname "$path")"
  # Pure-bash: the restricted test PATH has no grep/tr/cat.
  cat >"$path" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "-e" ]]; then
  key=${2#*\[\'}     # strip up to the opening ['
  key=${key%%\'\]*}  # strip from '] onward -> the script name
  pkg=$(<package.json)
  [[ "$pkg" == *"\"$key\""* ]] && exit 0 || exit 1
fi
exit 0
EOF
  chmod +x "$path"

codex
One small implementation detail I’m preserving carefully: the helper itself prints the first `▶ pytest -q`, so it can capture the raw exit code before `run` would collapse it into `fail=1`. Only the signal retry goes back through `run`, which keeps existing output behavior for the final attempt.
apply patch
patch: completed
/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience/scripts/gate.sh
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi

diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi

codex
The gate helper is in place. Next I’m adding fixture coverage that exercises the exact outputs and retry counts, including the real `kill -SEGV $$` path rather than only a synthetic exit code.
apply patch
patch: completed
/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience/tests/test-scripts.sh
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..098d4fd71c5251823e739215e0cd77dceaaf9e94
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]]"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..098d4fd71c5251823e739215e0cd77dceaaf9e94
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]]"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
The five fixture cases are added with absolute log paths and marker files so the pytest block actually runs. I’m updating the ARCHI snapshot now: one layout line for `knowledge/`, and one verification line to mention the signal retry.
exec
/bin/zsh -lc 'rg --files knowledge' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
knowledge/controlled-retest-discipline.md
knowledge/bootstrap-seed-and-determinism.md
knowledge/shell-argument-safety.md
knowledge/equivalence-band-savings.md
knowledge/README.md
knowledge/research-doc-citations.md
knowledge/anytime-valid-band.md
knowledge/release-tagging.md

exec
/bin/zsh -lc 'git diff -- scripts/gate.sh tests/test-scripts.sh' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf04870..1067f3a 100755
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@ run() {
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@ if [[ -f pyproject.toml || -f setup.py || -f requirements.txt ]]; then
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb4..098d4fd 100755
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@ setup_gate_fixture gate-python-no-tests
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]]"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..098d4fd71c5251823e739215e0cd77dceaaf9e94
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]]"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
I noticed one acceptance nuance while looking at the diff: the handoff asks for exact retry log contents across the new cases, so I’m tightening the persistent-crash assertion too before I run anything. Small, but it’s the kind of small that keeps future us out of a review loop.
apply patch
patch: completed
/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience/tests/test-scripts.sh
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
Now I’m applying the ARCHI edits. They’re deliberately narrow: just replacing the stale “empty but for README” phrase and expanding the pytest verification sentence.
apply patch
patch: completed
/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience/ARCHI.md
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
The implementation pieces are in place. I’m starting verification with the shell smoke suite first, because it directly exercises the five new gate fixtures and tends to catch quoting problems quickly.
exec
/bin/zsh -lc 'bash tests/test-scripts.sh' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
The new fixture cases have all passed inside `tests/test-scripts.sh`, including the real signal-death one. The suite is still running through the later release fixtures, so I’m waiting for its final tally before moving on.
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
Still healthy; the shell suite is in the tail end now. After it finishes, I’ll run `archi-fresh.sh`, then the full gate with no pytest workaround env vars and watch whether the warning retry appears.
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
The smoke suite has gone quiet for a bit after the tag-after-merge checks. I’m giving it a little more time rather than interrupting, because these later Git fixtures can be chatty in setup and silent while they work.
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
It’s been silent long enough that I’m checking the running process tree instead of guessing. If it’s stuck in a fixture, I’ll identify the exact command before deciding how to proceed.
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
The sandbox won’t allow `ps`, so I can’t inspect the process tree directly. I’m going to wait once more; if it remains silent, I’ll interrupt this smoke-suite run and rerun the required commands through the full gate, which will exercise the same suite under the official path.
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
That standalone smoke-suite run appears hung after several quiet minutes, so I’m interrupting it rather than letting it sit open. I’ll still run the required gate from the repo root before finishing, and I’ll handle any real failure there instead of papering over it.
2026-09-23T12:33:33.011139Z ERROR codex_core::tools::router: error=write_stdin failed: stdin is closed for this session; rerun exec_command with tty=true to keep stdin open
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
The session’s stdin is already closed, so a normal Ctrl-C isn’t available. I’m going to terminate that hung smoke-suite process by pattern, then continue with fresh verification runs.
exec
/bin/zsh -lc "pkill -f 'bash tests/test-scripts.sh' || true" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
sysmon request failed with error: sysmond service not found
pkill: Cannot get process list

diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
Process termination is also blocked by the sandbox’s process-list restriction. I’m moving on with independent verification commands; the previous session may eventually age out, but it’s no longer producing useful signal.
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
Before running the full gate, I’m checking the tail of `tests/test-scripts.sh` to see what comes after the point where the standalone run went quiet. That should tell me whether this was a known slow Git-path case or something newly introduced.
exec
/bin/zsh -lc "sed -n '1800,1905p' tests/test-scripts.sh" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
exec
/bin/zsh -lc 'tail -n 80 tests/test-scripts.sh' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
    exit 1
  fi
  grep -q 'rolled back' \"\$rollback_out\" &&
  [ ! -e work/.last-released ] &&
  [ \"\$(git status --porcelain)\" = '' ]
"

setup_release_fixture release-prev-no-retro 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous
check_exit "release refuses marker with missing retro" 1 "has no retro.md" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"

setup_release_fixture release-prev-empty-retro 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous ""
check_exit "release refuses marker with empty retro" 1 "has no retro.md" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"

setup_release_fixture release-prev-retro 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous "learned"
check "release proceeds when previous retro is non-empty" bash -c "
  cd '$REL_WORKTREE' &&
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo &&
  [ \"\$(cat work/.last-released)\" = demo ]
"

setup_release_fixture release-marker-deleted 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous "learned"
(
  cd "$REL_WORKTREE" || exit 1
  git rm -q work/.last-released
  GIT_AUTHOR_DATE="2026-08-16T10:00:30Z" GIT_COMMITTER_DATE="2026-08-16T10:00:30Z" git commit -qm "delete marker"
)
check_exit "release refuses deleted last-released marker" 1 "marker deleted" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"

setup_release_fixture release-marker-mutated 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous "learned"
(
  cd "$REL_WORKTREE" || exit 1
  mkdir -p work/other
  printf 'other\n' >work/.last-released
  printf 'learned\n' >work/other/retro.md
  git add work/.last-released work/other/retro.md
  GIT_AUTHOR_DATE="2026-08-16T10:00:30Z" GIT_COMMITTER_DATE="2026-08-16T10:00:30Z" git commit -qm "mutate marker"
)
check_exit "release refuses mutated last-released marker" 1 "marker differs" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"

setup_release_fixture release-marker-symlink 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous "learned"
(
  cd "$REL_WORKTREE" || exit 1
  git show origin/main:work/.last-released >"$TMP/release-marker-symlink-target"
  ln -sf "$TMP/release-marker-symlink-target" work/.last-released
  git add work/.last-released
  GIT_AUTHOR_DATE="2026-08-16T10:00:30Z" GIT_COMMITTER_DATE="2026-08-16T10:00:30Z" git commit -qm "symlink marker"
)
check_exit "release refuses symlinked last-released marker" 1 "marker is a symlink" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"

setup_release_fixture release-marker-extra-newline 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous "learned"
(
  cd "$REL_WORKTREE" || exit 1
  printf 'previous\n\n' >work/.last-released
  git add work/.last-released
  GIT_AUTHOR_DATE="2026-08-16T10:00:30Z" GIT_COMMITTER_DATE="2026-08-16T10:00:30Z" git commit -qm "add marker newline"
)
check_exit "release refuses last-released marker with extra trailing newline" 1 "marker differs" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"

setup_release_fixture release-rerun-release-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous "learned"
check_exit "release re-run on release branch names merge guidance" 1 "merge its PR instead of re-running release" bash -c "
  cd '$REL_WORKTREE' &&
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo &&
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
"

setup_release_fixture release-bootstrap-empty-marker 2026.8.9 "Code-review verdict: APPROVE" pass fresh
(
  cd "$REL_WORKTREE" || exit 1
  : >work/.last-released
  git add work/.last-released
  GIT_AUTHOR_DATE="2026-08-16T10:00:30Z" GIT_COMMITTER_DATE="2026-08-16T10:00:30Z" git commit -qm "empty bootstrap marker"
)
check_exit "release refuses empty bootstrap last-released marker" 1 "malformed" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"

setup_release_fixture release-bootstrap-multiline-marker 2026.8.9 "Code-review verdict: APPROVE" pass fresh
(
  cd "$REL_WORKTREE" || exit 1
  printf 'previous\nother\n' >work/.last-released
  git add work/.last-released
  GIT_AUTHOR_DATE="2026-08-16T10:00:30Z" GIT_COMMITTER_DATE="2026-08-16T10:00:30Z" git commit -qm "multiline bootstrap marker"
)
check_exit "release refuses multi-line bootstrap last-released marker" 1 "malformed" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"

setup_release_fixture release-bootstrap-symlink-marker 2026.8.9 "Code-review verdict: APPROVE" pass fresh
(
  cd "$REL_WORKTREE" || exit 1
  printf 'previous\n' >"$TMP/release-bootstrap-symlink-target"
  ln -sf "$TMP/release-bootstrap-symlink-target" work/.last-released
  git add work/.last-released
  GIT_AUTHOR_DATE="2026-08-16T10:00:30Z" GIT_COMMITTER_DATE="2026-08-16T10:00:30Z" git commit -qm "symlink bootstrap marker"
)
check_exit "release refuses symlinked bootstrap last-released marker" 1 "marker is a symlink" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"

setup_release_fixture release-no-marker 2026.8.9 "Code-review verdict: APPROVE" pass fresh
check "release proceeds without last-released marker" bash -c "
  cd '$REL_WORKTREE' &&
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo &&
  [ \"\$(cat work/.last-released)\" = demo ]
"

setup_release_fixture release-stale-before-retro 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous
(
  cd "$REL_PRIMARY" || exit 1
  printf 'remote change\n' >remote-change.txt
  git add remote-change.txt
  GIT_AUTHOR_DATE="2026-08-16T10:03:00Z" GIT_COMMITTER_DATE="2026-08-16T10:03:00Z" git commit -qm "advance main"

 succeeded in 0ms:
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo &&
  git push -q origin wt/demo:main &&
  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo &&
  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$(git rev-parse origin/main)\" ] &&
  [ ! -s '$push_log' ]
"

check "tag-after-merge refuses when local tag already exists" bash -c "
  cd '$REL_WORKTREE'
  retag_out='$TMP/tag-after-merge-retag.out'
  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
    exit 1
  fi
  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
"

setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
  set -e
  : > '$push_log'
  cd '$REL_WORKTREE'
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
  release_commit=\$(git rev-parse HEAD)
  git -C '$REL_PRIMARY' fetch -q origin main
  git -C '$REL_PRIMARY' reset -q --hard origin/main
  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
  git -C '$REL_PRIMARY' add review.txt
  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
  git -C '$REL_PRIMARY' push -q origin main
  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
  [ ! -s '$push_log' ]
"

setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
check "tag-after-merge tags squash commit with non-release subject" bash -c "
  set -e
  cd '$REL_WORKTREE'
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
  git -C '$REL_PRIMARY' fetch -q origin main
  git -C '$REL_PRIMARY' reset -q --hard origin/main
  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
  git -C '$REL_PRIMARY' push -q origin main
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
"

setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
  set -e
  cd '$REL_WORKTREE'
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
  git push -q origin wt/demo:main
  git -C '$REL_PRIMARY' fetch -q origin main
  git -C '$REL_PRIMARY' reset -q --hard origin/main
  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
  git -C '$REL_PRIMARY' add VERSION
  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
  git -C '$REL_PRIMARY' push -q origin main
  not_current_out='$TMP/tag-after-merge-not-current.out'
  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
    exit 1
  fi
  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
  ! git rev-parse --verify --quiet refs/tags/v2026.8.10
"

# --- gate.sh runs and exits cleanly on this repo
check "gate.sh runs on this repo" bash scripts/gate.sh

echo
echo "passed: $pass, failed: $fail"
exit "$((fail > 0 ? 1 : 0))"

exec
/bin/zsh -lc 'bash scripts/archi-fresh.sh' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
The quiet point lines up with the final “gate.sh runs on this repo” check in the standalone smoke suite. That’s expected to be awkward when invoked directly because the real gate includes the smoke-suite hook; I’ve already got the direct fixture evidence, and `archi-fresh.sh` exits 0. Next is the required full gate invocation from repo root.
exec
/bin/zsh -lc "ls -l scripts/gate.d && sed -n '1,80p' scripts/gate.d/*.sh" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
total 40
-rw-r--r--  1 cboyfly  staff  1908 Sep 23 07:26 ds-hygiene.sh
-rwxr-xr-x  1 cboyfly  staff   226 Sep 23 07:26 eval.sh
drwxr-xr-x  4 cboyfly  staff   128 Sep 23 07:26 examples
-rw-r--r--  1 cboyfly  staff  1361 Sep 23 07:26 nb-clean.sh
-rwxr-xr-x  1 cboyfly  staff   613 Sep 23 07:26 py-quality.sh
-rw-r--r--  1 cboyfly  staff   189 Sep 23 07:26 test-scripts.sh
#!/usr/bin/env bash
# Opt-in data-science repo hygiene gate. Copy to scripts/gate.d/ds-hygiene.sh to enable.
set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 1

: "${DS_DATA_MAX_BYTES=1048576}"
: "${DS_DATA_ALLOW_DIRS=tests/fixtures}"
: "${DS_PATH_SCAN=1}"

file_size_bytes() {
  local path="$1"

  stat -c %s "$path" 2>/dev/null || stat -f %z "$path"
}

is_data_artifact() {
  local path="$1"

  case "$path" in
    *.csv|*.tsv|*.parquet|*.pkl|*.pickle|*.h5|*.hdf5|*.onnx|*.joblib|*.npy|*.npz) return 0 ;;
    *) return 1 ;;
  esac
}

is_allowed_data_path() {
  local path="$1"
  local prefix
  local -a prefixes

  [[ -z "$DS_DATA_ALLOW_DIRS" ]] && return 1

  IFS=: read -r -a prefixes <<<"$DS_DATA_ALLOW_DIRS"
  for prefix in "${prefixes[@]}"; do
    [[ -z "$prefix" ]] && continue
    case "$path" in
      "$prefix"*) return 0 ;;
    esac
  done
  return 1
}

check_data_artifacts() {
  local path
  local size
  local found=0

  [[ -z "$DS_DATA_MAX_BYTES" ]] && return 0

  while IFS= read -r path; do
    [[ -f "$path" ]] || continue
    is_data_artifact "$path" || continue
    is_allowed_data_path "$path" && continue

    size=$(file_size_bytes "$path")
    if [[ "$size" -gt "$DS_DATA_MAX_BYTES" ]]; then
      printf 'Tracked data/model artifact exceeds DS_DATA_MAX_BYTES (%s bytes): %s (%s bytes)\n' \
        "$DS_DATA_MAX_BYTES" "$path" "$size" >&2
      found=1
    fi
  done < <(git ls-files)

  return "$found"
}

check_local_paths() {
  local path
  local found=0

  [[ -z "$DS_PATH_SCAN" ]] && return 0

  while IFS= read -r path; do
    [[ -f "$path" ]] || continue
    if grep -Eq '(/Users/|/home/|C:\\)' "$path"; then
      printf 'Tracked code/notebook contains a hardcoded local path: %s\n' "$path" >&2
      found=1
    fi
  done < <(git ls-files '*.py' '*.ipynb')

  return "$found"

exec
/bin/zsh -lc 'git status --short' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
 M ARCHI.md
 M scripts/gate.sh
 M tests/test-scripts.sh

diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
I’m checking the gate hook wrapper before launching the full gate, because the standalone suite’s last self-gate check can recurse if the hook lacks a guard. This is just to understand the verification path, not to widen the patch.
exec
/bin/zsh -lc "sed -n '1,80p' scripts/gate.d/test-scripts.sh" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if [[ "${TEST_SCRIPTS_RUNNING:-}" == 1 ]]; then
  exit 0
fi

TEST_SCRIPTS_RUNNING=1 bash tests/test-scripts.sh

diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
The hook has the expected `TEST_SCRIPTS_RUNNING` guard, so the official `scripts/gate.sh` path should avoid recursion. I’m running the full gate now from the repo root without setting `PYTEST_ADDOPTS` or any shim.
exec
/bin/zsh -lc 'bash scripts/gate.sh' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 352997ms:
ok: shellcheck scripts
ok: archi-fresh passes when ARCHI is newer than source paths
ok: archi-fresh reports stale source paths
ok: archi-fresh stale message says to refresh branch ARCHI
ok: archi-fresh treats equal epochs as fresh
ok: archi-fresh default ref checks current branch history
ok: archi-fresh explicit ref selects branch history
ok: archi-fresh exits 2 when one side has no history
ok: archi-fresh help documents optional ref
ok: state missing plan exits non-zero
ok: state derives plan stage
ok: state derives implement stage
ok: state derives review stage before codex review
ok: state derives release stage before marker
ok: state derives release stage for retro
ok: state derives done stage
ok: state reads review sentinels from wt branch when it exists
ok: state run is read-only
ok: state requires both review approval sentinels
ok: codex-review reads plan body from branch
ok: codex-review reads config from main
ok: codex-review prompt names exact verdict format
ok: codex-review emits verdict instruction after diff
ok: codex-review reads deferrals from branch
ok: codex-review emits deferrals before the diff
ok: 3-review skill routes deferrals to the ledger
ok: code-reviewer agent is told deferrals are settled scope
ok: code-reviewer agent defines severity taxonomy
ok: code-reviewer agent has calibration section
ok: code-reviewer agent requires concrete failure for blocking
ok: codex-review prompt includes calibration guidance
ok: codex-review prompt passes round number
ok: 3-review skill tracks round counter
ok: 3-review skill routes by severity
ok: 3-review skill caps at round 3 mechanically
ok: 3-review skill keeps codex-review work artifacts out of diff
ok: codex-review approve exits 0
ok: codex-review writes stdout artifact
ok: codex-review accepts indented approve verdict
ok: codex-review request-changes exits 1
ok: codex-review ignores branch reviewer.command override
ok: codex-review missing verdict exits 2
ok: codex-review missing reviewer.command exits 2
ok: codex-review parser stops before later command
ok: codex-review ignores commented command and uses real one
ok: codex-review missing branch plan exits 2 before reviewer
ok: codex-review does not invoke reviewer when branch plan is missing
ok: codex-review reviewer failure exits 2 before verdict parsing
ok: codex-review reviewer failure preserves previous artifact
ok: codex-review refuses wt checkout as root
ok: codex-review artifact-only run exits 0
ok: codex-review only dirties primary artifact
ok: codex-review leaves worktree branch clean
ok: codex-review with branch artifacts exits 0
ok: codex-review excludes work unit artifacts from reviewer diff
ok: codex-review from subdirectory exits 0
ok: codex-review from subdirectory includes top-level branch diff
ok: codex-review from subdirectory excludes work unit artifacts
ok: codex-review marks an absent deferral ledger explicitly
ok: codex-review rendered prompt includes severity taxonomy
ok: codex-review with a deferral ledger exits 0
ok: codex-review injects the deferral ledger into the prompt
ok: codex-review deferral ledger is not treated as absent
ok: codex-review prompt includes round number from REVIEW_ROUND
ok: codex-review passes custom round number
ok: codex-review prompt contains round 3
branch 'wt/demo' set up to track 'origin/main'.
ok: codex-review excludes origin-main-only changes
ok: codex-review bases diff on origin/main when local main is stale
ok: codex-review falls back to local main without origin/main
ok: codex-review fallback prompt uses local main base
ok: worktree add creates directory
ok: worktree branch checked out
ok: worktree.sh works FROM INSIDE a worktree (.git-as-file)
ok: worktree remove
ok: worktree add without slug fails
ok: worktree add bases new branch on origin/main from feature branch
ok: worktree add falls back to HEAD without origin/main
ok: worktree add uses stale origin/main when fetch fails
ok: worktree add commits plan.md and leaves worktree clean
ok: worktree add resume path does not duplicate plan commit
ok: worktree sync-artifacts without slug fails
ok: worktree sync-artifacts refuses missing worktree
ok: worktree sync-artifacts refuses missing primary work dir
ok: worktree sync-artifacts refuses invocation from unit worktree
ok: worktree sync-artifacts copies primary artifacts
ok: worktree sync-artifacts records handoff notes followup and codex review
ok: worktree sync-artifacts commits non-ASCII artifact filename
ok: worktree sync-artifacts preserves worktree plan sentinels
ok: worktree sync-artifacts excludes dotfiles and subdirectories
ok: worktree sync-artifacts keeps ignored primary stray absent after successful sync
ok: worktree sync-artifacts deliberately commits existing worktree-side unit files
ok: worktree sync-artifacts does not materialize symlink targets
ok: worktree sync-artifacts leaves worktree clean
ok: worktree sync-artifacts idempotent no-op exits zero
ok: worktree sync-artifacts no-op makes no extra commit
ok: worktree sync-artifacts refreshes changed artifact
ok: worktree sync-artifacts copied refreshed notes
ok: worktree sync-artifacts leaves pending worktree plan edit uncommitted
ok: worktree sync-artifacts keeps pending plan edit in worktree
ok: worktree sync-artifacts artifact commit excludes pending plan edit
ok: worktree sync-artifacts ignores unrelated staged files
ok: worktree sync-artifacts commit excludes unrelated staged file
ok: worktree sync-artifacts leaves unrelated unstaged edit alone
ok: worktree sync-artifacts does not stage unrelated worktree edit
ok: worktree sync-artifacts propagates a failed artifact commit
ok: worktree sync-artifacts accepts primary checkout on non-main branch
ok: worktree sync-artifacts synced from non-main primary checkout
ok: worktree sync-artifacts refuses expected path on wrong branch
ok: worktree sync-artifacts wrong branch receives no artifact commit
ok: gate reports skipped node when package.json exists and node is missing
ok: gate reports skipped lines for every missing guarded tool
ok: gate does not report absent cargo go or node in shell-only repo
ok: gate does not report skipped pytest when no tests match
ok: gate retries pytest once after exit 139 and then passes
ok: gate retries pytest once after real signal death and then passes
ok: gate does not retry ordinary pytest failure
ok: gate fails after one retry when pytest keeps crashing
ok: gate leaves healthy pytest path unchanged
ok: gate does not report skipped node when node check runs
ok: gate runs tsc --noEmit when TS project has no typecheck script
ok: gate does not add tsc fallback when a typecheck script exists
ok: gate reports skipped tsc when TS project has no typecheck script and tsc is absent
ok: gate required tool passes when fake executable is on PATH
ok: gate required tool fails and names missing executable
ok: gate required tool preflight reports every missing executable
ok: gate required tool preflight aborts before stack checks
ok: gate runs without config.yaml or GATE_REQUIRED_TOOLS
ok: gate uses GATE_REQUIRED_TOOLS instead of config required_tools
ok: gate reads required_tools from config.yaml
ok: gate ignores commented-out required_tools
ok: gate ignores required_tools outside gate section
ok: gate treats empty GATE_REQUIRED_TOOLS as no required tools
ok: agent-exec rejects missing handoff
ok: agent-exec exits 0 when implementer commits
ok: agent-exec exits 0 with relative worktree path when implementer commits
ok: agent-exec exits 0 when implementer cd's elsewhere then commits
ok: agent-exec exits 0 when implementer leaves uncommitted changes
ok: agent-exec exits 0 when dirty redispatch cleans tree without commit
ok: agent-exec exits non-zero when implementer produces nothing
ok: notebook hook flags dirty tracked notebook
ok: notebook hook passes cleaned tracked notebook
ok: ds hygiene hook flags oversized tracked artifact
ok: ds hygiene hook exempts default allowed directory
ok: ds hygiene hook treats empty allow dirs as no allowed dirs
ok: ds hygiene hook flags Unix local path in Python
ok: ds hygiene hook flags Windows local path in Python
ok: ds hygiene hook still flags artifact when path scan is disabled
ok: ds hygiene hook still flags local path when artifact scan is disabled
ok: ds hygiene hook disables artifact scan independently
ok: ds hygiene hook reports artifact and local path together
ok: ds hygiene hook passes clean fixture
ok: ds hygiene hook disables path scan independently
ok: ds hygiene hook skips deleted tracked artifact without stderr
ok: ds hygiene hook honours colon-separated allow dirs
ok: ds hygiene hook ignores empty allow-dir prefix
ok: fan dispatch manifest lists only gate passers
ok: fan adopt repoints canonical branch and cleans samples
ok: fan dispatch auto-commits non-committing sample work
ok: fan adopt preserves auto-committed sample work and cleans samples
ok: fan adopt force-cleans dirty sample worktrees and branches
ok: fan dispatch emits empty manifest and exits 0 with no survivors
ok: release version compare accepts .10 over .9
ok: release version compare rejects .9 after .10
ok: release refuses without code-review approval
ok: release refuses without codex-review approval
ok: release refuses when gate fails
ok: release refuses when ARCHI.md is stale
ok: release refuses when computed version does not exceed VERSION
ok: release can be invoked from primary checkout
ok: release commits bump on branch without touching main, origin/main, or tagging
ok: release writes last-released marker into release commit
ok: release rollback removes first-time last-released marker
ok: release refuses marker with missing retro
ok: release refuses marker with empty retro
ok: release proceeds when previous retro is non-empty
ok: release refuses deleted last-released marker
ok: release refuses mutated last-released marker
ok: release refuses symlinked last-released marker
ok: release refuses last-released marker with extra trailing newline
ok: release re-run on release branch names merge guidance
ok: release refuses empty bootstrap last-released marker
ok: release refuses multi-line bootstrap last-released marker
ok: release refuses symlinked bootstrap last-released marker
ok: release proceeds without last-released marker
ok: release reports stale branch before missing retro
ok: release refuses stale branch, then computes next micro after sync
ok: release catches origin/main moving during gate
ok: tag-after-merge creates local tag on origin/main and pushes nothing
ok: tag-after-merge refuses when local tag already exists
ok: tag-after-merge tags release commit below merge commit and pushes nothing
ok: tag-after-merge tags squash commit with non-release subject
ok: tag-after-merge refuses when origin/main version advanced past the release
ok: gate.sh runs on this repo

passed: 193, failed: 0

diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
The exact sandbox crash reproduced in the full gate: `pytest -q` exited 139, the new warning line fired, and the retry with `-p no:capture` is running and collecting normally. This is the unit doing its job in the wild, which is oddly satisfying.
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
The retried pytest is still progressing. I’m keeping the gate session open until it reaches the final `GATE: PASS` or a concrete failure.
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
Pytest passed on the retry, and shellcheck has already run through the touched shell files inside the full gate. The remaining gate.d hooks are running now.
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
No new output yet; this part includes the eval and smoke-suite hooks, so I’m letting it finish rather than restarting.
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
The full gate’s smoke-suite hook has reached the same final region but under the guarded environment, so it should complete rather than recurse. Waiting for the final tally and `GATE: PASS`.
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
It’s quiet again because the smoke suite’s last check runs a nested `scripts/gate.sh`; with the guard set, that nested gate skips only the smoke hook but still runs pytest and the other hooks. That explains the silence, so I’m letting it finish.
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
Still no output, but the nested gate check suppresses its own stdout/stderr by design, so this can look frozen while it runs the long Python checks. I’m keeping the session alive until it returns.
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

 succeeded in 302673ms:
scripts/gate.sh: line 26: 38249 Segmentation fault: 11  pytest -q
⚠ pytest died by signal (exit 139) — known native-readline crash under pytest capture; retrying once with -p no:capture
▶ pytest -q -p no:capture
..............................................heavy_tailed reference MCSE diagnostic: 0.001117
rare_event_imbalance reference MCSE diagnostic: 0.002325
.........
=============================== warnings summary ===============================
tests/test_equiv_probe.py::test_mechanism_diagnostic_is_per_instrument
tests/test_equiv_probe.py::test_probe_replays_deterministically
  /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience/src/adaptive_compute/betting.py:151: RuntimeWarning: overflow encountered in multiply
    self.capital_plus *= 1.0 + lambdas * centered

tests/test_equiv_probe.py::test_mechanism_diagnostic_is_per_instrument
tests/test_equiv_probe.py::test_probe_replays_deterministically
  /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience/src/adaptive_compute/betting.py:152: RuntimeWarning: overflow encountered in multiply
    self.capital_minus *= 1.0 - lambdas * centered

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
55 passed, 4 warnings in 88.89s (0:01:28)
▶ shellcheck scripts/agent-exec.sh scripts/archi-fresh.sh scripts/codex-review.sh scripts/fan-exec.sh scripts/gate.d/ds-hygiene.sh scripts/gate.d/eval.sh scripts/gate.d/examples/ds-hygiene.sh scripts/gate.d/examples/nb-clean.sh scripts/gate.d/nb-clean.sh scripts/gate.d/py-quality.sh scripts/gate.d/test-scripts.sh scripts/gate.sh scripts/release.sh scripts/state.sh scripts/worktree.sh tests/test-scripts.sh
▶ bash scripts/gate.d/ds-hygiene.sh
▶ bash scripts/gate.d/eval.sh
/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience/src/adaptive_compute/betting.py:151: RuntimeWarning: overflow encountered in multiply
  self.capital_plus *= 1.0 + lambdas * centered
/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience/src/adaptive_compute/betting.py:152: RuntimeWarning: overflow encountered in multiply
  self.capital_minus *= 1.0 - lambdas * centered
eval check passed; draws_consumed=7760
▶ bash scripts/gate.d/nb-clean.sh
▶ bash scripts/gate.d/py-quality.sh
▶ ruff format --check .
104 files already formatted
▶ mypy src
Success: no issues found in 12 source files
▶ bash scripts/gate.d/test-scripts.sh
ok: shellcheck scripts
ok: archi-fresh passes when ARCHI is newer than source paths
ok: archi-fresh reports stale source paths
ok: archi-fresh stale message says to refresh branch ARCHI
ok: archi-fresh treats equal epochs as fresh
ok: archi-fresh default ref checks current branch history
ok: archi-fresh explicit ref selects branch history
ok: archi-fresh exits 2 when one side has no history
ok: archi-fresh help documents optional ref
ok: state missing plan exits non-zero
ok: state derives plan stage
ok: state derives implement stage
ok: state derives review stage before codex review
ok: state derives release stage before marker
ok: state derives release stage for retro
ok: state derives done stage
ok: state reads review sentinels from wt branch when it exists
ok: state run is read-only
ok: state requires both review approval sentinels
ok: codex-review reads plan body from branch
ok: codex-review reads config from main
ok: codex-review prompt names exact verdict format
ok: codex-review emits verdict instruction after diff
ok: codex-review reads deferrals from branch
ok: codex-review emits deferrals before the diff
ok: 3-review skill routes deferrals to the ledger
ok: code-reviewer agent is told deferrals are settled scope
ok: code-reviewer agent defines severity taxonomy
ok: code-reviewer agent has calibration section
ok: code-reviewer agent requires concrete failure for blocking
ok: codex-review prompt includes calibration guidance
ok: codex-review prompt passes round number
ok: 3-review skill tracks round counter
ok: 3-review skill routes by severity
ok: 3-review skill caps at round 3 mechanically
ok: 3-review skill keeps codex-review work artifacts out of diff
ok: codex-review approve exits 0
ok: codex-review writes stdout artifact
ok: codex-review accepts indented approve verdict
ok: codex-review request-changes exits 1
ok: codex-review ignores branch reviewer.command override
ok: codex-review missing verdict exits 2
ok: codex-review missing reviewer.command exits 2
ok: codex-review parser stops before later command
ok: codex-review ignores commented command and uses real one
ok: codex-review missing branch plan exits 2 before reviewer
ok: codex-review does not invoke reviewer when branch plan is missing
ok: codex-review reviewer failure exits 2 before verdict parsing
ok: codex-review reviewer failure preserves previous artifact
ok: codex-review refuses wt checkout as root
ok: codex-review artifact-only run exits 0
ok: codex-review only dirties primary artifact
ok: codex-review leaves worktree branch clean
ok: codex-review with branch artifacts exits 0
ok: codex-review excludes work unit artifacts from reviewer diff
ok: codex-review from subdirectory exits 0
ok: codex-review from subdirectory includes top-level branch diff
ok: codex-review from subdirectory excludes work unit artifacts
ok: codex-review marks an absent deferral ledger explicitly
ok: codex-review rendered prompt includes severity taxonomy
ok: codex-review with a deferral ledger exits 0
ok: codex-review injects the deferral ledger into the prompt
ok: codex-review deferral ledger is not treated as absent
ok: codex-review prompt includes round number from REVIEW_ROUND
ok: codex-review passes custom round number
ok: codex-review prompt contains round 3
branch 'wt/demo' set up to track 'origin/main'.
ok: codex-review excludes origin-main-only changes
ok: codex-review bases diff on origin/main when local main is stale
ok: codex-review falls back to local main without origin/main
ok: codex-review fallback prompt uses local main base
ok: worktree add creates directory
ok: worktree branch checked out
ok: worktree.sh works FROM INSIDE a worktree (.git-as-file)
ok: worktree remove
ok: worktree add without slug fails
ok: worktree add bases new branch on origin/main from feature branch
ok: worktree add falls back to HEAD without origin/main
ok: worktree add uses stale origin/main when fetch fails
ok: worktree add commits plan.md and leaves worktree clean
ok: worktree add resume path does not duplicate plan commit
ok: worktree sync-artifacts without slug fails
ok: worktree sync-artifacts refuses missing worktree
ok: worktree sync-artifacts refuses missing primary work dir
ok: worktree sync-artifacts refuses invocation from unit worktree
ok: worktree sync-artifacts copies primary artifacts
ok: worktree sync-artifacts records handoff notes followup and codex review
ok: worktree sync-artifacts commits non-ASCII artifact filename
ok: worktree sync-artifacts preserves worktree plan sentinels
ok: worktree sync-artifacts excludes dotfiles and subdirectories
ok: worktree sync-artifacts keeps ignored primary stray absent after successful sync
ok: worktree sync-artifacts deliberately commits existing worktree-side unit files
ok: worktree sync-artifacts does not materialize symlink targets
ok: worktree sync-artifacts leaves worktree clean
ok: worktree sync-artifacts idempotent no-op exits zero
ok: worktree sync-artifacts no-op makes no extra commit
ok: worktree sync-artifacts refreshes changed artifact
ok: worktree sync-artifacts copied refreshed notes
ok: worktree sync-artifacts leaves pending worktree plan edit uncommitted
ok: worktree sync-artifacts keeps pending plan edit in worktree
ok: worktree sync-artifacts artifact commit excludes pending plan edit
ok: worktree sync-artifacts ignores unrelated staged files
ok: worktree sync-artifacts commit excludes unrelated staged file
ok: worktree sync-artifacts leaves unrelated unstaged edit alone
ok: worktree sync-artifacts does not stage unrelated worktree edit
ok: worktree sync-artifacts propagates a failed artifact commit
ok: worktree sync-artifacts accepts primary checkout on non-main branch
ok: worktree sync-artifacts synced from non-main primary checkout
ok: worktree sync-artifacts refuses expected path on wrong branch
ok: worktree sync-artifacts wrong branch receives no artifact commit
ok: gate reports skipped node when package.json exists and node is missing
ok: gate reports skipped lines for every missing guarded tool
ok: gate does not report absent cargo go or node in shell-only repo
ok: gate does not report skipped pytest when no tests match
ok: gate retries pytest once after exit 139 and then passes
ok: gate retries pytest once after real signal death and then passes
ok: gate does not retry ordinary pytest failure
ok: gate fails after one retry when pytest keeps crashing
ok: gate leaves healthy pytest path unchanged
ok: gate does not report skipped node when node check runs
ok: gate runs tsc --noEmit when TS project has no typecheck script
ok: gate does not add tsc fallback when a typecheck script exists
ok: gate reports skipped tsc when TS project has no typecheck script and tsc is absent
ok: gate required tool passes when fake executable is on PATH
ok: gate required tool fails and names missing executable
ok: gate required tool preflight reports every missing executable
ok: gate required tool preflight aborts before stack checks
ok: gate runs without config.yaml or GATE_REQUIRED_TOOLS
ok: gate uses GATE_REQUIRED_TOOLS instead of config required_tools
ok: gate reads required_tools from config.yaml
ok: gate ignores commented-out required_tools
ok: gate ignores required_tools outside gate section
ok: gate treats empty GATE_REQUIRED_TOOLS as no required tools
ok: agent-exec rejects missing handoff
ok: agent-exec exits 0 when implementer commits
ok: agent-exec exits 0 with relative worktree path when implementer commits
ok: agent-exec exits 0 when implementer cd's elsewhere then commits
ok: agent-exec exits 0 when implementer leaves uncommitted changes
ok: agent-exec exits 0 when dirty redispatch cleans tree without commit
ok: agent-exec exits non-zero when implementer produces nothing
ok: notebook hook flags dirty tracked notebook
ok: notebook hook passes cleaned tracked notebook
ok: ds hygiene hook flags oversized tracked artifact
ok: ds hygiene hook exempts default allowed directory
ok: ds hygiene hook treats empty allow dirs as no allowed dirs
ok: ds hygiene hook flags Unix local path in Python
ok: ds hygiene hook flags Windows local path in Python
ok: ds hygiene hook still flags artifact when path scan is disabled
ok: ds hygiene hook still flags local path when artifact scan is disabled
ok: ds hygiene hook disables artifact scan independently
ok: ds hygiene hook reports artifact and local path together
ok: ds hygiene hook passes clean fixture
ok: ds hygiene hook disables path scan independently
ok: ds hygiene hook skips deleted tracked artifact without stderr
ok: ds hygiene hook honours colon-separated allow dirs
ok: ds hygiene hook ignores empty allow-dir prefix
ok: fan dispatch manifest lists only gate passers
ok: fan adopt repoints canonical branch and cleans samples
ok: fan dispatch auto-commits non-committing sample work
ok: fan adopt preserves auto-committed sample work and cleans samples
ok: fan adopt force-cleans dirty sample worktrees and branches
ok: fan dispatch emits empty manifest and exits 0 with no survivors
ok: release version compare accepts .10 over .9
ok: release version compare rejects .9 after .10
ok: release refuses without code-review approval
ok: release refuses without codex-review approval
ok: release refuses when gate fails
ok: release refuses when ARCHI.md is stale
ok: release refuses when computed version does not exceed VERSION
ok: release can be invoked from primary checkout
ok: release commits bump on branch without touching main, origin/main, or tagging
ok: release writes last-released marker into release commit
ok: release rollback removes first-time last-released marker
ok: release refuses marker with missing retro
ok: release refuses marker with empty retro
ok: release proceeds when previous retro is non-empty
ok: release refuses deleted last-released marker
ok: release refuses mutated last-released marker
ok: release refuses symlinked last-released marker
ok: release refuses last-released marker with extra trailing newline
ok: release re-run on release branch names merge guidance
ok: release refuses empty bootstrap last-released marker
ok: release refuses multi-line bootstrap last-released marker
ok: release refuses symlinked bootstrap last-released marker
ok: release proceeds without last-released marker
ok: release reports stale branch before missing retro
ok: release refuses stale branch, then computes next micro after sync
ok: release catches origin/main moving during gate
ok: tag-after-merge creates local tag on origin/main and pushes nothing
ok: tag-after-merge refuses when local tag already exists
ok: tag-after-merge tags release commit below merge commit and pushes nothing
ok: tag-after-merge tags squash commit with non-release subject
ok: tag-after-merge refuses when origin/main version advanced past the release
ok: gate.sh runs on this repo

passed: 193, failed: 0
GATE: PASS

web search: 
web search: 
codex
The required full gate passed: `193` smoke checks, `0` failures, and `GATE: PASS`. I’m doing final housekeeping now: checking the old standalone session state, reviewing the diff, then committing on the verified branch.
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
The earlier direct smoke-suite session also completed cleanly after the nested gate finished: `passed: 193, failed: 0`. Nice, no loose session left. I’m reviewing the staged shape now, then I’ll commit and run `archi-fresh.sh` once more after the commit as requested.
exec
/bin/zsh -lc 'git status --short' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
 M ARCHI.md
 M scripts/gate.sh
 M tests/test-scripts.sh

exec
/bin/zsh -lc 'git diff --stat && git diff -- ARCHI.md scripts/gate.sh tests/test-scripts.sh' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
 ARCHI.md              |  4 +--
 scripts/gate.sh       | 23 ++++++++++++-
 tests/test-scripts.sh | 92 +++++++++++++++++++++++++++++++++++++++++++++++++++
 3 files changed, 116 insertions(+), 3 deletions(-)
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42..e6ee99f 100644
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@ Python 3.12 (`src/` layout) for the research code, plus the agentic-coding harne
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@ Python 3.12 (`src/` layout) for the research code, plus the agentic-coding harne
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf04870..1067f3a 100755
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@ run() {
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@ if [[ -f pyproject.toml || -f setup.py || -f requirements.txt ]]; then
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb4..9339b38 100755
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@ setup_gate_fixture gate-python-no-tests
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
The diff is within the declared footprint, and the full gate already confirmed shellcheck clean. I’m committing the three touched files now with the ARCHI update in the same commit, then I’ll run `archi-fresh.sh` against the committed history.
exec
/bin/zsh -lc 'git add ARCHI.md scripts/gate.sh tests/test-scripts.sh && git commit -m "Retry pytest once after signal death"' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
[wt/gate-readline-resilience a502158] Retry pytest once after signal death
 3 files changed, 116 insertions(+), 3 deletions(-)

diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
Commit is in place. I’m doing the post-commit freshness check now, exactly because the release path compares script history against `ARCHI.md`.
exec
/bin/zsh -lc 'bash scripts/archi-fresh.sh' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
exec
/bin/zsh -lc 'git status --short && git log -1 --oneline' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/gate-readline-resilience
 succeeded in 0ms:
a502158 Retry pytest once after signal death

diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

codex
Implemented and committed `a502158 Retry pytest once after signal death` on `wt/gate-readline-resilience`.

Changed:
- `scripts/gate.sh`: added a `run_pytest` helper that runs `pytest -q` once, does not retry normal failures, and retries once with `-p no:capture` only when pytest exits >128.
- `tests/test-scripts.sh`: added all five gate fixture cases, including the real `kill -SEGV $$` case and exact retry log assertions.
- `ARCHI.md`: updated `knowledge/` wording and documented the one-shot pytest signal-death retry.

Verification:
- `bash tests/test-scripts.sh` passed: `193` passed, `0` failed.
- `bash scripts/gate.sh` passed with `GATE: PASS`.
- `bash scripts/archi-fresh.sh` exited 0 after the commit.
- Shellcheck ran inside the gate and passed.

The `⚠ pytest died by signal (exit 139)` retry line did fire in the final gate run; the retry passed with `pytest -q -p no:capture`. No acceptance criteria were partially met, and I left no out-of-scope changes.
diff --git a/ARCHI.md b/ARCHI.md
index c72dc42fb6f02fdbe413298e52cec875ffa7d04d..e6ee99f80218c0f429f12c4323a868acb1ad875b
--- a/ARCHI.md
+++ b/ARCHI.md
@@ -18,7 +18,7 @@
 - `scripts/` — the deterministic layer: `gate.sh` (stack-detecting check runner), `worktree.sh`, `agent-exec.sh`, `fan-exec.sh`, `codex-review.sh`, `release.sh`, `state.sh`, `archi-fresh.sh`. `worktree.sh` and `codex-review.sh` bound their best-effort `git fetch origin` under `timeout`/`gtimeout` when one is on PATH (default 30s, overridable via `WORKTREE_FETCH_TIMEOUT`), falling back to an unbounded call when neither exists. `gate.d/*.sh` are auto-run hooks: `test-scripts.sh` (shell smoke suite), `py-quality.sh` (ruff format-check + mypy), `ds-hygiene.sh` and `nb-clean.sh` (ML profile hygiene). `gate.d/examples/` holds the un-enabled originals.
 - `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
 - `VERSION` / `CHANGELOG.md` — CalVer + Keep-a-Changelog; written only by `release.sh`. Seeded at `2026.8.0` so the first release computes cleanly.
-- `knowledge/` — cold-tier docs, loaded only on citation (empty but for a README).
+- `knowledge/` — cold-tier docs, loaded only on citation.
 - `.github/workflows/ci.yml` — runs the shell smoke suite + gate on push/PR.
 - `AGENTS.md` — the implementer's contract.
 
@@ -40,7 +40,7 @@
 
 ## Verification
 
-`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q`, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
+`bash scripts/gate.sh` — required-tool preflight (`shellcheck`), shellcheck over tracked `*.sh`, `ruff check .`, `pytest -q` with a one-shot `-p no:capture` retry if pytest dies by signal, plus `gate.d/` hooks (`test-scripts.sh` shell smoke suite, `py-quality.sh` format+types, `eval.sh`, `ds-hygiene.sh`, `nb-clean.sh`). CI runs the gate on push.
 
 ### ML profile declarations
 
diff --git a/scripts/gate.sh b/scripts/gate.sh
index bf048704d3beb92a4439a096e9d4a9c2f38daa90..1067f3ae66430bd43f54ebe91599f6b1f47260a4
--- a/scripts/gate.sh
+++ b/scripts/gate.sh
@@ -21,6 +21,27 @@
   fi
 }
 
+# pytest can die in _readline_workaround before collection with exit 139.
+# Disabling capture skips that native-readline path on the single retry.
+run_pytest() {
+  local rc
+
+  echo "▶ pytest -q"
+  pytest -q
+  rc=$?
+  if [[ $rc -eq 0 ]]; then
+    return
+  fi
+  if [[ $rc -le 128 ]]; then
+    fail=1
+    echo "✗ FAILED: pytest -q"
+    return
+  fi
+
+  echo "⚠ pytest died by signal (exit $rc) — known native-readline crash under pytest capture; retrying once with -p no:capture"
+  run pytest -q -p no:capture
+}
+
 required_tools=
 if [[ ${GATE_REQUIRED_TOOLS+set} ]]; then
   required_tools=$GATE_REQUIRED_TOOLS
@@ -99,7 +120,7 @@
   fi
   if compgen -G "tests/*" >/dev/null; then
     if command -v pytest >/dev/null; then
-      run pytest -q
+      run_pytest
     else
       skip pytest
     fi
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index e522bb46f624c4a1b88ae53ec9b257e9a2144c01..9339b386b5dba463b4e0a5d2ed99f0bb3bedee47
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1245,6 +1245,98 @@
 )
 check "gate does not report skipped pytest when no tests match" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); grep -Fq '⊘ skipped: ruff (not installed)' <<<\"\$out\" && ! grep -Fq 'skipped: pytest' <<<\"\$out\""
 
+setup_gate_fixture gate-pytest-exit-139-retry
+gate_pytest_log="$TMP/gate-pytest-exit-139-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after exit 139 and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-real-signal-retry
+gate_pytest_log="$TMP/gate-pytest-real-signal-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+[[ " \$* " == *" no:capture "* ]] && exit 0
+kill -SEGV \$\$
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate retries pytest once after real signal death and then passes" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-failure-no-retry
+gate_pytest_log="$TMP/gate-pytest-failure-no-retry/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 1
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate does not retry ordinary pytest failure" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '✗ FAILED: pytest -q' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
+setup_gate_fixture gate-pytest-persistent-crash
+gate_pytest_log="$TMP/gate-pytest-persistent-crash/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 139
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate fails after one retry when pytest keeps crashing" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -ne 0 ]] && grep -Fq '⚠ pytest died by signal (exit 139)' <<<\"\$out\" && grep -Fq '✗ FAILED: pytest -q -p no:capture' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 2 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q' && sed -n '2p' '$gate_pytest_log' | grep -Fx -- '-q -p no:capture'"
+
+setup_gate_fixture gate-pytest-healthy
+gate_pytest_log="$TMP/gate-pytest-healthy/pytest.log"
+cat >"$GATE_BIN/pytest" <<EOF
+#!/usr/bin/env bash
+echo "\$*" >>"$gate_pytest_log"
+exit 0
+EOF
+chmod +x "$GATE_BIN/pytest"
+(
+  cd "$GATE_REPO" || exit 1
+  mkdir -p tests
+  printf '[project]\nname = "fixture"\n' >pyproject.toml
+  printf 'def test_marker():\n    pass\n' >tests/test_x.py
+  git add pyproject.toml tests/test_x.py
+  git commit -qm pytest-marker
+)
+check "gate leaves healthy pytest path unchanged" bash -c "cd '$GATE_REPO' && out=\$(PATH='$GATE_BIN' bash scripts/gate.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && grep -Fq '▶ pytest -q' <<<\"\$out\" && grep -Fq 'GATE: PASS' <<<\"\$out\" && ! grep -Fq '⚠ pytest died by signal' <<<\"\$out\" && [[ \$(wc -l < '$gate_pytest_log') -eq 1 ]] && sed -n '1p' '$gate_pytest_log' | grep -Fx -- '-q'"
+
 setup_gate_fixture gate-node-runs
 write_fake_tool "$GATE_BIN/node"
 write_fake_tool "$GATE_BIN/npm"

tokens used
74,206
Implemented and committed `a502158 Retry pytest once after signal death` on `wt/gate-readline-resilience`.

Changed:
- `scripts/gate.sh`: added a `run_pytest` helper that runs `pytest -q` once, does not retry normal failures, and retries once with `-p no:capture` only when pytest exits >128.
- `tests/test-scripts.sh`: added all five gate fixture cases, including the real `kill -SEGV $$` case and exact retry log assertions.
- `ARCHI.md`: updated `knowledge/` wording and documented the one-shot pytest signal-death retry.

Verification:
- `bash tests/test-scripts.sh` passed: `193` passed, `0` failed.
- `bash scripts/gate.sh` passed with `GATE: PASS`.
- `bash scripts/archi-fresh.sh` exited 0 after the commit.
- Shellcheck ran inside the gate and passed.

The `⚠ pytest died by signal (exit 139)` retry line did fire in the final gate run; the retry passed with `pytest -q -p no:capture`. No acceptance criteria were partially met, and I left no out-of-scope changes.
