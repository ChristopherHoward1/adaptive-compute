# Controlled re-test discipline

How to build a unit that re-tests a *released* result under a changed component (a new
instrument, kernel, estimator) as an honest A/B. Written after `betting-cs-retest`
(v2026.9.4) took 5 review rounds — most of the churn traced to violating the first rule.

The setting: you have a released baseline (e.g. the empirical-Bernstein arm, whose
numbers live in a released artifact) and you want to swap one component (the confidence
band) and see whether a gated verdict changes. The result is only trustworthy if the
*only* thing that differs between arms is the component under test.

## 1. Never route the experiment through the released baseline's code path

The baseline arm you compare against and the released `--run`/regeneration path are two
different obligations that pull in opposite directions:

- The released path (`eval --run` → the released artifact) must **reproduce the prior
  release** — same tuning search space, same defaults, byte-for-byte except explicitly
  accepted changes.
- The experiment's baseline arm must be **matched to the new arm** (same shared inputs,
  same fixed hyper-parameters) so attribution is clean.

If a single shared function serves both, you cannot satisfy both, and it surfaces late as
a reviewer oscillating between "you changed the released path" and "your arms aren't
matched." In `betting-cs-retest` one shared `_tune_params` served `--run` (needs the v0
candidate set, incl. `b=32`) and `--compare`'s EB arm (needs `b=64` pinned); Codex
flipped between the two demands across rounds 3 and 4. The fix was an optional
`candidates` override so `--run` keeps the released default while `--compare` passes an
explicit matched set. **Design that seam into the plan from the start** — a parameter on
the shared function, or two entry points — and never mutate a global default (e.g.
`DEFAULT_BATCH`) to serve the experiment.

## 2. Hold the shared variable constant, and enforce it in code

The controlled variable (in `betting-cs-retest`, the bootstrap batch size `b`, because
`adaptive_bootstrap_stream` draws `rng.integers(0, n, size=(b, n))` per batch — a
different `b` shifts RNG call boundaries and the two arms no longer consume the identical
stream) must be *pinned*, not left to a tuner that "happens" to pick the same value.
Relying on deterministic selection is fragile: a reviewer will (correctly) point out the
invariant isn't enforced, and a later parameter change could silently break it. Pin it
explicitly for both arms and, where feasible, assert it.

## 3. Never overwrite the released artifact

Generate the experiment's outputs into the unit's own `work/<slug>/` directory. The
released baseline artifact (here `work/adaptive-procedure/results.*`) is protected: verify
`git diff origin/main...wt/<slug> -- <released artifact path>` is EMPTY before shipping.

## 4. A guard-test must be able to fail

The tests that certify the A/B's invariants (predictability of a predictable-λ estimator;
"only the band differs" stream equivalence) are load-bearing — but only if they can
actually fail. Two such tests in `betting-cs-retest` initially compared a value to itself
(both operands sliced to the same prefix; two identically-constructed fresh streams) and
passed the gate while guarding nothing. The gate runs tests; it cannot tell a tautology
from a real assertion. Write each guard-test so that the bug it guards against would make
it red: perturb the future and require an earlier value unchanged; reconstruct the shared
stream and require each arm's *consumed* prefix to equal it — never `x == x`.
