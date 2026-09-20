# Adaptive Procedure First Result

Verdict: **H1 NEGATIVE RESULT**.

Tuned on 24 seeds/member; tested on 500 seeds/member with b=32, alpha=0.05, B_max=320.

| stratum | scored | false-stop rate | 95% CI | draws p50/p90/p99 | abstain | ref unresolved | fixed-B dominating adaptive |
| --- | ---: | ---: | --- | --- | ---: | ---: | --- |
| easy | 514 | 0.0000 | [0.0000, 0.0074] | 128/160/284 | 0.0000 | 0 | 32, 64 |
| equivalent | 500 | 0.0000 | [0.0000, 0.0076] | 320/320/320 | 1.0000 | 1 | 32, 64, 128 |
| moderate | 943 | 0.0000 | [0.0000, 0.0041] | 320/320/320 | 0.9827 | 42 | 32, 64, 128 |

## Heavy-Tailed Check

Realized false-stop rate: 0.0000

## Pareto Savings

A fixed-B entry listed in the table has lower median draws and false-stop rate no higher than adaptive in that stratum; `none` means no fixed-B grid point dominated the adaptive run.

H1 requires both the per-stratum false-stop CI check and no fixed-B dominator; a listed fixed-B dominator makes this a negative result.
