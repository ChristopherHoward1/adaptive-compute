**Findings**

**HIGH** [src/adaptive_compute/benchmark.py](src/adaptive_compute/benchmark.py): `_tune_params(instrument="eb")` still treats `b` as a tuning dimension by including `AdaptiveParams(b=32, ...)` alongside `b=64`. The plan’s load-bearing A/B condition says `b` must be pinned to `64` for both arms so the bootstrap RNG call boundaries match and only the band changes. Even if the current generated artifact happened to pick `b=64`, this code can select `b=32` under a different tune split/sample count and silently invalidate the same-stream comparison while `comparison.md` still claims “fixed adaptive batch size b=64.” The EB candidates should all use `b=64`, tuning only `B_max`.

No other blocking findings found against the supplied diff and accepted deferrals.

Codex verdict: REQUEST CHANGES
