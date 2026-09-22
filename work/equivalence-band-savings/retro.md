# Retro — equivalence-band-savings (v2026.9.5)

Released 2026-09-22. Third scientific result and the one that **closes** the equivalence-band
question: inside `[−δ,δ]` fixed-B **structurally** beats both adaptive instruments, because
the fixed-B percentile interval is a *fixed-width functional* (resolves equivalence at
`B*≤~B_ref`) while any anytime-valid CS must shrink Monte-Carlo error below δ (EB median 1344,
`w_ad(320)=0.126>δ`, dominated by `{32,64,128,320}`; betting median 288, dominated by `{32,64,128}`,
`B*=32`). Savings are a *directional*-decision story, not an equivalence one
(`knowledge/equivalence-band-savings.md`, applied by the unit).

Unusually expensive path: **three plan revisions + two Owner arbitrations** before a green
implementation. The loop worked — cold plan-review caught both mis-framings — but the first
was caught only after a full implement+review cycle (rev-1). The lessons route one place each.

## Q1 — What did the gate miss that a reviewer caught?

The gate green-lit **rev-1**: a probe that scored adaptive against a fixed-B grid capped at
`B_ref=320`, which structurally forces "fixed-B wins" (adaptive's in-band median exceeds the
grid ceiling, so `pareto_verdict`'s `adaptive_median < b` can never hold), on a fixture whose
"difficulty heterogeneity" was `|Δ|` position spread with ~no required-draw spread (deep 32.0
vs shallow 34.7). The integration anchor caught it (HIGH): the measurement could not *express*
the effect the experiment existed to detect. The gate validates internal consistency, never
whether a comparison can express its hypothesis.

- **Route → process** (PLAN Decisions): a `/1-plan` unit that proposes an experiment to
  *detect* an effect must state, and its plan-reviewer must check, the **detectability
  precondition** — the comparison/measurement can actually express the sought effect (here: the
  baseline grid must contain a budget adaptive could beat) — and must load the governing
  `knowledge/` doc at plan time. *(applied — see Q3 for the doc that already existed)*

## Q2 — What did every check miss?

The **estimator-class premise** was mis-framed through *two* plan cycles: rev-1 was APPROVED
by plan-review and implemented; rev-2 ("fair test" — extend the grid above `B_ref` + engineer
difficulty) was a *new* unsound design that the rev-2 plan-reviewer finally killed by naming
the fixed-width-functional property. Even the rev-3 draft over-generalized the mechanism to
betting (betting resolves `equivalent` below `B_ref`), caught by the rev-3 reviewer and fixed
to a per-instrument statement. The load-bearing correction every round was the same:
fixed-width percentile functional vs. MC-error-shrinking CS, applied *per instrument*.

- **Route → contextual:** `knowledge/equivalence-band-savings.md` (written by the unit) now
  captures exactly this — the estimator-class mechanism, the per-instrument magnitudes, and the
  directional-vs-equivalence scoping, cross-linked from `anytime-valid-band.md`. Adequate; no
  further doc. *(applied by the unit; verified in retro — not re-touched)*

## Q3 — What got re-derived that a doc would have prevented?

The fixed-width-functional property **was already documented** — `knowledge/anytime-valid-band.md`
(the reference resolves at `B_ref` because it is a fixed-width functional; the mean CS must
shrink MC error below δ). The rev-2 plan-reviewer *cited that line* to kill rev-2. Yet rev-1
and rev-2 were both designed without consulting it. So the doc existed; the gap was **not
loading the governing cold doc at plan time** for an experiment whose validity turned on it.
This is the same root as Q1's process routing (load the governing doc + check detectability),
not a second lesson — folded into that one PLAN Decision, no duplicate doc.

## Q4 — What friction repeated from a prior retro?

- **The local `readline`/pytest-capture segfault recurred — 4th unit now** (`adaptive-procedure`,
  `betting-cs-retest`, and this unit on both rev-1 and rev-3). The implementer used the
  `PYTEST_ADDOPTS='-p no:capture'` workaround each time; my own gate runs hit it intermittently
  (clean on some runs). Already the named candidate `gate-readline-resilience` (priority raised
  in the betting retro). The fix touches `scripts/`/`gate.d/` → out of the retro branch's file
  boundary → stays a `/1-plan` unit.
  - **Route → process** (PLAN): bump `gate-readline-resilience` again (now 4th recurrence, the
    top mechanical candidate). *(applied)*

- **Operational (not worth keeping):** (a) CI ran ~15 min on a slow runner and `gh pr checks`
  reported a stale `pending` long after the run had `success`; I nearly mis-read it — verify via
  `gh run view --json conclusion`, not the checks summary. (b) Local `main`'s untracked
  `work/<slug>/` copy blocked the post-merge `--ff-only`; backed it up to scratchpad and
  ff-pulled. Both one-offs; no durable artifact.

## Routing summary

| Lesson | Label | Where |
| --- | --- | --- |
| Experiment plans must state + check a detectability precondition and load the governing knowledge doc at plan time | process | `PLAN.md` Decisions *(applied)* |
| Equivalence-band structural negative + estimator-class mechanism + directional-vs-equivalence scoping | contextual | `knowledge/equivalence-band-savings.md` *(applied by the unit)* |
| Governing cold doc (fixed-width functional) existed but wasn't loaded at plan time | (same as row 1) | folded into the process Decision — no duplicate |
| readline segfault recurred (4th unit) | process | `PLAN.md` — bump `gate-readline-resilience` *(applied)* |
| CI stale-`pending` read; local-main ff-pull friction | not worth keeping | this retro only |
