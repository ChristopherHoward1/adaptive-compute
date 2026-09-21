# Implementer notes — betting-cs-retest (round 2, review fixes)

Commit: 3ded9fb "Fix betting CS retest review findings"

- F-A: pinned EB tuning to B_max=2048 (b=64), betting keeps smaller B_max candidates. EB arm now
  reproduces v0 (equivalent p50=768, moderate p50=448). `work/adaptive-procedure/results.*` untouched.
- F-B: predictability test now compares capital paths over identical prefixes with DIFFERENT suffixes.
- F-C: stream-equivalence test reconstructs one bootstrap stream and replays both EB/betting band
  decisions from it (non-vacuous). Introduced `BettingCSState` (incremental hedged-capital state) in
  betting.py; adaptive.py now updates it per-batch instead of recomputing the full path each look
  (equivalent result, O(draws) not O(draws^2)). `betting_cs_bounds` preserved (delegates to the state).
- F-D: comparison.md headline now distinguishes savings-failed-(§7-held) vs §7-failed.
- Deferral D-grid: added ponytail comment at the grid-hull return documenting the ceiling + upgrade path.

Gate: GATE: PASS (49 pytest, mypy/ruff/eval green) on my run. Headline unchanged: NO flip.
