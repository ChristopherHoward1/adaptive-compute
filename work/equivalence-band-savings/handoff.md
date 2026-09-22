You are the implementer for **rev 3** of this work unit. Read AGENTS.md in the repo root first — it is your contract. Follow its build-discipline section while staying inside the plan footprint.

Work unit: work/equivalence-band-savings/plan.md  (read it IN FULL — it is rev 3 and your source of truth; the "Revision history" and "Review" sections explain why the design changed twice)
Branch: wt/equivalence-band-savings (already checked out; verify with `git branch --show-current`). **The rev-1 implementation is already committed on this branch** (`equiv_probe.py`, an unregistered `mixed_equivalence` generator, `eval --equiv-probe`, tests, artifacts). Your job is to **reframe it to rev 3**, not rebuild from scratch — reuse what fits, delete what rev-3 drops.

## What changed and why (read before touching code)

Two prior designs were rejected by cold review. The settled rev-3 finding:

**Inside `[−δ,δ]`, fixed-B *structurally* beats adaptive — this is a real negative, not a tuning/grid artifact.** The fixed-B percentile-bootstrap interval (the SAME estimator the reference uses, `sweep.py:71` ≡ `reference.py:91`) is a **fixed-width functional**: its half-width converges to a data-determined spread by some `B*≤~B_ref` and does NOT shrink with more draws. So fixed-B certifies `equivalent` cheaply at `B*`. Any anytime-valid adaptive instrument must instead shrink its CS half-width below δ, costing more draws than `B*`. The magnitude is **per instrument** (repo's own A/B, `anytime-valid-band.md:95-100`):
- **EB**: `equivalent` median ~768 ≫ `B_ref=320`; half-width still `> δ` at `B_ref`. Dominated by a fixed-B ~`B_ref`.
- **Betting**: `equivalent` median ~192 `< B_ref`; resolves below `B_ref`, but a smaller fixed-B `B*∈{32,64,128}` resolves the fixed-width interval even cheaper, so betting is dominated by a fixed-B `∈{32,64,128}` (never 320 — `pareto_verdict` lists only `b < adaptive_median`, `sweep.py:128-134`).

Both dominated ⇒ deep-negative, robustly. The unifying claim is the **estimator class**, not one budget.

## What to change (rev-1 → rev-3)

**DROP entirely** from the rev-1 code:
- `PROBE_FIXED_B_GRID` and any grid extension above `B_ref` (rev-2 idea; never score Pareto against a probe-local grid).
- The `precheck_region` / "resolvable-yet-hard" / difficulty-tier / `REQUIRED_DRAW_GRID` / `shallow_abs_delta` machinery and all "difficulty heterogeneity" framing. The fixture is now just an **in-band position spread**, no difficulty claim.

**ADD** (the load-bearing new content) — a **per-instrument mechanism diagnostic (A)**:
- `w_fix(B)` = half-width of `np.percentile(deltas[:B], [α/2,1−α/2])` for `B` on a **diagnostic sampling grid up to `4·B_ref=1280`** (needs 1280 bootstrap draws; this is a MEASUREMENT grid for curve (A) only — NOT the Pareto scoring grid, so it does not violate "no probe-local grid"). Expect a plateau by `B*≤~B_ref`.
- `w_ad(n)` = EB / betting band half-width vs draws `n`, evaluated at the **pinned `max_looks = ceil(b_max/b)`** of the scored run (record which value — the EB radius depends on it, `adaptive.py:59-62,123`). Expect: EB `> δ` at `B_ref`; betting reaches δ below `B_ref` but above its dominating `B*`.
- Write the curves to an artifact (`diagnostic.md` / `asymmetry.md`).

**KEEP / REFRAME**:
- Score BOTH instruments against the **released `FIXED_B_GRID=(32,64,128,320)`** via `fixed_b_sweep(grid=FIXED_B_GRID)` → build `MemberRun` **whose `fixed_decisions` is keyed by EVERY `b ∈ FIXED_B_GRID`** (hard contract: `_summarize_stratum` does `run.fixed_decisions[b]` for all grid `b`, `benchmark.py:237-249` — a missing key `KeyError`s) → reuse `benchmark._summarize_stratum` → `pareto_verdict`. No reimplemented savings math.
- Pin and assert: `b=64`, `b_max` (≫ EB median ~768 so EB resolves, e.g. keep a high value), and `FIXTURE_MAX_ABS_DELTA` (positions kept WELL inside the band so neither instrument mass-abstains).
- `verdict.md` headline **mechanically derived** from the JSON (as `_compare`, `eval.py:307-316`), stating the per-instrument dominating `b`.

## Key constraints (controlled-retest discipline — read knowledge/controlled-retest-discipline.md)

- **Feasibility guards must PASS on the scored set**: abstain rate ≤ a low bound AND reference-resolved fraction ≥ a high bound. Pushing fixture positions toward the edge makes EB abstain / go reference-unresolved; that is why `FIXTURE_MAX_ABS_DELTA` is pinned modestly. Tune these constants so the guards pass — but NEVER by lucky selection that hides a real problem; if you cannot make abstain-low pass without collapsing the position spread, STOP and surface it.
- **`PLATEAU_TOL`** for the `w_fix(4·B_ref) ≈ w_fix(B_ref)` guard must be derived from the `O(1/√B)` quantile MC noise and set WELL UNDER the ~2× drop a shrinking CS shows over `B_ref→4·B_ref` — so the test distinguishes fixed-width from shrinking, not jitter.
- **Guard-tests must be able to fail** (perturb/reconstruct, never self-compare), asserted on the SCORED cases, PER INSTRUMENT: (i-EB) `w_ad_eb(B_ref) > δ`; (i-bet) betting's cheapest resolving fixed-B `B* <` betting median; (ii) `w_fix` plateau; (iii) fixture in-band + `|Δ|` spread ≥ threshold; (iv) abstain-low + ref-resolved-high; (v) determinism; (vi) reuses `pareto_verdict`/`fixed_b_sweep`/`_summarize_stratum`; (vii) `b_max` pinned equal across arms; (viii) `BATTERY` still 5 members.
- **Do NOT touch** (must show empty diff vs origin/main): `generators.BATTERY` mapping (still exactly 5 members — adding an unregistered function is fine), `benchmark.py` incl. `FIXED_B_GRID`, `sweep.py`, `reference.py`, `metrics.py`, `bootstrap.py`, `adaptive.py`, `betting.py`, `strata.py`; and `work/adaptive-procedure/results.*`, `work/betting-cs-retest/results-*.*`, `comparison.md`.
- **Knowledge**: `knowledge/equivalence-band-savings.md` records the structural negative, the per-instrument estimator-asymmetry mechanism, and the scoping (adaptive saves on DIRECTIONAL decisions under difficulty heterogeneity, NOT equivalence). Cross-link from `anytime-valid-band.md`. Claim nothing beyond the artifacts.

## Acceptance criteria

The plan's "Acceptance criteria" list is authoritative — satisfy all of it (per-instrument mechanism diagnostic + guards; honest savings verdict per instrument; feasibility guards; mechanically-derived verdict; reuse released logic; released paths empty-diff; `eval --check` determinism; knowledge doc + cross-link).

## When done

1. Run `scripts/gate.sh` from the repo root — it must pass (exit 0). If the local native-`readline`/pytest segfault appears, work around with `PYTEST_ADDOPTS='-p no:capture'`, but the gate must pass on its own terms.
2. Commit on `wt/equivalence-band-savings` with a clear message.
3. Print a final summary: what you dropped/added/reframed, criteria partially met (if any), out-of-scope observations, and the **actual per-instrument numbers** (EB & betting medians, which fixed-B dominates each, `w_fix` plateau value, EB `w_ad(B_ref)` vs δ, betting `B*` vs median, abstain/ref-resolved fractions).
