# Betting-CS re-test of the v0 H1 negative

**Slug:** betting-cs-retest · **Date:** 2026-09-21 · **Status:** implemented

## Goal

The v0 first result (`adaptive-procedure` v2026.9.3) is a **genuine but
instrument-specific H1 negative**: the adaptive procedure resolves every
non-boundary stratum with a zero false-stop rate (§7 PASS) but fails §8's ≥2×
savings gate — its median draws (448 moderate / 768 equivalent) exceed the whole
fixed-B grid. `knowledge/anytime-valid-band.md` records *why*: the finite-horizon
empirical-Bernstein (EB) band's radius is dominated by a linear `≈14·log/3n` term
that cannot shrink below `δ=0.05` until `n` is large, so an `equivalent` decision
needs many draws. PLAN.md's standing decision forbids generalizing "adaptivity does
not save compute" until this is re-tested against a **tighter anytime-valid
instrument**.

Done = a **controlled A/B**: add a Waudby-Smith–Ramdas (WSR) betting confidence
sequence as a *selectable* adaptive band, run §7/§8 through the existing benchmark
under **both** instruments over the same bootstrap stream, and publish a comparison
artifact stating plainly whether the ≥2× savings verdict flips under betting while
the zero-false-stop guarantee holds. The result — flip or no-flip — is the
deliverable; either is a valid finding.

## Approach

**Add, don't replace.** Introduce `betting.py` and make the band an instrument
*seam* on `adaptive_decision` (`instrument: "eb" | "betting"`, default `"eb"`).
This (a) keeps the released v0 EB path bit-reproducible, (b) makes the re-test a
clean same-stream A/B where *only the band changes*, and (c) leaves promoting
betting to default as a separate, reversible Owner decision if it wins.

