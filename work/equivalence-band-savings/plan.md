# Equivalence-band savings: why fixed-B structurally beats adaptive inside [−δ,δ]

**Slug:** equivalence-band-savings · **Date:** 2026-09-22 · **Status:** approved (rev 3 — structural-negative reframe)

## Revision history (audit trail)

- **Rev 1** — probe on a mixed in-band fixture, scored against the released
  `FIXED_B_GRID=(32,64,128,320)`; verdict "deep-negative." Implemented, gate-green.
- **Rev-1 round-1 review** — Codex APPROVE (2 MEDIUMs); integration anchor **HIGH**: the
  fixture had `|Δ|` position spread but ~no difficulty spread, and the deep-negative was
  "not robustly distinguished from reference-resolving-power." Owner → re-plan.
- **Rev 2** — "fair test": probe-local grid above `B_ref` + engineered difficulty
  heterogeneity. **Rejected by cold plan-reviewer (REVISE, crux finding):** the fixed-B
  baseline uses the *same percentile-bootstrap estimator* as the reference, which is a
  **fixed-width functional** (interval width converges with draws, does not shrink). So a
  case reference-resolvable at `B_ref` is fixed-B-resolvable at ~`B_ref`; any grid entry
  above `B_ref` is **redundant**, and a "flip" against it is a strawman. The honest single
  fixed baseline is ≈`B_ref`, which adaptive's in-band median genuinely exceeds — so
  **rev-1's "fixed-B wins" was the *correct* verdict**, only mislabeled. "Difficulty
  heterogeneity" in-band is unachievable/circular. Owner → reframe to the structural
  negative (this rev 3).

## Goal

Close the equivalence-band question honestly: **can any adaptive instrument beat a single
fixed-B when the truth is inside `[−δ,δ]`? No — and structurally so.** Inside the band,
the fixed-B percentile-bootstrap interval (the *same* estimator the reference uses,
`sweep.py:71` ≡ `reference.py:91`) is a **fixed-width functional**: its half-width
converges to the data's bootstrap-quantile spread by some data-determined `B*` and does
not shrink with more draws, so fixed-B certifies `equivalent` cheaply at `B*` (≤ ~`B_ref`
on these cases) or not at all. Any anytime-valid adaptive instrument must instead drive its
confidence-sequence half-width below `δ` by *shrinking Monte-Carlo error*, which costs more
draws than the cheapest resolving fixed-B `B*` — so a single fixed-B **dominates** adaptive
on draws for in-band decisions. The magnitude is **instrument-specific**, and the repo's own
A/B pins it (`anytime-valid-band.md:95-100`):
- **EB** — `equivalent` median ~768 draws ≫ `B_ref=320`; its half-width is still `> δ` at
  `B_ref` (the EB linear term `14·log(40)/(3·319)=0.054 > δ` even at `max_looks=1`,
  `adaptive.py:59-62`). Dominated by a fixed-B at ~`B_ref`.
- **Betting** — `equivalent` median ~192 draws `< B_ref`; it *does* resolve equivalence
  below `B_ref`, but a still-smaller fixed-B (`B*≈128`) resolves the fixed-width interval
  even cheaper, so betting is dominated by a fixed-B `∈{32,64,128}`, not by ~`B_ref`.

Both are dominated by *some* fixed-B in-band — the negative is real and robust for both —
but the "needs ≫`B_ref` draws / half-width `> δ` at `B_ref`" mechanism is **EB-specific**;
for betting the observable is "fixed-B `B*` resolves below betting's median." The unifying
claim is the estimator class, not a single budget: fixed-width percentile functional vs.
MC-error-shrinking anytime-valid CS.

Done = (A) a **mechanism diagnostic**, *per instrument*, demonstrating the estimator
asymmetry directly (fixed-B half-width plateaus by `B*≤~B_ref`; the adaptive half-width
shrinks with draws — for EB still `> δ` at `B_ref`, for betting reaching `δ` only above the
cheapest resolving fixed-B); (B) the **honest savings verdict** — both instruments scored
against the released `FIXED_B_GRID`, showing fixed-B dominates in-band (per-instrument which
`b`); and (C) a `knowledge/` writeup recording the negative **and its correct scoping**: the
adaptive MC-budget saves on *directional* decisions under difficulty heterogeneity (the CS
can cross a threshold early), but not on *equivalence* decisions, where a fixed-width
percentile functional is the right tool and MC-error shrinkage is strictly more expensive.

