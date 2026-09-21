# Adaptive Procedure First Result

Verdict: **H1 NEGATIVE RESULT**.
False-stop test (§7): PASS in every non-boundary stratum (all upper CIs <= alpha). Savings/Pareto (§8): FAIL (no adaptive-dominated fixed-B at >=2x in every stratum). Therefore H1 is unsupported on the savings criterion.

Tuned on 24 seeds/member; tested on 2000 seeds/member with b=64, alpha=0.05, B_max=2048.

| stratum | scored | false-stop rate | 95% CI | draws p50/p90/p99 | abstain | ref unresolved | fixed-B unresolved | adaptive dominates fixed-B | fixed-B dominates adaptive | best savings |
| --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- | ---: |
| easy | 2054 | 0.0000 | [0.0000, 0.0019] | 128/128/256 | 0.0000 | 0 | 32:0.000, 64:0.000, 128:0.000, 320:0.000 | 320 | 32, 64 | 2.50x |
| equivalent | 2000 | 0.0000 | [0.0000, 0.0019] | 768/896/1088 | 0.0000 | 1 | 32:0.000, 64:0.000, 128:0.000, 320:0.000 | none | 32, 64, 128, 320 | 0.00x |
| moderate | 3749 | 0.0000 | [0.0000, 0.0010] | 448/704/1446 | 0.0000 | 193 | 32:0.009, 64:0.007, 128:0.007, 320:0.007 | none | none | 0.00x |

## Heavy-Tailed Check

Realized false-stop rate: 0.0000

## Pareto Savings

Fixed-B decisions use an independent bootstrap stream from adaptive. Unresolved fixed-B intervals and adaptive abstentions are accounted for symmetrically in the Pareto comparison.

H1 requires the per-stratum false-stop CI check, no fixed-B dominator, and at least 2x median-draw savings from an adaptive-dominated fixed-B in every non-boundary stratum.
