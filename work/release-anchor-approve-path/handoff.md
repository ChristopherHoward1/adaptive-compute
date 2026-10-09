You are the implementer for this work unit. Read AGENTS.md in the repo root first — it is your contract.
Follow its build-discipline section while staying inside the plan footprint.

Work unit: work/release-anchor-approve-path/plan.md  (read it in full; it is your source of truth)
Branch: wt/release-anchor-approve-path (already checked out in this worktree — verify with `git branch --show-current` before changing anything)

Footprint (from the plan, repeated here as the hard boundary):
- scripts/release.sh — `check_verdict` (now needs the slug or the artifact paths) and `prepend_changelog` (the optional override bullet)
- scripts/state.sh — the `review=` predicate
- tests/test-scripts.sh — new release and state fixtures and cases
- skills/3-review/SKILL.md — override close-out rules (steps 3–8 and the Rules line)

Do NOT touch: scripts/codex-review.sh, PLAN.md, CHANGELOG.md, VERSION, .claude/agents/code-reviewer.md, ARCHI.md (ARCHI is refreshed later by the review stage). Do not edit work/release-anchor-approve-path/plan.md.

Key constraints:
- Sentinel matching. The two verdict lines are exact whole-line matches (`grep -x`, as today). A `Codex override:` line counts only when it starts at column 0 (`^Codex override:`); indented lines never count. `state.sh` and `release.sh` must apply identical plan-text rules:
  - Both `Codex-review verdict: APPROVE` and `Codex-review verdict: OVERRIDDEN` present → refused / `review: pending`.
  - Exactly one column-0 `Codex override:` line is allowed; two or more → refused.
  - The reason is whitespace-trimmed (leading and trailing) and must be non-empty after trimming.
  - A column-0 `Codex override:` line on the standard path (APPROVE present, OVERRIDDEN absent) is ignored: no refusal, no changelog bullet.
- Override-path artifact checks live only in `release.sh` and are relative to the release checkout:
  - `work/<slug>/codex-review.md`: the last line matching `^[[:space:]]*Codex verdict:`, trimmed, must be `REQUEST CHANGES`. Parse it exactly as `scripts/codex-review.sh` lines 154–162 do.
  - `work/<slug>/deferrals.md` must exist and be non-empty.
- When neither Codex sentinel is present, the refusal message must still contain the literal `Codex-review verdict: APPROVE` (the existing test at tests/test-scripts.sh ~1747 greps it). Refusal messages must name `Codex override`, `codex-review.md` or `deferrals.md` respectively, as the acceptance criteria specify.
- The standard-path changelog output must be byte-identical to today's. The override bullet `- Codex override: <trimmed reason>` goes directly after the `- Confirm-delta:` bullet and before the section's single trailing blank line.
- The verdict check stays the first check in `release()`, before any write.
- Test fixtures:
  - The override happy path must write `codex-review.md` and `deferrals.md` AND have them committed on `wt/demo` (mirroring `sync-artifacts`); otherwise `check_clean_worktree` dies with "has untracked files". A simple option: write them in the primary fixture repo before the `source` commit.
  - The override and standard-path changelog cases seed CHANGELOG.md with a prior `## [x] - date` section, so the section boundary is exercised.
- Additional test-strengthening asks from the final plan review (please include):
  1. The `codex-review.md` "last verdict is APPROVE" refusal fixture has `Codex verdict: REQUEST CHANGES` on an earlier line and `Codex verdict: APPROVE` last. The happy-path fixture's last verdict line is indented (`  Codex verdict: REQUEST CHANGES`).
  2. The happy-path `Codex override:` reason carries trailing whitespace (e.g. a trailing space and tab), and the exact-line changelog assertion still holds.
  3. Indented case (b) (one column-0 override line plus one indented) also asserts `CHANGELOG.md` has exactly one `- Codex override:` line.
- Skill edits (skills/3-review/SKILL.md) must satisfy the two diff-inspection criteria in the plan:
  - five preconditions;
  - the Orchestrator never records OVERRIDDEN on its own judgement;
  - the step-3 cross-reference and step-4 carve-out;
  - step 5 keeps the literal `counter reaches 3` (a test greps it);
  - step 6 covers the override form and the single plan commit;
  - step 7 runs after either close-out;
  - step 8 reports either form;
  - the Rules line lists APPROVE|REQUEST CHANGES|OVERRIDDEN.
- Match the surrounding Bash style (`set -euo pipefail`, `die`, `[[ ]]`); the code must be shellcheck clean.

When done:
1. Run scripts/gate.sh from the repo root — it must pass.
2. Commit your work on this branch with a clear message.
3. Print a final summary: what changed and why, criteria partially met (if any), out-of-scope observations.
