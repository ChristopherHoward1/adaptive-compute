# Retro — codex-review-prompt-printf-fix (v2026.9.2)

Released 2026-09-20. One review round, dual APPROVE at round 1, zero findings.
This unit was itself the `mechanical` routing from `release-tag-merge-commit`'s
retro: it fixed `scripts/codex-review.sh` silently dropping its four
CRITICAL/HIGH/MEDIUM/LOW severity *definitions* from the Codex reviewer prompt
(leading `-` parsed as a `printf` option), replaced the false-comfort source-grep
gate test with a rendered-prompt assertion, and bounded the loop's unbounded
`git fetch origin` in both `worktree.sh` and `codex-review.sh`.

A fitting confirmation surfaced during this unit's own `/3-review`: because
`/3-review` runs `scripts/codex-review.sh` from the **primary checkout (on `main`,
still the buggy version)**, the review that approved the taxonomy fix was itself
conducted with the four severity definitions dropped — the exact
`printf: - : invalid option` lines printed to stderr on the way. The fix only
takes effect once merged; every prior review round genuinely ran without the
definitions, as diagnosed. Curiosity, not a defect.

## The four questions

**What did the gate miss that a reviewer caught?**
Nothing. Both reviewers APPROVED round 1 with zero findings, and both ran the
gate themselves (188/188). The gate now *catches* the very bug this unit
existed to fix (the new rendered-prompt assertion goes red on a re-drop; the
code-reviewer confirmed it by reproducing the drop). → **not worth keeping.**

**What did every check miss?**
Nothing live. Two accepted, already-documented limitations, neither a defect:
the bounded-fetch fallback is genuinely unbounded on a bare macOS box with
neither `timeout` nor `gtimeout` (recorded in the plan and ARCHI), and the
review-runs-the-old-prompt-until-merge property above is inherent to reviewing a
fix to the reviewer's own tooling. → **not worth keeping.**

**What got re-derived that a doc would have prevented?**
The leading-dash argument trap — `printf '- CRITICAL: …'` treats `- CRITICAL:`
as an option, and the *fix's own* acceptance-criterion grep (`grep -F '- CRITICAL:'`)
would have tripped the identical trap had the plan-reviewer not caught it. Both
the bug and a near-repeat in the test were the same gotcha, and it had gone
undetected project-wide for the codebase's whole history. The gate test now
guards the one call site in `codex-review.sh`, but the *rule* (use `printf '%s\n'`
/ `printf --`; use `grep -Fq --`) generalizes to every script here that builds
text from user- or data-derived leading-dash tokens. No doc captured it.
→ **contextual** — new `knowledge/shell-argument-safety.md` (small). *Applied here.*

**What friction repeated from a prior retro?**
- The implementer's sandbox `pytest` segfaulted again before repo tests ran; the
  authoritative gate ran clean in the repo env and I trusted the exit code, per
  standing guidance. → **not worth keeping** (already recorded, already handled).
- `.claude/agents/*.md` still aren't spawnable `subagent_type`s; both reviewers
  ran as fresh read-only `Plan` stand-ins. Standing PLAN decision (2026-09-19).
  → **not worth keeping** (already recorded).
- *Resolved, not repeated:* last retro's new friction — `worktree.sh add`'s
  `git fetch origin` hanging on a network stall — is exactly what this unit
  bounded (`WORKTREE_FETCH_TIMEOUT`), in both `worktree.sh` and `codex-review.sh`.
  Recorded as shipped in PLAN, no new routing.

## Routing

- **contextual** — `knowledge/shell-argument-safety.md` (new): the leading-dash
  trap for `printf` and `grep`, the `%s\n` / `--` / `grep -Fq --` guards, and the
  rule that a check must assert *rendered output*, not the source line that
  produces it. *Applied on this branch.*
- **process** — `PLAN.md`: record `codex-review-prompt-printf-fix` v2026.9.2
  shipped and clear it from In-progress. *Applied on this branch.*

## Not worth keeping

Clean dual-APPROVE gate/review split (none); the two accepted documented
limitations (bare-macOS unbounded fetch, review-runs-old-prompt); the recurring
pytest-sandbox-segfault and `.claude/agents` non-spawnability frictions, both
already recorded and handled.
