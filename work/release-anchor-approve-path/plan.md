# Release on the anchor's APPROVE with a recorded Owner override of Codex

**Slug:** release-anchor-approve-path · **Date:** 2026-10-08 · **Status:** approved

## Goal

The reviewer-calibration norm (PLAN 2026-09-19) says: when the two `/3-review` reviewers split, the integration `code-reviewer` is the calibration anchor. If Codex keeps re-flagging a non-live item that the anchor has cleared, ship on the anchor's APPROVE and write the item to `deferrals.md`. But `scripts/release.sh::check_verdict` (and `scripts/state.sh`) hard-require the exact line `Codex-review verdict: APPROVE`. So ship-on-anchor cannot pass the versioned release. In `betting-cs-retest` this forced rounds 3–5 purely to get Codex to approve (PLAN 2026-09-22; `work/betting-cs-retest/retro.md` Q4). Done looks like this: `release.sh` and `state.sh` accept a second, narrowly gated close-out (anchor APPROVE plus an Owner-authorized Codex override), and `/3-review` documents when it may be recorded. The dual-APPROVE path stays unchanged.

## Approach

Add a second accepted shape for the Codex sentinel. The plan must then carry exactly these lines, each at column 0. They are shown indented here on purpose, so that this plan does not match its own sentinels:

```
    Code-review verdict: APPROVE
    Codex-review verdict: OVERRIDDEN
    Codex override: <non-empty reason, naming the Owner's authorization>
```

**Sentinel matching.** Both scripts match the whole plan file, not just its Review section. The two verdict lines stay exact whole-line matches (`grep -x`, as today). A `Codex override:` line is a line matching `^Codex override:` at column 0. Indented lines, and prose that mentions the token inside backticks, never count, whether toward "exactly one" or toward detection.

**`release.sh`** — `check_verdict` becomes:

1. `Code-review verdict: APPROVE` is required on both paths (unchanged; the anchor is never optional).
2. **Standard path:** `Codex-review verdict: APPROVE` is present. The path behaves exactly as today.
3. **Override path:** `Codex-review verdict: OVERRIDDEN` is present, and all of the following hold, or the script dies naming the failed condition:
   - The plan has exactly one `Codex override:` line, and its reason after the colon is non-empty once whitespace is trimmed. More than one `Codex override:` line → die (ambiguous record).
   - `work/<slug>/codex-review.md` exists, and its **last** `Codex verdict:` line is `REQUEST CHANGES`. Parse it the same way `codex-review.sh` does: last `^[[:space:]]*Codex verdict:` line, whitespace-trimmed. This proves only that **the most recent Codex run** blocked. It does not prove that run reviewed the exact diff being released, because `codex-review.md` carries no SHA. It does stop `OVERRIDDEN` from being used when Codex never ran or last approved. That the run is from the current round, on the current diff, is a `/3-review` precondition (below), not a mechanical check; making it mechanical would mean changing `codex-review.sh`, which is out of footprint.
   - `work/<slug>/deferrals.md` exists and is non-empty. This proves only that a deferral ledger exists. It does not prove the cleared items are in it, which is a `/3-review` precondition (below).
4. Both `Codex-review verdict: APPROVE` and `Codex-review verdict: OVERRIDDEN` present → die (contradictory record). A column-0 `Codex override:` line on the standard path (APPROVE present, OVERRIDDEN absent) is **ignored**: no refusal, no changelog bullet, and the changelog stays byte-identical.
5. Neither present → die. The message must still contain the literal `Codex-review verdict: APPROVE` so the existing test at `tests/test-scripts.sh` ("release refuses without codex-review approval") keeps passing; it may also mention the override shape.

On the override path, `prepend_changelog` writes one more bullet, `- Codex override: <reason>` (trimmed reason), directly after the `Confirm-delta` bullet and before the section's single trailing blank line, so the override is auditable in `CHANGELOG.md`. The standard path's changelog output is byte-identical to today's.

`codex-review.md` and `deferrals.md` reach the release worktree through `scripts/worktree.sh sync-artifacts <slug>`. `/4-release` step 1 already runs that first, so `release.sh` checks them at `work/<slug>/…` relative to the release checkout. No new plumbing.

**`state.sh`** — `review=approve` when `Code-review verdict: APPROVE` is present, `Codex-review verdict: APPROVE` and `Codex-review verdict: OVERRIDDEN` are **not both** present, and either (a) `Codex-review verdict: APPROVE` is present, or (b) `Codex-review verdict: OVERRIDDEN` is present with exactly one `Codex override:` line whose trimmed reason is non-empty. These plan-text rules are the same ones `release.sh` applies, so the two scripts never disagree on the same plan text. `state.sh` stays a plan-text-only check (it reads the plan from the branch). The artifact checks (codex-review.md, deferrals.md) live only in `release.sh`, which is the authority.

