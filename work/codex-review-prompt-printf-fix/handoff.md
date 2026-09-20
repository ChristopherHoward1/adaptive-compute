You are the implementer for this work unit. Read AGENTS.md in the repo root first — it is your contract.
Follow its build-discipline section while staying inside the plan footprint.

Work unit: work/codex-review-prompt-printf-fix/plan.md  (read it in full; it is your source of truth)
Branch: wt/codex-review-prompt-printf-fix (already checked out in this worktree — verify with `git branch --show-current` before changing anything)

Footprint (from the plan, repeated here as the hard boundary):
- scripts/codex-review.sh — the four severity-bullet `printf`s (lines 113–116) and the unbounded `git fetch origin` at line 98.
- scripts/worktree.sh — the unbounded `git fetch origin` at line 48.
- tests/test-scripts.sh — add rendered-prompt severity assertions; replace the source-grep test at line 857.
Do NOT touch: .claude/agents/code-reviewer.md (its severity taxonomy is correct and out of scope), config.yaml.

Key constraints:

1. THE PRIMARY BUG. scripts/codex-review.sh builds the Codex reviewer prompt with four lines of the form
   `printf '- CRITICAL: …\n'` (lines 113–116, the CRITICAL/HIGH/MEDIUM/LOW severity definitions). Under the
   script's own `#!/usr/bin/env bash` runtime, `printf` parses the leading `-` as an option and aborts the
   line (`printf: - : invalid option`, exit 2). Because the script runs `set -uo pipefail` (no `-e`), each of
   the four lines fails independently and is silently dropped — so the Codex reviewer never receives its four
   severity definitions. Fix: rewrite those four lines to `printf '%s\n' '- CRITICAL: …'` (and HIGH/MEDIUM/LOW).
   This is the idiom the file ALREADY uses for its other dash-leading lines — see lines 77, 84, 105
   (`printf '%s\n' "--- PLAN …"`). Match that idiom; do not invent a new one. After the fix,
   `grep -n "printf '- " scripts/codex-review.sh` must return nothing.

2. THE GATE TEST THAT WOULD CATCH IT. The current test at tests/test-scripts.sh:857
   (`check "codex-review prompt includes severity taxonomy" grep -F "CRITICAL" scripts/codex-review.sh`)
   greps the SOURCE FILE, so it passes whether or not the bullet ever reaches the rendered prompt — it is the
   check that gave false comfort. Replace it with an assertion against the CAPTURED, RENDERED prompt.
   The harness already has what you need: the `capture-prompt` canned-reviewer mode (search for
   `capture-prompt` around line 336) writes the fully rendered prompt to a file, and the
   `codex-excludes-work-artifacts` fixture (around lines 912–927) already invokes it and greps
   `$TMP/codex-excludes-work-artifacts/prompt.txt`. Add assertions there that the rendered prompt contains
   each of the four severity bullets. IMPORTANT: a pattern beginning with `-` also trips option parsing, so you
   MUST use `grep -Fq -- '- CRITICAL:'` (note the `--`), exactly as the harness already does at lines ~956/964
   (`grep -Fq -- '--- DIFF …'`). Assert all four: `- CRITICAL:`, `- HIGH:`, `- MEDIUM:`, `- LOW:`.
   The new test MUST fail if a bullet is reverted to the `printf '- …'` form — sanity-check that yourself by
   temporarily reverting one line, running the suite, confirming red, then restoring.

3. THE FETCH STALL (secondary). Both scripts/worktree.sh:48 and scripts/codex-review.sh:98 run the
   byte-identical one-liner `git fetch origin --quiet 2>/dev/null || true`. The `|| true` catches a non-zero
   exit but NOT a network stall, which hung the loop last unit. Bound both: run the fetch under `timeout`
   (or `gtimeout`) when one is on PATH, with a default of 30s overridable via env var `WORKTREE_FETCH_TIMEOUT`;
   when NEITHER binary exists (e.g. a bare macOS box without coreutils), fall back to the current unbounded
   best-effort call so there is no regression. A stall under the wrapper exits non-zero into the existing
   `|| true`, and the worktree is still created off the last-known origin/main. Detect the binary with
   `command -v` and keep shellcheck clean (the gate runs shellcheck over all tracked *.sh). Use the same env
   var name in both scripts so the behavior is consistent.

Acceptance criteria (from the plan — all must hold):
- Rendered prompt contains all four severity bullets (checkable via the capture-prompt fixture + `grep -Fq --`).
- `grep -n "printf '- " scripts/codex-review.sh` returns nothing.
- The new gate test fails if a bullet is reverted to `printf '- …'`.
- The source-grep test at :857 no longer stands in as the taxonomy check (the :854 code-reviewer.md test stays).
- Both fetches run under timeout/gtimeout when available, fall back cleanly otherwise; shellcheck stays clean.
- `bash scripts/gate.sh` exits 0.

When done:
1. Run scripts/gate.sh from the repo root — it must pass.
2. Commit your work on this branch with a clear message.
3. Print a final summary: what changed and why, criteria partially met (if any), out-of-scope observations.
