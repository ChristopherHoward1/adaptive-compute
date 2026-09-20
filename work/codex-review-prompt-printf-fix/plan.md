# Fix dropped severity taxonomy in the Codex review prompt

**Slug:** codex-review-prompt-printf-fix · **Date:** 2026-09-20 · **Status:** implemented

## Goal

`scripts/codex-review.sh` builds the Codex reviewer's prompt with four
`printf '- CRITICAL: …\n'` lines (and HIGH/MEDIUM/LOW siblings). Under the
script's own `#!/usr/bin/env bash` runtime, `printf` parses the leading `-` of
each format string as an option and aborts the line (`printf: - : invalid
option`, exit 2), so **all four severity-definition bullets are silently dropped
from the rendered prompt**. Under `set -uo pipefail` (no `-e`) each dropped line
is independent: the `## Severity` header, the "Every finding gets exactly one
severity:" line, and the `## Calibration` section (which still names
CRITICAL/HIGH/LOW and the verdict rules) all survive — it is the four severity
*definitions* that never reach the Codex reviewer, in every review round of every
unit to date. The gate test
`codex-review prompt includes severity taxonomy` greps the *source file* for
`CRITICAL` (matched by the literal on line 113), so it passes whether or not the
bullet ever reaches the prompt — false comfort.

Done looks like: the four severity bullets appear verbatim in the rendered
prompt; a gate test asserts that against the *captured* prompt (not the source),
so a future re-drop fails the gate; and the same unbounded `git fetch origin`
one-liner that can hang the loop is bounded.

Reproduction (confirmed 2026-09-20): `bash -c "printf '- CRITICAL: x\n'"` →
`printf: - : invalid option`, exit 2. Same under `sh -c` and `/usr/bin/printf`.

## Approach

1. **The printf fix.** Change the four bullet lines (codex-review.sh:113–116)
   from `printf '- CRITICAL: …\n'` to `printf '%s\n' '- CRITICAL: …'`. This is
   the form the script already uses for its other dash-leading lines (77, 84,
   105: `printf '%s\n' "--- PLAN …"`), so it is the local idiom, not a new one.
   `printf -- '- …\n'` also works but `%s\n` is what the file already does.

2. **A gate test that would actually catch it.** The existing `capture-prompt`
   canned-reviewer mode (tests/test-scripts.sh:336) already writes the fully
   rendered prompt to `prompt.txt`, and the `codex-excludes-work-artifacts`
   fixture exercises it. Add checks asserting `prompt.txt` contains each of the
   four dash-led bullets (`- CRITICAL:`, `- HIGH:`, `- MEDIUM:`, `- LOW:`).
   Replace the source-grep test at line 857 (`grep -F "CRITICAL"
   scripts/codex-review.sh`) with the rendered-prompt assertion — the source
   grep is the check that gave false comfort, so it should not remain.

3. **Bound the loop's `git fetch origin` (secondary).** `worktree.sh:48` runs
   `git fetch origin --quiet 2>/dev/null || true` with no timeout; the `|| true`
   catches a non-zero exit, not a network *stall*, which hung `/5-retro` last
   unit until the process was killed. `codex-review.sh:98` has the identical
   one-liner and the same hazard (in scope: same fix, same loop hot-path — flag
   for review if this is unwanted creep). Wrap both: run under `timeout`
   (or `gtimeout`) when one is on PATH, with a default of 30s overridable via
   `WORKTREE_FETCH_TIMEOUT`; when neither exists, fall back to the current
   best-effort unbounded call (no regression on a bare macOS box). A stall then
   ends in a bounded non-zero exit that `|| true` already absorbs, and the
   worktree is still created off the last-known `origin/main`.

## Footprint

Files to modify:
- `scripts/codex-review.sh` — the four bullet `printf`s (113–116); the bounded fetch (98).
- `scripts/worktree.sh` — the bounded fetch (48).
- `tests/test-scripts.sh` — rendered-prompt severity assertions; replace the source-grep test.

Files NOT to touch:
- `.claude/agents/code-reviewer.md` — it carries the canonical severity taxonomy for the *Claude* reviewer and is fine; this unit is only about the Codex prompt.
- `config.yaml` — reviewer runtime/command unchanged.

## Acceptance criteria

