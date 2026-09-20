# Retro — release-tag-merge-commit (v2026.9.1)

Released 2026-09-20. One code-review round, dual APPROVE at round 1. The fix
dogfooded itself: v2026.9.1's PR was merged as a **merge commit** (the exact shape
that broke v2026.9.0), and the new `tag-after-merge` tagged the release commit
`8506121` automatically instead of refusing — first hands-free tag since the bug.

## The four questions

**What did the gate miss that a reviewer caught?**
Nothing blocking. Both reviewers APPROVED round 1 with zero CRITICAL/HIGH; the
three LOW findings are fail-safe (a false refusal at worst, on git histories
`release.sh` cannot produce, never a mistag). The one materially better idea —
locating the release commit by its **VERSION transition** rather than by matching
the `Release vX` subject, which also unlocked squash-merge support — came from the
`/1-plan` reviewer, i.e. the plan stage working as intended, not a gate gap.
→ **not worth keeping** as a defect lesson.

**What did every check miss?**
`scripts/codex-review.sh` assembles the Codex reviewer's prompt with
`printf '- CRITICAL: …\n'` (and three sibling lines). The leading `-` is parsed as
a `printf` **option**, so all four severity-taxonomy bullets are silently dropped
from the prompt (the `printf: - : invalid option` lines on stderr during
`/3-review`). The Codex reviewer has therefore been running **without its
severity definitions** every round, this unit included. Worse, the gate test
`codex-review prompt includes severity taxonomy` passes anyway — it must match a
non-dash line — so the check gives false comfort. This survived the gate and both
review rounds of *every* prior unit. → **mechanical** (`scripts/codex-review.sh`);
touches `scripts/`, so it is a **/1-plan unit**, not applied here (see Routing).

**What got re-derived that a doc would have prevented?**
The locator's correctness rests on git-history reasoning that the plan-reviewer,
the implementer, and the code-reviewer each re-derived/verified independently:
that `git log origin/main -- VERSION` path-simplification surfaces the release
commit and prunes the enclosing merge (TREESAME to its release-side parent); that
"`VERSION` is written only by `release.sh` ⇒ a VERSION change *is* a release"; and
the deliberate **currency guard** (`origin/main:VERSION == version`) that trades
away automatic back-tagging once a newer release ships. The deferred back-tagging
question and the codex-review fix will both re-open `tag_after_merge`.
→ **contextual** — `knowledge/release-tagging.md` (new, small). *Applied here.*

**What friction repeated from a prior retro?**
- The harness build still does not register `.claude/agents/*.md` as spawnable
  `subagent_type`s; both reviewers ran as fresh read-only `Plan` stand-ins.
  Already a standing PLAN Decision (2026-09-19) — recurred, confirms the
  workaround, no new routing. → **not worth keeping** (already recorded).
- The implementer's sandbox `pytest` segfaulted again; the authoritative gate ran
  clean in the repo env and I trusted the exit code, per the existing followup
  guidance. Known environment artifact. → **not worth keeping** (already covered).
- New this session: `scripts/worktree.sh add` hung on its internal
  `git fetch origin` (no timeout; the `|| true` guard catches a non-zero exit, not
  a stall), blocking `/5-retro` until the process was killed and the worktree
  created directly off the already-fresh `origin/main`. Thin evidence (one
  transient stall), but the guard is real. → folded into the same **/1-plan**
  script-robustness unit as a secondary item.

## Routing

- **mechanical (deferred to /1-plan)** — **`codex-review-prompt-printf-fix`**: guard
  `scripts/codex-review.sh`'s prompt `printf`s against `-`-leading format strings
  (use `printf '%s\n' '- …'` or `printf -- '…'`) so the Codex prompt carries the
  full severity taxonomy, and make a gate test that would actually catch a dropped
  `- CRITICAL` line (match the dash-led text, not a neighbouring line). Secondary
  item in the same unit: bound `worktree.sh add`'s `git fetch origin` so a network
  stall cannot hang the loop. Both touch `scripts/`, so not applied in this retro.
  **Next `/1-plan`: `codex-review-prompt-printf-fix`.**
- **contextual** — `knowledge/release-tagging.md` (new): how `tag-after-merge`
  locates the release commit (VERSION transition + path-simplification/TREESAME +
  first-parent), and the currency-guard / no-auto-back-tagging tradeoff. *Applied
  on this branch.*
- **process** — `PLAN.md`: record `release-tag-merge-commit` v2026.9.1 shipped,
  queue `codex-review-prompt-printf-fix`, and one Decisions line on the currency
  guard tradeoff. *Applied on this branch.*

## Not worth keeping

The three LOW review findings (fail-safe, on histories the tool cannot produce);
the recurring `.claude/agents` spawnability and pytest-sandbox-segfault frictions,
both already recorded and handled.
