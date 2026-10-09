# Review sentinels — how `state.sh` and `release.sh` read a plan

Load this doc only when a unit edits sentinel handling (`scripts/state.sh`, `scripts/release.sh::check_verdict`, the `/3-review` recording steps) or writes a plan that quotes sentinel lines. Rationale: `work/release-anchor-approve-path/plan.md` (v2026.10.0).

## The contract

- Both scripts match against **the whole `work/<slug>/plan.md`**, not only its `## Review` section. `state.sh` reads the plan from the `wt/<slug>` branch when that branch exists.
- The verdict lines are whole-line matches (`grep -x`), so each must sit at column 0 with no trailing text:
  - `Plan verdict: APPROVE`
  - `Code-review verdict: APPROVE`
  - `Codex-review verdict: APPROVE`, or `Codex-review verdict: OVERRIDDEN`
- `Codex override: <reason>` counts only at column 0 (`^Codex override:`). Exactly one is allowed, and its reason must be non-empty after trimming. On the standard (APPROVE) path a stray override line is ignored.
- On the override path `release.sh` also checks two artifacts: the last `Codex verdict:` in `codex-review.md` must be `REQUEST CHANGES`, and `deferrals.md` must be non-empty. Neither check can prove the Codex run reviewed the released diff, because `codex-review.md` has no SHA. That, and in-session Owner authorization, are `/3-review` preconditions, not mechanical checks.
- The scripts trust a sentinel whoever wrote it (PLAN 2026-09-23). A sentinel line is a record, never an example.

## The hazard: a plan can match its own sentinels

Any column-0 line anywhere in a plan that is shaped like a sentinel counts as one. That includes example blocks inside a fenced code block, because fences don't stop `grep`. Draft 1 of `release-anchor-approve-path` showed the override shape as a column-0 example block. Once implemented, `state.sh` would have reported `review: approve` before any review ran. Later, the real `Codex-review verdict: APPROVE` would have tripped the APPROVE-plus-OVERRIDDEN contradiction refusal, so the unit could not have released. The plan review caught this in round 2.

**Rule:** when a plan quotes a sentinel, indent it (4 spaces) or put it in inline backticks inside prose. Before recording a plan verdict, check:

    grep -nE '^(Plan verdict|Code-review verdict|Codex-review verdict|Codex override:)' work/<slug>/plan.md

It should list only the real records.