This reuses the rev-1 machinery (`equiv_probe.py`, `eval --equiv-probe`, the in-band
fixture) but **drops** rev-2's grid extension and all "difficulty-tier / resolvable-yet-
hard" framing, and **adds** the mechanism diagnostic that makes the negative explanatory
rather than merely observed.

## Approach

Offline, isolated from every released path per `knowledge/controlled-retest-discipline.md`:
`eval --equiv-probe` writes only to `work/equivalence-band-savings/`; the frozen `BATTERY`,
the released `FIXED_B_GRID`, the released §8 gate, and the released `--run`/`--compare`
artifacts are untouched.

**(A) Mechanism diagnostic — the estimator asymmetry (new, load-bearing), *per
instrument*.** On a set of in-band cases (`|Δ| < δ`, spanning positions from `Δ≈0` up to a
**pinned max `|Δ| ≤ FIXTURE_MAX_ABS_DELTA`** kept well inside the band — position spread
only, no "difficulty" claim; the cap keeps both instruments *resolving* rather than
abstaining, see feasibility below), measure and tabulate two half-width curves from the
*same* bootstrap draws, deterministically:
- **Fixed-B percentile half-width `w_fix(B)`** = half the width of `np.percentile(deltas[:B],
  [α/2,1−α/2])` for `B` on a **diagnostic sampling grid up to `4·B_ref=1280`** (this is a
  measurement grid for curve (A) only — it is *not* the Pareto scoring grid of (B), so the
  "no probe-local grid" rule is not violated; it just needs 1280 bootstrap draws available).
  Expected: `w_fix(B)` plateaus at the data-determined spread by `B*≤~B_ref` and is flat
  thereafter (fixed-width functional).
- **Adaptive CS half-width `w_ad(n)`** = the EB / betting band half-width as a function of
  draws `n` (from `adaptive.py` / `betting.py` bounds), evaluated at the **pinned
  `max_looks = ceil(b_max/b)`** used by the scored run (the EB radius depends on `max_looks`,
  `adaptive.py:59-62,123` — the diagnostic records which value it uses so `w_ad` is
  reproducible). Expected, **instrument-specific**: for **EB**, `w_ad(B_ref) > δ` (crosses
  `δ` only at `n≫B_ref`); for **betting**, `w_ad(n)` reaches `δ` at `n` *below* `B_ref` but
  *above* the cheapest resolving fixed-B `B*`.
