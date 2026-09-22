# Implementer notes — betting-cs-retest (round 4 fix: EB tuning decouple)

Commit: d0119ba "Decouple EB compare tuning candidates"

Resolves the Codex R3/R4 contradiction by decoupling EB tuning per entry point:
- Added optional `candidates` override to `_tune_params` and `run_benchmark` (default None = instrument default).
- `--run` (run_and_write_results, default): EB uses v0's candidate set {(b=32,B_max=1024),(b=64,B_max=2048)},
  DEFAULT_BATCH=32 — reproduces v0. (Satisfies Codex R3: default --run path unchanged.)
- `--compare` EB arm: explicit b=64-pinned candidates {(64,2048),(64,1024)}. (Satisfies Codex R4: A/B pins b=64.)
- A/B invariant now enforced in code (both arms b=64 by construction), not by lucky selection.

Verified (orchestrator): gate PASS; benchmark.py EB default set + DEFAULT_BATCH=32 unchanged vs origin/main
(only the optional `candidates` param + A5 added); --compare EB pinned b=64; v0 artifact diff empty;
EB 128/768/448 (b=64,B_max=2048), betting 64/192/128 (b=64,B_max=512). Headline NO flip, §7 held.
