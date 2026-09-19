**Findings**

HIGH — [src/adaptive_compute/reference.py:35] `fixed_budget_reference` can return a decision that is not read from the percentile interval. `_decision_from_interval` falls back to `decision_from_delta(estimate, margin)` when the interval overlaps a decision boundary. For example, with `margin=0.05`, interval `(0.03, 0.07)`, estimate `0.06`, it returns `A_better` even though the interval is not wholly above `+δ`. The plan makes the percentile interval load-bearing: above `+δ`, below `-δ`, or wholly within `[-δ,+δ]`. Since the reference has no `abstain`, this inconclusive interval case needs an explicit plan-consistent rule rather than a point-estimate fallback.

HIGH — [src/adaptive_compute/eval.py:20] `python -m adaptive_compute.eval --check` does not check the boundary `B_ref` sizing/MCSE condition. The acceptance criteria say `--check` exits non-zero if determinism, recovery, or sizing fails, but `_check()` only verifies replay and known-decision recovery. The MCSE assertion exists only in pytest. That means the wired `EVAL_COMMAND` can pass while one of its stated failure modes is broken.

LOW — [pyproject.toml:25] `addopts = "-p no:capture"` is outside the declared pyproject change. The plan only calls for adding `numpy` and explicitly says to keep tool config as-is. This is probably just to surface MCSE diagnostics, but it changes global pytest behavior and is scope creep under the implementer contract.

Codex verdict: REQUEST CHANGES
