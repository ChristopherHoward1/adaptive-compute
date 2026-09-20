# Retro — fixed-budget-reference (v2026.9.0)

Released 2026-09-19. Six code-review rounds, dual APPROVE at round 6.

## The four questions

**What did the gate miss that a reviewer caught?**
The gate was green every round; reviewers caught design-semantics and latent-API
issues the gate structurally can't: the silent point-estimate fallback, the
self-defeating within-run MCSE, straddle semantics, the `--check` draw undercount,
and the `SeedSequence`-reuse determinism footgun. This is the intended division of
labour (gate = mechanical, reviewers = judgment) and is **not worth keeping** as a
new lesson — with one exception routed below: the determinism-reuse gap.

**What did every check miss (for a while)?**
The `--check` draw undercount survived the gate and three review rounds. More
sharply: round 4's *own* hardening (routing a raw `SeedSequence` through `spawn`)
**introduced** a determinism regression that the int-seed-only determinism test
could not see; round 5 caught it. Lesson: changes to shared seed/determinism code
need replay assertions on *both* seed paths. → **contextual**
(`knowledge/bootstrap-seed-and-determinism.md`).

**What got re-derived that a doc would have prevented?**
The seed-branching contract (reference = branch [0], adaptive = branch [1]
reserved; clone-before-spawn; determinism over int *and* reused `SeedSequence`) was
argued in rounds 3 and 5. The adaptive unit will consume `bootstrap.py` directly
and would re-derive it. → **contextual**
(`knowledge/bootstrap-seed-and-determinism.md`, same doc).

**What friction repeated from a prior retro?**
The `research-bootstrap` retro flagged that `release.sh` makes workflow
assumptions (its two-sentinel precondition). This unit hit a *different*
`release.sh` assumption: `tag-after-merge` requires `origin/main`'s tip to **be**
the release commit (squash/rebase/ff merge) and tags the tip; PR #3 was merged as a
**merge commit**, so the tip was the merge commit and tagging refused even though
`main` had not advanced past the release. Completed by tagging the release commit
`74ddb64` by hand this once (Owner-authorized); the durable fix touches `scripts/`
so it is a **/1-plan unit**, not applied here (see below).

Also recurring all session: this harness build does not register digit-prefixed
slash commands (`/1-plan`…) or the `.claude/agents/*.md` types as spawnable
`subagent_type`s. Worked around by invoking skills directly and standing in fresh
read-only `Plan` subagents (writer ≠ reviewer preserved). → **process**.

Meta-observation (six rounds): Codex issued REQUEST CHANGES every round 1–5 with a
distinct, mostly-latent finding while the integration `code-reviewer` APPROVED
throughout. Handled by: Owner arbitration on genuine reviewer splits (straddle
semantics, seed API), and — per the `code-reviewer` contract's own
"blocking on LOW-only findings is miscalibration" — treating the integration
reviewer as the calibration anchor and shipping on its APPROVE when Codex blocked
only on latent/cosmetic items, with the latent items written to `deferrals.md`.
→ **process**.

## Routing

- **contextual** — `knowledge/bootstrap-seed-and-determinism.md` (new). The seed
  branching + clone-before-spawn + both-paths-determinism contract. *Applied on
  this branch.*
- **process** — two `PLAN.md` Decisions lines: (a) review-calibration norm;
  (b) harness build's unregistered skills/agents + the stand-in workaround.
  *Applied on this branch.*
- **mechanical (deferred to /1-plan)** — `release.sh tag-after-merge` must handle
  merge-commit PRs: either standardize the repo on squash-merge, or have
  `tag-after-merge` tag the release commit by SHA when it is reachable from
  `origin/main` with a matching `VERSION` (rather than requiring the tip subject to
  be `Release vX`). Touches `scripts/`, so it is a `/1-plan` unit, not applied in
  this retro. **Next `/1-plan`: `release-tag-merge-commit`.**
- **deferrals already recorded** (`work/fixed-budget-reference/deferrals.md`) —
  D1 (degenerate zero-positive resample) and D2 (hard-member MCSE diagnostic uses
  the raising reference) → both routed to the adaptive unit. Not re-litigated here.

## Not worth keeping

The many "gate green but reviewer caught it" findings — expected by design (gate is
mechanical, reviewers judge). Recorded only so it isn't mistaken for a gate defect.