**`skills/3-review/SKILL.md`** — document the override close-out:
- **Deliberately stricter than the 2026-09-19 norm** (Owner-confirmed 2026-10-08). The norm ships on the anchor without the Owner; the override needs in-session Owner authorization because it bypasses an independent reviewer and no script can verify the authorization. `/5-retro` records this as a PLAN decision.
- It may be recorded only when all five hold: the anchor `code-reviewer` returned APPROVE in the current round; Codex returned REQUEST CHANGES in the current round, on the current diff (no writer change since that run); every Codex CRITICAL/HIGH is a finding the anchor explicitly cleared as non-live; each such finding is written to `deferrals.md`; and **the Owner authorized the override in-session**.
- **Step 4** gains a carve-out: CRITICAL/HIGH findings block regardless of round, *except* Codex CRITICAL/HIGH findings the anchor explicitly cleared as non-live. Those may close through the Owner-authorized override (step 6). **Step 3**'s "exit 1 → followup flow" gets a cross-reference to that carve-out.
- **Step 5** gains the override as a second way to end the loop ("until both approve, the Owner authorizes an override, or the counter reaches 3"; the literal `counter reaches 3` stays, because a test greps for it).
- **Step 7** (ARCHI-freshness heal) runs after *either* close-out is recorded, not only "after both APPROVE sentinels". Otherwise `release.sh`'s `check_archi_fresh` blocks the override path.
- **Step 8** reports the anchor verdict plus either the Codex APPROVE or the override and its reason.
- The Orchestrator never records `OVERRIDDEN` on its own judgement. As with the plan-verdict rule (PLAN 2026-09-23), the scripts trust the sentinel whoever wrote it.
- Write the cleared findings to `deferrals.md` before recording the override.
- **Step 6** gains the override form: write `Code-review verdict: APPROVE`, `Codex-review verdict: OVERRIDDEN`, and the `Codex override:` line (the Owner's authorization as the reason) in the same single plan commit, then `sync-artifacts`. The **Rules** line lists `Codex-review verdict: APPROVE|REQUEST CHANGES|OVERRIDDEN`.

Alternatives considered:
- *Make Codex advisory (drop its sentinel).* Rejected: it throws away the second reviewer on every unit, not just the split ones.
- *Free-form bypass flag on `release.sh` (`--skip-codex`).* Rejected: it leaves no record in the plan, and `state.sh` would still report `review: pending`.
- *Also cover the spec-only single-review close-out (PLAN 2026-09-19).* Out of scope. That case has no Codex run at all, while this path requires Codex to have run and blocked. It stays a separate candidate if spec-only units recur.

## Footprint

Files to modify:
- `scripts/release.sh` — `check_verdict` (now needs the slug or paths) and `prepend_changelog` (optional override bullet).
- `scripts/state.sh` — the `review=` predicate.
- `tests/test-scripts.sh` — new release and state fixtures/cases. `setup_release_fixture` may grow an optional parameter or a post-setup hook that writes `codex-review.md` / `deferrals.md` and **commits them on `wt/demo`**, as `sync-artifacts` does in production. Otherwise `check_clean_worktree` (which runs right after `check_verdict`) dies with "has untracked files" on the happy path, while the refusal cases still pass and hide the gap. `work/` is outside `archi-fresh.sh`'s source paths, so the commit does not make ARCHI stale.
- `skills/3-review/SKILL.md` — the override close-out rules (steps 3–8 and Rules).

Expected outside the implementer's footprint: `ARCHI.md` will go stale from the `scripts/` and `skills/` edits. `/3-review` step 7 heals it on the branch, so an `ARCHI.md` change in the final diff is expected, not creep.

Files NOT to touch:
- `scripts/codex-review.sh` — its exit-code contract and artifact format are inputs here, not changes.
- `PLAN.md`, `CHANGELOG.md`, `VERSION` — `PLAN.md` decisions are updated at `/5-retro`; the other two are written only by `release.sh`.
- `.claude/agents/code-reviewer.md` — the anchor's own calibration contract is unchanged.

## Acceptance criteria

Each criterion below is a new or existing named check in `tests/test-scripts.sh`, run by the gate.

- [ ] **Override happy path:** the plan has Code APPROVE + `Codex-review verdict: OVERRIDDEN` + `Codex override: Owner authorized — anchor cleared D-x`; the worktree has a `codex-review.md` whose last verdict line is `Codex verdict: REQUEST CHANGES` and a non-empty `deferrals.md`. Then `release.sh demo` exits 0 and commits `Release v<next>`, and `CHANGELOG.md` contains the exact line `- Codex override: Owner authorized — anchor cleared D-x`.
- [ ] **Override changelog format:** the override and standard-path changelog cases seed `CHANGELOG.md` with a prior `## [x] - date` section, so the section boundary and the `sed -n '/^## /,$p'` concatenation path are both exercised. In the override case, the override bullet directly follows the `- Confirm-delta:` bullet and is followed by exactly one blank line, then the prior `## ` section.
- [ ] **Standard path unchanged:** a dual-APPROVE release's new `CHANGELOG.md` section matches exactly `## [<v>] - <date>`, blank line, `- Demo release note.`, `- Confirm-delta: none`, blank line then the prior `## ` section (so no `Codex override:` line and no extra or missing blank line). All existing release and state checks pass unmodified, including "release refuses without codex-review approval" with its `Codex-review verdict: APPROVE` message match.
- [ ] Override refused (exit 1, stderr names `Codex override`) when the `Codex override:` line is missing, when its reason is empty or whitespace-only, and when there are two `Codex override:` lines.
- [ ] Override refused (exit 1, stderr names `codex-review.md`) when `codex-review.md` is absent, and when its last `Codex verdict:` line is `APPROVE`.
- [ ] Override refused (exit 1, stderr names `deferrals.md`) when `deferrals.md` is absent, and when it is empty.
- [ ] Override refused without `Code-review verdict: APPROVE` (the anchor is mandatory on this path).
- [ ] Refused (exit 1) when both `Codex-review verdict: APPROVE` and `Codex-review verdict: OVERRIDDEN` are present.
- [ ] **Stray override line ignored:** a dual-APPROVE plan that also has a column-0 `Codex override: x` line releases (exit 0), and its new changelog section matches the standard-path exact form (no override bullet).
- [ ] **Check-ordering pin:** at least one override-refusal case asserts that `VERSION`, `CHANGELOG.md`, and `HEAD` are unchanged. This holds today because `check_verdict` runs first; the case catches a future reordering.
- [ ] **Indented lines don't count:** with Code APPROVE, a column-0 `Codex-review verdict: OVERRIDDEN`, and the artifacts present:
  - (a) the only `Codex override:` line is indented → `release.sh` exits 1 with stderr naming `Codex override`, and `state.sh` gives `review: pending`;
  - (b) one column-0 `Codex override:` line plus one indented one → it counts as exactly one: `release.sh` exits 0 (not a duplicate refusal), and `state.sh` gives `review: approve`.
- [ ] `state.sh`: an override fixture (Plan APPROVE + Code APPROVE + OVERRIDDEN + non-empty `Codex override:` + handoff) yields `review: approve`, `stage: release`, `next_action: /4-release`. `review: pending` for each of: `OVERRIDDEN` without a `Codex override:` line; `OVERRIDDEN` with a whitespace-only reason; both `Codex-review verdict: APPROVE` and `OVERRIDDEN` present.
- [ ] `skills/3-review/SKILL.md` names all five preconditions, including the current-round/current-diff Codex run, the findings written to `deferrals.md`, and explicit in-session Owner authorization, and states that the Orchestrator never records `OVERRIDDEN` on its own judgement (diff inspection).
- [ ] `skills/3-review/SKILL.md` step 4 carves out anchor-cleared Codex CRITICAL/HIGH findings for the override, and step 3 cross-references it; step 5 names the Owner-authorized override as a way to end the loop and keeps the literal `counter reaches 3`; step 6 writes `Codex-review verdict: OVERRIDDEN` plus the `Codex override:` line in the same single plan commit; step 7 runs after either close-out; step 8 reports either form; the Rules line lists `APPROVE|REQUEST CHANGES|OVERRIDDEN` (diff inspection).
- [ ] `bash scripts/gate.sh` exits 0 (shellcheck clean).

## Release

Release note: `release.sh` and `state.sh` accept an anchor-APPROVE close-out with an Owner-authorized, artifact-checked Codex override, so the reviewer-calibration norm no longer conflicts with the release gate.

## Verification

- `bash tests/test-scripts.sh` (also run by the gate through `gate.d/test-scripts.sh`).

## Review

**Round 1 (fresh plan-reviewer): REVISE.** It confirmed the codebase claims: `check_verdict` runs before any write, `sync-artifacts` delivers `codex-review.md`/`deferrals.md` to the worktree, and the verdict parsing matches `codex-review.sh`. All six findings were applied, with no disagreements:
1. Skill steps 5, 7 and 8 also needed to change, or the override has no exit from the loop and the ARCHI heal never runs. Added, with a criterion.
2. `state.sh`/`release.sh` disagreed on plans with both lines and on whitespace-only reasons. Unified, with two state cases.
3. The `codex-review.md` check was overclaimed (no SHA). Reworded to what is checked; current-round/current-diff moved to a skill precondition.
4. Standard-path byte-identity was untested. Added an exact section match and a blank-line check for the override bullet.
5. Duplicate `Codex override:` lines are now rejected, with a test.
6. Noted the expected step-7 `ARCHI.md` edit.

**Round 2 (fresh plan-reviewer): REVISE.** It confirmed all six round-1 fixes landed. Three new findings, all applied, no disagreements:
1. (Blocking) The plan's own example block was column-0 and would have matched the new sentinels: `state.sh` would report approve before any review, and a later real Codex APPROVE would trip the both-lines refusal. Fixed by indenting the example, specifying column-0 `^Codex override:` matching, and adding an indented-lines-don't-count criterion.
2. The happy-path fixture must commit the artifacts on `wt/demo`, or `check_clean_worktree` fails. Added to the footprint note.
3. The no-write-on-refusal criterion is relabeled as a check-ordering pin.

**Round 3 (fresh plan-reviewer): APPROVE.** It confirmed all nine prior fixes and the self-match safety (the only column-0 sentinel is the plan verdict line). Non-blocking findings, not yet applied:
1. Requiring in-session Owner authorization for every override is stricter than the 2026-09-19 norm (ship on the anchor, Owner only for design splits). It matches the 2026-09-22 interim wording. → Owner decision.
2. "`deferrals.md` non-empty" proves a ledger exists, not that the cleared items are in it. Reword like the `codex-review.md` caveat.
3. Skill step 6 and the Rules line have no acceptance criterion; without them the override can't be recorded through the documented flow.
4. A column-0 `Codex override:` line on the standard (dual-APPROVE) path is unspecified: ignore it or reject it.
5. Optional simplification: drop both artifact checks. A tooling failure in `codex-review.sh` (exit ≥2) leaves the previous artifact in place, so the check can pass on a stale REQUEST CHANGES.
6. LOW: the fixture can commit the artifacts before the `source` commit instead of adding a post-setup hook.

**Revision 4 (Owner-arbitrated, 2026-10-08).** The Owner chose to keep in-session Owner authorization (finding 1), now stated as deliberate in the Approach. Findings 2–4 applied: the `deferrals.md` caveat reworded and "findings written to `deferrals.md`" added as a skill precondition; a step-6/Rules criterion added; stray standard-path override lines are ignored, with a criterion. Finding 5 declined: the `codex-review.md` check is the only thing that blocks an override when Codex never ran. Finding 6 left to the implementer (the footprint note allows either fixture approach).

**Round 4 (fresh plan-reviewer on rev 4): REVISE.** It confirmed the revision-4 changes are coherent and self-match safe. Three findings, all applied in revision 5, no disagreements:
1. The indented-lines test couldn't fail, because an indented `OVERRIDDEN` already misses `grep -x`. Replaced with column-0-`OVERRIDDEN` cases: (a) only an indented override line → refuse; (b) column-0 plus indented → exactly one → release.
2. Skill steps 3–4 still said Codex CRITICAL/HIGH always block, contradicting the override. Added a step-4 carve-out and a step-3 cross-reference, widened the footprint to steps 3–8, and extended the criterion.
3. The changelog boundary criterion referenced a nonexistent next section. The fixtures now seed a prior `## ` section.

**Round 5 (fresh plan-reviewer on rev 5): APPROVE.** It confirmed each criterion can fail under a plausible wrong implementation, and that the plan is self-match safe. Three LOW test-strengthening notes, carried into the implementer handoff rather than a plan revision:
1. The `codex-review.md` refusal fixture has `Codex verdict: REQUEST CHANGES` earlier and `Codex verdict: APPROVE` last; the happy-path fixture's last verdict line is indented. This pins last-line parsing and `^[[:space:]]*` handling.
2. Put trailing whitespace on the happy-path `Codex override:` reason so trailing trimming is tested.
3. Indented case (b) also asserts `CHANGELOG.md` has exactly one `- Codex override:` line.

Plan verdict: APPROVE
