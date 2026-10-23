# Repeated Outer Entity-Disjoint Evaluation

Three deterministic outer entity partitions were executed (`outer_seed` 101, 202, 303). For each partition, the outer test entities were isolated before model fitting. Non-test entities were allocated to model training, calibration, and GA validation by deterministic inner assignment. Cross-role pairs were dropped. GB-17 and GB-18 were retrained, calibrated only on calibration entities, and GB-18-GA was selected only on GA-validation entities.

The declared illustrative utility is `2·FP + FN + 0.1·REVIEW`. It is not a measured economic cost.

## Per-outer-split workflow results

| Outer seed | Method | Precision | Recall | F1 | FP | FN | Review | Utility |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 101 | GB-17 | 0.9901 | 0.7285 | 0.8394 | 64 | 2,395 | 2 | 2,523.2 |
| 101 | GB-18 | 0.9931 | 0.7291 | 0.8408 | 45 | 1,910 | 512 | 2,051.2 |
| 101 | GB-18-GA | 0.9903 | 0.7625 | 0.8616 | 66 | 1,537 | 902 | 1,759.2 |
| 202 | GB-17 | 0.9964 | 0.6652 | 0.7978 | 21 | 2,223 | 720 | 2,337.0 |
| 202 | GB-18 | 0.9951 | 0.7279 | 0.8408 | 31 | 2,374 | 0 | 2,436.0 |
| 202 | GB-18-GA | 0.9935 | 0.7582 | 0.8600 | 43 | 1,603 | 784 | 1,767.4 |
| 303 | GB-17 | 0.9863 | 0.7474 | 0.8504 | 92 | 2,181 | 72 | 2,372.2 |
| 303 | GB-18 | 0.9937 | 0.6728 | 0.8023 | 38 | 2,172 | 802 | 2,328.2 |
| 303 | GB-18-GA | 0.9829 | 0.7635 | 0.8594 | 118 | 1,537 | 1,084 | 1,881.4 |

## Aggregate across outer splits

| Method | Precision mean ± SD | Recall mean ± SD | F1 mean ± SD | FP mean ± SD | FN mean ± SD | Review mean ± SD | Utility mean ± SD |
|---|---:|---:|---:|---:|---:|---:|---:|
| GB-17 | 0.9909 ± 0.0051 | 0.7137 ± 0.0431 | 0.8292 ± 0.0277 | 59.0 ± 35.8 | 2,266.3 ± 113.4 | 264.7 ± 395.9 | 2,410.8 ± 98.9 |
| GB-18 | 0.9940 ± 0.0010 | 0.7099 ± 0.0322 | 0.8280 ± 0.0222 | 38.0 ± 7.0 | 2,152.0 ± 232.6 | 438.0 ± 406.1 | 2,271.8 ± 198.5 |
| GB-18-GA | 0.9889 ± 0.0054 | 0.7614 ± 0.0028 | 0.8603 ± 0.0011 | 75.7 ± 38.4 | 1,559.0 ± 38.1 | 923.3 ± 151.1 | 1,802.7 ± 68.3 |

## Paired outer-split interpretation

- GB-18-GA exceeded GB-18 in F1 on all three outer splits: +0.0208, +0.0192, and +0.0571.
- GB-18-GA had lower declared utility than GB-18 on all three outer splits.
- The GA policy increased false positives and review decisions on all three outer splits, while reducing false negatives and increasing recall.
- GB-18's effect relative to GB-17 is not directionally stable for F1 across the three outer splits. The MiniLM feature is therefore supported as a useful primary-run ablation but not as a consistently superior standalone method under fixed thresholds.
- Candidate recall was stable across outer test partitions: mean 0.8838 ± 0.0002, with 1,023.7 ± 10.2 blocking-missed positives. This is a property of the frozen candidate generator, not a retrieval improvement.

Raw run artifacts: `experiments/icsec_final/repeated_outer/`.
