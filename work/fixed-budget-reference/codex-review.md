**Findings**

HIGH: [src/adaptive_compute/reference.py:43](src/adaptive_compute/reference.py:43) maps an interval that straddles a decision margin to `equivalent`. The plan defines equivalence only when the percentile interval is wholly inside `[-δ, +δ]`; otherwise `A_better`/`B_better` require the full interval beyond the margin. For example, the committed test case `[0.049, 0.051, 0.20]` has an estimate above `+δ` and an interval extending outside the equivalence band, but the implementation returns `equivalent`. That is a false equivalence decision, not “what the interval read-off concludes,” and it can corrupt recovery for any finite-B non-boundary case whose interval barely crosses a margin.

Codex verdict: REQUEST CHANGES
