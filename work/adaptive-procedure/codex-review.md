**Findings**
- MEDIUM: `eval --check` draw accounting no longer preserves the pre-unit reference draw count. The plan explicitly requires the existing reference draw count to stay bit-identical, but `total_draws` now includes adaptive runs and hard-member MCSE diagnostics in addition to the old reference draws (`src/adaptive_compute/eval.py`). Track/report/assert the reference subtotal separately.

- MEDIUM: D1 is implemented too broadly for invalid original datasets. `_resample_deltas` returns all-zero deltas when the original `y` has only positives or only negatives, silently treating an invalid evaluation set as “equivalent” (`src/adaptive_compute/bootstrap.py`). D1 only calls for degenerate bootstrap resamples from otherwise valid data to map to `Δ*=0`; the original input should still require both classes.

- LOW: The H1 CI gate uses strict `< DEFAULT_ALPHA` while the acceptance criterion says upper CI `≤ α` (`src/adaptive_compute/benchmark.py`). This only matters at the exact boundary, but the artifact wording also says `< alpha`, so it is worth aligning.

No CRITICAL/HIGH blockers found.

Codex verdict: APPROVE
