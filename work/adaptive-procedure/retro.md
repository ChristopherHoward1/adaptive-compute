# Retro — adaptive-procedure (v2026.9.3)

Released 2026-09-20. First real scientific result of the project: a genuine
**H1 NEGATIVE** (adaptive resolves every non-boundary case with a zero false-stop
rate, but fails §8's ≥2× savings/Pareto gate). Three `/3-review` rounds to dual
APPROVE. The lessons below are routed one durable place each.

## Q1 — What did the gate miss that a reviewer caught?

**The gate green-lit a scientifically vacuous result.** Round 1 shipped a green gate
(188 shell + pytest, `eval --check` passing) whose headline artifact reported
"H1 NEGATIVE" with false-stop rate 0.0000 everywhere — but the two hard strata were
abstaining ~100% of the time. A false-stop rate of 0 is trivial when the method
almost never decides. The gate's fast `eval --check` verifies determinism,
accounting, and stream independence, but nothing that the adaptive band actually
*resolves* a low-variance decision within a sane budget — so an instrument too loose
to ever stop passes. The R1 CRITICAL traced it to the EB boundary's linear term
(`14·log_term/3n = 0.1215` at n=320) exceeding δ=0.05, with `B_max` mis-set equal to
`B_ref=320`.

Also gate-invisible, caught in R2: the round-1 AUC-kernel optimization silently
dropped reference-path input validation (malformed input → Δ*=0 instead of raising),
and broke reference **bit-identity** (~1e-16 reassociation drift) — the gate's
regression tests asserted *decisions*, which are too coarse to see it.

- **Route → contextual:** `knowledge/anytime-valid-band.md` — add the *abstain-vacuity
  trap* (false-stop is only meaningful conditioned on a low abstain/non-decision
  rate; read the abstain column before the false-stop column) and the *B_max sizing*
  rule (size against the boundary's resolving power, never `= B_ref`). *(applied)*
- **Route → contextual:** `knowledge/bootstrap-seed-and-determinism.md` — reference
  invariance must be asserted at the **delta-array** level (bit-identical), not just
  the decision level. *(applied)*
- **Named /1-plan candidate (mechanical, cannot apply on a retro branch — edits
  `src/`/`scripts/`):** `eval-check-resolution-guard` — extend `eval --check` to
  assert a low-variance member resolves (non-abstain) within a sane budget, so an
  abstain-everything instrument fails the gate one layer earlier instead of only at
  cold review.

## Q2 — What did every check miss?

**The H1 negative's dependence on the chosen instrument was never tested.** Both
reviewers verified the result is *internally* valid (resolves, fair independent-stream
Pareto, zero false stops), but nobody checked whether the negative *survives a tighter
anytime-valid instrument*. The negative rests on adaptive median draws (448 moderate /
768 equivalent) exceeding the whole fixed-B grid — which is a property of the
finite-horizon EB boundary's looseness and `B_max=2048`. A tighter betting CS
(Waudby-Smith–Ramdas) could plausibly resolve at far smaller budgets and flip the
savings verdict. The negative is honest for *this* instrument; it is not yet a
statement about adaptivity in general.

- **Route → process:** one line in `PLAN.md` (Decisions/Risks) recording that the
  v0 H1 negative is instrument-specific, to be re-tested against a betting CS before
  any general "adaptivity does not save compute" claim. *(applied)*

## Q3 — What got re-derived that a doc would have prevented?

Little, this time — the estimand-alignment reasoning (why the mean CS agrees with the
reference on the battery; the rejected tail-prob alternative) was captured in
`knowledge/anytime-valid-band.md`, created *by this unit* exactly as the plan
required, so it did not have to be re-argued in review. The one thing re-derived
independently by orchestrator and reviewer was the EB-boundary-width arithmetic that
proved the abstain-everything artifact — now folded into the same doc under Q1's
contextual add, so the next consumer sizes `B_max` without re-deriving it.

## Q4 — What friction repeated from a prior retro?

- **Local `readline`/pytest-capture segfault** — the implementer's conda Python
  segfaults on native `import readline` under pytest capture, and it worked around it
  every one of the three rounds (`PYTEST_ADDOPTS='-p no:capture'`). My own gate runs
  never hit it, so it is environment-specific, not a repo defect — but it recurred
  enough to cost real cycles.
  - **Named /1-plan candidate (mechanical, cannot apply here — edits `scripts/`):**
    `gate-readline-resilience` — have the gate detect the native-readline segfault and
    self-apply the no-capture workaround (or document it in one place the implementer
    is guaranteed to read). Not applied on the retro branch per the mechanical-file
    boundary.
- **Agent-type stand-in** — the named `plan-reviewer`/`code-reviewer` agent types are
  unregistered in this harness build, so I again stood in fresh read-only `Plan`
  subagents. This is *already* recorded (PLAN decision 2026-09-19); no new routing.
- **Long review cycles / a watchdog stall** — the round-2 `code-reviewer` stalled on a
  600s stream watchdog before emitting a verdict; resuming the same thread recovered it
  with its cold context intact. Worth remembering (resume, don't respawn — respawning
  would have burned a fresh review and the anchoring rule), but not worth a durable
  artifact. **Not worth keeping** beyond this line.

## Routing summary

| Lesson | Label | Where |
| --- | --- | --- |
| Abstain-vacuity trap + B_max sizing | contextual | `knowledge/anytime-valid-band.md` (applied) |
| Reference invariance at array level | contextual | `knowledge/bootstrap-seed-and-determinism.md` (applied) |
| H1 negative is instrument-specific | process | `PLAN.md` (applied) |
| `eval --check` resolution guard | mechanical | named `/1-plan` unit `eval-check-resolution-guard` |
| Gate readline resilience | mechanical | named `/1-plan` unit `gate-readline-resilience` |
| Review watchdog stall → resume not respawn | not worth keeping | this line only |
