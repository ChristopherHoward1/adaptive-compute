# Adaptive Procedure First Result

Verdict: **H1 NEGATIVE RESULT**.

Tuned on 24 seeds/member; tested on 500 seeds/member with b=64, alpha=0.05, B_max=2048.

| stratum | scored | false-stop rate | 95% CI | draws p50/p90/p99 | abstain | ref unresolved | fixed-B unresolved | adaptive dominates fixed-B | fixed-B dominates adaptive | best savings |
| --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- | ---: |
| easy | 514 | 0.0000 | [0.0000, 0.0074] | 128/128/256 | 0.0000 | 0 | 32:0.000, 64:0.000, 128:0.000, 320:0.000 | 320 | 32, 64 | 2.50x |
| equivalent | 500 | 0.0000 | [0.0000, 0.0076] | 768/960/1152 | 0.0000 | 1 | 32:0.000, 64:0.000, 128:0.000, 320:0.000 | none | 32, 64, 128, 320 | 0.00x |
| moderate | 943 | 0.0000 | [0.0000, 0.0041] | 448/704/1162 | 0.0000 | 42 | 32:0.007, 64:0.003, 128:0.006, 320:0.008 | none | none | 0.00x |

## Heavy-Tailed Check

Realized false-stop rate: 0.0000

## Pareto Savings

Fixed-B decisions use an independent bootstrap stream from adaptive. Unresolved fixed-B intervals and adaptive abstentions are accounted for symmetrically in the Pareto comparison.

H1 requires the per-stratum false-stop CI check, no fixed-B dominator, and at least 2x median-draw savings from an adaptive-dominated fixed-B in every non-boundary stratum.
