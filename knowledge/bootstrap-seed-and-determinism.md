# Bootstrap seed & determinism contract

Load this before touching `src/adaptive_compute/bootstrap.py` or adding a new
Monte-Carlo consumer (the adaptive procedure, a SHAP-sample controller, a fixed-B
sweep). It captures the seed-branching contract that was argued twice during the
`fixed-budget-reference` review (rounds 3 and 5) so it is not re-derived.

## The contract

- **One root seed, two structural branches.** `seed_branches(seed)` returns
  `spawn(2)` of the root: **branch [0] is the reference stream, branch [1] is the
  adaptive stream.** `reference_seed()` / `adaptive_seed()` are the named accessors.
  Any new stream that must be independent of these gets its own branch index —
  never reuse [0] or [1].
- **`paired_bootstrap_deltas` is the reference resampler** and therefore *always*
  routes its seed through `reference_seed` (branch [0]), for both `int` and
  `SeedSequence` inputs. The adaptive resampler, when it exists, must route through
  `adaptive_seed` (branch [1]) — do not have two consumers share branch [0].
- **Clone a `SeedSequence` before spawning.** `SeedSequence.spawn()` advances the
  object's `n_children_spawned` counter, so spawning a *caller-supplied* sequence
  mutates it and makes a second call with the same object produce different
  children. `seed_branches` clones from `(entropy, spawn_key, pool_size)` with a
  fresh counter, so a reused `SeedSequence` object replays bit-identically and the
  caller's object is never mutated.

## Determinism must be tested on BOTH seed paths

The determinism acceptance criterion is over `(params, seed)`. A regression can
hide if only int seeds are tested: round 4's hardening (routing a raw
`SeedSequence` through `spawn`) *introduced* a mutation-on-reuse bug that the
int-seed determinism test could not see; round 5 caught it. So any change to seed
handling must assert bit-identical replay for **(a) the same int seed twice** and
**(b) the same `SeedSequence` object reused twice**, and confirm a raw
`SeedSequence(k)` yields the same stream as `int k`. See
`tests/test_determinism.py`.

## Why it matters

Compute is counted in draws and every result must be reproducible from
`(generator params, seed)` (`docs/experiment-design.md` §9). The reference is the
yardstick the adaptive method is judged against; if their MC streams are not
provably independent, a favorable comparison could be a seed artifact rather than a
real saving.
