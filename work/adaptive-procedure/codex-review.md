**Findings**

HIGH: [src/adaptive_compute/adaptive.py:113](/Users/cboyfly/Documents/repos/adaptive-compute/src/adaptive_compute/adaptive.py:113) drops valid terminal decisions at `B_max`.

`adaptive_decision` only returns a resolved decision when `decision is not None and draws < b_max`. If the confidence sequence first resolves on the final allowed batch, the function falls through and returns `abstain`. That violates the stopping contract: `abstain` should mean unresolved at `B_max`, not “resolved exactly at `B_max`.” A realistic repro is any strong case with `b == b_max`: the only check occurs at the terminal budget and is discarded.

HIGH: [src/adaptive_compute/benchmark.py:190](/Users/cboyfly/Documents/repos/adaptive-compute/src/adaptive_compute/benchmark.py:190) and [src/adaptive_compute/sweep.py:108](/Users/cboyfly/Documents/repos/adaptive-compute/src/adaptive_compute/sweep.py:108) let unresolved fixed-B baselines dominate adaptive.

The fixed-B false-stop rate treats `"unresolved"` as “not false,” and `pareto_verdict` then declares any smaller fixed budget with `fixed_rate <= adaptive_rate` a dominator. A tiny fixed-B that never makes a decision can therefore get false-stop rate `0.0` and dominate adaptive purely by abstaining, which silently corrupts the Pareto/savings comparison and can flip the reported H1 verdict. The benchmark needs to either exclude unresolved fixed-B decisions from domination, account for their unresolved/abstain rate, or otherwise require a comparable resolved-decision surface.

Codex verdict: REQUEST CHANGES
