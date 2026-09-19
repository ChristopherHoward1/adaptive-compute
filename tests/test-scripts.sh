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
if compgen -G "scripts/gate.d/*.sh" >/dev/null; then
  for hook in scripts/gate.d/*.sh; do
    bash "$hook"
  done
fi
echo "GATE: PASS"
EOF
    chmod +x scripts/release.sh scripts/archi-fresh.sh scripts/gate.sh
    printf 'name: fixture\n' >config.yaml
    printf 'merge rules\n' >CLAUDE.md
    printf '%s\n' "$version" >VERSION
    printf '# Changelog\n\nAll notable changes to this project are documented in this file.\n\n' >CHANGELOG.md
    {
      printf '# Demo\n\n'
      printf '## Release\n\n'
      printf 'Release note: Demo release note.\n\n'
      printf '## Review\n\n'
      printf '%s\n' "$verdict_line"
      if [[ -n "$codex_verdict_line" ]]; then
        printf '%s\n' "$codex_verdict_line"
      fi
    } >work/demo/plan.md
    [[ "$gate_mode" == fail ]] && printf 'fail\n' >GATE_FAIL
    if [[ -n "$marker_slug" ]]; then
      printf '%s\n' "$marker_slug" >work/.last-released
      if [[ "$retro_content" != __missing__ ]]; then
        mkdir -p "work/$marker_slug"
        printf '%s' "$retro_content" >"work/$marker_slug/retro.md"
      fi
    fi
  )
  commit_fixture "$REL_PRIMARY" "2026-08-16T10:00:00Z" source
  printf 'architecture\n' >"$REL_PRIMARY/ARCHI.md"
  commit_fixture "$REL_PRIMARY" "2026-08-16T10:01:00Z" archi
  if [[ "$archi_mode" == stale ]]; then
    printf 'merge rules updated\n' >>"$REL_PRIMARY/CLAUDE.md"
    commit_fixture "$REL_PRIMARY" "2026-08-16T10:02:00Z" stale-source
  fi
  (
    cd "$REL_PRIMARY" || exit 1
    git push -q -u origin main
    git branch wt/demo
    git worktree add -q "$REL_WORKTREE" wt/demo
    git -C "$REL_WORKTREE" config user.email tester@example.com
    git -C "$REL_WORKTREE" config user.name Tester
  )
  write_release_fixture_date "$REL_FAKEBIN" "2026.8" "2026-08-16"
}

setup_archi_fresh_fixture() {
  local name="$1"
  local mode="$2"
  local tmp_root="$TMP/$name"

  ARCHI_REPO="$tmp_root/repo"

  mkdir -p "$ARCHI_REPO"
  git init -q -b main "$ARCHI_REPO"
  (
    cd "$ARCHI_REPO" || exit 1
    git config user.email tester@example.com
    git config user.name Tester
    mkdir -p scripts skills profiles
    cp "$ROOT/scripts/archi-fresh.sh" scripts/archi-fresh.sh
    chmod +x scripts/archi-fresh.sh
    printf 'name: fixture\n' >config.yaml
    printf 'merge rules\n' >CLAUDE.md
    printf 'profile\n' >profiles/default.md
    printf 'skill\n' >skills/fixture.md
    git add -A
    GIT_AUTHOR_DATE="2026-08-16T10:00:00Z" GIT_COMMITTER_DATE="2026-08-16T10:00:00Z" git commit -qm source

    if [[ "$mode" == missing-archi ]]; then
      return 0
    fi

    printf 'architecture\n' >ARCHI.md
    if [[ "$mode" == equal ]]; then
      printf 'merge rules updated\n' >>CLAUDE.md
    fi
    git add -A
    GIT_AUTHOR_DATE="2026-08-16T10:01:00Z" GIT_COMMITTER_DATE="2026-08-16T10:01:00Z" git commit -qm archi

    case "$mode" in
      stale)
        printf 'skill updated\n' >>skills/fixture.md
        git add skills/fixture.md
        GIT_AUTHOR_DATE="2026-08-16T10:02:00Z" GIT_COMMITTER_DATE="2026-08-16T10:02:00Z" git commit -qm stale-source
        ;;
      branch-ref)
        git branch wt/demo
        printf 'branch-only skill update\n' >>skills/fixture.md
        git add skills/fixture.md
        GIT_AUTHOR_DATE="2026-08-16T10:02:00Z" GIT_COMMITTER_DATE="2026-08-16T10:02:00Z" git commit -qm branch-source
        git branch -f wt/demo HEAD
        git reset -q --hard HEAD~1
        ;;
    esac
  )
}

setup_codex_review_fixture() {
  local name="$1"
  local command_mode="$2"
  local tmp_root="$TMP/$name"

  COD_PRIMARY="$tmp_root/primary"
  COD_WORKTREE="$tmp_root/demo-wt"
  COD_REVIEWER="$tmp_root/canned-reviewer.sh"
  COD_MARKER="$tmp_root/reviewer-invoked"

  mkdir -p "$tmp_root"
  git init -q -b main "$COD_PRIMARY"
  (
    cd "$COD_PRIMARY" || exit 1
    git config user.email tester@example.com
    git config user.name Tester
    mkdir -p scripts work/demo
    cp "$ROOT/scripts/codex-review.sh" scripts/codex-review.sh
    chmod +x scripts/codex-review.sh
    printf 'base\n' >base.txt
    printf '# Primary plan\n' >work/demo/plan.md
    case "$command_mode" in
      normal|branch-override)
        cat >config.yaml <<EOF
reviewer:
  command: '$COD_REVIEWER approve'
EOF
        ;;
      indented)
        cat >config.yaml <<EOF
reviewer:
  command: '$COD_REVIEWER indented-approve'
EOF
        ;;
      request)
        cat >config.yaml <<EOF
reviewer:
  command: '$COD_REVIEWER request'
EOF
        ;;
      missing-verdict)
        cat >config.yaml <<EOF
reviewer:
  command: '$COD_REVIEWER missing'
EOF
        ;;
      absent)
        printf 'name: fixture\n' >config.yaml
        ;;
      later-command)
        cat >config.yaml <<'EOF'
reviewer:
  note: none
gate:
  command: scripts/gate.sh
EOF
        ;;
      commented)
        cat >config.yaml <<EOF
reviewer:
  # command: '$COD_REVIEWER request'
  command: '$COD_REVIEWER approve'
EOF
        ;;
      missing-plan)
        cat >config.yaml <<EOF
reviewer:
  command: 'COD_REVIEWER_MARKER=$COD_MARKER $COD_REVIEWER approve'
EOF
        ;;
      reviewer-fails)
        cat >config.yaml <<EOF
reviewer:
  command: '$COD_REVIEWER approve-then-fail'
EOF
        ;;
      capture-prompt|origin-main-ahead)
        cat >config.yaml <<EOF
reviewer:
  command: '$COD_REVIEWER capture-prompt $tmp_root/prompt.txt'
EOF
        ;;
    esac
    git add -A
    git commit -qm main
    case "$command_mode" in
      origin-main-ahead)
        git init -q --bare "$tmp_root/origin.git"
        git remote add origin "$tmp_root/origin.git"
        git push -q -u origin main
        local_main=$(git rev-parse HEAD)
        printf 'remote-only\n' >remote-only.txt
        git add remote-only.txt
        git commit -qm remote-only
        git push -q origin main
        git reset -q --hard "$local_main"
        git fetch origin --quiet
        git branch wt/demo origin/main
        ;;
      *)
        git branch wt/demo
        ;;
    esac
    git worktree add -q "$COD_WORKTREE" wt/demo
    git -C "$COD_WORKTREE" config user.email tester@example.com
    git -C "$COD_WORKTREE" config user.name Tester
  )

  cat >"$COD_REVIEWER" <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
if [[ -n "${COD_REVIEWER_MARKER:-}" ]]; then
  printf 'invoked\n' >>"$COD_REVIEWER_MARKER"
fi
if [[ "${1:-approve}" == capture-prompt ]]; then
  cat >"$2"
  printf 'looks fine\n'
  printf 'Codex verdict: APPROVE\n'
  exit 0
fi
cat >/dev/null
case "${1:-approve}" in
  approve)
    printf 'looks fine\n'
    printf 'Codex verdict: APPROVE\n'
    ;;
  indented-approve)
    printf 'looks fine\n'
    printf '  Codex verdict: APPROVE\n'
    ;;
  request)
    printf 'needs work\n'
    printf 'Codex verdict: REQUEST CHANGES\n'
    ;;
  missing)
    printf 'no machine verdict here\n'
    ;;
  approve-then-fail)
    printf 'looks fine\n'
    printf 'Codex verdict: APPROVE\n'
    exit 42
    ;;
esac
EOF
  chmod +x "$COD_REVIEWER"

  (
    cd "$COD_WORKTREE" || exit 1
    mkdir -p work/demo
    printf '# Demo\n\n## Goal\n\nReview me.\n' >work/demo/plan.md
    printf 'feature\n' >feature.txt
    case "$command_mode" in
      branch-override)
        cat >config.yaml <<EOF
reviewer:
  command: '$COD_REVIEWER request'
EOF
        ;;
      missing-plan)
        git rm -q -f work/demo/plan.md
        ;;
    esac
    git add -A
    git commit -qm "fixture $command_mode"
  )
}

setup_agent_exec_fixture() {
  local name="$1"
  local mode="$2"
  local tmp_root="$TMP/$name"

  AGENT_PRIMARY="$tmp_root/primary"
  AGENT_WORKTREE="$tmp_root/wts/demo-wt"
  AGENT_IMPL="$tmp_root/canned-implementer.sh"
  AGENT_HANDOFF="$tmp_root/handoff.md"

  mkdir -p "$tmp_root"
  git init -q -b main "$AGENT_PRIMARY"
  (
    cd "$AGENT_PRIMARY" || exit 1
    git config user.email tester@example.com
    git config user.name Tester
    mkdir -p scripts
    cp "$ROOT/scripts/agent-exec.sh" scripts/agent-exec.sh
    chmod +x scripts/agent-exec.sh
    cat >"$AGENT_IMPL" <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
cat >/dev/null
git config user.email tester@example.com
git config user.name Tester
case "${AGENT_MODE:-nothing}" in
  commit)
    printf 'committed\n' >agent-result.txt
    git add agent-result.txt
    git commit -qm 'agent result'
    ;;
  cd-elsewhere-commit)
    cd /tmp || exit 1
    printf 'committed after cd\n' >"$AGENT_WORKTREE_PATH/agent-result.txt"
    git -C "$AGENT_WORKTREE_PATH" add agent-result.txt
    git -C "$AGENT_WORKTREE_PATH" commit -qm 'agent result after cd'
    ;;
  dirty)
    printf 'dirty\n' >agent-result.txt
    ;;
  predirty-clean)
    rm -f preexisting-dirty.txt
    ;;
  nothing)
    ;;
esac
EOF
    chmod +x "$AGENT_IMPL"
    cat >config.yaml <<EOF
implementer:
  command: 'AGENT_MODE=$mode AGENT_WORKTREE_PATH=$AGENT_WORKTREE $AGENT_IMPL'
EOF
    printf 'base\n' >base.txt
    git add -A
    git commit -qm init
    mkdir -p "$tmp_root/wts"
    git branch wt/demo
    git worktree add -q "$AGENT_WORKTREE" wt/demo
    git -C "$AGENT_WORKTREE" config user.email tester@example.com
    git -C "$AGENT_WORKTREE" config user.name Tester
    if [[ "$mode" == predirty-clean ]]; then
      printf 'preexisting dirty state\n' >"$AGENT_WORKTREE/preexisting-dirty.txt"
    fi
  )
  printf 'handoff\n' >"$AGENT_HANDOFF"
}

setup_worktree_sync_fixture() {
  local name="$1"
  local tmp_root="$TMP/$name"

  SYNC_PRIMARY="$tmp_root/primary"
  SYNC_WORKTREE="$tmp_root/wts/demo"

  mkdir -p "$tmp_root"
  git init -q -b main "$SYNC_PRIMARY"
  (
    cd "$SYNC_PRIMARY" || exit 1
    git config user.email tester@example.com
    git config user.name Tester
    mkdir -p scripts work/demo
    cp "$ROOT/scripts/worktree.sh" scripts/worktree.sh
    chmod +x scripts/worktree.sh
    printf 'worktrees:\n  dir: ../wts\n' >config.yaml
    printf '.DS_Store\nwork/*/scratch.bin\n' >.gitignore
    printf '# Primary plan\n' >work/demo/plan.md
    git add -A
    git commit -qm init
    git branch wt/demo
    git worktree add -q "$SYNC_WORKTREE" wt/demo
    git -C "$SYNC_WORKTREE" config user.email tester@example.com
    git -C "$SYNC_WORKTREE" config user.name Tester
    printf '# Worktree plan\nCode-review verdict: APPROVE\n' >"$SYNC_WORKTREE/work/demo/plan.md"
    git -C "$SYNC_WORKTREE" add work/demo/plan.md
    git -C "$SYNC_WORKTREE" commit -qm "record review sentinel"
    printf 'handoff\n' >work/demo/handoff.md
    printf 'notes v1\n' >work/demo/notes.md
    printf 'followup\n' >work/demo/followup-1.md
    printf 'codex\n' >work/demo/codex-review.md
    printf 'accented\n' >work/demo/résumé.md
    printf 'ignored primary stray\n' >work/demo/scratch.bin
    printf 'temp\n' >work/demo/.codex-review.tmpAB
    printf 'external secret\n' >"$tmp_root/external-secret.txt"
    ln -s "$tmp_root/external-secret.txt" work/demo/leak.md
    mkdir -p work/demo/sub
    printf 'nested\n' >work/demo/sub/x.md
    printf 'finder\n' >"$SYNC_WORKTREE/work/demo/.DS_Store"
  )
}

