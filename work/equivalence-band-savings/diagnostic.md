# Equivalence-Band Estimator Asymmetry

The fixture spans in-band positions only. It does not claim difficulty heterogeneity; the measured mechanism is fixed-width percentile intervals versus shrinking anytime-valid confidence sequences.

## Mechanism curves

Scored with b=64, B_max=8192, max_looks=128, fixed-B scoring grid=(32, 64, 128, 320). The diagnostic-only fixed curve samples through 1280 draws.

| arm | fixed w(B_ref) | fixed w(4*B_ref) | plateau gap | adaptive w(B_ref) | median adaptive crossing | median fixed B* |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| eb | 0.0121 | 0.0123 | 0.0002 | 0.1264 | 832 | 32 |
| betting | 0.0121 | 0.0123 | 0.0002 | n/a | 192 | 32 |

## Representative case curves

| arm | seed | `|Delta|` | w_fix(B) | w_ad(n) |
| --- | ---: | ---: | --- | --- |
| eb | 8075 | 0.0240 | 32:0.0111, 64:0.0112, 128:0.0127, 320:0.0127, 640:0.0126, 960:0.0122, 1280:0.0123 | 64:0.6359, 128:0.3161, 192:0.2105, 320:0.1264, 512:0.0792, 768:0.0529, 1024:0.0398, 1536:0.0266, 2048:0.0200, 4096:0.0101, 8192:0.0052 |
| betting | 8075 | 0.0240 | 32:0.0111, 64:0.0112, 128:0.0127, 320:0.0127, 640:0.0126, 960:0.0122, 1280:0.0123 | 64:0.1375, 128:0.0600, 192:0.0400, 320:0.0200, 512:0.0125, 768:0.0075, 1024:0.0050, 1536:0.0025, 2048:0.0000, 4096:0.0000, 8192:0.0000 |

## Natural equivalent stratum

This frozen-battery diagnostic is generator-homogeneous context only; the verdict is the scored in-band fixture above.

| instrument | scored | adaptive draws p50/p90/p99 | draws CV | delta - `|Delta|` p50/p90/p99 | gap CV |
| --- | ---: | --- | ---: | --- | ---: |
| eb | 32 | 960/1152/1216 | 0.110 | 0.0444/0.0490/0.0494 | 0.102 |
| betting | 32 | 192/256/256 | 0.128 | 0.0444/0.0490/0.0494 | 0.102 |