- [ ] The rendered prompt contains all four severity-definition bullets. Checkable: run `scripts/codex-review.sh` against the `capture-prompt` fixture and `grep -Fq -- '- CRITICAL:' prompt.txt` (also `-- '- HIGH:'`, `-- '- MEDIUM:'`, `-- '- LOW:'`) succeeds. (Note the `--`: a bare `grep -F '- CRITICAL:'` hits the very option-parsing bug being fixed; the harness already uses `grep -Fq --` at lines 956/964.)
- [ ] `grep -n "printf '- " scripts/codex-review.sh` returns nothing (no dash-leading format strings remain).
- [ ] A gate test asserts the four severity bullets appear in the **captured** prompt, and it *fails* if a bullet is reverted to `printf '- …'` (verify by temporarily reverting one line and confirming the gate goes red).
- [ ] The old source-grep test `grep -F "CRITICAL" scripts/codex-review.sh` (test-scripts.sh:857) no longer stands in as the taxonomy check. (Leave the code-reviewer.md test at :854 alone — a different, legitimate check.)
- [ ] `worktree.sh:48` and `codex-review.sh:98` fetches run under `timeout`/`gtimeout` when one is on PATH, and fall back to the current unbounded best-effort call otherwise (no regression on a macOS box without coreutils). Checkable by inspection + shellcheck stays clean.
- [ ] `bash scripts/gate.sh` exits 0 (shellcheck over both scripts + full shell smoke suite + Python checks).

## Release

Release note: Fixed the Codex review prompt silently dropping its CRITICAL/HIGH/MEDIUM/LOW severity taxonomy (leading-dash `printf`), added a rendered-prompt gate test that catches a re-drop, and bounded the loop's `git fetch origin` against network stalls.

## Verification

- `bash scripts/gate.sh`
- Targeted: `bash tests/test-scripts.sh` and confirm the new severity-in-prompt checks pass; then revert one bullet to the `printf '- …'` form and confirm the suite goes red (then restore).

## Review

Fresh `plan-reviewer` stand-in (cold read-only `Plan` subagent, per the
2026-09-19 PLAN decision on agent spawnability), 2026-09-20. Verdict **APPROVE**
with three corrections, all applied:

1. **Fetch line citation was wrong** — the `codex-review.sh` fetch is at line
   **98**, not 103 (103 is `base=main`). Corrected in Approach + Footprint +
   acceptance criteria. (worktree.sh:48 was correct.)
2. **Acceptance-criterion grep would hit the same bug** — `grep -F '- CRITICAL:'`
   parses the leading dash as an option. Rewrote the criterion to
   `grep -Fq -- '- CRITICAL:'` (the harness's existing idiom at :956/:964), so it
   isn't copied literally into the test.
3. **Goal wording tightened** — the `## Calibration` section and verdict rules
   survive; only the four severity *definitions* are dropped. Reworded so the
   claim is precise.

Reviewer confirmed sound: the `printf '%s\n'` fix matches the file idiom
(:77/:84/:105); the `capture-prompt` fixture (:336) + `codex-excludes-work-artifacts`
prompt.txt (:912–927) make the rendered-prompt test trivial and genuinely
discriminating; the source-grep at :857 is the right test to retire and :854 is
correctly left alone. On the two scope questions: bounding **both** identical
fetch one-liners is honest scope, not creep; and the `timeout`/`gtimeout`-else-
fallback shape is portable — with the accepted limitation that a bare
macOS-without-coreutils box stays unbounded (criterion reworded to say so).

No disagreements to route to the Owner.

Plan verdict: APPROVE

### /3-review — round 1 (2026-09-20)

Both reviewers APPROVE, zero findings; gate green (both ran it independently, 188/188).

- **`code-reviewer`** (fresh cold `Plan` stand-in): APPROVE. Verified all six acceptance
  criteria met — rendered prompt carries all four bullets; `grep -n "printf '- "` empty;
  the new `grep -Fq --` test goes red on a re-drop (confirmed the bug reproduces and the
  assertion is itself immune to the option-parse trap); source-grep at :857 retired, :854
  left intact; bounded fetch with portable `timeout`/`gtimeout`-else-fallback, shellcheck
  clean. Footprint exactly the three declared files. The duplicated `fetch_origin_best_effort`
  is deliberate honest scope, not a defect (no shared-lib convention in `scripts/`).
- **`codex-review.sh`** (cold read-only Codex, exit 0): APPROVE, no substantive findings.
  Confirmed the `%s\n` idiom, the rendered-prompt test replacing the false source-grep, and
  both fetch call sites bounded with fallback preserved.

Code-review verdict: APPROVE
Codex-review verdict: APPROVE
