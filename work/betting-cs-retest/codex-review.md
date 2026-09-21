**Findings**

1. HIGH: `src/adaptive_compute/betting.py:91-97` reports a continuous-looking CS by taking the min/max surviving grid points, but Ville validity only applies at the tested grid means. For true means between grid points, the implementation can reject both neighboring grid points and move the interval past the true mean, so the returned Δ interval is not an anytime-valid confidence sequence for arbitrary bounded means. That can directly produce a false `A_better`/`B_better`/`equivalent` stop while still satisfying the grid test. The implementation needs continuous inversion or conservative grid padding at minimum before this can support the §7 guarantee.

2. HIGH: `src/adaptive_compute/benchmark.py:27,167-175` changes the EB benchmark tuning surface by setting `DEFAULT_BATCH = 64` and replacing the old EB candidates `(b=32, B_max=1024)` and `(b=64, B_max=2048)` with fixed-`b=64` candidates. The plan says existing `--run` behavior and the released EB-default path remain unchanged except the A5 `<= alpha` correction. This means a plain EB benchmark can now tune/run differently from v0, so the A/B is no longer “add, don’t replace” for the EB arm.

3. MEDIUM: `tests/test_betting.py:80-123` does not actually assert drop-in stream equivalence between EB and betting. It runs both adaptive decisions, then compares two freshly-created `adaptive_bootstrap_stream(...)` instances to each other with the same seed. That would pass even if `adaptive_decision(..., instrument="betting")` consumed a different stream internally. The acceptance criterion asks for exact `np.array_equal` on the per-batch deltas consumed by the two arms at matched prefixes.

4. MEDIUM: `src/adaptive_compute/eval.py:304-310` can write a misleading headline if betting fails §7. The non-flip branch always says betting “did not flip to true while preserving §7”, even when `betting.false_stop_test_pass` is false. Since `comparison.md` is the deliverable headline artifact, it should distinguish “no flip because savings failed” from “no flip because §7 failed.”

Codex verdict: REQUEST CHANGES
