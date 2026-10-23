# Supplementary results — frozen-family additive analysis

Means and sample SD over seeds 101/202/303, calculated from per-seed metrics (not pooled counts). Review rate and coverage below are fractions. REVIEW does not imply successful human resolution.

| Policy | precision | decision_recall | end_to_end_recall | decision_F1 | end_to_end_F1 | review_rate | coverage | positive_REVIEW | FP | FN | REVIEW | U |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GB17_B0 | 0.986348 ± 0.002380 | 0.746588 ± 0.040460 | 0.718739 ± 0.075633 | 0.849436 ± 0.025698 | 0.829952 ± 0.050957 | 0.001884 ± 0.002384 | 0.998116 ± 0.002384 | 344.000 ± 444.581 | 89.000 ± 25.060 | 2137.333 ± 211.864 | 366.333 ± 461.021 | 2351.967 ± 212.326 |
| B0 | 0.986969 ± 0.007999 | 0.748619 ± 0.038720 | 0.735744 ± 0.060377 | 0.850965 ± 0.023525 | 0.841952 ± 0.038483 | 0.000871 ± 0.001491 | 0.999129 ± 0.001491 | 160.667 ± 275.689 | 88.000 ± 56.507 | 2171.333 ± 251.806 | 168.667 ± 288.682 | 2364.200 ± 212.009 |
| B1 | 0.983362 ± 0.004697 | 0.814565 ± 0.000825 | 0.774848 ± 0.011789 | 0.891037 ± 0.002415 | 0.866722 ± 0.009001 | 0.003847 ± 0.000916 | 0.996153 ± 0.000916 | 430.000 ± 115.659 | 115.333 ± 30.139 | 1557.667 ± 31.070 | 762.333 ± 178.113 | 1864.567 ± 45.883 |
| B2 | 0.984357 ± 0.002870 | 0.812413 ± 0.004070 | 0.765436 ± 0.018972 | 0.890149 ± 0.001602 | 0.861105 ± 0.011450 | 0.004273 ± 0.001381 | 0.995727 ± 0.001381 | 509.667 ± 164.865 | 107.667 ± 21.733 | 1560.333 ± 32.578 | 843.667 ± 260.715 | 1860.033 ± 27.069 |
| B3 | 0.984355 ± 0.002867 | 0.812652 ± 0.003731 | 0.765323 ± 0.019066 | 0.890293 ± 0.001481 | 0.861031 ± 0.011501 | 0.004318 ± 0.001401 | 0.995682 ± 0.001401 | 513.333 ± 167.381 | 107.667 ± 21.733 | 1557.667 ± 31.070 | 852.333 ± 263.898 | 1858.233 ± 29.960 |
| Chow | 0.985869 ± 0.006649 | 0.838423 ± 0.010984 | 0.753990 ± 0.029849 | 0.906145 ± 0.006042 | 0.854216 ± 0.018305 | 0.020442 ± 0.002468 | 0.979558 ± 0.002468 | 890.333 ± 208.150 | 96.000 ± 46.163 | 1281.000 ± 43.863 | 4060.333 ± 579.614 | 1879.033 ± 51.485 |

Full per-partition values: ../../experiments/icsec_final/reviewer_revision/metrics_per_seed.csv. Full-precision final vectors: selected_vectors.csv. Incumbent vectors and objectives at 48 checkpoints: anytime_checkpoints.csv. Each per-seed B2/B3_anytime.csv contains all 12,000 realized evaluations. These are validation-only replay traces, not original historical logs or extra independent scientific partitions.
