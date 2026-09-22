Resuming in the SAME worktree on branch wt/betting-cs-retest. Owner-authorized fix round. One well-defined architectural change, plus keep everything else exactly as it is.

## The problem to fix

Right now a SINGLE EB tuning candidate set is shared by two entry points with conflicting requirements, so it can't satisfy both:
- `eval --run` (→ `run_and_write_results` → `run_benchmark(instrument="eb")`, writes the PROTECTED `work/adaptive-procedure/results.*`) must reproduce v0's tuning search **exactly** — v0's EB candidates include `b=32` and `b=64`.
- `eval --compare`'s EB arm must have `b` **pinned to 64** (the controlled A/B requires both arms at the same batch size so they consume the identical bootstrap stream; today it only *happens* to select b=64, it isn't enforced).

The fix is to **decouple** these two so each gets the candidate set it needs.

## REQUIRED — decouple EB tuning between `--run` and `--compare`

1. **Add a candidate-set override parameter** to the tuning path so a caller can supply explicit `AdaptiveParams` candidates instead of the instrument default. Suggested shape (adapt names to the code):
   - `_tune_params(n_tune, *, instrument="eb", candidates=None)` — if `candidates` is provided, tune over exactly those; otherwise fall back to the current instrument-default set.
   - `run_benchmark(*, n_tune=DEFAULT_N_TUNE, n_test=DEFAULT_N_TEST, instrument="eb", candidates=None)` — passes `candidates` through to `_tune_params`.
2. **Leave the DEFAULT (`--run`) path untouched:** with `candidates=None`, the EB default set stays v0's exact pair `{AdaptiveParams(b=32,...,b_max=1024), AdaptiveParams(b=64,...,b_max=2048)}`, and `DEFAULT_BATCH` stays `32`. `run_and_write_results`/`_run` must remain diff-free except that they already were. So `eval --run` reproduces v0 byte-for-byte (except the accepted A5 wording), and the protected artifact is never altered.
3. **In `_compare`, pin the EB arm to b=64** by passing explicit candidates: `run_benchmark(instrument="eb", candidates=(AdaptiveParams(b=64, alpha=DEFAULT_ALPHA, b_max=1024), AdaptiveParams(b=64, alpha=DEFAULT_ALPHA, b_max=2048)))`. The betting arm stays as it is (already b=64-pinned over B_max {128,256,512,1024}). Now BOTH `--compare` arms are b=64 by construction — the A/B invariant is enforced in code, not lucky.
4. **Keep the comparison numbers identical:** the b=64-pinned EB arm still tunes to `B_max=2048` (128/768/448); betting still `B_max=512` (64/192/128); headline still NO flip. If any number changes, stop and explain — it shouldn't.

## Verify after the fix
- `git diff origin/main...wt/betting-cs-retest -- src/adaptive_compute/benchmark.py`: the EB DEFAULT candidate set and `DEFAULT_BATCH=32` are identical to origin/main; the only new EB-side surface is the optional `candidates` parameter (default `None` = old behavior) plus the accepted A5 `<= alpha`.
- `git diff origin/main...wt/betting-cs-retest -- work/adaptive-procedure/` is EMPTY.
- `python -m adaptive_compute.eval --compare` regenerates artifacts: EB `b=64, B_max=2048`, medians 128/768/448; betting `b=64, B_max=512`, medians 64/192/128; `comparison.md` headline unchanged (NO flip, §7 held, savings fail in equivalent stratum).
- `python -m adaptive_compute.eval --run` (you may run it in a scratch copy to confirm behavior, but DO NOT commit any regenerated `work/adaptive-procedure/results.*`) still tunes EB over v0's set including b=32.
- `scripts/gate.sh` exits 0.

## DO NOT change
- The WSR betting CS / `BettingCSState` logic, the grid method (settled deferral D-grid), the betting arm's candidates, the F-C/F-B tests, or anything outside the plan footprint. This is only the EB-tuning decoupling.

## When done
1. Gate passes (exit 0); `--compare` artifacts regenerated with unchanged numbers; v0 artifact untouched.
2. Commit on wt/betting-cs-retest with a clear message.
3. Print a summary: the decoupling change, confirmation that `--run` EB default == v0 set and `--compare` EB arm is b=64-pinned, and the unchanged headline.
