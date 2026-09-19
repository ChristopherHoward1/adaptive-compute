# Retro — research-bootstrap

**Date:** 2026-09-19 · Unit merged via PR #1 (docs-only, no version bump).

First retro in the project; no prior retros to compare against.

## What did the gate miss that a reviewer caught?

The gate is prose-blind — it checked that the docs exist and are formatted, and
nothing more. The two findings that mattered were scientific: the plan-reviewer
caught (a) an over-claim that optional-stopping bias "does not transfer" to the
Monte-Carlo-budget setting (it *does*, at the decision level), and (b) that the
near-exact prior art (Gandy 2009 bounded-resampling-risk) was unnamed, inflating
the novelty claim. Neither is gate-checkable, and it would be wrong to try — this
is exactly the correlated-validator / review-carries-the-weight split the ML
profile already describes.

**Route: not worth keeping.** The gate behaved correctly; adversarial review is
the designed mechanism for research-content defects, and it worked.

## What did every check miss?

Citation accuracy. Neither the gate nor either reviewer can web-verify a
reference, and the cold review flagged one likely slip on its own reasoning
(Hyperband is usually cited as JMLR 2018, not 2017). For a `prior-art.md` this is
a standing fabrication/mis-attribution risk that the loop structurally cannot
catch.

**Route: contextual** → `knowledge/research-doc-citations.md`. A short standing
note so future research docs treat citations as verify-before-external-use by
default, rather than each doc re-inventing the caveat inline.

## What got re-derived that a doc would have prevented?

The release-close-out shape. On reaching `/4-release` I had to discover
in-situ that an **Orchestrator-authored** unit (chosen for this spec because
Codex is a poor fit for prose + prior art) produces only **one** review sentinel,
while `scripts/release.sh` requires **two** (Claude code-review + Codex second
review). That forced a mid-loop Owner decision and a plain-PR close-out. A one-
line standing note would have told me the close-out shape up front.

**Route: process** → one line in `PLAN.md` Decisions.

A durable *fix* (teaching `release.sh` a single-review / spec-only close-out path)
would touch `scripts/` and is therefore **out of bounds for the retro branch**.
If we want it, it becomes its own `/1-plan` unit — named here, not applied:
*"release.sh: supported close-out for single-review / spec-only units."* Only
worth doing if spec-only units recur; for now the process line suffices.

## What friction repeated from a prior retro?

None — first retro.
