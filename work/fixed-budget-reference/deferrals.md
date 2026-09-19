# Accepted deferrals — fixed-budget-reference

Settled scope from review. Do not re-raise as findings against this unit; each names where it lands.

## D1 — Degenerate bootstrap resample (zero positives or zero negatives) crashes AUC

- **Raised (round 1, code-reviewer MEDIUM):** `metrics.auc()` raises `ValueError`
  ("AUC requires at least one positive and one negative label") if a bootstrap
  resample happens to draw all-positive or all-negative rows. `bootstrap.py`
  has no degenerate-resample guard, so the whole reference / `--check` run would
  crash on such a draw.
- **Why deferred:** at this unit's committed generator params the probability is
  ~7e-10 per resample (`rare_event_imbalance`: n=520, ~21 positives), so it never
  bites, and every run here is deterministic and seeded. It becomes real only if a
  future caller lowers `n` or the positive count.
- **Where it lands:** the **adaptive procedure unit** (`experiment-design.md` §3),
  which owns batch/small-budget behavior and will reuse `bootstrap.py`. It must
  define the degenerate-resample policy (guard + clear error, rejection-resample,
  or a defined AUC=0.5 for a degenerate draw) so the choice is made where
  small-budget batches make it observable — not bolted onto the reference now.
