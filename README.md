# Adaptive Compute

A research project asking a narrow question about Monte-Carlo evaluation, built
through a self-contained agentic-coding harness. The repository is two things at
once: the **research code** (`src/adaptive_compute/`) and the **development
machinery** (skills, agents, and scripts) that plans, implements, reviews, and
releases it.

## The research question

> For an iterative Monte-Carlo evaluation procedure run on a **fixed dataset**,
> can we allocate simulation draws adaptively — stopping when the *decision* the
> procedure supports is resolved — so as to spend materially fewer draws than a
> large fixed budget, while keeping the probability of reaching a *different
> decision than the full-budget procedure* below a pre-set bound?

The unit of compute is the **Monte-Carlo draw** (a bootstrap resample, a
permutation, later a sampled attribution coalition), not wall-clock time, so
"compute saved" is hardware-independent by construction. Crucially this is
adaptive *simulation budget on fixed data* — the estimand is the B→∞ value on
this exact dataset — **not** adaptive *sample size* / sequential analysis, where
the estimand is an unknown population. See [`docs/research-definition.md`](docs/research-definition.md)
for the full framing, [`docs/prior-art.md`](docs/prior-art.md) for where the
novelty sits (an application + empirical result over Gandy (2009) and anytime-valid
confidence sequences), and [`docs/experiment-design.md`](docs/experiment-design.md)
for the first experiment.

### Current result (v2026.9.3)

The first end-to-end result is a **genuine H1 negative**: the blind adaptive
controller (an anytime-valid empirical-Bernstein confidence sequence on the
bounded mean `E*[Δ*]`) achieves a **zero false-stop rate in every non-boundary
stratum** of the synthetic battery — but **fails the ≥2× savings gate**, because
its median draws exceed the whole fixed-B grid. The negative is
**instrument-specific**, resting on the finite-horizon EB boundary's looseness
and `B_max=2048`; the queued next step is to re-test with a tighter betting
confidence sequence (Waudby-Smith–Ramdas) before any general "adaptivity doesn't
save compute" claim. Details in [`work/adaptive-procedure/`](work/adaptive-procedure/)
and [`PLAN.md`](PLAN.md).

## The research code

Python 3.12, `src/` layout, numpy-only runtime:

| Module | Role |
| --- | --- |
| `metrics.py` | numpy-only AUC and paired `Δ` |
| `generators.py` | the five-member frozen synthetic battery (near-boundary, small-effect, heavy-tailed, rare-event/imbalance, easy/lopsided) |
| `bootstrap.py` | paired row-resampler with exact draw accounting and `SeedSequence.spawn` branches |
| `reference.py` | the fixed-budget percentile-bootstrap decision |
| `adaptive.py` | the blind adaptive bootstrap controller (empirical-Bernstein confidence sequence) |
| `sweep.py` | fixed-B sweep and Pareto helpers |
| `strata.py` | plug-in `Δ(E)` difficulty classification |
| `benchmark.py` | offline first-result harness |
| `eval.py` | `python -m adaptive_compute.eval` entry point |

```bash
python -m adaptive_compute.eval --check   # fast decision check (wired into the gate)
python -m adaptive_compute.eval --run     # offline benchmark → work/adaptive-procedure/results.{md,json}
```

## The harness (how this repo builds itself)

Development runs as a five-stage loop, driven by an Orchestrator session against
a human Owner. Each stage is a skill; reviews always come from **fresh
subagents** (separate model, cold context, read-only) — the writer never reviews
its own work.

```
/1-plan  →  /2-implement  →  /3-review  →  /4-release  →  /5-retro
```

- **/1-plan** — draft a work unit in `work/<slug>/plan.md`; a fresh reviewer critiques it.
- **/2-implement** — dispatch the implementer into an isolated git worktree; drive the gate loop until green.
- **/3-review** — a fresh reviewer reviews the diff against the plan.
- **/4-release** — run the release script, push, PR, and tag autonomously.
- **/5-retro** — record lessons and route each to the smallest durable artifact.

Invariants that are mechanical, not aspirational: the gate is a script
(`scripts/gate.sh` exits 0 or it doesn't), implementation happens only in
worktrees, release is a script (`scripts/release.sh`), and artifacts — not
transcripts — flow between stages. See [`CLAUDE.md`](CLAUDE.md) for the full
constitution.

## The gate

`scripts/gate.sh` is the single source of truth for "is it correct". Run it from
anywhere:

```bash
bash scripts/gate.sh
```

It `cd`s to the repo root, auto-detects stacks (here: Python + Shell), and runs
`shellcheck` over tracked scripts, `ruff check`, `pytest -q`, plus the
`gate.d/*.sh` hooks (shell smoke suite, ruff format-check + mypy, the eval check,
and ML-profile hygiene). CI runs the same gate on every push and PR.

## Layout

- `CLAUDE.md` / `ARCHI.md` / `PLAN.md` — the always-loaded "hot" context tier (~300-line budget).
- `config.yaml` — the one knob: profile, per-role models, implementer runtime, gate settings.
- `src/adaptive_compute/` — the research package. `tests/` — its tests plus the harness shell smoke suite.
- `skills/` — the loop stages (`1-plan`…`5-retro`) plus `init` / `compact`.
- `.claude/agents/` — the fresh-subagent reviewers.
- `scripts/` — the deterministic layer (gate, worktree, agent-exec, release, …).
- `profiles/` — `software` / `machine-learning` (active) / `database` / `work`.
- `knowledge/` — cold-tier docs, loaded only on citation.
- `docs/` — the research definition, prior art, and experiment design.
- `work/` — one directory per work unit (plan, review, retro, results).
- `VERSION` / `CHANGELOG.md` — CalVer (`YYYY.M.MICRO`) + Keep-a-Changelog, written only by `release.sh`.

## Conventions

- Writer never reviews; reviews come only from fresh read-only subagents.
- The gate and release scripts are authoritative — never overruled.
- Implementation happens in worktrees, never in the main checkout.
- Vendor/model names live only in `config.yaml`.
- Shell must pass `shellcheck`; Python must pass `ruff check`, `ruff format --check`, `mypy src`, and `pytest`.
- Notebooks are exploratory-only; correctness-critical logic moves to a gated `.py` module.

## License

See [`LICENSE`](LICENSE).
