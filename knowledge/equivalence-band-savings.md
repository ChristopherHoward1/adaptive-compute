# Equivalence-Band Savings

The equivalence budget is position-dependent. To conclude `equivalent`, the
whole confidence interval must sit inside `[-delta, +delta]`; a truth at
`|Delta| = delta - epsilon` needs half-width near `epsilon`, so cases closer to
the band edge are harder.

The frozen natural `equivalent` stratum is generator-homogeneous rather than
mechanistically homogeneous. In `eval --equiv-probe`, the diagnostic over the
released battery reported tightly clustered `delta - |Delta|` values and low
draw CV for the equivalent stratum under both instruments; it is only a framing
check, not the verdict.

The decisive mixed-equivalence probe constructs a separate unregistered fixture,
proves a non-empty reference-resolvable shallow region at `B_ref=320`, and then
scores both adaptive instruments through `_summarize_stratum -> pareto_verdict`
on the shared fixed-B grid. The production probe selected shallow
`|Delta| ~= 0.034`, with deep mean required reference draws 32.0 and shallow
mean required reference draws 34.7, and scored all 96 primary-ratio cases with
zero reference unresolved.

Verdict from `work/equivalence-band-savings/verdict.md`: **deep-negative**.
Neither EB nor betting met the fixed-B Pareto gate on the heterogeneous in-band
population. Primary 1:1 medians were EB 1824 draws and betting 384 draws; both
had 0.00x best savings, fixed-B dominators, zero abstentions, and zero false
stops with Wilson upper CI 0.0385. The headline was stable across the 1:1 and
2:1 deep:shallow ratios.

If a future fixture cannot prove a non-empty reference-resolvable shallow tier
at `B_ref=320`, the correct interpretation is reference-resolving power, not an
adaptivity verdict.
