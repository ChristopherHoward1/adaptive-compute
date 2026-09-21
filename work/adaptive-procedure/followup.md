Round-2 independent review of work/adaptive-procedure/plan.md: the integration code-reviewer APPROVED (no CRITICAL/HIGH); Codex requested changes. Your round-1 fixes are confirmed real and good (genuine non-artifact result, fair independent-stream Pareto, D1/D2 resolved). This is the FINAL fix round (round 3 of a 3-round cap). Fix the items below, stay in-footprint, re-run scripts/gate.sh to green, regenerate `python -m adaptive_compute.eval --run`, commit, and print an updated summary. The H1 verdict is expected to remain NEGATIVE — these fixes harden the reference substrate and the artifact's reporting; they must NOT change the science conclusion, only its trustworthiness.

=== MUST FIX (blocking) ===

[1] Reference-path input validation was silently dropped by the round-1 AUC-kernel optimization.
- Evidence: `paired_bootstrap_deltas` with a non-binary label (e.g. y=[0,2,1]) or a NaN/inf score now returns Δ*=0 silently instead of raising. Before the optimization, `metrics.delta`'s validation (`_as_float_vector` finite check, `_as_binary_labels` 0/1 check) raised on such input. This is a silent-wrong-result regression on the FROZEN reference path's trust boundary — the yardstick must never silently score malformed input.
- Fix: restore equivalent validation (finite scores, binary 0/1 labels, matching shapes) before/at the new resample kernel, for BOTH the reference resampler and the adaptive stream. Prefer validating once up front (not per-draw, to keep the optimization's speed). Add a test asserting non-binary y and non-finite scores raise, on both paths.

[2] Reference path is no longer bit-identical (explicit acceptance criterion unmet).
- Evidence: the new kernel computes `(U_a − U_b)/D` instead of the original `U_a/D − U_b/D`; floating-point reassociation drifts reference deltas by ~1e-16 on most draws vs origin/main. Decisions/estimates are unchanged, but the plan's criterion "Reference path unchanged … bit-identical to pre-unit" is literally violated.
- Fix: preserve the original association so the reference deltas are bit-identical to origin/main again — compute the per-model AUCs and subtract as `auc_a − auc_b` (same order/associativity as `metrics.delta`), keeping the vectorized speedup. Add/keep a regression test asserting the reference delta ARRAY (not just the decision) is bit-identical to a recorded baseline for at least one hard member.

=== JUDGE-AND-FIX ===

[3] N_test=500 does not meet the plan's "false-stop-rate CI half-width ≤ 0.01 at the tolerance" (§7). At p≈α=0.05 that needs n≈1825; at n=500 the half-width is ~0.019. (The realized rate is 0 so the reported CIs are still tight and the §7 conclusion is robust — but the committed precision is unmet.)
- Preferred fix: raise DEFAULT_N_TEST to satisfy ≤0.01 at the tolerance (use N_test = 2000). The AUC kernel is now optimized, so this should be tractable — report the new `eval --run` wall time.
- If (and only if) the full run becomes impractical (say >45 min) at N_test=2000: keep 500 but EXPLICITLY amend the precision statement in results.md AND note it in the plan's Verification section — state "CI half-width ≤ 0.01 holds at the realized rate (0); the ≤0.01-at-tolerance (p≈α) design basis would require n≈1825" — so the commitment is honestly reconciled, not silently missed. State which path you took and why.

[4] H1 headline label conflates §7's statistical test with §8's overall conclusion.
- The headline prints only "H1 NEGATIVE RESULT" though §7's false-stop test PASSES in every stratum and H1 falls solely on §8's ≥2× Pareto gate. This is faithful to §8 but could be misread as a false-stop failure.
- Fix: add a one-line breakdown to results.md immediately under the verdict, e.g. "False-stop test (§7): PASS in every non-boundary stratum (all upper CIs < α). Savings/Pareto (§8): FAIL (no fixed-B dominated at ≥2×). → H1 unsupported on the savings criterion." Keep the machine-readable results.json consistent (separate fields for the §7 test outcome and the §8 conclusion).

=== NOTE (no code change) ===

[5] tests/test_reference.py remains modified but outside the plan's declared footprint (in service of the D2 diagnostic assertion; reference.py source untouched). This is an accepted deliberate addition — just keep calling it out in your summary so it stays on record.

=== DO NOT REGRESS ===
- reference.py frozen and untouched. D1 (degenerate → Δ*=0, counted) and D2 (diagnostic via paired_bootstrap_deltas+np.mean, off the raising path). Blindness, both-path determinism, branch [0]≠[1] independence, fair independent-stream Pareto, exact draw accounting, no abstain-everything. The corrected genuine H1 NEGATIVE result.

When done: gate green; `eval --run` regenerated; commit; print what changed, the (unchanged) H1 verdict with the new §7/§8 breakdown, the N_test decision + new run wall time, and confirm items [1] and [2] are covered by tests.
