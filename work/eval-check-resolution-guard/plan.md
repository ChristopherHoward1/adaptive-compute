# eval --check equivalence-resolution guard

**Slug:** eval-check-resolution-guard · **Date:** 2026-10-09 · **Status:** approved

## Goal

`work/adaptive-procedure/retro.md` (Q1) records that the gate let a vacuous result through. Round 1 abstained about 100% of the time on the hard strata, because every benchmark tuning candidate had `b_max = DEFAULT_B_MAX = 320` (`git show 0401b00:src/adaptive_compute/benchmark.py`, around lines 164–165), and that budget was too small for the EB boundary to stop. The retro named this unit to make `eval --check` catch the failure in the gate instead of leaving it to cold review.

The existing `_check()` guard cannot do that, for two reasons:
- **Wrong member.** It uses `easy_lopsided`. That case is directional with Δ≈0.39, so it resolves even under a band too loose to certify equivalence. On the current code at `b=64, b_max=320`, EB resolves it as `A_better` at 128 draws.
- **Wrong budget.** It uses the fixed constant `CHECK_ADAPTIVE_B_MAX = 1024`, so it never sees the benchmark's B_max, which is the setting R1 actually got wrong. The plan-reviewer checked this against R1's original boundary (from `0401b00`): a guard fixed at 1024 still certifies `small_effect` at 832 draws and passes.

Done means: `eval --check` fails when, for either instrument, even the largest default tuning candidate cannot certify the low-variance equivalence member `small_effect` within its own `b_max`. `small_effect` is the battery's only `equivalent`-stratum member, with Δ≈−0.0006. A test must show that `_check()` returns 1 under the R1 grid, where every candidate has `b_max=320`.

## Approach

- **`src/adaptive_compute/benchmark.py`, constant move only, no behavior change.** Move the default candidates out of `_tune_params` (currently lines 176–186) into a module-level mapping such as `DEFAULT_CANDIDATES: dict[AdaptiveInstrument, tuple[AdaptiveParams, ...]]`, with:
  - EB: `(32, 1024)` and `(64, 2048)`.
  - Betting: `(64, b_max)` for `b_max` in `(128, 256, 512, 1024)`.

  `_tune_params` reads the defaults from the mapping when `candidates is None`.
- **`src/adaptive_compute/eval.py`.** Add a helper, for example `_equivalence_guard() -> tuple[str | None, int]`, that returns a failure message (or `None`) and the draws consumed. For each instrument in `("eb", "betting")`:
  - Take the candidate with the largest `b_max` from `DEFAULT_CANDIDATES[instrument]`.
  - Run `adaptive_decision` on `BATTERY["small_effect"]` with that candidate's `b`, `alpha` and `b_max`, plus `instrument=instrument`, `margin=DEFAULT_DELTA` and `seed=12345`. If `instrument=` is omitted, the betting arm silently runs EB.
  - Pass only if `decision == decision_from_delta(plugin Δ, DEFAULT_DELTA)` (that is, `"equivalent"`) **and** `draws_consumed < b_max`.

  Read `DEFAULT_CANDIDATES` through the module attribute (`benchmark.DEFAULT_CANDIDATES`) so a test can monkeypatch it.
- **Call the guard first in `_check()`**, before the battery loop that takes about 44 s. The guard costs about 0.03 s. On failure, print `adaptive (<instrument>) did not certify small_effect equivalence before B_max=<n>` to stderr and return 1. Add the guard's draws to `total_draws`.
- **Detectability test** (`tests/test_eval_check.py`): monkeypatch `DEFAULT_CANDIDATES` to the R1 grid (every candidate `b_max=320`, same `b` values). Call `_check()` and assert it returns 1 and that the EB message appears in stderr, captured with `contextlib.redirect_stderr(io.StringIO())` to match `tests/test_determinism.py`. Do not use `capsys`: it errors under `-p no:capture`, and the gate's retry runs pytest that way. This one test covers the "can fail" requirement, the failure-path return value, and the link between the guard and the benchmark grid (`knowledge/controlled-retest-discipline.md`: guard-tests that can actually fail).
- **Betting-branch test:** a second case patches only the betting entry to `(64, 128)`, keeps the EB defaults, and asserts `_check()` returns 1 with `adaptive (betting) did not certify` in stderr. With betting's `small_effect` run needing 192 draws, a 128 limit forces the failure. This shows the betting branch can fail too.
- The existing `easy_lopsided` guard stays unchanged. It covers the directional path and the determinism checks.

Alternatives considered:
- Anchor to the fixed `CHECK_ADAPTIVE_B_MAX`. Rejected: it does not catch R1 (finding 1 above).
- Assert at *every* candidate. Rejected: betting `b_max=128` is a legitimate candidate, but betting needs 192 draws on `small_effect`.

Known scope limit: `--compare` passes its own explicit EB candidates, `(64, 2048)` and `(64, 1024)`. The guard covers the defaults used by `--run` / `run_benchmark()`. `--compare` is not covered, and that is accepted.

Also accepted: the guard checks only the largest-`b_max` candidate, on one member and one seed. It would not catch a tuner that selects a smaller candidate which always abstains. That gap is narrow, because the tuner scores `(false_rate, abstain_rate, median_draws)`, so a candidate that abstains more loses unless it lowers the false-stop rate. Closing the gap would mean running the tuner inside the gate.

