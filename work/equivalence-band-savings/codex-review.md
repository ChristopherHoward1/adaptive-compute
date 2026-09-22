No CRITICAL or HIGH findings.

MEDIUM: `src/adaptive_compute/equiv_probe.py` in `run_and_write_probe` recomputes the resolvability precheck separately for each deep:shallow ratio. Because each precheck can select a different `shallow_abs_delta`, the “stability across ratios” check is not purely varying mixture ratio; it may also vary shallow-case difficulty. That weakens the acceptance criterion, though it does not obviously invalidate the submitted result.

MEDIUM: `run_probe` summarizes only `scored_equivalent` runs, so any non-equivalent or unresolved primary cases are dropped before `_summarize_stratum`. The production path’s precheck appears intended to prevent this for shallow cases, but the JSON/verdict do not preserve the original denominator, so a future fixture regression could look like a smaller clean scored set unless separately caught.

Overall, the implementation stays within the declared footprint, leaves released paths alone, reuses `_summarize_stratum`, `fixed_b_sweep`, and `pareto_verdict`, and has no blocking correctness issue that I can substantiate from the diff.

Codex verdict: APPROVE
