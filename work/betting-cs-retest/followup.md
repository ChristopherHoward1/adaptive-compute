Resuming in the SAME worktree on branch wt/betting-cs-retest. Round-3 review split: the integration reviewer APPROVED, but Codex re-raised one HIGH about the default `eval --run` path. The Owner has authorized one more scoped fix round to resolve it cleanly. Fix the items below, stay in the plan footprint, re-run `scripts/gate.sh` until green, run `python -m adaptive_compute.eval --compare`, commit, and print an updated summary.

## REQUIRED — make the default `--run` / EB path provably unchanged from v0 (Codex HIGH)

The problem: you set the GLOBAL `DEFAULT_BATCH = 64` and narrowed the EB `_tune_params` candidate set, so `python -m adaptive_compute.eval --run` (→ `run_and_write_results` → `run_benchmark(instrument="eb")`, which writes the PROTECTED `work/adaptive-procedure/results.*`) now uses an altered tuning search space. Even though it happens to land on v0's selection, the default `--run` procedure must be byte-for-byte the v0 procedure (except the accepted A5 `<= alpha` verdict wording). The batch-fixing belongs to the A/B comparison, not the global default.

Do this:
1. **Restore `DEFAULT_BATCH = 32`** (its v0 value).
2. **Restore the EB arm's `_tune_params` candidate set to v0's exact pair:** `AdaptiveParams(b=32, alpha=DEFAULT_ALPHA, b_max=1024)` and `AdaptiveParams(b=64, alpha=DEFAULT_ALPHA, b_max=2048)`. This makes `run_benchmark(instrument="eb")` — and thus `--run` — reproduce v0's tuning search and selection (it deterministically selects `b=64, B_max=2048`, medians 128/768/448) exactly as before.
3. **Pin the BETTING arm to `b=64` explicitly** (do NOT rely on `DEFAULT_BATCH`, which is now 32): betting `_tune_params` candidates = `b=64` with its own `B_max` set (e.g. 128/256/512/1024). Betting must stay at `b=64`.

Why this is still a valid controlled A/B: in `--compare`, the EB arm's tune deterministically selects `b=64, B_max=2048` from v0's candidate set (as v0 did — verify it still does), and the betting arm is pinned to `b=64`. So BOTH arms run at `b=64` (shared stream preserved, attribution intact), while the default `--run`/EB path is provably the v0 procedure again.

**Verify after the fix:**
- `git diff origin/main...wt/betting-cs-retest -- src/adaptive_compute/benchmark.py` shows `DEFAULT_BATCH` back at 32 and the EB candidate set identical to origin/main's (only the instrument-branch for betting + the A5 `<= alpha` change remain as diffs).
- `work/betting-cs-retest/results-eb.md` still shows tuned `b=64, B_max=2048`, medians 128/768/448 (unchanged).
- `work/betting-cs-retest/results-betting.md` still shows `b=64`, `B_max=512`, medians 64/192/128 (unchanged).
- `git diff origin/main...wt/betting-cs-retest -- work/adaptive-procedure/` is EMPTY (never regenerate/commit the v0 artifact).
- `comparison.md` headline unchanged: NO flip, §7 held, savings still fail in the equivalent stratum.

## CHEAP — clear the two LOW findings while you're here

4. **Remove the redundant/misordered `COMPARE_DIR.mkdir(...)` in `eval.py::_compare`** — it runs AFTER the `write_results(...)` calls that already create the dir (and `write_results` does its own parent mkdir). Just delete the dead line (or move it before the writes if you prefer a guard; deletion is fine since the committed dir exists).
5. **De-tautologize the F-C drop-in stream-equivalence test** (`tests/test_betting.py`): the `np.array_equal(eb_consumed[:matched], betting_consumed[:matched])` compares two slices of the SAME reconstructed array, so it is always true. The real proof is already the two adjacent `_replay_decision(replayed, ...) == (run.decision, run.draws_consumed)` assertions (they tie each live arm to the one shared stream). Remove the decorative self-comparison, or make it meaningful by asserting each arm's replayed consumed-prefix equals the shared stream's prefix (`np.array_equal(replayed[:run.draws_consumed], shared_prefix)`). Keep the replay-decision equalities as the load-bearing assertions.

## DO NOT change — settled deferral (work/betting-cs-retest/deferrals.md)
The betting-CS grid-hull inversion (D-grid) is settled; keep the grid method and its `ponytail:` comment. Do not implement continuous inversion.

## When done
1. `scripts/gate.sh` passes (exit 0).
2. `python -m adaptive_compute.eval --compare` regenerates the four artifacts; confirm the EB (128/768/448) and betting (64/192/128) numbers are unchanged and v0 is untouched.
3. Commit on wt/betting-cs-retest. Print a per-item summary and restate the headline (unchanged: no flip).
