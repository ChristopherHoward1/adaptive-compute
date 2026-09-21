# Betting-CS Re-test Comparison

Headline verdict: **NO** — betting savings_pareto_pass did not flip because savings still failed (§7 held).

| arm | false_stop_test_pass | savings_pareto_pass | h1_holds | b | B_max |
| --- | ---: | ---: | ---: | ---: | ---: |
| EB | True | False | False | 64 | 2048 |
| Betting | True | False | False | 64 | 512 |

Both arms use the shared fixed-B grid and fixed adaptive batch size b=64.