A dict lookup raises `KeyError` for an instrument that is neither `"eb"` nor `"betting"`, where today such a value falls through to the betting defaults. This is unreachable for type-correct callers, since `AdaptiveInstrument` is `Literal["eb", "betting"]`.

## Footprint

Files to modify:
- `src/adaptive_compute/benchmark.py`: move the default candidates into a module-level constant. No behavior change.
- `src/adaptive_compute/eval.py`: add the guard helper and call it at the top of `_check()`.
- `tests/test_eval_check.py` (new): the R1-grid (EB) and betting `(64, 128)` detectability tests.

Files NOT to touch:
- `src/adaptive_compute/adaptive.py`, `betting.py`, `generators.py`: the guard must test the instruments and battery as they are.
- Released results under `work/*/results*`.

## Acceptance criteria

- [ ] On `main` (663756c), `eval --check` prints `draws_consumed=7760`. On the branch it exits 0 and prints `7760 + guard draws`. Today the guard draws are 704 (EB `64/2048`) + 192 (betting `64/1024`) = 896, so the expected total is `draws_consumed=8656`.
- [ ] `tests/test_eval_check.py` monkeypatches `DEFAULT_CANDIDATES` to the R1 grid (`b_max=320`), and asserts `_check()` returns 1 and stderr (captured via `contextlib.redirect_stderr`, not `capsys`) contains `adaptive (eb) did not certify small_effect equivalence`.
- [ ] The guard compares against `decision_from_delta(...)`, not just `!= "abstain"` (diff inspection).
- [ ] The guard reads the largest-`b_max` candidate per instrument from `benchmark.DEFAULT_CANDIDATES`. It must not use `CHECK_ADAPTIVE_B_MAX` (diff inspection).
- [ ] A second case in `tests/test_eval_check.py` patches only betting to `(64, 128)` and asserts `_check()` returns 1 with `adaptive (betting) did not certify` in stderr.
- [ ] The guard passes `instrument=instrument` to `adaptive_decision` (diff inspection; the 8656 total also pins it).
- [ ] `_tune_params` uses `DEFAULT_CANDIDATES[instrument]` when `candidates is None`, and no candidate tuples remain inline in `_tune_params` (diff inspection). This keeps the guard and the real tuner reading the same grid.
- [ ] The `benchmark.py` change only moves the constant. The existing `tests/test_benchmark.py` passes unmodified, and `git diff` of `benchmark.py` is limited to the new constant's definition and the `candidates is None` branch of `_tune_params`.
- [ ] No files in the "NOT to touch" list change (`git diff --stat`).
- [ ] `scripts/gate.sh` exits 0.

## Release

Release note: `eval --check` now fails if either adaptive instrument's largest default tuning candidate cannot certify the equivalence-stratum member within its `b_max`, so a tuning grid sized too small to ever stop (the adaptive-procedure R1 failure) is caught by the gate.

## Verification

- `PYTHONPATH=src python -m adaptive_compute.eval --check` (expect `draws_consumed=8656`)
- `pytest -q tests/test_eval_check.py tests/test_benchmark.py`

## Review

Round 1 (plan-reviewer): REVISE. All five findings applied, none disputed:
1. Anchor the guard to the benchmark's largest default candidate, not `CHECK_ADAPTIVE_B_MAX`. The reviewer showed the fixed-1024 guard passes under R1's original boundary (832 < 1024). `benchmark.py` moves into the footprint for a constant move only.
2. The detectability test monkeypatches the real anchor (the R1 grid), not a hand-picked `b_max`.
3. The guard goes at the top of `_check()`, so the "returns 1" criterion is a cheap pytest instead of diff inspection.
4. Draw counts corrected (640 at 64/1024; 704 at 32/1024 and 64/2048). Baseline `draws_consumed=7760` recorded.
5. Verdict line left for the re-review; the `total_draws` accounting is now its own criterion.

Round 2 (fresh plan-reviewer): REVISE. It confirmed the baseline of 7760, the draw counts (+896, total 8656), that the R1 grid of `32/320` and `64/320` makes EB abstain so the guard fails, and that the round-1 findings were applied correctly. All findings applied:
1. Capture stderr with `contextlib.redirect_stderr`, not `capsys`. `capsys` errors under the gate's `-p no:capture` retry (`scripts/gate.sh:42`).
2. Added a criterion that `_tune_params` reads `DEFAULT_CANDIDATES`. Without it, the guard and the tuner could drift apart and R1 could happen again.
3. and 4. The `KeyError` edge case and the largest-candidate-only scope limit are both recorded as accepted under Approach.

Round 3 (fresh plan-reviewer): APPROVE, with three non-blocking findings, all applied as revision 4:
1. Pass `instrument=instrument` explicitly.
2. Add a betting-branch failure case `(64, 128)`, because the R1 grid only exercises EB.
3. Word the `benchmark.py` diff criterion to cover the constant plus the `candidates is None` branch.

Round 4 (fresh plan-reviewer): APPROVE of revision 4. It re-ran every guard case: EB 64/2048 passes at 704; betting 64/1024 passes at 192; the R1 grid fails EB at 320; betting 64/128 fails at 128; the total is 8656. Two optional findings are left to the implementer. The plan body above is unchanged, so this verdict covers the text above:
- An optional fast pass-path case: call the guard helper on the unpatched defaults and expect `(None, 896)`.
- Patch with `monkeypatch.setattr(benchmark, "DEFAULT_CANDIDATES", {...})`, never by mutating the dict in place, so the R1 grid does not leak into `test_benchmark.py`.

Plan verdict: APPROVE

