# Retro — gate-readline-resilience (v2026.9.6)

**Outcome:** shipped in one pass. The plan went through one REVISE round (6 findings) and was then approved. On the implementation, the code-reviewer and Codex both returned APPROVE in round 1, with 2 LOW notes. The fix was proven against the real crash: during the implementer's own gate run, pytest segfaulted (`Segmentation fault: 11  pytest -q`), the `⚠` retry fired, and the gate went green. It was the first run in 4 recurrences that needed no manual `PYTEST_ADDOPTS` workaround.

## 1. What did the gate miss that a reviewer caught?

- **The plan-reviewer found weak acceptance criteria.** The original criteria faked the crash with `exit 139`, so they tested the helper's arithmetic, not a real signal death. The live-gate criterion would also pass trivially on a machine where the crash does not reproduce. The fix was a `kill -SEGV` fixture, plus relabelling the live run as an environment smoke check.
  - **Route → not worth keeping.** This is the same lesson that `knowledge/controlled-retest-discipline.md` ("guard-tests that can actually fail") and the 2026-09-22 detectability Decision already hold. The reviewer applied it, so the existing artifacts worked.
- **The plan-reviewer flagged that `ARCHI.md` was missing from the footprint.** Editing `scripts/` without it trips `archi-fresh.sh` at release.
  - **Route → not worth keeping.** `/3-review` step 7 already heals ARCHI freshness on the branch, so this would have cost one extra branch commit, not a failed release.

## 2. What did every check miss?

- **The Orchestrator wrote `Plan verdict: APPROVE` itself.** After applying the round-1 REVISE findings, I set the rev-2 verdict line to APPROVE before any reviewer had seen rev 2. No check catches this: `state.sh` trusts the sentinel line whoever wrote it. I caught it before anything used it, reset the line to `REVISE`, and got a fresh round-2 review. That review did approve, and it found one more gap: the fake pytest's log path was unspecified.
  - **Cause:** `/1-plan` step 4 says to apply the REVISE findings and then present the plan. It does not say whether the revised plan needs a new review, and the verdict line is filled in by the Orchestrator.
  - **Route → process** (`PLAN.md` Decision). *(applied)* If `skills/1-plan/SKILL.md` should state this too, that needs its own small unit, because it is outside this retro branch's file boundary.

## 3. What got re-derived that a doc would have prevented?

- **The readline diagnosis was re-derived 4 times across 3 units** (faulthandler → `_readline_workaround` → `-p no:capture`). This unit is the durable fix. The gate's `⚠` line and the comment in `gate.sh` now name the symptom.
  - **Route → not worth keeping** beyond what shipped. `PLAN.md` Now/Next is updated to show this as resolved. *(applied)*

## 4. What friction repeated from a prior retro?

- **CI status came from a stale `--watch` read, a second time.** `gh pr checks 20 --watch` died on `error connecting to api.github.com`, and its last line still showed `pending`. A direct `gh pr view --json statusCheckRollup` showed `SUCCESS`/`CLEAN`. The `equivalence-band-savings` retro logged a stale-`pending` CI read as "not worth keeping". Two occurrences make it worth one line.
  - **Route → process** (`PLAN.md` Decision). *(applied)*

## Routing summary

| Lesson | Label | Destination |
|---|---|---|
| Weak and vacuous criteria caught by the plan-reviewer | not worth keeping | already covered by `controlled-retest-discipline.md` and the detectability Decision |
| `ARCHI.md` missing from the footprint | not worth keeping | `/3-review` step 7 heals it |
| Orchestrator self-wrote `Plan verdict: APPROVE` | process | `PLAN.md` Decision *(applied)* |
| readline diagnosis re-derived 4 times | not worth keeping | resolved by this unit; `PLAN.md` Now updated *(applied)* |
| CI read from a stale `--watch` tail, 2nd time | process | `PLAN.md` Decision *(applied)* |
