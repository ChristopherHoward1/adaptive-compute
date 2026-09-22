# Deferrals — equivalence-band-savings (rev 3)

Latent, non-blocking findings from the rev-3 round-1 review (both reviewers APPROVE; no
CRITICAL/HIGH). Recorded here so the next cold reviewer / `/5-retro` sees settled scope.

## D1 — `PLATEAU_TOL` is band-scaled, a weak discriminator (anchor MEDIUM)
`equiv_probe.py:PLATEAU_TOL = 4·δ/√B_ref ≈ 0.01118` is scaled to the band (δ=0.05), not to
the `w_fix`-scale quantile MC-noise. At the fixed-width scale `w_fix(B_ref)=0.0121`, a
genuinely shrinking functional would drop ≈0.006 over 320→1280 — below the 0.0112 tolerance,
so the plateau guard cannot, in principle, distinguish fixed-width from shrinking.
**Why deferred:** does not affect this verdict — the measured gap is 0.000185 (~60× under
tolerance) and the percentile bootstrap provably converges to a fixed quantile spread, so the
plateau is demonstrated with large empirical margin. The defect is the guard's *protective
value for future reuse*, not correctness.
**Where it lands:** re-derive `PLATEAU_TOL` from `w_fix`-scale MC noise (well under the
shrinking-CS drop) when this asymmetry-guard pattern is next touched or reused.

## D2 — mechanism diagnostic runs over generated, not strictly scored, cases (Codex MEDIUM)
`equiv_probe.py:mechanism_diagnostic()` computes curves/medians over all generated fixture
cases; the plan says "on the scored in-band cases."
**Why deferred:** identical today — abstain=0.0, ref-resolved=1.000, scored 96/96 — so the
populations coincide. A future fixture with <100% resolution could diverge.
**Where it lands:** restrict the diagnostic to the scored set (or assert scored==generated)
when the fixture or feasibility bounds change.

## D3 — `verdict.md` derived from in-memory objects, not JSON read-back (Codex MEDIUM)
The headline is computed from the in-memory `ProbeRun`/`summary` (same values written to JSON),
not by reading the JSON artifacts back.
**Why deferred:** values are identical today; not behaviorally wrong. Misses hypothetical
serialization/artifact drift only.
**Where it lands:** read the JSON back for the headline if the write/derive paths ever diverge.

## D4 — `--check` determinism replay exercises only the betting arm (anchor LOW)
`deterministic_probe_signature` replays `instrument="betting"` only; EB's
`mechanism`/`eb_width_at_b_ref` path is not in the determinism assertion.
**Why deferred:** shared machinery is exercised; EB-only nondeterminism is low-risk.
**Where it lands:** add an EB replay to the signature if `--check` coverage is revisited.
