# Accepted deferrals — adaptive-procedure

Settled scope from the `/3-review` rounds (all LOW, non-blocking; dual APPROVE round 3).
Do not re-raise as findings against this unit; each names where it lands.

## A1 — Bootstrap conflates an INVALID single-class original eval set with a degenerate RESAMPLE

- **Raised (round 3, Codex MEDIUM → code-reviewer LOW):** `bootstrap.py` short-circuits an
  all-positive/all-negative *original* evaluation set to `Δ*=0` (the D1 degenerate-resample
  policy), rather than raising the way a malformed input should. D1 only intended a degenerate
  *bootstrap resample* drawn from otherwise-valid data to map to `Δ*=0`; an invalid original set
  (one class) should still raise.
- **Why deferred:** not reachable as a silent wrong result in the pipeline — `benchmark._run_member_seed`
  computes `plugin_delta = delta(...)` first, and `metrics.auc` raises on a single-class set before
  bootstrap is ever called; every generator produces both classes by construction (`_labels` guarantees
  ≥1 positive and ≤ n−1). Latent, not live. D1's own acceptance criterion is met.
- **Where it lands:** the next unit that touches `bootstrap.py` input validation (or a small
  reference-hardening unit). Fix: distinguish an invalid single-class *original* set (raise) from a
  degenerate *resample* of a valid set (→ Δ*=0), so the reference path never silently scores an invalid
  eval set as `equivalent`.

## A2 — D1 unit test exercises only the original-set short-circuit, not the per-resample path

- **Raised (round 3, code-reviewer LOW):** `test_degenerate_resample_counts_as_zero_delta_draw`
  passes `y=[1,1,1]`, hitting the `pos_count==0` original-set branch — not the actual D1 scenario
  (a mixed original set where a specific *resample* happens to pick one class, hitting the
  per-resample `denominators>0` guard). That path is correct by construction but unasserted.
- **Why deferred:** the behavior is correct and exercised indirectly by the full `--run`; only the
  direct unit assertion is missing. Latent test-coverage gap, not a defect.
- **Where it lands:** whenever `tests/test_bootstrap.py` is next touched — add a seeded case whose
  resample draws a single class from a two-class original set.

## A3 — Fixed-B sweep grid top entry equals `DEFAULT_B_REF` (320)

- **Raised (round 3, code-reviewer LOW):** `FIXED_B_GRID`'s largest member is `B_ref` itself; §4
  describes the sweep's large member as "short of `B_ref`".
- **Why deferred:** does not affect the H1 NEGATIVE conclusion — the smaller fixed budgets already
  dominate / are non-dominated, and adaptive's median draws exceed the whole grid regardless.
- **Where it lands:** the next benchmark/sweep tuning unit; set the top grid entry strictly below `B_ref`.

## A4 — `eval --check` printed draw total folds adaptive + diagnostic draws into the reference total

- **Raised (round 3, Codex MEDIUM → code-reviewer LOW):** the reference sub-computations are
  byte-identical to pre-unit (verified: max abs diff 0.0), but the aggregate `total_draws` the check
  prints now includes adaptive-coverage and hard-member-MCSE draws, so the *printed* total is not the
  old reference-only number. No test pins the aggregate, so nothing breaks.
- **Why deferred:** cosmetic/reporting only; the reference invariance that matters (byte-identical
  deltas) holds and is asserted. Latent.
- **Where it lands:** the next `eval.py` unit — track and print the reference draw subtotal separately
  if the number is ever consumed downstream.

## A5 — H1 false-stop CI gate uses strict `<` where the criterion says `≤ α`

- **Raised (round 3, Codex LOW):** `benchmark.py` (and the artifact wording) compares the upper CI
  with strict `< DEFAULT_ALPHA`; the plan/§7 criterion is `≤ α`. Matters only at the exact boundary.
- **Why deferred:** realized upper CIs (~0.002) sit far below α; the boundary is never hit.
- **Where it lands:** align to `≤ α` the next time the verdict logic is touched.

## Noted (no future work) — footprint

`tests/test_reference.py` was modified outside the plan's declared test-file list, in service of the
accepted D2 diagnostic assertion (`reference.py` source itself untouched). Recorded as a deliberate,
legitimate footprint addition; no action required.
