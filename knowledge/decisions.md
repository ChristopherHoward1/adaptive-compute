# Archived decisions

Older `PLAN.md` decisions, moved here by `/compact`. Still in force unless a newer decision supersedes them.

- 2026-09-19 — Adopt the agentic-coding harness with the `machine-learning` profile; keep Codex/Claude role defaults (Claude orchestrator + reviewers, Codex implementer + second reviewer) — scaffolding session.
- 2026-09-19 — Research reframed to **adaptive Monte-Carlo budget on fixed data** (grow simulation draws toward a fixed estimand), *not* adaptive sample size / sequential analysis. Compute counted in draws, not wall-clock. Reasoning: `work/research-bootstrap/plan.md`, `docs/research-definition.md` §3.
- 2026-09-19 — v0 stopping rule uses an **anytime-valid** band (confidence sequence / Gandy-style bounded-resampling-risk); the naive peeked band is rejected because optional-stopping bias applies at the decision level. Novelty claim narrowed to an *application + empirical* result over Gandy (2009) et al. — `docs/prior-art.md`.
- 2026-09-19 — **Architecture: one repository** for adaptive validation + adaptive explainability (they share the "grow MC draws under an anytime-valid band until a decision resolves" controller), but the **shared abstraction stays un-scaffolded** until the explainability consumer exists. **Dynamic inference routing is deferred, likely a separate repo** (per-input, streaming, regime-A methodology — not the MC-budget primitive). Revisit if v0/v1 shows the controller genuinely reused. — `docs/research-definition.md` §5, `docs/prior-art.md`.
