You are the implementer for this work unit. Read AGENTS.md in the repo root first — it is your contract.
Follow its build-discipline section while staying inside the plan footprint.

Work unit: work/release-tag-merge-commit/plan.md  (read it in full; it is your source of truth)
Branch: wt/release-tag-merge-commit (already checked out in this worktree — verify with `git branch --show-current` before changing anything)

Footprint (from the plan, repeated here as the hard boundary):
- `scripts/release.sh` — rewrite the `tag_after_merge` function (~lines 260-289) AND update two lines elsewhere in the same file that describe the OLD contract:
  - the `usage()` heredoc line (~line 18): "After the PR merges, tag-after-merge verifies origin/main is the release commit …" — reword to describe the new behavior (it locates the release commit by SHA and tags it).
  - the success message (~line 288): `created local tag v%s on origin/main` — reword since the tag target is now the release commit, not origin/main's tip.
- `tests/test-scripts.sh` — update the two existing `tag-after-merge` tests (~lines 1883-1924) and add regression tests (see Acceptance criteria in the plan). Use the existing `setup_release_fixture` helper and the `check` / `check_exit` / `check_fails` helpers already in the file; mirror the style of the current tag-after-merge tests exactly.

Do NOT touch: `release()` or any other subcommand in `scripts/release.sh` beyond the three items above; `scripts/gate.sh`, `config.yaml`, `.claude/`, `PLAN.md`, `skills/`. (Confirmed: `skills/4-release/SKILL.md` depends only on `tag-after-merge`'s exit code, and no test greps the success message, so those two message rewordings are safe.)

Key constraints:
- **The core change (plan Approach step 3):** `tag_after_merge` must locate the release commit by the VERSION *transition*, NOT by matching the commit subject. `VERSION` is written only by `release.sh` (line 245), so a VERSION change is a release. Walk `git log origin/main --format=%H -- VERSION` newest-first and take the first commit `C` where `git show C:VERSION` == the branch's `$version` and its parent's VERSION differs (the transition to `$version`). Path-simplification on `-- VERSION` yields the actual release commit, not the enclosing merge commit. Because `git log origin/main` only walks commits reachable from the tip, `C` is provably on `main`. Tag `C` by SHA: `git tag "v$version" "$C"`. This must work for merge-commit, fast-forward, rebase, AND squash merges.
- **Keep the currency guard:** still require `git show origin/main:VERSION` == the branch's `$version`. If a later release bumped VERSION past this one (or the release was never merged), refuse with a clear message. This is deliberate — tag only the release that is current on `main`.
- **Keep the "tag already exists" guard** (current lines 284-285): refuse if `refs/tags/v$version` already exists.
- **Never push and never tag anything but the located release commit.** The tag-push remains a separate step outside this function.
- Determinism / no behavior change to the ff/happy path: when `origin/main`'s tip IS the release commit, the located `C` equals the tip, so the existing happy-path test (tag == origin/main) still passes unchanged.
- All shell must pass `shellcheck` (enforced by the gate). Match the surrounding script style (`set -euo pipefail`, `die` for errors, local vars).

Tests you must end up with (see the plan's Acceptance criteria for the authoritative list):
1. **Merge-commit success (new):** release on origin/main with a merge commit (or any non-release commit, VERSION unchanged) on top → `tag-after-merge` exits 0, `refs/tags/v$version` == the release-commit SHA (NOT origin/main's tip), pushes nothing.
2. **Squash-merge success (new):** release lands as a single commit whose subject is NOT `Release v$version` (a PR title) but which sets VERSION to `$version` → exits 0, tags that commit.
3. **ff/happy path (existing ~line 1897):** unchanged, still passes.
4. **Not-current refused (rewrite the existing ~line 1907 test):** the old test left VERSION unchanged and expected refusal — under the new logic that scenario SUCCEEDS, so the fixture must add a real commit that bumps `origin/main`'s VERSION *past* `$version` before asserting refusal + no tag created.
5. **Re-tag guard (existing):** second `tag-after-merge` when the tag exists still refuses.

When done:
1. Run scripts/gate.sh from the repo root — it must pass.
2. Commit your work on this branch with a clear message.
3. Print a final summary: what changed and why, criteria partially met (if any), out-of-scope observations.
