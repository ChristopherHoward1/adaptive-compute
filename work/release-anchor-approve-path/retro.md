# Retro — release-anchor-approve-path (v2026.10.0)

Released 2026-10-09. `release.sh` and `state.sh` now accept a second way to close out review: the anchor's APPROVE plus an Owner-authorized, artifact-checked Codex override. That removes the conflict between the reviewer-calibration norm and the release gate that cost `betting-cs-retest` rounds 3–5.

Cost:
- **Planning:** five plan-review rounds, plus one Owner arbitration on whether an override needs the Owner.
- **Implementation:** one dispatch with a green gate (245/245).
- **Review:** one review round with a dual APPROVE and three LOWs.

Almost all of the work was in planning, and implementation went through cleanly.

## Q1 — What did the gate miss that a reviewer caught?

Nothing at implementation; both reviewers approved in round 1 with LOWs only. The catches came at plan stage. The most important one: **draft 1 would have matched its own sentinels.** Its example block showed the new override lines at column 0, and both scripts `grep` the whole plan file. So `state.sh` would have reported this unit approved before any review. A later real Codex APPROVE would then have tripped the contradiction refusal, and the unit could not have released. No test can see this, because the hazard is in the plan's own text. Before this unit no plan quoted a sentinel at column 0 outside its Review section (checked across all `work/*/plan.md`), so the risk had been latent, not live.

- **Route → contextual:** new `knowledge/review-sentinels.md`. It covers the sentinel contract (whole-file, column-0 matching), the self-match hazard, and the indent rule plus a one-line `grep` check. *(applied)*

## Q2 — What did every check miss?

**The session started in a linked checkout (`plaice`), not the primary checkout.** `sync-artifacts` refuses to run outside the primary checkout. `codex-review.sh` writes into whichever checkout runs it. `release.sh` needs `main` checked out in the primary checkout. Nothing flags this when a session starts, so `/2-implement` stalled at step 1 until the Owner was asked. The Owner chose to run the loop from the primary checkout. The primary checkout also had to be fast-forwarded first (it was two merges behind `origin/main`).

- **Route → process:** a PLAN decision that harness scripts run from the primary checkout even when the session starts in a linked one. *(applied)*

## Q3 — What got re-derived that a doc would have prevented?

The plan reviewers had to work out the "tests must be able to fail" property again. Round 4 found that the indented-lines test could not fail, because an indented `OVERRIDDEN` already misses `grep -x`. That rule is in `knowledge/controlled-retest-discipline.md`, but it is framed for experiment re-tests.

- **Route → not worth keeping:** a fresh plan-reviewer found it in one round, which is the reviewer's job working as designed. A general "tests must fail" doc would be bigger than the instance warrants.

## Q4 — What friction repeated from a prior retro?

- **The `release.sh` / calibration-norm conflict (`betting-cs-retest` Q4)** is resolved by this unit. Under that unit's ship-on-anchor norm, overriding Codex needed no Owner. The Owner chose to require in-session Owner authorization for every override instead, which is deliberately stricter: an override bypasses an independent reviewer, and no script can verify the authorization.
  - **Route → process:** mark the 2026-09-22 decision resolved, and add a decision recording the Owner-tightened norm. *(applied)*
- **The implementer's sandbox cannot commit in a linked worktree.** The error was `index.lock` permission denied, because the git dir lives under the primary `.git/worktrees/`. This is the second time; it happened before in `betting-cs-retest`.
  - **Route → not worth keeping:** `/2-implement` step 6 ("commit in the worktree if the implementer didn't") absorbs it at zero cost. The gate result and the diff are unaffected.
