Findings:

- MEDIUM: [src/adaptive_compute/equiv_probe.py:377] `mechanism_diagnostic()` is run over all generated fixture cases, not the scored set used for the savings verdict. The plan requires the mechanism guards and curves “on the scored in-band cases.” Because the feasibility guard allows less than 100% reference resolution, a future fixture could pass with up to 5% unscored cases while the diagnostic plateau/crossing medians include those unscored cases. That would make the reported mechanism population differ from the verdict population.

- MEDIUM: [src/adaptive_compute/equiv_probe.py:570] `verdict.md` is derived from in-memory `ProbeRun` objects after writing JSON, not by reading the JSON artifacts. The values currently come from the same objects, so this is not behaviorally wrong today, but it does not fully satisfy the “headline is computed from the JSON” contract and would miss serialization/artifact drift.

No CRITICAL or HIGH findings. The implementation otherwise stays inside the declared footprint, reuses the released savings helpers/grid, preserves `BATTERY`, and the per-instrument EB vs betting asymmetry is represented correctly.

Codex verdict: APPROVE
