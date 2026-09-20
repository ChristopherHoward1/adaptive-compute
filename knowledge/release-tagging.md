# How `release.sh tag-after-merge` locates the release commit

Loaded only when touching release tagging (e.g. the deferred back-tagging question,
or any change to `tag_after_merge`). Everything here is about
`scripts/release.sh:tag_after_merge`, added by the `release-tag-merge-commit` unit
(v2026.9.1). See `work/release-tag-merge-commit/plan.md` for the full rationale.

## The problem it solves

The tag must land on the `Release vX` commit, but that commit is usually **not**
`origin/main`'s tip: the harness merges release PRs as **merge commits**, and the
unit's own retro PR then lands on top. The original code checked the tip *subject*
and tagged the tip, so it refused (or would have mistagged) on every merge-commit
release. v2026.9.0 had to be tagged by hand.

## How it locates the commit (VERSION transition, not subject)

`VERSION` is written **only** by `release.sh` (the release commit at
`release.sh:245`), so *a change to `VERSION` is, by definition, a release*. The
locator exploits that instead of matching commit subjects:

- Walk `git log origin/main --format=%H -- VERSION`, newest first.
- Take the first commit `C` where `C:VERSION == $version` **and** its first parent's
  VERSION differs — the transition *to* this version.
- Tag `C` by SHA.

Why this is robust across merge strategies:

- **Path simplification.** `git log <ref> -- VERSION` prunes commits that are
  TREESAME to a parent along `VERSION`. A `--no-ff` merge commit's tree matches its
  release-side parent's `VERSION`, so the merge is pruned and the walk surfaces the
  real `Release vX` commit underneath — not the merge. (Verified by the regression
  test asserting the tag `!=` `origin/main`.)
- **Squash** produces one commit that sets `VERSION` with a PR-title subject;
  subject-matching would miss it, the transition does not.
- **ff / rebase**: the release commit is linear; trivially found.

Because `git log origin/main …` only walks commits reachable from the tip, a match
is provably on `main`.

## The two guards (both retained)

- **Currency guard:** `git show origin/main:VERSION` must equal the branch's
  `$version`. This is a **deliberate** limitation: it tags only the release that is
  *current* on `main`. Once a newer release bumps `VERSION`, this one can no longer
  be tagged by the script — a missed tag then needs a manual `git tag`. Accepted
  because the loop tags immediately after each merge (`/4-release` step 4). If
  automatic back-tagging is ever wanted, that is a separate unit and this guard is
  what must change.
- **Re-tag guard:** refuses if `refs/tags/v$version` already exists.

## Known-safe edge behaviour

The first-parent-only transition check and the "die if a candidate can't be read"
path fail **safe** — a false refusal on an off-nominal history (octopus/evil merge
that edits `VERSION` in the merge itself, or a `VERSION`-deleting commit), never a
wrong tag. Such histories are not produced by `release.sh` itself. Recorded as LOW
in `work/release-tag-merge-commit/plan.md`.