setup_fan_fixture() {
  local name="$1"
  local pass_mode="${2:-some}"
  local commit_mode="${3:-commit}"
  local gate_dirty="${4:-clean}"
  local tmp_root="$TMP/$name"

  FAN_PRIMARY="$tmp_root/primary"
  FAN_REMOTE="$tmp_root/origin.git"
  FAN_WTS="$tmp_root/wts"
  FAN_IMPL="$tmp_root/canned-implementer.sh"
  FAN_HANDOFF="$FAN_PRIMARY/work/demo/handoff.md"

  mkdir -p "$tmp_root"
  git init -q -b main "$FAN_PRIMARY"
  git init -q --bare "$FAN_REMOTE"
  (
    cd "$FAN_PRIMARY" || exit 1
    git config user.email tester@example.com
    git config user.name Tester
    git remote add origin "$FAN_REMOTE"

    mkdir -p scripts work/demo
    cp "$ROOT/scripts/worktree.sh" scripts/worktree.sh
    cp "$ROOT/scripts/agent-exec.sh" scripts/agent-exec.sh
    cp "$ROOT/scripts/fan-exec.sh" scripts/fan-exec.sh
    cat >scripts/gate.sh <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 1
tracked_result=$(git show HEAD:result.txt 2>/dev/null) || exit 1
[[ "$tracked_result" == pass ]] || exit 1
EOF
    if [[ "$gate_dirty" == dirty ]]; then
      cat >>scripts/gate.sh <<'EOF'
mkdir -p .pytest_cache
: >.pytest_cache/x
EOF
    fi
    chmod +x scripts/*.sh

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
          printf 'Code-review verdict: APPROVE\n'
          printf 'Codex-review verdict: APPROVE\n'
        } >work/demo/plan.md
        printf 'handoff\n' >work/demo/handoff.md
        printf 'codex review\n' >work/demo/codex-review.md
        printf 'demo\n' >work/.last-released
        printf 'learned\n' >work/demo/retro.md
        ;;
      branch-approve)
        {
          printf '# Demo\n\n'
          printf 'Plan verdict: APPROVE\n'
          printf 'Code-review verdict: APPROVE\n'
          printf 'Codex-review verdict: APPROVE\n'
        } >work/demo/plan.md
        printf 'handoff\n' >work/demo/handoff.md
        printf 'codex review\n' >work/demo/codex-review.md
        git add -A
        git commit -qm branch-plan
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
}

# --- shellcheck the scripts themselves (gate.sh covers this too; belt+braces)
if command -v shellcheck >/dev/null; then
  check "shellcheck scripts" shellcheck scripts/*.sh tests/*.sh
fi

# --- worktree.sh lifecycle in a throwaway repo
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# --- archi-fresh.sh freshness checks in hermetic git repos
setup_archi_fresh_fixture archi-fresh fresh
check_exit "archi-fresh passes when ARCHI is newer than source paths" 0 "" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"

setup_archi_fresh_fixture archi-stale stale
check_exit "archi-fresh reports stale source paths" 1 "skills/" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"
check_exit "archi-fresh stale message says to refresh branch ARCHI" 1 "refresh ARCHI on the branch" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"

setup_archi_fresh_fixture archi-equal equal
check_exit "archi-fresh treats equal epochs as fresh" 0 "" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"

setup_archi_fresh_fixture archi-ref branch-ref
check_exit "archi-fresh default ref checks current branch history" 0 "" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"
check_exit "archi-fresh explicit ref selects branch history" 1 "skills/" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh wt/demo"

setup_archi_fresh_fixture archi-missing missing-archi
check_exit "archi-fresh exits 2 when one side has no history" 2 "ARCHI.md has no git history" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"

check "archi-fresh help documents optional ref" bash -c "
  out=\$(bash scripts/archi-fresh.sh --help) &&
  grep -Fq 'Usage: scripts/archi-fresh.sh [<ref>]' <<<\"\$out\" &&
  grep -Fq 'Defaults to HEAD' <<<\"\$out\"
"

# --- state.sh derives cold-session work-unit state without writes
setup_state_fixture state-missing missing-plan
check_exit "state missing plan exits non-zero" 1 "not a work unit" bash -c "cd '$STATE_REPO' && bash scripts/state.sh demo"

setup_state_fixture state-plan plan
check "state derives plan stage" bash -c "
  cd '$STATE_REPO' &&
  out=\$(bash scripts/state.sh demo) &&
  grep -qx 'stage: plan' <<<\"\$out\" &&
  grep -qx 'next_action: finish /1-plan' <<<\"\$out\"
"

setup_state_fixture state-implement implement
check "state derives implement stage" bash -c "
  cd '$STATE_REPO' &&
  out=\$(bash scripts/state.sh demo) &&
  grep -qx 'stage: implement' <<<\"\$out\" &&
  grep -qx 'next_action: /2-implement' <<<\"\$out\"
"

setup_state_fixture state-review-gate review-gate
check "state derives review stage before codex review" bash -c "
  cd '$STATE_REPO' &&
  out=\$(bash scripts/state.sh demo) &&
  grep -qx 'stage: review' <<<\"\$out\" &&
  grep -qx 'review: pending' <<<\"\$out\" &&
  grep -qx 'next_action: run scripts/gate.sh' <<<\"\$out\"
"

setup_state_fixture state-release release
check "state derives release stage before marker" bash -c "
  cd '$STATE_REPO' &&
  out=\$(bash scripts/state.sh demo) &&
  grep -qx 'stage: release' <<<\"\$out\" &&
  grep -qx 'review: approve' <<<\"\$out\" &&
  grep -qx 'next_action: /4-release' <<<\"\$out\"
"

setup_state_fixture state-retro retro
check "state derives release stage for retro" bash -c "
  cd '$STATE_REPO' &&
  out=\$(bash scripts/state.sh demo) &&
  grep -qx 'stage: release' <<<\"\$out\" &&
  grep -qx 'next_action: /5-retro' <<<\"\$out\"
"

setup_state_fixture state-done "done"
check "state derives done stage" bash -c "
  cd '$STATE_REPO' &&
  out=\$(bash scripts/state.sh demo) &&
  grep -qx 'stage: done' <<<\"\$out\" &&
  grep -qx 'next_action: none' <<<\"\$out\"
"

setup_state_fixture state-branch-approve branch-approve
check "state reads review sentinels from wt branch when it exists" bash -c "
  cd '$STATE_REPO' &&
  out=\$(bash scripts/state.sh demo) &&
  grep -qx 'review: approve' <<<\"\$out\" &&
  ! grep -qx 'Code-review verdict: APPROVE' work/demo/plan.md
"

setup_state_fixture state-read-only release
check "state run is read-only" bash -c "
  cd '$STATE_REPO' &&
  before=\$(find . -path ./.git -prune -o -type f -print | sort) &&
  out=\$(bash scripts/state.sh demo) &&
  after=\$(find . -path ./.git -prune -o -type f -print | sort) &&
  grep -qx 'slug: demo' <<<\"\$out\" &&
  [ \"\$before\" = \"\$after\" ] &&
  [ \"\$(git status --porcelain)\" = '' ]
"

# Mutation pin: if state.sh treats either review sentinel as approval, this fixture
# moves from review/pending to release/approve and the check fails.
setup_state_fixture state-review-and-pin review-single-sentinel
check "state requires both review approval sentinels" bash -c "
  cd '$STATE_REPO' &&
  out=\$(bash scripts/state.sh demo) &&
  grep -qx 'stage: review' <<<\"\$out\" &&
  grep -qx 'review: pending' <<<\"\$out\" &&
  grep -qx 'next_action: /3-review' <<<\"\$out\"
"

# --- codex-review.sh pure-reader contract with a canned reviewer
check "codex-review reads plan body from branch" grep -F "git show \"\$branch:\$plan_path\"" scripts/codex-review.sh
check "codex-review reads config from main" grep -F "git show \"main:config.yaml\"" scripts/codex-review.sh
check "codex-review prompt names exact verdict format" grep -F 'Codex verdict: REQUEST CHANGES' scripts/codex-review.sh
check "codex-review emits verdict instruction after diff" awk '/--- DIFF/ {d=1} d && /Your final line must/ {found=1} END {exit !found}' scripts/codex-review.sh
check "codex-review reads deferrals from branch" grep -F "git show \"\$branch:\$deferrals_path\"" scripts/codex-review.sh
check "codex-review emits deferrals before the diff" awk '/--- ACCEPTED DEFERRALS/ {f=1} /--- DIFF/ {exit !f}' scripts/codex-review.sh
check "3-review skill routes deferrals to the ledger" grep -F 'work/<slug>/deferrals.md' skills/3-review/SKILL.md
check "code-reviewer agent is told deferrals are settled scope" grep -F 'work/<slug>/deferrals.md' .claude/agents/code-reviewer.md
check "code-reviewer agent defines severity taxonomy" grep -F "CRITICAL" .claude/agents/code-reviewer.md
check "code-reviewer agent has calibration section" grep -F "Calibration" .claude/agents/code-reviewer.md
check "code-reviewer agent requires concrete failure for blocking" grep -F "finding without a concrete failure scenario is LOW" .claude/agents/code-reviewer.md
check "codex-review prompt includes severity taxonomy" grep -F "CRITICAL" scripts/codex-review.sh
check "codex-review prompt includes calibration guidance" grep -F "Calibration" scripts/codex-review.sh
check "codex-review prompt passes round number" grep -F "REVIEW_ROUND" scripts/codex-review.sh
check "3-review skill tracks round counter" grep -F "work/<slug>/review-round" skills/3-review/SKILL.md
check "3-review skill routes by severity" grep -F "CRITICAL/HIGH" skills/3-review/SKILL.md
check "3-review skill caps at round 3 mechanically" grep -F "counter reaches 3" skills/3-review/SKILL.md
check "3-review skill keeps codex-review work artifacts out of diff" grep -F "git diff origin/main...wt/<slug> -- ':/' \":(exclude,top)work/<slug>\"" skills/3-review/SKILL.md

setup_codex_review_fixture codex-approve normal
check_exit "codex-review approve exits 0" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
check "codex-review writes stdout artifact" grep -Fx 'Codex verdict: APPROVE' "$COD_PRIMARY/work/demo/codex-review.md"

setup_codex_review_fixture codex-indented indented
check_exit "codex-review accepts indented approve verdict" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"

setup_codex_review_fixture codex-request request
check_exit "codex-review request-changes exits 1" 1 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"

setup_codex_review_fixture codex-branch-override branch-override
check_exit "codex-review ignores branch reviewer.command override" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"

setup_codex_review_fixture codex-missing-verdict missing-verdict
check_exit "codex-review missing verdict exits 2" 2 "no verdict" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"

setup_codex_review_fixture codex-command-absent absent
check_exit "codex-review missing reviewer.command exits 2" 2 "reviewer.command" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"

setup_codex_review_fixture codex-later-command later-command
check_exit "codex-review parser stops before later command" 2 "reviewer.command" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"

setup_codex_review_fixture codex-commented-command commented
check_exit "codex-review ignores commented command and uses real one" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"

setup_codex_review_fixture codex-missing-plan missing-plan
check_exit "codex-review missing branch plan exits 2 before reviewer" 2 "cannot read plan" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
check "codex-review does not invoke reviewer when branch plan is missing" test ! -e "$COD_MARKER"

setup_codex_review_fixture codex-reviewer-fails reviewer-fails
printf 'previous artifact\nCodex verdict: REQUEST CHANGES\n' >"$COD_PRIMARY/work/demo/codex-review.md"
check_exit "codex-review reviewer failure exits 2 before verdict parsing" 2 "reviewer command failed (exit 42)" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
check "codex-review reviewer failure preserves previous artifact" bash -c "
  diff -u <(printf 'previous artifact\nCodex verdict: REQUEST CHANGES\n') '$COD_PRIMARY/work/demo/codex-review.md'
"

setup_codex_review_fixture codex-from-worktree normal
check_exit "codex-review refuses wt checkout as root" 2 "primary checkout" bash -c "cd '$COD_WORKTREE' && bash '$COD_PRIMARY/scripts/codex-review.sh' demo"

setup_codex_review_fixture codex-artifact-only normal
check_exit "codex-review artifact-only run exits 0" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
check "codex-review only dirties primary artifact" bash -c "
  cd '$COD_PRIMARY' &&
  diff -u <(printf '?? work/demo/codex-review.md\n') <(git status --porcelain)
"
check "codex-review leaves worktree branch clean" bash -c "[ \"\$(git -C '$COD_WORKTREE' status --porcelain)\" = '' ]"

setup_codex_review_fixture codex-excludes-work-artifacts capture-prompt
printf 'do-not-leak-review-artifact\n' >"$COD_WORKTREE/work/demo/notes.md"
git -C "$COD_WORKTREE" add work/demo/notes.md
git -C "$COD_WORKTREE" commit -qm "record synced artifact"
check_exit "codex-review with branch artifacts exits 0" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
check "codex-review excludes work unit artifacts from reviewer diff" bash -c "
  ! grep -Fq 'do-not-leak-review-artifact' '$TMP/codex-excludes-work-artifacts/prompt.txt'
"
mkdir -p "$COD_PRIMARY/subdir"
check_exit "codex-review from subdirectory exits 0" 0 "" bash -c "cd '$COD_PRIMARY/subdir' && bash ../scripts/codex-review.sh demo"
check "codex-review from subdirectory includes top-level branch diff" grep -F '+feature' "$TMP/codex-excludes-work-artifacts/prompt.txt"
check "codex-review from subdirectory excludes work unit artifacts" bash -c "
  ! grep -Fq 'do-not-leak-review-artifact' '$TMP/codex-excludes-work-artifacts/prompt.txt'
"
check "codex-review marks an absent deferral ledger explicitly" bash -c "
  grep -Fq '(none recorded)' '$TMP/codex-excludes-work-artifacts/prompt.txt'
"

setup_codex_review_fixture codex-deferrals capture-prompt
printf '# Deferrals\n\n- version bump on NEEDS_REFINEMENT -> deferred to work/version-bump\n' \
  >"$COD_WORKTREE/work/demo/deferrals.md"
git -C "$COD_WORKTREE" add work/demo/deferrals.md
git -C "$COD_WORKTREE" commit -qm "record accepted deferral"
check_exit "codex-review with a deferral ledger exits 0" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
check "codex-review injects the deferral ledger into the prompt" bash -c "
  grep -Fq 'version bump on NEEDS_REFINEMENT' '$TMP/codex-deferrals/prompt.txt'
"
check "codex-review deferral ledger is not treated as absent" bash -c "
  ! grep -Fq '(none recorded)' '$TMP/codex-deferrals/prompt.txt'
"

check "codex-review prompt includes round number from REVIEW_ROUND" bash -c "
  grep -Fq 'review round' '$TMP/codex-deferrals/prompt.txt'
"

setup_codex_review_fixture codex-round-env capture-prompt
check_exit "codex-review passes custom round number" 0 "" bash -c "cd '$COD_PRIMARY' && REVIEW_ROUND=3 bash scripts/codex-review.sh demo"
check "codex-review prompt contains round 3" bash -c "
  grep -Fq 'round 3' '$TMP/codex-round-env/prompt.txt'
"

setup_codex_review_fixture codex-origin-main-ahead origin-main-ahead
check_exit "codex-review excludes origin-main-only changes" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
check "codex-review bases diff on origin/main when local main is stale" bash -c "
  grep -Fq -- '--- DIFF (origin/main...wt/demo excluding work/demo) ---' '$TMP/codex-origin-main-ahead/prompt.txt' &&
  grep -Fq '+feature' '$TMP/codex-origin-main-ahead/prompt.txt' &&
  ! grep -Fq 'remote-only' '$TMP/codex-origin-main-ahead/prompt.txt'
"

setup_codex_review_fixture codex-no-origin-fallback capture-prompt
check_exit "codex-review falls back to local main without origin/main" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
check "codex-review fallback prompt uses local main base" bash -c "
  grep -Fq -- '--- DIFF (main...wt/demo excluding work/demo) ---' '$TMP/codex-no-origin-fallback/prompt.txt' &&
  grep -Fq '+feature' '$TMP/codex-no-origin-fallback/prompt.txt'
"

(
  cd "$TMP"
  git init -q -b main sandbox && cd sandbox
  git commit -q --allow-empty -m init
  cp "$ROOT/scripts/worktree.sh" wt.sh
  printf 'worktrees:\n  dir: ../wts\n' > config.yaml
  git add -A && git commit -qm files
) || { echo "FAIL: sandbox setup"; exit 1; }

SB="$TMP/sandbox"
WT_PATH=$(cd "$SB" && bash wt.sh add demo 2>/dev/null)
check "worktree add creates directory" test -d "$WT_PATH"
check "worktree branch checked out" bash -c "cd '$WT_PATH' && [ \"\$(git branch --show-current)\" = wt/demo ]"
check "worktree.sh works FROM INSIDE a worktree (.git-as-file)" bash -c "cd '$WT_PATH' && bash wt.sh list"
check "worktree remove" bash -c "cd '$SB' && bash wt.sh remove demo"
check_fails "worktree add without slug fails" bash -c "cd '$SB' && bash wt.sh add"

BASE_FEATURE="$TMP/base-feature"
BASE_FEATURE_REMOTE="$TMP/base-feature.git"
git init -q -b main "$BASE_FEATURE"
git init -q --bare "$BASE_FEATURE_REMOTE"
(
  cd "$BASE_FEATURE" || exit 1
  git config user.email tester@example.com
  git config user.name Tester
  git remote add origin "$BASE_FEATURE_REMOTE"
  mkdir -p scripts
  cp "$ROOT/scripts/worktree.sh" scripts/worktree.sh
  printf 'worktrees:\n  dir: ../base-feature-wts\n' >config.yaml
  printf 'main\n' >main.txt
  git add -A
  git commit -qm main
  git push -q -u origin main
  git switch -q -c feature
  printf 'feature\n' >feature.txt
  git add feature.txt
  git commit -qm feature
)
BASE_FEATURE_WT=$(cd "$BASE_FEATURE" && bash scripts/worktree.sh add clean-base 2>/dev/null)
check "worktree add bases new branch on origin/main from feature branch" bash -c "
  cd '$BASE_FEATURE' &&
  [ \"\$(git merge-base wt/clean-base origin/main)\" = \"\$(git rev-parse origin/main)\" ] &&
  ! git -C '$BASE_FEATURE_WT' rev-parse --verify --quiet HEAD:feature.txt
"

NO_ORIGIN="$TMP/no-origin-main"
git init -q -b main "$NO_ORIGIN"
(
  cd "$NO_ORIGIN" || exit 1
  git config user.email tester@example.com
  git config user.name Tester
  mkdir -p scripts
  cp "$ROOT/scripts/worktree.sh" scripts/worktree.sh
  printf 'worktrees:\n  dir: ../no-origin-wts\n' >config.yaml
  git add -A
  git commit -qm init
)
NO_ORIGIN_HEAD=$(git -C "$NO_ORIGIN" rev-parse HEAD)
NO_ORIGIN_WT=$(cd "$NO_ORIGIN" && bash scripts/worktree.sh add no-origin 2>/dev/null)
check "worktree add falls back to HEAD without origin/main" bash -c "
  [ -d '$NO_ORIGIN_WT' ] &&
  [ \"\$(git -C '$NO_ORIGIN' rev-parse wt/no-origin)\" = '$NO_ORIGIN_HEAD' ]
"

STALE_REPO="$TMP/stale-origin-main"
STALE_REMOTE="$TMP/stale-origin-main.git"
git init -q -b main "$STALE_REPO"
git init -q --bare "$STALE_REMOTE"
(
  cd "$STALE_REPO" || exit 1
  git config user.email tester@example.com
  git config user.name Tester
  git remote add origin "$STALE_REMOTE"
  mkdir -p scripts
  cp "$ROOT/scripts/worktree.sh" scripts/worktree.sh
  printf 'worktrees:\n  dir: ../stale-wts\n' >config.yaml
  printf 'base\n' >base.txt
  git add -A
  git commit -qm base
  git push -q -u origin main
  printf 'head only\n' >head-only.txt
  git add head-only.txt
  git commit -qm head-only
  git remote set-url origin "$TMP/missing-remote.git"
)
STALE_WT=$(cd "$STALE_REPO" && bash scripts/worktree.sh add stale-base 2>/dev/null)
check "worktree add uses stale origin/main when fetch fails" bash -c "
  cd '$STALE_REPO' &&
  [ \"\$(git rev-parse wt/stale-base)\" = \"\$(git rev-parse origin/main)\" ] &&
  ! git -C '$STALE_WT' rev-parse --verify --quiet HEAD:head-only.txt
"

SEED_REPO="$TMP/seed-plan"
SEED_REMOTE="$TMP/seed-plan.git"
git init -q -b main "$SEED_REPO"
git init -q --bare "$SEED_REMOTE"
(
  cd "$SEED_REPO" || exit 1
  git config user.email tester@example.com
  git config user.name Tester
  git remote add origin "$SEED_REMOTE"
  mkdir -p scripts work/seeded
  cp "$ROOT/scripts/worktree.sh" scripts/worktree.sh
  printf 'worktrees:\n  dir: ../seed-wts\n' >config.yaml
  git add config.yaml scripts
  git commit -qm init
  git push -q -u origin main
  printf '# Seeded plan\n' >work/seeded/plan.md
)
SEED_WT=$(cd "$SEED_REPO" && bash scripts/worktree.sh add seeded 2>/dev/null)
check "worktree add commits plan.md and leaves worktree clean" bash -c "
  cd '$SEED_REPO' &&
  [ -n \"\$(git ls-tree -r --name-only wt/seeded -- work/seeded/plan.md)\" ] &&
  [ \"\$(git -C '$SEED_WT' status --porcelain)\" = '' ]
"
SEED_PLAN_COMMITS_BEFORE=$(git -C "$SEED_REPO" log --format=%s wt/seeded | grep -c '^Record plan for seeded$')
git -C "$SEED_REPO" worktree remove "$SEED_WT" >/dev/null
SEED_WT_RESUME=$(cd "$SEED_REPO" && bash scripts/worktree.sh add seeded 2>/dev/null)
SEED_PLAN_COMMITS_AFTER=$(git -C "$SEED_REPO" log --format=%s wt/seeded | grep -c '^Record plan for seeded$')
check "worktree add resume path does not duplicate plan commit" bash -c "
  [ -d '$SEED_WT_RESUME' ] &&
  [ '$SEED_PLAN_COMMITS_BEFORE' = 1 ] &&
  [ '$SEED_PLAN_COMMITS_AFTER' = 1 ]
"

setup_worktree_sync_fixture sync-artifacts
check_exit "worktree sync-artifacts without slug fails" 1 "usage: worktree.sh sync-artifacts <slug>" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts"
mkdir -p "$SYNC_PRIMARY/work/no-wt"
check_exit "worktree sync-artifacts refuses missing worktree" 1 "no worktree for no-wt" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts no-wt"
(
  cd "$SYNC_PRIMARY" || exit 1
  git branch wt/no-primary
  git worktree add -q ../wts/no-primary wt/no-primary
)
check_exit "worktree sync-artifacts refuses missing primary work dir" 1 "primary checkout has no work/no-primary directory" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts no-primary"
check_exit "worktree sync-artifacts refuses invocation from unit worktree" 1 "sync-artifacts must run from the primary checkout" bash -c "cd '$SYNC_WORKTREE' && bash scripts/worktree.sh sync-artifacts demo"

mkdir -p "$SYNC_WORKTREE/work/demo/sub"
printf 'worktree-side\n' >"$SYNC_WORKTREE/work/demo/sub/worktree-side.md"
check_exit "worktree sync-artifacts copies primary artifacts" 0 "" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
sync_tree="$TMP/sync-artifacts-tree.out"
git -C "$SYNC_PRIMARY" -c core.quotePath=false ls-tree -r --name-only wt/demo -- work/demo >"$sync_tree"
check "worktree sync-artifacts records handoff notes followup and codex review" bash -c "
  grep -Fx work/demo/handoff.md '$sync_tree' &&
  grep -Fx work/demo/notes.md '$sync_tree' &&
  grep -Fx work/demo/followup-1.md '$sync_tree' &&
  grep -Fx work/demo/codex-review.md '$sync_tree'
"
check "worktree sync-artifacts commits non-ASCII artifact filename" grep -Fx "work/demo/résumé.md" "$sync_tree"
check "worktree sync-artifacts preserves worktree plan sentinels" grep -Fx "Code-review verdict: APPROVE" "$SYNC_WORKTREE/work/demo/plan.md"
check "worktree sync-artifacts excludes dotfiles and subdirectories" bash -c "
  ! grep -Fx work/demo/.codex-review.tmpAB '$sync_tree' &&
  ! grep -Fx work/demo/sub/x.md '$sync_tree' &&
  ! grep -Fx work/demo/.DS_Store '$sync_tree'
"
check "worktree sync-artifacts keeps ignored primary stray absent after successful sync" bash -c "
  ! grep -Fx work/demo/scratch.bin '$sync_tree'
"
check "worktree sync-artifacts deliberately commits existing worktree-side unit files" grep -Fx work/demo/sub/worktree-side.md "$sync_tree"
check "worktree sync-artifacts does not materialize symlink targets" bash -c "
  ! grep -Fx work/demo/leak.md '$sync_tree' &&
  ! git -C '$SYNC_PRIMARY' grep -q 'external secret' wt/demo -- work/demo
"
check "worktree sync-artifacts leaves worktree clean" bash -c "[ \"\$(git -C '$SYNC_WORKTREE' status --porcelain)\" = '' ]"
sync_commits_before=$(git -C "$SYNC_PRIMARY" log --format=%s wt/demo | grep -c '^Record artifacts for demo$')
check_exit "worktree sync-artifacts idempotent no-op exits zero" 0 "" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
sync_commits_after=$(git -C "$SYNC_PRIMARY" log --format=%s wt/demo | grep -c '^Record artifacts for demo$')
check "worktree sync-artifacts no-op makes no extra commit" bash -c "[ '$sync_commits_before' = 1 ] && [ '$sync_commits_after' = 1 ]"
printf 'notes v2\n' >"$SYNC_PRIMARY/work/demo/notes.md"
check_exit "worktree sync-artifacts refreshes changed artifact" 0 "" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
check "worktree sync-artifacts copied refreshed notes" bash -c "[ \"\$(cat '$SYNC_WORKTREE/work/demo/notes.md')\" = 'notes v2' ]"

setup_worktree_sync_fixture sync-plan-pending
printf 'Codex-review verdict: APPROVE\n' >>"$SYNC_WORKTREE/work/demo/plan.md"
check_exit "worktree sync-artifacts leaves pending worktree plan edit uncommitted" 0 "" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
check "worktree sync-artifacts keeps pending plan edit in worktree" grep -Fx "Codex-review verdict: APPROVE" "$SYNC_WORKTREE/work/demo/plan.md"
check "worktree sync-artifacts artifact commit excludes pending plan edit" bash -c "
  ! git -C '$SYNC_PRIMARY' show wt/demo:work/demo/plan.md | grep -Fx 'Codex-review verdict: APPROVE' &&
  git -C '$SYNC_WORKTREE' status --porcelain | grep -Fx ' M work/demo/plan.md'
"

setup_worktree_sync_fixture sync-unrelated-staged
printf 'staged unrelated\n' >"$SYNC_WORKTREE/AGENTS.md"
git -C "$SYNC_WORKTREE" add AGENTS.md
check_exit "worktree sync-artifacts ignores unrelated staged files" 0 "" bash -c "cd '$SYNC_PRIMARY' && bash scripts/worktree.sh sync-artifacts demo"
check "worktree sync-artifacts commit excludes unrelated staged file" bash -c "
  ! git -C '$SYNC_PRIMARY' ls-tree -r --name-only wt/demo -- AGENTS.md | grep -q . &&
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
     "name": "stdout",
     "output_type": "stream",
     "text": ["trained\n"]
    }
   ],
   "source": ["print('trained')\n"]
  }
 ],
 "metadata": {},
 "nbformat": 4,
 "nbformat_minor": 5
}
EOF
  cat >notebooks/cb/clean.ipynb <<'EOF'
{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": ["print('clean')\n"]
  }
 ],
 "metadata": {},
 "nbformat": 4,
 "nbformat_minor": 5
}
EOF
  git add -A
  git commit -qm notebooks
)
check_fails "notebook hook flags dirty tracked notebook" bash -c "cd '$NB_REPO' && bash scripts/gate.d/nb-clean.sh"
cp "$NB_REPO/notebooks/cb/clean.ipynb" "$NB_REPO/notebooks/cb/dirty.ipynb"
check "notebook hook passes cleaned tracked notebook" bash -c "cd '$NB_REPO' && bash scripts/gate.d/nb-clean.sh"

# --- opt-in data-science hygiene hook
DS_REPO="$TMP/ds-hygiene"
git init -q -b main "$DS_REPO"
(
  cd "$DS_REPO" || exit 1
  git config user.email tester@example.com
  git config user.name Tester
  mkdir -p scripts/gate.d data src tests/fixtures
  cp "$ROOT/scripts/gate.d/examples/ds-hygiene.sh" scripts/gate.d/ds-hygiene.sh
  printf '01234567890123456789\n' >data/too-big.parquet
  printf '01234567890123456789\n' >tests/fixtures/allowed.csv
  printf 'DATA_ROOT = "/Users/someone/data"\n' >src/user_path.py
  printf "DATA_ROOT = 'C:\\\\data'\n" >src/windows_path.py
  git add -A
  git commit -qm ds-hygiene
)
check_exit "ds hygiene hook flags oversized tracked artifact" 1 "data/too-big.parquet" bash -c "cd '$DS_REPO' && DS_DATA_MAX_BYTES=10 bash scripts/gate.d/ds-hygiene.sh"
check "ds hygiene hook exempts default allowed directory" bash -c "cd '$DS_REPO' && out=\$(DS_DATA_MAX_BYTES=10 bash scripts/gate.d/ds-hygiene.sh 2>&1); ! grep -q allowed.csv <<<\"\$out\""
check_exit "ds hygiene hook treats empty allow dirs as no allowed dirs" 1 "tests/fixtures/allowed.csv" bash -c "cd '$DS_REPO' && DS_DATA_MAX_BYTES=10 DS_DATA_ALLOW_DIRS='' bash scripts/gate.d/ds-hygiene.sh"
check_exit "ds hygiene hook flags Unix local path in Python" 1 "src/user_path.py" bash -c "cd '$DS_REPO' && DS_DATA_MAX_BYTES=1000 bash scripts/gate.d/ds-hygiene.sh"
check_exit "ds hygiene hook flags Windows local path in Python" 1 "src/windows_path.py" bash -c "cd '$DS_REPO' && DS_DATA_MAX_BYTES=1000 bash scripts/gate.d/ds-hygiene.sh"
check_exit "ds hygiene hook still flags artifact when path scan is disabled" 1 "data/too-big.parquet" bash -c "cd '$DS_REPO' && DS_DATA_MAX_BYTES=10 DS_PATH_SCAN='' bash scripts/gate.d/ds-hygiene.sh"
check_exit "ds hygiene hook still flags local path when artifact scan is disabled" 1 "src/user_path.py" bash -c "cd '$DS_REPO' && DS_DATA_MAX_BYTES='' bash scripts/gate.d/ds-hygiene.sh"

DS_ARTIFACT_ONLY_REPO="$TMP/ds-hygiene-artifact-only"
git init -q -b main "$DS_ARTIFACT_ONLY_REPO"
(
  cd "$DS_ARTIFACT_ONLY_REPO" || exit 1
  git config user.email tester@example.com
  git config user.name Tester
  mkdir -p scripts/gate.d data src
  cp "$ROOT/scripts/gate.d/examples/ds-hygiene.sh" scripts/gate.d/ds-hygiene.sh
  printf '01234567890123456789\n' >data/too-big.parquet
  printf 'DATA_ROOT = "relative/data"\n' >src/clean.py
  git add -A
  git commit -qm ds-hygiene-artifact-only
)
check "ds hygiene hook disables artifact scan independently" bash -c "cd '$DS_ARTIFACT_ONLY_REPO' && out=\$(DS_DATA_MAX_BYTES='' bash scripts/gate.d/ds-hygiene.sh 2>&1); status=\$?; [[ \"\$status\" -eq 0 ]] && [[ -z \"\$out\" ]]"

DS_BOTH_FAIL_REPO="$TMP/ds-hygiene-both-fail"
git init -q -b main "$DS_BOTH_FAIL_REPO"
(
  cd "$DS_BOTH_FAIL_REPO" || exit 1
  git config user.email tester@example.com
  git config user.name Tester
  mkdir -p scripts/gate.d data src
  cp "$ROOT/scripts/gate.d/examples/ds-hygiene.sh" scripts/gate.d/ds-hygiene.sh
  printf '01234567890123456789\n' >data/both.parquet
  printf 'DATA_ROOT = "/Users/someone/data"\n' >src/both_path.py
  git add -A
  git commit -qm ds-hygiene-both-fail
)
check "ds hygiene hook reports artifact and local path together" bash -c "cd '$DS_BOTH_FAIL_REPO' && out=\$(DS_DATA_MAX_BYTES=10 bash scripts/gate.d/ds-hygiene.sh 2>&1 >/dev/null); status=\$?; [[ \"\$status\" -eq 1 ]] && grep -Fq data/both.parquet <<<\"\$out\" && grep -Fq src/both_path.py <<<\"\$out\""

DS_CLEAN_REPO="$TMP/ds-hygiene-clean"
git init -q -b main "$DS_CLEAN_REPO"
(
  cd "$DS_CLEAN_REPO" || exit 1
  git config user.email tester@example.com
  git config user.name Tester
  mkdir -p scripts/gate.d data src tests/fixtures
  cp "$ROOT/scripts/gate.d/examples/ds-hygiene.sh" scripts/gate.d/ds-hygiene.sh
  printf 'small\n' >tests/fixtures/small.csv
  printf '0123456789' >data/exact.npy
  printf 'DATA_ROOT = "relative/data"\n' >src/clean.py
  git add -A
  git commit -qm ds-hygiene-clean
)
check "ds hygiene hook passes clean fixture" bash -c "cd '$DS_CLEAN_REPO' && DS_DATA_MAX_BYTES=10 bash scripts/gate.d/ds-hygiene.sh"

DS_PATH_ONLY_REPO="$TMP/ds-hygiene-path-only"
git init -q -b main "$DS_PATH_ONLY_REPO"
(
  cd "$DS_PATH_ONLY_REPO" || exit 1
  git config user.email tester@example.com
  git config user.name Tester
  mkdir -p scripts/gate.d src
  cp "$ROOT/scripts/gate.d/examples/ds-hygiene.sh" scripts/gate.d/ds-hygiene.sh
  printf 'DATA_ROOT = "/home/someone/data"\n' >src/path.py
  git add -A
  git commit -qm ds-hygiene-path-only
)
check "ds hygiene hook disables path scan independently" bash -c "cd '$DS_PATH_ONLY_REPO' && DS_PATH_SCAN='' bash scripts/gate.d/ds-hygiene.sh"

DS_DELETED_REPO="$TMP/ds-hygiene-deleted"
git init -q -b main "$DS_DELETED_REPO"
(
  cd "$DS_DELETED_REPO" || exit 1
  git config user.email tester@example.com
  git config user.name Tester
  mkdir -p scripts/gate.d data
  cp "$ROOT/scripts/gate.d/examples/ds-hygiene.sh" scripts/gate.d/ds-hygiene.sh
  printf '01234567890123456789\n' >data/deleted.parquet
  git add -A
  git commit -qm ds-hygiene-deleted
  rm data/deleted.parquet
)
check "ds hygiene hook skips deleted tracked artifact without stderr" bash -c "cd '$DS_DELETED_REPO' && out=\$(DS_DATA_MAX_BYTES=10 bash scripts/gate.d/ds-hygiene.sh 2>&1 >/dev/null); status=\$?; [[ \"\$status\" -eq 0 ]] && [[ -z \"\$out\" ]]"

DS_ALLOW_LIST_REPO="$TMP/ds-hygiene-allow-list"
git init -q -b main "$DS_ALLOW_LIST_REPO"
(
  cd "$DS_ALLOW_LIST_REPO" || exit 1
  git config user.email tester@example.com
  git config user.name Tester
  mkdir -p scripts/gate.d tests/fixtures data/samples
  cp "$ROOT/scripts/gate.d/examples/ds-hygiene.sh" scripts/gate.d/ds-hygiene.sh
  printf '01234567890123456789\n' >tests/fixtures/allowed.csv
  printf '01234567890123456789\n' >data/samples/allowed.csv
  git add -A
  git commit -qm ds-hygiene-allow-list
)
check "ds hygiene hook honours colon-separated allow dirs" bash -c "cd '$DS_ALLOW_LIST_REPO' && DS_DATA_MAX_BYTES=10 DS_DATA_ALLOW_DIRS=tests/fixtures:data/samples bash scripts/gate.d/ds-hygiene.sh"

DS_EMPTY_PREFIX_REPO="$TMP/ds-hygiene-empty-prefix"
git init -q -b main "$DS_EMPTY_PREFIX_REPO"
(
  cd "$DS_EMPTY_PREFIX_REPO" || exit 1
  git config user.email tester@example.com
  git config user.name Tester
  mkdir -p scripts/gate.d data/samples data/raw
  cp "$ROOT/scripts/gate.d/examples/ds-hygiene.sh" scripts/gate.d/ds-hygiene.sh
  printf 'small\n' >data/samples/allowed.csv
  printf '01234567890123456789\n' >data/raw/outside.csv
  git add -A
  git commit -qm ds-hygiene-empty-prefix
)
check_exit "ds hygiene hook ignores empty allow-dir prefix" 1 "data/raw/outside.csv" bash -c "cd '$DS_EMPTY_PREFIX_REPO' && DS_DATA_MAX_BYTES=10 DS_DATA_ALLOW_DIRS=':data/samples' bash scripts/gate.d/ds-hygiene.sh"

# --- fan-exec.sh dispatch/adopt in a hermetic repo with a canned implementer
setup_fan_fixture fan-basic
fan_manifest="$TMP/fan-manifest.out"
check "fan dispatch manifest lists only gate passers" bash -c "
  cd '$FAN_PRIMARY' &&
  bash scripts/fan-exec.sh dispatch demo '$FAN_HANDOFF' 3 >'$fan_manifest' &&
  diff -u <(printf 'wt/demo-fan-2\nwt/demo-fan-3\n') '$fan_manifest'
"
check "fan adopt repoints canonical branch and cleans samples" bash -c "
  cd '$FAN_PRIMARY' &&
  bash scripts/fan-exec.sh adopt demo wt/demo-fan-3 &&
  [ \"\$(git rev-parse wt/demo)\" = \"\$(git -C '$FAN_WTS/demo' rev-parse HEAD)\" ] &&
  [ \"\$(cat '$FAN_WTS/demo/branch.txt')\" = 'wt/demo-fan-3' ] &&
  ! git show-ref --verify --quiet refs/heads/wt/demo-fan-1 &&
  ! git show-ref --verify --quiet refs/heads/wt/demo-fan-2 &&
  ! git show-ref --verify --quiet refs/heads/wt/demo-fan-3 &&
  [ ! -e '$FAN_WTS/demo-fan-1' ] &&
  [ ! -e '$FAN_WTS/demo-fan-2' ] &&
  [ ! -e '$FAN_WTS/demo-fan-3' ]
"
setup_fan_fixture fan-no-commit some no-commit
fan_no_commit_manifest="$TMP/fan-no-commit-manifest.out"
check "fan dispatch auto-commits non-committing sample work" bash -c "
  cd '$FAN_PRIMARY' &&
  bash scripts/fan-exec.sh dispatch demo '$FAN_HANDOFF' 3 >'$fan_no_commit_manifest' &&
  diff -u <(printf 'wt/demo-fan-2\nwt/demo-fan-3\n') '$fan_no_commit_manifest' &&
  [ \"\$(git show wt/demo-fan-2:result.txt)\" = pass ] &&
  [ \"\$(git show wt/demo-fan-2:branch.txt)\" = wt/demo-fan-2 ] &&
  [ -z \"\$(git ls-tree -r --name-only wt/demo-fan-2 -- work/demo)\" ] &&
  [ -f '$FAN_WTS/demo-fan-2/work/demo/plan.md' ] &&
  [ \"\$(git log -1 --format=%s wt/demo-fan-2)\" = 'Fan sample implementation for wt/demo-fan-2' ]
"
fan_no_commit_diff="$TMP/fan-no-commit-diff.out"
check "fan adopt preserves auto-committed sample work and cleans samples" bash -c "
  cd '$FAN_PRIMARY' &&
  bash scripts/fan-exec.sh adopt demo wt/demo-fan-2 &&
  [ \"\$(git rev-parse wt/demo)\" = \"\$(git -C '$FAN_WTS/demo' rev-parse HEAD)\" ] &&
  [ \"\$(cat '$FAN_WTS/demo/result.txt')\" = pass ] &&
  [ \"\$(cat '$FAN_WTS/demo/branch.txt')\" = 'wt/demo-fan-2' ] &&
  [ \"\$(git -C '$FAN_WTS/demo' status --porcelain)\" = '' ] &&
  git diff --name-only main...wt/demo >'$fan_no_commit_diff' &&
  grep -Fx result.txt '$fan_no_commit_diff' &&
  grep -Fx branch.txt '$fan_no_commit_diff' &&
  grep -Fx work/demo/plan.md '$fan_no_commit_diff' &&
  diff -u <(printf 'work/demo/plan.md\n') <(grep -E '^work/demo/' '$fan_no_commit_diff') &&
  ! git show-ref --verify --quiet refs/heads/wt/demo-fan-1 &&
  ! git show-ref --verify --quiet refs/heads/wt/demo-fan-2 &&
  ! git show-ref --verify --quiet refs/heads/wt/demo-fan-3 &&
  [ ! -e '$FAN_WTS/demo-fan-1' ] &&
  [ ! -e '$FAN_WTS/demo-fan-2' ] &&
  [ ! -e '$FAN_WTS/demo-fan-3' ]
"
setup_fan_fixture fan-dirty-gate some no-commit dirty
fan_dirty_gate_manifest="$TMP/fan-dirty-gate-manifest.out"
check "fan adopt force-cleans dirty sample worktrees and branches" bash -c "
  cd '$FAN_PRIMARY' &&
  bash scripts/fan-exec.sh dispatch demo '$FAN_HANDOFF' 3 >'$fan_dirty_gate_manifest' &&
  diff -u <(printf 'wt/demo-fan-2\nwt/demo-fan-3\n') '$fan_dirty_gate_manifest' &&
  [ -f '$FAN_WTS/demo-fan-2/.pytest_cache/x' ] &&
  bash scripts/fan-exec.sh adopt demo wt/demo-fan-3 &&
  ! git show-ref --verify --quiet refs/heads/wt/demo-fan-1 &&
  ! git show-ref --verify --quiet refs/heads/wt/demo-fan-2 &&
  ! git show-ref --verify --quiet refs/heads/wt/demo-fan-3 &&
  [ ! -e '$FAN_WTS/demo-fan-1' ] &&
  [ ! -e '$FAN_WTS/demo-fan-2' ] &&
  [ ! -e '$FAN_WTS/demo-fan-3' ]
"
setup_fan_fixture fan-all-fail all-fail
fan_empty_manifest="$TMP/fan-empty-manifest.out"
check "fan dispatch emits empty manifest and exits 0 with no survivors" bash -c "
  cd '$FAN_PRIMARY' &&
  bash scripts/fan-exec.sh dispatch demo '$FAN_HANDOFF' 3 >'$fan_empty_manifest' &&
  [ ! -s '$fan_empty_manifest' ]
"

# --- release.sh version comparison
check "release version compare accepts .10 over .9" bash scripts/release.sh check-version 2026.8.10 2026.8.9
check_fails "release version compare rejects .9 after .10" bash scripts/release.sh check-version 2026.8.9 2026.8.10

# --- release.sh refusals and happy path in the mandated worktree topology
setup_release_fixture release-no-verdict 2026.8.9 "Plan verdict: APPROVE" pass fresh
check_fails "release refuses without code-review approval" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"

setup_release_fixture release-no-codex-verdict 2026.8.9 "Code-review verdict: APPROVE" pass fresh ""
check_exit "release refuses without codex-review approval" 1 "Codex-review verdict: APPROVE" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"

setup_release_fixture release-gate-fails 2026.8.9 "Code-review verdict: APPROVE" fail fresh
check_fails "release refuses when gate fails" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"

setup_release_fixture release-archi-stale 2026.8.9 "Code-review verdict: APPROVE" pass stale
check_fails "release refuses when ARCHI.md is stale" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"

setup_release_fixture release-version-regresses 2026.9.0 "Code-review verdict: APPROVE" pass fresh
check_fails "release refuses when computed version does not exceed VERSION" bash -c "cd '$REL_WORKTREE' && PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo"

setup_release_fixture release-happy-primary 2026.8.9 "Code-review verdict: APPROVE" pass fresh
main_before=$(git -C "$REL_PRIMARY" rev-parse main)
check "release can be invoked from primary checkout" bash -c "
  cd '$REL_PRIMARY' &&
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo &&
  [ \"\$(git -C '$REL_PRIMARY' rev-parse main)\" = '$main_before' ] &&
  [ \"\$(cat '$REL_PRIMARY/VERSION')\" = 2026.8.9 ] &&
  [ \"\$(cat '$REL_WORKTREE/VERSION')\" = 2026.8.10 ] &&
  ! git -C '$REL_WORKTREE' rev-parse --verify --quiet refs/tags/v2026.8.10
"

setup_release_fixture release-single 2026.8.9 "Code-review verdict: APPROVE" pass fresh
origin_before=$(git -C "$REL_PRIMARY" rev-parse origin/main)
main_before=$(git -C "$REL_PRIMARY" rev-parse main)
check "release commits bump on branch without touching main, origin/main, or tagging" bash -c "
  cd '$REL_WORKTREE' &&
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo &&
  [ \"\$(git -C '$REL_PRIMARY' rev-parse main)\" = '$main_before' ] &&
  [ \"\$(git -C '$REL_PRIMARY' rev-parse origin/main)\" = '$origin_before' ] &&
  [ \"\$(cat VERSION)\" = 2026.8.10 ] &&
  [ \"\$(git log -1 --format=%s)\" = 'Release v2026.8.10' ] &&
  ! git rev-parse --verify --quiet refs/tags/v2026.8.10
"

setup_release_fixture release-marker-written 2026.8.9 "Code-review verdict: APPROVE" pass fresh
check "release writes last-released marker into release commit" bash -c "
  cd '$REL_WORKTREE' &&
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo &&
  [ \"\$(cat work/.last-released)\" = demo ] &&
  [ \"\$(git show HEAD:work/.last-released)\" = demo ]
"

setup_release_fixture release-marker-rollback 2026.8.9 "Code-review verdict: APPROVE" pass fresh
cat >"$REL_PRIMARY/.git/hooks/pre-commit" <<'EOF'
#!/usr/bin/env bash
exit 1
EOF
chmod +x "$REL_PRIMARY/.git/hooks/pre-commit"
check "release rollback removes first-time last-released marker" bash -c "
  cd '$REL_WORKTREE'
  rollback_out='$TMP/release-marker-rollback.out'
  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo >\"\$rollback_out\" 2>&1; then
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
  git push -q origin main
)
check "release reports stale branch before missing retro" bash -c "
  cd '$REL_WORKTREE'
  stale_retro_out='$TMP/release-stale-before-retro.out'
  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo >\"\$stale_retro_out\" 2>&1; then
    exit 1
  fi
  grep -q 'is stale' \"\$stale_retro_out\" &&
  ! grep -q 'has no retro.md' \"\$stale_retro_out\"
"

setup_release_fixture release-sequential 2026.8.9 "Code-review verdict: APPROVE" pass fresh
check "release refuses stale branch, then computes next micro after sync" bash -c "
  set -e
  cd '$REL_WORKTREE'
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
  git push -q origin wt/demo:main
  rel_b='$TMP/release-sequential/b-wt'
  git -C '$REL_PRIMARY' branch wt/b main
  git -C '$REL_PRIMARY' worktree add -q \"\$rel_b\" wt/b
  git -C \"\$rel_b\" config user.email tester@example.com
  git -C \"\$rel_b\" config user.name Tester
  mkdir -p \"\$rel_b/work/b\"
  sed 's/# Demo/# B/' '$REL_WORKTREE/work/demo/plan.md' > \"\$rel_b/work/b/plan.md\"
  git -C \"\$rel_b\" add work/b/plan.md
  GIT_AUTHOR_DATE='2026-08-16T10:00:30Z' GIT_COMMITTER_DATE='2026-08-16T10:00:30Z' git -C \"\$rel_b\" commit -qm 'add b plan'
  stale_out='$TMP/release-stale.out'
  if PATH='$REL_FAKEBIN':\$PATH bash \"\$rel_b/scripts/release.sh\" b >\"\$stale_out\" 2>&1; then
    exit 1
  fi
  grep -q 'rebase/sync your branch onto origin/main' \"\$stale_out\"
  git -C '$REL_PRIMARY' fetch -q origin main
  git -C '$REL_PRIMARY' reset -q --hard origin/main
  mkdir -p '$REL_PRIMARY/work/demo'
  printf 'learned\n' > '$REL_PRIMARY/work/demo/retro.md'
  git -C '$REL_PRIMARY' add work/demo/retro.md
  GIT_AUTHOR_DATE='2026-08-16T10:01:30Z' GIT_COMMITTER_DATE='2026-08-16T10:01:30Z' git -C '$REL_PRIMARY' commit -qm 'Retro demo'
  git -C '$REL_PRIMARY' push -q origin main
  git -C \"\$rel_b\" fetch -q origin main
  git -C \"\$rel_b\" rebase -q origin/main
  cd \"\$rel_b\"
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh b
  [ \"\$(cat VERSION)\" = 2026.8.11 ] &&
  [ \"\$(git log -1 --format=%s)\" = 'Release v2026.8.11' ] &&
  ! git rev-parse --verify --quiet refs/tags/v2026.8.11
"

setup_release_fixture release-mid-gate 2026.8.9 "Code-review verdict: APPROVE" pass fresh
mkdir -p "$REL_WORKTREE/scripts/gate.d"
cat >"$REL_WORKTREE/scripts/gate.d/move-origin-main.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
repo='$REL_PRIMARY'
printf 'merge during gate\n' >> "\$repo/remote-change.txt"
git -C "\$repo" add remote-change.txt
GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C "\$repo" commit -qm 'merge during gate'
git -C "\$repo" push -q origin main
EOF
chmod +x "$REL_WORKTREE/scripts/gate.d/move-origin-main.sh"
(
  cd "$REL_WORKTREE" || exit 1
  git add scripts/gate.d/move-origin-main.sh
  GIT_AUTHOR_DATE="2026-08-16T10:00:30Z" GIT_COMMITTER_DATE="2026-08-16T10:00:30Z" git commit -qm "add mid-gate hook"
)
check "release catches origin/main moving during gate" bash -c "
  cd '$REL_WORKTREE'
  mid_gate_out='$TMP/release-mid-gate.out'
  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo >\"\$mid_gate_out\" 2>&1; then
    exit 1
  fi
  grep -q 'rebase/sync your branch onto origin/main' \"\$mid_gate_out\"
"

setup_release_fixture release-tag-after-merge-happy 2026.8.9 "Code-review verdict: APPROVE" pass fresh
real_git=$(command -v git)
push_log="$TMP/tag-after-merge-push.log"
tag_guard_bin="$TMP/tag-after-merge-bin"
mkdir -p "$tag_guard_bin"
cat >"$tag_guard_bin/git" <<EOF
#!/usr/bin/env bash
if [[ "\$1" == push ]]; then
  printf 'unexpected push\n' >> "$push_log"
  exit 99
fi
"$real_git" "\$@"
EOF
chmod +x "$tag_guard_bin/git"
check "tag-after-merge creates local tag on origin/main and pushes nothing" bash -c "
  cd '$REL_WORKTREE' &&
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo &&
  git push -q origin wt/demo:main &&
  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo &&
  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$(git rev-parse origin/main)\" ] &&
  [ ! -s '$push_log' ]
"

setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
  set -e
  cd '$REL_WORKTREE'
  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
  git push -q origin wt/demo:main
  git -C '$REL_PRIMARY' fetch -q origin main
  git -C '$REL_PRIMARY' reset -q --hard origin/main
  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
  git -C '$REL_PRIMARY' add after-release.txt
  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
  git -C '$REL_PRIMARY' push -q origin main
  wrong_out='$TMP/tag-after-merge-wrong.out'
  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
    exit 1
  fi
  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
  ! git rev-parse --verify --quiet refs/tags/v2026.8.10
"

# --- gate.sh runs and exits cleanly on this repo
check "gate.sh runs on this repo" bash scripts/gate.sh

echo
echo "passed: $pass, failed: $fail"
exit "$((fail > 0 ? 1 : 0))"
