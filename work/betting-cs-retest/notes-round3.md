# Implementer notes — betting-cs-retest (round 3 fix: EB default-path scoping)

Commit: a169d77 "Restore EB default benchmark tuning"

Resolves Codex round-3 HIGH (default --run/EB path must be provably v0):
- Restored DEFAULT_BATCH=32.
- EB _tune_params candidates restored to v0 pair {(b=32,B_max=1024),(b=64,B_max=2048)} → --run reproduces v0.
- Betting _tune_params pinned to b=64 with B_max in {128,256,512,1024}.
- A/B integrity preserved: EB deterministically selects b=64,B_max=2048; betting pinned b=64 → both arms b=64.
- LOW fixes: removed redundant COMPARE_DIR.mkdir in eval._compare; de-tautologized F-C stream-equivalence
  assertion (now asserts each arm's consumed prefix == shared replayed stream prefix).

Verified (orchestrator): gate PASS; benchmark.py diff vs origin/main = betting branch + A5 only;
v0 artifact diff empty; EB 128/768/448 (b=64,B_max=2048); betting 64/192/128 (b=64,B_max=512). No flip.
