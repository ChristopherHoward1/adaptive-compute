# release-tag-merge-commit — tag the release commit by SHA, not origin/main's tip

**Slug:** release-tag-merge-commit · **Date:** 2026-09-19 · **Status:** implemented

## Goal

`scripts/release.sh tag-after-merge <slug>` refuses to tag whenever `origin/main`'s
**tip** is not literally the `Release v$version` commit. It (a) checks the tip
*subject* equals `Release v$version` (`release.sh:279-282`) and (b) tags
`origin/main` itself (`release.sh:287`). Both assume a squash/rebase/ff merge where
the tip *is* the release commit. When the release PR merges as a **merge commit**
(the harness's default — PR #3 for v2026.9.0), or any non-version-bumping commit
lands on top (e.g. that unit's retro PR), the tip is no longer the release commit,
so tagging refuses even though the release is genuinely on `main` and unsuperseded.
v2026.9.0 had to be tagged at release commit `74ddb64` by hand.

Done = `tag-after-merge` locates the commit that set `VERSION` to `$version` on
`origin/main` and tags **that commit by SHA**, succeeding for merge-commit / ff /
rebase / squash merges and when later non-release commits sit on top; while still
refusing when the release is not the current version on `origin/main`. It must not
weaken the guarantee that the tagged release is actually present on `origin/main`.

## Approach

Rewrite `tag_after_merge` in `scripts/release.sh` (that function), and update the
two lines elsewhere in the file that describe the old contract (see Footprint).

1. Keep the existing preamble: resolve the release worktree, read the branch's
   `VERSION` ($version), `git fetch origin main`, verify `origin/main` exists.
2. **Currency guard (kept):** require `git show origin/main:VERSION` == $version.
   If a later release bumped VERSION past this one, or the release was never merged
   (VERSION on main still the old value), refuse — we tag only the release that is
   *current* on `main`. This is a deliberate scope decision (see Review): the loop
   tags immediately after each merge, so this holds in normal flow; delayed
   back-tagging after a newer release has shipped stays a manual step, out of scope
   here.
3. **Locate the release commit by the VERSION transition** (merge-strategy-agnostic;
   `VERSION` is written only by `release.sh:245`, so a VERSION change *is* a release):
   walk `git log origin/main --format=%H -- VERSION` (path-simplification yields the
   commit that changed VERSION, not the enclosing merge commit) newest-first, and
   take the first commit `C` where `git show C:VERSION` == $version and its parent's
   VERSION differs (the transition to $version). Because `git log origin/main` only
   walks commits reachable from the tip, `C` is provably on `main`. This locates the
   right commit for merge-commit, ff, rebase, **and** squash merges (a squash sets
   VERSION in one commit whose subject is the PR title — subject-matching would miss
   it, the VERSION transition does not). If no such commit is found (should be
   unreachable given the step-2 guard), refuse with a clear message.
4. Keep the "tag already exists" guard (`release.sh:284-285`).
5. `git tag "v$version" <C>` (was `git tag ... origin/main`); print the tagged SHA
   and subject so the operator sees which commit was tagged.

No push (still a separate confirmed step). No change to `release()`, the gate, or
any other subcommand.

Alternatives considered:
- *Match the commit by subject `Release v$version`*: rejected — brittle to arbitrary
  subjects and, more importantly, cannot see a squash-merged release (subject becomes
  the PR title). The VERSION-transition locator is strictly more robust and covers
  squash for free.
- *Standardize on squash-merge for release PRs* (retro option a): unnecessary once the
  locator is VERSION-based — all merge strategies work as-is.
- *Tag `origin/main`'s tip when VERSION matches*: rejected — after a merge commit or a
  later non-release commit the tip is the wrong commit; the tag would not point at the
  release.

## Footprint

Files to modify:
- `scripts/release.sh` —
  - rewrite the `tag_after_merge` function (~lines 260-289);
  - update the `usage()` heredoc line (~line 18: "tag-after-merge verifies origin/main
    is the release commit …") to describe the new SHA-locating behavior;
  - reword the success message (~line 288, `created local tag v%s on origin/main`)
    since the tag target is the release commit, not the tip.
- `tests/test-scripts.sh` — update the two existing `tag-after-merge` tests and add
  regression tests (see Acceptance criteria).

Files NOT to touch:
- `release()` and every other subcommand in `scripts/release.sh` — the bug is
  isolated to `tag_after_merge` and its two doc/message lines.
- `scripts/gate.sh`, `config.yaml`, `.claude/`, `PLAN.md` (PLAN update happens at
  release/retro, not here). `skills/4-release/SKILL.md` (confirmed: it only branches
  on `tag-after-merge`'s exit code, no message dependency).

## Acceptance criteria

- [ ] `bash scripts/gate.sh` is green (includes `shellcheck` over `release.sh` and
      the full `tests/test-scripts.sh` shell smoke suite).
- [ ] **Merge-commit success (new regression test — the motivating bug):** fixture
      where the release is on `origin/main` and a **merge commit** (or any non-release
      commit, VERSION unchanged) sits on top → `tag-after-merge` exits 0, creates
      `v$version`, `git rev-parse refs/tags/v$version` equals the SHA of the commit
      that set VERSION to $version (**not** `origin/main`'s tip), and pushes nothing.
- [ ] **Squash-merge success (new regression test):** fixture where the release lands
      as a single commit whose subject is *not* `Release v$version` (a PR title) but
      which sets VERSION to $version → `tag-after-merge` exits 0 and tags that commit.
- [ ] **ff/happy path still passes:** the existing "tag-after-merge creates local
      tag … and pushes nothing" test (tip *is* the release commit) still passes
      unchanged; the tag equals both the release commit and `origin/main`.
- [ ] **Not-current refused (rewritten from the line-1907 test):** when `origin/main`
      is *not* at VERSION $version — because a later commit bumped VERSION past it —
      `tag-after-merge` exits non-zero, creates no tag, and prints a message naming
      the mismatch. (The old test left VERSION unchanged; that scenario now correctly
      *succeeds* per finding 1, so the fixture must bump VERSION with a real commit
      before the push.)
- [ ] `tag-after-merge` still never pushes (push-guard assertion, as in the current
      happy-path test).
- [ ] Re-tagging guard intact: a second `tag-after-merge` when `v$version` already
      exists still refuses.

## Release

Release note: Fix `release.sh tag-after-merge` to tag the commit that set VERSION (by SHA) so merge-commit, squash, and non-ff release-PR merges tag correctly instead of refusing.

## Verification

- `bash scripts/gate.sh` (authoritative; runs shellcheck + the shell smoke suite).
- Manual replay of the original failure: a fixture whose `origin/main` tip is a
  merge commit over the release commit now tags the release commit and exits 0.

## Review

Reviewer (fresh read-only `Plan` subagent standing in for `plan-reviewer` — writer ≠
reviewer preserved): verdict **REVISE**, all four codebase claims independently
verified. All findings accepted and folded in:

1. **Locate by VERSION transition, not subject string** (strongest) — adopted as the
   primary approach (step 3). Subject-matching dropped; this also makes squash merges
   work, so the earlier "squash unsupported" alternative was removed and a squash
   success criterion added.
2. **Multiple-match contradiction** — dissolved: the VERSION transition to a given
   version is unique on the walked history; step 3 takes the first (newest) transition
   and stops. No ambiguity clause.
3. **Footprint omitted `usage()` line 18 and the success message line 288** — both now
   listed explicitly in Footprint. Confirmed `skills/4-release/SKILL.md` depends only
   on exit code, and no test greps the success string, so no wider ripple.
4. **"squashed-away refused" criterion collided with finding 1** — rewritten: the
   refusal case is now unambiguously "VERSION on `origin/main` is not $version"
   (superseded or not-merged), and squash is a success case.

Design question raised by the reviewer — the currency guard (`origin/main:VERSION ==
version`) means a release missed at merge time can't be back-tagged by the script once
a newer release ships. **Decision (Orchestrator): keep the strict guard.** It exactly
fixes the motivating incident (current release, merge-commit tip) and matches the
loop's tag-immediately-after-merge cadence; delayed back-tagging is a rare off-nominal
recovery that stays manual rather than widening this unit's scope or weakening the
"tag only the current release" safety. Flagging for the Owner in case broader
back-tagging is wanted — that would be a separate unit.

Plan verdict: APPROVE (post-revision)

### /3-review — round 1 (both reviewers cold, read-only)

Gate: PASS (188/188, run independently by the code-reviewer; no segfault in the repo env — the implementer's reported segfault was the known pytest sandbox artifact). All seven acceptance criteria met; footprint respected (only `tag_after_merge`, the `usage()` doc lines, the success message, and `tests/test-scripts.sh`).

Code-review verdict: APPROVE
Codex-review verdict: APPROVE

LOW findings (recorded for awareness; none blocking — all fail *safe*, i.e. a false refusal in an off-nominal history, never a wrong tag; and VERSION is written only by `release.sh:245`, so those histories are not produced by the tool):
- L1 — the locator dies if a candidate commit *deleted* VERSION; unreachable because the newest transition-to-$version commit is found and the loop breaks first.
- L2 — the transition check uses only the first parent (`${parent%% *}`); an evil/octopus merge that edited VERSION in the merge itself and whose first parent already held $version could be skipped → safe refusal, never a mistag.
- L3 — the parent-transition guard is effectively redundant given "take newest matching candidate and break"; its only off-nominal effect is to turn a would-be mistag into a safe refusal (desirable).
