# Equivalence-Band Savings Verdict

Headline verdict: **deep-negative** — fixed-B dominates both adaptive instruments inside the equivalence band.

| arm | stable headline | primary ratio | scored/generated | median draws | best savings | fixed-B dominators | abstain | ref resolved | false stops | 95% CI |
| --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| eb | deep-negative | 1:1 | 96/96 | 1344 | 0.00x | 32, 64, 128, 320 | 0.0000 | 1.000 | 0 | [0.0000, 0.0385] |
| betting | deep-negative | 1:1 | 96/96 | 288 | 0.00x | 32, 64, 128 | 0.0000 | 1.000 | 0 | [0.0000, 0.0385] |

Fixture cap: |Delta| <= 0.024; primary spread 0.0240; minimum band gap 0.0260.
Mechanism: EB has w_ad(B_ref)=0.1264 > delta=0.0500; betting resolves below B_ref, but its median fixed B*=32 is below its adaptive median 288.
The headline is mechanically derived from probe JSON fields and checked across ratios 1:1, 2:1.
