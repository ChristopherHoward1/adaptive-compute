# Retro — eval-check-resolution-guard (v2026.10.1)

Released 2026-10-09 (PR #29). The plan took four plan-review rounds. Code review closed in round 1 with dual APPROVE, and the gate passed on the first dispatch.

## Q1 — What did the gate miss that a reviewer caught?

Code review found nothing above LOW. The plan stage caught the real defect. My first draft anchored the guard to `CHECK_ADAPTIVE_B_MAX = 1024`, and I validated it only against **today's** EB boundary, where a `b_max=320` run abstains. The plan-reviewer restored R1's actual boundary from `0401b00` and found the 1024-anchored guard still passes (832 < 1024). R1's real defect was the tuning grid's `b_max`, which the draft guard never read. I had shown the guard can fail on a stand-in configuration, not on the failure it was named for.

- **Route → contextual:** `knowledge/controlled-retest-discipline.md` §4 gets one paragraph: a guard named for a past failure must be shown to fail on that failure's actual configuration, reconstructed from its commit, and must read the setting that failure got wrong. *(applied)*

## Q2 — What did every check miss?

Nothing reached release. The two LOW review notes are cosmetic and within the accepted scope:
- One message covers both "undecided at `b_max`" and "wrong early decision".
- A tie on the largest `b_max` tests only the first candidate.

- **Route → not worth keeping:** these were recorded in the plan's Review section, and a future edit can sharpen the message if a failure ever needs debugging.

## Q3 — What got re-derived that a doc would have prevented?

The round-2 plan-reviewer worked out that a `capsys` test errors under the gate's `-p no:capture` retry. The `no:capture` workaround has a long history (see `gate-readline-resilience`), but its consequence for *test authoring* was not written down anywhere.

- **Route → not worth keeping:** one reviewer round caught it, and the failure would be loud, not silent. The existing tests in `tests/test_determinism.py` already show the `redirect_stderr` pattern.

## Q4 — What friction repeated from a prior retro?

**The loop ran from the linked checkout (`plaice`) again.** This is the second time (after `release-anchor-approve-path` Q2), and it happened despite the 2026-10-09 PLAN decision "harness scripts run from the primary checkout". I read `PLAN.md` while `plaice` was still on a stale, already-merged branch, before switching to `origin/main`, so the decision was never in my context. The effects:
- `worktree.sh add` resolved its relative `worktrees.dir` against the linked root and created the implementation worktree in a second worktrees directory (`orca/.../adaptive-compute-worktrees`).
- `sync-artifacts` refused, so I copied the artifacts by hand twice.
- `codex-review.sh` wrote its artifact into `plaice`.

The release itself was unaffected: gate, reviews, tag and PR were all correct. A process decision that depends on the Orchestrator having read the right `PLAN.md` revision has now failed once.

- **Route → mechanical:** named `/1-plan` unit **`linked-checkout-preflight`**. `worktree.sh add` and `codex-review.sh` should refuse to run, or at least print a loud warning, outside the primary checkout (`git rev-parse --git-dir` ≠ `--git-common-dir`), the same way `sync-artifacts` already does. This applies the decision in code rather than relying on memory. It cannot be applied on a retro branch because it edits `scripts/`.

The implementer sandbox also hit `index.lock` and could not commit in a linked worktree, for the third time. **Not worth keeping:** `/2-implement` step 6 absorbs it, as the previous retro concluded.

## Routing summary

| Lesson | Label | Where |
| --- | --- | --- |
| A guard must fail on the named failure's real configuration | contextual | `knowledge/controlled-retest-discipline.md` §4 (applied) |
| LOW review notes | not worth keeping | plan Review section |
| `capsys` vs `-p no:capture` | not worth keeping | this line only |
| Loop ran from linked checkout despite the decision | mechanical | named `/1-plan` unit `linked-checkout-preflight` |
| Implementer `index.lock` (3rd time) | not worth keeping | absorbed by `/2-implement` step 6 |