**The instrument.** WSR (2023), "Estimating means of bounded random variables by
betting" — the hedged-capital betting CS for a bounded mean. Each draw
`Δ* ∈ [-1,1]` is affinely rescaled to `X = (Δ*+1)/2 ∈ [0,1]`; the CS is built for
`μ_X ∈ [0,1]` and mapped back to Δ-space by `2·[l,u]−1`. Construction over a fixed
grid `m ∈ [0,1]`: for each `m`, maintain the two-sided hedged capital
`K_t(m)=½(K⁺_t+K⁻_t)`, `K±_t=∏_{i≤t}(1±λ_i(m)(X_i−m))`, with a **predictable**
betting fraction `λ_i(m)` from the running mean/variance of `X_{<i}` only
(WSR's approx-GRAPA plug-in, truncated to `[0, c/(m∨(1−m))]`); the level-α CS is
`{m : max_{s≤t} K_s(m) < 1/α}`, bounds = min/max surviving grid points. Anytime
validity comes from Ville's inequality on the nonnegative martingale — enforced by
(i) `λ_i` depending only on past draws and (ii) the running-max over `s≤t`. The
exact λ scheme and grid resolution are the implementer's to finalize against the
coverage test; the plan pins the estimand, the rescale, the decision functional,
and the validity mechanics.

**Same decision rule, same stream — `b` held constant.** Betting reuses
`decision_from_bounds` (band wholly above `+δ` / below `−δ` / inside `[−δ,δ]`) and
consumes the **same** `adaptive_bootstrap_stream`. Critically, the **batch size `b`
is fixed across both arms**: `adaptive_bootstrap_stream` draws each batch with a
fresh `rng.integers(0, n, size=(b, n))` (`bootstrap.py:196-205`), so a different `b`
shifts the RNG call boundaries and the per-draw deltas would no longer match — which
would confound the very attribution this unit exists to make. So the *only* degree
of freedom that changes between arms is the band, and `b` is a shared constant (pin
the current `b=64`). This makes the drop-in stream-equivalence check exact.

**Per-instrument `B_max` tuning only.** Betting is expected to resolve at far
smaller budgets — the whole point on the savings axis (`savings = fixed_B /
adaptive_median_draws`). It gets its own `B_max` tune (candidate set includes
entries `< 2048`, e.g. 256/512/1024) on the tune split, reported honestly on the
test split, mirroring `_tune_params`' discipline — but **`b` is not a tuning
dimension here** (fixed per above). Reusing EB's `B_max=2048` would understate
betting's savings and is disallowed.

**On-path deferral folded in:** **A5** (`benchmark.py` verdict uses strict `< α`
where §7 says `≤ α`) — the verdict logic is edited here anyway; correct it to `≤ α`
for both arms. **A3** (fixed-B grid top `== B_ref`) is *deliberately left alone*:
moving the grid would change the §8 baseline and confound the instrument
attribution; it stays a separate tuning unit.

**Structure: single-arm `run_benchmark`, run twice — not a paired object.**
`run_benchmark`/`_run_member_seed`/`_tune_params` are parametrized by `instrument`
(keyword, default `"eb"`), keeping the existing single-arm `BenchmarkResult` schema
and `_summary_markdown` intact. The offline path runs it once per instrument and
writes two standard-schema artifacts, `results-eb.{md,json}` and
`results-betting.{md,json}`, under `work/betting-cs-retest/`; a thin wrapper reads
both JSONs to emit a one-line headline (does betting's `savings_pareto_pass` flip to
true while `false_stop_test_pass` stays true?). This keeps the comparison honest —
both arms scored against the **same shared fixed-B grid** (the §8 baseline, identical
across arms) — without restructuring `BenchmarkResult` or breaking
`tests/test_benchmark.py`. The **released v0 artifact
`work/adaptive-procedure/results.*` is preserved untouched**: the comparison writes
to the new work dir only, via a new `eval --compare` flag; existing `--run` behavior
is unchanged.

Alternatives considered: *replace EB in-place* — rejected (loses v0 reproducibility,
mutates a released instrument, no controlled A/B). *A bespoke paired `BenchmarkResult`
+ custom comparison markdown* — rejected (breaks `test_benchmark.py`, rewrites
`_summary_markdown`; the single-arm-twice structure gets the same honest same-grid
re-test for far less surface). *Compare betting only against the archived v0
`results.json`* — rejected (different process version; a same-run, same-grid A/B is
the honest object).

## Footprint

Files to add:
- `src/adaptive_compute/betting.py` — WSR hedged-capital betting CS: `betting_cs_bounds(values, *, alpha, grid_size=..., c=...) -> (lower, upper)` in Δ-space, input-validated (matching `empirical_bernstein_bounds`' contract), anytime-valid. Grid fine enough near `±δ` for `equivalent` resolution.
- `tests/test_betting.py` — deterministic validity mechanics (predictability; capital-process/martingale sanity), fixed-seed coverage sanity bound, rescale round-trip, drop-in stream equivalence, resolves-faster-than-EB on an `equivalent`-stratum case.
- `work/betting-cs-retest/results-eb.{md,json}`, `results-betting.{md,json}`, `comparison.md` — the A/B artifacts (generated by `eval --compare`).

Files to modify:
- `src/adaptive_compute/adaptive.py` — add `instrument: Literal["eb","betting"]` (keyword, default `"eb"`) to `adaptive_decision`, route to the chosen band; `empirical_bernstein_bounds` body and all other signatures/defaults unchanged.
- `tests/test_adaptive.py` — update `test_public_entry_is_blind`'s expected parameter tuple to include `instrument`, and assert its default is `"eb"` (adding the param changes `inspect.signature`; this test asserts the exact tuple).
- `src/adaptive_compute/benchmark.py` — parametrize `run_benchmark`/`_run_member_seed`/`_tune_params` by `instrument` (keyword, default `"eb"`, single-arm schema preserved); betting tunes `B_max` only (`b` fixed); apply A5 (`≤ α`) in the §7 verdict for both arms.
- `src/adaptive_compute/eval.py` — add a `--compare` flag that runs both arms, writes the two artifacts + `comparison.md` headline; `--check` gains a light betting determinism + resolves-`easy_lopsided` assertion. `--run` behavior and all EB-default `--check` assertions unchanged.
- `knowledge/anytime-valid-band.md` — add a "Betting CS (WSR)" section: construction, λ scheme, why it resolves smaller, and the re-test verdict; supersede the existing parenthetical forward-reference.

Files NOT to touch (live hazard — controlled-experiment constants):
- `src/adaptive_compute/bootstrap.py` — the stream and seed-branch semantics are the *held-constant* variable; any change confounds the A/B. The betting arm must consume the identical stream EB consumes (guaranteed only while `b` is fixed).
- `src/adaptive_compute/reference.py`, `generators.py`, `metrics.py`, `strata.py` — the reference labels, battery, and strata are fixed baselines.
- `work/adaptive-procedure/results.*` — released v0 artifact; do not relocate or overwrite.

## Acceptance criteria

- [ ] `betting_cs_bounds` returns a Δ-space `(lower, upper)`, validates inputs (non-empty 1-D, `alpha∈(0,1)`, values in `[-1,1]`) matching `empirical_bernstein_bounds`' contract, and clips to `[-1,1]`.
- [ ] **Deterministic validity (load-bearing):** `tests/test_betting.py` asserts (a) **predictability** — the bound at time `t` is unchanged when draws after `t` are permuted/altered (proves `λ_i` uses only `X_{<i}`); and (b) **capital sanity** — under a null stream centered at `m`, the wealth process `K_t(m)` has `E[K_t]≈1` / never triggers stopping beyond the `1/α` rate, checked on a fixed `SeedSequence`.
- [ ] **Coverage sanity (fixed-seed, hard bound):** on a named fixed `SeedSequence` and an explicit `N` seeds with a known bounded mean, observed CS miss count ≤ an explicit hard integer bound (chosen with margin, since betting is conservative) — a non-flaky sanity check, not the primary validity guarantee.
- [ ] **Drop-in equivalence (exact):** for a fixed seed and **fixed `b`**, `adaptive_decision(..., instrument="betting")` and `instrument="eb"` consume the identical bootstrap stream — asserted by `np.array_equal` on per-batch `deltas` at matched `draws_consumed` prefixes (only the band/decision differs).
- [ ] **Tighter-resolves-smaller on the stratum that mattered:** on an `equivalent`-stratum case (where the v0 negative lived, median 768 draws) at a matched seed and stream, betting reaches the correct `equivalent` decision in **strictly fewer draws** than EB. (An `easy_lopsided` case may be included too, but the `equivalent` case is required.)
- [ ] `adaptive_decision` default is unchanged (`instrument="eb"`), so `eval --check`'s existing EB assertions and the v0 reference/adaptive determinism all still pass; `git diff` shows `empirical_bernstein_bounds`' body unchanged. `tests/test_adaptive.py::test_public_entry_is_blind` updated to expect the new tuple with `instrument` defaulting to `"eb"`.
- [ ] `python -m adaptive_compute.eval --compare` writes `work/betting-cs-retest/results-eb.{md,json}`, `results-betting.{md,json}` (standard single-arm schema, same shared fixed-B grid), and `comparison.md` with a one-line headline verdict: does the ≥2× savings verdict flip under betting while §7 still holds? The released `work/adaptive-procedure/results.*` is not written or altered.
- [ ] §7/§8 pass logic is computed identically to v0 for both arms **except** A5's corrected `≤ α`; betting tunes `B_max` only over a candidate set including an entry `< 2048` (`b` fixed across arms), tuned on the tune split, reported on the test split.
- [ ] `eval --check` gains a betting determinism (int-seed replay) + resolves-`easy_lopsided`-before-`B_max` assertion; `bash scripts/gate.sh` exits 0.
- [ ] `knowledge/anytime-valid-band.md` documents the betting instrument and the recorded verdict; no claim beyond what the artifact shows.

## Release

Release note: Add a Waudby-Smith–Ramdas betting confidence-sequence band as a selectable adaptive instrument and re-run the §7/§8 gates under both bands over one shared bootstrap stream, testing whether the v0 empirical-Bernstein H1 savings negative survives a tighter anytime-valid instrument.

## Verification

- `bash scripts/gate.sh` (shellcheck + `ruff check` + `ruff format --check` + `mypy src` + `pytest -q` + `gate.d/` hooks incl. `eval --check`).
- `python -m adaptive_compute.eval --compare` then read `work/betting-cs-retest/comparison.md` — confirm both arms populated, betting median draws reported, headline verdict present and consistent with the two results tables.

## Review

Cold `plan-reviewer` (fresh read-only Opus subagent) — verdict **REVISE**, 5 findings + a statistics sanity note. The WSR construction was confirmed faithful and anytime-valid (no invalidating flaw). All findings accepted and applied:

1. **Batch tuning confounded the same-stream A/B.** Per-instrument tuning of `b` would shift `adaptive_bootstrap_stream`'s RNG call boundaries, so the arms would no longer consume an identical stream — breaking the attribution. **Applied:** `b` is now fixed across arms; only `B_max` is tuned per instrument.
2. **Adding `instrument` breaks `test_public_entry_is_blind` (exact-tuple assertion) → gate red.** Verified against `tests/test_adaptive.py:14-26`. **Applied:** added `tests/test_adaptive.py` to the footprint with a criterion to update the tuple + assert default `"eb"`.
3. **Dual-arm restructure would break `test_benchmark.py` and risked overwriting the released v0 artifact.** Verified against `tests/test_benchmark.py:12-26` and `benchmark.py:34-35,410-413`. **Applied (with finding 5):** keep single-arm `BenchmarkResult`, parametrize `run_benchmark` by `instrument`, write new `results-eb/-betting.*` under the unit's own dir via a new `--compare` flag; v0 `--run` path preserved untouched.
4. **Coverage criterion was stochastic/unpinnable.** **Applied:** validity now rests on two deterministic tests (predictability; capital/martingale sanity); MC coverage demoted to a fixed-seed hard-integer-bound sanity check.
5. **Simpler structure:** single-arm-run-twice against the shared fixed-B grid instead of a bespoke paired object. **Applied** (see finding 3).
6. **Stats note (b):** the v0 negative lived in the `equivalent` stratum, not `easy_lopsided`. **Applied:** the resolves-faster acceptance test now requires an `equivalent`-stratum case, and `betting.py`'s grid must be fine enough near `±δ` for `equivalent` resolution.

No disagreements to route to the Owner.

Plan verdict: **APPROVE** (post-revision)

### /3-review — implementation review (5 rounds)

Two cold reviewers per round: the integration `code-reviewer` (calibration anchor) and Codex (`codex-review.sh`).

- **R1** — both REQUEST CHANGES. Shared HIGH: the EB arm re-tuned off v0's `B_max=2048`, and `eval --run` would overwrite the protected v0 artifact with divergent numbers. Plus two vacuous validity tests (predictability, drop-in stream equivalence) and a headline mislabel. Codex also raised a grid-inversion HIGH; the anchor cleared the WSR construction as sound and anytime-valid, so it was **deferred** (see `deferrals.md` D-grid: keep the grid method + a `ponytail:` comment; empirically 0 false stops over ~8000 seeds).
- **R2** — both APPROVE. One MEDIUM remained: the knowledge doc misreported the EB baseline medians (`704/384` → corrected to `768/448`, matching the artifact).
- **R3** — anchor APPROVE; Codex REQUEST CHANGES (HIGH), re-raising that the global `DEFAULT_BATCH` change altered the default `--run`/EB tuning procedure. Owner consulted (open HIGH at the round cap): chose to fix for a genuine dual-APPROVE.
- **R4** — anchor APPROVE (3rd consecutive); Codex REQUEST CHANGES (HIGH) that *contradicted* its R3 ask (now objecting to `b=32` being in the EB set). Root cause: a single shared EB candidate set can't serve both `--run` (needs v0's set) and `--compare` (needs `b=64` pinned). Owner authorized the decoupling fix.
- **R5** — **both APPROVE.** Decoupled EB tuning via an optional `candidates` override: `--run` keeps v0's default set (reproduces v0); `--compare`'s EB arm passes explicit `b=64` candidates, enforcing the A/B invariant in code. Numbers unchanged (EB 128/768/448, betting 64/192/128, NO flip). Residual LOWs (cosmetic `b=32` literal vs `DEFAULT_BATCH` symbol; A5 measure-zero edge) recorded, non-blocking.

Gate green (188 shell + 49 pytest + ruff/mypy/`eval --check`) on the orchestrator's own run every round. Footprint clean throughout; released v0 `work/adaptive-procedure/results.*` never altered (empty diff).

Code-review verdict: APPROVE
Codex-review verdict: APPROVE
