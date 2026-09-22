# Equivalence-Band Savings

Inside `[-delta, +delta]`, fixed-B structurally beats the adaptive instruments in this
repo's offline probe. The reason is estimator class, not a lucky grid: the fixed-B
percentile-bootstrap interval is the same fixed-width functional used by the reference, so
its half-width converges to the data's bootstrap-quantile spread and then plateaus. An
anytime-valid instrument must instead shrink a confidence-sequence half-width below
`delta`, which costs additional Monte Carlo draws.

`eval --equiv-probe` records this asymmetry in `work/equivalence-band-savings/`. On the
primary in-band fixture (`|Delta| <= 0.024`, 96/96 scored), the median fixed percentile
half-width was `0.0121` at `B_ref=320` and `0.0123` at `4*B_ref=1280`, a plateau gap of
`0.0002`. EB's adaptive half-width at `B_ref` was still `0.1264 > delta=0.0500`, with a
median adaptive crossing at 832 draws and median scored draws 1344. Betting crossed below
`delta` earlier, at median 192 draws with median scored draws 288, but the median cheapest
resolving fixed-B was 32, so fixed-B still dominated betting on equivalence decisions.

The honest savings verdict is therefore **deep-negative** for both instruments against the
released `FIXED_B_GRID=(32,64,128,320)`: EB had fixed-B dominators `32, 64, 128, 320`, and
betting had dominators `32, 64, 128`. Both arms had zero abstentions, zero false stops, and
reference-resolved fraction 1.000 on the scored fixture, so the negative is not an
abstention or attrition artifact.

Scope this narrowly. Adaptive Monte Carlo can still save draws for directional decisions
under difficulty heterogeneity, where a confidence sequence can cross a one-sided
threshold early. This note only claims the equivalence-band result: for in-band decisions,
the fixed-width percentile functional is the cheaper tool in the measured fixture.
