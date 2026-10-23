# Main Ablation: Frozen ICSEC Reproduction

Protocol: entity-disjoint nested split (`entity_nested_v1`, seed 42); identical sealed test role; labels derived from `user_folder`; exact-tier and blocking-missed constants included in the workflow metrics. Cost is the frozen GA objective `2·FP + FN + 0.1·REVIEW`.

| Method | Isolated change | Precision | Recall | F1 | FP | FN | REVIEW | Weighted cost |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| GB-17 | 17 handcrafted profile-pair features; fixed 0.98/0.95 thresholds | 0.9949 | 0.4258 | 0.5963 | 19 | 1,976 | 3,192 | 2,333.2 |
| GB-18 | GB-17 + MiniLM cosine; fixed 0.98/0.95 thresholds | 0.9884 | 0.7283 | 0.8387 | 75 | 1,831 | 623 | 2,043.3 |
| GB-18-GA | GB-18 calibrated probabilities + validation-selected GA three-way policy | 0.9843 | 0.7670 | 0.8622 | 107 | 1,565 | 847 | 1,863.7 |

Interpretation boundaries:

- GB-17 to GB-18 isolates the added MiniLM cosine feature under the same classifier family, model seed, sampled training rows, calibration role, and fixed decision thresholds.
- GB-18 to GB-18-GA isolates the decision policy: GA uses the same persisted calibrated GB-18 probabilities and does not alter the classifier or calibrator.
- The table must not be combined with historical R0–R6 metrics because their protocol, model family, candidate scope, or cost weights differ.
- CIs are in `experiments/icsec_final/statistical_analysis/paired_bootstrap_ci.csv`; they are conditional paired bootstrap intervals over scored held-out candidate pairs, with exact/blocking constants fixed.
