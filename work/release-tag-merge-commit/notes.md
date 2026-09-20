Dispatching implementer in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
  codex exec --sandbox workspace-write - < /Users/cboyfly/Documents/repos/adaptive-compute/work/release-tag-merge-commit/handoff.md
OpenAI Codex v0.139.0
--------
workdir: /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
model: gpt-5.5
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR]
reasoning effort: none
reasoning summaries: none
session id: 01a0bccd-254d-79e1-b968-99576a66bcb0
--------
user
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

codex
I’ll start by reading the contract and plan, then I’ll verify the branch before touching anything. After that I’ll inspect only the two files in the stated footprint and trace the existing tests around `tag-after-merge`.
exec
/bin/zsh -lc "sed -n '1,220p' AGENTS.md" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
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
/bin/zsh -lc 'pwd && git branch --show-current' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
 succeeded in 0ms:
/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
wt/release-tag-merge-commit

exec
/bin/zsh -lc "sed -n '1,260p' work/release-tag-merge-commit/plan.md" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
 succeeded in 0ms:
# release-tag-merge-commit — tag the release commit by SHA, not origin/main's tip

**Slug:** release-tag-merge-commit · **Date:** 2026-09-19 · **Status:** draft

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

codex
Branch is correct and the plan is explicit: this is a real bug fix, tightly bounded to `scripts/release.sh` and the existing script tests. I’m going to read the current function and nearby tests now so the edit follows the existing shell style instead of inventing a parallel universe.
exec
/bin/zsh -lc "nl -ba scripts/release.sh | sed -n '1,330p'" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
 succeeded in 0ms:
     1	#!/usr/bin/env bash
     2	# Release driver. Exit 0 = release staged locally. Non-zero = stop and report.
     3	set -euo pipefail
     4	
     5	cd "$(git rev-parse --show-toplevel)"
     6	
     7	usage() {
     8	  cat <<'EOF'
     9	Usage:
    10	  scripts/release.sh <slug> [--confirm-delta <text>]
    11	  scripts/release.sh tag-after-merge <slug>
    12	  scripts/release.sh check-version <new-version> [current-version]
    13	  scripts/release.sh next-version [current-version]
    14	
    15	The release path never pushes, never tags, and never touches main. It commits
    16	the version bump on the release branch for PR review.
    17	
    18	After the PR merges, tag-after-merge verifies origin/main is the release commit
    19	and creates the local version tag. The tag push is a separate confirmed step.
    20	EOF
    21	}
    22	
    23	die() {
    24	  echo "release: $*" >&2
    25	  exit 1
    26	}
    27	
    28	valid_version() {
    29	  [[ "$1" =~ ^([1-9][0-9]{3})\.([1-9]|1[0-2])\.(0|[1-9][0-9]*)$ ]]
    30	}
    31	
    32	version_gt() {
    33	  local new="$1"
    34	  local old="$2"
    35	  local new_year new_month new_micro old_year old_month old_micro
    36	
    37	  valid_version "$new" || die "invalid new version '$new' (expected YYYY.M.MICRO)"
    38	  valid_version "$old" || die "invalid current version '$old' (expected YYYY.M.MICRO)"
    39	
    40	  IFS=. read -r new_year new_month new_micro <<<"$new"
    41	  IFS=. read -r old_year old_month old_micro <<<"$old"
    42	
    43	  if (( new_year > old_year )); then return 0; fi
    44	  if (( new_year < old_year )); then return 1; fi
    45	  if (( new_month > old_month )); then return 0; fi
    46	  if (( new_month < old_month )); then return 1; fi
    47	  (( new_micro > old_micro ))
    48	}
    49	
    50	next_version() {
    51	  local current="$1"
    52	  local today year month current_year current_month current_micro
    53	
    54	  valid_version "$current" || die "invalid current version '$current' (expected YYYY.M.MICRO)"
    55	  today=$(date +%Y.%-m)
    56	  IFS=. read -r year month <<<"$today"
    57	  IFS=. read -r current_year current_month current_micro <<<"$current"
    58	
    59	  if (( year == current_year && month == current_month )); then
    60	    printf '%s.%s.%s\n' "$current_year" "$current_month" "$((current_micro + 1))"
    61	  else
    62	    printf '%s.%s.0\n' "$year" "$month"
    63	  fi
    64	}
    65	
    66	extract_release_note() {
    67	  local plan_path="$1"
    68	  local note
    69	
    70	  # Release notes are intentionally one line so changelog assembly stays deterministic.
    71	  note=$(
    72	    sed -n -E 's/^\**Release note:\**[[:space:]]*//p' "$plan_path" | head -n 1
    73	  )
    74	  [[ -n "$note" ]] || die "$plan_path is missing a Release note: line"
    75	  printf '%s\n' "$note"
    76	}
    77	
    78	prepend_changelog() {
    79	  local version="$1"
    80	  local release_note="$2"
    81	  local confirm_delta="$3"
    82	  local date_stamp
    83	  local tmp
    84	
    85	  date_stamp=$(date +%F)
    86	  tmp=$(mktemp)
    87	
    88	  {
    89	    if [[ -f CHANGELOG.md ]]; then
    90	      sed -n '1,/^## /{ /^## /q; p; }' CHANGELOG.md
    91	    else
    92	      printf '# Changelog\n\n'
    93	      printf 'All notable changes to this project are documented in this file.\n\n'
    94	    fi
    95	    printf '## [%s] - %s\n\n' "$version" "$date_stamp"
    96	    printf '%s\n' "- $release_note"
    97	    printf '%s\n\n' "- Confirm-delta: $confirm_delta"
    98	    if [[ -f CHANGELOG.md ]]; then
    99	      sed -n '/^## /,$p' CHANGELOG.md
   100	    fi
   101	  } >"$tmp"
   102	
   103	  mv "$tmp" CHANGELOG.md
   104	}
   105	
   106	check_verdict() {
   107	  local plan_path="$1"
   108	  grep -qx 'Code-review verdict: APPROVE' "$plan_path" \
   109	    || die "$plan_path must contain exact line: Code-review verdict: APPROVE"
   110	  grep -qx 'Codex-review verdict: APPROVE' "$plan_path" \
   111	    || die "$plan_path must contain exact line: Codex-review verdict: APPROVE"
   112	}
   113	
   114	check_gate() {
   115	  bash scripts/gate.sh || die "scripts/gate.sh failed"
   116	}
   117	
   118	check_archi_fresh() {
   119	  scripts/archi-fresh.sh || die "ARCHI.md is stale; refresh it on the branch"
   120	}
   121	
   122	check_version_exceeds() {
   123	  local new_version="$1"
   124	  local current_version="$2"
   125	
   126	  version_gt "$new_version" "$current_version" \
   127	    || die "new version $new_version must exceed VERSION $current_version"
   128	}
   129	
   130	worktree_for_branch() {
   131	  local branch="$1"
   132	
   133	  git worktree list --porcelain | awk -v branch="refs/heads/$branch" '
   134	    $1 == "worktree" {
   135	      path = substr($0, 10)
   136	      next
   137	    }
   138	    $1 == "branch" && $2 == branch {
   139	      print path
   140	      found = 1
   141	      exit
   142	    }
   143	    END {
   144	      if (!found) exit 1
   145	    }
   146	  '
   147	}
   148	
   149	check_clean_worktree() {
   150	  local checkout="$1"
   151	  local label="$2"
   152	
   153	  git -C "$checkout" diff --quiet || die "$label has unstaged changes"
   154	  git -C "$checkout" diff --cached --quiet || die "$label has staged changes"
   155	  [[ -z "$(git -C "$checkout" ls-files --others --exclude-standard)" ]] \
   156	    || die "$label has untracked files"
   157	}
   158	
   159	check_origin_main_ancestor() {
   160	  local release_branch="$1"
   161	
   162	  git fetch origin main
   163	  git rev-parse --verify --quiet origin/main >/dev/null \
   164	    || die "missing origin/main after fetch"
   165	  git merge-base --is-ancestor origin/main "$release_branch" \
   166	    || die "$release_branch is stale; rebase/sync your branch onto origin/main"
   167	}
   168	
   169	check_previous_retro() {
   170	  local marker="work/.last-released"
   171	  local previous_slug
   172	  local previous_retro
   173	
   174	  if git show origin/main:"$marker" >/dev/null 2>&1; then
   175	    [[ ! -L "$marker" ]] || die "previous release marker is a symlink"
   176	    [[ -f "$marker" ]] || die "previous release marker deleted; restore $marker from origin/main"
   177	    git show origin/main:"$marker" | cmp -s - "$marker" \
   178	      || die "previous release marker differs from origin/main; if this branch already carries its release commit, merge its PR instead of re-running release"
   179	  else
   180	    [[ ! -L "$marker" ]] || die "previous release marker is a symlink"
   181	    if [[ -f "$marker" ]]; then
   182	      [[ -s "$marker" ]] || die "previous release marker malformed"
   183	      [[ "$(awk 'END { print NR }' "$marker")" -eq 1 ]] \
   184	        || die "previous release marker malformed"
   185	    fi
   186	  fi
   187	
   188	  [[ -f "$marker" ]] || return 0
   189	
   190	  previous_slug=$(<"$marker")
   191	  previous_retro="work/$previous_slug/retro.md"
   192	  [[ -s "$previous_retro" ]] \
   193	    || die "$previous_slug has no retro.md; run /5-retro for $previous_slug, or sync onto origin/main"
   194	}
   195	
   196	rollback_release() {
   197	  local status=$?
   198	  local pre_release_head="$1"
   199	
   200	  trap - ERR
   201	  set +e
   202	  git reset --hard "$pre_release_head" >/dev/null 2>&1
   203	  git clean -f work/.last-released >/dev/null 2>&1
   204	  echo "release: irreversible step failed; release commit was rolled back" >&2
   205	  exit "$status"
   206	}
   207	
   208	release() {
   209	  local slug="$1"
   210	  local confirm_delta="$2"
   211	  local plan_path="work/$slug/plan.md"
   212	  local release_branch="wt/$slug"
   213	  local release_checkout
   214	  local current_version
   215	  local new_version
   216	  local release_note
   217	  local pre_release_head
   218	
   219	  worktree_for_branch main >/dev/null \
   220	    || die "main must be checked out in the primary worktree"
   221	  release_checkout=$(worktree_for_branch "$release_branch") \
   222	    || die "$release_branch must be checked out in a linked worktree"
   223	
   224	  [[ -f "$release_checkout/$plan_path" ]] || die "missing work unit plan: $plan_path"
   225	  [[ -f "$release_checkout/VERSION" ]] || die "missing VERSION"
   226	
   227	  cd "$release_checkout"
   228	  current_version=$(<VERSION)
   229	  new_version=$(next_version "$current_version")
   230	
   231	  check_verdict "$plan_path"
   232	  check_clean_worktree "$release_checkout" "$release_branch"
   233	  check_origin_main_ancestor "$release_branch"
   234	  check_previous_retro
   235	  check_gate
   236	  check_clean_worktree "$release_checkout" "$release_branch"
   237	  check_archi_fresh
   238	  check_version_exceeds "$new_version" "$current_version"
   239	  check_origin_main_ancestor "$release_branch"
   240	
   241	  release_note=$(extract_release_note "$plan_path")
   242	  pre_release_head=$(git rev-parse HEAD)
   243	  trap 'rollback_release "$pre_release_head"' ERR
   244	
   245	  printf '%s\n' "$new_version" >VERSION
   246	  prepend_changelog "$new_version" "$release_note" "$confirm_delta"
   247	  printf '%s\n' "$slug" >work/.last-released
   248	
   249	  git add VERSION CHANGELOG.md work/.last-released
   250	  git commit -m "Release v$new_version"
   251	  trap - ERR
   252	
   253	  cat <<EOF
   254	release: prepared v$new_version on $release_branch
   255	release: no tag created; local main untouched
   256	release: push $release_branch, open a PR, and merge it after review
   257	EOF
   258	}
   259	
   260	tag_after_merge() {
   261	  local slug="$1"
   262	  local release_branch="wt/$slug"
   263	  local release_checkout
   264	  local version
   265	  local origin_version
   266	  local origin_subject
   267	
   268	  release_checkout=$(worktree_for_branch "$release_branch") \
   269	    || die "$release_branch must be checked out in a linked worktree"
   270	  [[ -f "$release_checkout/VERSION" ]] || die "missing VERSION in $release_branch"
   271	
   272	  git fetch origin main
   273	  git rev-parse --verify --quiet origin/main >/dev/null \
   274	    || die "missing origin/main after fetch"
   275	
   276	  version=$(<"$release_checkout/VERSION")
   277	  origin_version=$(git show origin/main:VERSION) \
   278	    || die "origin/main does not contain VERSION"
   279	  origin_subject=$(git log -1 --format=%s origin/main)
   280	
   281	  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
   282	    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
   283	
   284	  git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
   285	    && die "tag v$version already exists"
   286	
   287	  git tag "v$version" origin/main
   288	  printf 'release: created local tag v%s on origin/main\n' "$version"
   289	}
   290	
   291	if [[ $# -eq 0 ]]; then
   292	  usage
   293	  exit 2
   294	fi
   295	
   296	case "$1" in
   297	  tag-after-merge)
   298	    [[ $# -eq 2 ]] || { usage; exit 2; }
   299	    tag_after_merge "$2"
   300	    ;;
   301	  check-version)
   302	    [[ $# -eq 2 || $# -eq 3 ]] || { usage; exit 2; }
   303	    current=${3:-$(<VERSION)}
   304	    check_version_exceeds "$2" "$current"
   305	    ;;
   306	  next-version)
   307	    [[ $# -le 2 ]] || { usage; exit 2; }
   308	    next_version "${2:-$(<VERSION)}"
   309	    ;;
   310	  -h|--help|help)
   311	    usage
   312	    ;;
   313	  *)
   314	    slug="$1"
   315	    confirm_delta="none"
   316	    shift
   317	    while [[ $# -gt 0 ]]; do
   318	      case "$1" in
   319	        --confirm-delta)
   320	          [[ $# -ge 2 ]] || die "--confirm-delta requires a value"
   321	          confirm_delta="$2"
   322	          shift 2
   323	          ;;
   324	        *)
   325	          usage
   326	          exit 2
   327	          ;;
   328	      esac
   329	    done
   330	    release "$slug" "$confirm_delta"

exec
/bin/zsh -lc "nl -ba tests/test-scripts.sh | sed -n '1800,1960p'" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
 succeeded in 0ms:
  1800	  [ \"\$(cat work/.last-released)\" = demo ]
  1801	"
  1802	
  1803	setup_release_fixture release-stale-before-retro 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous
  1804	(
  1805	  cd "$REL_PRIMARY" || exit 1
  1806	  printf 'remote change\n' >remote-change.txt
  1807	  git add remote-change.txt
  1808	  GIT_AUTHOR_DATE="2026-08-16T10:03:00Z" GIT_COMMITTER_DATE="2026-08-16T10:03:00Z" git commit -qm "advance main"
  1809	  git push -q origin main
  1810	)
  1811	check "release reports stale branch before missing retro" bash -c "
  1812	  cd '$REL_WORKTREE'
  1813	  stale_retro_out='$TMP/release-stale-before-retro.out'
  1814	  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo >\"\$stale_retro_out\" 2>&1; then
  1815	    exit 1
  1816	  fi
  1817	  grep -q 'is stale' \"\$stale_retro_out\" &&
  1818	  ! grep -q 'has no retro.md' \"\$stale_retro_out\"
  1819	"
  1820	
  1821	setup_release_fixture release-sequential 2026.8.9 "Code-review verdict: APPROVE" pass fresh
  1822	check "release refuses stale branch, then computes next micro after sync" bash -c "
  1823	  set -e
  1824	  cd '$REL_WORKTREE'
  1825	  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
  1826	  git push -q origin wt/demo:main
  1827	  rel_b='$TMP/release-sequential/b-wt'
  1828	  git -C '$REL_PRIMARY' branch wt/b main
  1829	  git -C '$REL_PRIMARY' worktree add -q \"\$rel_b\" wt/b
  1830	  git -C \"\$rel_b\" config user.email tester@example.com
  1831	  git -C \"\$rel_b\" config user.name Tester
  1832	  mkdir -p \"\$rel_b/work/b\"
  1833	  sed 's/# Demo/# B/' '$REL_WORKTREE/work/demo/plan.md' > \"\$rel_b/work/b/plan.md\"
  1834	  git -C \"\$rel_b\" add work/b/plan.md
  1835	  GIT_AUTHOR_DATE='2026-08-16T10:00:30Z' GIT_COMMITTER_DATE='2026-08-16T10:00:30Z' git -C \"\$rel_b\" commit -qm 'add b plan'
  1836	  stale_out='$TMP/release-stale.out'
  1837	  if PATH='$REL_FAKEBIN':\$PATH bash \"\$rel_b/scripts/release.sh\" b >\"\$stale_out\" 2>&1; then
  1838	    exit 1
  1839	  fi
  1840	  grep -q 'rebase/sync your branch onto origin/main' \"\$stale_out\"
  1841	  git -C '$REL_PRIMARY' fetch -q origin main
  1842	  git -C '$REL_PRIMARY' reset -q --hard origin/main
  1843	  mkdir -p '$REL_PRIMARY/work/demo'
  1844	  printf 'learned\n' > '$REL_PRIMARY/work/demo/retro.md'
  1845	  git -C '$REL_PRIMARY' add work/demo/retro.md
  1846	  GIT_AUTHOR_DATE='2026-08-16T10:01:30Z' GIT_COMMITTER_DATE='2026-08-16T10:01:30Z' git -C '$REL_PRIMARY' commit -qm 'Retro demo'
  1847	  git -C '$REL_PRIMARY' push -q origin main
  1848	  git -C \"\$rel_b\" fetch -q origin main
  1849	  git -C \"\$rel_b\" rebase -q origin/main
  1850	  cd \"\$rel_b\"
  1851	  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh b
  1852	  [ \"\$(cat VERSION)\" = 2026.8.11 ] &&
  1853	  [ \"\$(git log -1 --format=%s)\" = 'Release v2026.8.11' ] &&
  1854	  ! git rev-parse --verify --quiet refs/tags/v2026.8.11
  1855	"
  1856	
  1857	setup_release_fixture release-mid-gate 2026.8.9 "Code-review verdict: APPROVE" pass fresh
  1858	mkdir -p "$REL_WORKTREE/scripts/gate.d"
  1859	cat >"$REL_WORKTREE/scripts/gate.d/move-origin-main.sh" <<EOF
  1860	#!/usr/bin/env bash
  1861	set -euo pipefail
  1862	repo='$REL_PRIMARY'
  1863	printf 'merge during gate\n' >> "\$repo/remote-change.txt"
  1864	git -C "\$repo" add remote-change.txt
  1865	GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C "\$repo" commit -qm 'merge during gate'
  1866	git -C "\$repo" push -q origin main
  1867	EOF
  1868	chmod +x "$REL_WORKTREE/scripts/gate.d/move-origin-main.sh"
  1869	(
  1870	  cd "$REL_WORKTREE" || exit 1
  1871	  git add scripts/gate.d/move-origin-main.sh
  1872	  GIT_AUTHOR_DATE="2026-08-16T10:00:30Z" GIT_COMMITTER_DATE="2026-08-16T10:00:30Z" git commit -qm "add mid-gate hook"
  1873	)
  1874	check "release catches origin/main moving during gate" bash -c "
  1875	  cd '$REL_WORKTREE'
  1876	  mid_gate_out='$TMP/release-mid-gate.out'
  1877	  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo >\"\$mid_gate_out\" 2>&1; then
  1878	    exit 1
  1879	  fi
  1880	  grep -q 'rebase/sync your branch onto origin/main' \"\$mid_gate_out\"
  1881	"
  1882	
  1883	setup_release_fixture release-tag-after-merge-happy 2026.8.9 "Code-review verdict: APPROVE" pass fresh
  1884	real_git=$(command -v git)
  1885	push_log="$TMP/tag-after-merge-push.log"
  1886	tag_guard_bin="$TMP/tag-after-merge-bin"
  1887	mkdir -p "$tag_guard_bin"
  1888	cat >"$tag_guard_bin/git" <<EOF
  1889	#!/usr/bin/env bash
  1890	if [[ "\$1" == push ]]; then
  1891	  printf 'unexpected push\n' >> "$push_log"
  1892	  exit 99
  1893	fi
  1894	"$real_git" "\$@"
  1895	EOF
  1896	chmod +x "$tag_guard_bin/git"
  1897	check "tag-after-merge creates local tag on origin/main and pushes nothing" bash -c "
  1898	  cd '$REL_WORKTREE' &&
  1899	  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo &&
  1900	  git push -q origin wt/demo:main &&
  1901	  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo &&
  1902	  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$(git rev-parse origin/main)\" ] &&
  1903	  [ ! -s '$push_log' ]
  1904	"
  1905	
  1906	setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
  1907	check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
  1908	  set -e
  1909	  cd '$REL_WORKTREE'
  1910	  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
  1911	  git push -q origin wt/demo:main
  1912	  git -C '$REL_PRIMARY' fetch -q origin main
  1913	  git -C '$REL_PRIMARY' reset -q --hard origin/main
  1914	  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
  1915	  git -C '$REL_PRIMARY' add after-release.txt
  1916	  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
  1917	  git -C '$REL_PRIMARY' push -q origin main
  1918	  wrong_out='$TMP/tag-after-merge-wrong.out'
  1919	  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
  1920	    exit 1
  1921	  fi
  1922	  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
  1923	  ! git rev-parse --verify --quiet refs/tags/v2026.8.10
  1924	"
  1925	
  1926	# --- gate.sh runs and exits cleanly on this repo
  1927	check "gate.sh runs on this repo" bash scripts/gate.sh
  1928	
  1929	echo
  1930	echo "passed: $pass, failed: $fail"
  1931	exit "$((fail > 0 ? 1 : 0))"

exec
/bin/zsh -lc 'rg -n "tag-after-merge|setup_release_fixture|tag_after_merge" scripts/release.sh tests/test-scripts.sh' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
 succeeded in 0ms:
scripts/release.sh:11:  scripts/release.sh tag-after-merge <slug>
scripts/release.sh:18:After the PR merges, tag-after-merge verifies origin/main is the release commit
scripts/release.sh:260:tag_after_merge() {
scripts/release.sh:297:  tag-after-merge)
scripts/release.sh:299:    tag_after_merge "$2"
tests/test-scripts.sh:85:setup_release_fixture() {
tests/test-scripts.sh:1646:setup_release_fixture release-no-verdict 2026.8.9 "Plan verdict: APPROVE" pass fresh
tests/test-scripts.sh:1649:setup_release_fixture release-no-codex-verdict 2026.8.9 "Code-review verdict: APPROVE" pass fresh ""
tests/test-scripts.sh:1652:setup_release_fixture release-gate-fails 2026.8.9 "Code-review verdict: APPROVE" fail fresh
tests/test-scripts.sh:1655:setup_release_fixture release-archi-stale 2026.8.9 "Code-review verdict: APPROVE" pass stale
tests/test-scripts.sh:1658:setup_release_fixture release-version-regresses 2026.9.0 "Code-review verdict: APPROVE" pass fresh
tests/test-scripts.sh:1661:setup_release_fixture release-happy-primary 2026.8.9 "Code-review verdict: APPROVE" pass fresh
tests/test-scripts.sh:1672:setup_release_fixture release-single 2026.8.9 "Code-review verdict: APPROVE" pass fresh
tests/test-scripts.sh:1685:setup_release_fixture release-marker-written 2026.8.9 "Code-review verdict: APPROVE" pass fresh
tests/test-scripts.sh:1693:setup_release_fixture release-marker-rollback 2026.8.9 "Code-review verdict: APPROVE" pass fresh
tests/test-scripts.sh:1710:setup_release_fixture release-prev-no-retro 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous
tests/test-scripts.sh:1713:setup_release_fixture release-prev-empty-retro 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous ""
tests/test-scripts.sh:1716:setup_release_fixture release-prev-retro 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous "learned"
tests/test-scripts.sh:1723:setup_release_fixture release-marker-deleted 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous "learned"
tests/test-scripts.sh:1731:setup_release_fixture release-marker-mutated 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous "learned"
tests/test-scripts.sh:1742:setup_release_fixture release-marker-symlink 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous "learned"
tests/test-scripts.sh:1752:setup_release_fixture release-marker-extra-newline 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous "learned"
tests/test-scripts.sh:1761:setup_release_fixture release-rerun-release-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous "learned"
tests/test-scripts.sh:1768:setup_release_fixture release-bootstrap-empty-marker 2026.8.9 "Code-review verdict: APPROVE" pass fresh
tests/test-scripts.sh:1777:setup_release_fixture release-bootstrap-multiline-marker 2026.8.9 "Code-review verdict: APPROVE" pass fresh
tests/test-scripts.sh:1786:setup_release_fixture release-bootstrap-symlink-marker 2026.8.9 "Code-review verdict: APPROVE" pass fresh
tests/test-scripts.sh:1796:setup_release_fixture release-no-marker 2026.8.9 "Code-review verdict: APPROVE" pass fresh
tests/test-scripts.sh:1803:setup_release_fixture release-stale-before-retro 2026.8.9 "Code-review verdict: APPROVE" pass fresh "Codex-review verdict: APPROVE" previous
tests/test-scripts.sh:1821:setup_release_fixture release-sequential 2026.8.9 "Code-review verdict: APPROVE" pass fresh
tests/test-scripts.sh:1857:setup_release_fixture release-mid-gate 2026.8.9 "Code-review verdict: APPROVE" pass fresh
tests/test-scripts.sh:1883:setup_release_fixture release-tag-after-merge-happy 2026.8.9 "Code-review verdict: APPROVE" pass fresh
tests/test-scripts.sh:1885:push_log="$TMP/tag-after-merge-push.log"
tests/test-scripts.sh:1886:tag_guard_bin="$TMP/tag-after-merge-bin"
tests/test-scripts.sh:1897:check "tag-after-merge creates local tag on origin/main and pushes nothing" bash -c "
tests/test-scripts.sh:1901:  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo &&
tests/test-scripts.sh:1906:setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
tests/test-scripts.sh:1907:check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
tests/test-scripts.sh:1918:  wrong_out='$TMP/tag-after-merge-wrong.out'
tests/test-scripts.sh:1919:  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then

codex
The current implementation confirms the old assumptions: it checks the tip subject and tags `origin/main`. The existing “advanced past release” test only adds a non-version change, which the new plan says should now succeed, so I’ll rewrite that fixture to supersede `VERSION` and add the merge/squash regressions next to the current tests.
exec
/bin/zsh -lc "nl -ba tests/test-scripts.sh | sed -n '1,140p'" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
exec
/bin/zsh -lc "nl -ba tests/test-scripts.sh | sed -n '140,240p'" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
 succeeded in 0ms:
     1	#!/usr/bin/env bash
     2	# Smoke tests for the deterministic layer. Run from repo root: bash tests/test-scripts.sh
     3	set -uo pipefail
     4	
     5	pass=0; fail=0
     6	check() {
     7	  local desc="$1"; shift
     8	  if "$@" >/dev/null 2>&1; then
     9	    echo "ok: $desc"; pass=$((pass+1))
    10	  else
    11	    echo "FAIL: $desc"; fail=$((fail+1))
    12	  fi
    13	}
    14	check_fails() {
    15	  local desc="$1"; shift
    16	  if "$@" >/dev/null 2>&1; then
    17	    echo "FAIL: $desc (expected non-zero exit)"; fail=$((fail+1))
    18	  else
    19	    echo "ok: $desc"; pass=$((pass+1))
    20	  fi
    21	}
    22	check_exit() {
    23	  local desc="$1"
    24	  local expected="$2"
    25	  local stderr_substring="$3"
    26	  shift 3
    27	  local err
    28	  local status
    29	
    30	  err=$(mktemp)
    31	  if "$@" >/dev/null 2>"$err"; then
    32	    status=0
    33	  else
    34	    status=$?
    35	  fi
    36	
    37	  if [[ "$status" -eq "$expected" ]] \
    38	    && { [[ -z "$stderr_substring" ]] || grep -Fq -- "$stderr_substring" "$err"; }; then
    39	    echo "ok: $desc"; pass=$((pass+1))
    40	  else
    41	    echo "FAIL: $desc (exit $status, expected $expected; stderr: $(tr '\n' ' ' <"$err"))"
    42	    fail=$((fail+1))
    43	  fi
    44	  rm -f "$err"
    45	}
    46	
    47	ROOT=$(git rev-parse --show-toplevel)
    48	cd "$ROOT" || exit 1
    49	
    50	# This suite runs nested inside scripts/gate.sh (via the gate.d/ hook), so an inherited
    51	# value would reach every fixture gate and abort it. Keep this here, not beside the gate
    52	# cases — a guard that works only because of where it sits is lost by the next case
    53	# added above it. See knowledge/test-helper-contract.md.
    54	unset GATE_REQUIRED_TOOLS
    55	
    56	commit_fixture() {
    57	  local repo="$1"
    58	  local stamp="$2"
    59	  local msg="$3"
    60	
    61	  (
    62	    cd "$repo" || exit 1
    63	    git add -A
    64	    GIT_AUTHOR_DATE="$stamp" GIT_COMMITTER_DATE="$stamp" git commit -qm "$msg"
    65	  )
    66	}
    67	
    68	write_release_fixture_date() {
    69	  local bin_dir="$1"
    70	  local ym="$2"
    71	  local ymd="$3"
    72	
    73	  mkdir -p "$bin_dir"
    74	  cat >"$bin_dir/date" <<EOF
    75	#!/usr/bin/env bash
    76	case "\${1:-}" in
    77	  +%Y.%-m) printf '%s\n' "$ym" ;;
    78	  +%F) printf '%s\n' "$ymd" ;;
    79	  *) /bin/date "\$@" ;;
    80	esac
    81	EOF
    82	  chmod +x "$bin_dir/date"
    83	}
    84	
    85	setup_release_fixture() {
    86	  local name="$1"
    87	  local version="$2"
    88	  local verdict_line="$3"
    89	  local gate_mode="$4"
    90	  local archi_mode="$5"
    91	  local codex_verdict_line="${6-Codex-review verdict: APPROVE}"
    92	  local marker_slug="${7-}"
    93	  local retro_content="${8-__missing__}"
    94	  local tmp_root="$TMP/$name"
    95	
    96	  REL_PRIMARY="$tmp_root/primary"
    97	  REL_WORKTREE="$tmp_root/demo-wt"
    98	  REL_REMOTE="$tmp_root/remote.git"
    99	  REL_FAKEBIN="$tmp_root/bin"
   100	
   101	  mkdir -p "$tmp_root"
   102	  git init -q -b main "$REL_PRIMARY"
   103	  git init -q --bare "$REL_REMOTE"
   104	  (
   105	    cd "$REL_PRIMARY" || exit 1
   106	    git config user.email tester@example.com
   107	    git config user.name Tester
   108	    git remote add origin "$REL_REMOTE"
   109	
   110	    mkdir -p scripts skills/3-review skills/1-plan/prompts work/demo
   111	    cp "$ROOT/scripts/release.sh" scripts/release.sh
   112	    cp "$ROOT/scripts/archi-fresh.sh" scripts/archi-fresh.sh
   113	    cat >scripts/gate.sh <<'EOF'
   114	#!/usr/bin/env bash
   115	set -euo pipefail
   116	cd "$(git rev-parse --show-toplevel)"
   117	if [[ -f GATE_FAIL ]]; then
   118	  echo "GATE: FAIL"
   119	  exit 1
   120	fi
   121	if compgen -G "scripts/gate.d/*.sh" >/dev/null; then
   122	  for hook in scripts/gate.d/*.sh; do
   123	    bash "$hook"
   124	  done
   125	fi
   126	echo "GATE: PASS"
   127	EOF
   128	    chmod +x scripts/release.sh scripts/archi-fresh.sh scripts/gate.sh
   129	    printf 'name: fixture\n' >config.yaml
   130	    printf 'merge rules\n' >CLAUDE.md
   131	    printf '%s\n' "$version" >VERSION
   132	    printf '# Changelog\n\nAll notable changes to this project are documented in this file.\n\n' >CHANGELOG.md
   133	    {
   134	      printf '# Demo\n\n'
   135	      printf '## Release\n\n'
   136	      printf 'Release note: Demo release note.\n\n'
   137	      printf '## Review\n\n'
   138	      printf '%s\n' "$verdict_line"
   139	      if [[ -n "$codex_verdict_line" ]]; then
   140	        printf '%s\n' "$codex_verdict_line"

 succeeded in 0ms:
   140	        printf '%s\n' "$codex_verdict_line"
   141	      fi
   142	    } >work/demo/plan.md
   143	    [[ "$gate_mode" == fail ]] && printf 'fail\n' >GATE_FAIL
   144	    if [[ -n "$marker_slug" ]]; then
   145	      printf '%s\n' "$marker_slug" >work/.last-released
   146	      if [[ "$retro_content" != __missing__ ]]; then
   147	        mkdir -p "work/$marker_slug"
   148	        printf '%s' "$retro_content" >"work/$marker_slug/retro.md"
   149	      fi
   150	    fi
   151	  )
   152	  commit_fixture "$REL_PRIMARY" "2026-08-16T10:00:00Z" source
   153	  printf 'architecture\n' >"$REL_PRIMARY/ARCHI.md"
   154	  commit_fixture "$REL_PRIMARY" "2026-08-16T10:01:00Z" archi
   155	  if [[ "$archi_mode" == stale ]]; then
   156	    printf 'merge rules updated\n' >>"$REL_PRIMARY/CLAUDE.md"
   157	    commit_fixture "$REL_PRIMARY" "2026-08-16T10:02:00Z" stale-source
   158	  fi
   159	  (
   160	    cd "$REL_PRIMARY" || exit 1
   161	    git push -q -u origin main
   162	    git branch wt/demo
   163	    git worktree add -q "$REL_WORKTREE" wt/demo
   164	    git -C "$REL_WORKTREE" config user.email tester@example.com
   165	    git -C "$REL_WORKTREE" config user.name Tester
   166	  )
   167	  write_release_fixture_date "$REL_FAKEBIN" "2026.8" "2026-08-16"
   168	}
   169	
   170	setup_archi_fresh_fixture() {
   171	  local name="$1"
   172	  local mode="$2"
   173	  local tmp_root="$TMP/$name"
   174	
   175	  ARCHI_REPO="$tmp_root/repo"
   176	
   177	  mkdir -p "$ARCHI_REPO"
   178	  git init -q -b main "$ARCHI_REPO"
   179	  (
   180	    cd "$ARCHI_REPO" || exit 1
   181	    git config user.email tester@example.com
   182	    git config user.name Tester
   183	    mkdir -p scripts skills profiles
   184	    cp "$ROOT/scripts/archi-fresh.sh" scripts/archi-fresh.sh
   185	    chmod +x scripts/archi-fresh.sh
   186	    printf 'name: fixture\n' >config.yaml
   187	    printf 'merge rules\n' >CLAUDE.md
   188	    printf 'profile\n' >profiles/default.md
   189	    printf 'skill\n' >skills/fixture.md
   190	    git add -A
   191	    GIT_AUTHOR_DATE="2026-08-16T10:00:00Z" GIT_COMMITTER_DATE="2026-08-16T10:00:00Z" git commit -qm source
   192	
   193	    if [[ "$mode" == missing-archi ]]; then
   194	      return 0
   195	    fi
   196	
   197	    printf 'architecture\n' >ARCHI.md
   198	    if [[ "$mode" == equal ]]; then
   199	      printf 'merge rules updated\n' >>CLAUDE.md
   200	    fi
   201	    git add -A
   202	    GIT_AUTHOR_DATE="2026-08-16T10:01:00Z" GIT_COMMITTER_DATE="2026-08-16T10:01:00Z" git commit -qm archi
   203	
   204	    case "$mode" in
   205	      stale)
   206	        printf 'skill updated\n' >>skills/fixture.md
   207	        git add skills/fixture.md
   208	        GIT_AUTHOR_DATE="2026-08-16T10:02:00Z" GIT_COMMITTER_DATE="2026-08-16T10:02:00Z" git commit -qm stale-source
   209	        ;;
   210	      branch-ref)
   211	        git branch wt/demo
   212	        printf 'branch-only skill update\n' >>skills/fixture.md
   213	        git add skills/fixture.md
   214	        GIT_AUTHOR_DATE="2026-08-16T10:02:00Z" GIT_COMMITTER_DATE="2026-08-16T10:02:00Z" git commit -qm branch-source
   215	        git branch -f wt/demo HEAD
   216	        git reset -q --hard HEAD~1
   217	        ;;
   218	    esac
   219	  )
   220	}
   221	
   222	setup_codex_review_fixture() {
   223	  local name="$1"
   224	  local command_mode="$2"
   225	  local tmp_root="$TMP/$name"
   226	
   227	  COD_PRIMARY="$tmp_root/primary"
   228	  COD_WORKTREE="$tmp_root/demo-wt"
   229	  COD_REVIEWER="$tmp_root/canned-reviewer.sh"
   230	  COD_MARKER="$tmp_root/reviewer-invoked"
   231	
   232	  mkdir -p "$tmp_root"
   233	  git init -q -b main "$COD_PRIMARY"
   234	  (
   235	    cd "$COD_PRIMARY" || exit 1
   236	    git config user.email tester@example.com
   237	    git config user.name Tester
   238	    mkdir -p scripts work/demo
   239	    cp "$ROOT/scripts/codex-review.sh" scripts/codex-review.sh
   240	    chmod +x scripts/codex-review.sh

exec
/bin/zsh -lc "rg -n \"check_exit|check_fails|check \\\"\" tests/test-scripts.sh | head -n 80" in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
 succeeded in 0ms:
14:check_fails() {
22:check_exit() {
730:  check "shellcheck scripts" shellcheck scripts/*.sh tests/*.sh
739:check_exit "archi-fresh passes when ARCHI is newer than source paths" 0 "" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"
742:check_exit "archi-fresh reports stale source paths" 1 "skills/" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"
743:check_exit "archi-fresh stale message says to refresh branch ARCHI" 1 "refresh ARCHI on the branch" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"
746:check_exit "archi-fresh treats equal epochs as fresh" 0 "" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"
749:check_exit "archi-fresh default ref checks current branch history" 0 "" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"
750:check_exit "archi-fresh explicit ref selects branch history" 1 "skills/" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh wt/demo"
753:check_exit "archi-fresh exits 2 when one side has no history" 2 "ARCHI.md has no git history" bash -c "cd '$ARCHI_REPO' && bash scripts/archi-fresh.sh"
755:check "archi-fresh help documents optional ref" bash -c "
763:check_exit "state missing plan exits non-zero" 1 "not a work unit" bash -c "cd '$STATE_REPO' && bash scripts/state.sh demo"
766:check "state derives plan stage" bash -c "
774:check "state derives implement stage" bash -c "
782:check "state derives review stage before codex review" bash -c "
791:check "state derives release stage before marker" bash -c "
800:check "state derives release stage for retro" bash -c "
808:check "state derives done stage" bash -c "
816:check "state reads review sentinels from wt branch when it exists" bash -c "
824:check "state run is read-only" bash -c "
837:check "state requires both review approval sentinels" bash -c "
846:check "codex-review reads plan body from branch" grep -F "git show \"\$branch:\$plan_path\"" scripts/codex-review.sh
847:check "codex-review reads config from main" grep -F "git show \"main:config.yaml\"" scripts/codex-review.sh
848:check "codex-review prompt names exact verdict format" grep -F 'Codex verdict: REQUEST CHANGES' scripts/codex-review.sh
849:check "codex-review emits verdict instruction after diff" awk '/--- DIFF/ {d=1} d && /Your final line must/ {found=1} END {exit !found}' scripts/codex-review.sh
850:check "codex-review reads deferrals from branch" grep -F "git show \"\$branch:\$deferrals_path\"" scripts/codex-review.sh
851:check "codex-review emits deferrals before the diff" awk '/--- ACCEPTED DEFERRALS/ {f=1} /--- DIFF/ {exit !f}' scripts/codex-review.sh
852:check "3-review skill routes deferrals to the ledger" grep -F 'work/<slug>/deferrals.md' skills/3-review/SKILL.md
853:check "code-reviewer agent is told deferrals are settled scope" grep -F 'work/<slug>/deferrals.md' .claude/agents/code-reviewer.md
854:check "code-reviewer agent defines severity taxonomy" grep -F "CRITICAL" .claude/agents/code-reviewer.md
855:check "code-reviewer agent has calibration section" grep -F "Calibration" .claude/agents/code-reviewer.md
856:check "code-reviewer agent requires concrete failure for blocking" grep -F "finding without a concrete failure scenario is LOW" .claude/agents/code-reviewer.md
857:check "codex-review prompt includes severity taxonomy" grep -F "CRITICAL" scripts/codex-review.sh
858:check "codex-review prompt includes calibration guidance" grep -F "Calibration" scripts/codex-review.sh
859:check "codex-review prompt passes round number" grep -F "REVIEW_ROUND" scripts/codex-review.sh
860:check "3-review skill tracks round counter" grep -F "work/<slug>/review-round" skills/3-review/SKILL.md
861:check "3-review skill routes by severity" grep -F "CRITICAL/HIGH" skills/3-review/SKILL.md
862:check "3-review skill caps at round 3 mechanically" grep -F "counter reaches 3" skills/3-review/SKILL.md
863:check "3-review skill keeps codex-review work artifacts out of diff" grep -F "git diff origin/main...wt/<slug> -- ':/' \":(exclude,top)work/<slug>\"" skills/3-review/SKILL.md
866:check_exit "codex-review approve exits 0" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
867:check "codex-review writes stdout artifact" grep -Fx 'Codex verdict: APPROVE' "$COD_PRIMARY/work/demo/codex-review.md"
870:check_exit "codex-review accepts indented approve verdict" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
873:check_exit "codex-review request-changes exits 1" 1 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
876:check_exit "codex-review ignores branch reviewer.command override" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
879:check_exit "codex-review missing verdict exits 2" 2 "no verdict" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
882:check_exit "codex-review missing reviewer.command exits 2" 2 "reviewer.command" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
885:check_exit "codex-review parser stops before later command" 2 "reviewer.command" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
888:check_exit "codex-review ignores commented command and uses real one" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
891:check_exit "codex-review missing branch plan exits 2 before reviewer" 2 "cannot read plan" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
892:check "codex-review does not invoke reviewer when branch plan is missing" test ! -e "$COD_MARKER"
896:check_exit "codex-review reviewer failure exits 2 before verdict parsing" 2 "reviewer command failed (exit 42)" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
897:check "codex-review reviewer failure preserves previous artifact" bash -c "
902:check_exit "codex-review refuses wt checkout as root" 2 "primary checkout" bash -c "cd '$COD_WORKTREE' && bash '$COD_PRIMARY/scripts/codex-review.sh' demo"
905:check_exit "codex-review artifact-only run exits 0" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
906:check "codex-review only dirties primary artifact" bash -c "
910:check "codex-review leaves worktree branch clean" bash -c "[ \"\$(git -C '$COD_WORKTREE' status --porcelain)\" = '' ]"
916:check_exit "codex-review with branch artifacts exits 0" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
917:check "codex-review excludes work unit artifacts from reviewer diff" bash -c "
921:check_exit "codex-review from subdirectory exits 0" 0 "" bash -c "cd '$COD_PRIMARY/subdir' && bash ../scripts/codex-review.sh demo"
922:check "codex-review from subdirectory includes top-level branch diff" grep -F '+feature' "$TMP/codex-excludes-work-artifacts/prompt.txt"
923:check "codex-review from subdirectory excludes work unit artifacts" bash -c "
926:check "codex-review marks an absent deferral ledger explicitly" bash -c "
935:check_exit "codex-review with a deferral ledger exits 0" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
936:check "codex-review injects the deferral ledger into the prompt" bash -c "
939:check "codex-review deferral ledger is not treated as absent" bash -c "
943:check "codex-review prompt includes round number from REVIEW_ROUND" bash -c "
948:check_exit "codex-review passes custom round number" 0 "" bash -c "cd '$COD_PRIMARY' && REVIEW_ROUND=3 bash scripts/codex-review.sh demo"
949:check "codex-review prompt contains round 3" bash -c "
954:check_exit "codex-review excludes origin-main-only changes" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
955:check "codex-review bases diff on origin/main when local main is stale" bash -c "
962:check_exit "codex-review falls back to local main without origin/main" 0 "" bash -c "cd '$COD_PRIMARY' && bash scripts/codex-review.sh demo"
963:check "codex-review fallback prompt uses local main base" bash -c "
979:check "worktree add creates directory" test -d "$WT_PATH"
980:check "worktree branch checked out" bash -c "cd '$WT_PATH' && [ \"\$(git branch --show-current)\" = wt/demo ]"
981:check "worktree.sh works FROM INSIDE a worktree (.git-as-file)" bash -c "cd '$WT_PATH' && bash wt.sh list"
982:check "worktree remove" bash -c "cd '$SB' && bash wt.sh remove demo"
983:check_fails "worktree add without slug fails" bash -c "cd '$SB' && bash wt.sh add"
1007:check "worktree add bases new branch on origin/main from feature branch" bash -c "
1027:check "worktree add falls back to HEAD without origin/main" bash -c "
1054:check "worktree add uses stale origin/main when fetch fails" bash -c "

codex
I’ve got the flow now. I’m making the smallest surgical change: keep the existing fetch, branch worktree lookup, current-version guard, and tag-exists guard; replace only the subject/tip assumption with a `VERSION` transition scan over `origin/main`.
apply patch
patch: completed
/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit/scripts/release.sh
diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then

diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then

codex
The code change is in place. I’m updating the tests now: one fixture for a true merge commit above the release, one for a squash-style commit with a non-release subject, and the refusal case now advances `VERSION` past the branch version so it exercises the retained currency guard.
apply patch
patch: completed
/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit/tests/test-scripts.sh
diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index 1e9d962f00d5c78aff867c1380b626b7ddf97e75..a6959c3a957c5897da5baf5060d314dde33249bc
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1903,23 +1903,70 @@
   [ ! -s '$push_log' ]
 "
 
-setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
-check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
+check "tag-after-merge refuses when local tag already exists" bash -c "
+  cd '$REL_WORKTREE'
+  retag_out='$TMP/tag-after-merge-retag.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
+    exit 1
+  fi
+  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
+"
+
+setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
   set -e
+  : > '$push_log'
   cd '$REL_WORKTREE'
   PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  release_commit=\$(git rev-parse HEAD)
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
+  git -C '$REL_PRIMARY' add review.txt
+  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
+  [ ! -s '$push_log' ]
+"
+
+setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags squash commit with non-release subject" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
+  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
+  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
+  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
+  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
+"
+
+setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
   git push -q origin wt/demo:main
   git -C '$REL_PRIMARY' fetch -q origin main
   git -C '$REL_PRIMARY' reset -q --hard origin/main
-  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
-  git -C '$REL_PRIMARY' add after-release.txt
-  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
+  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
+  git -C '$REL_PRIMARY' add VERSION
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
   git -C '$REL_PRIMARY' push -q origin main
-  wrong_out='$TMP/tag-after-merge-wrong.out'
-  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
+  not_current_out='$TMP/tag-after-merge-not-current.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
     exit 1
   fi
-  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
+  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
   ! git rev-parse --verify --quiet refs/tags/v2026.8.10
 "
 

diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index 1e9d962f00d5c78aff867c1380b626b7ddf97e75..a6959c3a957c5897da5baf5060d314dde33249bc
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1903,23 +1903,70 @@
   [ ! -s '$push_log' ]
 "
 
-setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
-check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
+check "tag-after-merge refuses when local tag already exists" bash -c "
+  cd '$REL_WORKTREE'
+  retag_out='$TMP/tag-after-merge-retag.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
+    exit 1
+  fi
+  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
+"
+
+setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
   set -e
+  : > '$push_log'
   cd '$REL_WORKTREE'
   PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  release_commit=\$(git rev-parse HEAD)
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
+  git -C '$REL_PRIMARY' add review.txt
+  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
+  [ ! -s '$push_log' ]
+"
+
+setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags squash commit with non-release subject" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
+  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
+  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
+  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
+  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
+"
+
+setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
   git push -q origin wt/demo:main
   git -C '$REL_PRIMARY' fetch -q origin main
   git -C '$REL_PRIMARY' reset -q --hard origin/main
-  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
-  git -C '$REL_PRIMARY' add after-release.txt
-  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
+  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
+  git -C '$REL_PRIMARY' add VERSION
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
   git -C '$REL_PRIMARY' push -q origin main
-  wrong_out='$TMP/tag-after-merge-wrong.out'
-  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
+  not_current_out='$TMP/tag-after-merge-not-current.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
     exit 1
   fi
-  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
+  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
   ! git rev-parse --verify --quiet refs/tags/v2026.8.10
 "
 

codex
The test block now mirrors the requested behaviors without widening the footprint. I’m going to run the script test suite first, because it will catch fixture mistakes faster than the full gate, then I’ll run the required gate.
exec
/bin/zsh -lc 'bash tests/test-scripts.sh' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index 1e9d962f00d5c78aff867c1380b626b7ddf97e75..a6959c3a957c5897da5baf5060d314dde33249bc
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1903,23 +1903,70 @@
   [ ! -s '$push_log' ]
 "
 
-setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
-check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
+check "tag-after-merge refuses when local tag already exists" bash -c "
+  cd '$REL_WORKTREE'
+  retag_out='$TMP/tag-after-merge-retag.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
+    exit 1
+  fi
+  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
+"
+
+setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
   set -e
+  : > '$push_log'
   cd '$REL_WORKTREE'
   PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  release_commit=\$(git rev-parse HEAD)
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
+  git -C '$REL_PRIMARY' add review.txt
+  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
+  [ ! -s '$push_log' ]
+"
+
+setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags squash commit with non-release subject" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
+  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
+  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
+  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
+  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
+"
+
+setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
   git push -q origin wt/demo:main
   git -C '$REL_PRIMARY' fetch -q origin main
   git -C '$REL_PRIMARY' reset -q --hard origin/main
-  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
-  git -C '$REL_PRIMARY' add after-release.txt
-  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
+  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
+  git -C '$REL_PRIMARY' add VERSION
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
   git -C '$REL_PRIMARY' push -q origin main
-  wrong_out='$TMP/tag-after-merge-wrong.out'
-  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
+  not_current_out='$TMP/tag-after-merge-not-current.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
     exit 1
   fi
-  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
+  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
   ! git rev-parse --verify --quiet refs/tags/v2026.8.10
 "
 

codex
The suite is still running, but the release-area tests leading up to the edited block are passing so far. I’m waiting for the full result rather than declaring victory early.
diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index 1e9d962f00d5c78aff867c1380b626b7ddf97e75..a6959c3a957c5897da5baf5060d314dde33249bc
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1903,23 +1903,70 @@
   [ ! -s '$push_log' ]
 "
 
-setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
-check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
+check "tag-after-merge refuses when local tag already exists" bash -c "
+  cd '$REL_WORKTREE'
+  retag_out='$TMP/tag-after-merge-retag.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
+    exit 1
+  fi
+  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
+"
+
+setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
   set -e
+  : > '$push_log'
   cd '$REL_WORKTREE'
   PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  release_commit=\$(git rev-parse HEAD)
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
+  git -C '$REL_PRIMARY' add review.txt
+  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
+  [ ! -s '$push_log' ]
+"
+
+setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags squash commit with non-release subject" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
+  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
+  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
+  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
+  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
+"
+
+setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
   git push -q origin wt/demo:main
   git -C '$REL_PRIMARY' fetch -q origin main
   git -C '$REL_PRIMARY' reset -q --hard origin/main
-  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
-  git -C '$REL_PRIMARY' add after-release.txt
-  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
+  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
+  git -C '$REL_PRIMARY' add VERSION
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
   git -C '$REL_PRIMARY' push -q origin main
-  wrong_out='$TMP/tag-after-merge-wrong.out'
-  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
+  not_current_out='$TMP/tag-after-merge-not-current.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
     exit 1
   fi
-  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
+  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
   ! git rev-parse --verify --quiet refs/tags/v2026.8.10
 "
 

codex
Good signal: all five `tag-after-merge` checks passed, including merge-commit and squash. The rest of the suite is continuing through the gate-related checks.
diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index 1e9d962f00d5c78aff867c1380b626b7ddf97e75..a6959c3a957c5897da5baf5060d314dde33249bc
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1903,23 +1903,70 @@
   [ ! -s '$push_log' ]
 "
 
-setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
-check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
+check "tag-after-merge refuses when local tag already exists" bash -c "
+  cd '$REL_WORKTREE'
+  retag_out='$TMP/tag-after-merge-retag.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
+    exit 1
+  fi
+  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
+"
+
+setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
   set -e
+  : > '$push_log'
   cd '$REL_WORKTREE'
   PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  release_commit=\$(git rev-parse HEAD)
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
+  git -C '$REL_PRIMARY' add review.txt
+  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
+  [ ! -s '$push_log' ]
+"
+
+setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags squash commit with non-release subject" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
+  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
+  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
+  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
+  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
+"
+
+setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
   git push -q origin wt/demo:main
   git -C '$REL_PRIMARY' fetch -q origin main
   git -C '$REL_PRIMARY' reset -q --hard origin/main
-  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
-  git -C '$REL_PRIMARY' add after-release.txt
-  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
+  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
+  git -C '$REL_PRIMARY' add VERSION
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
   git -C '$REL_PRIMARY' push -q origin main
-  wrong_out='$TMP/tag-after-merge-wrong.out'
-  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
+  not_current_out='$TMP/tag-after-merge-not-current.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
     exit 1
   fi
-  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
+  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
   ! git rev-parse --verify --quiet refs/tags/v2026.8.10
 "
 

 exited 1 in 76027ms:
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
ok: codex-review prompt includes severity taxonomy
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
FAIL: gate.sh runs on this repo

passed: 187, failed: 1

codex
The direct script suite found one failure: its final “gate.sh runs on this repo” check. Since the edited release tests passed, I’m running the gate directly now to see the actual diagnostic instead of guessing from the smoke-suite wrapper.
exec
/bin/zsh -lc 'bash scripts/gate.sh' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index 1e9d962f00d5c78aff867c1380b626b7ddf97e75..a6959c3a957c5897da5baf5060d314dde33249bc
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1903,23 +1903,70 @@
   [ ! -s '$push_log' ]
 "
 
-setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
-check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
+check "tag-after-merge refuses when local tag already exists" bash -c "
+  cd '$REL_WORKTREE'
+  retag_out='$TMP/tag-after-merge-retag.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
+    exit 1
+  fi
+  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
+"
+
+setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
   set -e
+  : > '$push_log'
   cd '$REL_WORKTREE'
   PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  release_commit=\$(git rev-parse HEAD)
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
+  git -C '$REL_PRIMARY' add review.txt
+  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
+  [ ! -s '$push_log' ]
+"
+
+setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags squash commit with non-release subject" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
+  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
+  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
+  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
+  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
+"
+
+setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
   git push -q origin wt/demo:main
   git -C '$REL_PRIMARY' fetch -q origin main
   git -C '$REL_PRIMARY' reset -q --hard origin/main
-  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
-  git -C '$REL_PRIMARY' add after-release.txt
-  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
+  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
+  git -C '$REL_PRIMARY' add VERSION
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
   git -C '$REL_PRIMARY' push -q origin main
-  wrong_out='$TMP/tag-after-merge-wrong.out'
-  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
+  not_current_out='$TMP/tag-after-merge-not-current.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
     exit 1
   fi
-  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
+  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
   ! git rev-parse --verify --quiet refs/tags/v2026.8.10
 "
 

codex
The gate’s only visible failure so far is `pytest -q` crashing with a segmentation fault before the shell checks. The shellcheck and the full script smoke suite are running cleanly inside the same gate, so this looks outside the touched shell files; I’ll still let the gate finish and then decide whether a retry is warranted.
diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index 1e9d962f00d5c78aff867c1380b626b7ddf97e75..a6959c3a957c5897da5baf5060d314dde33249bc
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1903,23 +1903,70 @@
   [ ! -s '$push_log' ]
 "
 
-setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
-check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
+check "tag-after-merge refuses when local tag already exists" bash -c "
+  cd '$REL_WORKTREE'
+  retag_out='$TMP/tag-after-merge-retag.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
+    exit 1
+  fi
+  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
+"
+
+setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
   set -e
+  : > '$push_log'
   cd '$REL_WORKTREE'
   PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  release_commit=\$(git rev-parse HEAD)
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
+  git -C '$REL_PRIMARY' add review.txt
+  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
+  [ ! -s '$push_log' ]
+"
+
+setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags squash commit with non-release subject" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
+  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
+  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
+  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
+  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
+"
+
+setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
   git push -q origin wt/demo:main
   git -C '$REL_PRIMARY' fetch -q origin main
   git -C '$REL_PRIMARY' reset -q --hard origin/main
-  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
-  git -C '$REL_PRIMARY' add after-release.txt
-  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
+  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
+  git -C '$REL_PRIMARY' add VERSION
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
   git -C '$REL_PRIMARY' push -q origin main
-  wrong_out='$TMP/tag-after-merge-wrong.out'
-  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
+  not_current_out='$TMP/tag-after-merge-not-current.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
     exit 1
   fi
-  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
+  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
   ! git rev-parse --verify --quiet refs/tags/v2026.8.10
 "
 

 exited 1 in 40565ms:
scripts/gate.sh: line 16: 35709 Segmentation fault: 11  "$@"
✗ FAILED: pytest -q
▶ shellcheck scripts/agent-exec.sh scripts/archi-fresh.sh scripts/codex-review.sh scripts/fan-exec.sh scripts/gate.d/ds-hygiene.sh scripts/gate.d/eval.sh scripts/gate.d/examples/ds-hygiene.sh scripts/gate.d/examples/nb-clean.sh scripts/gate.d/nb-clean.sh scripts/gate.d/py-quality.sh scripts/gate.d/test-scripts.sh scripts/gate.sh scripts/release.sh scripts/state.sh scripts/worktree.sh tests/test-scripts.sh
▶ bash scripts/gate.d/ds-hygiene.sh
▶ bash scripts/gate.d/eval.sh
eval check passed; draws_consumed=7040
▶ bash scripts/gate.d/nb-clean.sh
▶ bash scripts/gate.d/py-quality.sh
▶ ruff format --check .
48 files already formatted
▶ mypy src
Success: no issues found in 7 source files
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
ok: codex-review prompt includes severity taxonomy
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
FAIL: gate.sh runs on this repo

passed: 187, failed: 1
✗ FAILED: bash scripts/gate.d/test-scripts.sh
GATE: FAIL — fix everything marked ✗ above.

codex
The gate finished red because `pytest -q` segfaulted, and that made the nested self-gate check fail too. I’m going to run `pytest -q` directly once to distinguish a flaky interpreter crash from a deterministic repo failure before I touch anything else.
exec
/bin/zsh -lc 'pytest -q' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index 1e9d962f00d5c78aff867c1380b626b7ddf97e75..a6959c3a957c5897da5baf5060d314dde33249bc
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1903,23 +1903,70 @@
   [ ! -s '$push_log' ]
 "
 
-setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
-check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
+check "tag-after-merge refuses when local tag already exists" bash -c "
+  cd '$REL_WORKTREE'
+  retag_out='$TMP/tag-after-merge-retag.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
+    exit 1
+  fi
+  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
+"
+
+setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
   set -e
+  : > '$push_log'
   cd '$REL_WORKTREE'
   PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  release_commit=\$(git rev-parse HEAD)
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
+  git -C '$REL_PRIMARY' add review.txt
+  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
+  [ ! -s '$push_log' ]
+"
+
+setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags squash commit with non-release subject" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
+  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
+  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
+  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
+  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
+"
+
+setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
   git push -q origin wt/demo:main
   git -C '$REL_PRIMARY' fetch -q origin main
   git -C '$REL_PRIMARY' reset -q --hard origin/main
-  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
-  git -C '$REL_PRIMARY' add after-release.txt
-  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
+  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
+  git -C '$REL_PRIMARY' add VERSION
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
   git -C '$REL_PRIMARY' push -q origin main
-  wrong_out='$TMP/tag-after-merge-wrong.out'
-  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
+  not_current_out='$TMP/tag-after-merge-not-current.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
     exit 1
   fi
-  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
+  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
   ! git rev-parse --verify --quiet refs/tags/v2026.8.10
 "
 

 exited -1 in 162ms:
codex
`pytest -q` segfaults immediately even outside the gate, with no test output. I’m not editing outside the footprint, but I’m going to grab a faulthandler trace so the blocker is concrete rather than a shrug in a trench coat.
exec
/bin/zsh -lc 'python -X faulthandler -m pytest -q' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index 1e9d962f00d5c78aff867c1380b626b7ddf97e75..a6959c3a957c5897da5baf5060d314dde33249bc
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1903,23 +1903,70 @@
   [ ! -s '$push_log' ]
 "
 
-setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
-check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
+check "tag-after-merge refuses when local tag already exists" bash -c "
+  cd '$REL_WORKTREE'
+  retag_out='$TMP/tag-after-merge-retag.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
+    exit 1
+  fi
+  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
+"
+
+setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
   set -e
+  : > '$push_log'
   cd '$REL_WORKTREE'
   PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  release_commit=\$(git rev-parse HEAD)
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
+  git -C '$REL_PRIMARY' add review.txt
+  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
+  [ ! -s '$push_log' ]
+"
+
+setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags squash commit with non-release subject" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
+  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
+  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
+  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
+  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
+"
+
+setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
   git push -q origin wt/demo:main
   git -C '$REL_PRIMARY' fetch -q origin main
   git -C '$REL_PRIMARY' reset -q --hard origin/main
-  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
-  git -C '$REL_PRIMARY' add after-release.txt
-  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
+  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
+  git -C '$REL_PRIMARY' add VERSION
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
   git -C '$REL_PRIMARY' push -q origin main
-  wrong_out='$TMP/tag-after-merge-wrong.out'
-  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
+  not_current_out='$TMP/tag-after-merge-not-current.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
     exit 1
   fi
-  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
+  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
   ! git rev-parse --verify --quiet refs/tags/v2026.8.10
 "
 

 exited -1 in 134ms:
Fatal Python error: Segmentation fault

Current thread 0x00000001f40bbac0 (most recent call first):
  File "<frozen importlib._bootstrap>", line 488 in _call_with_frames_removed
  File "<frozen importlib._bootstrap_external>", line 1289 in create_module
  File "<frozen importlib._bootstrap>", line 813 in module_from_spec
  File "<frozen importlib._bootstrap>", line 921 in _load_unlocked
  File "<frozen importlib._bootstrap>", line 1331 in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 1360 in _find_and_load
  File "/opt/miniconda3/lib/python3.12/site-packages/_pytest/capture.py", line 95 in _readline_workaround
  File "/opt/miniconda3/lib/python3.12/site-packages/_pytest/capture.py", line 161 in pytest_load_initial_conftests
  File "/opt/miniconda3/lib/python3.12/site-packages/pluggy/_callers.py", line 116 in _multicall
  File "/opt/miniconda3/lib/python3.12/site-packages/pluggy/_manager.py", line 120 in _hookexec
  File "/opt/miniconda3/lib/python3.12/site-packages/pluggy/_hooks.py", line 512 in __call__
  File "/opt/miniconda3/lib/python3.12/site-packages/_pytest/config/__init__.py", line 1556 in parse
  File "/opt/miniconda3/lib/python3.12/site-packages/_pytest/config/__init__.py", line 1186 in pytest_cmdline_parse
  File "/opt/miniconda3/lib/python3.12/site-packages/pluggy/_callers.py", line 121 in _multicall
  File "/opt/miniconda3/lib/python3.12/site-packages/pluggy/_manager.py", line 120 in _hookexec
  File "/opt/miniconda3/lib/python3.12/site-packages/pluggy/_hooks.py", line 512 in __call__
  File "/opt/miniconda3/lib/python3.12/site-packages/_pytest/config/__init__.py", line 361 in _prepareconfig
  File "/opt/miniconda3/lib/python3.12/site-packages/_pytest/config/__init__.py", line 193 in main
  File "/opt/miniconda3/lib/python3.12/site-packages/_pytest/config/__init__.py", line 223 in console_main
  File "/opt/miniconda3/lib/python3.12/site-packages/pytest/__main__.py", line 9 in <module>
  File "<frozen runpy>", line 88 in _run_code
  File "<frozen runpy>", line 198 in _run_module_as_main

codex
The faulthandler trace points to pytest crashing while importing its capture/readline path, before any repo tests run. That’s outside the allowed file footprint, so I’m checking the actual diff and local shell validation now, then I’ll decide how to handle the requested commit with the gate blocker clearly recorded.
exec
/bin/zsh -lc 'git diff -- scripts/release.sh tests/test-scripts.sh' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
exec
/bin/zsh -lc 'git diff --check -- scripts/release.sh tests/test-scripts.sh' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
 succeeded in 0ms:
 succeeded in 0ms:
diff --git a/scripts/release.sh b/scripts/release.sh
index 5335666..2ac7971 100755
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@ Usage:
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@ tag_after_merge() {
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@ tag_after_merge() {
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index 1e9d962..a6959c3 100755
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1903,23 +1903,70 @@ check "tag-after-merge creates local tag on origin/main and pushes nothing" bash
   [ ! -s '$push_log' ]
 "
 
-setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
-check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
+check "tag-after-merge refuses when local tag already exists" bash -c "
+  cd '$REL_WORKTREE'
+  retag_out='$TMP/tag-after-merge-retag.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
+    exit 1
+  fi
+  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
+"
+
+setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
+  set -e
+  : > '$push_log'
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  release_commit=\$(git rev-parse HEAD)
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
+  git -C '$REL_PRIMARY' add review.txt
+  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
+  [ ! -s '$push_log' ]
+"
+
+setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags squash commit with non-release subject" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
+  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
+  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
+  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
+  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
+"
+
+setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
   set -e
   cd '$REL_WORKTREE'
   PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
   git push -q origin wt/demo:main
   git -C '$REL_PRIMARY' fetch -q origin main
   git -C '$REL_PRIMARY' reset -q --hard origin/main
-  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
-  git -C '$REL_PRIMARY' add after-release.txt
-  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
+  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
+  git -C '$REL_PRIMARY' add VERSION
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
   git -C '$REL_PRIMARY' push -q origin main
-  wrong_out='$TMP/tag-after-merge-wrong.out'
-  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
+  not_current_out='$TMP/tag-after-merge-not-current.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
     exit 1
   fi
-  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
+  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
   ! git rev-parse --verify --quiet refs/tags/v2026.8.10
 "
 

exec
/bin/zsh -lc 'shellcheck scripts/release.sh tests/test-scripts.sh' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index 1e9d962f00d5c78aff867c1380b626b7ddf97e75..a6959c3a957c5897da5baf5060d314dde33249bc
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1903,23 +1903,70 @@
   [ ! -s '$push_log' ]
 "
 
-setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
-check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
+check "tag-after-merge refuses when local tag already exists" bash -c "
+  cd '$REL_WORKTREE'
+  retag_out='$TMP/tag-after-merge-retag.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
+    exit 1
+  fi
+  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
+"
+
+setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
   set -e
+  : > '$push_log'
   cd '$REL_WORKTREE'
   PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  release_commit=\$(git rev-parse HEAD)
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
+  git -C '$REL_PRIMARY' add review.txt
+  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
+  [ ! -s '$push_log' ]
+"
+
+setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags squash commit with non-release subject" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
+  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
+  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
+  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
+  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
+"
+
+setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
   git push -q origin wt/demo:main
   git -C '$REL_PRIMARY' fetch -q origin main
   git -C '$REL_PRIMARY' reset -q --hard origin/main
-  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
-  git -C '$REL_PRIMARY' add after-release.txt
-  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
+  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
+  git -C '$REL_PRIMARY' add VERSION
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
   git -C '$REL_PRIMARY' push -q origin main
-  wrong_out='$TMP/tag-after-merge-wrong.out'
-  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
+  not_current_out='$TMP/tag-after-merge-not-current.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
     exit 1
   fi
-  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
+  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
   ! git rev-parse --verify --quiet refs/tags/v2026.8.10
 "
 

 succeeded in 894ms:
codex
The footprint diff is clean, `git diff --check` is clean, and `shellcheck` passes for the edited files. The remaining blocker is still the pre-existing-looking pytest interpreter crash, not the shell changes; I’m checking status now and then I’ll commit the scoped work with that caveat noted.
exec
/bin/zsh -lc 'git status --short && git branch --show-current' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
 succeeded in 0ms:
 M scripts/release.sh
 M tests/test-scripts.sh
wt/release-tag-merge-commit

diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index 1e9d962f00d5c78aff867c1380b626b7ddf97e75..a6959c3a957c5897da5baf5060d314dde33249bc
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1903,23 +1903,70 @@
   [ ! -s '$push_log' ]
 "
 
-setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
-check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
+check "tag-after-merge refuses when local tag already exists" bash -c "
+  cd '$REL_WORKTREE'
+  retag_out='$TMP/tag-after-merge-retag.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
+    exit 1
+  fi
+  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
+"
+
+setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
   set -e
+  : > '$push_log'
   cd '$REL_WORKTREE'
   PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  release_commit=\$(git rev-parse HEAD)
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
+  git -C '$REL_PRIMARY' add review.txt
+  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
+  [ ! -s '$push_log' ]
+"
+
+setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags squash commit with non-release subject" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
+  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
+  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
+  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
+  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
+"
+
+setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
   git push -q origin wt/demo:main
   git -C '$REL_PRIMARY' fetch -q origin main
   git -C '$REL_PRIMARY' reset -q --hard origin/main
-  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
-  git -C '$REL_PRIMARY' add after-release.txt
-  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
+  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
+  git -C '$REL_PRIMARY' add VERSION
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
   git -C '$REL_PRIMARY' push -q origin main
-  wrong_out='$TMP/tag-after-merge-wrong.out'
-  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
+  not_current_out='$TMP/tag-after-merge-not-current.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
     exit 1
   fi
-  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
+  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
   ! git rev-parse --verify --quiet refs/tags/v2026.8.10
 "
 

exec
/bin/zsh -lc 'git add scripts/release.sh tests/test-scripts.sh && git commit -m "Tag release commit after merge by version transition"' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
 succeeded in 0ms:
[wt/release-tag-merge-commit 59d551c] Tag release commit after merge by version transition
 2 files changed, 93 insertions(+), 16 deletions(-)

diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index 1e9d962f00d5c78aff867c1380b626b7ddf97e75..a6959c3a957c5897da5baf5060d314dde33249bc
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1903,23 +1903,70 @@
   [ ! -s '$push_log' ]
 "
 
-setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
-check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
+check "tag-after-merge refuses when local tag already exists" bash -c "
+  cd '$REL_WORKTREE'
+  retag_out='$TMP/tag-after-merge-retag.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
+    exit 1
+  fi
+  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
+"
+
+setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
   set -e
+  : > '$push_log'
   cd '$REL_WORKTREE'
   PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  release_commit=\$(git rev-parse HEAD)
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
+  git -C '$REL_PRIMARY' add review.txt
+  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
+  [ ! -s '$push_log' ]
+"
+
+setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags squash commit with non-release subject" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
+  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
+  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
+  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
+  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
+"
+
+setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
   git push -q origin wt/demo:main
   git -C '$REL_PRIMARY' fetch -q origin main
   git -C '$REL_PRIMARY' reset -q --hard origin/main
-  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
-  git -C '$REL_PRIMARY' add after-release.txt
-  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
+  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
+  git -C '$REL_PRIMARY' add VERSION
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
   git -C '$REL_PRIMARY' push -q origin main
-  wrong_out='$TMP/tag-after-merge-wrong.out'
-  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
+  not_current_out='$TMP/tag-after-merge-not-current.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
     exit 1
   fi
-  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
+  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
   ! git rev-parse --verify --quiet refs/tags/v2026.8.10
 "
 

codex
The scoped changes are committed on the requested branch. I’m doing one final status check so the handoff is clear and there are no stray edits from the test runs.
exec
/bin/zsh -lc 'git status --short && git log -1 --oneline' in /Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit
 succeeded in 0ms:
59d551c Tag release commit after merge by version transition

diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index 1e9d962f00d5c78aff867c1380b626b7ddf97e75..a6959c3a957c5897da5baf5060d314dde33249bc
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1903,23 +1903,70 @@
   [ ! -s '$push_log' ]
 "
 
-setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
-check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
+check "tag-after-merge refuses when local tag already exists" bash -c "
+  cd '$REL_WORKTREE'
+  retag_out='$TMP/tag-after-merge-retag.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
+    exit 1
+  fi
+  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
+"
+
+setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
   set -e
+  : > '$push_log'
   cd '$REL_WORKTREE'
   PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  release_commit=\$(git rev-parse HEAD)
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
+  git -C '$REL_PRIMARY' add review.txt
+  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
+  [ ! -s '$push_log' ]
+"
+
+setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags squash commit with non-release subject" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
+  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
+  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
+  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
+  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
+"
+
+setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
   git push -q origin wt/demo:main
   git -C '$REL_PRIMARY' fetch -q origin main
   git -C '$REL_PRIMARY' reset -q --hard origin/main
-  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
-  git -C '$REL_PRIMARY' add after-release.txt
-  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
+  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
+  git -C '$REL_PRIMARY' add VERSION
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
   git -C '$REL_PRIMARY' push -q origin main
-  wrong_out='$TMP/tag-after-merge-wrong.out'
-  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
+  not_current_out='$TMP/tag-after-merge-not-current.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
     exit 1
   fi
-  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
+  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
   ! git rev-parse --verify --quiet refs/tags/v2026.8.10
 "
 

codex
Implemented and committed the scoped change.

Commit: `59d551c Tag release commit after merge by version transition`

Changed:
- [scripts/release.sh](/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit/scripts/release.sh): `tag-after-merge` now keeps the current-version guard, finds the commit that transitioned `VERSION` to the release version on `origin/main`, and tags that SHA instead of `origin/main`’s tip.
- [tests/test-scripts.sh](/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit/tests/test-scripts.sh): added/updated coverage for ff, merge commit, squash merge, not-current refusal, no-push behavior, and re-tag refusal.

Validation:
- `shellcheck scripts/release.sh tests/test-scripts.sh` passed.
- `git diff --check -- scripts/release.sh tests/test-scripts.sh` passed.
- `bash tests/test-scripts.sh` passed all edited `tag-after-merge` tests, but failed its final repo gate check.
- `bash scripts/gate.sh` did not pass because `pytest -q` segfaults before running repo tests:
  `Fatal Python error: Segmentation fault` in pytest capture/readline import path.

Out of scope: I did not modify gate/pytest/environment files because they are outside the hard footprint. The worktree is clean.
diff --git a/scripts/release.sh b/scripts/release.sh
index 53356664a9ab3aae25dab23a61b6652a5aed0a59..2ac7971a8ad2c3f01b17bff1c68e04a0af4b0092
--- a/scripts/release.sh
+++ b/scripts/release.sh
@@ -15,8 +15,9 @@
 The release path never pushes, never tags, and never touches main. It commits
 the version bump on the release branch for PR review.
 
-After the PR merges, tag-after-merge verifies origin/main is the release commit
-and creates the local version tag. The tag push is a separate confirmed step.
+After the PR merges, tag-after-merge locates the release commit by SHA from
+the VERSION transition on origin/main and creates the local version tag. The tag
+push is a separate confirmed step.
 EOF
 }
 
@@ -263,7 +264,12 @@
   local release_checkout
   local version
   local origin_version
-  local origin_subject
+  local release_commit
+  local release_subject
+  local candidate
+  local candidate_version
+  local parent
+  local parent_version
 
   release_checkout=$(worktree_for_branch "$release_branch") \
     || die "$release_branch must be checked out in a linked worktree"
@@ -276,16 +282,40 @@
   version=$(<"$release_checkout/VERSION")
   origin_version=$(git show origin/main:VERSION) \
     || die "origin/main does not contain VERSION"
-  origin_subject=$(git log -1 --format=%s origin/main)
 
-  [[ "$origin_version" == "$version" && "$origin_subject" == "Release v$version" ]] \
-    || die "origin/main is not Release v$version (VERSION is $origin_version; subject is '$origin_subject')"
+  [[ "$origin_version" == "$version" ]] \
+    || die "origin/main VERSION is $origin_version, not $version"
 
   git rev-parse --verify --quiet "refs/tags/v$version" >/dev/null \
     && die "tag v$version already exists"
 
-  git tag "v$version" origin/main
-  printf 'release: created local tag v%s on origin/main\n' "$version"
+  release_commit=
+  while IFS= read -r candidate; do
+    candidate_version=$(git show "$candidate:VERSION") \
+      || die "could not read VERSION at $candidate"
+    [[ "$candidate_version" == "$version" ]] || continue
+
+    parent=$(git rev-list --parents -n 1 "$candidate")
+    parent=${parent#"$candidate"}
+    parent=${parent# }
+    if [[ -z "$parent" ]]; then
+      release_commit="$candidate"
+      break
+    fi
+    parent=${parent%% *}
+    parent_version=$(git show "$parent:VERSION" 2>/dev/null || true)
+    [[ "$parent_version" != "$version" ]] || continue
+
+    release_commit="$candidate"
+    break
+  done < <(git log origin/main --format=%H -- VERSION)
+
+  [[ -n "$release_commit" ]] \
+    || die "could not locate release commit that set VERSION to $version on origin/main"
+
+  release_subject=$(git log -1 --format=%s "$release_commit")
+  git tag "v$version" "$release_commit"
+  printf 'release: created local tag v%s on %s (%s)\n' "$version" "$release_commit" "$release_subject"
 }
 
 if [[ $# -eq 0 ]]; then
diff --git a/tests/test-scripts.sh b/tests/test-scripts.sh
index 1e9d962f00d5c78aff867c1380b626b7ddf97e75..a6959c3a957c5897da5baf5060d314dde33249bc
--- a/tests/test-scripts.sh
+++ b/tests/test-scripts.sh
@@ -1903,23 +1903,70 @@
   [ ! -s '$push_log' ]
 "
 
-setup_release_fixture release-tag-after-merge-wrong-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
-check "tag-after-merge refuses when origin/main advanced past the release" bash -c "
+check "tag-after-merge refuses when local tag already exists" bash -c "
+  cd '$REL_WORKTREE'
+  retag_out='$TMP/tag-after-merge-retag.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$retag_out\" 2>&1; then
+    exit 1
+  fi
+  grep -q 'tag v2026.8.10 already exists' \"\$retag_out\"
+"
+
+setup_release_fixture release-tag-after-merge-merge-commit 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags release commit below merge commit and pushes nothing" bash -c "
   set -e
+  : > '$push_log'
   cd '$REL_WORKTREE'
   PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  release_commit=\$(git rev-parse HEAD)
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  printf 'reviewed\n' > '$REL_PRIMARY/review.txt'
+  git -C '$REL_PRIMARY' add review.txt
+  GIT_AUTHOR_DATE='2026-08-16T10:02:00Z' GIT_COMMITTER_DATE='2026-08-16T10:02:00Z' git -C '$REL_PRIMARY' commit -qm 'Review release PR'
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' merge --no-ff -m 'Merge release PR' wt/demo
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$tag_guard_bin:$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$release_commit\" ] &&
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" != \"\$(git rev-parse origin/main)\" ] &&
+  [ ! -s '$push_log' ]
+"
+
+setup_release_fixture release-tag-after-merge-squash 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge tags squash commit with non-release subject" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
+  git -C '$REL_PRIMARY' fetch -q origin main
+  git -C '$REL_PRIMARY' reset -q --hard origin/main
+  cp '$REL_WORKTREE/VERSION' '$REL_PRIMARY/VERSION'
+  cp '$REL_WORKTREE/CHANGELOG.md' '$REL_PRIMARY/CHANGELOG.md'
+  printf 'demo\n' > '$REL_PRIMARY/work/.last-released'
+  git -C '$REL_PRIMARY' add VERSION CHANGELOG.md work/.last-released
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Merge pull request #7 from wt/demo'
+  squash_commit=\$(git -C '$REL_PRIMARY' rev-parse HEAD)
+  git -C '$REL_PRIMARY' push -q origin main
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo
+  [ \"\$(git rev-parse refs/tags/v2026.8.10)\" = \"\$squash_commit\" ]
+"
+
+setup_release_fixture release-tag-after-merge-not-current 2026.8.9 "Code-review verdict: APPROVE" pass fresh
+check "tag-after-merge refuses when origin/main version advanced past the release" bash -c "
+  set -e
+  cd '$REL_WORKTREE'
+  PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh demo
   git push -q origin wt/demo:main
   git -C '$REL_PRIMARY' fetch -q origin main
   git -C '$REL_PRIMARY' reset -q --hard origin/main
-  printf 'next change\n' > '$REL_PRIMARY/after-release.txt'
-  git -C '$REL_PRIMARY' add after-release.txt
-  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Next change'
+  printf '2026.8.11\n' > '$REL_PRIMARY/VERSION'
+  git -C '$REL_PRIMARY' add VERSION
+  GIT_AUTHOR_DATE='2026-08-16T10:03:00Z' GIT_COMMITTER_DATE='2026-08-16T10:03:00Z' git -C '$REL_PRIMARY' commit -qm 'Release v2026.8.11'
   git -C '$REL_PRIMARY' push -q origin main
-  wrong_out='$TMP/tag-after-merge-wrong.out'
-  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$wrong_out\" 2>&1; then
+  not_current_out='$TMP/tag-after-merge-not-current.out'
+  if PATH='$REL_FAKEBIN':\$PATH bash scripts/release.sh tag-after-merge demo >\"\$not_current_out\" 2>&1; then
     exit 1
   fi
-  grep -q 'origin/main is not Release v2026.8.10' \"\$wrong_out\" &&
+  grep -q 'origin/main VERSION is 2026.8.11, not 2026.8.10' \"\$not_current_out\" &&
   ! git rev-parse --verify --quiet refs/tags/v2026.8.10
 "
 

tokens used
51,093
Implemented and committed the scoped change.

Commit: `59d551c Tag release commit after merge by version transition`

Changed:
- [scripts/release.sh](/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit/scripts/release.sh): `tag-after-merge` now keeps the current-version guard, finds the commit that transitioned `VERSION` to the release version on `origin/main`, and tags that SHA instead of `origin/main`’s tip.
- [tests/test-scripts.sh](/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/release-tag-merge-commit/tests/test-scripts.sh): added/updated coverage for ff, merge commit, squash merge, not-current refusal, no-push behavior, and re-tag refusal.

Validation:
- `shellcheck scripts/release.sh tests/test-scripts.sh` passed.
- `git diff --check -- scripts/release.sh tests/test-scripts.sh` passed.
- `bash tests/test-scripts.sh` passed all edited `tag-after-merge` tests, but failed its final repo gate check.
- `bash scripts/gate.sh` did not pass because `pytest -q` segfaults before running repo tests:
  `Fatal Python error: Segmentation fault` in pytest capture/readline import path.

Out of scope: I did not modify gate/pytest/environment files because they are outside the hard footprint. The worktree is clean.
