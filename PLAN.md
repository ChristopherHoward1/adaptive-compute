# Plan

One screen, always. Reasoning lives in work units — link, don't restate.

## Objective

Build the **Adaptive Compute** research system through the agentic-coding harness loop. The research scope (adaptive-compute mechanism, bootstrap logic, SHAP-based analysis, model validation, routing) is defined and adversarially reviewed starting in the next session's `/1-plan`; nothing of it is implemented yet.

## Now

- **Shipped:** Harness scaffold (`machine-learning` profile); `research-bootstrap` (research definition, prior-art, v0 experiment design); **`fixed-budget-reference` v2026.9.0** — the deterministic, seeded, draws-accounted fixed-budget bootstrap reference + §6 generator battery (no adaptivity); `EVAL_COMMAND` wired; GROUND_TRUTH_SOURCE + DATA_REGIME resolved, EVAL_METRIC still PROVISIONAL. **`release-tag-merge-commit` v2026.9.1** — `release.sh tag-after-merge` tags the release commit by VERSION transition (merge-commit / squash / non-ff all tag hands-free; `knowledge/release-tagging.md`).
- **Next:** `/1-plan` the **adaptive procedure** (`docs/experiment-design.md` §3) — the system under test, judged against the fixed-budget reference. It consumes `bootstrap.py` (see `knowledge/bootstrap-seed-and-determinism.md`) and must resolve deferrals D1/D2 (`work/fixed-budget-reference/deferrals.md`).
- **Queued (mechanical):** `/1-plan` **`codex-review-prompt-printf-fix`** — `scripts/codex-review.sh` drops its `- CRITICAL/HIGH/MEDIUM/LOW` severity bullets from the Codex prompt (leading `-` parsed as a `printf` option) and the gate test misses it; also bound `worktree.sh add`'s `git fetch` so a stall can't hang the loop. Small; see `work/release-tag-merge-commit/retro.md`.

## Decisions

- 2026-09-19 — Adopt the agentic-coding harness with the `machine-learning` profile; keep Codex/Claude role defaults (Claude orchestrator + reviewers, Codex implementer + second reviewer) — scaffolding session.
- 2026-09-19 — Research reframed to **adaptive Monte-Carlo budget on fixed data** (grow simulation draws toward a fixed estimand), *not* adaptive sample size / sequential analysis. Compute counted in draws, not wall-clock. Reasoning: `work/research-bootstrap/plan.md`, `docs/research-definition.md` §3.
- 2026-09-19 — v0 stopping rule uses an **anytime-valid** band (confidence sequence / Gandy-style bounded-resampling-risk); the naive peeked band is rejected because optional-stopping bias applies at the decision level. Novelty claim narrowed to an *application + empirical* result over Gandy (2009) et al. — `docs/prior-art.md`.
- 2026-09-19 — **Architecture: one repository** for adaptive validation + adaptive explainability (they share the "grow MC draws under an anytime-valid band until a decision resolves" controller), but the **shared abstraction stays un-scaffolded** until the explainability consumer exists. **Dynamic inference routing is deferred, likely a separate repo** (per-input, streaming, regime-A methodology — not the MC-budget primitive). Revisit if v0/v1 shows the controller genuinely reused. — `docs/research-definition.md` §5, `docs/prior-art.md`.
- 2026-09-19 — ML declarations EVAL_METRIC / GROUND_TRUTH_SOURCE / DATA_REGIME set PROVISIONAL (not resolved) pending the reference unit; EVAL_COMMAND stays PENDING until code exists.
- 2026-09-19 — Close-out shape for **spec-only / Orchestrator-authored units**: they produce only one review sentinel, so `scripts/release.sh` (two-sentinel precondition) cannot run — close them via a plain PR to `main`, no CalVer bump. If such units recur, spin a `/1-plan` unit to teach `release.sh` a single-review close-out path. — `work/research-bootstrap/retro.md`.
- 2026-09-19 — **Reviewer calibration norm.** When the two `/3-review` reviewers split, the integration `code-reviewer` is the calibration anchor (its own contract: blocking on LOW-only findings is miscalibration); Codex tends to REQUEST CHANGES on latent/cosmetic items. Genuine design splits go to the Owner to arbitrate; otherwise ship on the integration reviewer's APPROVE with the latent items written to `deferrals.md`. Do not churn the implementer round-after-round on non-live findings. — `work/fixed-budget-reference/retro.md`.
- 2026-09-19 — **This harness build does not register digit-prefixed slash commands (`/1-plan`…) or `.claude/agents/*.md` as spawnable `subagent_type`s.** Invoke the loop skills directly (Skill tool) and stand in fresh read-only `Plan` subagents for the `plan-reviewer` / `code-reviewer` roles (writer ≠ reviewer preserved). — `work/fixed-budget-reference/retro.md`.
- 2026-09-19 — **`release.sh tag-after-merge` assumed a squash/rebase/ff merge** (origin/main tip must *be* the release commit); merge-commit PRs broke it and v2026.9.0 was hand-tagged. **Fixed in `release-tag-merge-commit` v2026.9.1**: it now tags the release commit located by VERSION transition, so all merge strategies tag hands-free. — `work/fixed-budget-reference/retro.md`, `knowledge/release-tagging.md`.
- 2026-09-20 — **`tag-after-merge` tags only the release *current* on `main`** (currency guard `origin/main:VERSION == version`) — deliberate; a tag missed until after a newer release ships needs a manual `git tag`. The loop tags immediately post-merge, so this holds in normal flow. Automatic back-tagging, if ever wanted, is a separate unit that relaxes this guard. — `work/release-tag-merge-commit/retro.md`, `knowledge/release-tagging.md`.

## Risks

- **Novelty is thin by design.** The stopping guarantee is Gandy (2009) / confidence sequences; our contribution is empirical (savings + uniform false-stop on equivalence-band comparison). If that residual collapses under a closer reading, narrow the question — don't inflate it. — `docs/prior-art.md`.
- **Most-likely negative result:** the anytime-valid band is too conservative, `B_max` is hit often, and savings evaporate. Acceptable as a finding; the fixed-B Pareto baseline is built to detect it. — `docs/research-definition.md` §8.
