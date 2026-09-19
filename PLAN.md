# Plan

One screen, always. Reasoning lives in work units — link, don't restate.

## Objective

Build the **Adaptive Compute** research system through the agentic-coding harness loop. The research scope (adaptive-compute mechanism, bootstrap logic, SHAP-based analysis, model validation, routing) is defined and adversarially reviewed starting in the next session's `/1-plan`; nothing of it is implemented yet.

## Now

- **Shipped:** Repository scaffolded on the agentic-coding harness (`machine-learning` profile). Minimal `src/` Python package, deterministic gates green.
- **In review:** `work/research-bootstrap` — research definition, prior-art map, and v0 experiment design authored (`docs/`); ML declarations set PROVISIONAL. Awaiting `/3-review`.
- **Next:** `/1-plan` the **fixed-budget reference bootstrap decision procedure** — deterministic, seeded, draws-accounted generators + reference (no adaptivity). It is the yardstick the first adaptive algorithm is judged against, and it wires `EVAL_COMMAND` into the gate. See `docs/experiment-design.md` §10.

## Decisions

- 2026-09-19 — Adopt the agentic-coding harness with the `machine-learning` profile; keep Codex/Claude role defaults (Claude orchestrator + reviewers, Codex implementer + second reviewer) — scaffolding session.
- 2026-09-19 — Research reframed to **adaptive Monte-Carlo budget on fixed data** (grow simulation draws toward a fixed estimand), *not* adaptive sample size / sequential analysis. Compute counted in draws, not wall-clock. Reasoning: `work/research-bootstrap/plan.md`, `docs/research-definition.md` §3.
- 2026-09-19 — v0 stopping rule uses an **anytime-valid** band (confidence sequence / Gandy-style bounded-resampling-risk); the naive peeked band is rejected because optional-stopping bias applies at the decision level. Novelty claim narrowed to an *application + empirical* result over Gandy (2009) et al. — `docs/prior-art.md`.
- 2026-09-19 — **Architecture: one repository** for adaptive validation + adaptive explainability (they share the "grow MC draws under an anytime-valid band until a decision resolves" controller), but the **shared abstraction stays un-scaffolded** until the explainability consumer exists. **Dynamic inference routing is deferred, likely a separate repo** (per-input, streaming, regime-A methodology — not the MC-budget primitive). Revisit if v0/v1 shows the controller genuinely reused. — `docs/research-definition.md` §5, `docs/prior-art.md`.
- 2026-09-19 — ML declarations EVAL_METRIC / GROUND_TRUTH_SOURCE / DATA_REGIME set PROVISIONAL (not resolved) pending the reference unit; EVAL_COMMAND stays PENDING until code exists.

## Risks

- **Novelty is thin by design.** The stopping guarantee is Gandy (2009) / confidence sequences; our contribution is empirical (savings + uniform false-stop on equivalence-band comparison). If that residual collapses under a closer reading, narrow the question — don't inflate it. — `docs/prior-art.md`.
- **Most-likely negative result:** the anytime-valid band is too conservative, `B_max` is hit often, and savings evaporate. Acceptable as a finding; the fixed-B Pareto baseline is built to detect it. — `docs/research-definition.md` §8.