The diagnostic reports, per case and per instrument, `w_fix(B*)` vs `δ` (fixed-B resolves at
`B*`) and the smallest `n` with `w_ad(n)<δ` (the instrument's true certification cost). The
guard-test is therefore **per instrument** (EB: `w_ad(B_ref)>δ`; betting: cheapest resolving
fixed-B `B* <` betting's `w_ad<δ` crossing / median) — see Acceptance.

**(B) Honest savings verdict — reuse the released grid and helpers.** The probe scores both
instruments against the released `FIXED_B_GRID=(32,64,128,320)` via the released path:
`fixed_b_sweep(grid=FIXED_B_GRID)` → build `MemberRun` **whose `fixed_decisions` is keyed by
every `b ∈ FIXED_B_GRID`** (hard contract — `_summarize_stratum` indexes
`run.fixed_decisions[b]` for all grid `b`, `benchmark.py:237-249`; a missing key `KeyError`s)
→ `benchmark._summarize_stratum` (reads module-level `FIXED_B_GRID`, `benchmark.py:32,237`) →
`pareto_verdict`. No probe-local grid, no reimplemented savings math. The verdict is
**per-instrument on which `b` dominates**: for EB `fixed_b_dominating_adaptive` centers on
`~B_ref` (median ~768 > 320); for betting it is `⊂{32,64,128}` (median ~192, so 320 can
never appear — `pareto_verdict` lists only `b < adaptive_median`, `sweep.py:128-134`). Both
tuples are non-empty ⇒ fixed-B dominates ⇒ deep-negative, robustly. Both arms pin `b=64` and
a pinned, asserted `b_max`; the JSON records `pareto_best_savings_ratio`,
`fixed_b_dominating_adaptive`, **abstain/nondecision rate** (read first — the abstain-vacuity
trap, `anytime-valid-band.md:47-57`), false-stop count + CI, and the **scored denominator**
(n scored / n generated, per round-1 Codex MEDIUM).

**Feasibility (must-fix from rev-3 review): pin `b_max` and `FIXTURE_MAX_ABS_DELTA` so
abstain stays low.** Pushing fixture positions toward the band edge fights the abstain-low
requirement: near-edge in-band cases make EB abstain (inflating the rate) or go
reference-unresolved (shrinking the denominator). So (i) `FIXTURE_MAX_ABS_DELTA` is pinned
well inside the band (a modest position spread — enough to clear the `|Δ|`-spread threshold,
not so much that EB abstains), and (ii) `b_max` is pinned high enough that EB resolves the
scored cases (EB in-band median ~768, so `b_max` ≫ that). The probe asserts, on the scored
set, abstain rate ≤ a low bound and reference-resolved fraction ≥ a high bound — so the
negative reflects draws, not abstention/attrition.

**(C) Verdict + knowledge.** `verdict.md`'s one-line headline is **mechanically derived**
from the JSON (as `_compare`, `eval.py:307-316`): fixed-B dominates adaptive in-band at
≥2×; H1 unsupported in the equivalence band. `knowledge/equivalence-band-savings.md`
records the structural negative, the estimator-asymmetry mechanism, and the scoping (saves
on directional, not equivalence, decisions); `anytime-valid-band.md` cross-links it.

**The in-band fixture is a fixture, not a battery member** — a new unregistered generator
function (`generate()`/`BATTERY` diff-invariant), used only by the probe. It exists only to
give the diagnostic a spread of in-band positions; it carries no "difficulty" claim.

Alternatives considered:
- *Extend the fixed-B grid above `B_ref`* — rejected (rev-2 crux): fixed-B is a fixed-width
  functional, so budgets above `B_ref` are redundant and a win against them is a strawman.
- *Engineer difficulty heterogeneity in-band* — rejected: unachievable on the fixed-B
  estimator (deep and edge cases both resolve at ~`B_ref`) and circular on adaptive draws.
- *Report rev-1's numbers unchanged with no mechanism* — rejected: the anchor's HIGH was
  that the negative wasn't *explained*; the mechanism diagnostic (A) is what earns the
  verdict.

## Footprint

Files to add / carry over from rev-1 (branch `wt/equivalence-band-savings`):
- `src/adaptive_compute/generators.py` — the unregistered in-band `mixed_equivalence`
  fixture function (position spread inside `[−δ,δ]`; **not** in `BATTERY`). Strip any
  "hard-tier / resolvable-yet-hard" difficulty machinery from the rev-1 version.
- `src/adaptive_compute/equiv_probe.py` — reframed: (i) the mechanism diagnostic (A)
  computing `w_fix(B)` (sampling grid up to `4·B_ref`) and `w_ad(n)` (at the pinned
  `max_looks`) curves; (ii) the per-case driver scoring against the **released
  `FIXED_B_GRID`**, building `MemberRun.fixed_decisions` keyed by every grid `b` (drop
  rev-1's precheck/`PROBE_FIXED_B_GRID`/difficulty-margin code); (iii) reuse
  `benchmark._summarize_stratum` + `pareto_verdict`; (iv) the minimal diagnostic over the
  natural `equivalent` stratum (Δ by regeneration); (v) pinned `b=64`/`b_max`/
  `FIXTURE_MAX_ABS_DELTA` constants, asserted; mechanically-derived headline.
- `tests/test_equiv_probe.py` — guard-tests that can fail, **per instrument** and on the
  **scored** cases: (i-EB) `w_ad_eb(B_ref) > δ` (EB not resolved at `B_ref`); (i-bet)
  betting's cheapest resolving fixed-B `B* <` betting's median draws (betting resolves
  below `B_ref` but a smaller fixed-B beats it); (ii) fixed-width plateau: `w_fix(4·B_ref)`
  within `PLATEAU_TOL` of `w_fix(B_ref)`, where `PLATEAU_TOL` is set from the `O(1/√B)`
  quantile MC-noise and **well under** the ~2× drop a shrinking CS shows over `B_ref→4·B_ref`
  (so the test distinguishes fixed-width from shrinking, not MC jitter); (iii) fixture
  in-band (`|Δ|<δ`, `|Δ| ≤ FIXTURE_MAX_ABS_DELTA`) with `|Δ|` spread ≥ threshold; (iv)
  abstain rate ≤ low bound and reference-resolved fraction ≥ high bound on the scored set;
  (v) probe determinism (int-seed replay); (vi) probe calls
  `pareto_verdict`/`fixed_b_sweep`/`_summarize_stratum` (no reimplemented savings); (vii)
  `b_max` pinned + equal across arms; (viii) `BATTERY` still 5 members.
- `work/equivalence-band-savings/diagnostic.md`, `asymmetry.md` (or a section of
  diagnostic.md), `probe-eb.json`, `probe-betting.json`, `verdict.md`.
- `knowledge/equivalence-band-savings.md`.

Files to modify:
- `src/adaptive_compute/eval.py` — `--equiv-probe` subcommand + light `--check`
  determinism assertion. `--run`/`--compare` unchanged.
- `knowledge/anytime-valid-band.md` — one cross-reference line.

Files NOT to touch (live hazard):
- `generators.py` **`BATTERY` mapping** (frozen 5 members).
- `benchmark.py` (incl. released `FIXED_B_GRID`), `sweep.py`, `reference.py`, `metrics.py`,
  `bootstrap.py`, `adaptive.py`, `betting.py`, `strata.py`.
- `work/adaptive-procedure/results.*`, `work/betting-cs-retest/results-*.*`, `comparison.md`.

## Acceptance criteria

- [ ] **Mechanism diagnostic (A), the load-bearing new content, per instrument:** the probe
  writes the `w_fix(B)` (sampling `B` up to `4·B_ref`) and `w_ad(n)` (at pinned `max_looks`,
  value recorded) curves for the scored in-band cases, and asserts: (a) fixed-width plateau
  `|w_fix(4·B_ref) − w_fix(B_ref)| ≤ PLATEAU_TOL` (tolerance derived from quantile MC noise,
  well under the shrinking-CS drop); (b-EB) `w_ad_eb(B_ref) > δ`; (b-bet) betting's cheapest
  resolving fixed-B `B*` is strictly less than betting's median draws. Deterministic on
  int-seed replay. Fails if the plateau is absent or the per-instrument asymmetry is absent.
- [ ] **Honest savings verdict (B), per instrument:** both instruments scored against the
  released `FIXED_B_GRID` (no probe-local grid) via `_summarize_stratum` → `pareto_verdict`;
  `probe-eb.json`/`probe-betting.json` carry `pareto_best_savings_ratio`,
  `fixed_b_dominating_adaptive` (non-empty for both — EB centered on ~`B_ref`, betting
  `⊂{32,64,128}`), abstain/nondecision rate, false-stop count + CI, scored denominator, and
  draw percentiles. Verdict = fixed-B dominates in-band for both (deep-negative).
- [ ] **Feasibility guards pass:** `FIXTURE_MAX_ABS_DELTA` and `b_max` are pinned so that, on
  the scored set, abstain rate ≤ a low bound **and** reference-resolved fraction ≥ a high
  bound — asserted, so the negative reflects draws, not abstention or attrition.
- [ ] **Verdict mechanically derived:** `verdict.md`'s headline is computed from the JSON,
  not hand-written, and states the per-instrument dominating `b`.
- [ ] **Fixture in-band:** `test_equiv_probe.py` asserts all fixture `|Δ| < δ` and `|Δ|`
  spread ≥ a threshold; perturb/reconstruct, never self-compare. No "difficulty" claim.
- [ ] **Diagnostic over the natural stratum:** `diagnostic.md` reports the frozen
  `equivalent` stratum's `adaptive_draws` (p50/p90/p99 + CV) and `δ−|Δ|` (Δ by
  regeneration), framed as "generator-homogeneous."
- [ ] **Reuses released savings logic:** `git diff` shows `pareto_verdict` / `fixed_b_sweep`
  / `_summarize_stratum` called with the released `FIXED_B_GRID`; no reimplemented Pareto
  math and no probe-local grid constant.
- [ ] **Released paths untouched:** `git diff` shows `generators.BATTERY` unchanged (5
  members), `benchmark.py` (incl. `FIXED_B_GRID`) unchanged, `work/adaptive-procedure/` +
  `work/betting-cs-retest/` artifacts empty diff.
- [ ] `eval --check` gains a light `--equiv-probe` determinism assertion; `bash
  scripts/gate.sh` exits 0.
- [ ] `knowledge/equivalence-band-savings.md` records the structural negative, the
  estimator-asymmetry mechanism, and the directional-vs-equivalence scoping, claiming
  nothing beyond the artifacts; `anytime-valid-band.md` cross-links it.

## Release

Release note: Add an offline equivalence-band probe (`eval --equiv-probe`) that measures the
fixed-B-vs-adaptive estimator asymmetry inside `[−δ,δ]` and scores both adaptive instruments
against the released fixed-B grid, establishing that fixed-B structurally dominates adaptive
on equivalence decisions — the fixed-B percentile interval is a fixed-width functional that
resolves at ~`B_ref`, while any anytime-valid instrument must shrink Monte-Carlo error below
δ — so the residual H1 savings negative in the equivalence band is real and mechanistic, not
a tuning or grid artifact.

## Verification

- `bash scripts/gate.sh` (shellcheck + ruff + ruff format + mypy + pytest + `gate.d/` incl.
  `eval --check`).
- `python -m adaptive_compute.eval --equiv-probe`, then read `verdict.md` + the asymmetry
  table — confirm `w_fix` plateaus by `B*≤B_ref`, EB `w_ad(B_ref)>δ`, betting resolves below
  `B_ref` but above its dominating `B*`, both arms populated, headline consistent with the JSON.
- `git diff --stat` confirms `FIXED_B_GRID`, `BATTERY`, and the released artifacts untouched.

## Out of scope (follow-on, not this unit)

- Whether the directional-decision savings claim (adaptive wins under difficulty
  heterogeneity on `A_better`/`B_better`) warrants its own dedicated positive-result unit —
  a separate `/1-plan`.
- Any change to the released §8 metric, `FIXED_B_GRID`, or the frozen battery.

## Review

**Rev 1** — plan-reviewer APPROVE (post-revision, 5 must-fix applied). Implemented,
gate-green.

**Rev-1 round-1 implementation review** — Codex APPROVE (2 MEDIUMs: per-ratio precheck may
vary shallow difficulty; scored denominator not preserved). Integration `code-reviewer`
(anchor) **REQUEST CHANGES / HIGH**: fixture had `|Δ|` spread but ~no difficulty spread,
deep-negative not distinguished from reference-resolving-power. Owner arbitrated → re-plan.

**Rev 2** — cold plan-reviewer **REVISE** (crux): a grid above `B_ref` is a strawman
because fixed-B is a fixed-width functional; rev-1's "fixed-B wins" was correct; difficulty
heterogeneity in-band is unachievable/circular. Owner arbitrated → reframe to the structural
negative (rev 3).

**Rev 3** — reframed to the honest structural negative + estimator-asymmetry mechanism;
scores against the released grid; Codex MEDIUMs folded in (denominator recorded; difficulty
framing dropped entirely). Cold plan-reviewer **REVISE**, 3 must-fix + 4 clarity findings,
all accepted (no disagreements to route to the Owner):

1. **The strong mechanism is EB-specific — betting resolves `equivalent` at median ~192 <
   `B_ref=320`**, so `w_ad(B_ref)>δ` is false for betting. **Applied:** Goal/Approach/guards
   made **per instrument** — EB: `w_ad(B_ref)>δ`, dominated by ~`B_ref`; betting: resolves
   below `B_ref` but a smaller fixed-B `B*∈{32,64,128}` resolves the fixed-width interval
   even cheaper and dominates. Both non-empty ⇒ deep-negative.
2. **"fixed-B at ~`B_ref` dominates" mislabels betting** (`pareto_verdict` lists only
   `b < adaptive_median`, so 320 can't appear for betting median ~192). **Applied:** verdict
   (B) reworded per-instrument on which `b` dominates.
3. **Abstain-low vs edge-position spread feasibility not pinned.** **Applied:** pinned
   `FIXTURE_MAX_ABS_DELTA` (positions kept well inside the band) and `b_max` (≫ EB median),
   with asserted abstain-low + reference-resolved-high guards on the scored set.
4–7 (clarity, applied): pin/record `max_looks` for `w_ad`; `PLATEAU_TOL` derived from
   quantile MC noise and set under the shrinking-CS drop; the `w_fix` diagnostic sampling
   grid may reach `4·B_ref` (distinct from the Pareto scoring grid — "no probe-local grid"
   binds only on (B)); `MemberRun.fixed_decisions` keyed by every `FIXED_B_GRID` `b` (hard
   contract, else `_summarize_stratum` `KeyError`s).

The reviewer confirmed the estimator-asymmetry mechanism is **correct for EB** and the honest
negative real and non-circular for both instruments; reuse of `_summarize_stratum` (reading
module `FIXED_B_GRID`) and released-path inertness were confirmed sound (no findings).

Plan verdict (rev 3): **APPROVE** (post-revision)
