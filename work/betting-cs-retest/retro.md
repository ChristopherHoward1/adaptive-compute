# Retro — betting-cs-retest (v2026.9.4)

Released 2026-09-22. Second scientific result: the WSR betting confidence sequence
**narrows but does not reverse** the v0 H1 negative — betting holds the zero-false-stop
guarantee and cuts median draws 2–5× (easy 128→64, moderate 384→128, equivalent
768→192), flipping the easy and moderate strata to ≥2× savings, but the **equivalent
stratum** still fails §8 (small fixed-B budgets resolve equivalence and dominate). So
"adaptivity doesn't beat fixed-B on compute" now rests on the equivalence-band case
alone. Cost: **5 review rounds** to dual-APPROVE (the normal cap is 3). The lessons
below are routed one durable place each.

## Q1 — What did the gate miss that a reviewer caught?

**(a) The A/B's EB baseline was silently not the released v0.** Round-1 shipped a green
gate whose EB arm had re-tuned to `B_max=1024` (the unit set a global `DEFAULT_BATCH=64`
and narrowed the EB candidate set), so the comparison's baseline was not the v0
instrument it claimed to re-test, and `eval --run` would have overwritten the released
`work/adaptive-procedure/results.*`. The gate green-lights any internally-consistent
run; it cannot know the EB arm must *reproduce a specific prior release*.

**(b) Two validity tests passed the gate while asserting tautologies.** The
"predictability" and "drop-in stream equivalence" tests each compared a value to
itself (both operands sliced to the same prefix / two identically-constructed fresh
streams). They passed pytest but guarded nothing. The gate runs tests; it cannot tell a
test that *can fail* from one that cannot.

- **Route → contextual:** new `knowledge/controlled-retest-discipline.md` — how to build
  a controlled A/B re-test: never route the experiment through the released baseline's
  code path; give the new arm its own parameterized entry point; hold the shared variable
  constant and **enforce it in code**, not by lucky tuning selection; and a guard-test
  must be able to fail (perturb/reconstruct, never self-compare). *(applied)*

## Q2 — What did every check miss?

**The architectural tension that caused the review to oscillate.** A single shared EB
tuning path served two conflicting masters: `eval --run` must reproduce v0 (needs v0's
candidate set, which includes `b=32`), while `eval --compare`'s EB arm must be pinned to
`b=64` for the controlled A/B. No check — gate or reviewer — flagged this up front; it
surfaced only as Codex **contradicting itself across rounds** (R3 demanded the v0 set be
kept; R4 objected to `b=32` being in it). The fix was to *decouple* the two entry points
(an optional `candidates` override), which no round proposed until round 5. Had the plan
specified separate entry points from the start, rounds 3–5 would not have happened.

- **Route → contextual:** folded into the same `knowledge/controlled-retest-discipline.md`
  (decouple the released default path from the experiment path — the load-bearing rule).
  *(applied)*

## Q3 — What got re-derived that a doc would have prevented?

Little. The WSR construction and its anytime-validity were re-verified cold every round,
but that is the reviewers' job and the math was already captured in
`knowledge/anytime-valid-band.md` (extended by this unit with the betting section), so it
was confirmed, not re-argued from scratch. No new routing.

## Q4 — What friction repeated from a prior retro?

- **The release gate (`release.sh` two-APPROVE precondition) structurally conflicts with
  the reviewer-calibration norm.** The norm (PLAN 2026-09-19) says: when Codex re-flags a
  non-live item the integration anchor has cleared, ship on the anchor's APPROVE and
  defer the item — "do not churn the implementer round-after-round on non-live findings."
  But `release.sh` hard-requires an exact `Codex-review verdict: APPROVE` line, so
  ship-on-anchor **cannot go through the versioned release**. This forced fix rounds
  purely to obtain a Codex APPROVE for the script's sake, directly against the norm. The
  Owner had to arbitrate twice. This is new (first TRIP release where Codex would not
  converge) and load-bearing.
  - **Route → process** (PLAN Decisions) + **named `/1-plan` candidate
    `release-anchor-approve-path`** (mechanical, edits `scripts/release.sh` → cannot apply
    on this retro branch): teach `release.sh` a close-out that accepts the integration
    anchor's APPROVE plus a recorded Owner override when Codex is blocked on
    anchor-cleared non-live findings, so the calibration norm and the release gate stop
    contradicting each other. *(candidate named; PLAN decision applied)*
- **The local `readline`/pytest-capture segfault recurred — third unit running.** The
  implementer again worked around it every round (`PYTEST_ADDOPTS='-p no:capture'` /
  a `PYTHONPATH` no-readline shim). My own gate runs never hit it. Already a named
  candidate; this recurrence raises its priority.
  - **Route → process:** one line in `PLAN.md` bumping `gate-readline-resilience`
    priority (it has now cost cycles across `adaptive-procedure` and `betting-cs-retest`).
    *(applied)*

- **Operational (not worth keeping):** I twice mis-read `codex-review.sh`'s exit code
  because I appended `; echo "…$?"` in a compound command whose *wrapper* reported exit 0
  while the script itself exited 1. Capture the script's own exit directly. One line here;
  no durable artifact.

## Routing summary

| Lesson | Label | Where |
| --- | --- | --- |
| Controlled-retest discipline (decouple baseline path; enforce shared var in code; guard-tests must be able to fail) | contextual | `knowledge/controlled-retest-discipline.md` (applied) |
| Architectural tension = single shared tuning path serving two masters | contextual | folded into the same doc (applied) |
| release.sh two-APPROVE vs ship-on-anchor calibration norm | process + mechanical candidate | `PLAN.md` decision (applied) + `/1-plan` `release-anchor-approve-path` |
| readline segfault recurred (3rd unit) | process | `PLAN.md` — bump `gate-readline-resilience` priority (applied) |
| codex-review.sh exit-code mis-read (compound `echo`) | not worth keeping | this line only |
